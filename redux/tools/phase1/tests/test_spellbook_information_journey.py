"""Source-only independent information-plan/identity/route negatives."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import types
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import spellbook_information_journey_validation as v
import spellbook_operation_validation as base
from test_spellbook_operation_journey import state as source_state

def state():
    result=source_state()
    for pc,kind,ref in ((2,1,'SPWI302'),(3,0,'SPPR303')):
        page=dict(type=kind,level=2,slots=1,slots_with_bonus=1,known=[dict(resref=ref,type=kind,level=2)],memorized=[])
        result['party'][pc-1]['spellbook'].append(page)
        identity=result['party'][pc-1]['runtime_id']
        next(a for a in result['current_area_actors']if a['runtime_id']==identity)['spellbook'].append(copy.deepcopy(page))
    return result

class InformationJourneyContracts(unittest.TestCase):
    def resources(self,s):
        return {r['resref'].upper()+'.spl':dict(spell_name=r['resref'])for a in s['party']for p in a['spellbook']for r in p['known']}

    def test_natural_31_entry_library_requires_five_actual_pages_without_grants(self):
        s=state();p=s['party'][2]['spellbook'][0]
        p['known']=[dict(resref='SP%06d'%i,type=0,level=0)for i in range(31)]
        plan=v.expected_plan(s,'operate',self.resources(s))
        self.assertEqual([n for n in plan if n.startswith('priest.level0')and n.endswith('.default')],
            ['priest.level0.page%d.default'%i for i in range(5)])
        self.assertEqual(sum(n.startswith('priest.level0')and n.endswith('.next')for n in plan),4)
        self.assertEqual(sum(n.endswith('.other-actor')for n in plan),2)
        self.assertEqual(len(plan),len(set(plan)))

    def test_reload_inventory_contains_browsing_but_no_mutating_or_full_icon_steps(self):
        raw=state();plan=v.expected_plan(raw,'reload',self.resources(raw))
        self.assertIn('mage.scroll.scroll-down',plan)
        self.assertNotIn('mage.target.scroll-down',plan)
        self.assertIn('priest.level0.page0.deselected',plan)
        for suffix in ('remove','separate','full-icon','remove-depleted','icon'):
            self.assertFalse(any(n.endswith('.'+suffix)for n in plan))

    def test_actual_runtime_plan_matches_independent_raw_inventory_for_both_modes(self):
        raw=state();pages=raw['party'][2]['spellbook'][0]
        pages['known']=[dict(resref='SP%06d'%i,type=0,level=0)for i in range(31)]
        def count(pc,kind,level):
            found=[p for p in raw['party'][pc-1]['spellbook']if p['type']==kind and p['level']==level]
            return len(found[0]['known'])if found else 0
        for mode in ('operate','reload'):
            def known(pc,kind,level,index):return dict(SpellResRef=next(p for p in raw['party'][pc-1]['spellbook']if p['type']==kind and p['level']==level)['known'][index]['resref'])
            gem=types.SimpleNamespace(GetPartySize=lambda:4,GetKnownSpellsCount=count,GetKnownSpell=known,GetSpell=lambda ref:dict(SpellName=ref),GetString=lambda ref:ref,GetPlayerName=lambda pc,_:raw['party'][pc-1]['name'])
            external=types.SimpleNamespace(CASES=base.CASES,MODE=mode)
            spec=importlib.util.spec_from_file_location('InformationPlanRuntime',Path(__file__).resolve().parents[1]/'SpellbookInformationRuntime.py')
            runtime=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,{'GemRB':gem,'SpellbookOperationRuntime':external}):spec.loader.exec_module(runtime)
            runtime.BuildPlan()
            with self.subTest(mode=mode):self.assertEqual([name for name,_ in runtime.PLAN],v.expected_plan(raw,mode,self.resources(raw)))

    def test_missing_duplicate_or_unbounded_natural_inventory_rejected(self):
        for kind in ('absent','duplicate','excess'):
            s=state();pages=s['party'][2]['spellbook']
            if kind=='absent':pages.clear()
            elif kind=='duplicate':pages.append(copy.deepcopy(pages[0]))
            else:pages[0]['known']*=40
            with self.subTest(kind=kind),self.assertRaises(ValueError):v.expected_plan(s,'operate',self.resources(s))

    def test_selection_and_deselection_bind_first_real_visible_identity(self):
        c=base.CASES[1];row=dict(resref='SPPR113',original_index=4,name='localized target')
        m=dict(actor=3,level=0,information_page=dict(top=7,selected=row,visible_rows=[row]))
        v.selection_guard('priest.level0.page1.selected',m,c)
        m['information_page']['selected']=dict(row,original_index=0)
        with self.assertRaises(ValueError):v.selection_guard('priest.level0.page1.selected',m,c)
        with self.assertRaises(ValueError):v.selection_guard('priest.level0.page1.deselected',m,c)

    def test_actor_change_and_return_must_clear_selection_and_page(self):
        c=base.CASES[1];m=dict(actor=2,level=0,information_page=dict(top=0,selected=None))
        v.selection_guard('priest.target.other-actor',m,c)
        for field,value in (('actor',3),('top',7),('selected',dict(resref='SPPR113',original_index=4))):
            bad=copy.deepcopy(m)
            if field=='actor':bad[field]=value
            else:bad['information_page'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):v.selection_guard('priest.target.other-actor',bad,c)

    def test_actual_name_select_cannot_be_replaced_with_mutating_icon_callback(self):
        s=state();resources=self.resources(s);rows=s['party'][1]['spellbook'][0]['known'];ordered=sorted(enumerate(rows),key=lambda p:resources[p[1]['resref']+'.spl']['spell_name']);shown=next(i for i,(original,_)in enumerate(ordered)if original==2)
        actual=dict(pack='GUIMG',window=2,control=0x7fff0400+shown)
        v.callback_route('mage.target.select',actual,s,resources)
        actual['control']=27+shown
        with self.assertRaises(ValueError):v.callback_route('mage.target.select',actual,s,resources)

    def test_separate_action_and_icon_shortcut_have_distinct_exact_routes(self):
        s=state();resources=self.resources(s)
        v.callback_route('mage.target.separate',dict(pack='GUIMG',window=2,control=0x7fff0413),s,resources)
        with self.assertRaises(ValueError):v.callback_route('mage.target.separate',dict(pack='GUIMG',window=2,control=29),s,resources)
        with self.assertRaises(ValueError):v.callback_route('mage.scroll.scroll-down',dict(pack='GUIMG',window=2,control=0x7fff0415),s,resources)

    def test_intermediate_observations_cannot_hide_known_stat_or_other_page_mutations(self):
        before=state();after=copy.deepcopy(before);after['selection']=3
        v.observation_world_guard(before,after)
        for kind in ('stat','known','slot','journal'):
            changed=copy.deepcopy(after)
            if kind=='stat':changed['party'][0]['modified_stats'][1]+=1
            elif kind=='known':changed['party'][1]['spellbook'][0]['known'].reverse()
            elif kind=='slot':changed['party'][1]['spellbook'][0]['slots_with_bonus']+=1
            else:changed['journal'].clear()
            with self.subTest(kind=kind),self.assertRaises(ValueError):v.observation_world_guard(before,changed)

    def test_terminal_nonce_incomplete_and_forced_claims_fail_before_world_acceptance(self):
        nonce='a'*32
        host=dict(schema='bg-redux-information-host/1',nonce=nonce,mode='operate',confirmation_policy='ee-direct',completed=True,error='',os_pointer_input=False,direct_spell_mutation=False)
        with tempfile.TemporaryDirectory()as root:
            folder=Path(root);(folder/'book-runtime.json').write_text('{}',encoding='utf8')
            for key,value in (('nonce','b'*32),('completed',False),('os_pointer_input',True),('direct_spell_mutation',True),('confirmation_policy','legacy-confirmation')):
                bad=dict(host,**{key:value});(folder/'book-result.json').write_text(json.dumps(bad),encoding='utf8')
                with self.subTest(key=key),self.assertRaises(ValueError):v.validate_capture(folder,nonce,'operate',None,{})

    def test_scroll_target_is_natural_separate_identity_and_can_require_real_paging(self):
        raw=state();p=base.page(raw['party'][1],1,2)
        p['known']=[dict(resref='A%07d'%i,type=1,level=2)for i in range(9)]+p['known']
        resources=self.resources(raw);position,target=v.scroll_identity(raw,base.CASES[0],resources)
        self.assertEqual((position,target['resref'],target['original_index']),(9,'SPWI302',9))
        plan=v.expected_plan(raw,'reload',resources)
        self.assertIn('mage.scroll.next1',plan)
        v.callback_route('mage.scroll.select',dict(pack='GUIMG',window=2,control=0x7fff0402),raw,resources)
        with self.assertRaises(ValueError):v.callback_route('mage.scroll.select',dict(pack='GUIMG',window=2,control=0x7fff0400),raw,resources)
        p['known'].pop()
        with self.assertRaises(ValueError):v.scroll_identity(raw,base.CASES[0],self.resources(raw))

class InformationGenderTokenContracts(unittest.TestCase):
    table=b'2DA V1.0\n*\nTYPE MALE FEMALE\nPRO_HESHE 0 27484 27485\nPRO_HIMHER 0 27488 27487\nPRO_HISHER 0 27486 27487\n'
    words={'27484':'he','27485':'she','27488':'him','27486':'his','27487':'her'}
    def actor(self,sex):
        raw=state();raw['party'][0]['modified_stats'][35]=sex
        raw['current_area_actors'][0]=copy.deepcopy(raw['party'][0]);return raw
    def test_each_measured_pronoun_and_repetition_resolve_female_from_protagonist(self):
        text,trace=v.resolve_description('<PRO_HESHE> protects <PRO_HIMHER> with <PRO_HISHER> shield; <PRO_HESHE>.',self.table,self.words,self.actor(2))
        self.assertEqual(text,'she protects her with her shield; she.')
        self.assertEqual([t['word_ref']for t in trace],[27485,27487,27487,27485])
        self.assertTrue(all(t['slot']==0 and t['sex']==2 for t in trace))
    def test_engine_male_fallback_applies_to_every_nonfemale_stat_not_selected_actor(self):
        for sex in (0,1,3,255):
            raw=self.actor(sex);raw['selection']=3
            text,_=v.resolve_description('<PRO_HESHE>/<PRO_HIMHER>/<PRO_HISHER>',self.table,self.words,raw)
            with self.subTest(sex=sex):self.assertEqual(text,'he/him/his')
    def test_wrong_slot_reference_missing_or_duplicate_table_row_rejected(self):
        for table in (self.table.replace(b'PRO_HESHE 0',b'PRO_HESHE -1'),self.table.replace(b'27484 27485',b'27485 27484'),self.table+self.table.splitlines()[3]+b'\n',self.table.replace(b'PRO_HIMHER 0 27488 27487\n',b'')):
            with self.subTest(table=table),self.assertRaises(ValueError):v.resolve_description('<PRO_HESHE>',table,self.words,self.actor(1))
    def test_unsupported_or_malformed_tokens_are_never_stripped(self):
        for raw in ('<CHARNAME>','<HESHE>','<PRO_HIMHER','PRO_HESHE>','<<PRO_HESHE>>','<pro_heshe>'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):v.resolve_description(raw,self.table,self.words,self.actor(1))
    def test_word_actor_and_mirror_substitution_fails(self):
        for problem in ('word','tagword','slot','identity','mirror','sex'):
            words=dict(self.words);raw=self.actor(1)
            if problem=='word':words.pop('27484')
            elif problem=='tagword':words['27484']='<PRO_HISHER>'
            elif problem=='slot':raw['party'][0]['in_party']=2
            elif problem=='identity':raw['party'][0]['script_name']='imoen'
            elif problem=='mirror':raw['current_area_actors'][0]['modified_stats'][35]=2
            else:raw['party'][0]['modified_stats'][35]='2'
            with self.subTest(problem=problem),self.assertRaises(ValueError):v.resolve_description('<PRO_HESHE>',self.table,words,raw)
    def test_literal_description_is_preserved_byte_for_text_without_fabricated_tokens(self):
        text,trace=v.resolve_description('Full literal paragraph.\nSecond line.',self.table,self.words,self.actor(1))
        self.assertEqual(text,'Full literal paragraph.\nSecond line.');self.assertEqual(trace,[])

if __name__=='__main__':unittest.main()
