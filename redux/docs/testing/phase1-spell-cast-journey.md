# Imoen ordinary SPWI102 callback journey

Executed coordinator checkpoint: **276 integrated Python tests pass** in
`results/phase1-integrated-tests-20261022T0431.log`. Fresh external build
`candidate-9aa-ui1-spell-public3` and native run
`20261022T043347Z-spell-cast-journey-3dd76c87` pass both processes. Cast PID13524
exits zero in 71.239 seconds; reload PID11952 exits zero in 50.975 seconds.
Both complete 89 samples, including 80 running samples. The Cast button opens
at sample9, one spell icon press queues actual self action75 at sample10, and
required persistent effects plus released/idle state appear by sample31.
The ready spell changes 1 to 0. Fresh reload makes no new cast, preserves the
effects/depletion, and creates a second GUI save. Save-state checks and all
preservation guards pass. GUI save return codes remain explicitly unobserved.

Initial `spell1` build remains failed because its game-only resource probe
could not find the actual GemRB SPLDISP provider. `spell-provider2` remains failed
at link time on unexported GetWindow. The corrected external adapter binds actual
runtime table paths/bytes and uses exported GetViews with exact window IDs;
engine source and binaries remain unchanged.

This external adapter uses the protected two-character AR0602 fixture without changing it. It observes candidate behavior only. Original spell behavior, OS pointer hit testing, whole-world equivalence, deterministic RNG behavior, and numeric armor-class parity remain unmeasured.

`spell_cast_journey.py` builds a separate host from byte-exact copies of the established Phase0 GUI host and serializer. Its new external header runs in the normal 250 ms host clock; engine source, DLLs, shared helpers, and other journey files are unchanged. The separate `gui/SpellStart.py` preserves the established fixture-loading startup, copied under the expected `ReduxStart` module name for this run.

The cast process requires Imoen in party position 2, the actual `portrait=2` control, and its shipped portrait callback selecting only Imoen. Four consecutive running observations must show the stock area startup completed (`BD_DEFAI=1`, leader's actual class script `BDDEFAI`), Imoen idle with no current/next action or movement, and sole Imoen selection. It presses the actual action-row `ACT_CAST=2` control once. On the next sample it resolves the enabled icon's existing `Spell` binding through the actor's actual spell-info cache, requires SPWI102, mage book/level 0 and self target 5, and presses it exactly once. A lost boundary fails; no retries, spell grants, forced spell applications, AI disabling, stat/global writes, or teleports are used.

Native `PerformAction` calls the real callback but does not refresh the control's bound GUI dictionary. The adapter rebinds the identical existing variable/value/range before dispatch, copying the variable first to avoid self-aliasing. This is declared GUI selection plumbing; it never writes game globals or manufactures successful gameplay outcomes.

Acceptance requires the actual queued SPWI102 action to resolve to Imoen, observed casting with Imoen as the last spell target, subsequent idle/released queue, exactly one ready SPWI102 changing from flags 1 to 0, and unchanged other memorized spells, known spell lists, slot capacity, and equipment. Consumption alone cannot pass: `HandleCastingStance` consumes before later casting checks. New SPWI102-sourced effects must include opcode 0 `(6,16)` and opcode 142 icon 12, with positive bounded remaining duration; the cast process additionally binds their actual caster to Imoen. The reload process does not require serialized caster IDs: EFF V2 does not serialize the native runtime caster ID. Every raw field remains captured.

Opcode 0 parameter 2 value 16 selects the natural-AC-cap/deflection branch in `FXOpcodes.cpp`; the harness records all base/modified stats and does not assume the resulting AC must numerically equal 6. A casting animation or depleted charge is insufficient.

Both processes end through the shipped options Save button, new-row selector, name-edit ValueChange, and `GUISAVE.ConfirmedSaveGame` callbacks. This path does not expose the return value of `GemRB.SaveGame` to the adapter: `save_return_code_observed=false` is explicit, and success instead requires exactly one newly named save, a complete five-file manifest, and matching wire depletion/persistent effects. GUI state differences are retained; Imoen gameplay state and game time must be unchanged by the paused save operation. The second fresh process loads only the first immutable output, presses the portrait but never Cast/spell, observes depletion/effects, and creates a second ordinary GUI save.

Each process has exactly 80 running samples plus 5 initial and 4 final paused samples, with at most 90 seconds per process. Every run uses a unique private result directory and private GamePath wrapper, profile, cache and empty override. Source/helper/compiler/binary/header/generated-source receipts, protected Phase0 and candidate inventories, exact startup scripts, SPWI102, ACTION.IDS, SPLDISP and GUIBTACT bytes are pinned before/after/final. Missing or stale evidence, drift, timeout, callback exceptions and incomplete effects stay failed with their raw prefix preserved. Linked asset-wrapper scope follows the existing private-game helper and does not imply independently hashing every linked asset on each sample.

Snapshots include all serialized gameplay surfaces, per-sample Imoen stats/effects/spellbook/inventory, current/next actions and direct target fields, clock target trace, actual button bindings, and screenshots at portrait/callback/release/save boundaries. Screenshots are instantaneous render-buffer observations; GUI save callbacks run synchronously at the paused clock end, so a screenshot immediately following a callback need not contain a newly rendered frame. Callback identity and outcome rely on control/state/wire evidence, not an assumed pixel transition.

Coordinator commands after integrating and reviewing the source (substitute the current matching candidate build and a fresh external host output directory):

```powershell
$py = 'C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe'
$tool = 'C:\BGRedux\phase1-local\engine\redux\tools\phase1\spell_cast_journey.py'
$source = 'C:\BGRedux\phase1-local\engine'
$build = 'C:\BGRedux\phase1-local\builds\20261022T012223Z-candidate-9aa69cd5'
$host = 'C:\BGRedux\phase1-local\weapon-query-probes\candidate-9aa-ui1-spell1'
& $py -B -m unittest discover -s C:\BGRedux\phase1-local\engine\redux\tools\phase1\tests -p test_spell_cast_journey.py
& $py -B $tool build --project-root C:\BGRedux --engine-source-root $source --engine-build-root $build --output-dir $host --timeout 180
& $py -B $tool run --project-root C:\BGRedux --engine-source-root $source --engine-build-root $build --host-build "$host\build.json" --fixture C:\BGRedux\phase0-local\fixtures\original-bg2ee-20261020\GemRB --results-root C:\BGRedux\phase1-local\results --running-samples 80 --timeout 90
```

The first coordinator build attempt failed before compilation because the Phase0 resource probe covers game providers only. This is preserved as a failed attempt. The spell adapter now has a deliberately bounded BG2EE table contract: `Interface.cpp` registers GemRB overrides before game providers, then `unhardcoded/bg2ee` before `unhardcoded/shared`; `ResourceManager.cpp` searches in that insertion order. The stock files here are `gemrb/unhardcoded/shared/spldisp.2da` and `gemrb/unhardcoded/bg2ee/guibtact.2da`. They are explicit build-source pins and frozen resource bytes, with selected path and checked present/absent candidates in the receipt. The adapter rejects unexpected game-probe or GemRB-override shadows, requires a valid table, and never skips a missing resource. Cache and ModPath remain private and initially empty; no table is installed or edited.

The Phase0 game probe does not reproduce every profile/loose/language provider. Therefore this preflight is not presented as a general resolver: each fresh native process independently obtains both actual resource streams through `gamedata->GetResourceStream`, freezes their exact bytes without a newline transformation, and records each stream's original file path. Acceptance requires those runtime paths and bytes to equal the pinned selected source files, and requires fresh evidence. Profile or other unmodeled higher-priority shadows consequently fail even if their bytes happen to be identical. Source/resource checks repeat before/after/final and detect changed selected contents, new higher-priority candidates, or changed absence/provenance proof. The closure also pins `InterfaceConfig.cpp`, `ResourceManager.cpp` and `DirectoryImporter.cpp`. A fresh external host build is required after this correction; old failed or pre-correction receipts cannot satisfy the changed source closure.

No test, compiler, or runtime execution was performed by the implementing worker. All native semantics are proposed acceptance checks until the coordinator obtains actual receipts. Negative test sources cover wrong/missing self-target actions, depletion without effects, missing casting/release, early/duplicate callback, readiness/multiselection/movement, disabled/wrong icon, forced save claims, stale/missing/invalid images, save mutation, reload recast, clock failure, spell grants/other depletion/inventory/slot changes, source/caster/parameter/expiry/timing errors, duplicate effects/pages, wire range overlap/truncation, frozen-source tamper, host anchor drift, and launch budget rejection.
