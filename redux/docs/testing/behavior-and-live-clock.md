# Phase 0 — protection behavior, creature exposure and live clock

October 20, 2026 PDT / October 21 UTC. Engine revision `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351` and engine/plugin binaries remain unchanged. All new C++ is in the external host. All effects and simulation runs use disposable copies; personal game sessions are not attached.

## Opcode267: observed behavior rather than return-code inference

The [original reference](equip-exposure-and-original-reference.md) established matching IMMCLOUD count growth but a Parameter2 serialization difference. The [protection handler](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/FXOpcodes/FXOpcodes.cpp#L7332) sets Parameter2 to0. The [DisplayString handler](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/FXOpcodes/FXOpcodes.cpp#L4552) queries protection using the string reference and Parameter2=0. The effect dispatcher also [checks string protection for first-application feedback](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1242).

`harness.py string-challenge` loads the baseline, original r1 and original r2 in three fresh normal-mode GemRB processes. Each selects the same Mephit, then applies controlled DisplayString effects through `Interface::ApplyEffect`, not by directly calling the opcode handler. This is explicit laboratory construction, not a player cast, inventory command or original-BG2EE behavioral test.

For each input:

1. All five loaded string protections suppress the matching message: the actual message TextArea text remains identical.
2. Remove only that private actor's Protection:String effects and refresh; all five DisplayString challenges append their expected text. The Python oracle requires the expected text in the newly appended suffix, not somewhere in an older log.
3. Apply a protection for string14665 with Parameter2=134 through the ordinary effect queue. It is normalized to0 and suppresses the next matching message.
4. Check that the synchronous challenge interventions do not advance game time or alter the target's base stats. Modified stats and arbitrary combat state are not declared invariant.

**Results:** three processes exit0; **48/48 observations pass** ([execution evidence](../compatibility/evidence/string-challenge-results.json)). All eleven DisplayString applications per process return0, whether they suppress or display text. A return-code-only test would not distinguish those outcomes. No save is created by this destructive laboratory case; input and source fixtures remain hashed and unchanged.

**Conclusion within scope:** imported original protections still suppress these messages in GemRB despite the wire-field difference. That supports the existing normalization contract for this fixture. It does not establish original-runtime outcome parity, arbitrary mod semantics, complete save equivalence or combat correctness. Keep raw Parameter2 differences visible; do not silently normalize the compatibility comparator or recommend a deduplication fix.

## Packaged creature loadouts

The [read-only census](../compatibility/evidence/cre-loadout-results.json) parses all **4,735 KEY-listed CRE resources**, all CRE V1.0, without errors. It validates the item table and38 raw file-slot indices, following the inspected [importer slot-table path](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/CREImporter/CREImporter.cpp#L1088). This scanner shares the metadata reader's limited resource-provider scope; it is not a full game/mod-provider resolver.

Seventeen of the32 candidate items occur in111 creature resources. IMMCLOUD appears in53, RING09 in10 and MAGIWEB in0. These are resource references, not53 encounters or a count of bugs. Item presence in a table, including a raw slot index, does not prove the item is equipped at runtime. Scripts, spells, stores, containers and dynamically generated loadouts are not covered; zero CRE matches does not mean unused game content.

The earlier MAGIWEB substitution remains a synthetic contrast. Prioritize natural IMMCLOUD loadouts for removal/stacking investigation before presenting MAGIWEB as a campaign defect. Retain RING09 as a useful negative lifetime contrast.

## Actual main-loop clock and startup readiness

The [main loop](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Interface.cpp#L1055) gates GameLoop by elapsed milliseconds and updates `lastGameUpdate` to the current time after a single update; it is not a general catch-up accumulator. The [configured simulation rate](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Interface.cpp#L476) comes from Maximum Frame Rate divided by2. `CapFPS` limits buffer swapping separately. These observations justify an explicit clock/step contract before claiming deterministic replay; they do not by themselves establish a movement defect.

The first live-clock run (`20261021T032744Z-live-clock-49ee9f31`) exited0 twice but passed only8/10 observations: the intended initial pause was lost. Raw samples show dialogue flags8→0 and game time advancing. Source inspection identifies a concrete interfering callback: [LoadScreen.EndLoadScreen](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/GUIScripts/bg2/LoadScreen.py#L70) installs an unpause-on-close callback and schedules close500ms later. Having a game and game control is insufficient readiness for a paused scenario.

The external live-clock adapter now waits until the LOADWIN alias is gone, with a bounded wait, before pausing and starting observations. It does not rewrite the stock callback or repeatedly force pause during the measured interval. It samples the actual main loop with1s nominal initial pause,2s nominal unpaused simulation and1s nominal final pause. Engine timers fire on observed wall time, so actual sample intervals may be longer. No direct GameLoop calls or synthetic time advancement are used.

Corrected run `20261021T032938Z-live-clock-bc8fe860`: two fresh processes exit0, **10/10 observations pass**, source fixture unchanged ([evidence](../compatibility/evidence/live-clock-results.json)). Each waited two observation callbacks for LOADWIN to close. Both initial and final pauses keep game time stable; resume advances monotonically.

| Requested render cap | Observed running interval | Game ticks | Observed game ticks/wall second | Configured ticks/second |
|---|---:|---:|---:|---:|
|30 |2,660ms |28 |10.526 |15 |
|60 |2,830ms |26 |9.187 |15 |

These are short opening-area measurements on this machine with scripts/resources active. They do not measure achieved render FPS, establish a statistically reliable cap comparison, explain the user's movement smoothness report, or verify an original-engine timing match. They do establish that configured rate is not a sufficient observation oracle. The harness records actual elapsed time and does not assert exact tick-rate equality or call this deterministic stepping.

One development attempt failed to compile because GameTime is atomic; the shell then launched a previous host binary under the new mode and hit its bounded45s timeout. This is external harness failure, not evidence of an engine timing defect. The common native launcher now refuses failed builds, binary/source/core-DLL hash drift before creating a run. The host also refuses unknown mode names. The failed artifacts remain under `phase0-local/results/live-clock-development/`.

## Implications for the foundation

- **Retain** the verified protection handlers and legacy format adapters for now. Add behavior cases before classifying representational differences as defects.
- **Wrap** startup readiness with an explicit post-load milestone. A future engine hook should acknowledge loading-screen closure, pause state and observation revision together; the current LOADWIN wait is a pinned legacy adapter.
- **Refactor later, after a clock ADR:** separate simulation progression, GUI timers, presentation and test stepping without changing ordering blindly. Document startup fade, script-freeze and pause behavior. Preserve observed live-loop fixtures alongside future deterministic ones.
- **Extend the harness through bounded commands and independent observations.** Do not infer behavior from effect return codes or treat native exit0 as scenario success. Missing cases, leaked protected messages, unrelated appended text and paused-clock drift are covered by oracle mutation tests.

The harness unit suite now has **39 passing tests**. Existing core-test locale failure/skips remain outstanding and were not reclassified. Full Phase0 acceptance remains open.
