"""Intended identity, permitted native deltas and stale/incorrect callback controls."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import spellbook_erase_validation as v

def page():
    return dict(type=1,level=1,slots=3,slots_with_bonus=3,
        known=[dict(resref=r,type=1,level=1) for r in ('SPWI211','SPWI212','SPWI213')],
        memorized=[dict(resref=r,flags=f) for r,f in (('SPWI213',1),('SPWI211',0),('SPWI213',0))])

def erased(p):
    q=copy.deepcopy(p);q['known']=q['known'][:2];q['memorized']=[q['memorized'][1]];return q

class EraseContracts(unittest.TestCase):
    def test_all_target_memorized_copies_removed(self):
        p=page();v.intended_page(p,erased(p))
    def test_wrong_known_ref_deletion_is_failure(self):
        p=page();q=erased(p);q['known']=[p['known'][1],p['known'][2]]
        with self.assertRaises(ValueError):v.intended_page(p,q)
    def test_target_depleted_copy_left_is_failure(self):
        p=page();q=erased(p);q['memorized'].append(p['memorized'][2])
        with self.assertRaises(ValueError):v.intended_page(p,q)
    def test_unrelated_ready_flag_cannot_change(self):
        p=page();q=erased(p);q['memorized'][0]['flags']=1
        with self.assertRaises(ValueError):v.intended_page(p,q)
    def test_capacity_cannot_change(self):
        p=page();q=erased(p);q['slots_with_bonus']=4
        with self.assertRaises(ValueError):v.intended_page(p,q)
    def test_duplicate_target_known_rejected(self):
        p=page();p['known'].append(copy.deepcopy(p['known'][2]))
        with self.assertRaises(ValueError):v.intended_page(p,erased(page()))
    def test_wrong_parent_original_index_rejected(self):
        p=page();p['known'].reverse()
        with self.assertRaises(ValueError):v.intended_page(p,erased(page()))
    def test_wire_reversed_known_order_preserved(self):
        p=page();q=erased(p);p['known'].reverse();q['known'].reverse()
        a=[dict(name=n,pages=[copy.deepcopy(p)] if n=='imoen' else []) for n in ('none','imoen','jaheira','minsc')]
        b=copy.deepcopy(a);b[1]['pages']=[q];v.wire_delta_guard(a,b)
        b[2]['pages']=[page()]
        with self.assertRaises(ValueError):v.wire_delta_guard(a,b)
    def test_display_zero_binds_original_two_rightpress(self):
        meta=dict(shown=[dict(resref='SPWI213',original_index=2)])
        event=dict(pack='GUIMG',window=2,control=27,actual_value=2,action='RightPress',actual_tooltip='Controlled name')
        self.assertTrue(v.target_binding(meta,event,{'SPWI213':dict(name='Controlled name')},True))
        for key,value in (('action','Press'),('actual_value',0),('control',29),('actual_tooltip','Another spell')):
            bad=dict(event);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):v.target_binding(meta,bad,{'SPWI213':dict(name='Controlled name')},True)
    def test_control_must_actually_move_target_to_display_zero(self):
        meta=dict(shown=[dict(resref='SPWI211',original_index=0),dict(resref='SPWI213',original_index=2)])
        with self.assertRaises(ValueError):v.target_binding(meta,{}, {'SPWI213':dict(name='name')},True)
    def test_stale_nonce_and_truncated_plan_fail(self):
        nonce='a'*32;plan=v.expected_plan('operate')
        host=dict(schema='bg-redux-book-host/1',nonce=nonce,mode='operate',confirmation_policy='ee-direct',completed=True,error='',os_pointer_input=False,direct_spell_mutation=False)
        runtime=dict(schema='bg-redux-book-runtime/1',nonce=nonce,mode='operate',confirmation_policy='ee-direct',planned=plan,steps=len(plan),completed=True)
        v.terminal_identity(host,runtime,nonce,'operate','ee-direct')
        for bad in (dict(runtime,nonce='b'*32),dict(runtime,planned=plan[:-1]),dict(runtime,steps=len(plan)-1)):
            with self.assertRaises(ValueError):v.terminal_identity(host,bad,nonce,'operate','ee-direct')
        with self.assertRaises(ValueError):v.terminal_identity(dict(host,direct_spell_mutation=True),runtime,nonce,'operate','ee-direct')
    def test_wrong_confirmation_route_and_rightpress_kind_fail(self):
        plan=v.expected_plan('operate');step=plan.index('mage.confirm')
        row=dict(event='request',step=step,pack='GUIMG',window=101,control=0)
        event=dict(row,action='Press');v.callback_inventory([event],[row],plan)
        for bad in (dict(event,window=3),dict(event,action='RightPress')):
            with self.assertRaises(ValueError):v.callback_inventory([bad],[row],plan)
    def test_world_delta_preserves_other_actor_and_journal(self):
        actors=[dict(script_name=n,runtime_id=i,spellbook=[page()])for i,n in enumerate(('none','imoen','jaheira','minsc'))]
        before=dict(party=actors,current_area_actors=copy.deepcopy(actors),selection=2,journal=[dict(text=34105)])
        after=copy.deepcopy(before)
        for group in ('party','current_area_actors'):after[group][1]['spellbook']=[erased(page())]
        v.world_delta(before,after,True)
        bad=copy.deepcopy(after);bad['journal']=[]
        with self.assertRaises(ValueError):v.world_delta(before,bad,True)
        bad=copy.deepcopy(after);bad['party'][2]['spellbook'][0]['slots']=0
        with self.assertRaises(ValueError):v.world_delta(before,bad,True)
    def test_cancel_does_not_allow_even_intended_erase(self):
        actors=[dict(script_name=n,runtime_id=i,spellbook=[page()])for i,n in enumerate(('none','imoen','jaheira','minsc'))]
        before=dict(party=actors,current_area_actors=copy.deepcopy(actors),selection=2)
        after=copy.deepcopy(before)
        for group in ('party','current_area_actors'):after[group][1]['spellbook']=[erased(page())]
        with self.assertRaises(ValueError):v.world_delta(before,after,False)

if __name__=='__main__':unittest.main()
