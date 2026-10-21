"""Challenge query preconditions, coverage, evaluator controls and state diffs."""
from pathlib import Path
import copy
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import query_side_effects as query


class QuerySideEffects(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.spec = dict(id='01-normal',weapon='sw1h01',defense=None)

    def state(self, weapon='sw1h01', defense=None):
        def actor(identifier, script):
            return dict(runtime_id=identifier,script_name=script,name=script,area='AR0602',position=[1,2],
                        base_stats=[47]+[0]*255,modified_stats=[47]+[0]*255,locals={},effects=[],spellbook=[],
                        inventory=dict(equipped=0,equipped_header=0,items=[]))
        sender,target = actor(100,'Protagonist'),actor(101,'Imoen')
        sender['inventory']['items']=[dict(slot=35,resref=weapon.upper(),usages=[0,0,0])]
        if weapon == 'bow01':
            sender['inventory']['equipped']=-24
            sender['inventory']['items'].append(dict(slot=11,resref='AROW01',usages=[40,0,0]))
        if defense:
            op,p1,p2=defense
            target['effects']=[dict(source_ref='RDXDEF',opcode=op,parameters=[p1,p2,0,0,0,0])]
            stat={86:(21,100),218:(88,3),159:(254,3)}.get(op)
            if stat: target['modified_stats'][stat[0]]=stat[1]
        return dict(schema='bg-redux-state/1',current_area='AR0602',selection=1,game_time=32715,
                    globals={},area_locals={},party=[sender,target],stored_npcs=[],current_area_actors=[],journal=[])

    def capture(self, repeats=2):
        state=self.state()
        query.write(self.folder/'initialized.state.json',state)
        observations=[]
        expected=[('True()',0,1),('False()',0,0)]+[(q,i,0) for i in range(1,repeats+1) for q in query.QUERIES]
        for call,(expression,repetition,value) in enumerate(expected,1):
            before=f'call-{call}-before.state.json';after=f'call-{call}-after.state.json'
            query.write(self.folder/before,state);query.write(self.folder/after,state)
            observations.append(dict(call=call,expression=expression,repetition=repetition,value=value,
                                     before=before,after=after,native_equal=True))
        query.write(self.folder/'final.state.json',state)
        parsed=[dict(expression=q,trigger_id=tid,hand=1,target_count=1,target_runtime_id=101)
                for q,tid in zip(query.QUERIES,(0xec,0xf2))]
        data=dict(schema='bg-redux-query-side-effects-native/1',completed=True,case_id='01-normal',repeats=repeats,
                  sender_runtime_id=100,target_runtime_id=101,parsed_queries=parsed,observations=observations)
        query.write(self.folder/'query-result.json',data)
        log=self.folder/'process.log'
        log.write_text(''.join(name+' has not been implemented yet!\n' for _ in range(repeats)
                               for name in ('WeaponEffectiveVs','WeaponCanDamage')))
        return data,log

    def test_valid_repeats_are_collected_state_observation_not_hidden_state_proof(self):
        _,log=self.capture()
        result=query.validate_capture(self.folder,self.spec,2,log)
        self.assertTrue(result['collected_state_unchanged'])
        self.assertEqual(result['repeated_queries'],4)
        self.assertIsNone(result['hidden_state_unchanged'])
        self.assertTrue(result['expected_frozen_stub_values'])

    def test_fists_selection_rejected_even_when_sword_is_owned(self):
        state=self.state();state['party'][0]['inventory']['equipped']=-25
        with self.assertRaisesRegex(ValueError,'weapon, selection'):
            query.runtime_guard(self.spec,state)

    def test_wrong_ability_rejected(self):
        state=self.state();state['party'][0]['inventory']['equipped_header']=1
        with self.assertRaisesRegex(ValueError,'weapon, selection'):
            query.runtime_guard(self.spec,state)

    def test_missing_or_exhausted_ammunition_rejected(self):
        spec=dict(id='08-bow',weapon='bow01',defense=None)
        for missing in (True,False):
            state=self.state('bow01')
            if missing: state['party'][0]['inventory']['items'].pop()
            else: state['party'][0]['inventory']['items'][1]['usages'][0]=0
            with self.subTest(missing=missing),self.assertRaisesRegex(ValueError,'ammunition'):
                query.runtime_guard(spec,state)

    def test_required_runtime_defense_must_have_derived_value(self):
        spec=dict(id='05-slash100',weapon='sw1h01',defense=(86,100,1))
        state=self.state(defense=spec['defense'])
        query.runtime_guard(spec,state)
        state['party'][1]['modified_stats'][21]=0
        with self.assertRaisesRegex(ValueError,'derived defense'):
            query.runtime_guard(spec,state)

    def test_wrong_target_identity_rejected(self):
        state=self.state();state['party'][1]['script_name']='SomebodyElse'
        with self.assertRaisesRegex(ValueError,'target identity'):
            query.runtime_guard(self.spec,state)

    def test_zero_parse_failure_cannot_masquerade_as_real_stub_calls(self):
        _,log=self.capture();log.write_text('Unknown trigger, returning zero\n')
        with self.assertRaisesRegex(ValueError,'actual resolved stub invocation'):
            query.validate_capture(self.folder,self.spec,2,log)

    def test_changed_parsed_hand_rejected(self):
        data,log=self.capture();data['parsed_queries'][0]['hand']=0
        query.write(self.folder/'query-result.json',data)
        with self.assertRaisesRegex(ValueError,'Parsed EE trigger'):
            query.validate_capture(self.folder,self.spec,2,log)

    def test_failed_positive_control_rejected(self):
        data,log=self.capture();data['observations'][0]['value']=0
        query.write(self.folder/'query-result.json',data)
        with self.assertRaisesRegex(ValueError,'evaluator control failed'):
            query.validate_capture(self.folder,self.spec,2,log)

    def test_missing_repeat_is_not_silently_accepted(self):
        data,log=self.capture();data['observations'].pop()
        query.write(self.folder/'query-result.json',data)
        with self.assertRaisesRegex(ValueError,'coverage incomplete'):
            query.validate_capture(self.folder,self.spec,2,log)

    def test_wrong_case_identity_rejected(self):
        data,log=self.capture();data['case_id']='old-case'
        query.write(self.folder/'query-result.json',data)
        with self.assertRaisesRegex(ValueError,'identity mismatch'):
            query.validate_capture(self.folder,self.spec,2,log)

    def test_native_equal_flag_cannot_hide_damage(self):
        _,log=self.capture()
        path=self.folder/'call-3-after.state.json';changed=query.read(path)
        changed['party'][0]['base_stats'][0]-=1;query.write(path,changed)
        with self.assertRaisesRegex(ValueError,'equality flag contradicts'):
            query.validate_capture(self.folder,self.spec,2,log)

    def test_observed_damage_is_retained_when_reported_honestly(self):
        data,log=self.capture()
        changed=self.state();changed['party'][0]['base_stats'][0]-=1
        for index in range(3,len(data['observations'])+1):
            if index>3: query.write(self.folder/f'call-{index}-before.state.json',changed)
            query.write(self.folder/f'call-{index}-after.state.json',changed)
        query.write(self.folder/'final.state.json',changed)
        data['observations'][2]['native_equal']=False
        query.write(self.folder/'query-result.json',data)
        result=query.validate_capture(self.folder,self.spec,2,log)
        self.assertFalse(result['collected_state_unchanged'])
        self.assertEqual(result['mutation_observations'][0]['changes'][0]['path'],'/party/0/base_stats/0')

    def test_hidden_intercall_reinitialization_rejected(self):
        _,log=self.capture()
        path=self.folder/'call-3-before.state.json';changed=query.read(path)
        changed['game_time']+=1;query.write(path,changed)
        with self.assertRaisesRegex(ValueError,'State discontinuity'):
            query.validate_capture(self.folder,self.spec,2,log)

    def test_minimized_state_snapshot_cannot_prove_invariance(self):
        state=self.state();state['party'][0]['effects']=[dict(opcode=1)]
        del state['party'][0]['spellbook']
        with self.assertRaisesRegex(ValueError,'surface incomplete'):
            query.require_state(state)

    def test_effect_and_global_changes_are_never_normalized_away(self):
        state=self.state();changed=copy.deepcopy(state)
        changed['globals']['NEW_VALUE']=1
        changed['party'][1]['effects'].append(dict(opcode=218,parameters=[3,0]))
        paths={row['path'] for row in query.diff(state,changed)}
        self.assertIn('/globals/NEW_VALUE',paths)
        self.assertIn('/party/1/effects/length',paths)


if __name__=='__main__':unittest.main()
