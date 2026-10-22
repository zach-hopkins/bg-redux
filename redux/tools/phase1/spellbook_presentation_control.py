"""Declared private SpellName-only presentation control; never changes clean assets."""
import copy
from pathlib import Path
import struct
import weapon_query_validation as evidence
PAIRS=(('SPWI213.spl','SPWI211.spl'),('SPPR113.spl','SPPR111.spl'))
CONTROL='spellname-permutation'

def exchange(originals):
    if set(originals)!={name for pair in PAIRS for name in pair}:raise ValueError('Exact four original SPLs required')
    changed={}
    for left,right in PAIRS:
        a,b=originals[left],originals[right]
        for raw in (a,b):
            if len(raw)<12 or raw[:8]not in (b'SPL V1  ',b'SPL V2.0'):raise ValueError('Supported complete SPL header required')
        if a[8:12]==b[8:12]:raise ValueError('Permutation requires distinct original SpellName refs')
        changed[left]=a[:8]+b[8:12]+a[12:];changed[right]=b[:8]+a[8:12]+b[12:]
    for name,raw in changed.items():field_guard(originals[name],raw)
    return changed

def field_guard(original,override):
    if len(original)!=len(override)or original[:8]!=override[:8]or original[12:]!=override[12:]or original[8:12]==override[8:12]:raise ValueError('Override must change only the SpellName field [8:12]')

def prepare(receipt,override_dir):
    """Use frozen build inputs, never current clean-game data or a modified TLK."""
    override_dir=Path(override_dir)
    if any(override_dir.iterdir()):raise ValueError('Fresh empty private override required')
    originals={}
    for name in (n for pair in PAIRS for n in pair):
        row=receipt['resources'][name];file=Path(row['frozen']);raw=file.read_bytes()
        if evidence.sha(file)!=row['sha256']or len(raw)!=row['bytes']or struct.unpack_from('<I',raw,8)[0]!=row['spell_name_ref']:raise ValueError('Frozen original SPL drift')
        originals[name]=raw
    changed=exchange(originals);resources=copy.deepcopy(receipt['resources']);proof=[]
    for left,right in PAIRS:
        for name,donor in ((left,right),(right,left)):
            raw=changed[name];file=override_dir/name;file.write_bytes(raw);old=receipt['resources'][name];source=receipt['resources'][donor]
            resources[name].update(provider=str(file.resolve()),provider_sha256=evidence.sha(file),sha256=evidence.sha(file),bytes=len(raw),origin=str(file.resolve()),frozen=str(file.resolve()),spell_name_ref=source['spell_name_ref'],spell_name=source['spell_name'])
            proof.append(dict(resref=name[:-4],original_provider=old['provider'],original_provider_sha256=old['provider_sha256'],original_frozen=old['frozen'],original_sha256=old['sha256'],override_provider=str(file.resolve()),override_sha256=evidence.sha(file),bytes=len(raw),allowed_field=[8,12],changed_offsets=[i for i,(a,b)in enumerate(zip(originals[name],raw))if a!=b],original_name_ref=old['spell_name_ref'],override_name_ref=source['spell_name_ref'],original_name=old['spell_name'],override_name=source['spell_name']))
    return dict(control=CONTROL,tlk=copy.deepcopy(receipt['resources']['tlk']),proof=proof,resources=resources,original_parity=None)

def verify(control,receipt):
    expected={n for pair in PAIRS for n in pair}
    if control.get('control')!=CONTROL or {row['resref']+'.spl'for row in control['proof']}!=expected or len(control['proof'])!=4 or control['tlk']!=receipt['resources']['tlk']:raise ValueError('Control provenance/coverage differs')
    originals={name:Path(receipt['resources'][name]['frozen']).read_bytes()for name in expected};desired=exchange(originals)
    for row in control['proof']:
        name=row['resref']+'.spl';old=receipt['resources'][name];file=Path(row['override_provider'])
        if evidence.sha(old['frozen'])!=old['sha256']or row['original_sha256']!=old['sha256']or row['original_provider']!=old['provider']or row['original_provider_sha256']!=old['provider_sha256']or file.read_bytes()!=desired[name]or evidence.sha(file)!=row['override_sha256']:raise ValueError('Original/override presentation evidence drift')
        field_guard(originals[name],file.read_bytes())
    return True
