# Active main-hand, ammunition and launcher replacement journey

Status: **both new native scenarios passed; the raw 14 stages and 196 calls were independently audited read-only**. See the execution addendum below and the public [evidence summary](../compatibility/evidence/phase1-active-slot-lab.json). Engine code, game resources and the old offhand journey/validator are unchanged by this adapter. This is a separate host, CLI and versioned receipt, not an expansion of the meaning of old results.

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

The candidate/build roots are explicit and preserved separately from accepted Phase0. Timeout is finite and bounded to600 seconds per compilation/process; repeats are1–8. Unit-test sources exercise stale/legacy/incomplete coverage, wrong or ambiguous TransformItem dispatch, forged resource metadata, stale launcher THAC0 despite unchanged max enchantment, wrong range/proficiency/header, raw ITM hashes/bounds and zero-proficiency conversion. These tests were not executed by the independent audit worker; subsequent coordinator execution is recorded below.

## Native execution and independent audit, 2026-10-22 UTC

The external host built successfully in `20261022T033147Z-active-slot-build-41d00737`. Serial native run `20261022T033723Z-active-slot-run-81396091` passed both scenarios on the Debug candidate core with SHA256 `79650612926d96a8748320bcf3d0f8f265f7d20747448a30a5ec8918b472ebb9`. The frozen run receipt hashes to `71244e9fc3343e9ad40604d8b26d980b343afd3db643a3391702dbfbf3963753`; the host executable hashes to `3b08aa82fb5c6030bebb604c520ba69c2b41cd2fcf99f181ac413f0a0be8a38b`. The public JSON binds the build receipt, manifests, compiler, CMake cache, preparation and frozen native/Python source identities. The coordinator reports 10 focused tests and the full 237-test suite passing. This independent audit launched no tests, build or native processes.

| Scenario | Owned PID | Stages | Calls | Elapsed | Process disposition |
| --- | ---: | ---: | ---: | ---: | --- |
| Main, nonce `2f8ae11af927495a8b2d462e0d5b690e` | 13532 | 5 | 70 | 9.175 s | Exit 0, no timeout; 120 s bound |
| Ranged, nonce `a107b10547c140c99e597b0a9e472ee4` | 14184 | 9 | 126 | 11.417 s | Exit 0, no timeout; 120 s bound |

Independent JSON ingestion and SHA256 comparisons confirmed 196 calls: 168 predicates and 28 True/False controls. All **588 state/cache/calling-thread RNG before/after pairs** are byte-equal, with uninterrupted initialized-to-call-to-final and inter-stage continuity. The 14 query directories contain exactly 1,274 query-capture files. Repeated predicate values are stable, controls return 1/0, sender/target are 10002/10003, and the collected diagnostic target state remains unchanged. All initialized selected item/header metadata matches the six retained resource records and the frozen preparation-bound raw metadata. Main selection remains physical slot35/header0 with SW1H01 in offhand slot9; ranged selection remains slot11/header0, 40 arrows, launcher slot35 and empty offhand. Cache range, item type, proficiency, selected-header range/THAC0 and launcher bonuses match the corresponding loaded resources.

The actual route receipts cover two initial no-ops, six explicit-slot CreateItem mutations, three ordinary remove/add/select mutations and three parsed TransformItem mutations. Each TransformItem receipt records action356, no object parameters, flags0, charges `[0,0,0]`, exactly one old-resource match at physical slot35, and sender10002 as the first resolved ST_ANY target among 37 enumerated targets. These observations bind actual dispatch without treating enumeration count as a singleton-target contract.

The decisive reverse launcher evidence is ranged `03-ordinary-ammo-plus` → `04-transform-launcher-normal`: BOW02/AROW02 becomes BOW01/AROW02, launcher THAC0 bonus **2 → 1**, launcher damage bonus remains1, selected arrow header THAC0 remains1, range remains101, proficiency remains104, and maximum combat enchantment remains1. The separate ordinary launcher replacement at stage07 also restores THAC0 bonus2 → 1, this time with AROW01 selected. These are direct cache observations after the mutation routes; no observer repair was invoked.

**Query RNG preservation does not imply whole-journey RNG preservation.** Independent mutation-boundary hashes confirm calling-thread RNG changes during main `02-ordinary-main-plus`, ranged `03-ordinary-ammo-plus` and ranged `07-ordinary-launcher-normal`. The other mutation boundaries preserve that RNG snapshot. Every query's before/after RNG pair remains identical. These intentional mutation changes are retained as evidence; this audit does not attribute them to a particular internal operation or apply query-noninterference requirements to the deliberate mutations.

Independent rehashes matched all 1,683 run artifacts and 25 build artifacts; 3,507 current candidate source files and 48 candidate build files; 3,500 protected Phase0 source files, 50 protected build files and six protected fixture files; all 18 live/frozen helper entries in each build/run receipt; 24 final-fixture source/copy file checks; four source/copied script checks; and driver/compiler/CMake pins. Candidate and Phase0 before/after inventories are identical. Both private-game guards preserve clean-game inventory, root hashes and immutable private inputs, allowing only `GemRB.log` changes. Linked asset content was not comprehensively rehashed.

This accepts the bounded native active-slot mutation/query observations. It leaves **original mutation parity and magic-slot coverage unobserved**, retains the old offhand and original 22-case results under their existing meanings, and establishes no complete AI, normal-loop combat, hidden-state or uninstrumented resource-lifetime guarantee. The retained-resource observer changes resource lifetime by design. All historical and failed evidence remains intact.
