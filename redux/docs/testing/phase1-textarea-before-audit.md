# Independent audit of the TextArea BEFORE matrix

The retained BEFORE run `phase1-local/results/20261022T063003Z-textarea-selection-v2-5489dbb0` is a failed regression matrix: all fifteen requested cases executed in distinct owned processes, with three passes, seven crashes and five completed contract failures. Coverage and terminal cleanup are complete; the matrix is not a pass. This report makes no acceptance claim for the subsequently changed production code.

The raw result SHA256 is `7b680ace7086a8512adb62a8040e2610be7be743bbf14ccf01336a29cae00c31`; artifact manifest `44717789f1734c3e7adef6f1b57805cc00e4acb84f2a8b943182b95f5909140e`. Independent read-only review rehashed all 3147 declared artifacts, 34 historical frozen/run-copied source triplets, the compiled host inputs, original engine build binaries and source bindings, and 3556 currently protected Phase0 files. The external build receipt SHA256 is `8c037666fe1a80ef514d4ac7e3b288301f5c7eda830c8ca0a482647d509bf6cd`; host executable `9f1a1f577c68054894822aa80048c957028eb5fa25989dfa3315554cf5c8d01f`. Current production source legitimately differs and was not required to match the historical BEFORE source.

Each case reached an actual normal stock GUI load with the two-party AR0602 fixture, then dispatched one named unmanaged native control fixture while paused. Raw `dispatch.json` binds the case and nonce. Every terminal receipt matches the exact owned command, PID, integer exit and pinned runner's `Popen.wait` result. All cases finished within their individual 90-second bounds, without timeout. Declared/requested/executed inventories match exactly, with no missing cases. None of these facts upgrades a failed control contract to a pass.

`V:n` denotes ValueChange and `S:n` the Select responder. The independent audit uses its own explicit trace/value map and reads raw JSONL, rather than accepting native `passed` or `expected` declarations.

| Case | BEFORE outcome | Raw callback sequence or crash prefix |
| --- | --- | --- |
| direct-replace | Crash3221226505 | V:40,S:40 |
| direct-remove | Crash3221226505 | V:40,S:40 |
| normal-replace | Pass | V:40,S:40 |
| already-selected | Contract failure | V:40,S:40,S:40 |
| new-context | Contract failure | V:40,S:40,S:40,S:40,S:40 |
| invalid-visible-index | Pass | V:40,S:40,V:4294967295 |
| invalid-value-clear | Crash3221225477 | V:40,S:40,V:4294967295 |
| value-clear | Crash3221226505 | V:40,S:40 |
| value-replace | Crash3221226505 | V:40,S:40 |
| select-reentry | Contract failure | V:40,S:40,S:40 |
| invalid-unselected | Pass | No callbacks |
| unnumbered-direct-clear | Crash3221226505 | V:40,S:40 |
| unnumbered-direct-replace | Crash3221226505 | V:40,S:40 |
| unnumbered-normal-clear | Contract failure | V:40,S:40 |
| unnumbered-normal-replace | Contract failure | V:40,S:40,V:99,S:99,S:99 |

Six crash logs explicitly report a `std::vector<unsigned int>::operator[]` bounds assertion. The invalid-value-clear process instead exits3221225477; its raw log does not provide the same assertion, so no exact crash instruction is inferred. Crash prefixes may match part or all of an expected callback sequence, but their absent completion and AFTER evidence remain failures.

The five completed failures have actual emitted results: already-selected and same-value Select reentry should produce one Select for the original selection, while new-context should produce a second Select for the new context; observed extra Select calls violate those declared contracts. Unnumbered ValueChange clear/replace should suppress the removed/replaced context's Select. Replacement then explicitly selects99, requiring one V:99,S:99 pair. The normal unnumbered replacement instead records stale S:40 and duplicate S:99. Its mutation and pre-new-selection trace are retained, not inferred solely from an event-monitor identity.

Frozen `TextArea.cpp` SHA256 `b9a27b0deaee16ef40703a06522f5245f1fc156fef52eea1091c0f4dcf406826` supports the mechanism: `UpdateState` records context before `MakeSelection`, which can reenter; after that callback path it reads `values[optIdx]` and dispatches Select without revalidating the option collection. ValueChange/Select responders can clear or replace that collection. Frozen `TextArea.h` SHA256 `6f8e8efcef3f5fb316dee70b70633387dfc5ee340f718fc017e738b1f0d47454` defines context by event-monitor id and index; unnumbered construction uses id=-1. The additive unnumbered cases therefore exercise same-id replacement through real callbacks. This is source-supported diagnosis, not a debugger trace of every faulting instruction.

All eight noncrashing cases—including the five failed contracts—have independently equal full collected-world and dictionary snapshots before versus after the fixture returned/threw and its local destructors ran. The seven crashes have no AFTER snapshots: post-call world/dictionary invariance is unobserved for those processes. External protected/candidate boundary inventories, copied inputs and private-game guards still pass for the whole run. The synthetic fixture creates unmanaged controls; it does not measure OS pointer hit testing, original-game parity, general gameplay, immediate control deletion or different-selection nested responder recursion.

The private read-only auditor is `phase1-local/results/textarea-before-audit-20261022-worker.py`. Its new receipt is `20261022T063841Z-textarea-before-audit-d44e4101/audit.json`, SHA256 `228dc2b16dbad06c8fbbcb2741f82a1e383d7fa6b90ce294f65216d53df521f3`. No tests, compilers, native hosts, original game or production edits were executed during this audit. Both the earlier one-case v1 crash and this full v2 failed matrix remain unchanged.
