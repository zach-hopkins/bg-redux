# P1-02 runtime item replacement and weapon caches

Status: reproduced on the preserved baseline; source fix awaits coordinator
build and native regression. This is inventory/cache coherence evidence, not
an original-game mutation journey comparison or a combat-damage measurement.

## Preserved reproduction

The complete native receipt is
`C:/BGRedux/phase1-local/results/20261022T005759Z-inventory-journey-a65af39d/result.json`
(SHA256 `ec0fd26eecd30df01bcc59bd60f9f54aa5082120b5ad439ebcc32bef0444539f`).
Its artifact manifest SHA256 is
`d6f97542fb60c44360109bfddebe5fb798b6023c060c17e7328b4899dfde2a46`.
Independent review rehashed all 785 manifest entries and ingested all ten
stages using the strict journey validator. Phase 0 and candidate before/after
inventories matched. Each stage retains mutation snapshots, exact inventory
slots, actual cached item/header metadata, repeated six-hand query results,
True/False controls and before/after query snapshots.

| Stage | Actual offhand after mutation | Cached offhand | Route |
|---|---|---|---|
| 05-create-plus | SW1H02, enchantment 1 | SW1H01, enchantment 0 | explicit-slot CreateItem API calls |
| 07-transform-plus | SW1H02, enchantment 1 | SW1H01, enchantment 0 | parsed shipped TransformItem action 356 |
| 09-create-normal | SW1H01, enchantment 0 | SW1H02, enchantment 1 | explicit-slot CreateItem API calls |

Ordinary removal, shield replacement and ordinary add/reset stages were
coherent. Both sword resources use animation S0. All 140 observations
(120 predicate calls and 20 controls) retained collected state/cache equality
and stable repeated values. Baseline predicates are stubs returning zero;
those values establish no fixed-query semantics. The retained resource
references in the external driver prevent dereferencing freed cached items;
unknown pointer identities stop the driver before queries.

The earlier incomplete journey and its failed TransformItem target guard
remain preserved separately. The complete run records the parsed no-object
action, old/new resources, target count 37, and implicit sender runtime ID
10002 before actual dispatch. It does not substitute TransformItemCore for
the action.

## Root cause and bounded source change

`Inventory::SetSlotItemRes` replaces the CRE item through SetSlotItem without
refreshing derived weapon metadata. CreateItem subsequently calls EquipItem,
whose offhand path refreshes only when UpdateShieldAnimation reports a change.
TransformItemCore calls SetSlotItemRes without EquipItem. Equal animation thus
leaves the previous item/header/enchantment in the cache on both paths.

After successful item creation, SetSlotItemRes now checks whether an actor
already has an initialized weapon cache and the destination is an active
selected weapon/ammo slot, offhand, selected launcher, or magic slot. It
refreshes those caches immediately after replacement. The launcher is included
because cached ranged bonuses and combat enchantment depend on it even when
the selected slot holds ammunition. The offhand is included when currently
holding a shield or empty, so a replacement can establish a new offhand cache.

The initialization guard avoids introducing eager cache initialization during
fist setup; low-level CRE loading still uses unchanged SetSlotItem. Backpack
and inactive weapon slots do not trigger this refresh. Failed item creation
does not refresh or replace anything. Empty-resource deletion retains the
existing KillSlot refresh path. No query/UI refresh, equip-effect application,
animation rewrite, damage formula or combat-enchantment policy changes.

The three reproduced transitions are offhand cases. The selected mainhand,
ammo, launcher and magic-slot dependencies follow CacheWeaponInfo/GetUsedWeapon
source logic; native coverage of those additional replacement paths remains
to be collected rather than inferred from the offhand result.

## Regression gate

The existing external ten-stage journey exercises initialized Actor methods
through actual inventory APIs and the shipped action parser. Its CLI returns
success only for `journey-observed-cache-coherent`; stale cache observations,
state mutations, unstable values, missing evidence and incomplete execution
remain failures. The new evidence regression reproduces all three observed
stale transitions, including reverse enchantment 1-to-0, and confirms the
validator preserves them as mismatches rather than waiving them.

Worker verification: 46 Python tests passed and git diff --check passed.
No engine/native compilation or launch was performed by this worker. The
coordinator must preserve the before-fix candidate journey, build the fix,
repeat the identical ten stages with zero cache mismatches and no query
mutations/unstable values, and retain provenance/preservation receipts. The
22-case original-query comparison remains a separate required regression.
Collected snapshots do not establish hidden-state or RNG purity.
