# P1-02: distinct read-only weapon predicates

Candidate implementation on `codex/phase1-weapon-predicates`, based on
`2cc14fbd0`. Engine edits are authorized for this Phase 1 task. This report
records implementation and compiler checks, not completed runtime acceptance
or completion of Phase 1.

## Contract and evidence

The eight Phase 0 paired fixtures in
[equipped defenses](../testing/equipped-defenses-and-ai-fallback.md) require
different predicates. The original normal/+1 swords and bow+arrow return
1/1. A +1 sword against diagnostic opcode120 magical-weapon protection
returns 0/1. A normal sword against slashing resistance100 returns 1/0.
Stoneskins3 and mirror images3 return 1/1. These observations do not establish
damage parity, charge consumption or secondary on-hit damage semantics.

[IESDP trigger documentation](https://gibberlings3.github.io/iesdp/scripting/triggers/bgeetriggers.htm#0x40EC)
describes a hit-eligibility query and a nonzero-damage query separately.
[HAND.IDS](https://gibberlings3.github.io/iesdp/files/ids/bgee/hand.htm)
defines MAINHAND1, OFFHAND2 and BOTH3. That reference does not define how
mixed hands combine. **BOTH currently uses an isolated any-hand policy;
this is unverified and must pass an original mixed-hand oracle before
acceptance.** Tests pin that implementation policy, not original parity.

## Implementation

The trigger handlers retain actor sender/target checks and dispatch only the
requested hand. Invalid hand values return false without inspecting either
weapon. OFFHAND reads its own cache; it does not borrow the main hand as
`Actor::GetWeapon` can. Empty or invalid cached item/header returns false.
These empty-hand/invalid-input policies also await expanded original controls.

`Actor::WeaponEffectiveVs` reads cached `WeaponInfo`, including the selected
ability and ammunition. It uses existing enchantment adjustments and the
target's const `EffectQueue::WeaponImmunity`. The enchantment helper now takes
the queried hand explicitly. The existing combat caller passes exactly its
previous `usedLeftHand` value; no combat rule or attack path is changed.

`Actor::WeaponCanDamage` independently selects the target-dependent base
damage type using existing `ConvertDamageType`, then reads its resistance
through `DamageInfoMap`. Resistance below100 permits damage; 100 or higher
does not. No resistance stat means no resistance barrier. It does not consult
weapon immunity, skins or images. This matches the measured separation;
it is not a simulation of whether a particular rolled attack deals damage.

The existing weapon cache, rather than new inventory selection, supplies
launcher/ammunition data. That cache currently takes maximum launcher/ammo
enchantment. This inherited behavior is source-grounded but **not yet verified
as the original query's launcher/ammo policy**. Hand-specific opcode344/345
adjustments are reused; their complete original-query behavior is unverified.

No query calls `GetCombatDetails`, `ModifyWeaponDamage`, `ModifyDamage`,
attack execution, RNG, inventory selection, stat setters or effect application.
Queries do not rebuild equipment caches. Existing effect-reference resolution
may populate global lookup metadata; this is not a claim that every hidden
cache remains untouched. Repeated collected-state observations remain required
against the newly built Phase 1 engine.

## Focused tests and validation

`gemrb/tests/core/Test_WeaponQuery.cpp` adds four GoogleTest cases to
`Test_gemrb_core`: invalid hand avoids both callbacks; explicit hand avoids
fallback/other-hand access; the isolated pending-oracle BOTH truth table;
and negative/99/100/100-plus resistance boundaries. These are policy tests,
not initialized Actor/effect/inventory integration tests.

Executed here:

- `git diff --check`: passed.
- UCRT `g++ -fsyntax-only -std=gnu++14` for `Actor.cpp` and `Triggers.cpp`:
  passed with the existing generated Phase 0 configuration/include paths and
  core/FMT defines. No object or binary was emitted.
- UCRT `g++ -fsyntax-only -std=gnu++17 -DGTEST_LINKED_AS_SHARED_LIBRARY=1
  gemrb/tests/core/Test_WeaponQuery.cpp`: passed.

The compiler is
`C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/g++.exe`. Its directory
must be prepended to PATH. An initial syntax-check invocation without that
PATH exited1 with no diagnostics; all three checks after setting PATH exited0.
No native process, game, engine build or test executable ran in this worktree.
Coordinator P1-01 owns the fresh isolated build and runtime validation.

## Acceptance still required

Run the eight original fixtures against the new engine and compare all16
Boolean results, then repeat the side-effect captures with True/False controls.
The Phase 0 side-effect validator deliberately requires old stub log counts
and all-zero values; preserve that historical validator and use a Phase 1
contract instead of treating its stub-specific failure as mutation evidence.
Re-run paired AI tails: normal +1 stock conditions should reach the preferred
branch while still sampling AttackOneRound against the declared foe.

Expanded paired original cases requested from the coordinator:

1. Main normal/off +1 sword and reversed hands against magical protection;
   query1/2/3. Empty off-hand and shield controls. Mixed hands settle BOTH.
2. Main crushing/off slashing, then reversed, against slashing100; query1/2/3.
3. Normal launcher/+1 ammo and +1 launcher/normal ammo against enchantment
   thresholds0/1/2 and magical protection; verify selected ammo/header/flags.
4. Crushing, piercing and missile100, plus unrelated resistance100 controls.

Compound damage types, elemental secondary on-hit effects, zero-dice weapons,
stock protection spells and enchantment modifiers require further paired
coverage. Current CanDamage examines the selected base damage channel only;
it does not inspect arbitrary feature opcodes, proc probabilities or damage
bonuses. Do not advertise those cases as compatible or infer DPR. Keep
failures and raw results rather than weakening evidence gates.
