import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).parents[1]))
import saved_npc_color_journey as journey
import weapon_query_observer as shared
from test_weapon_query_validation import setup_case,write


def stage(folder,reload=False,color=237):
    _,_,before,_=setup_case()
    row=dict(expected_ready_globals=dict(RDXCCASE=1,RDXCNONCE=123,RDXCSTAGE=2,RDXCREADY=1))
    before['game_time']=100;before['current_area_actors']=[];before['globals']={}
    after=copy.deepcopy(before);after['game_time']=108;after['globals']=row['expected_ready_globals'].copy()
    actor=copy.deepcopy(after['party'][0]);actor.update(runtime_id=10170,script_name='RDXCOLOR',name='NPC',position=[3781,2801])
    actor['base_stats'][205]=0x6100;actor['base_stats'][231]=1;actor['base_stats'][234]=128
    actor['base_stats'][212]=actor['modified_stats'][212]=color*0x01010101
    after['current_area_actors']=[actor]
    if reload:
        before=copy.deepcopy(after);before['game_time']=100
    samples=[]
    for i in range(17):
        phase='paused-initial' if i<5 else 'running' if i<13 else 'paused-final'
        samples.append(dict(sample=i,phase=phase,elapsed_ms=i*250,game_time=100 if i<5 else min(108,96+i)))
    records={'clock-before.state.json':before,'clock-after.state.json':after,
        'clock-samples.json':dict(schema='bg-redux-live-clock/1',samples=samples,ticks_per_second=15),
        'gui-result.json':dict(completed=True,steps=17,events=['ReduxStart.PopulateLoad','press:load.baseline-row','ReduxStart.Ready','clock:resume','clock:pause']),
        'color-before-save.state.json':copy.deepcopy(after),'color-after-save.state.json':copy.deepcopy(after),
        'color-save-result.json':dict(schema='bg-redux-color-save-native/1',save_return_code=0,forced=False,directories=['owned/save'])}
    for name,value in records.items():write(folder/name,value)
    return row,records


class ColorStageEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.folder=Path(self.temp.name)
        self.row,self.records=stage(self.folder)

    def validate(self,reload=False):return journey.validate_stage(self.folder,self.row,8,reload)

    def test_creation_then_fresh_reload_observations_are_distinct(self):
        result=self.validate()
        self.assertIsNone(result['before'])
        self.assertEqual(result['after_clock']['base_color212'],0xedededed)
        self.assertEqual(result['after_save']['modified_color212'],0xedededed)
        self.assertEqual(result['samples'],17)
        with self.assertRaisesRegex(ValueError,'Exactly one runtime'):self.validate(True)
        row,_=stage(self.folder,True,color=46)
        result=journey.validate_stage(self.folder,row,8,True)
        # Different actual color is characterized, never waived or rejected as an assumed oracle mismatch.
        self.assertEqual(result['before']['base_leather_byte'],46)
        self.assertEqual(result['after_clock']['modified_leather_byte'],46)

    def test_ready_nonce_and_runtime_identity_cannot_be_faked(self):
        for mutation in ['wrong_nonce','missing_ready','duplicate','wrong_palette','boolean_color']:
            data=copy.deepcopy(self.records['clock-after.state.json'])
            if mutation=='wrong_nonce':data['globals']['RDXCNONCE']=124
            elif mutation=='missing_ready':del data['globals']['RDXCREADY']
            elif mutation=='duplicate':data['current_area_actors']*=2
            elif mutation=='wrong_palette':data['current_area_actors'][0]['base_stats'][205]=0xe200
            else:data['current_area_actors'][0]['base_stats'][212]=True
            write(self.folder/'clock-after.state.json',data)
            with self.assertRaises(ValueError):self.validate()

    def test_forced_or_failed_or_ambiguous_save_is_not_characterized(self):
        valid=self.records['color-save-result.json']
        for mutation in [dict(forced=True),dict(save_return_code=1),dict(save_return_code=False),dict(directories=[]),dict(directories=['a','b'])]:
            write(self.folder/'color-save-result.json',valid|mutation)
            with self.assertRaisesRegex(ValueError,'Ordinary color save'):self.validate()

    def test_clock_coverage_pause_progress_and_strict_sample_types(self):
        valid=self.records['clock-samples.json']
        for mutation in ['missing','phase','paused_drift','no_progress','bool_index','decreasing_time']:
            data=copy.deepcopy(valid)
            if mutation=='missing':data['samples'].pop()
            elif mutation=='phase':data['samples'][8]['phase']='paused-final'
            elif mutation=='paused_drift':data['samples'][1]['game_time']=101
            elif mutation=='no_progress':
                for s in data['samples']:s['game_time']=100
            elif mutation=='bool_index':data['samples'][1]['sample']=True
            else:data['samples'][9]['elapsed_ms']=0
            write(self.folder/'clock-samples.json',data)
            with self.assertRaises(ValueError):self.validate()

    def test_missing_stale_and_discontinuous_evidence_is_failure(self):
        with self.assertRaisesRegex(ValueError,'Stale'):
            journey.validate_stage(self.folder,self.row,8,False,started_ns=2**63)
        changed=copy.deepcopy(self.records['color-before-save.state.json']);changed['game_time']+=1
        write(self.folder/'color-before-save.state.json',changed)
        with self.assertRaisesRegex(ValueError,'continuity'):self.validate()
        (self.folder/'clock-before.state.json').unlink()
        with self.assertRaises(OSError):self.validate()


class ColorHostSourceTests(unittest.TestCase):
    def test_only_exact_frozen_gui_anchors_can_generate_host(self):
        raw=(Path(journey.__file__).parent/'native/phase0_gui_probe_snapshot.cpp').read_bytes()
        generated=journey.instrument_gui(raw)
        self.assertEqual(generated.count(b'ColorSaveAfterClock(out);'),1)
        self.assertIn(b'args["--save-after-clock"] != "1"',generated)
        self.assertIn(b'#include "phase0_save_probe_snapshot.cpp"',generated)
        for wrong in [raw.replace(b'static Window* WindowIn',b'static Window* Changed'),raw+b'\nstatic Window* WindowIn']:
            with self.assertRaisesRegex(ValueError,'anchor'):journey.instrument_gui(wrong)

    def test_nested_private_wrappers_do_not_enter_shared_asset_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);wrapper=root/'case/create/private-game';(wrapper/'data').mkdir(parents=True)
            (wrapper/'data/shared.bif').write_bytes(b'shared asset')
            (wrapper/'GemRB.log').write_bytes(b'private log')
            rows=journey.output_manifest(root)
            self.assertEqual(set(rows),{'case/create/private-game/GemRB.log'})

    def test_preparation_rejects_executed_status_or_wrong_case_without_game_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'prep.json';write(path,dict(schema='bg-redux-phase1-color-preparation/1',phase='prepared-not-executed',executed=True))
            with self.assertRaisesRegex(ValueError,'preparation failed'):journey.preparation(path,None)


class HistoricalConstructionBindingTests(unittest.TestCase):
    OLD=b'import json\nMAX=64\ndef sav_records(data):\n    return [data]\ndef prepare():\n    return MAX\n'
    CURRENT=OLD.replace(b'return [data]',b'return list(data)')

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.old=self.root/'historical.py';self.current=self.root/'current.py'
        self.old.write_bytes(self.OLD);self.current.write_bytes(self.CURRENT)
        self.prep=dict(generator_sha256=journey.fixtures.digest(self.OLD))

    def test_explicit_historical_source_requires_exact_hash_and_parser_only_ast_difference(self):
        binding=journey.bind_construction_source(self.prep,self.old,self.current)
        self.assertEqual(binding['mode'],'explicit-historical-source')
        self.assertTrue(binding['ast_proof']['outside_parser_ast_identical'])
        self.assertTrue(binding['ast_proof']['parser_ast_changed'])
        self.assertFalse(binding['ast_proof']['historical_code_executed'])
        self.assertEqual(binding['construction_source_sha256'],self.prep['generator_sha256'])
        self.old.write_bytes(self.OLD+b'\n')
        with self.assertRaisesRegex(ValueError,'hash differs'):
            journey.bind_construction_source(self.prep,self.old,self.current)

    def test_no_implicit_historical_fallback_when_current_hash_differs(self):
        with self.assertRaisesRegex(ValueError,'explicit --construction-source'):
            journey.bind_construction_source(self.prep,current=self.current)
        self.current.write_bytes(self.OLD)
        binding=journey.bind_construction_source(self.prep,current=self.current)
        self.assertEqual(binding['mode'],'current-exact-generator')

    def test_constructor_constant_import_and_parser_signature_changes_rejected(self):
        for changed in [self.CURRENT.replace(b'return MAX',b'return 0'),self.CURRENT.replace(b'MAX=64',b'MAX=65'),
                        self.CURRENT.replace(b'import json',b'import os'),self.CURRENT.replace(b'sav_records(data)',b'sav_records(data, extra=None)')]:
            self.current.write_bytes(changed)
            with self.assertRaisesRegex(ValueError,'outside allowlisted'):
                journey.bind_construction_source(self.prep,self.old,self.current)
        for changed in [self.OLD.replace(b'def sav_records',b'def other'),self.OLD+b'def sav_records(data):\n    return []\n']:
            with self.assertRaisesRegex(ValueError,'Exactly one'):
                journey.construction_ast_proof(changed,self.CURRENT)

    def test_source_frozen_consumer_and_proof_tamper_fail_rechecks(self):
        for index,target in enumerate(['historical','frozen','consumer','proof']):
            self.old.write_bytes(self.OLD);self.current.write_bytes(self.CURRENT)
            out=self.root/str(index);out.mkdir()
            receipt=journey.freeze_construction_source(journey.bind_construction_source(self.prep,self.old,self.current),out)
            journey.check_construction_source(receipt) # before a hypothetical launch
            if target=='historical':self.old.write_bytes(self.OLD+b'\n')
            elif target=='frozen':Path(receipt['frozen_source']).write_bytes(self.OLD+b'\n')
            elif target=='consumer':self.current.write_bytes(self.CURRENT+b'\n')
            else:
                proof=shared.read(receipt['proof_file']);proof['ast_proof']['outside_parser_ast_identical']=False
                shared.write(Path(receipt['proof_file']),proof)
            with self.assertRaises(ValueError):journey.check_construction_source(receipt)
            with self.assertRaises(ValueError):journey.check_construction_source(receipt) # final guard also fails

    def test_historical_module_is_parsed_without_execution(self):
        old=b'raise AssertionError("must never execute old code")\n'+self.OLD
        current=b'raise AssertionError("must never execute old code")\n'+self.CURRENT
        self.old.write_bytes(old);self.current.write_bytes(current)
        binding=journey.bind_construction_source(dict(generator_sha256=journey.fixtures.digest(old)),self.old,self.current)
        self.assertTrue(binding['ast_proof']['outside_parser_ast_identical'])


if __name__=='__main__':unittest.main()
