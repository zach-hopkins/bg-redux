# Phase 0 — equipped weapons, defenses and AI fallback execution

October 21 LAB continuation: [final coverage and limits](phase0-expanded-coverage.md) and [release evidence](../PHASE0_RELEASE.md) supersede historical pending-run statements below. Original live branch/combat capture, repeated-query state observations and the 151-test consolidated baseline are now executed; known differences remain.

October 21, 2026 PDT. Engine checkout and engine/plugin binaries remain unchanged. The external GUI test host gained read-only action/target samples and a final runtime snapshot; that host is outside engine source.

## Executed equipped/defense cases

Eight fresh GemRB processes completed the ordinary BCS query/autosave route, exit0. Each input declares the actual item table, physical slot, equipped selection and ability. The output save must retain that setup as well as both explicit Boolean globals and the final completion markers. A separate post-load paused snapshot checks runtime equipment/derived defenses before the script runs.

| Case | Equipped weapon | Target defense | GemRB EffectiveVs / CanDamage | Original BG2EE |
|---|---|---|---|---|
| 01 | SW1H01, enchantment0 | Baseline | 0 / 0 | 1 / 1 |
| 02 | SW1H02, enchantment1 | Baseline | 0 / 0 | 1 / 1 |
| 03 | SW1H01 | Diagnostic protection from magical weapons | 0 / 0 | 1 / 1 |
| 04 | SW1H02 | Diagnostic protection from magical weapons | 0 / 0 | 0 / 1 |
| 05 | SW1H01 | Slashing resistance100 | 0 / 0 | 1 / 0 |
| 06 | SW1H02 | Three Stoneskins | 0 / 0 | 1 / 1 |
| 07 | SW1H02 | Three mirror images | 0 / 0 | 1 / 1 |
| 08 | BOW01 + AROW01 | Baseline | 0 / 0 | 1 / 1 |

All queries use MAINHAND against party member2. These zero results are consistent with the verified stubs, **not a defense compatibility pass**. The original engine now completes all eight identical-input cases. The independently re-read saves show14/16 predicate values differ, across all eight cases. [Frozen original comparison](../compatibility/evidence/original-equipped-comparison.json) binds the original receipts and native outputs. [Native execution/inputs/output saves](../compatibility/evidence/equipped-defense-results.json), [runtime preflight](../compatibility/evidence/equipped-runtime-preflight.json). Native run: `20261021T174444Z-equipped-defenses-41fae879`.

The post-load runtime preflight independently observes selected melee slot0 and the actual sword in internal slot35; the ranged case selects ammo code-24, with BOW01 in35 and AROW01 in11. Target Modified stats show slashing resistance100 (stat21), Stoneskins3 (stat88), and mirror images3 (stat254) in the respective cases. The output retains each declared defense effect. The weapon-protection case retains opcode120/mode1; GemRB normalizes Parameter1 to0xffffffff. No attack is performed in these query cases, so actual resistance, image consumption, damage suppression and query side-effect freedom are not established.

## Fixture construction and failed preflight

Disposable GAMEV2.0 files append relocated embedded CRE V1.0 copies and update only the corresponding party CRE offset/size. Appended CREs point to their own inventory/effect tables; original GAM sections and obsolete unreferenced bytes remain intact. The protagonist receives only the declared sword, or bow/arrows. Baseline actor scripts are replaced by the bounded probe. Other baseline stats/content remain; defender effects are appended, preserving existing effects. Custom v2 effects use source RDXDEF, timing9, probability100: opcode120 /0/1, opcode86 /100/1, opcode218 /3/0, or opcode159 /3/0. These are synthetic isolated defenses, not complete stock spell-casting scenarios.

The first eight-run attempt failed its equipment gate: the sword remained in a weapon slot, but the inherited GAM quick slots still named fists. The output used equipped code-25 rather than required0. Those are **invalid test setups**, not eight weapon-predicate observations. Source inspection distinguishes [CRE item-slot translation](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/CREImporter/CREImporter.cpp#L1115), [GAM quick weapons](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/GAMImporter/GAMImporter.cpp#L424) and the [BG2EE slot table](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/unhardcoded/bg2ee/slottype.2da#L14). Correcting the disposable GAM quick-slot IDs to35 for melee or11 for ammo, with ability0, fixes the setup; input/output/runtime gates then pass. Failed development run: `20261021T174150Z-equipped-defenses-8f6fc32d`.

Preserve this preflight in future tests: owning an item, placing it in a physical slot, selecting the weapon/ammo and selecting its ability are separate facts. A query script finishing does not establish any of them.

## Executed AI attack-selection tails

Four fresh native processes execute an isolated four-block attack tail copied from each packaged BDIMOENC or BDDEFAI script. All original conditions and AttackOneRound payloads are retained, with explicit laboratory instrumentation. An idle synthetic RDXFOE replaces the embedded Mephit originally at2573,2461, moves40px east of the protagonist, has EA255/HP200, no effects/scripts, and no weapon. The protagonist holds SW1H02. Other area actors/scripts remain.

The controls remove exactly six query trigger records (two in each of three preferred attack conditions) from the private script only. They are **not an engine implementation or a proposed behavior patch**. Earlier/later full-script branches are deliberately absent, so this test characterizes what happens upon reaching the attack tail, not whether the full AI would first heal, cast or choose another action.

| Source tail | Private script condition | Selected stock block | Sampled action / target |
|---|---|---:|---|
| BDIMOENC115–118 | Original query guards retained | 118, fallback | AttackOneRound105 → RDXFOE |
| BDIMOENC115–118 | Query guards removed | 115, first preferred condition | AttackOneRound105 → RDXFOE |
| BDDEFAI307–310 | Original query guards retained | 310, fallback | AttackOneRound105 → RDXFOE |
| BDDEFAI307–310 | Query guards removed | 307, first preferred condition | AttackOneRound105 → RDXFOE |

[Machine results, source-script hashes and input manifests](../compatibility/evidence/ai-fallback-results.json) bind these observations to each run. Markers alone do not pass: the oracle checks a named-foe visibility marker, a valid tail block, the selected +1 weapon, and actual normal-loop samples with current action105 targeting that specific foe's runtime ID. Damage varies under uncontrolled RNG; do not compare the raw HP differences as evidence that either branch improves DPR.

This confirms the earlier caution: **the missing predicates divert preferred conditions, but the later fallback still attacks in this controlled case**. Both tails select the same nearest synthetic foe. Alternate target choice, defense discrimination, spell decisions, full-script scheduling, and campaign consequences remain open. A generic interpreter rewrite would not supply the missing predicate contract.

Instrumentation adds one named-foe visibility response, one-response gates and response-entry globals. It then preserves the original attack, followed by laboratory cleanup (neutralize the foe, Wait3, request SaveGame0). RDXAIDONE means the response was entered, not that the entire action queue or autosave finished. The core execution evidence is the sampled action/target and final runtime state.

## Observation failures and timing follow-up

The first AI wrapper unnecessarily tried to locate the removed Mephit for a generic live-clock run. Its effect-specific assumption failed after the native process; it is fixed so generic live-clock cases do not require that target. A subsequent save-dependent result gate also failed despite actual attacks. The external host now records final state and current actions/targets, and the oracle validates that independent evidence. Earlier failed receipts/raw runs remain available; their status is not silently rewritten as a successful autosave.

The four-case provenance rerun freezes the verified driver build receipt and driver source copies in each run directory before launch. This avoids losing the only old driver receipt when later external host builds overwrite the shared build.json. Engine/core/plugin provenance remains separate from the test driver.

A longer bounded [Wait characterization](../compatibility/evidence/ai-wait-characterization.json) observes the Wait3 counter advance through45 ticks over about3s, then finish. No completed autosave appears even by the end of that longer run. This does **not** establish a Wait timing bug. The scripted save's return code was not captured; the reason for no save is unresolved. [Normal save restrictions](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/SaveGameIterator.cpp#L453) include combat, nearby enemies and other state. Do not infer the exact rejection branch from missing files or a feedback sound. A future save diagnostic should record the actual result and relevant state without forcing save success.

Development-only external-host compilation initially missed ie_stats.h; the corrected host builds and the subsequent processes exit0. Engine code was not changed for that repair.

## Original execution and remaining gate

[Nine prepared original inputs](../compatibility/evidence/original-equipped-preparation.json) cover the eight equipment/defense cases plus the BDIMOENC stock-tail case. After user restoration, the private original window became accessible. All eight equipment fixtures were selected and loaded through the ordinary GUI, then completed their script-driven autosaves without movement/attack commands. Frozen outputs retain the declared equipment/defenses and completion markers, with identical input manifests across engines. The original executable and each script remain hash-bound. A separate Chapter1 Start autosave appeared in the private profile; named input folders remain intact. The optional Steam DLL remains retained under an inert filename in the private game copy.

The original truth table demonstrates different contracts: magical-weapon protection changes EffectiveVs for the +1 sword to0 while CanDamage remains1; 100% slashing resistance changes CanDamage to0 while EffectiveVs remains1. Stoneskin and mirror images both give1/1. These are measured query values in synthetic fixtures, not a universal rule or proof of damage/charge behavior. Implementing both predicates as the same damage forecast would contradict this evidence.

The original AI fixture was also loaded. Its feedback visibly reports attacks and slashing damage, but no completed AI-marker autosave was captured. The parser correctly rejected the stale equipment autosave for missing AI markers. A subsequent ordinary GUI save attempt explicitly reports “You cannot save during combat.” This establishes that manual save rejection at that moment, not the reason for every earlier scripted request. The original selected block remains unknown; visible attacks do not establish block115/118 or the exact action/target ID. [Partial original AI observation](../compatibility/evidence/original-ai-observation.json) preserves this boundary. The private window is left at its combat-save feedback dialog. No full original AI parity claim is made.

Next extend dual-wield/launcher-ammo variants, enchantment thresholds and elemental secondary damage, actual stock protection spells, invalid sender controls and query side-effect measurements. Obtain an original AI branch observation independent of combat save availability, then compare full scripts only after isolating other decisions. Keep core/plugin code unchanged during this Phase0 work.

The harness suite has **71 passing tests**. New guards reject invalid/fists selection, wrong weapons, missing ammunition, missing/changed defenses, out-of-tail markers and wrong-target/nonexistent attack samples. These validate the observation machinery separately from the measured original/native compatibility differences.
