# Active main-hand, ammunition and launcher replacement journey

Status: **new external source and focused negative test sources prepared; no worker test, build or native execution**. Engine code, game resources and the old offhand journey/validator are unchanged. This is a separate host, CLI and versioned receipt, not an expansion of the meaning of old results.

`weapon_slot_journey.py` and `native/weapon_slot_journey.cpp` exercise initialized Actor/Inventory operations with the exact existing 22-case preparation (SHA256 `b18bb391c451fb9ace9bdab3a43313c554f82cddf170af0751d95dd06ece1ce4`). Main-hand coverage starts from `02-plus-normal-pfmw`; ranged coverage starts from `ammo-plus-pfmw`. The two scenarios use distinct fresh input copies, private game wrappers, profiles, caches and serial owned processes. Magic-slot coverage is explicitly deferred: no supported ordinary magic-weapon fixture/route is established by these inputs.

## Actual mutation boundaries

| Scenario | Ordered states after completed mutation routes |
| --- | --- |
| Main, physical slot35, header0, offhand SW1H01 | Initial SW1H02 → explicit-slot CreateItem SW1H01 → ordinary remove/add/select SW1H02 → parsed TransformItem SW1H01 → explicit-slot CreateItem SW1H02 |
| Ranged, selected ammo slot11/header0, launcher slot35, empty offhand | Initial BOW01/AROW02 → CreateItem AROW01 → TransformItem BOW02 → ordinary remove/add/select AROW02 → TransformItem BOW01 → CreateItem AROW01 → CreateItem BOW02 → ordinary remove/add/select BOW01 → CreateItem AROW02 |

All ammunition routes preserve the prepared count40 explicitly. The explicit-slot CreateItem route calls SetSlotItemRes, EquipItem and ReinitQuickSlots, matching the existing API sequence. The ordinary route calls UnEquipItem, RemoveItem, CreateItemCore, AddSlotItem, EquipItem and ReinitQuickSlots. Any recache inside these real mutation methods is production behavior; the observer never invokes CacheAllWeaponInfo, CacheWeaponInfo, GetUsedWeapon or a repair query.

TransformItem is generated from the shipped action definition and dispatched through the actual engine handler. Before dispatch, the host records action356, exact old/new resources, absent object arguments, flags, default charge arguments, actual enumerated target count and first ST_ANY sender identity. It additionally requires exactly one matching old item at physical slot35. This avoids silently transforming a duplicate offhand or backpack item. It neither substitutes TransformItemCore nor invents a singleton target requirement.

The default two repetitions produce a planned 14 stage boundaries and 196 calls (168 predicates plus 28 True/False controls). These are intended counts, not executed results. Deliberate state/cache/RNG changes are captured before/after the mutation separately from each query's before/after snapshots. Diagnostic target state must remain identical throughout. Per-query ingestion uses the existing strict six-query validator unchanged, including parser/target identity, complete file inventory, continuity, native equality versus independent diffs, positive/negative controls, repeated values, exact physical item/slot/header selection and optional calling-thread RNG evidence. `--require-rng-observed` makes that observation mandatory on the candidate.

## Additional launcher/cache proof

Cached item/header pointers are matched against retained references to all six stock item resources before any observer dereference or query. Unknown pointers produce address-only failure evidence and stop observation. References survive mutation and actor destruction. This retention changes diagnostic resource lifetime; it does not establish absence of lifetime bugs in an uninstrumented game.

The new cache surface adds launcher damage/THAC0 bonuses, range, item type and proficiency. Independent raw ITM reads must match the preparation's six resource SHA256 values. They bind selected header0 fields and loaded resource metadata before derived cache assertions. The bounded reader models the inspected ITMImporter conversions: dagger/shortsword finesse-bit conversion and zero-proficiency lookup through the candidate BG2EE `proftype.2da` row index, converted to ieByte. That source table is bound by the before/after candidate source inventory. This reader is not a general resource-provider precedence implementation; a loaded/raw metadata mismatch remains a failure.

Read-only resource inspection confirms SW1H01/SW1H02 enchantment0/1, proficiency89 and range1; BOW01/BOW02 enchantment0/1, proficiency104 and range100; AROW01/AROW02 enchantment0/1, raw proficiency0 and range100. Arrow proficiency becomes255 through BG2EE proftype row5=-1. **Both stock bows have damage bonus1; their THAC0 bonuses are1 and2.** Consequently the reverse launcher transform with AROW02 still selected must restore launcher THAC0 bonus1 even while maximum combat enchantment remains1. Checking enchantment or resource names alone would miss this stale cache. Exact cached resource flags, selected header contents, derived range/proficiency and both launcher bonuses are checked; cleared offhand fields have no asserted semantic range/launcher meaning.

The read-only mapping below is for the preparation-bound stock ITM header0, not a claim about every ability or provider. `Range` is the raw header value; the candidate cache stores range plus one. Recharge flags are raw for these six item types. The numeric raw reader verifies hashes before decoding and records the same values on a future accepted run.

| Item | Item type | Raw proficiency | Enchantment | Range | Damage bonus | THAC0 bonus | Recharge flags |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SW1H01 | 20 | 89 | 0 | 1 | 0 | 0 | 3 |
| SW1H02 | 20 | 89 | 1 | 1 | 1 | 1 | 1 |
| BOW01 | 15 | 104 | 0 | 100 | 1 | 1 | 0 |
| BOW02 | 15 | 104 | 1 | 100 | 1 | 2 | 0 |
| AROW01 | 5 | 0 | 0 | 100 | 0 | 0 | 0 |
| AROW02 | 5 | 0 | 1 | 100 | 0 | 1 | 0 |

Source review anchors: `gemrb/plugins/GUIScript/GUIScript.cpp`, `GemRB_CreateItem` explicit-slot path; `gemrb/core/Inventory.cpp`, `EquipItem`, `SetSlotItemRes` and `CacheWeaponInfo`; `gemrb/core/GameScript/Actions.cpp`, `GameScript::TransformItem`; `gemrb/core/GameScript/Matching.cpp`, implicit-object resolution; `gemrb/plugins/ITMImporter/ITMImporter.cpp`, `Initializer`, `GetProficiency` and extended-header import; and `gemrb/unhardcoded/bg2ee/proftype.2da`. The importer uses table row indices, including descriptive row labels such as `15_BOW`; the bounded reader validates their numeric prefixes and row order. This audit establishes source-grounded expected values, while successful ordinary-route selection/cache behavior remains a native validation requirement.

## Provenance, interpretation and invocation

Build/run freeze the new driver/adapter, existing six-query/serializer/helper sources, and all imported Phase0 helper source files. The serializer must still match the protected Phase0 original. Compiler, CMake cache, source/binary inventories, driver/build receipt, preparation, final fixture manifests and case scripts are checked. Copied launch inputs, scripts, driver/helpers and config are pinned through teardown even on a failed native process. Private root copies and receipts are retained; shared asset links are excluded from bulk artifact traversal. Wrapper inventory/root guards and explicit resource hashes remain distinct from a claim that every linked asset byte was rehashed. Any source/build/fixture/private-root drift, malformed/partial/stale capture, cache mismatch, query mutation or unstable value fails. Failed receipts and raw captures remain in fresh unique directories; canonical and historical outputs are not overwritten.

No original mutation journey is claimed. Similar final weapon names are insufficient to bind an original case when item quantities, flags, effects or action history may differ. The starting fixtures retain their original preparation identities; subsequent snapshots are native mutation observations. The original 22-case query comparison remains separate, and no supplied original result is silently transferred onto a mutated state.

Coordinator commands, after integration and outside an active native guard:

```powershell
$slotTool = 'C:/BGRedux/phase1-local/engine/redux/tools/phase1/weapon_slot_journey.py'
$slotPrefix = 'C:/BGRedux/phase0-local/toolchain/msys64/ucrt64'
$slotArgs = @('--project-root','C:/BGRedux','--engine-source-root','C:/BGRedux/phase1-local/engine','--engine-build-root','C:/BGRedux/phase1-local/builds/20261022T012223Z-candidate-9aa69cd5','--results-root','C:/BGRedux/phase1-local/results','--timeout','240')
& "$slotPrefix/bin/python.exe" -B $slotTool build @slotArgs
& "$slotPrefix/bin/python.exe" -B $slotTool run @slotArgs --build-receipt '<new-build-directory>/build.json' --preparation C:/BGRedux/phase1-local/results/20261021T235241Z-weapon-oracle-ccf85085/preparation.json --scenarios main ranged --repeats 2 --require-rng-observed
```

The candidate/build roots are explicit and preserved separately from accepted Phase0. Timeout is finite and bounded to600 seconds per compilation/process; repeats are1–8. Unit-test sources exercise stale/legacy/incomplete coverage, wrong or ambiguous TransformItem dispatch, forged resource metadata, stale launcher THAC0 despite unchanged max enchantment, wrong range/proficiency/header, raw ITM hashes/bounds and zero-proficiency conversion. These tests are **unexecuted by this worker**. Compilation, first actual stage captures and full preservation validation remain coordinator work before any coverage result is accepted.
