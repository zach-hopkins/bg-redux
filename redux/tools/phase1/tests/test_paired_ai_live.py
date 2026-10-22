import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch


spec=importlib.util.spec_from_file_location('candidate_paired_ai',Path(__file__).resolve().parents[1]/'paired_ai_live.py')
adapter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class NativeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        party=[dict(runtime_id=10,inventory=dict(equipped=0,items=[dict(slot=35,resref='SW1H02')])),dict(runtime_id=11)]
        foe=dict(runtime_id=20,script_name='RDXFOE',modified_stats=[200])
        self.before=dict(schema='bg-redux-state/1',game_time=100,party=party,current_area_actors=[foe])
        self.after=copy.deepcopy(self.before)
        self.after.update(game_time=180,globals=dict(RDXAIDONE=1,RDXFOESEEN=1,RDXBRANCH=115))
        self.result=dict(completed=True,steps=89,events=['ReduxStart.PopulateLoad','press:load.baseline-row',
            'ReduxStart.Ready','clock:resume','clock:pause'])
        self.clock=dict(schema='bg-redux-live-clock/1',ticks_per_second=15,samples=[])
        for index in range(89):
            self.clock['samples'].append(dict(sample=index,elapsed_ms=index*300,
                game_time=100 if index<5 else min(180,96+index),
                phase='paused-initial' if index<5 else 'running' if index<85 else 'paused-final',
                action_trace=[dict(runtime_id=10,action_id=105,current_action_target=20),dict(runtime_id=20,name='RDXFOE')]))

    def observe(self):
        for name,data in [('gui-result.json',self.result),('clock-before.state.json',self.before),
                          ('clock-after.state.json',self.after),('clock-samples.json',self.clock)]:
            adapter.write(self.root/name,data)
        return adapter.observe_native(self.root,dict(first=115),115)

    def test_exact_branch_and_target_with_no_damage_is_valid_without_dpr_claim(self):
        observed=self.observe()
        self.assertTrue(observed['original_visual_branch_matches'])
        self.assertEqual(observed['foe_hp_before'],observed['foe_hp_after'])
        self.assertFalse(observed['whole_ai_or_dpr_parity'])
        self.assertFalse(observed['original_exact_action_or_target_sample'])

    def test_old_fallback_is_completed_execution_but_compatibility_difference(self):
        self.after['globals']['RDXBRANCH']=118
        observed=self.observe()
        self.assertFalse(observed['original_visual_branch_matches'])
        self.assertTrue(observed['native_action_target_observed'])

    def test_marker_without_sampled_attack_rejected(self):
        for row in self.clock['samples']: row['action_trace'][0]['action_id']=63
        with self.assertRaisesRegex(ValueError,'not sampled'): self.observe()

    def test_attack_against_wrong_target_rejected(self):
        for row in self.clock['samples']: row['action_trace'][0]['current_action_target']=11
        with self.assertRaisesRegex(ValueError,'not sampled'): self.observe()

    def test_only_paused_attack_cannot_satisfy_running_observation(self):
        for row in self.clock['samples'][5:85]: row['action_trace']=[]
        with self.assertRaisesRegex(ValueError,'not sampled'): self.observe()

    def test_attack_needs_same_sample_declared_target_identity(self):
        self.clock['samples'][5]['action_trace'][1]['name']='another_actor'
        with self.assertRaisesRegex(ValueError,'same-sample'): self.observe()

    def test_ambiguous_foe_rejected(self):
        self.after['current_area_actors']*=2
        with self.assertRaisesRegex(ValueError,'ambiguous'): self.observe()

    def test_runtime_identity_reuse_rejected(self):
        self.after['current_area_actors'][0]['runtime_id']=10
        with self.assertRaisesRegex(ValueError,'identity'): self.observe()

    def test_missing_equipped_weapon_rejected_even_with_correct_branch(self):
        self.after['party'][0]['inventory']['items']=[]
        with self.assertRaisesRegex(ValueError,'weapon'): self.observe()

    def test_outside_prepared_tail_rejected(self):
        self.after['globals']['RDXBRANCH']=119
        with self.assertRaisesRegex(ValueError,'prepared tail'): self.observe()

    def test_boolean_marker_is_not_an_integer_branch(self):
        self.after['globals']['RDXBRANCH']=True
        with self.assertRaisesRegex(ValueError,'prepared tail'): self.observe()

    def test_unseen_foe_rejected(self):
        self.after['globals']['RDXFOESEEN']=0
        with self.assertRaisesRegex(ValueError,'visibility'): self.observe()

    def test_partial_run_rejected(self):
        self.result['completed']=False
        with self.assertRaisesRegex(ValueError,'incomplete'): self.observe()

    def test_bypassed_load_boundary_rejected(self):
        self.result['events'].remove('press:load.baseline-row')
        with self.assertRaisesRegex(ValueError,'boundary'): self.observe()

    def test_duplicate_sample_index_rejected(self):
        self.clock['samples'][20]['sample']=19
        with self.assertRaisesRegex(ValueError,'phases/count'): self.observe()

    def test_paused_clock_drift_rejected(self):
        self.clock['samples'][-1]['game_time']+=1
        with self.assertRaisesRegex(ValueError,'boundaries'): self.observe()

    def test_stale_before_state_rejected(self):
        self.before['game_time']=99
        with self.assertRaisesRegex(ValueError,'boundaries'): self.observe()

    def test_nonmonotonic_wall_elapsed_rejected(self):
        self.clock['samples'][20]['elapsed_ms']=0
        with self.assertRaisesRegex(ValueError,'ordering'): self.observe()


class InputBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_frozen_input_refuses_changed_source_and_preserves_destination(self):
        source=self.root/'input';source.write_bytes(b'authorized')
        digest=adapter.sha(source)
        destination=self.root/'frozen'
        adapter.freeze(source,destination,digest)
        source.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed'): adapter.freeze(source,destination,digest)
        self.assertEqual(destination.read_bytes(),b'authorized')

    def test_frozen_input_refuses_overwrite_of_historical_collision(self):
        source=self.root/'input';source.write_bytes(b'new')
        destination=self.root/'frozen';destination.write_bytes(b'historical')
        with self.assertRaisesRegex(ValueError,'collision'): adapter.freeze(source,destination)
        self.assertEqual(destination.read_bytes(),b'historical')

    def test_manifest_rejects_traversal_absolute_and_drive_members(self):
        for name in ('../outside','C:/outside','/outside','a/../../outside'):
            with self.subTest(name=name),self.assertRaises(ValueError): adapter.member(self.root,name)

    def driver(self):
        for name in ('gui_probe.cpp','save_probe.cpp','host.exe','gemrb/libgemrb_core.dll','bin/g++.exe'):
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(name.encode())
        receipt=dict(command=['g++','gui_probe.cpp'],exit_code=0,sources={name:adapter.sha(self.root/name)
            for name in ('gui_probe.cpp','save_probe.cpp')},binary_sha256=adapter.sha(self.root/'host.exe'),
            engine_dll_sha256=adapter.sha(self.root/'gemrb/libgemrb_core.dll'),compiler_sha256=adapter.sha(self.root/'bin/g++.exe'))
        args=types.SimpleNamespace(probe_build_receipt=self.root/'build.json',probe=self.root/'host.exe',
            engine_build_root=self.root,prefix=self.root,probe_source_root=self.root)
        return args,receipt

    def test_external_driver_requires_real_gui_host_and_exact_core(self):
        args,receipt=self.driver();adapter.write(args.probe_build_receipt,receipt)
        self.assertEqual(len(adapter.check_driver(args)[1]),2)
        (self.root/'gemrb/libgemrb_core.dll').write_bytes(b'other candidate')
        with self.assertRaisesRegex(ValueError,'pin drift'): adapter.check_driver(args)

    def test_menu_host_cannot_substitute_for_live_clock_host(self):
        args,receipt=self.driver();receipt['command']=['g++','menu_probe.cpp']
        adapter.write(args.probe_build_receipt,receipt)
        with self.assertRaisesRegex(ValueError,'normal-loop'): adapter.check_driver(args)

    def test_included_serializer_source_must_match_receipt(self):
        args,receipt=self.driver();adapter.write(args.probe_build_receipt,receipt)
        (self.root/'save_probe.cpp').write_bytes(b'changed serializer')
        with self.assertRaisesRegex(ValueError,'source pin'): adapter.check_driver(args)

    def test_failed_build_cannot_reuse_existing_binary(self):
        args,receipt=self.driver();receipt['exit_code']=1;adapter.write(args.probe_build_receipt,receipt)
        with self.assertRaisesRegex(ValueError,'build failed'): adapter.check_driver(args)

    def test_wrong_preparation_rejected_before_loading_oracle_validator(self):
        path=self.root/'preparation.json';adapter.write(path,dict(nonce='E1AEF966'))
        with self.assertRaisesRegex(ValueError,'exact authorized'):
            adapter.original_inputs(self.root,path,[],self.root)

    def test_wrong_nonce_in_preparation_is_not_accepted_from_filename(self):
        path=self.root/'preparation.json'
        adapter.write(path,dict(run_id='20261021T230944Z-original-live-6efa5f54',nonce='STALE'))
        with patch.object(adapter,'sha',return_value=adapter.PREPARATION_SHA):
            with self.assertRaisesRegex(ValueError,'nonce differs'):
                adapter.original_inputs(self.root,path,[],self.root)

    def test_wrong_case_and_changed_visual_attestation_rejected_before_visual_validator(self):
        prep=self.root/'preparation.json';obs=self.root/'observed.json'
        adapter.write(prep,dict(run_id='20261021T230944Z-original-live-6efa5f54',nonce='E1AEF966',
                               cases=[dict(spec=dict(id=c)) for c in adapter.CASES]))
        validator=types.SimpleNamespace(validate_capture=lambda *args:self.fail('Untrusted visual input reached validator'))
        for case in ('wrong-case','ai-imoen-stock'):
            adapter.write(obs,dict(case=case,observations=['wrong nonce or branch']))
            def fake_sha(path):
                return adapter.PREPARATION_SHA if Path(path)==prep else 'changed-attestation'
            with self.subTest(case=case),patch.object(adapter,'sha',side_effect=fake_sha),patch.object(adapter,'load',return_value=validator):
                with self.assertRaisesRegex(ValueError,'observation'):
                    adapter.original_inputs(self.root,prep,[obs],self.root)


if __name__=='__main__': unittest.main()
