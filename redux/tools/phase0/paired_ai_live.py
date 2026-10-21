"""Run the exact private original-live AI fixtures in the unchanged native host."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import shutil
import uuid

from harness import ROOT, LOCAL, BUILD, environment, run_process, digest
from save_harness import manifest, write
from baseline_runner import preflight, protected, check_build
from ai_fallback import completed_ai


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation',type=Path,required=True)
    args=parser.parse_args()
    prep=json.loads(args.preparation.read_text(encoding='utf-8'))
    out=LOCAL/'results'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-paired-ai-live-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    result=dict(schema='bg-redux-paired-ai-live-native/1',directory=str(out),cases=[],verdict='failed',
                preparation=str(args.preparation),preparation_sha256=digest(args.preparation))
    before=None
    try:
        result['preflight']=preflight(ROOT); before=protected(ROOT);write(out/'protected-before.json',before)
        game=Path(prep['game'])
        if digest(game/'Baldur.exe')!=prep['executable_sha256'] or digest(game/'lang/en_US/dialog.tlk')!=prep['private_tlk_sha256']:
            raise ValueError('Private original game identity/TLK drift')
        driver=check_build(ROOT,'gui');shutil.copytree(driver,out/'driver')
        shutil.copy2(args.preparation,out/'preparation.json')
        for name in ['paired_ai_live.py','ai_fallback.py','harness.py','baseline_runner.py']:
            dest=out/'tool-source'/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/'tools/phase0'/name,dest)
        for row in prep['cases']:
            spec=row['spec'];case=dict(id=spec['id'],verdict='failed');result['cases'].append(case)
            folder=out/spec['id'];folder.mkdir()
            try:
                fixture=Path(row['fixture']);script=game/'override'/(row['script']+'.bcs')
                if manifest(fixture)!=row['fixture_files'] or digest(script)!=row['script_sha256']:
                    raise ValueError('Paired input/script drift')
                profile=folder/'engine-profile';(profile/'save').mkdir(parents=True)
                copied=profile/'save/000000007-HarnessInput';shutil.copytree(fixture,copied)
                (folder/'cache').mkdir()
                config=dict(GameType='bg2ee',GameName='LAB paired original AI fixture',GamePath=game,
                            GemRBPath=ROOT/'gemrb/gemrb',GUIScriptsPath=ROOT/'gemrb/gemrb',
                            GemRBOverridePath=ROOT/'gemrb/gemrb',GemRBUnhardcodedPath=ROOT/'gemrb/gemrb',
                            PluginsPath=BUILD/'gemrb/plugins',CachePath=folder/'cache',SavePath=profile,
                            UseAsLibrary=0,Width=1024,Height=768,FullScreen=0,CapFPS=30,AudioDriver='none',
                            GameLanguagePath='lang/en_US',SkipIntroVideos=1,Logging=1,LogColor=0,
                            PathfinderThreadsCount=0,PathfinderMainThreadMode='immediate')
                cfg=folder/'probe.cfg';cfg.write_text(''.join(f'{k}={str(v).replace(chr(92),chr(47))}\n' for k,v in config.items()),encoding='utf-8')
                command=[str(out/'driver/Redux_gui_probe.exe'),'--config',str(cfg),'--output',str(folder),
                         '--scripts',str(ROOT/'tools/phase0/gui'),'--mode','live-clock',
                         '--clock-running-samples','80','--trace-actions','1']
                env=environment(folder);env['PYTHONDONTWRITEBYTECODE']='1'
                case['process']=run_process(command,BUILD,env,folder/'process.log',90)
                case['command']=command;case['input_files']=manifest(copied);case['script_sha256']=digest(script)
                shutil.copy2(script,folder/script.name)
                if case['process']['exit_code']!=0 or case['process']['timed_out']:
                    raise ValueError('Paired native process failed or timed out')
                if json.loads((folder/'gui-result.json').read_text())['completed'] is not True:
                    raise ValueError('Normal-loop samples incomplete')
                case['observation']=completed_ai(folder,spec)
                case['input_unchanged']=manifest(fixture)==row['fixture_files'] and manifest(copied)==row['fixture_files']
                if not case['input_unchanged']:raise ValueError('Input changed during paired run')
                case['verdict']='native-ai-observed'
            except (OSError,ValueError,KeyError,TypeError) as error:
                case['error']=str(error)
            write(folder/'result.json',case);write(out/'result.json',result)
            print(case['id'],case['verdict'],case.get('error',''),flush=True)
        if len(result['cases'])==4 and all(c['verdict']=='native-ai-observed' for c in result['cases']):
            result['verdict']='four-native-paired-input-cases-observed'
    except (OSError,ValueError,KeyError,TypeError) as error:result['error']=str(error)
    finally:
        if before:
            after=protected(ROOT);write(out/'protected-after.json',after)
            result['preservation']={k:before[k]==after[k] for k in before}
            if not all(result['preservation'].values()):result['verdict']='failed'
        result['scope']='Identical final fixture/script/TLK inputs to original-live capture. Native action/target samples are separate from original visual branch/combat attestations. No full-AI, DPR, timing or hidden-state parity claim.'
        write(out/'result.json',result)
    print(json.dumps(dict(directory=str(out),verdict=result['verdict']),indent=2))
    return 0 if result['verdict']=='four-native-paired-input-cases-observed' else 1


if __name__=='__main__':raise SystemExit(main())
