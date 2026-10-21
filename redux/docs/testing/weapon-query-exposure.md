# Phase 0 — EE weapon-query exposure and compatibility plan

October 21 LAB continuation: [final coverage and limits](phase0-expanded-coverage.md) and [release evidence](../PHASE0_RELEASE.md) supersede historical pending-run statements below. Original live branch/combat capture, repeated-query state observations and the 151-test consolidated baseline are now executed; known differences remain.

October 20, 2026 PDT / October 21 UTC. Read-only source/resource inspection; no engine changes or proposed gameplay change is implemented.

## Verified limitation and packaged use

Pinned [WeaponEffectiveVs](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GameScript/Triggers.cpp#L4740) and [WeaponCanDamage](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GameScript/Triggers.cpp#L4754) resolve actor/target, then log an unimplemented error and return0. Invalid actors also return0. The earlier opening run's two WeaponEffectiveVs errors establish actual invocation, not which branch or target produced them.

The [IESDP trigger reference](https://gibberlings3.github.io/iesdp/scripting/triggers/bgeetriggers.htm#0x40EC) describes WeaponEffectiveVs as testing whether the selected hand's weapon can hit a target, and WeaponCanDamage as testing whether it can deal non-zero damage. This is useful intended-contract documentation, not a complete original-executable truth table. Stoneskin, mirror image, damage-type immunity, protection from magical weapons and related boundaries still require direct original-game tests. The pinned source explicitly leaves those details unresolved.

`harness.py weapon-triggers` parses **4,358 KEY-listed BCS resources /173,315 trigger records**, with no rejected scripts. It supports the observed BG2EE compiled-text layout; unmatched trigger records fail instead of being silently omitted. The [compiled trigger reader](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GameScript/ParseBCS.cpp#L103) grounds opcode/parameter/negation extraction. This tool is not a BCS interpreter, full provider resolver, dialogue scan or runtime branch trace.

[Machine evidence](../compatibility/evidence/weapon-trigger-results.json): **84 WeaponEffectiveVs and84 WeaponCanDamage records**, paired in84 response conditions across24 scripts. All specify hand1, MAINHAND in this dataset's hand.ids. All affected conditions use positive queries and contain no OR trigger. Given the current handlers' false result, those individual conditions cannot succeed. This is a source-and-data inference; it is not84 observed runtime failures.

Twenty-three companion/default scripts each contain three affected conditions leading to AttackOneRound: BDAERIEC, BDANOMEC, BDCERNDC, BDDEFAI, BDDORNC, BDEDWINC, BDHAERC, BDHEXXAC, BDIMOENC, BDJAHEIC, BDJANC, BDKELDOC, BDKORGAC, BDMAZZYC, BDMINSCC, BDNALIAC, BDNEERAC, BDRASAAC, BDSAREVC, BDVALYGC, BDVICONC, BDWILSOC and BDYOSHIC. BDSUM00 supplies the other15 conditions, whose listed response is NoAction.

**Do not infer that companions cannot attack.** BDDEFAI and BDIMOENC also contain later AttackOneRound fallback conditions without these queries. Earlier ranged/spell decisions may apply too. Which fallback runs, how targeting changes and whether damage effectiveness suffers need actual decision/action observations. Static reference count is neither encounter count nor severity by itself.

The baseline GAM's embedded party CREs assign DPLAYER3 to the protagonist's default slot; Imoen has override IMOEN, class BDIMOENC and default DPLAYER2. These are independently read saved assignments, not proof of every current runtime attachment. Together with the opening log and packaged branch use, they justify prioritizing this compatibility work over speculative queue deduplication or combat redesign.

## Architectural disposition

**Retain GameScript parsing and scheduling; implement the missing legacy predicates after characterization.** A wholesale script engine replacement would not resolve the missing contract and would risk existing immediate/blocking action semantics. Keep the future diagnostic/query boundary separate from rules changes.

Prefer a small, side-effect-free weapon/target query shared with the relevant combat predicates once original behavior is known. Existing [weapon selection](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Actor.cpp#L6389), [combat details](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Actor.cpp#L6985) and [weapon immunity check](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Actor.cpp#L9615) are dependencies to inspect, not drop-in implementations of either EE trigger. A hypothetical query must not roll attacks, consume mirror images/Stoneskin, apply effects, emit combat feedback, advance actions or change RNG state. Reusing a mutating resolution path just to ask a question would create a new compatibility defect.

## Prioritized proof before an engine patch

1. Build an original-engine query fixture with recorded actor/target, hand, selected weapon/ammo, defenses and executable/data hashes. Start with ordinary hittable/damageable targets and enchantment/protection contrasts. Use stock scripting outputs where possible so EEex is not required.
2. Record separate Boolean results for both queries. Extend to main/off/both hands, empty hand/fists, ranged launcher/ammo, physical immunity, elemental secondary damage, Stoneskin/mirror image/PfMW, dead/missing/invisible targets. Do not fill unknown cells with assumptions.
3. Run equivalent input through GemRB and keep stub results as expected failures. Trace the selected BCS response and queued action in BDIMOENC/BDDEFAI, including the later fallback. Repeat with ally/enemy and invalid target cases.
4. Propose the narrowest shared predicate only after the truth table distinguishes can-hit from can-damage. Preserve fallback behavior and existing attack resolution; add cause-specific observations without presenting predictions as resolved combat outcomes.

The harness currently has **43 passing unit tests**, including malformed compiled records, OR alternatives and negated queries. These validate the census/oracle, not original trigger behavior. Full AI/campaign parity remains open.

Follow-up: [original scripted comparison](original-script-query-results.md) executes the same two-query fixture in both runtimes. Original returns1/1, GemRB0/0, with completion markers in both autosaves. This supplies the first observed fists/MAINHAND case; it does not replace the remaining truth-table/branch-trace gates.52 harness tests now pass.

## Executed equipped and attack-tail follow-up

[New results](equipped-defenses-and-ai-fallback.md) supersede the equipped preflight's unexecuted status: eight identical-input original/native query cases complete, with14/16 values different. Original magical-weapon protection gives0/1 for a +1 sword; slashing100 gives1/0 for a normal sword. Six other cases give1/1, including Stoneskin/mirror images. Keep the predicate contracts separate. Four native AI tails sample actual attacks: guarded variants choose118/310 fallback, noquery laboratory controls115/307. Original AI visibly attacks but its branch is not captured. Full-script severity, actual damage/charge consumption and query side effects remain open; no engine implementation has been made.
