"""Full-loop stock GUI load, presentation, create/cancel/overwrite and reload probe.

Owns a fresh test process/profile, never attaches to a player's session. Semantic
callbacks bypass pointer hit testing; screenshots come from the engine buffer.
"""
from __future__ import annotations
import argparse
import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import uuid

from harness import ROOT, LOCAL, BUILD, digest, environment, run_process
from save_harness import manifest, validate_fixture, write, normalize, differences, comparison_scopes
from gui_comparison import compare as compare_legacy

PROBE = LOCAL/'gui-probe/Redux_gui_probe.exe'
SCRIPTS = ROOT/'tools/phase0/gui'

def ui_control(ui, pack, window, cid):
    rows = [c for c in ui['controls'] if c['pack']==pack and c['window']==window and c['id']==cid]
    if len(rows)!=1: raise ValueError(f'Required unique control absent: {pack}/{window}/{cid}')
    return rows[0]

def check_ui(directory):
    """Content assertions do not certify visible pixels or font correctness."""
    state=json.loads((directory/'00-game.state.json').read_text(encoding='utf-8'))
    inv=json.loads((directory/'01-inventory.ui.json').read_text(encoding='utf-8'))
    rec=json.loads((directory/'02-record.ui.json').read_text(encoding='utf-8'))
    checks=[]
    def check(name, actual, expected):
        checks.append(dict(name=name, actual=actual,expected=expected,passed=actual==expected))
    check('area',state['current_area'].upper(),'AR0602')
    check('party-size',len(state['party']),2)
    check('inventory-name',ui_control(inv,'GUIINV',2,0x10000032)['text'],state['party'][0]['name'])
    check('record-name',ui_control(rec,'GUIREC',2,0x1000000e)['text'],state['party'][0]['name'])
    check('inventory-hp-populated',bool(ui_control(inv,'GUIINV',2,0x10000039)['text']),True)
    check('record-overview-populated',bool(ui_control(rec,'GUIREC',2,45)['text']),True)
    check('inventory-visible',ui_control(inv,'GUIINV',2,0x10000032)['visible'],True)
    return checks

def font_override(directory, mode):
    if mode=='stock': return None
    override=directory/'mod'
    override.mkdir()
    source=(ROOT/'gemrb/gemrb/unhardcoded/bg2ee/fonts.2da').read_text(encoding='utf-8')
    lines=[]
    for line in source.splitlines():
        columns=line.split()
        if len(columns)==7 and columns[0].isdigit() and columns[1] not in ('STATES','STATES2'):
            if mode=='bam': columns[6]='1'
            elif mode=='ttf-18': columns[3]='18'
            line='  '.join(columns)
        lines.append(line)
    (override/'fonts.2da').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return override

def stage(output, name, fixture, mode, font_mode, timeout, debug=False):
    directory=output/name
    directory.mkdir()
    profile=directory/'engine-profile'
    (profile/'save').mkdir(parents=True)
    copied=profile/'save/000000007-HarnessInput'
    shutil.copytree(fixture,copied)
    before=manifest(copied)
    cache=directory/'cache'
    cache.mkdir()
    config=dict(GameType='bg2ee', GameName='BG Redux Phase 0 GUI probe', GamePath=LOCAL/'bg2ee-clean',
        GemRBPath=ROOT/'gemrb/gemrb', GUIScriptsPath=ROOT/'gemrb/gemrb',
        GemRBOverridePath=ROOT/'gemrb/gemrb', GemRBUnhardcodedPath=ROOT/'gemrb/gemrb',
        PluginsPath=BUILD/'gemrb/plugins',CachePath=cache,SavePath=profile,UseAsLibrary=0,
        Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',
        GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,
        PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
    override=font_override(directory,font_mode)
    if override: config['ModPath']=override
    config_path=directory/'gui.cfg'
    config_path.write_text(''.join(f'{k}={str(v).replace(chr(92),chr(47))}\n' for k,v in config.items()),encoding='utf-8')
    command=[str(PROBE),'--config',str(config_path),'--output',str(directory),'--scripts',str(SCRIPTS),'--mode',mode]
    if debug:
        command=[str(LOCAL/'toolchain/msys64/ucrt64/bin/gdb.exe'),'-q','-batch',
                 '-ex','set pagination off','-ex','run','-ex','thread apply all bt','--args']+command
    # This build's shaders are relative to the build root, as in launch.py.
    process=run_process(command,BUILD,environment(directory),directory/'process.log',timeout)
    result=dict(name=name,mode=mode,font_mode=font_mode,command=command,process=process,
        fixture_copy_unchanged=manifest(copied)==before,config_sha256=digest(config_path),
        font_override_sha256=digest(override/'fonts.2da') if override else None, assertions=[])
    try:
        if process['exit_code']!=0 or process['timed_out']: raise ValueError('GUI process did not exit successfully')
        result['native']=json.loads((directory/'gui-result.json').read_text(encoding='utf-8'))
        if not result['native']['completed']: raise ValueError('GUI stages incomplete')
        result['assertions']=check_ui(directory)
        if mode=='save':
            events=result['native']['events']
            for required in ['press:load.baseline-row','guard:empty-name-refused','press:save.create-confirm',
                             'press:overwrite.cancel','press:overwrite.confirm']:
                result['assertions'].append(dict(name=required,passed=required in events))
            result['assertions'].append(dict(name='cancel-keeps-save-bytes',
                passed=manifest(directory/'checkpoint-create')==manifest(directory/'checkpoint-cancel')))
            created=[p for p in (profile/'save').iterdir() if p.is_dir() and p.name.endswith('-Redux GUI Baseline')]
            if len(created)!=1: raise ValueError('GUI-created save folder absent/ambiguous')
            validate_fixture(created[0])
            # A valid preview is necessary for the ordinary save picker.
            import struct
            bmp=(created[0]/'BALDUR.bmp')
            if not bmp.exists(): bmp=next(p for p in created[0].iterdir() if p.name.lower()=='baldur.bmp')
            header=bmp.read_bytes()
            if header[:2]!=b'BM' or len(header)<54: raise ValueError('Invalid GUI preview')
            width,height=struct.unpack_from('<ii',header,18)
            result['created_save']=dict(path=str(created[0]),manifest=manifest(created[0]),preview_size=[width,height])
        result['passed']=result['fixture_copy_unchanged'] and all(c['passed'] for c in result['assertions'])
    except (OSError,ValueError,KeyError,StopIteration) as error:
        result['passed']=False
        result['error']=str(error)
    native_error=directory/'error.json'
    if native_error.exists(): result['native_error']=json.loads(native_error.read_text(encoding='utf-8'))
    write(directory/'process-result.json',result)
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['gui'])
    parser.add_argument('--font-mode',choices=['stock','bam','ttf-18'],default='stock')
    parser.add_argument('--timeout',type=float,default=100)
    parser.add_argument('--name',default='gui-baseline')
    parser.add_argument('--fixture',default='original-vanilla',choices=['original-vanilla','missing-negative'])
    parser.add_argument('--debug',action='store_true',help='Collect native crash stacks with GDB')
    parser.add_argument('--screens-only',action='store_true',help='Load and capture inventory/record; no save or reload test')
    args=parser.parse_args(argv)
    if args.timeout<=0 or not re.fullmatch(r'[a-zA-Z0-9_-]+',args.name): parser.error('Positive timeout/simple name required')
    run_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+args.name+'-'+uuid.uuid4().hex[:8]
    output=LOCAL/'results'/run_id
    output.mkdir(parents=True)
    result=dict(schema='bg-redux-gui-run/1',run_id=run_id,font_mode=args.font_mode,stages=[],assertions=[],
                coverage='Stock GUI load/save callbacks and full render loop; no pointer hit-testing or visual parity certification')
    result['screens_only']=args.screens_only
    if args.screens_only: result['coverage']='Stock GUI load and inventory/record capture only; saving and visual parity are not tested'
    fixture=LOCAL/'fixtures/original-bg2ee-20261020/GemRB'
    if args.fixture=='missing-negative': fixture=output/'missing-fixture'
    try:
        receipt=json.loads((PROBE.parent/'build.json').read_text(encoding='utf-8'))
        if receipt['exit_code']!=0 or receipt['binary_sha256']!=digest(PROBE) or receipt['engine_dll_sha256']!=digest(BUILD/'gemrb/libgemrb_core.dll'):
            raise ValueError('Probe binary or engine provenance drift; rebuild the external host')
        for path, sha in receipt['sources'].items():
            if digest(ROOT/path)!=sha: raise ValueError('Probe source drift; rebuild external host')
        validate_fixture(fixture)
        before=manifest(fixture)
        pinned=json.loads((ROOT/'docs/compatibility/evidence/vanilla-save-fixture.json').read_text(encoding='utf-8'))
        # Same pinned fixture validation as the library probe, including original bytes.
        if before!=pinned['files']: raise ValueError('Pinned vanilla fixture hash mismatch')
        result['provenance']=dict(build=receipt,startup_sha256=digest(SCRIPTS/'ReduxStart.py'),
            source_revision=subprocess.check_output(['git','-C',str(ROOT/'gemrb'),'rev-parse','HEAD'],text=True).strip(),
            tool_files={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),Path(__file__).with_name('gui_comparison.py'),Path(__file__).with_name('harness.py')]},
            plugins={p.name:digest(p) for p in sorted((BUILD/'gemrb/plugins').glob('*.dll'))},
            gui_scripts={str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'gemrb/gemrb/GUIScripts/GUISAVE.py',
                ROOT/'gemrb/gemrb/GUIScripts/GUILOAD.py',ROOT/'gemrb/gemrb/GUIScripts/bg2/GUIINV.py',
                ROOT/'gemrb/gemrb/GUIScripts/GUIREC.py',ROOT/'gemrb/gemrb/GUIScripts/bg2/Game.py']},fixture=before)
        first=stage(output,'gui-save',fixture,'inspect' if args.screens_only else 'save',args.font_mode,args.timeout,args.debug)
        result['stages'].append(first)
        if first['passed'] and not args.screens_only:
            created=Path(first['created_save']['path'])
            created_before=manifest(created)
            second=stage(output,'gui-reload',created,'inspect',args.font_mode,args.timeout,args.debug)
            result['stages'].append(second)
            result['created_save_unchanged_on_reload']=manifest(created)==created_before
            if second['passed']:
                a=json.loads((output/'gui-save/overwrite-persisted.state.json').read_text(encoding='utf-8'))
                b=json.loads((output/'gui-reload/00-game.state.json').read_text(encoding='utf-8'))
                diff=differences(normalize(a),normalize(b))
                write(output/'gui-reload-differences.json',diff)
                result['persistence']=dict(differences=len(diff),scopes=comparison_scopes(a,b),passed=not diff)
                result['legacy_semantic_diagnostic'],legacy_diff=compare_legacy(a,b)
                write(output/'legacy-semantic-differences.json',legacy_diff)
        result['fixture_unchanged']=manifest(fixture)==before
        expected_stages=1 if args.screens_only else 2
        result['execution_verdict']='passed' if len(result['stages'])==expected_stages and all(s['process']['exit_code']==0 and not s['process']['timed_out'] and s.get('native',{}).get('completed') for s in result['stages']) else 'failed'
        result['assertion_verdict']='passed' if len(result['stages'])==expected_stages and all(s['passed'] for s in result['stages']) else 'failed'
        save_ok=args.screens_only or (result.get('persistence',{}).get('passed') and result.get('created_save_unchanged_on_reload'))
        if any(s['process']['timed_out'] for s in result['stages']): result['verdict']='timeout'
        elif result['execution_verdict']!='passed' or result['assertion_verdict']!='passed': result['verdict']='failed'
        else: result['verdict']='passed' if save_ok and result['fixture_unchanged'] else 'differences'
    except (OSError,ValueError,KeyError) as error:
        result['verdict']='failed'
        result['error']=str(error)
    result['artifacts']=str(output)
    write(output/'result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['provenance','stages']},indent=2))
    for s in result['stages']: print(json.dumps({k:s[k] for k in ('name','passed','process','error','native_error') if k in s}))
    return 0 if result['verdict']=='passed' else 1

if __name__=='__main__': raise SystemExit(main())
