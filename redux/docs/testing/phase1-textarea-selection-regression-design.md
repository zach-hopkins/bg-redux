# Direct TextArea selection correction and regression design

Coordinator BEFORE execution, October 22 UTC: the dedicated private host builds successfully against unchanged candidate `20261022T051113Z-candidate-df3a5c5e`. Run `20261022T061836Z-textarea-selection-0736a57d` loads the stock two-party save through the normal GUI path, then executes only `direct-replace`. PID3436 terminates after8.038 seconds with exit3221226505 and the `std::vector<unsigned int>::operator[]` bounds assertion. Its flushed native trace contains exactly V40, S40 before the selection handler replaces the options; the host terminal receipt and AFTER snapshots are absent because the process asserts. This is a reproduced failure, not a missing-evidence pass. Phase0 source/binaries/fixture, candidate source/binaries and immutable inputs all pass the outer preservation checks. No engine fix has been applied.

Private source package `phase1-local/textarea-selection-preparation-20261022-worker-a` retains the original eleven-case header byte-for-byte and adds four unnumbered ValueChange clear/replace cases, through both direct and normal selection entry. The host compares full collected world and sorted dictionary snapshots after fixture cleanup on normal return; a guard-installed flag alone is insufficient. The remaining BEFORE cases, production correction, fresh source-bound build and all fifteen AFTER cases remain unexecuted. Ordinary dialogue/save/reload and broad-menu regression on a corrected core are also required.

The production correction remains design work. The BEFORE execution does not fix the engine or establish a native pass. The two earlier [confirmed direct-entry assertion runs](../compatibility/phase1-textarea-update-state-reentrancy.md) remain failed evidence. Completing the ordinary dialogue through SelectAvailableOption did not close that public UpdateState defect.

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

Original fixture preparation launched no compiler, tests or native runtime. The coordinator execution above now establishes build/link success and a native direct-replace BEFORE assertion. The broader before/after matrix, all cases on a corrected engine, ordinary dialogue regression and successful-case dictionary/world preservation remain for coordinator validation. No existing engine, helper or historical-result files were edited for this external fixture.
