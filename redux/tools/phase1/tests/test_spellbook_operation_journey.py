"""Focused synthetic operation/sort/tab/wire negatives. Never launches a runtime."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]))
import spellbook_operation_validation as v
import spellbook_operation_journey as runner
import spellbook_presentation_control as presentation
from test_spellbook_information_validation import page_fixture

def state():
    people=[]
    for index,name in enumerate(('None','Imoen','Jaheira','Minsc')):
        people.append(dict(script_name=name,name=name,runtime_id=10002+index,in_party=index+1,area='AR0602',position=[1,2],base_stats=[0]*256,modified_stats=[0]*256,inventory=dict(fist_slot=10,items=[]),effects=[],spellbook=[],locals={}))
    for case in v.CASES:
        refs=['SPWI211','SPWI212','SPWI213','SPWI214','SPWI215']if case['name']=='mage'else['SPPR111','SPPR101','SPPR103','SPPR104','SPPR113','SPPR105','SPPR110'];memo=['SPWI213','SPWI214','SPWI215']if case['name']=='mage'else['SPPR113','SPPR105','SPPR105','SPPR103','SPPR103']
        people[case['pc']-1]['spellbook']=[dict(type=case['kind'],level=case['level'],slots=len(memo),slots_with_bonus=len(memo),known=[dict(resref=ref,type=case['kind'],level=case['level'])for ref in refs],memorized=[dict(resref=ref,flags=1)for ref in memo])]
    return dict(schema='bg-redux-state/1',game_time=100,current_area='AR0602',selection=2,globals={'JAHEIRARELEASED':1},area_locals={},party=people,stored_npcs=[],current_area_actors=copy.deepcopy(people),journal=[dict(text_ref=47518,chapter=1,section=2)])

def change(s,case,rows):
    identity=s['party'][case['pc']-1]['runtime_id']
    for group in('party','current_area_actors'):
        actor=next(a for a in s[group]if a['runtime_id']==identity);v.page(actor,case['kind'],case['level'])['memorized']=copy.deepcopy(rows)

def net(s):
    after=copy.deepcopy(s)
    for case in v.CASES:
        rows=v.page(after['party'][case['pc']-1],case['kind'],case['level'])['memorized'];change(after,case,rows[1:]+[dict(resref=case['ref'],flags=0)])
    return after

def book_capture():
    s=state();case=v.CASES[0];data=v.page(s['party'][1],1,1);names={r['resref']:dict(name='name'+str(i))for i,r in enumerate(data['known'])};names['SPWI212']['name']='Z';names['SPWI213']['name']='B'
    known=[dict(original_index=i,resref=r['resref'],name=names[r['resref']]['name'])for i,r in enumerate(data['known'])];shown=sorted(known,key=lambda r:r['name']);memo=copy.deepcopy(data['memorized']);meta=dict(actor=2,actor_name='Imoen',pack='GUIMG',kind=1,level=1,known=known,shown=shown,memorized=memo,slots=3,label='Level 2');controls=[]
    for i,row in enumerate(shown):controls.append(dict(pack='GUIMG',window=2,id=27+i,visible=True,value=row['original_index'],tooltip=row['name'],stored_tooltip=row['name'],disabled=False,picture_present=True))
    for i,row in enumerate(memo):controls.append(dict(pack='GUIMG',window=2,id=3+i,visible=True,value=i,tooltip=names[row['resref']]['name'],picture_present=True))
    for cid,text in((0x10000035,'Imoen'),(0x10000032,'Level 2')):controls.append(dict(pack='GUIMG',window=2,id=cid,visible=True,text=text))
    layout,page_controls=page_fixture(shown,pack='GUIMG',actor=2,kind=1,level=1)
    meta.update(schema='bg-redux-book-observation/2',information_page=layout)
    controls=page_controls+[c for c in controls if not 27<=c['id']<51]
    return meta,s,dict(controls=controls),case,names

def bmp(path,width=4,height=3):
    stride=((width*24+31)//32)*4;pixels=bytes((i%251 for i in range(stride*height)));raw=bytearray(54);raw[:2]=b'BM';struct.pack_into('<I',raw,2,54+len(pixels));struct.pack_into('<I',raw,10,54);struct.pack_into('<IiiHH',raw,14,40,width,height,1,24);path.write_bytes(raw+pixels)

def wire_fixture(folder):
    source=state();gam=bytearray(0xb4+4*0x160);gam[:8]=b'GAMEV2.0';struct.pack_into('<II',gam,0x20,0xb4,4)
    for index,actor in enumerate(source['party']):
        cre=bytearray(0x2d4+80);cre[:8]=b'CRE V1.0';cre[0x33]=1;cre[0x280:0x2a0]=actor['script_name'].encode().ljust(32,b'\0');struct.pack_into('<I',cre,0x2b8,0x2d4);struct.pack_into('<38HhH',cre,0x2d4,*([0xffff]*38),1000,0)
        if actor['spellbook']:
            page=actor['spellbook'][0];ka=len(cre)
            for r in reversed(page['known']):cre.extend(r['resref'].encode().ljust(8,b'\0')+struct.pack('<2H',r['level'],r['type']))
            ba=len(cre);cre.extend(struct.pack('<4H2I',page['level'],page['slots'],page['slots_with_bonus'],page['type'],0,len(page['memorized'])));ma=len(cre)
            for r in page['memorized']:cre.extend(r['resref'].encode().ljust(8,b'\0')+struct.pack('<I',r['flags']))
            struct.pack_into('<6I',cre,0x2a0,ka,len(page['known']),ba,1,ma,len(page['memorized']))
        row=0xb4+index*0x160;struct.pack_into('<2I',gam,row+4,len(gam),len(cre));gam.extend(cre)
    (folder/'baldur.gam').write_bytes(gam);return source

class PresentationControlContracts(unittest.TestCase):
    def originals(self):
        return {name:b'SPL V1  '+struct.pack('<I',i+100)+bytes(range(64))for i,name in enumerate(n for pair in presentation.PAIRS for n in pair)}
    def fixture(self,folder):
        resources={}
        for name,raw in self.originals().items():
            file=folder/name;file.write_bytes(raw);ref=struct.unpack_from('<I',raw,8)[0]
            resources[name]=dict(frozen=str(file),sha256=runner.evidence.sha(file),bytes=len(raw),spell_name_ref=ref,spell_name='name'+str(ref),provider='archive.bif',provider_sha256='frozenarchive')
        resources['tlk']=dict(path='dialog.tlk',sha256='frozenTLK',bytes=1000)
        return dict(resources=resources)
    def test_only_name_field_is_exchanged_and_spell_body_identity_retained(self):
        originals=self.originals();changed=presentation.exchange(originals)
        for left,right in presentation.PAIRS:
            self.assertEqual(changed[left][8:12],originals[right][8:12])
            self.assertEqual(changed[left][:8]+changed[left][12:],originals[left][:8]+originals[left][12:])
            presentation.field_guard(originals[left],changed[left])
        bad=bytearray(changed['SPWI213.spl']);bad[-1]^=1
        with self.assertRaises(ValueError):presentation.field_guard(originals['SPWI213.spl'],bad)
        with self.assertRaises(ValueError):presentation.field_guard(originals['SPWI213.spl'],originals['SPWI213.spl'])
    def test_missing_extra_identical_names_and_truncated_header_rejected(self):
        for mutation in ('missing','extra','same','truncated'):
            originals=self.originals()
            if mutation=='missing':originals.pop('SPPR111.spl')
            elif mutation=='extra':originals['OTHER.spl']=originals['SPWI213.spl']
            elif mutation=='same':originals['SPWI211.spl']=originals['SPWI213.spl']
            else:originals['SPWI213.spl']=b'SPL V1  '
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):presentation.exchange(originals)
    def test_private_override_provider_and_tlk_are_bound_and_tamper_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);receipt=self.fixture(folder);private=folder/'override';private.mkdir();control=presentation.prepare(receipt,private)
            self.assertTrue(presentation.verify(control,receipt));self.assertEqual(len(list(private.iterdir())),4)
            for row in control['proof']:
                name=row['resref']+'.spl';self.assertEqual(control['resources'][name]['provider'],str((private/name).resolve()));self.assertTrue(set(row['changed_offsets'])<=set(range(8,12)))
            file=private/'SPWI213.spl';file.write_bytes(file.read_bytes()+b'bad')
            with self.assertRaises(ValueError):presentation.verify(control,receipt)
    def test_original_hash_drift_and_nonempty_private_override_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);receipt=self.fixture(folder);private=folder/'override';private.mkdir();receipt['resources']['SPWI213.spl']['sha256']='wrong'
            with self.assertRaises(ValueError):presentation.prepare(receipt,private)
            (private/'unexpected').write_bytes(b'x')
            with self.assertRaises(ValueError):presentation.prepare(receipt,private)
    def test_tlk_proof_and_original_provider_cannot_be_rebound(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp);receipt=self.fixture(folder);private=folder/'override';private.mkdir();control=presentation.prepare(receipt,private)
            bad=copy.deepcopy(control);bad['tlk']['sha256']='other'
            with self.assertRaises(ValueError):presentation.verify(bad,receipt)
            bad=copy.deepcopy(control);bad['proof'][0]['original_provider']='other'
            with self.assertRaises(ValueError):presentation.verify(bad,receipt)

class SpellbookOperationContracts(unittest.TestCase):
    def test_conflicting_party_map_spellbook_cannot_be_normalized_away(self):
        before=state();after=net(before)
        after['current_area_actors'][1]['spellbook'][0]['memorized'][0]['resref']='SPWI211'
        with self.assertRaises(ValueError):v.declared_world_delta(before,after,{'mage','priest'})
        with self.assertRaises(ValueError):v.callback_guard(before,after,v.CASES[0],'confirm-remove')

    def test_unbound_python_null_only_matches_exact_native_invalid_sentinel(self):
        self.assertTrue(v.request_value_guard(dict(value=None),dict(actual_value=0xffffffff,actual_variable='')))
        for value,var in ((0,''),(-1,''),(0xfffffffe,''),(0xffffffff,'Memorized'),(None,''),(True,''),(0xffffffff,None)):
            with self.subTest(value=value,var=var),self.assertRaises(ValueError):v.request_value_guard(dict(value=None),dict(actual_value=value,actual_variable=var))
    def test_integer_control_values_remain_exact_without_null_coercion(self):
        self.assertTrue(v.request_value_guard(dict(value=2),dict(actual_value=2,actual_variable='Memorized')))
        for wanted,actual in ((2,3),(0,0xffffffff),(2,None),(2,'2'),(1,True),(True,1)):
            with self.subTest(wanted=wanted,actual=actual),self.assertRaises(ValueError):v.request_value_guard(dict(value=wanted),dict(actual_value=actual,actual_variable='Memorized'))

    def test_initial_load_records_null_only_when_game_is_actually_absent(self):
        event=dict(sequence=1,step=-1,pack='GUILOAD',window=0,control=26,before_game_present=False,after_game_present=False)
        self.assertTrue(v.callback_game_boundary(event,None,None))
        event['after_game_present']=True
        self.assertTrue(v.callback_game_boundary(event,None,state()))
        with self.assertRaises(ValueError):v.callback_game_boundary(event,None,None)
        with self.assertRaises(ValueError):v.callback_game_boundary(event,state(),state())
        for key,value in (('sequence',2),('pack','GUIMG'),('control',27)):
            bad=dict(event);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):v.callback_game_boundary(bad,None,state())

    def test_postload_callbacks_require_game_and_truthful_presence_flags(self):
        event=dict(sequence=2,step=0,pack='PORTWIN',window=0,control=1,before_game_present=True,after_game_present=True)
        self.assertFalse(v.callback_game_boundary(event,state(),state()))
        for key in ('before_game_present','after_game_present'):
            bad=dict(event);bad[key]=False
            before=None if key=='before_game_present'else state();after=None if key=='after_game_present'else state()
            with self.subTest(key=key),self.assertRaises(ValueError):v.callback_game_boundary(bad,before,after)
            bad=dict(event);bad.pop(key)
            with self.assertRaises(ValueError):v.callback_game_boundary(bad,state(),state())
        with self.assertRaises(ValueError):v.callback_game_boundary(event,{},state())

    def test_cancel_preserves_ready_remove_readd_is_depleted(self):
        before=state();case=v.CASES[0];v.stage_delta(before,copy.deepcopy(before),case,'after-cancel');removed=copy.deepcopy(before);rows=v.page(before['party'][1],1,1)['memorized'];change(removed,case,rows[1:]);v.stage_delta(before,removed,case,'after-remove');after=copy.deepcopy(removed);change(after,case,rows[1:]+[dict(resref='SPWI213',flags=0)]);v.stage_delta(before,after,case,'after-add')
        change(after,case,rows[1:]+[dict(resref='SPWI213',flags=1)])
        with self.assertRaises(ValueError):v.stage_delta(before,after,case,'after-add')
    def test_actual_wrong_added_spell_or_wrong_memorized_index_fails(self):
        before=state();case=v.CASES[0];rows=v.page(before['party'][1],1,1)['memorized'];removed=copy.deepcopy(before);change(removed,case,rows[1:]);after=copy.deepcopy(removed);change(after,case,rows[1:]+[dict(resref='SPWI211',flags=0)])
        with self.assertRaises(ValueError):v.callback_guard(removed,after,case,'known-add')
        wrong=copy.deepcopy(before);change(wrong,case,[rows[0],rows[2]])
        with self.assertRaises(ValueError):v.callback_guard(before,wrong,case,'confirm-remove')
    def test_duplicate_priest_memorizations_are_retained_exactly(self):
        before=state();case=v.CASES[1];after=net(before);v.stage_delta(before,after,case,'final');rows=v.page(after['party'][2],0,0)['memorized'];change(after,case,rows[1:])
        with self.assertRaises(ValueError):v.stage_delta(before,after,case,'final')
    def test_no_cast_rest_recharge_or_other_world_delta_is_whitelisted(self):
        before=state();after=net(before);v.declared_world_delta(before,after,{'mage','priest'})
        for kind in('xp','item','quest','effects','clock','other-ready'):
            bad=copy.deepcopy(after)
            if kind=='xp':bad['party'][0]['base_stats'][44]+=1
            elif kind=='item':bad['party'][3]['inventory']['items']=[{'resref':'GIFT'}]
            elif kind=='quest':bad['journal']=[]
            elif kind=='effects':bad['party'][1]['effects']=[{'opcode':0}]
            elif kind=='clock':bad['game_time']+=1
            else:v.page(bad['party'][1],1,1)['memorized'][0]['flags']=0
            with self.subTest(kind=kind),self.assertRaises(ValueError):v.declared_world_delta(before,bad,{'mage','priest'})
    def test_known_order_and_slots_cannot_change_during_memorization(self):
        before=state();after=copy.deepcopy(before);case=v.CASES[0];v.page(after['party'][1],1,1)['known'].reverse()
        with self.assertRaises(ValueError):v.stage_delta(before,after,case,'after-cancel')
        after=copy.deepcopy(before);v.page(after['party'][1],1,1)['slots_with_bonus']+=1
        with self.assertRaises(ValueError):v.stage_delta(before,after,case,'after-cancel')
    def test_nonidentity_shown_sort_retains_original_index(self):
        meta,s,ui,case,names=book_capture();self.assertTrue(v.book_guard(meta,s,ui,case,names,'Level <SPELLLEVEL>'))
        chosen=next(c for c in ui['controls']if c['id']==27+next(i for i,r in enumerate(meta['shown'])if r['resref']=='SPWI213'));chosen['value']=1
        with self.assertRaises(ValueError):v.book_guard(meta,s,ui,case,names,'Level <SPELLLEVEL>')
    def test_icon_presence_cannot_hide_wrong_resref_tooltip_or_caster(self):
        for kind in('tooltip','caster','level','known'):
            meta,s,ui,case,names=book_capture()
            if kind=='tooltip':ui['controls'][0]['tooltip']='wrong'
            elif kind=='caster':s['selection']=3
            elif kind=='level':meta['label']='Level 1'
            else:meta['known'][0]['resref']='SPWI215'
            with self.subTest(kind=kind),self.assertRaises(ValueError):v.book_guard(meta,s,ui,case,names,'Level <SPELLLEVEL>')
    def test_direct_tabs_must_visibly_differ_and_arrows_match(self):
        case=v.CASES[0];zero=['selected','plain']+['x']*7;one=['plain','selected']+['x']*7;rows={'mage.'+n:list(one if n in('tab1','arrow1','back1','tab1-repeat')else zero)for n in('tab0','tab1','arrow0','arrow1','back1','tab1-repeat')};v.tabs_guard(rows,case)
        rows['mage.arrow1']=list(zero)
        with self.assertRaises(ValueError):v.tabs_guard(rows,case)
        for key in rows:rows[key]=list(zero)
        with self.assertRaises(ValueError):v.tabs_guard(rows,case)
    def test_tab_bmp_pixels_are_bounded_and_sensitive_to_actual_bytes(self):
        with tempfile.TemporaryDirectory()as temp:
            p=Path(temp)/'capture.bmp';bmp(p);a=v.bmp_region_sha(p,[0,0,2,2]);raw=bytearray(p.read_bytes());raw[-12]^=1;p.write_bytes(raw);self.assertNotEqual(v.bmp_region_sha(p,[0,0,2,2]),a)
            with self.assertRaises(ValueError):v.bmp_region_sha(p,[3,0,2,2])
            p.write_bytes(raw[:-1])
            with self.assertRaises(ValueError):v.bmp_region_sha(p,[0,0,1,1])
    def test_wire_known_order_is_exact_reverse_not_arbitrary_permutation(self):
        with tempfile.TemporaryDirectory()as temp:
            p=Path(temp);runtime=wire_fixture(p);saved=v.wire_spellbooks(p);v.wire_state_guard(saved,runtime)
            known=saved[1]['pages'][0]['known'];self.assertGreaterEqual(len(known),3)
            self.assertEqual([r['resref']for r in known],[r['resref']for r in reversed(runtime['party'][1]['spellbook'][0]['known'])])
            for mutation in ('identity','rotate','ref','type','level','ready','memo-order'):
                bad=copy.deepcopy(saved);page=bad[1]['pages'][0]
                if mutation=='identity':page['known'].reverse()
                elif mutation=='rotate':page['known']=page['known'][1:]+page['known'][:1]
                elif mutation in ('type','level'):page['known'][0][mutation]+=1
                elif mutation=='ref':page['known'][0]['resref']='SPWI999'
                elif mutation=='ready':page['memorized'][0]['flags']=0
                else:page['memorized'].reverse()
                with self.subTest(mutation=mutation),self.assertRaises(ValueError):v.wire_state_guard(bad,runtime)

    def test_wire_actual_refs_ready_flags_and_all_other_pages_conserved(self):
        with tempfile.TemporaryDirectory()as temp:
            p=Path(temp);s=wire_fixture(p);before=v.wire_spellbooks(p);v.wire_state_guard(before,s);after=copy.deepcopy(before)
            for case in v.CASES:
                page=after[case['pc']-1]['pages'][0];page['memorized']=page['memorized'][1:]+[dict(resref=case['ref'],flags=0)]
            v.wire_delta_guard(before,after);after[1]['pages'][0]['known'].reverse()
            with self.assertRaises(ValueError):v.wire_delta_guard(before,after)
    def test_wire_overlap_or_orphan_memorization_rejected(self):
        for kind in('overlap','orphan','duplicate','escape'):
            with tempfile.TemporaryDirectory()as temp:
                p=Path(temp);wire_fixture(p);g=bytearray((p/'baldur.gam').read_bytes());start=struct.unpack_from('<I',g,0xb4+0x160+4)[0];ka,kn,ba,bn,ma,mn=struct.unpack_from('<6I',g,start+0x2a0)
                if kind=='overlap':struct.pack_into('<I',g,start+0x2b0,ka)
                elif kind=='orphan':struct.pack_into('<I',g,start+ba+12,mn-1)
                elif kind=='duplicate':struct.pack_into('<I',g,start+0x2ac,2)
                else:struct.pack_into('<I',g,start+ba+8,mn+1)
                (p/'baldur.gam').write_bytes(g)
                with self.subTest(kind=kind),self.assertRaises(ValueError):v.wire_spellbooks(p)
    def test_after_plan_explicitly_replaces_modal_cancel_with_one_charged_press(self):
        before=v.expected_plan('operate','legacy-confirmation');after=v.expected_plan('operate','ee-direct')
        self.assertEqual(len(before),69);self.assertEqual(len(after),57)
        for case in v.CASES:
            prefix=case['name']+'.';self.assertIn(prefix+'charged-remove',after)
            for step in ('cancel-modal','after-cancel','remove-modal','confirm-remove','charged-cancel-request','charged-remove-request'):self.assertNotIn(prefix+step,after)
            for step in ('known-add','depleted-remove','known-readd','final'):self.assertIn(prefix+step,after)
        self.assertEqual(v.expected_plan('reload','ee-direct'),v.expected_plan('reload','legacy-confirmation'))
        with self.assertRaises(ValueError):v.expected_plan('operate','automatic')
    def test_direct_charged_callback_requires_immediate_exact_removal(self):
        before=state();case=v.CASES[0];after=copy.deepcopy(before);rows=v.page(before['party'][1],1,1)['memorized'];change(after,case,rows[1:]);v.callback_guard(before,after,case,'charged-remove')
        with self.assertRaises(ValueError):v.callback_guard(before,before,case,'charged-remove')
        wrong=copy.deepcopy(before);change(wrong,case,rows[:-1])
        with self.assertRaises(ValueError):v.callback_guard(before,wrong,case,'charged-remove')
    def test_policy_is_explicit_in_host_and_runtime_without_fallback(self):
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp)
            for hostpolicy,runtimepolicy in (('legacy-confirmation','ee-direct'),('ee-direct','legacy-confirmation'),(None,'ee-direct')):
                (folder/'book-result.json').write_text(json.dumps(dict(confirmation_policy=hostpolicy)))
                (folder/'book-runtime.json').write_text(json.dumps(dict(confirmation_policy=runtimepolicy)))
                with self.subTest(host=hostpolicy,runtime=runtimepolicy),self.assertRaisesRegex(ValueError,'policy'):runner.validate_capture(folder,'a'*32,'operate',None,dict(confirmation_policy='ee-direct'))

    def test_independent_plan_rejects_missing_confirmation_or_depleted_operation(self):
        self.assertEqual(len(v.expected_plan('operate')),69);self.assertEqual(len(v.expected_plan('reload')),41)
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp);host=dict(schema='bg-redux-book-host/1',nonce='a'*32,mode='operate',confirmation_policy='legacy-confirmation',completed=True,error='',os_pointer_input=False,direct_spell_mutation=False);runtime=dict(schema='bg-redux-book-runtime/1',nonce='a'*32,mode='operate',confirmation_policy='legacy-confirmation',planned=v.expected_plan('operate')[:-1],steps=68,completed=True)
            (folder/'book-result.json').write_text(json.dumps(host));(folder/'book-runtime.json').write_text(json.dumps(runtime))
            with self.assertRaises(ValueError):runner.validate_capture(folder,'a'*32,'operate',None,{})
    def test_wrong_nonce_or_forced_native_receipt_rejected(self):
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp);(folder/'book-runtime.json').write_text(json.dumps(dict(confirmation_policy='legacy-confirmation')))
            for kind in('nonce','forced'):
                host=dict(schema='bg-redux-book-host/1',nonce='b'*32 if kind=='nonce'else'a'*32,mode='operate',confirmation_policy='legacy-confirmation',completed=True,error='',os_pointer_input=False,direct_spell_mutation=kind=='forced');(folder/'book-result.json').write_text(json.dumps(host))
                with self.subTest(kind=kind),self.assertRaises(ValueError):runner.validate_capture(folder,'a'*32,'operate',None,{})
    def test_wrong_measured_parent_hash_fails_before_any_runtime(self):
        with patch.object(runner.evidence,'sha',return_value='wrong'),self.assertRaises(ValueError):runner.parent_proof(Path('private-parent'))
    def test_gui_helper_rejects_nested_or_missing_main(self):
        with self.assertRaises(ValueError):runner.gui_helpers(b'int main(){} int main(){}')

if __name__=='__main__':unittest.main()
