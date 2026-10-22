# Direct TextArea selection correction and regression design

The reviewed correction is applied and built in fresh candidate `20261022T063419Z-candidate-24f35a4e`. AFTER run `20261022T063920Z-textarea-selection-v2-df237edb` passes all fifteen declared cases in separate owned processes, with exact independent traces/values, post-cleanup world/dictionary equality and all Phase0/candidate/input guards. The core suite passes 231 tests with nine skips and six disabled; the six remaining CTest executables also pass. The ordinary eleven-branch Jaheira/GUI save/fresh-reload run `20261022T064605Z-jaheira-dialogue-dbcdba69` passes on this core (PIDs 9200/4644, exits 0, all preservation guards). Independent AFTER artifact audit, an opt-in real-dialogue direct UpdateState regression and the two-resolution menu regression remain pending.

The correction returns immediately after recursive span selection, commits the option context before SetValue, and dispatches Select only if the generation, context, selected span/index and scalar value survive ValueChange. ClearSelectOptions invalidates pending commits through a new private generation counter, including unnumbered replacements. Existing frozen candidates and BEFORE evidence remain unchanged. The added member changes the C++ object size: use newly rebuilt plugins and external hosts with the same headers.

The complete BEFORE batch `20261022T063003Z-textarea-selection-v2-5489dbb0` executes all fifteen declared cases in separate terminal processes: three pass (`normal-replace`, `invalid-visible-index`, `invalid-unselected`), seven crash, and five return failed contracts. Repeated/direct selection produces duplicate Select callbacks; ValueChange removal/replacement can crash or dispatch a stale Select. The independently pinned Python validator suite passes18 tests. All Phase0, candidate and immutable-input preservation checks pass. No failed case is dropped from the inventory. The v1 isolated assertion below remains preserved separately.

Coordinator BEFORE execution, October 22 UTC: the dedicated private host builds successfully against unchanged candidate `20261022T051113Z-candidate-df3a5c5e`. Run `20261022T061836Z-textarea-selection-0736a57d` loads the stock two-party save through the normal GUI path, then executes only `direct-replace`. PID3436 terminates after8.038 seconds with exit3221226505 and the `std::vector<unsigned int>::operator[]` bounds assertion. Its flushed native trace contains exactly V40, S40 before the selection handler replaces the options; the host terminal receipt and AFTER snapshots are absent because the process asserts. This is a reproduced failure, not a missing-evidence pass. Phase0 source/binaries/fixture, candidate source/binaries and immutable inputs all pass the outer preservation checks. No engine fix has been applied.

Private source package `phase1-local/textarea-selection-preparation-20261022-worker-a` retains the original eleven-case header byte-for-byte and adds four unnumbered ValueChange clear/replace cases, through both direct and normal selection entry. Its separate v2 successor adds independent Python contracts, owned terminal receipts and explicit case inventories, and is used unchanged for both fifteen-case batches. The host compares full collected world and sorted dictionary snapshots after fixture cleanup on normal return; a guard-installed flag alone is insufficient. Ordinary dialogue/save/reload and broad-menu regression on the corrected core are also required.

The AFTER synthetic execution validates the declared control contracts, with broader runtime regressions still required. The BEFORE execution does not establish a native pass. The two earlier [confirmed direct-entry assertion runs](../compatibility/phase1-textarea-update-state-reentrancy.md) remain failed evidence. Completing the earlier ordinary dialogue through SelectAvailableOption did not close that public UpdateState defect.

## Proposed production contract

For a valid option value, first validate/map it to its visible index. If the index differs from the actual selected span, call MakeSelection and immediately return: the recursive UpdateStateWithSelection entry owns the value update and one Select dispatch. Do not access values or the selector after that callback chain. Caching values before MakeSelection alone still permits duplicate dispatch.

For the already-selected index with a changed option context, commit that context before SetValue. Preserve Control's ordering: dictionary redraw, then ValueChange, then Select when the same selection context remains valid. Committing context first makes benign same-value dictionary redraw and Select-handler same-selection reentry no-ops. A repeated selection in an unchanged context must not dispatch another Select. A new numbered option context at the same visible index must permit one fresh Select even when the scalar value did not change.

SetValue is itself a callback boundary. After it returns, check that the option generation/context and selection still represent the event being committed before dispatching Select. ValueChange clearing/replacing options invalidates the pending old Select; a later explicit selection of the new options is a distinct event. Do not dereference a selector saved before SetValue without validation. A monotonically changing options-generation token is stronger than pointer identity (allocators can reuse addresses) or an unnumbered context ID of -1; use an explicit generation if claiming the general replacement guarantee.

The invalid-value path needs the same treatment: deselect a currently selected span through MakeSelection and return to its recursive commit; when no actual span is selected, commit INVALID_VALUE without dereferencing the selector afterwards. Out-of-range visible indices and -1 must not emit Select. Do not use `index != -1` alone to recognize a valid selected span: an arbitrary invalid visible index can also be stored by MakeSelection. Preserve ValueChange on an actual valid→invalid value change.

Normal close requests are deferred by WindowManager while action handlers run. Arbitrary immediate deletion of the executing TextArea and same-handler recursive dispatch of a different selection interact with the existing responder-stack lifetime/assertion contract and are outside this narrow repair. Do not claim arbitrary callback lifetime safety.

## External fixture

The NEW [textarea_selection_regression.h](../../tools/phase1/native/textarea_selection_regression.h) exposes:

```cpp
static void TextAreaSelectionRegression(const std::string& out, const std::string& caseName);
```

The coordinator should invoke one named case per fresh owned bounded native process after normal load, using a frozen host/header/source/build closure. This isolation matters: the unchanged core can assert before producing result.json. Every case writes begin.json before entry and flushes an events.jsonl record before callback mutation, preserving useful failure evidence. Missing/incomplete results, assertions, callback/value mismatches and timeouts fail; they cannot be converted to a pass because another route succeeds.

The fixture uses an unmanaged real Window/TextArea, the existing NORMAL font and synthetic ASCII text. Nonconsecutive option values 10 and 40 distinguish values from visible indices. It exercises the private control dictionary binding and ordinary redraw reentry. Constructor key Selected and private RDXTASELECT are saved and restored on normal return/unwinding, including prior absence. The outer host must independently verify dictionary/world preservation; a process assertion cannot unwind C++ guards and must remain isolated to its private process. It requests no OS input or gameplay callbacks.

| Case | Required callback trace | Purpose |
| --- | --- | --- |
| direct-replace | V40, S40 | Select replaces two options with one; no stale index read or duplicate dispatch |
| direct-remove | V40, S40 | Select deletes all options; direct public entry returns safely |
| normal-replace | V40, S40 | Public normal selector route retains exactly-once behavior |
| already-selected | V40, S40 | Subsequent direct/normal reselection is a no-op; selected text remains beta |
| new-context | V40, S40, S40 | Recreated numbered context fires once without a second ValueChange |
| invalid-visible-index | V40, S40, VINVALID | Out-of-range deselection has no Select |
| invalid-value-clear | V40, S40, VINVALID | ValueChange clears options during invalid-value commit safely |
| value-clear | V40 | ValueChange removes options, canceling stale Select |
| value-replace | V40, V99, S99 | ValueChange replaces context; only explicit new selection dispatches |
| select-reentry | V40, S40 | Select reenters the same value without recursive handler dispatch |
| invalid-unselected | empty | Invalid value/index on an unselected control has no callbacks |

V denotes ValueChange, S denotes Select, INVALID is unsigned 4294967295. ValueChange-cancellation traces are the proposed explicit contract, not a claim about unchanged-engine behavior. Exactly-once traces, final values and the already-selected text are asserted against actual native callbacks, not mock callback counters standing in for engine dispatch. Each result records scope and reports gameplay_acceptance:false.

Original fixture preparation launched no compiler, tests or native runtime. The coordinator executions above establish build/link success, native BEFORE failures and the full fifteen-case AFTER pass with successful-case dictionary/world preservation. Ordinary dialogue/save/reload, menu regression and independent AFTER audit remain for coordinator validation. No historical helper or result files were edited for this external fixture.
