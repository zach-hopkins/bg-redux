# Phase 0 — permanent equip exposure and original-reference gate

October 20, 2026 PDT / October 21 UTC. Pinned engine revision `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351`; engine source and binaries remain unchanged. This extends the [IMMCLOUD investigation](immcloud-lifecycle-investigation.md), without applying a production fix.

**Result:** permanent-timing equip effects occur in32 of2,867 inspected item resources. Two controlled item-block experiments show why these are candidates rather than32 bugs: RING09's one-shot cures do not accumulate, while MAGIWEB's protection effects do. The original BG2EE 2.7.3.0 GUI reference now exists: selected saved IMMCLOUD counts grow **7→14→21**, matching GemRB. Saved record signatures still differ, so this is count agreement, not full save fidelity.

[Scan and execution receipts](../compatibility/evidence/equip-exposure-results.json), [original-reference status](../compatibility/evidence/original-reference-status.json), [tool usage](../../tools/phase0/README.md).

## Data exposure

The read-only scan enumerates KEY item resources and checks each item header, equipping feature offset/count and48-byte effect records with bounds checks. It reads fixture loose override/language resources before packaged resources. It does not reproduce all GemRB search providers, scan installed mod collections or establish that every listed item is naturally encountered/equipped in this campaign.

| Observation | Count |
|---|---:|
| Item resources inspected |2,867 |
| Equipping effect records inspected |11,795 |
| Items with timing1 equipping records |32 |
| Timing1 equipping records |84 |
| Unsupported/invalid item headers |0 |

The84 records include16 `FreeAction`,14 `Cure:Hold`,14 `Cure:Stun`,7 `Protection:String`,6 `Protection:Opcode` and6 palette-color effects, plus other operations. The complete item/parameter/opcode inventory and asset hashes are in the JSON evidence. The scan reads equipping effects specifically; ability-use effects are outside this count.

Every candidate resource:

```text
amul21 beholder bdhelm11 blun30 freering goboom3 immcloud jwsuper
mageamul magicold magiweb misc9s npplat ohhexam4 ring09 rossring
slimed2 sper12 sprngb04 sprngl03 sprngl04 sprngs01 sprngs02 sprngs03
sprngs04 sprngz05 staf11 sw1h50 sw2h06 sw2h13 swordi wolfwi2
```

**Do not replace timing1 globally.** A timing flag is only one part of effect lifetime. The [effect dispatcher](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1255) also consumes handler outcomes: `FX_NOT_APPLIED` expires an effect, while `FX_APPLIED` can retain it. Some `FX_PERMANENT` handlers apply a permanent state change and expire the queue entry. Therefore a static timing1 count is neither a retained-effect count nor proof of reload growth.

## Controlled contrasts

Run: `20261021T030127Z-equip-exposure-f2d38305`. Four fresh normal-mode processes exit0; all five scenario observations pass. Each uses the established stock GUI load/EnterGame path, two paused effect refreshes and an ordinary native save.

The tests keep the same saved Mephit carrier and replace **only the private `IMMCLOUD.ITM` provider bytes** with the inspected RING09 or MAGIWEB item resource. Consequently runtime SourceRef remains `IMMCLOUD`. The input contains seven pre-existing IMMCLOUD permanent effects. These are deliberately synthetic item-block contrasts, not natural RING09/MAGIWEB loadouts or original-executable tests. Game assets and normal player configuration are untouched.

| Private carrier block | Cycles | Saved source-effect progression | Conclusion within this fixture |
|---|---:|---|---|
| RING09 |2 |7→7→7 |Its timing1 cures are consumed; no saved growth |
| MAGIWEB |2 |7→13→19 |Its six timing1 protections survive and are re-added |

RING09 also supplies40 retained while-equipped effects in this carrier: runtime source-effect counts stay47 before saving and return to7 on disk. The cure handlers for [hold](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/FXOpcodes/FXOpcodes.cpp#L5124), [stun](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/FXOpcodes/FXOpcodes.cpp#L2437) and [slow/FreeAction](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/FXOpcodes/FXOpcodes.cpp#L5140) illustrate one-shot cleanup. The exact runtime observation is more informative than interpreting the timing byte in isolation.

MAGIWEB's six permanent rows comprise two animation protections, one string protection and three opcode protections. Runtime source-effect counts grow13→19 and saved counts7→13→19. Same-session refreshes do not grow either contrast. These results justify a second targeted persistence fixture; they do not establish natural player impact, full save parity or equivalence to original BG2EE.

## Original-game reference adapter

The adapter discovers `Redux EE Reload 1` and `Redux EE Reload 2`, or accepts explicit paths, freezes copies and hashes the source and copied files before comparison. It uses the same independent SAV→ARE→embedded CRE reader and unique target identity as the GemRB experiment. Missing inputs return `pending-reference`/exit2, never pass or skip. Changes during copy, unsupported formats, invalid bounds and EEex markers fail the reference gate. Marker absence alone is explicitly insufficient to certify a clean game.

The user authorized Codex to create the reference saves through the computer-use skill. Direct executable launch first crashed before the menu (cause unverified); double-clicking the observed Steam installation's Baldur application in Explorer succeeded. The returned process path and window title identified BG2EE2.7.3.0. Codex loaded `GemRB`, created **r1**, loaded **r1**, then created **r2**, observing both successful-save messages. Short names avoided an observed input limitation: `type_text` was ignored, whereas physical key presses worked. Existing saves were not overwritten; the game was left paused. Other running modded sessions were not targeted.

[Operator observation](../compatibility/evidence/original-ui-observation.json) binds the executable and both new save manifests. This is an operator-authored UI observation, not module attestation. All2,324 Steam source files still match the original manifest, with no extra files ([verification](../compatibility/evidence/original-source-verification.json)); there was no independent depot verification. The adapter freezes the saves and accepts this receipt only when executable and source-save hashes match. `--human-confirmed-clean` remains a separate user-attestation option; it was not used for this run.

**Timing limitation:** the first load ran before pause was confirmed; Imoen's AI cast Stoneskin/Armor. The second load also ran briefly before the clock was clicked. No manual movement command was issued. Both saves were created after visible PAUSED confirmation. This is not a zero-tick replay, and party/whole-world equality must not be inferred.

Run `20261021T031614Z-original-reference-d4d98065` established the reference; the latest status file also includes repeatable comparison with the existing GemRB lifecycle evidence. Both source saves and frozen copies are hashed. The unique Mephit remains readable at `[2573,2461]` in AR0602.

| Save observation | IMMCLOUD mode1 records | Embedded CRE bytes |
|---|---:|---:|
| Original baseline GemRB |7 |3,008 |
| Original BG2EE r1 |14 |4,856 |
| Original BG2EE r2 |21 |6,704 |
| GemRB first resave |14 |4,856 |
| GemRB second resave |21 |6,704 |

**Interpretation:** original BG2EE also retains and adds seven saved effects per reload/save. Accumulation alone does not establish a GemRB-specific compatibility defect. Preserve this behavior for now; do not ship the timing override or deduplication as a compatibility fix.

**Remaining verified wire difference:** original BG2EE preserves Parameter2 on opcode267 string protections (134 for string14665,216 for the other four strings), while GemRB writes0. Counts and opcode/Parameter1/timing multiplicities agree; full reported signatures do not. The [GemRB handler](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/FXOpcodes/FXOpcodes.cpp#L7332) explicitly resets Parameter2 and describes it as unused for this effect. This explains the observed serialization difference; harmlessness in every use or mod remains unverified. The comparator reports counts and signatures separately and does not erase this field. Neither protection outcomes nor full runtime parity were tested in original BG2EE.

Twenty-eight harness tests pass, including executable/save hash binding for operator receipts. Missing/unconfirmed references and malformed files retain their distinct outcomes. Synthetic unit fixtures are not original-runtime evidence. The engine's existing core-test locale failure/skips were not repaired or rerun.

## Architectural and implementation implications

1. **Retain effect handlers and format importers.** The observed differences depend on existing handler-return and timing contracts. Replacing the queue or parser would enlarge the compatibility surface without answering the original-runtime question.
2. **Make origin and lifetime observable before changing policy.** A future causal trace should distinguish imported saved effects, freshly generated equipment effects, spell applications and one-shot consumption. SourceRef and slot alone are not sufficient justification for a universal deduplication key; legitimate repeated applications must remain possible.
3. **Keep the correction bounded.** Original IMMCLOUD count growth agrees; next validate MAGIWEB in a natural fixture and test removal/stacking before selecting a compatibility rule. Preserve cure execution and permanent base-stat changes. The private carrier/timing overrides remain laboratory inputs.
4. **Use explicit harness outcomes.** `characterized` means the expected behavior was measured, including accumulation. `pending-reference` means missing required evidence. Neither is a native-like/save-fidelity pass. Add original reference artifacts to the fixture registry only after provenance and identity checks.

The original selected-record reference gate is now executed. Next prioritize causal effect observations and a natural MAGIWEB fixture; UI completeness, controlled clock/RNG, timed effects, containers, transitions and portable CI remain separate Phase0 gates.

## Subsequent behavioral validation

[Protection and live-clock tests](behavior-and-live-clock.md) now exercise actual DisplayString output in GemRB after importing baseline/r1/r2:48/48 observations pass. Opcode267 normalization preserves suppression for the selected fixture; full original-runtime/mod parity remains open. A packaged CRE scan finds IMMCLOUD references in53 resources and MAGIWEB in0, narrowing the next natural-loadout investigation without claiming unused content.
