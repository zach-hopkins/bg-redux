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

This source-only adapter exercises Imoen's wizard book and Jaheira's priest book from the measured four-party Minsc checkpoint `20261022T075243Z-minsc-recruitment-072650e1/recruit/frozen-save`. No build, test, or runtime result is claimed by this implementation delivery. The coordinator owns execution. It adds no engine changes or fixture edits.

## Ordinary route and acceptance

Each caster is selected with the registered portrait callback, then the real OPTWIN spellbook callback. Observations bind selected identity, shown name/level, original known index, displayed tooltip, actual registered control, and raw spellbook content. Arrow results are compared with the same level reached by a real tab press. Actual tab BMP regions must distinguish tab 0 from tab 1 before their equality is accepted; icon presence alone cannot pass.

Imoen's zero-based level 1 target is SPWI213 (known index 2, memorized index 0); Jaheira's level 0 target is SPPR113 (known index 4, memorized index 0). For each: press the charged memorization, observe and cancel the stock confirmation, prove unchanged state, press and confirm removal, press the resref-bound known icon, prove the appended instance is **depleted** (flags 0), remove that depleted instance without confirmation, then re-add it depleted. The final delta is the original charged instance removed and the same resref appended depleted. Other memorized instances, duplicates, known order, and saved slot counts must be retained. There is no rest, cast, recharge, grant, direct spellbook mutation, or game-global setter.

The host runs the normal loop through observed natural startup, then pauses for callbacks. It saves through GUIOPT/GUISAVE, freezes the seven-file output, and loads it in a second owned process. The reload repeats navigation without memorization mutations. Independent GAME/CRE decoding checks saved known/memorized order and flags, page ownership/bounds, and exact declared spellbook delta. The established four-party checkpoint parser also binds identity, items/charges, XP, doors, and retained quests. Party and current-area caster spellbooks must agree before any permitted field normalization.

## Provenance and bounds

Build and run require the coherent full candidate engine build receipt, including its complete source, binary, and build-support inventories. The external compile receipt freezes the compiler/CMake hashes, Python dependency closure, GUIMG/GUIPR/Spellbook/portrait/load/save/control/provider sources, generated helper, and exact resource bytes. The GUI helper is copied with its unused main renamed, avoiding nested main macros. Runtime resource streams must match frozen provider paths and bytes; KEY, TLK, SPL/CHU archive providers, and source fallback 2DAs are bound. `spldisp` and `guibtact` follow the previously characterized explicit provider resolver, not a game-only assumption.

Each process gets a private GamePath wrapper, empty private override, cache, profile, immutable input, fresh nonce, and owned bounded subprocess receipt. The normal phase is bounded to 180 seconds/720 timer samples; reload to 120 seconds/480 samples. No retry or fallback hides a failed callback. All logs, raw before/after callback snapshots, screenshots, UI dictionaries, startup samples, resource streams, and failed prefixes remain in a unique result folder. Phase0, candidate, source/resource closure, parent artifacts, input/save, and private wrapper guards run before/after/final.

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

The coordinator authorized a **separate future controlled presentation case**, not yet implemented here: exchange only the little-endian SpellName strref at SPL bytes [8:12] between SPWI213/SPWI211 and SPPR113/SPPR111. Four private overrides would retain every other byte, resref identity, icon, effect and casting data, using existing frozen English TLK entries without editing TLK. SPWI213 original index 2 and SPPR113 original index 4 would display at index 0, while the same actual callback and saved resref delta must still select the original identity. It must freeze original/override providers and exact four-byte-field difference proofs, use isolated runs, and require actual runtime override stream provenance. It must never be labeled stock or original parity. No override or control fixture is generated by the present ordinary CLI.

Focused test sources include wrong resref/index/charge, duplicate loss, forbidden world/XP/item/quest changes, inconsistent party/map surfaces, wrong caster/tooltip/level, vacuous tab equality, malformed BMP bounds, overlapping/orphan CRE spell tables, wrong parent hash, stale nonce, missing plan completion, and incorrect helper-main derivation.
