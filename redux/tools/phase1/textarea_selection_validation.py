"""Pure independent contracts: no helper/native expected fields are authoritative."""
INVALID=4294967295
EXPECTED={
 'direct-replace':(['V:40','S:40'],40),
 'direct-remove':(['V:40','S:40'],40),
 'normal-replace':(['V:40','S:40'],40),
 'already-selected':(['V:40','S:40'],40),
 'new-context':(['V:40','S:40','S:40'],40),
 'invalid-visible-index':(['V:40','S:40','V:4294967295'],INVALID),
 'invalid-value-clear':(['V:40','S:40','V:4294967295'],INVALID),
 'value-clear':(['V:40'],40),
 'value-replace':(['V:40','V:99','S:99'],99),
 'select-reentry':(['V:40','S:40'],40),
 'invalid-unselected':([],INVALID),
 'unnumbered-direct-clear':(['V:40'],40),
 'unnumbered-direct-replace':(['V:40','V:99','S:99'],99),
 'unnumbered-normal-clear':(['V:40'],40),
 'unnumbered-normal-replace':(['V:40','V:99','S:99'],99),
}
CASES=tuple(EXPECTED)
def require(value,message):
 if not value:raise ValueError(message)
def native_contract(case,result,events):
 require(case in EXPECTED,'Unknown declared case')
 expected,value=EXPECTED[case]
 require(result.get('case')==case and result.get('schema')=='bg-redux-textarea-selection-regression/1','Wrong result identity')
 require(result.get('completed')is True and result.get('passed')is True,'Native contract incomplete/failed')
 require(result.get('actual_events')==expected and type(result.get('actual_value'))is int and result['actual_value']==value,'Actual trace/value differs from independent Python contract')
 require(result.get('expected_events')==expected and result.get('expected_value')==value,'Native expected declarations differ from independent contract')
 require([e.get('sequence')for e in events]==list(range(1,len(events)+1)),'Missing/duplicate event prefix')
 require(all(set(e)=={'sequence','kind','value'}and e['kind']in('V','S')and type(e['value'])is int for e in events),'Malformed callback evidence')
 require([f"{e['kind']}:{e['value']}"for e in events]==expected,'Raw callback evidence differs from independent contract')
 require(type(result.get('value_changes'))is int and type(result.get('selects'))is int and result['value_changes']==sum(e['kind']=='V'for e in events)and result['selects']==sum(e['kind']=='S'for e in events),'Wrong callback counts')
 require(result.get('selected_text_matches')is True,'Selected text check failed')
 if case.startswith('unnumbered-'):
  require(result.get('mutation_observed')is True and result.get('old_selection_suppressed')is True and result.get('before_new_selection_events')==['V:40'],'Generation mutation/suppression evidence missing')
 return dict(events=expected,value=value,independent_contract=True)
def owned_terminal(process,expected_command):
 """Use the actual baseline.execute schema, whose exit_code is Popen.wait's
 return for that OWNED process handle. PID liveness queries risk PID reuse.
 A pending timeout/launch failure has no authoritative owned exit_code.
 """
 require(process.get('command')==expected_command,'Owned command identity differs')
 require(type(process.get('pid'))is int and process['pid']>0 and type(process.get('exit_code'))is int,'Owned process has no terminal wait result')
 require(type(process.get('timed_out'))is bool,'Timeout status missing')
 if process['timed_out']:require(process.get('cleanup')=='owned process tree termination completed','Timeout cleanup not authoritatively completed')
 else:require(process.get('cleanup')=='not required','Unexpected non-timeout cleanup status')
 return dict(schema='bg-redux-owned-native-terminal/1',pid=process['pid'],terminal=True,exit_code=process['exit_code'],timed_out=process['timed_out'],cleanup=process['cleanup'],evidence='Pinned baseline_runner.execute: exit_code returned by owned subprocess.Popen.wait',command=expected_command,success=process['exit_code']==0 and not process['timed_out'])
def case_inventory(requested,stages):
 require(bool(requested)and len(requested)==len(set(requested))and all(c in EXPECTED for c in requested),'Invalid requested inventory')
 executed=[r.get('case')for r in stages if 'process'in r]
 require(len(executed)==len(set(executed))and executed==list(requested[:len(executed)]),'Wrong/duplicate execution inventory')
 for row in stages:
  if 'process'in row:
   expected_terminal=owned_terminal(row['process'],row['process'].get('command'))
   require(row.get('terminal')==expected_terminal,'Executed case lacks matching authoritative terminal receipt')
 complete=executed==list(requested)
 return dict(declared_cases=list(CASES),declared_count=15,requested=list(requested),requested_count=len(requested),executed=executed,executed_count=len(executed),missing=list(requested[len(executed):]),complete=complete,full_fifteen_executed=executed==list(CASES),passed=complete and all(r.get('passed')is True for r in stages)and len(stages)==len(requested))
