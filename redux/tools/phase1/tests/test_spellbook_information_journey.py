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
from test_spellbook_operation_journey import state

class InformationJourneyContracts(unittest.TestCase):
    def resources(self,s):
        return {r['resref'].upper()+'.spl':dict(spell_name=r['resref'])for a in s['party']for p in a['spellbook']for r in p['known']}

    def test_natural_31_entry_library_requires_five_actual_pages_without_grants(self):
        s=state();p=s['party'][2]['spellbook'][0]
        p['known']=[dict(resref='SP%06d'%i,type=0,level=0)for i in range(31)]
        plan=v.expected_plan(s,'operate')
        self.assertEqual([n for n in plan if n.startswith('priest.level0')and n.endswith('.default')],
            ['priest.level0.page%d.default'%i for i in range(5)])
        self.assertEqual(sum(n.startswith('priest.level0')and n.endswith('.next')for n in plan),4)
        self.assertEqual(sum(n.endswith('.other-actor')for n in plan),2)
        self.assertEqual(len(plan),len(set(plan)))

    def test_reload_inventory_contains_browsing_but_no_mutating_or_full_icon_steps(self):
        plan=v.expected_plan(state(),'reload')
        self.assertIn('mage.target.scroll-down',plan)
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
            gem=types.SimpleNamespace(GetPartySize=lambda:4,GetKnownSpellsCount=count,GetPlayerName=lambda pc,_:raw['party'][pc-1]['name'])
            external=types.SimpleNamespace(CASES=base.CASES,MODE=mode)
            spec=importlib.util.spec_from_file_location('InformationPlanRuntime',Path(__file__).resolve().parents[1]/'SpellbookInformationRuntime.py')
            runtime=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,{'GemRB':gem,'SpellbookOperationRuntime':external}):spec.loader.exec_module(runtime)
            runtime.BuildPlan()
            with self.subTest(mode=mode):self.assertEqual([name for name,_ in runtime.PLAN],v.expected_plan(raw,mode))

    def test_missing_duplicate_or_unbounded_natural_inventory_rejected(self):
        for kind in ('absent','duplicate','excess'):
            s=state();pages=s['party'][2]['spellbook']
            if kind=='absent':pages.clear()
            elif kind=='duplicate':pages.append(copy.deepcopy(pages[0]))
            else:pages[0]['known']*=40
            with self.subTest(kind=kind),self.assertRaises(ValueError):v.expected_plan(s,'operate')

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
        with self.assertRaises(ValueError):v.callback_route('mage.target.scroll-down',dict(pack='GUIMG',window=2,control=0x7fff0415),s,resources)

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

if __name__=='__main__':unittest.main()
