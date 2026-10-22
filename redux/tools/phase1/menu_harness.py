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


def validate_stage(directory, resolution=None):
    """Fail incomplete/missing evidence; never turn screenshots into visual QA."""
    directory = Path(directory)
    host = json.loads((directory / "menu-host-result.json").read_text(encoding="utf8"))
    runtime = json.loads((directory / "menu-runtime.json").read_text(encoding="utf8"))
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
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = args.output_root / (stamp + "-menu-" + args.mode + "-" + uuid.uuid4().hex[:8])
    directory.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([str(args.prefix / "bin"), str(args.build / "gemrb"), env.get("PATH", "")])
    dll = args.build / "gemrb/libgemrb_core.dll"
    source_files = [HERE / "menu_probe.cpp", HERE / "gui/MenuRuntime.py", HERE / "gui/MenuStart.py",
                    HERE / "private_game.py",
                    HERE / "../phase0/native/gui_probe.cpp", HERE / "../phase0/native/save_probe.cpp"]
    identities = {str(p.resolve()): sha(p) for p in source_files}
    receipt = dict(schema="bg-redux-menu-run/1", source_files=identities, engine_dll_sha256=sha(dll),
                   directory=str(directory), stages=[], font_mode="game-resources-no-override")
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
            command = [str(args.probe), "--config", str(cfg), "--output", str(stage), "--scripts", str(HERE / "gui")]
            stage_env = env.copy()
            stage_env.update(HOME=str(profile), USERPROFILE=str(profile), APPDATA=str(profile / "AppData/Roaming"))
            row = dict(resolution=[width, height], process=run_owned(command, args.build, stage_env, stage / "process.log", args.timeout))
            row.update(config_sha256_before=config_before, config_sha256_after=sha(cfg))
            try:
                row['private_game_validation'] = private_game.validate(private)
            except (ValueError, OSError) as error:
                row['private_game_error'] = str(error)
            try:
                row["validation"] = validate_stage(stage, (width, height))
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
    receipt["passed"] = receipt["passed"] and receipt["engine_dll_unchanged"] and receipt["source_inputs_unchanged"]
    write(directory / "result.json", receipt)
    write(directory / "artifact-manifest.json", artifact_manifest(directory))
    print(directory)
    return 0 if receipt["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
