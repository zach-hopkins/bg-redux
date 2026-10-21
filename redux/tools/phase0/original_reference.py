"""Freeze and compare externally created original BG2EE reload/resave references.

No game is launched or controlled. Missing reference saves return pending/exit2;
absence of EEex markers alone is never a claim of clean execution provenance.
"""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import struct
import uuid
import zlib

from harness import ROOT,LOCAL,digest
from effect_cycle import wire_target,summarize_effects
from save_harness import manifest,write,validate_fixture

PROFILE=Path("C:/Users/zach/Documents/Baldur's Gate II - Enhanced Edition/save")

def locate(profile,slotname):
    found=[p for p in profile.iterdir() if p.is_dir() and p.name.lower().endswith('-'+slotname.lower())] if profile.is_dir() else []
    if len(found)>1:raise ValueError('Ambiguous original reference: '+slotname)
    return found[0] if found else None

def classify(counts):
    if len(counts)!=3 or counts[0]!=7:raise ValueError('Expected baseline plus two reference observations')
    if counts==[7,7,7]:return 'reference-record-count-stable'
    if counts==[7,14,21]:return 'reference-also-grows-seven'
    return 'reference-different-progression'

def observed_receipt(path,exe,first,second):
    """Bind an operator observation to these exact files; not runtime instrumentation."""
    receipt=json.loads(path.read_text(encoding='utf-8'))
    if receipt.get('schema')!='bg-redux-original-ui-observation/1':raise ValueError('Unsupported execution receipt')
    if receipt.get('executable_sha256')!=digest(exe):raise ValueError('Observed executable hash drift')
    if Path(receipt['executable']).resolve()!=exe.resolve():raise ValueError('Observed executable path mismatch')
    if receipt.get('sequence_completed') is not True:raise ValueError('Incomplete observed sequence')
    for label,source in [('reload1',first),('reload2',second)]:
        if receipt['saves'][label]['files']!=manifest(source):raise ValueError('Observed save manifest mismatch: '+label)
    return receipt

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,default=PROFILE)
    parser.add_argument('--first',type=Path)
    parser.add_argument('--second',type=Path)
    parser.add_argument('--execution-receipt',type=Path,help='Operator-authored computer-use observation bound to executable and save hashes; not a runtime attestation')
    parser.add_argument('--gemrb-evidence',type=Path,help='Optional existing lifecycle evidence; compare counts and full reported signatures separately')
    parser.add_argument('--human-confirmed-clean',action='store_true',help='Record the user confirmation of clean original execution; not an automated certificate')
    args=parser.parse_args(argv)
    output=LOCAL/'results'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-original-reference-'+uuid.uuid4().hex[:8]);output.mkdir()
    result=dict(schema='bg-redux-original-reference/1',directory=str(output),observations=[],
        provenance=dict(execution='User-mediated load/save via requested clean Steam BG2EE; not observed by this tool',
                        human_confirmation_recorded=args.human_confirmed_clean,
                        marker_absence_is_not_clean_certificate=True))
    try:
        first=args.first or locate(args.profile,'Redux EE Reload 1')
        second=args.second or locate(args.profile,'Redux EE Reload 2')
        missing=[name for name,path in [('Redux EE Reload 1',first),('Redux EE Reload 2',second)] if path is None or not path.is_dir()]
        if missing:
            result.update(verdict='pending-reference',missing=missing,
                requested_action='Clean BG2EE: load GemRB, Save As Redux EE Reload 1, load that save, Save As Redux EE Reload 2. Keep paused and avoid gameplay.')
        else:
            original=LOCAL/'fixtures/original-bg2ee-20261020/GemRB'
            pinned=json.loads((ROOT/'docs/compatibility/evidence/vanilla-save-fixture.json').read_text())
            if manifest(original)!=pinned['files']:raise ValueError('Pinned original baseline drift')
            for label,source in [('baseline',original),('reload1',first),('reload2',second)]:
                validate_fixture(source);before=manifest(source)
                copied=output/label;shutil.copytree(source,copied)
                if manifest(source)!=before or manifest(copied)!=before:raise ValueError('Reference changed during copy')
                gam=next(p for p in copied.iterdir() if p.name.lower()=='baldur.gam')
                if b'EEex' in gam.read_bytes():raise ValueError('EEex marker present; refusing clean reference designation')
                actor=wire_target(copied)
                result['observations'].append(dict(label=label,source=str(source),files=before,
                    cre_bytes=actor['cre_bytes'],cre_sha256=actor['cre_sha256'],immcloud=summarize_effects(actor['effects'])))
            counts=[o['immcloud']['total'] for o in result['observations']]
            result['progression']=counts
            result['classification']=classify(counts)
            exe=Path("C:/Program Files (x86)/Steam/steamapps/common/Baldur's Gate II Enhanced Edition/Baldur.exe")
            observed=observed_receipt(args.execution_receipt,exe,first,second) if args.execution_receipt else None
            if observed:
                result['provenance'].update(execution='Computer-use operator observed clean Steam path launch and ordinary load/save sequence',
                    operator_observation=observed,receipt_sha256=digest(args.execution_receipt),
                    limitation='Operator-authored observation and file binding; no process/module attestation or continuous clock control')
            result['nominated_executable']=dict(path=str(exe),sha256=digest(exe),actual_launch_observed=bool(observed))
            result['verdict']='reference-observed' if observed or args.human_confirmed_clean else 'reference-provenance-unconfirmed'
            result['interpretation_limit']='Selected saved effect records only; no combat or complete runtime equivalence certification.'
            if args.gemrb_evidence:
                gemrb=json.loads(args.gemrb_evidence.read_text(encoding='utf-8'))
                stages=gemrb['conditions']['stock']
                if len(stages)<2:raise ValueError('Two GemRB comparison cycles required')
                result['gemrb_comparison']=dict(evidence_sha256=digest(args.gemrb_evidence),directory=gemrb['directory'],cycles=[])
                for index,stage in enumerate(stages[:2],1):
                    original=result['observations'][index]['immcloud'];other=stage['output_wire']
                    result['gemrb_comparison']['cycles'].append(dict(cycle=index,original=original,gemrb=other,
                        counts_equal=original['total']==other['total'],signatures_equal=original['signatures']==other['signatures']))
    except (OSError,ValueError,KeyError,struct.error,zlib.error) as error:
        result.update(verdict='failed',error=str(error))
    result['tool_sources']={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'tools/phase0/effect_cycle.py']}
    write(output/'result.json',result)
    write(ROOT/'docs/compatibility/evidence/original-reference-status.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['observations','tool_sources']},indent=2))
    return 0 if result['verdict']=='reference-observed' else (2 if result['verdict'].startswith(('pending','reference-provenance')) else 1)

if __name__=='__main__':raise SystemExit(main())
