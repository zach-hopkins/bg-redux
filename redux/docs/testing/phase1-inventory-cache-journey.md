# Inventory-cache mutation journey and independent capture review

This is external diagnostic tooling. No engine cache fix is included and no
native journey has been compiled or launched by the implementing worker.
The coordinator must reproduce any cache defect before changing Inventory.

The first coordinator baseline run now supplies a bounded reproduction:
`20261022T005119Z-inventory-journey-a4f2c27f` completed00–06 and then failed
an external action-target guard at07. At05-create-plus, physical slot9 contains
SW1H02 but the actual off-hand cache still names SW1H01 with enchantment0.
Ordinary remove/restore/shield changes and06-reset-normal remain coherent.
All98 completed calls (84 predicates and14 controls) preserve collected
state/cache across query evaluation. The baseline predicates remain stubs;
these zeros do not establish candidate query behavior.

An independent prefix review rehashed597 artifacts and checked both
preservation inventory pairs, retaining the original exit1/completedfalse:
`C:/BGRedux/phase1-local/results/20261022T005545Z-inventory-prefix-review-f7dc6d31/review.json`.
This is a seven-stage observation, not successful ten-stage acceptance.

## TransformItem guard correction

The shipped definition is `356 TransformItem(S:OldItem*,S:NewItem*)`, with no
object argument. The parser leaves object parameters absent. Matching.cpp's
GetAllObjects returns all actors, sender first, for this no-object action;
the TransformItem handler's GetScriptableFromObject chooses the first ST_ANY
target. Requiring a singleton actor list was an external-harness error.

The corrected guard retains the actual parsed action and engine handler.
It requires action356, exact old/new resources, no objects or ANYONE flag,
one or more returned actors and the sender as first ST_ANY target. It records
the parsed fields, flags, count and resolved runtime ID in transform-action.json
before dispatch. It does not invent an object, change the action ID or call
TransformItemCore directly. Wrong action/resource/target/selector evidence
fails Python ingestion as well. A separate review_completed_prefix helper
supports forensic inspection without weakening normal full-journey acceptance.

The coordinator's first baseline-host compile failed at three resource-API
calls because ResRef has an explicit constructor. The external source now
constructs ResRef explicitly for GetItem, CreateItemCore and SetSlotItemRes.
The failed build log remains at
`C:/BGRedux/phase1-local/weapon-query-probes/baseline-cache-20261022/build.log`.
This is a compile failure, not a cache or query observation. The worker reran
the43 Python ingestion tests; compilation and native execution remain the
coordinator's next checks.

## Independent original evidence review

Re-ingested the exact preparation, case/script/nonce/executable/input bindings,
frozen wire output and capture artifact manifests for these actual receipts:

| Original case | Frozen capture suffix | Six values E1,D1,E2,D2,E3,D3 |
|---|---|---|
| 22 missile/slashing100 | a929b033 | 1,1,0,0,1,1 |
| 4 slash/crush against slashing100 | a763a55b | 1,0,1,1,1,1 |
| 3 crush/slash against slashing100 | d5ad9ed1 | 1,1,1,0,1,1 |

Each independently rehashed five frozen save files and15 capture artifacts.
Cases3/4 support ANY-hand CanDamage for asymmetric mixed physical resistance.
They do not alone establish every BOTH/EffectiveVs combination.

The strict coordinator capture source hash
`bd7e168cdcbb144fa24cddb419159dc3ab7841b5dd78d9c7bb563de8669d410b`
matches the frozen source in adversarial batch
`20261022T000649Z-capture-adversarial-87e47547`. The eight challenges were
independently replayed against the same source, with the clock fixed to its
recorded batch instant and the positive wire read redirected to frozen actual
case3 rather than the changing live autosave. Positive validation succeeded;
all eight rejected for the exact recorded reasons: wrong nonce, wrong case,
wrong executable window, stale timestamp, image drift, wrong loaded fixture,
Boolean case index and missing operator attestation. This was a read-only
forensic replay, not another original game run. No material blocker was found
in those three captures or that bounded negative batch.

## Source-grounded cache risk

`Inventory::CacheAllWeaponInfo` clears off-hand item/header pointers and mode
when `Actor::IsDualWielding` is false. Ordinary GUI drag/removal goes through
`UnEquipItem` then `RemoveItem`/`KillSlot`. For SLOT_EFFECT_LEFT, KillSlot
clears the slot, resets shield animation and calls CacheAllWeaponInfo.
`AddSlotItem` then equips the new item. That path appears to refresh correctly.

In contrast, `SetSlotItemRes` calls `SetSlotItem`, which replaces the CRE item
and updates weight/action UI but does not refresh weapon caches. The explicit
slot `GemRB_CreateItem` path follows it with `EquipItem` and ReinitQuickSlots.
For the left slot, EquipItem calls CacheAllWeaponInfo **only when**
`UpdateShieldAnimation` reports a change. The source `TransformItemCore` path
performs the replacement without an equip call.

Read-only inspection of the actual stock items confirms SW1H01/SW1H02 both
use animation `S0`, with enchantment0/1 respectively. Their hashes are
`c78bbec33abcd8d37225801edf59cbfae88699e217a8c567dbeef534f094ce8c`
and `6b7a2f8288b9921f9a0ce3913ee211d3329fc9cc89ae7f19b1bef8f6391a4d66`.
Thus a same-animation in-place replacement is a concrete suspected stale-cache
path. This is source evidence, not a reproduced runtime defect yet.

## Actual API journey

`native/weapon_inventory_journey.cpp` uses prepared case02: main SW1H02,
off SW1H01, diagnostic magical-weapon protection on Player2. It executes:

1. Observe initial state.
2. Ordinary UnEquipItem+RemoveItem to empty off-hand.
3. Ordinary CreateItemCore+AddSlotItem restore of SW1H01.
4. Ordinary remove/add SHLD01.
5. Explicit-slot CreateItem call sequence to SW1H01 (C0→S0 animation control).
6. Same call sequence SW1H01→SW1H02 (same animation).
7. Ordinary remove/add restore of SW1H01.
8. Actual parsed GameScript::TransformItem dispatch SW1H01→SW1H02.
9. Ordinary remove/add restore of SW1H02.
10. Explicit-slot CreateItem call sequence SW1H02→SW1H01 (reverse control).

The CreateItem sequence is the existing API's SetSlotItemRes, EquipItem,
ReinitQuickSlots sequence, rather than a replacement cache implementation.
TransformItem uses actual action356 from packaged ACTION.IDS, verifies its
resolved sender target, then calls the exported engine handler. That handler
executes TransformItemCore. The initial +1 main hand makes old SW1H01 unique
to the off-hand at that transform step.

Before and after each intentional mutation, capture full inventory/state and
actual weapon-cache metadata. Afterward, run True/False plus all six actual
queries, with per-call state/cache before/after snapshots. Repeats default2,
bounded1–8. Deliberate mutation deltas and query-caused deltas are separate.
The observer never calls CacheAllWeaponInfo or repairs the cache itself.

To avoid dereferencing a cache pointer after replacement frees its former
owner, the observer retains GetItem references to all three Item resources
until the journey ends. Before every cache dereference/query it confirms the
cached Item pointer and header pointer belong to these retained resources.
Unknown pointers produce raw address-only evidence and abort query execution;
partial results remain. Retention changes resource lifetime for the test and
does not prove absence of memory-lifetime defects in an uninstrumented run.

## Coordinator build and run

`weapon_inventory_journey.py` has separate `build`/`run` modes and creates a
distinct host. Existing six-query observer sources/receipts are unchanged.
Use explicit source/build roots for the intended baseline or candidate:

```powershell
& $python -B $tools/weapon_inventory_journey.py build `
  --project-root C:/BGRedux --engine-source-root $sourceRoot `
  --engine-build-root $buildRoot --output-dir $freshJourneyHost

& $python -B $tools/weapon_inventory_journey.py run `
  --project-root C:/BGRedux --engine-source-root $sourceRoot `
  --engine-build-root $buildRoot --build-receipt $freshJourneyHost/build.json `
  --preparation C:/BGRedux/phase1-local/results/20261021T235241Z-weapon-oracle-ccf85085/preparation.json `
  --results-root C:/BGRedux/phase1-local/results --repeats 2
```

The input preparation must include case02 and SHLD01 metadata (the current
22-case preparation does). Build and run pin Phase0 inventories, candidate
source/binaries, external source/binary/receipt and all clean game files,
with bounded owned process handling. Deliberate mutations affect loaded
process memory, while the copied input fixture remains hash-immutable.

Python independently checks exact physical main/off-hand results after each
API call, target identity/state, step and query continuity, complete raw
evidence and native equality against independent diffs. It records cache
mismatches without replacing metadata or skipping query evidence. The status
`cache-mismatch-observed` is a failing diagnostic result, distinct from process
failure or query state mutation. It does not claim an original mutation
journey comparison. Baseline and candidate should both be retained so any
preexisting cache defect is distinguished from predicate changes.

The eight focused journey evidence tests cover complete intentional mutations,
stale cached item identity, unsafe/partial completion, wrong physical output,
inter-step continuity, stale extra files, query mutation/equality flags,
implicit-sender action resolution and explicit failed-prefix review.
The total Phase1 Python suite passes45 tests. These validate ingestion policy,
not engine cache behavior; the actual API host remains unexecuted by this
worker. No shared files, existing results, engine source or binaries were
changed during this review/extension task.
