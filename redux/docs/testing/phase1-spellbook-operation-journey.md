# Stock spellbook operations: external journey

Coordinator checkpoint, October 22 UTC: the first 16 focused tests and external
build pass, but `20261022T084001Z-spellbook-operation-6cc4d25f` crashes before game
load. Fresh diagnostic `20261022T084520Z-spellbook-operation-5f0f9586` confirms
`Snapshot(game=null)` from the external initial-load callback; this is a host
defect, not evidence of an engine crash. The pregame-boundary correction adds
two negative methods; all 18 pass, and external `ordinary-2` builds. Its run
`20261022T085000Z-spellbook-operation-f06e9985` completes the native operation/save
phase (41 callbacks, 32 captures, owned exit zero), but the outer validator rejects
eight unbound control values: Python reports null and native reports the exact
INVALID_VALUE sentinel. Reload is not launched. All three result verdicts and
preservation guards remain retained. A narrow bridge-contract correction is
prepared separately; no full journey pass is claimed from these receipts.

The [original reference](phase1-original-spellbook-reference.md) records the
heading/count location, immediate wizard removal without a confirmation, and
serialized ready=0 after re-preparation. This evidence does not approve the
current native prompt policy as original parity.

The subsequent narrow bridge fix accepts Python null only for an unbound native
control with an empty variable and exact INVALID_VALUE integer; every bound
integer still requires exact identity. Together with the separate presentation
control, all 25 focused methods and 393 integrated external methods pass.
External `ordinary-control-3` compiles; fresh executions remain pending. A
separate read-only content review of the earlier completed operation phase
passes the corrected contracts, but skips freshness/build/reload validation and
does not rewrite its raw failed verdict. Review receipt:
`phase1-local/results/spellbook-bridge-content-review-20261022/review.json`.

This source-only adapter exercises Imoen's wizard book and Jaheira's priest book from the measured four-party Minsc checkpoint `20261022T075243Z-minsc-recruitment-072650e1/recruit/frozen-save`. No build, test, or runtime result is claimed by this implementation delivery. The coordinator owns execution. It adds no engine changes or fixture edits.

## Ordinary route and acceptance

Each caster is selected with the registered portrait callback, then the real OPTWIN spellbook callback. Observations bind selected identity, shown name/level, original known index, displayed tooltip, actual registered control, and raw spellbook content. Arrow results are compared with the same level reached by a real tab press. Actual tab BMP regions must distinguish tab 0 from tab 1 before their equality is accepted; icon presence alone cannot pass.

Imoen's zero-based level 1 target is SPWI213 (known index 2, memorized index 0); Jaheira's level 0 target is SPPR113 (known index 4, memorized index 0). For each: press the charged memorization, observe and cancel the stock confirmation, prove unchanged state, press and confirm removal, press the resref-bound known icon, prove the appended instance is **depleted** (flags 0), remove that depleted instance without confirmation, then re-add it depleted. The final delta is the original charged instance removed and the same resref appended depleted. Other memorized instances, duplicates, known order, and saved slot counts must be retained. There is no rest, cast, recharge, grant, direct spellbook mutation, or game-global setter.

The host runs the normal loop through observed natural startup, then pauses for callbacks. It saves through GUIOPT/GUISAVE, freezes the seven-file output, and loads it in a second owned process. The reload repeats navigation without memorization mutations. Independent GAME/CRE decoding checks saved known/memorized order and flags, page ownership/bounds, and exact declared spellbook delta. The established four-party checkpoint parser also binds identity, items/charges, XP, doors, and retained quests. Party and current-area caster spellbooks must agree before any permitted field normalization.

## Provenance and bounds

Build and run require the coherent full candidate engine build receipt, including its complete source, binary, and build-support inventories. The external compile receipt freezes the compiler/CMake hashes, Python dependency closure, GUIMG/GUIPR/Spellbook/portrait/load/save/control/provider sources, generated helper, and exact resource bytes. The GUI helper is copied with its unused main renamed, avoiding nested main macros. Runtime resource streams must match frozen provider paths and bytes; KEY, TLK, SPL/CHU archive providers, and source fallback 2DAs are bound. `spldisp` and `guibtact` follow the previously characterized explicit provider resolver, not a game-only assumption.

Each process gets a private GamePath wrapper, empty private override for stock runs, cache, profile, immutable input, fresh nonce, and owned bounded subprocess receipt. The normal phase is bounded to 240 seconds/720 timer samples; reload to 120 seconds/480 samples. No retry or fallback hides a failed callback. All logs, raw before/after callback snapshots, screenshots, UI dictionaries, startup samples, resource streams, and failed prefixes remain in a unique result folder. Phase0, candidate, source/resource closure, parent artifacts, input/save, and private wrapper guards run before/after/final.

The original 180-second process budget had only about three seconds of margin:
two completed native phases took 177.292/177.009 seconds. Run
`compressed-spellbook-20261022/20261022T090558Z-spellbook-operation-b75b1509`
completed all 69 Python plan steps but timed out during GUI saving at 181.298
seconds; owned process-tree cleanup completed and every preservation guard passes.
It remains failed. The new 240-second bound provides measured evidence-writing
margin; it changes no plan, state, callback, pixel or saved-byte assertion. Timer
sampling counts and requested intervals do not establish wall-clock performance.

## Coordinator commands

Use the integrated source tree and the current coherent engine build path; choose a new external output path every time. In PowerShell (the variables are explicit coordinator selections):

```powershell
$taskPython = 'C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe'
$taskSource = 'C:\BGRedux\phase1-local\engine'
$taskBuild = 'C:\BGRedux\phase1-local\builds\REPLACE_WITH_COHERENT_CANDIDATE'
$taskHost = 'C:\BGRedux\phase1-local\spellbook-probes\ordinary-1'
& $taskPython -B -m unittest discover -s "$taskSource\redux\tools\phase1\tests" -p test_spellbook_operation_journey.py
& $taskPython -B "$taskSource\redux\tools\phase1\spellbook_operation_journey.py" build --project-root C:\BGRedux --engine-source-root $taskSource --engine-build-root $taskBuild --output-dir $taskHost --timeout 240
& $taskPython -B "$taskSource\redux\tools\phase1\spellbook_operation_journey.py" run --project-root C:\BGRedux --engine-source-root $taskSource --engine-build-root $taskBuild --host-build "$taskHost\build.json" --results-root C:\BGRedux\phase1-local\results
```

Run only after the coordinator's other game process has terminated. Fresh source changes invalidate the external receipt and require a new build.

## Deliberate coverage limits and next control

These are actual registered callbacks, not OS pointer input. The coordinator subsequently observed original BG2EE 2.7.3.0 remove a charged prepared SPWI213 with one ordinary click and **no confirmation**. The current GemRB prompt path characterized here therefore differs from that original observation; this before-policy adapter does not approve the prompt as an EE contract. A future policy fix needs a separately explicit expectation, retaining classic-game behavior as appropriate. No original-game operation parity, whole-world equivalence, or RNG purity is inferred. The measured parent's known lists happen already alphabetically sorted at the observed levels: the ordinary baseline explicitly reports `nonidentity_sort_runtime=false` and `passed-with-runtime-sort-permutation-gap`. Synthetic negative tests exercise a nonidentity name permutation and reject visible-index substitution for original-index mapping; that is validator coverage, not runtime reproduction of issue #2494. Raw observations report any actual nonidentity ordering independently.

The coordinator authorized a **separate controlled presentation case**, explicitly enabled by `run --presentation-control spellname-permutation`: exchange only the little-endian SpellName strref at SPL bytes [8:12] between SPWI213/SPWI211 and SPPR113/SPPR111. Four private overrides retain every other byte, resref identity, icon, effect and casting data, using existing frozen English TLK entries without editing TLK. SPWI213 original index 2 and SPPR113 original index 4 must display at index 0, while the same actual callback and saved resref delta must still select the original identity. The implementation freezes original/override providers and exact field-only difference proofs, uses isolated runs, and requires actual runtime override stream provenance. It must never be labeled stock or original parity. The default ordinary run keeps an empty override and produces no control fixture. The opt-in run creates a separate `spellbook-operation-name-control` result; each process gets its own four files and a `presentation-control.json`. Both resref-bound known presses must select visible index zero while retaining original indices 2/4, and the same exact saved charged-to-depleted deltas are required. The four override files and the original build-frozen bytes are revalidated after/final, including TLK proof. Control results say `passed-private-presentation-control`; they are not stock results. A new external build is required because the helper/runner closure changed.

Focused test sources include wrong resref/index/charge, duplicate loss, forbidden world/XP/item/quest changes, inconsistent party/map surfaces, wrong caster/tooltip/level, vacuous tab equality, malformed BMP bounds, overlapping/orphan CRE spell tables, wrong parent hash, stale nonce, missing plan completion, and incorrect helper-main derivation.

Coordinator control command (after a fresh external build and all other runtimes terminal):

```powershell
& $taskPython -B "$taskSource\redux\tools\phase1\spellbook_operation_journey.py" run --project-root C:\BGRedux --engine-source-root $taskSource --engine-build-root $taskBuild --host-build "$taskHost\build.json" --results-root C:\BGRedux\phase1-local\results --presentation-control spellname-permutation
```

Original serialized append order is a separate observation: the coordinator decoded SPWI213 ready1/SPWI214 ready1/SPWI215 ready1 becoming SPWI214 ready1/SPWI215 ready1/SPWI213 ready0, while prepared icons remained visually sorted. This control validates the declared raw memorization delta and known-icon original-index mapping; it does not declare GemRB prepared-row display order equivalent to original.

## Known-spell wire/runtime representation correction

Preserved ordinary-3 result `20261022T085806Z-spellbook-operation-3c673787` failed its outer wire check after the actual host completed 41 callbacks/32 captures and saved successfully. The reader/writer source explains the representation: CREImporter::PutKnownSpells iterates known entries from last to first; ReadSpellbook traverses the serialized entries backwards before pushing runtime known entries. Therefore each serialized known page must equal the **exact reverse** of that page's actual runtime list, including innates. The validator now enforces this exact mapping, including resref/type/level; it does not sort or accept multiset equality. Memorized entries/order/flags remain exact in both representations. Serialized before/after known lists and slot fields still must remain unchanged. CREImporter.cpp remains in the frozen external source closure. The raw failed result stays failed and unchanged; the correction requires a fresh build/run.

## Explicit confirmation-policy BEFORE and AFTER

The CLI now declares `--confirmation-policy legacy-confirmation` (default historical BEFORE route) or `--confirmation-policy ee-direct` (AFTER route). Native and Python runtime receipts must both contain the exact requested policy, and the independent validator builds its plan from that explicit value. Neither mode detects behavior or falls back to another route. Existing raw receipts remain untouched; new source-closure receipts are required.

Legacy operate retains 69 plan steps including charged confirmation cancellation and confirm-removal. EE-direct operate has 57 steps: exactly one real charged prepared-button callback per caster must immediately remove the exact charged target, followed by the unchanged known-add/depleted-remove/known-readd operations. The raw before/after callback must already contain the correct removal; waiting for a later modal/confirmation cannot satisfy it. Every AFTER capture must have no confirmation modal. The precise registered prepared control/index is independently checked. Reload remains the same 41 navigation-only steps under either declared policy. Both paths retain exact spellbook wire conservation, reverse-known representation binding, resources, snapshots, private input guards, and save/fresh-process reload.

EE-direct runs add `-ee-direct` to their distinct result directory label and retain the requested policy in the outer observation/result as well as host/runtime receipts. To characterize the repaired candidate after a coherent engine and external rebuild, append `--confirmation-policy ee-direct` to the run command. Add `--presentation-control spellname-permutation` only for the separate controlled-name case; stock AFTER stays empty override.

This AFTER expectation is supported by original wizard physical-UI observation and both shipped menu callback sources. Eligible original priest operation remains unmeasured; this is not full priest runtime parity. Classic confirmation behavior and existing spontaneous restrictions remain separate production regression requirements. New focused source tests exercise actual policy selection for BG2EE/non-BG2EE and charged/depleted entries; external negatives reject implicit policy mismatches, omitted direct removal and wrong immediate deltas. No tests, builds or runtime were executed by the worker for this delivery.


## Executed BEFORE passes, October 22

The fresh stock run
`compressed-spellbook-20261022/20261022T091807Z-spellbook-operation-5f358ffc`
passes operation, ordinary GUI save and fresh-process reload. Its result SHA-256
is `73501918d980527b9382f9d684c213bbfa6d23ce6d4b2fdec4f4aa0e74fb5acc`.
Operate PID 13104 exited 0 in 187.058 seconds; reload PID 468 exited 0 in
111.648 seconds. Actual callbacks, arrow/tab pixels, exact spellbook wire delta
and all candidate/Phase0/input preservation guards pass. Stock known order is
already sorted, so its explicit verdict retains the runtime permutation gap.
The [independent stock audit](phase1-stock-spellbook-pass-audit.md) confirms
raw callback, pixel, saved-order/duplicate and provenance evidence.

The separate private name control
`compressed-spellbook-20261022/20261022T092348Z-spellbook-operation-name-control-eda150fa`
passes both processes with actual nonidentity ordering. Its result SHA-256 is
`3e845d639093b8cbd4dcc7e04dd4a7e8422e44b671714652b0e6014b9bcb0459`.
Operate PID 11696 exited 0 in 189.671 seconds; reload PID 5204 exited 0 in
110.993 seconds. Each target displays at index 0, retains original known index
2/4 and the correct saved resref delta. Four private name-only overrides and
unchanged TLK are bound; all preservation guards pass. This is controlled
presentation coverage, not a stock or original-parity result.

Both passes characterize the legacy confirmation policy and precede the new
heading/direct-removal production changes. Fresh AFTER execution must explicitly
select `--confirmation-policy ee-direct`; neither historical pass validates the
new production behavior. All earlier failed results remain unchanged.
