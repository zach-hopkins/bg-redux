# P1-02 ammunition identity in WeaponEffectiveVs

Original cases9–16 distinguish the selected ammunition's own enchantment and
magical flag from the launcher's. The former candidate reused the combat
cache's maximum launcher/ammunition enchantment; that predicts a wrong query
for BOW02+AROW01 against protection from enchantment0. This record describes
independently verified original evidence and the source correction. The
coordinator retains the old core/host to capture its actual pre-fix mismatch;
no native pre-fix or fixed result is claimed here.

All eight references bind the exact preparation
`20261021T235241Z-weapon-oracle-ccf85085` (nonce690073517), input/script hashes,
original executable, loaded fixture and frozen output. Each independently
rehashed five save files and15 capture artifacts, and re-read all six values
from the frozen GAM rather than trusting the result JSON.

| Case | Launcher / ammunition | Diagnostic opcode120 | MAINHAND E/D | BOTH E/D | Frozen receipt suffix |
|---|---|---|---|---|---|
| 9 | BOW01 / AROW02 | Magical | 0/1 | 0/1 | 1a3d9378 |
| 10 | BOW01 / AROW02 | Enchantment≤0 | 1/1 | 1/1 | 93d7a40c |
| 11 | BOW01 / AROW02 | Enchantment≤1 | 0/1 | 0/1 | dd6d3bc6 |
| 12 | BOW01 / AROW02 | Enchantment≤2 | 0/1 | 0/1 | 4bffb304 |
| 13 | BOW02 / AROW01 | Magical | 1/1 | 1/1 | 7682657c |
| 14 | BOW02 / AROW01 | Enchantment≤0 | 0/1 | 0/1 | 864f6f9f |
| 15 | BOW02 / AROW01 | Enchantment≤1 | 0/1 | 0/1 | b65efd18 |
| 16 | BOW02 / AROW01 | Enchantment≤2 | 0/1 | 0/1 | cb88a641 |

OFFHAND returns0/0 in all eight cases. BOW01/AROW01 have enchantment0 and
BOW02/AROW02 have enchantment1. ITM flags are respectively174/44 and238/108;
the latter values contain the magical bit0x40. In both mixed pairs the combat
cache's maximum enchantment is1, yet original case10 and case14 differ.
Case9/case13 independently distinguish the ammo's magical flag from the bow's.
CanDamage remains1 in these protection cases, preserving the distinct query
contracts established in Phase0.

The machine-readable [verification record](evidence/phase1-ammo-query-enchantment.json)
records exact receipt paths/SHA256 values and stock item metadata hashes.
These are synthetic laboratory protection effects, not stock spell or actual
combat-damage observations.

## Minimal source correction

`Inventory::CacheWeaponInfo` already stores the selected ammunition as
`wi.item`, its selected header and its CRE flags as `wi.itemflags`. For ranged
combat it separately sets `wi.enchantment` to the maximum of ammo/launcher.
Changing that cache would change actual combat without combat evidence.

Only `Actor::WeaponEffectiveVs` changes. It makes a value copy of the selected
WeaponInfo, sets that copy's starting enchantment from `item->Enchantment`,
then passes the copy through existing AdjustEnchantment and WeaponImmunity.
Ammo-derived flags, item/header pointers, selection and all original cache
fields remain untouched. The same projection leaves ordinary melee unchanged,
since that cache already uses the item's enchantment.

`ModifyWeaponDamage`, CacheWeaponInfo, projectile damage, launcher bonuses and
combat immunity checks retain their existing inputs. No query repair of stale
caches, inventory/effect/stat writes or RNG calls are introduced. Opcode344/345
query interactions remain a separate unverified boundary; their existing
source behavior is reused on the projected value rather than asserted as
universal original parity.

## Validation and next coordinator gate

A focused C++ regression constructs actual Item/ITMExtHeader/WeaponInfo values
for both measured mixed pairs. It checks ammo0 vs cached1, ammo1 vs cached1,
the ammunition magical flag, selected item/header/slot/mode and launcher bonus,
and that source combat cache/item enchantments stay unchanged. The production
predicate uses that exact projection helper. This unit covers the projection;
it does not exercise initialized actors or effects by itself.

The worker ran43 Python evidence tests and `git diff --check`, both passing.
Per coordinator instruction the new C++ test and engine changes were not
compiled or launched by this worker. Coordinator acceptance must first retain
the old candidate's actual case14 mismatch (or other observed result), then
build the corrected source, compare all selected original values, and repeat
the before/after collected-state/cache observations. A failed build or setup
must remain distinct from a semantic result.
