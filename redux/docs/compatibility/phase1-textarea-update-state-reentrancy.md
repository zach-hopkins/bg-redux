# Confirmed direct TextArea::UpdateState selection reentrancy defect

Status: **correction passes the fifteen-case synthetic AFTER matrix and ordinary dialogue/save/reload; direct-API real-dialogue and menu regressions pending**. The [selection regression design and execution](../testing/phase1-textarea-selection-regression-design.md) records the isolated direct-entry reproduction, all fifteen BEFORE cases and the reviewed generation/context source correction. Fresh candidate `20261022T063419Z-candidate-24f35a4e` builds, passes its core suite and all fifteen dedicated cases with world/dictionary preservation. The ordinary eleven-branch Jaheira/GUI save/fresh-reload regression also passes. Independent AFTER artifact audit, a direct-API real-dialogue rerun and the fresh menu regression remain pending. The historical native evidence and unchanged-source analysis below describe the defect before that correction.

A direct public `TextArea::UpdateState(4)` selection of Jaheira's first response crashes the unchanged candidate core after the response handler replaces the options. The separate ordinary journey's use of the public mouse/key selection entry does not fix or close this public-API defect. No complete dialogue, journal effect, save/reload or original-engine parity result follows from either failed run below.

## Bound native evidence

Both runs used Debug core DLL SHA256 `79650612926d96a8748320bcf3d0f8f265f7d20747448a30a5ec8918b472ebb9`, protected stock input and the same frozen external host source SHA256 `dfd15b336d5327f19c172ca47e944df425ebdb0a4e876d0617f164c9c8d83393`. Results remain under `C:/BGRedux/phase1-local/results/`; build directories remain under `C:/BGRedux/phase1-local/weapon-query-probes/`. The different host executable hashes bind separate external builds/debug paths, without an engine binary change.

| Evidence | First ordinary attempt | Fresh debugger diagnostic |
| --- | --- | --- |
| Run | `20261022T041456Z-jaheira-dialogue-c93397b8` | `20261022T041748Z-jaheira-dialogue-61cca34e` |
| Result SHA256 | `dba364780cf89e383dec5c2c97b875885a8f4c6c66266dfe398c66743b23f8a4` | `1ea29715939519dd64764ef5a23b962b78e2997b8064a7b599f3f2aa889a05f8` |
| Build directory | `candidate-9aa-ui1-jaheira2` | `candidate-9aa-ui1-jaheira-trace3` |
| Frozen build receipt SHA256 | `8b14dffd426e4c59139d3c349bc3291cc46a5c4443c91e0b698086437115f804` | `bf1876ac08e95eacf12dbf0b84a12ab6444fdd6f576bec21aa002f6c4de89105` |
| Host executable SHA256 | `4f8c1eb617b72bff7d770358695d2e1074d4d9a4152c105245d39d6e24f2efec` | `2b8dc1a3c3d7a7be02e327ab76ed9a03030b1c17572c6ff1c64afcf1c28beb46` |
| `talk/process.log` SHA256 | `e9662fb5d4c23028e11549f7600ac7035b04fc109cdeffb5d746c574dde6983a` | `4f3fcef77d4c92dceac1fed1fd22adcc8a93b6927c9cb392cff11e18c97bd78c` |
| Owned process | Native PID6568, exit3221226505 | GDB PID5028; traced native PID5188; debugger exit4294967295 |
| Bound / elapsed | 120 s /27.216 s; no timeout | 120 s /35.283 s; no timeout |
| Artifact manifest SHA256 | `19d3250ab9ea3808dbc89c3a1af2b7b5a85d95f5f217d5351f791f26550aaff5` | `4fbfa84c01404ac283675869bb4fe5ce34396ebcad4555a334bec1c2862dfc8b` |

The first result is failed. The second is explicitly a debugger diagnostic, not an acceptance run. Neither has `talk/capture/dialogue-result.json`. **Both do retain branch0-before artifacts**: screenshot, focused scene, full state and text receipt. An earlier partial directory inventory was not evidence that the branch timer had never run.

Independent read-only rehashes matched all278 first-run artifacts and277 debugger-run artifacts, including the frozen source and logs. Both receipts report protected Phase0 source/binaries/fixture, candidate source/binaries and immutable inputs preserved. Independently compared candidate and Phase0 before/after inventory file hashes match in each run. Both private-game guards preserve clean-game inventory, root hashes and immutable copied inputs, allowing only `GemRB.log` changes; linked asset bytes were not comprehensively rehashed. No worker tests, builds, native processes or engine/source changes were performed for this audit.

## What actually reached the failure

Both branch0 scenes show JAHEIRA, target10005, speaker/leader10002, TalkCount1, two party members, closed Cell01 flags1634 and no MISC4B. The observed first NPC strref899 occurrence increases0→1 over the pre-request transcript. The journal still contains only34089 and96383. The screenshot/text/state capture precedes the direct selection call. These facts establish that the initial dialogue and observation hook were reached; they do not establish successful response completion or the later34105 quest effect.

The debugger log's final Thread1 stack is decisive:

```text
frame2 std::vector<unsigned int>::operator[] (__n=4)
frame3 GemRB::TextArea::UpdateState (opt=4), TextArea.cpp:567
frame4 external dialogue_journey.cpp:207, ta->UpdateState(expected.local)
frames8–10 Timer::Update -> Interface::Main
```

The assertion is the non-const unsigned-vector bounds check. It identifies the direct host selection entry and the engine's post-selection `values[optIdx]` access. The stack does not retain inner callback frames after they have returned, nor directly print the replacement vector size. Source and the pinned DLG provide the reentrancy explanation below; the stack itself proves index4 is out of bounds at that outer access. This is not a font-provider, speaker-palette, original-engine or read-only text-scan attribution.

## Source explanation and supported entry points

`gemrb/core/GUI/TextArea.cpp:541–579` implements the public virtual UpdateState. Starting from direct UpdateState(4), it finds the option, saves the old option context, then calls SpanSelector::MakeSelection before reading `values[optIdx]` and dispatching Select. MakeSelection changes selected span/index and calls UpdateStateWithSelection, which enters UpdateState again. The inner selection sees the updated context, returns from its already-selected MakeSelection, and invokes the registered Select handler. `DialogHandler.cpp` registers that handler to call DialogChoose. The chosen JAHEIRA state0 transition4 goes to state47, which has a Continue transition rather than selectable response text. DialogChoose replaces options through SetSelectOptions, whose first operation is ClearSelectOptions; that operation clears `values`. When the original outer UpdateState resumes, its old index4 is invalid.

UpdateState is a public override in TextArea.h and its own source comment explicitly says it may be called from GUIScript. `Control::UpdateStateForVar` dispatches to it from `Window::RedrawControls`. It should safely select once even when the resulting callback changes or destroys the old options. This does **not** mean every Python control setter takes this path: `GemRB_Control_SetValue` calls SetValue, and the direct UpdateState call in Control_SetVarAssoc is slider-specific. No additional Python entry reproduction is claimed here.

The ordinary selection route is distinct. TextArea::SelectAvailableOption takes an **available/visible option index** and calls SpanSelector::MakeSelection directly. Normal numeric-key selection and OnMouseUp also enter MakeSelection. That sets the selected span/index before UpdateStateWithSelection enters UpdateState, eliminating the extra outer UpdateState frame responsible for the demonstrated stale-vector access. Console history uses the same public SelectAvailableOption API. This source analysis justifies trying that normal route first; it is not a native pass or a guarantee against every possible reentrant callback.

For the bounded Jaheira journey, visible index4 maps to state0 transition4 because all five responses are unconditional. Visible index1 maps to state9 transition14 because its first two transitions are both available under the guarded closed-door/no-key conditions. **Do not generalize visible index to DLG local/global transition identity.** The adapter must record the selection entry and visible index, retain actual displayed response/participant/fresh-text evidence and reject wrong branches. Mouse hit testing and OS pointer input remain unobserved.

## Open correction and validation work

The engine defect remains open even if the separate ordinary journey later succeeds. Expected supported behavior is one safe public selection/callback execution with coherent new options or dialogue end. A future correction needs focused native tests where direct UpdateState callbacks replace options, clear options and end the dialogue, plus normal mouse/key/public-selection and invalid-option behavior. Merely caching the old value before MakeSelection avoids one bounds access but can still dispatch a duplicate callback; that is insufficient as an unexamined fix. No engine correction, test result or full dialogue/save/reload success is claimed by this record.
