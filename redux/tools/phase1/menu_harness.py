"""Build/run the external menu observer with fresh private profiles and receipts.

Invoked by the coordinator only; no engine rebuild, player attachment or font
override. Assertion success is separate from rendered/pointer fidelity.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import uuid
import importlib.util

_stats_spec = importlib.util.spec_from_file_location('redux_stats_validation', Path(__file__).with_name('stats_validation.py'))
stats_validation = importlib.util.module_from_spec(_stats_spec)
_stats_spec.loader.exec_module(stats_validation)

_page_spec = importlib.util.spec_from_file_location('redux_information_validation', Path(__file__).with_name('spellbook_information_validation.py'))
page_validation = importlib.util.module_from_spec(_page_spec)
_page_spec.loader.exec_module(page_validation)

_private_spec = importlib.util.spec_from_file_location('redux_private_game', Path(__file__).with_name('private_game.py'))
private_game = importlib.util.module_from_spec(_private_spec)
_private_spec.loader.exec_module(private_game)

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REQUIRED_OBSERVATIONS = {name + ".observed" for name in (
    "inventory", "record", "mage-book", "priest-book", "journal", "area-map", "world-map-view",
    "options", "video", "audio", "gameplay", "character-sounds", "feedback", "autopause", "save", "load",
    "information", "customization", "kit-description", "biography", "export")}
REQUIRED_OBSERVATIONS.update("stats.observed-%d" % index for index in range(6))
REQUIRED_OBSERVATIONS.update(("hotkeys.transition", "load.closed", "save.closed", "record.closed"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(path):
    return {str(p.relative_to(path)).replace("\\", "/"): sha(p)
            for p in sorted(Path(path).rglob("*")) if p.is_file()}


def artifact_manifest(path):
    """Never traverse private GamePath asset junctions into licensed archives."""
    path = Path(path)
    result = {}
    for parent, directories, files in os.walk(path, followlinks=False):
        directories[:] = [d for d in directories if d != 'game']
        for name in files:
            item = Path(parent) / name
            result[str(item.relative_to(path)).replace('\\', '/')] = sha(item)
    return result


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf8")


def menu_source_inputs(source):
    return [Path(__file__), HERE/'menu_probe.cpp', HERE/'gui/MenuRuntime.py', HERE/'gui/MenuStart.py',
            HERE/'gui/StatsRuntime.py', HERE/'stats_validation.py',
            HERE/'private_game.py', HERE/'spellbook_information_validation.py', HERE/'../phase0/native/gui_probe.cpp', HERE/'../phase0/native/save_probe.cpp'] + [
            Path(source)/'gemrb/GUIScripts'/name for name in
            ('GUIREC.py','GUIRECCommon.py','EECharacterSheet.py','PortraitWindow.py','GUIMG.py','GUIPR.py','EESpellbookHeading.py','EESpellbookInformation.py','BG2EEConfirmation.py','GUIOPT.py','GUIOPTControls.py','GUICommon.py','GUICommonWindows.py','Spellbook.py','GameCheck.py','GUIDefines.py','GUIClasses.py')] + [Path(source)/'gemrb/unhardcoded/shared/defaults.ini']


def freeze_source_inputs(paths, directory):
    identities = {str(Path(path).resolve()): sha(path) for path in paths}
    copies = {}
    for path, digest in identities.items():
        original = Path(path)
        frozen = Path(directory)/'sources'/digest/original.name
        frozen.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, frozen)
        if sha(frozen) != digest:
            raise ValueError('Menu frozen source differs from its input')
        copies[path] = dict(frozen=str(frozen),sha256=digest)
    return identities, copies


def callback_errors(path):
    """Known native bridge failure prefixes, not arbitrary UI text 'error'."""
    return [dict(line=i+1, text=line) for i,line in enumerate(Path(path).read_text(encoding='utf-8',errors='replace').splitlines())
            if line.startswith('[Python/ERROR]: Traceback (most recent call last):')
            or line.startswith('[GUIScript/ERROR]: Runtime Error:')]


def run_owned(command, cwd, env, log, timeout):
    with Path(log).open("wb") as stream:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        timed_out = False
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=stream, stderr=stream,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=30)
            else:
                process.kill()
            code = process.wait(timeout=30)
    return dict(command=command, owned_pid=process.pid, exit_code=code, timed_out=timed_out,
                cleanup_complete=process.poll() is not None)


def validate_spellbook_capture(contract, state, ui):
    """Bind queried spell slots to the independently captured visible controls.

    Tooltip/value plus public Picture presence prove populated slot assembly;
    they do not prove sprite pixels identify the claimed resref or visual QA.
    """
    pack, pc = contract['pack'], contract['actor']
    if pack not in ('GUIMG', 'GUIPR') or not isinstance(pc, int) or not 1 <= pc <= len(state['party']):
        raise ValueError('Invalid spellbook actor/pack')
    def field(cid):
        found = [item for item in ui['controls'] if item['pack'] == pack and item['window'] == 2 and item['id'] == cid]
        if len(found) != 1 or not found[0]['visible']:
            raise ValueError('Missing/ambiguous visible spellbook control')
        return found[0]
    checks = [dict(name=pack+'.native-selected-actor', passed=state['selection'] == pc),
        dict(name=pack+'.native-displayed-name', passed=field(0x10000035)['text'] ==
             state['party'][pc-1]['name'] == contract['actor_name'])]
    if not contract['sorcerer']:
        checks.extend(validate_spellbook_heading(contract, state, ui, field))
    families = [('known',27,24),('memorized',3,0)] if contract['sorcerer'] else [('memorized',3,12)]
    if not contract['sorcerer']:
        if contract.get('layout_mode')!='ordinary-information/1' or contract.get('known_capacity')!=7:raise ValueError('Unknown ordinary information layout mode')
        shown=[dict(original_index=r['value'],resref=r['resref'].upper(),name=r['tooltip'])for r in contract['known']]
        if not isinstance(contract.get('information_page'),dict)or contract['information_page'].get('top')!=0:raise ValueError('Menu open did not navigate information pages')
        page_validation.validate_page(contract.get('information_page'),shown,ui['controls'],pack,pc,1 if pack=='GUIMG'else 0,contract['level'])
    elif contract.get('layout_mode')!='legacy-spontaneous/1':raise ValueError('Unknown spontaneous layout mode')
    for family, base, capacity in families:
        spells = contract[family]
        if contract[family+'_capacity'] != capacity or len(spells) > capacity:
            raise ValueError('Unsupported spellbook slot capacity')
        for index in range(capacity):
            item = field(base+index)
            expected = spells[index] if index < len(spells) else None
            if expected:
                size = item.get('picture_size')
                rect = item.get('rect')
                passed = (bool(expected['resref']) and bool(expected['tooltip']) and
                    item.get('stored_tooltip') == expected['tooltip'] and
                    item.get('tooltip') == expected['tooltip'] and
                    item.get('value') == expected['value'] and not item.get('disabled', True) and
                    bool(item.get('flags', 0) & 2) and item.get('picture_observable') is True and
                    item.get('picture_present') is True and isinstance(size, list) and
                    len(size) == 2 and all(isinstance(n, int) and n > 0 for n in size) and
                    isinstance(rect, list) and len(rect) == 4 and rect[2] > 0 and rect[3] > 0)
            else:
                # Empty controls may retain a cached Picture internally, but it
                # must no longer be displayed or expose a stale spell tooltip.
                passed = item.get('stored_tooltip') == '' and not (item.get('flags', 0) & 2)
            checks.append(dict(name=pack+'.'+family+'-slot-'+str(index), passed=passed))
    if not contract['known'] and not contract['memorized']:
        raise ValueError('Populated spellbook coverage absent')
    return checks


def validate_spellbook_heading(contract, state, ui, field):
    """Compare ordinary heading queries with actual native controls/world pages.

    Label font/color/alignment are private and not sampled by MenuUIJSON. Global
    FontsJSON provenance and rendered QA remain separate evidence requirements.
    """
    pack, pc, level = contract['pack'], contract['actor'], contract['level']
    kind = 1 if pack == 'GUIMG' else 0
    heading = contract.get('heading')
    if (type(level) is not int or not 0 <= level < (9 if kind else 7) or
        not isinstance(heading, dict) or heading.get('schema') != 'bg-redux-ordinary-spellbook-heading/1' or
        heading.get('strref') != 11944 or heading.get('per_label_style_observed') is not False or
        not isinstance(heading.get('localized_prefix'), str) or not heading['localized_prefix'] or
        not isinstance(heading.get('level_text'), str) or not heading['level_text'] or
        any(type(heading.get(key)) is not int or heading[key] < 0 for key in ('allocated_count','capacity'))):
        raise ValueError('Missing/malformed ordinary spellbook heading contract')
    pages = [page for page in state['party'][pc-1].get('spellbook', [])
             if page.get('type') == kind and page.get('level') == level]
    if len(pages) != 1 or not isinstance(pages[0].get('memorized'), list) or type(pages[0].get('slots_with_bonus')) is not int:
        raise ValueError('Missing/ambiguous native spellbook page for heading')
    page = pages[0]
    label, level_label = field(0x10000033), field(0x10000032)
    windows = [row for row in ui['controls'] if row.get('pack') == pack and row.get('id') == 2 and
               row.get('window') is None and row.get('type') is None]
    if len(windows) != 1 or not windows[0].get('visible') or windows[0].get('disabled', True):
        raise ValueError('Missing/ambiguous eligible native spellbook window')
    window_rect = windows[0].get('rect')
    expected = '%s: %d/%d' % (heading['localized_prefix'], heading['allocated_count'], heading['capacity'])
    rect = label.get('rect')
    prepared = [field(3+index).get('rect') for index in range(12)]
    geometry = (isinstance(window_rect,list) and len(window_rect)==4 and all(type(n) is int for n in window_rect) and
                rect == [295,598,275,40] and rect[0]+rect[2] <= window_rect[2] and
                rect[1]+rect[3] <= window_rect[3] and all(isinstance(r,list) and len(r)==4 and
                all(type(n) is int for n in r) and r[1] == 644 and r[2] > 0 and r[3] > 0 and
                r[0] >= 0 and r[0]+r[2] <= window_rect[2] and r[1]+r[3] <= window_rect[3] and
                rect[1]+rect[3] < r[1] for r in prepared))
    return [
        dict(name=pack+'.heading-native-page-counts', passed=(heading['allocated_count'] == len(page['memorized']) and
             heading['capacity'] == page['slots_with_bonus'])),
        dict(name=pack+'.heading-native-localized-text', passed=label.get('text') == expected),
        dict(name=pack+'.heading-native-selected-level', passed=(heading.get('level_token') == str(level+1) and
             level_label.get('text') == heading['level_text'])),
        dict(name=pack+'.heading-native-strip-geometry', passed=geometry)]


def validate_stage(directory, resolution=None, *, expected_nonce, require_ordinary_spellbooks=False):
    """Fail incomplete/missing evidence; never turn screenshots into visual QA."""
    directory = Path(directory)
    host = json.loads((directory / "menu-host-result.json").read_text(encoding="utf8"))
    runtime = json.loads((directory / "menu-runtime.json").read_text(encoding="utf8"))
    if (not isinstance(expected_nonce, str) or len(expected_nonce) != 32 or
        any(c not in '0123456789abcdef' for c in expected_nonce) or
        host.get('nonce') != expected_nonce or runtime.get('nonce') != expected_nonce):
        raise ValueError('Missing/mismatched caller-pinned menu nonce')
    if not host.get("completed") or runtime["steps"] != runtime["planned_steps"]:
        raise ValueError("Menu plan incomplete")
    if REQUIRED_OBSERVATIONS - {row.get("action") for row in runtime["checks"]}:
        raise ValueError("Required menu/category coverage missing")
    if any(not row.get("capture") for row in runtime["checks"] if row.get("action") in REQUIRED_OBSERVATIONS):
        raise ValueError("Required observation lacks its capture")
    captures = [row for row in runtime["checks"] if row.get("capture")]
    ids = [row["capture"] for row in captures]
    if not ids or len(ids) != len(set(ids)) or len(ids) != host["captures"]:
        raise ValueError("Capture inventory missing or ambiguous")
    for index in ids:
        prefix = directory / ("capture-%d" % index)
        bmp = prefix.with_suffix(".bmp").read_bytes()
        if len(bmp) < 54 or bmp[:2] != b"BM":
            raise ValueError("Invalid/missing screenshot")
        declared = struct.unpack_from("<I", bmp, 2)[0]
        offset = struct.unpack_from("<I", bmp, 10)[0]
        width, height = struct.unpack_from("<ii", bmp, 18)
        if declared != len(bmp) or not 54 <= offset < len(bmp) or width <= 0 or height == 0:
            raise ValueError("Malformed screenshot dimensions/length")
        if resolution and [width, abs(height)] != list(resolution):
            raise ValueError("Screenshot resolution differs from requested run")
        for suffix in (".ui.json", ".state.json", ".observer.json"):
            json.loads(Path(str(prefix) + suffix).read_text(encoding="utf8"))
    checks = [row for row in runtime["checks"] if isinstance(row.get("passed"), bool)]
    if not checks:
        raise ValueError("No actionable menu assertions")
    errors=callback_errors(directory/'process.log')
    checks.append(dict(name='native-python-callback-log',passed=not errors, errors=errors))
    ordinary_spellbooks = []
    for name in ('mage-book', 'priest-book'):
        applicability = [r for r in runtime['checks'] if r.get('name') == name+'.applicability']
        if len(applicability) != 1:
            raise ValueError('Missing/ambiguous spellbook applicability')
        contracts = [r for r in runtime['checks'] if r.get('name') == name+'.content-contract']
        if not applicability[0]['applicable']:
            if contracts or applicability[0].get('selected_actor') is not None:
                raise ValueError('Context-gated spellbook has fabricated content')
            continue
        if (len(contracts) != 1 or contracts[0]['actor'] != applicability[0]['selected_actor'] or
            contracts[0]['pack'] != ('GUIMG' if name == 'mage-book' else 'GUIPR')):
            raise ValueError('Missing/ambiguous spellbook semantic contract')
        if not contracts[0]['sorcerer']:
            ordinary_spellbooks.append(name)
        callbacks = [json.loads(p.read_text(encoding='utf8')) for p in directory.glob('callback-*.json')
                     if p.stem.removeprefix('callback-').isdigit()]
        for action, pack, control_id in ((name+'.select-eligible', 'PORTWIN', contracts[0]['actor']-1),
                                         (name+'.open', 'OPTWIN', 5 if name=='mage-book' else 6)):
            steps = [r for r in runtime['checks'] if r.get('action') == action]
            if len(steps) != 1 or not isinstance(steps[0].get('step'), int):
                raise ValueError('Missing spellbook callback action identity')
            dispatch = [r for r in callbacks if r.get('runtime_step') == steps[0]['step']+1]
            if (len(dispatch) != 1 or dispatch[0].get('pack') != pack or dispatch[0].get('window') != 0 or
                dispatch[0].get('control') != control_id or dispatch[0].get('performed') is not True or
                dispatch[0].get('nonce') != expected_nonce):
                raise ValueError('Missing/stale/wrong spellbook registered callback')
        capture = next(r['capture'] for r in runtime['checks'] if r.get('action') == name+'.observed')
        prefix = directory / ('capture-%d' % capture)
        checks.extend(validate_spellbook_capture(contracts[0],
            json.loads(Path(str(prefix)+'.state.json').read_text(encoding='utf8')),
            json.loads(Path(str(prefix)+'.ui.json').read_text(encoding='utf8'))))
    if require_ordinary_spellbooks:
        checks.append(dict(name='ordinary-spellbooks.heading-coverage',
            passed=set(ordinary_spellbooks) == {'mage-book','priest-book'}))
    for action, pack, nameid, hpid, thacid in (
            ("inventory.observed", "GUIINV", 0x10000032, 0x10000039, 0x10000055),
            ("record.observed", "GUIREC", 0x1000000e, 0x10000029, 0x10000040)):
        row = next(row for row in runtime["checks"] if row.get("action") == action)
        prefix = directory / ("capture-%d" % row["capture"])
        state = json.loads(Path(str(prefix) + ".state.json").read_text(encoding="utf8"))
        observer = json.loads(Path(str(prefix) + ".observer.json").read_text(encoding="utf8"))
        ui = json.loads(Path(str(prefix) + ".ui.json").read_text(encoding="utf8"))
        pc = state["selection"]
        actor = state["party"][pc - 1]
        native = next(actor for actor in observer["actors"] if actor["party_index"] == pc)
        def text(cid):
            found = [item for item in ui["controls"] if item["pack"] == pack and item["window"] == 2 and item["id"] == cid]
            if len(found) != 1 or not found[0]["visible"]:
                raise ValueError("Missing/ambiguous visible sheet field")
            return found[0]["text"]
        checks.extend([
            dict(name=action + ".native-name", passed=text(nameid) == actor["name"]),
            dict(name=action + ".native-hp", passed=text(hpid) == str(actor["modified_stats"][0])),
            dict(name=action + ".native-cached-thac0", passed=text(thacid).split("/")[0] == str(native["cached_thac0"]))])
    before = json.loads((directory / "before.state.json").read_text(encoding="utf8"))
    after = json.loads((directory / "after.state.json").read_text(encoding="utf8"))
    # UI selection is explicitly changed by the test. Preserve all remaining raw
    # fields/differences; no blanket effect/time/global normalization is allowed.
    before.pop("selection", None)
    after.pop("selection", None)
    return dict(checks=checks, assertion_passed=all(row["passed"] for row in checks),
                collected_world_unchanged=before == after, captures=len(ids),
                context_required=runtime["context_required"], visual_acceptance=False,
                applicability=[row for row in runtime['checks'] if 'applicable' in row],
                per_label_font_color_alignment_observed=False,
                ordinary_spellbook_heading_coverage=ordinary_spellbooks,
                ordinary_spellbook_heading_coverage_complete=set(ordinary_spellbooks) == {'mage-book','priest-book'},
                font_provenance_scope='Separate fonts.json provider/metric validation; role presence does not prove label assignment',
                pointer_hit_testing=False, hidden_rng_unchanged=None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "run"))
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--game", type=Path)
    parser.add_argument("--resolutions", default="1024x768,1280x960")
    parser.add_argument("--timeout", type=int, default=330)
    parser.add_argument("--require-ordinary-spellbooks", action='store_true',
                        help='Require eligible ordinary wizard and priest heading evidence; context gating is not heading acceptance')
    parser.add_argument('--journey', choices=('menus', 'stats'), default='menus')
    args = parser.parse_args()
    if args.journey == 'stats' and args.require_ordinary_spellbooks:
        parser.error('Stats journey does not validate ordinary spellbooks')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = args.output_root / (stamp + "-menu-" + args.mode + "-" + uuid.uuid4().hex[:8])
    directory.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PATH"] = os.pathsep.join([str(args.prefix / "bin"), str(args.build / "gemrb"), env.get("PATH", "")])
    dll = args.build / "gemrb/libgemrb_core.dll"
    identities, frozen_sources = freeze_source_inputs(menu_source_inputs(args.source), directory)
    receipt = dict(schema="bg-redux-menu-run/1", source_files=identities, engine_dll_sha256=sha(dll),
                   frozen_sources=frozen_sources, require_ordinary_spellbooks=args.require_ordinary_spellbooks,
                   directory=str(directory), stages=[], font_mode="game-resources-no-override", journey=args.journey)
    write(directory / "preparation.json", receipt)
    if args.mode == "build":
        receipt["compiler_sha256"] = sha(args.prefix / "bin/g++.exe")
        receipt["import_library_sha256"] = sha(args.build / "gemrb/core/libgemrb_core.dll.a")
        command = [str(args.prefix / "bin/g++.exe"), "-std=gnu++17", "-g", "-O0", "-DHAVE_CONFIG_H",
                   "-DUSE_OPENGL_API", "-D_USE_MATH_DEFINES", "-DFMT_HEADER_ONLY", "-DFMT_USE_CONSTEVAL=0",
                   "-DFMT_EXCEPTIONS=0", "-DFMT_UNICODE=1", "-fno-strict-aliasing"]
        for inc in (args.build, args.source / "gemrb/includes", args.source / "gemrb/core",
                    args.source / "platforms/Windows", args.build / "gemrb/includes", args.prefix / "include/SDL2",
                    args.prefix / "include/python3.14", args.source / "gemrb/includes/fmt"):
            command += ["-I", str(inc)]
        binary = directory / "Redux_menu_probe.exe"
        command += [str(HERE / "menu_probe.cpp"), str(args.build / "gemrb/core/libgemrb_core.dll.a"),
                    str(args.prefix / "lib/libiconv.dll.a"), "-lshlwapi", "-o", str(binary)]
        receipt["process"] = run_owned(command, args.build, env, directory / "build.log", args.timeout)
        receipt["binary_sha256"] = sha(binary) if binary.is_file() else None
        receipt["binary"] = str(binary)
        receipt["passed"] = receipt["process"]["exit_code"] == 0 and bool(receipt["binary_sha256"])
    else:
        if not args.probe or not args.fixture or not args.game:
            parser.error("run requires --probe, --fixture and --game")
        original = manifest(args.fixture)
        if not original or not any(p.lower() == "baldur.gam" for p in original):
            raise ValueError("Required private save fixture missing")
        receipt["probe_sha256"] = sha(args.probe)
        receipt["fixture_manifest"] = original
        for size in args.resolutions.split(","):
            width, height = (int(x) for x in size.split("x"))
            if width < 800 or height < 600:
                raise ValueError("Resolution below the declared UI baseline")
            stage = directory / size
            stage.mkdir()
            profile = stage / "profile"
            copied = profile / "save/000000007-HarnessInput"
            shutil.copytree(args.fixture, copied)
            private = private_game.prepare(args.game, stage / 'game')
            write(stage / 'private-game-preparation.json', private)
            (stage / "cache").mkdir()
            config = dict(GameType="bg2ee", GameName="BG Redux menu fidelity " + directory.name,
                GamePath=stage / 'game', GemRBPath=args.source / "gemrb", GUIScriptsPath=args.source / "gemrb",
                GemRBOverridePath=args.source / "gemrb", GemRBUnhardcodedPath=args.source / "gemrb",
                PluginsPath=args.build / "gemrb/plugins", CachePath=stage / "cache", SavePath=profile,
                UseAsLibrary=0, Width=width, Height=height, FullScreen=0, CapFPS=30, AudioDriver="none",
                GameLanguagePath="lang/en_US", SkipIntroVideos=1, Logging=1, LogColor=0,
                PathfinderThreadsCount=0, PathfinderMainThreadMode="immediate")
            cfg = stage / "menu.cfg"
            cfg.write_text("".join("%s=%s\n" % (key, str(value).replace("\\", "/")) for key, value in config.items()), encoding="utf8")
            config_before = sha(cfg)
            stage_nonce = uuid.uuid4().hex
            command = [str(args.probe), "--config", str(cfg), "--output", str(stage), "--scripts", str(HERE / "gui"),
                       "--nonce", stage_nonce]
            if args.journey == 'stats':
                command += ['--journey', 'stats']
            # Freeze identity before the owned process can produce evidence.
            write(stage / 'launch-pin.json', dict(schema='bg-redux-menu-launch-pin/1',
                  nonce=stage_nonce, resolution=[width, height], command=command,
                  require_ordinary_spellbooks=args.require_ordinary_spellbooks,
                  config_sha256=config_before, probe_sha256=receipt['probe_sha256']))
            stage_env = env.copy()
            stage_env.update(HOME=str(profile), USERPROFILE=str(profile), APPDATA=str(profile / "AppData/Roaming"))
            row = dict(resolution=[width, height], expected_nonce=stage_nonce,
                       process=run_owned(command, args.build, stage_env, stage / "process.log", args.timeout))
            row.update(config_sha256_before=config_before, config_sha256_after=sha(cfg))
            try:
                row['private_game_validation'] = private_game.validate(private)
            except (ValueError, OSError) as error:
                row['private_game_error'] = str(error)
            try:
                if args.journey == 'stats':
                    row['validation'] = stats_validation.validate_stage(stage, (width, height),
                        expected_nonce=stage_nonce, tlk_path=args.game/'lang/en_US/dialog.tlk')
                else:
                    row["validation"] = validate_stage(stage, (width, height), expected_nonce=stage_nonce,
                                                       require_ordinary_spellbooks=args.require_ordinary_spellbooks)
            except (ValueError, OSError, KeyError, IndexError, TypeError, StopIteration) as error:
                row["error"] = str(error)
            row["fixture_copy_unchanged"] = manifest(copied) == original
            row["passed"] = row["process"]["exit_code"] == 0 and not row["process"]["timed_out"] and row["fixture_copy_unchanged"] and not row.get('private_game_error') and row.get("validation", {}).get("assertion_passed", False) and row.get("validation", {}).get("collected_world_unchanged", False)
            write(stage / "result.json", row)
            receipt["stages"].append(row)
        receipt["original_fixture_unchanged"] = manifest(args.fixture) == original
        receipt["passed"] = receipt["original_fixture_unchanged"] and all(row["passed"] for row in receipt["stages"])
    receipt["engine_dll_unchanged"] = sha(dll) == receipt["engine_dll_sha256"]
    receipt["source_inputs_unchanged"] = all(sha(Path(path)) == expected for path, expected in identities.items())
    receipt["frozen_sources_unchanged"] = all(sha(row['frozen']) == row['sha256'] for row in frozen_sources.values())
    receipt["passed"] = receipt["passed"] and receipt["engine_dll_unchanged"] and receipt["source_inputs_unchanged"] and receipt["frozen_sources_unchanged"]
    write(directory / "result.json", receipt)
    write(directory / "artifact-manifest.json", artifact_manifest(directory))
    print(directory)
    return 0 if receipt["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
