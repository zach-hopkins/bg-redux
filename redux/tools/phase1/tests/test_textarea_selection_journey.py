"""Pure bounded validator tests; never invoke builds or native processes."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from textarea_selection_validation import CASES, EXPECTED, INVALID, native_contract, owned_terminal, case_inventory
import textarea_selection_journey as journey

def evidence(case):
 trace,value=EXPECTED[case]
 events=[dict(sequence=i+1,kind=x.split(':')[0],value=int(x.split(':')[1]))for i,x in enumerate(trace)]
 result=dict(schema='bg-redux-textarea-selection-regression/1',case=case,completed=True,passed=True,actual_events=list(trace),expected_events=list(trace),actual_value=value,expected_value=value,value_changes=sum(x['kind']=='V'for x in events),selects=sum(x['kind']=='S'for x in events),selected_text_matches=True)
 if case.startswith('unnumbered-'):result.update(mutation_observed=True,old_selection_suppressed=True,before_new_selection_events=['V:40'])
 return result,events
def process():return dict(command=['owned.exe','--case','direct-replace'],pid=3436,exit_code=0,timed_out=False,cleanup='not required')

class IndependentContractTest(unittest.TestCase):
 def test_all_fifteen_declared_contracts(self):
  self.assertEqual(len(CASES),15)
  for case in CASES:
   with self.subTest(case=case):native_contract(case,*evidence(case))
 def test_forged_native_expected_and_pass_do_not_authorize_wrong_trace(self):
  result,events=evidence('direct-replace');result['actual_events']=result['expected_events']=['V:99'];result['actual_value']=result['expected_value']=99
  with self.assertRaises(ValueError):native_contract('direct-replace',result,[dict(sequence=1,kind='V',value=99)])
 def test_wrong_native_expectation_rejected_even_if_actual_correct(self):
  result,events=evidence('direct-replace');result['expected_events']=[]
  with self.assertRaises(ValueError):native_contract('direct-replace',result,events)
 def test_missing_and_duplicate_raw_callbacks_rejected(self):
  result,events=evidence('new-context')
  for bad in (events[:-1],events+[events[-1]],events[::-1]):
   with self.subTest(events=bad),self.assertRaises(ValueError):native_contract('new-context',result,bad)
 def test_wrong_value_and_false_integer_rejected(self):
  for value in (99,True):
   result,events=evidence('direct-replace');result['actual_value']=value
   with self.subTest(value=value),self.assertRaises(ValueError):native_contract('direct-replace',result,events)
 def test_invalid_unselected_is_no_callbacks_and_invalid_value(self):
  result,events=evidence('invalid-unselected');self.assertEqual(result['actual_value'],INVALID);self.assertEqual(events,[]);native_contract('invalid-unselected',result,events)
  result['actual_events']=['V:4294967295']
  with self.assertRaises(ValueError):native_contract('invalid-unselected',result,[dict(sequence=1,kind='V',value=INVALID)])
 def test_unnumbered_generation_evidence_required(self):
  for field in ('mutation_observed','old_selection_suppressed','before_new_selection_events'):
   result,events=evidence('unnumbered-normal-replace');del result[field]
   with self.subTest(field=field),self.assertRaises(ValueError):native_contract('unnumbered-normal-replace',result,events)
 def test_unnumbered_stale_select_rejected(self):
  result,events=evidence('unnumbered-direct-clear');result['actual_events']=result['expected_events']=['V:40','S:40'];result['selects']=1
  with self.assertRaises(ValueError):native_contract('unnumbered-direct-clear',result,events+[dict(sequence=2,kind='S',value=40)])

class OwnedTerminalTest(unittest.TestCase):
 def test_normal_exit_and_crash_are_terminal_but_not_both_success(self):
  p=process();self.assertTrue(owned_terminal(p,p['command'])['success']);p['exit_code']=3221226505
  r=owned_terminal(p,p['command']);self.assertTrue(r['terminal']);self.assertFalse(r['success'])
 def test_timeout_with_owned_wait_and_actual_cleanup_string(self):
  p=process();p.update(exit_code=1,timed_out=True,cleanup='owned process tree termination completed');r=owned_terminal(p,p['command']);self.assertTrue(r['terminal']);self.assertFalse(r['success'])
 def test_pending_and_unproven_cleanup_rejected(self):
  for changes in (dict(exit_code=None,timed_out=True,cleanup='termination pending; not a successful run'),dict(exit_code=1,timed_out=True,cleanup='taskkill timed out'),dict(exit_code=None,launch_error='failure'),dict(exit_code=True)):
   p=process();p.update(changes)
   with self.subTest(changes=changes),self.assertRaises(ValueError):owned_terminal(p,p['command'])
 def test_wrong_owned_command_and_missing_pid_rejected(self):
  p=process()
  with self.assertRaises(ValueError):owned_terminal(p,['other.exe'])
  del p['pid']
  with self.assertRaises(ValueError):owned_terminal(p,p['command'])
 def test_no_invented_cleanup_complete_field_required(self):
  p=process();self.assertNotIn('cleanup_complete',p);self.assertTrue(owned_terminal(p,p['command'])['terminal'])

class CaseInventoryTest(unittest.TestCase):
 def rows(self,n):
  rows=[]
  for case in CASES[:n]:
   p=process();p['command']=['owned.exe','--case',case];rows.append(dict(case=case,process=p,terminal=owned_terminal(p,p['command']),passed=True))
  return rows
 def test_full_fifteen_inventory_required_for_full_success(self):
  r=case_inventory(CASES,self.rows(15));self.assertEqual(r['requested_count'],15);self.assertEqual(r['executed_count'],15);self.assertTrue(r['passed'])
 def test_partial_inventory_lists_missing_and_is_not_pass(self):
  r=case_inventory(CASES,self.rows(2));self.assertFalse(r['complete']);self.assertFalse(r['passed']);self.assertEqual(len(r['missing']),13)
 def test_duplicate_out_of_order_and_unrequested_rejected(self):
  for bad in (self.rows(2)+self.rows(1),self.rows(2)[::-1],[dict(case='unknown',process=process(),terminal=dict(terminal=True),passed=True)]):
   with self.subTest(rows=bad),self.assertRaises(ValueError):case_inventory(CASES,bad)
 def test_missing_terminal_and_failed_case_cannot_pass(self):
  rows=self.rows(15);rows[0]['passed']=False;self.assertFalse(case_inventory(CASES,rows)['passed']);del rows[0]['terminal']
  with self.assertRaises(ValueError):case_inventory(CASES,rows)
 def test_terminal_true_boolean_alone_is_not_evidence(self):
  rows=self.rows(15);rows[0]['terminal']=dict(terminal=True)
  with self.assertRaises(ValueError):case_inventory(CASES,rows)

class CanonicalBuildBindingTest(unittest.TestCase):
 def fixture(self,root):
  source=root/'source';build=root/'build';source.mkdir();build.mkdir()
  for name in ('gemrb/libgemrb_core.dll','gemrb/core/libgemrb_core.dll.a'):
   path=build/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'bound stand-in binary')
  supports=('redux/tools/phase1/cmake/managed-tests.cmake','redux/tools/phase0/managed-test-main.cpp','redux/tools/phase0/cmake/FindGLEW.cmake')
  for name in supports:
   for path in (source/name,build/'build-support'/name):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'bound test support')
  receipt=dict(schema='bg-redux-phase1-build/1',status='built-not-validated',source=str(source),directory=str(build),
   source_unchanged_during_build=True,build_support_unchanged=True,phase0_preservation=dict(source=True,binaries=True,fixture=True),
   source_files={'engine.cpp':'bound-git-inventory'},binaries=journey.engine_binary_inventory(build),
   build_support_files={name:journey.sha(source/name)for name in supports})
  journey.write(build/'build-receipt.json',receipt)
  return source,build,receipt
 def test_canonical_helpers_use_declared_roots_without_private_package(self):
  project,source=Path('/project'),Path('/candidate')
  self.assertEqual(journey.canonical_helpers(project,source),
   {'gui_probe.cpp':project/'tools/phase0/native/gui_probe.cpp','save_probe.cpp':project/'tools/phase0/native/save_probe.cpp',
    'ReduxStart.py':project/'tools/phase0/gui/ReduxStart.py','textarea_selection_regression.h':source/'redux/tools/phase1/native/textarea_selection_regression.h'})
 def test_extra_unreceipted_plugin_is_rejected(self):
  with tempfile.TemporaryDirectory()as tmp:
   source,build,r=self.fixture(Path(tmp))
   with patch.object(journey,'engine_source_inventory',return_value=r['source_files']):
    journey.check_engine_receipt(source,build)
    (build/'gemrb/plugins').mkdir()
    for name in ('Unexpected.dll','Unexpected.DLL'):
     extra=build/'gemrb/plugins'/name;extra.write_bytes(b'not compiled in receipt')
     with self.subTest(name=name),self.assertRaisesRegex(ValueError,'binary inventory'):journey.check_engine_receipt(source,build)
     extra.unlink()
 def test_changed_frozen_compiled_support_is_rejected(self):
  with tempfile.TemporaryDirectory()as tmp:
   source,build,r=self.fixture(Path(tmp));(build/'build-support/redux/tools/phase0/managed-test-main.cpp').write_bytes(b'drift')
   with patch.object(journey,'engine_source_inventory',return_value=r['source_files']):
    with self.assertRaisesRegex(ValueError,'compiled support differs'):journey.check_engine_receipt(source,build)
 def test_wrong_build_receipt_directory_is_not_relabelled(self):
  with tempfile.TemporaryDirectory()as tmp:
   source,build,r=self.fixture(Path(tmp));r['directory']=str(build/'different');journey.write(build/'build-receipt.json',r)
   with self.assertRaisesRegex(ValueError,'source-bound engine'):journey.check_engine_receipt(source,build)

if __name__=='__main__':unittest.main()
