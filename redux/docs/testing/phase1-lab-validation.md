# Phase 1 LAB validation status

Evidence checkpoint: October 22, 2026 UTC, after the completed candidate `9aa69cd5` inventory journey. Phase 1 engine work is authorized; the accepted Phase 0 source/build/results remain protected. This report updates the earlier first-batch pending descriptions. It does not declare Phase 1, all menus, combat or campaign fidelity complete.

Latest checkpoint: the later sections and linked summaries supersede pending
descriptions below. Earlier failures and incomplete runs retain their verdicts.

October22 UTC renderer checkpoint: **301 external Python tests pass**
(`phase1-integrated-tests-20261022T0520.log`). User-observed stale dialogue choices
led to a `Window::WillDraw` correction replacing only the active target's repaint
clip before drawing translucent backgrounds. Fresh candidate
`20261022T051113Z-candidate-df3a5c5e` retains all Phase0 preservation guards.
Its held-response frames match a cleared reference, twelve synthetic alpha/scale
cases pass216 image comparisons and96 opacity probes, and ordinary Jaheira
dialogue/save/fresh reload passes in `20261022T052139Z-jaheira-dialogue-82159919`.
The first broad-clear correction fails partial-clip tests and is rejected;
fixture alpha/probe-oracle failures remain preserved. Correct-CWD core testing
returns229 passes, one retained StringToUpper locale failure, nine skips and six
disabled tests; the direct CTest CWD/teardown crash is separately retained.
See [rendering evidence and limits](phase1-dialogue-rendering.md). Broader menu,
GameControl/world, nonzero-origin scaled and campaign regressions remain open.

October 22 UTC spell checkpoint: **276 external Python tests pass** in
`results/phase1-integrated-tests-20261022T0431.log`. Native run
`20261022T043347Z-spell-cast-journey-3dd76c87` passes ordinary Imoen portrait,
Cast and resref-bound Armor callbacks, one actual self-cast and observed release,
memorization consumption and new sourced persistent effects. GUI save/fresh
reload/second GUI save preserves depletion and expiration; reload performs no
cast. Both processes complete 89 samples and exit zero within their 90-second
bounds. All preservation checks pass, with exact runtime SPLDISP/GUIBTACT table
paths and bytes matched. Actual GUI save return codes are unobserved; real save
files and wire outcomes establish this bounded result. See the
[spell journey](phase1-spell-cast-journey.md). Earlier resource-provider and
external linker failures remain failed. No engine source or binary changed.

October 22 UTC dialogue checkpoint: **272 external Python tests pass** in
`results/phase1-integrated-tests-20261022T0426.log`, including twelve focused
dialogue methods. Fresh external build `candidate-9aa-ui1-jaheira-label6` and
run `20261022T042747Z-jaheira-dialogue-30a50511` pass: one TryToTalk, eleven
displayed branches through registered response/Continue/End callbacks, seventeen
operations including GUI save, then a separate process reload with no new talk.
The actual saved NPC counter is 1 and journal34105 is unique in section1/chapter1;
the prior entries, closed Cell01 and unrecruited two-member party persist.
Both owned processes exit zero (78.352/18.320 seconds); all preservation checks
pass. This is callback/state/wire coverage, not OS pointer or original parity.
The [journey report](phase1-jaheira-dialogue-journey.md) retains the direct-entry
assertion, its debugger trace, capitalization-guard failure and failed builds.
The [direct public UpdateState defect](../compatibility/phase1-textarea-update-state-reentrancy.md)
remains open; normal selection success does not repair it. No engine source or
binary changed during this checkpoint. The separate spell adapter passes its
synthetic validators but its first build rejects a game-only resource-provider
assumption; its later bounded native pass is recorded above.
The [independent dialogue audit](phase1-jaheira-dialogue-lab-audit.md) confirms
567 retained artifacts and the saved/reloaded talk-counter and journal effects.

October 22 UTC readiness follow-up: external tooling passes **243 tests** in
`results/phase1-integrated-tests-20261022T0358.log`. The corrected readiness
adapter passes 21 focused tests and fresh external compilation in
`weapon-query-probes/candidate-9aa-ui1-loot-ready5/build.json`. Native run
`20261022T040338Z-container-loot-journey-25ffdf30` passes both fresh processes:
one UseContainer command at sample 9, actual stock take/close callbacks at
sample 31, table 11 to 10 items and leader 0 to 1 SW1H04. Ordinary save returns
zero, frozen output reload preserves ownership, and its second ordinary save
also returns zero. Each process completes 89 samples, including 80 running;
Phase 0, candidate, private-input and output preservation checks pass. This
observes external callback dispatch, without OS pointer input or original parity.
The [journey report](phase1-container-loot-journey.md) retains the three earlier
failed native runs. Readiness adapter build `candidate-9aa-ui1-loot-ready4`
also remains failed: explicit `StringView(name)` fixes an external C++ string
comparison; no engine source or binary changed for this rerun.
The [independent loot audit](phase1-container-loot-audit.md) rechecks 500
artifacts, 34 source bindings and the complete saved-file chain, with a separate
wire decoder confirming the item in the leader and absent from the table.

October 22, 03:38 UTC follow-up: external tooling passes **237 tests** in
`results/phase1-integrated-tests-20261022T0335.log`. The new active-slot run
`20261022T033723Z-active-slot-run-81396091` passes main/ranged scenarios with
14 stages and 196 query calls, coherent caches, stable values and unchanged
calling-thread RNG. Candidate and Phase 0 preservation checks pass. The
[independent audit](phase1-active-slot-journey.md) confirms 588 byte-equal query
snapshot pairs and the reverse launcher THAC0 restoration. Three deliberate
mutation boundaries changed RNG; the query intervals did not. Original mutation
parity and magic-slot coverage remain
unobserved. The [original color controls audit](phase1-original-color-controls-audit.md)
completes the low and stock-selector reference observations alongside the earlier
[paired controlled-color audit](phase1-paired-color-audit.md).

The separate container journey has three preserved failed runs:
`20261022T032531Z-container-loot-journey-c3703e13` and
`20261022T032917Z-container-loot-journey-eff5ffad` reject an external stored-name
versus normalized-script-name assumption; no transfer occurs. Corrected external
host run `20261022T033328Z-container-loot-journey-42d3a11e` observes normal
approach movement to the table, but no container UI or transfer before its bound.
The queued UseContainer action is seen briefly, then absent while movement
continues. These three failures remain historical evidence, superseded for the
corrected bounded route by the later pass above. All three retain passing input,
candidate and protected Phase 0 checks. No production fix or general P1-06
completion is claimed.

## Fresh isolated regression checkpoint

The [isolated regression summary](../compatibility/evidence/phase1-isolated-regression-lab.json)
binds candidate `9aa69cd5` to new private-folder runs: query
`20261022T020452Z-phase1-weapon-query-54df55ff` matches 22 original cases and
preserves calling-thread RNG and collected state across 1,100 observations;
cache run `20261022T020405Z-inventory-journey-69ac9c88` completes ten coherent
stages. Deliberate draw control `20261022T020930Z-phase1-weapon-query-468541fb`
remains failed as intended, detecting a real draw at call 3. All three pass
source-root, private-input, candidate and protected Phase 0 preservation checks.

Separate runtime `runtime-candidate-9aa69cd5-guarded` uses the frozen build-matched
source from preparation onward. Vanilla run
`20261022T021035Z-phase1-9aa-guarded-vanilla-60ea184f` passes 24 assertions and
GUI run `20261022T021057Z-phase1-9aa-guarded-gui-c6ac9bbf` passes 20. The new
preservation receipt records `all_preserved: true`; both compatibility verdicts
still record persistence differences. This does not relabel the prior broad
guard failure. Private-folder guards hash root inputs and inventory; the separate
2,324-asset check supplies content coverage for linked assets.

Selected menus now complete 107 checks, 107 actions and 51 captures at each of
1024×768 and 1280×960 in `20261022T015239Z-menu-run-b9d5ebb2`.
The [menu summary](../compatibility/evidence/phase1-menu-lab.json) retains the
earlier callback failure and timeout. Selected actual font provider/face/size
metadata is checked; complete typography, pointer and menu-family fidelity is open.
The [opaque hotkey journey](../compatibility/evidence/phase1-hotkeys-opaque-lab.json)
and [RNG snapshot cost](../compatibility/evidence/phase1-rng-cost-lab.json) have
their own bounded native results. Neither establishes physical keyboard fidelity
or full game performance. External tooling passes 212 Python tests in
`results/phase1-integrated-tests-20261022T0255.log`; core GoogleTest retains its
separate locale failure, skips and disabled cases.

## Executed results

| Check | Retained evidence | Outcome and boundary |
| --- | --- | --- |
| Selected original weapon queries | `20261022T005240Z-phase1-weapon-query-7c384246`, candidate `58c2995e` | All **22 original cases match**, six MAINHAND/OFFHAND/BOTH queries per case. Execution and evidence validation pass. Collected state/cache snapshots show no query-caused mutations; this library-initialized test has no running loop, ticks or save. |
| Before-fix item replacement | Baseline `20261022T005759Z-inventory-journey-a65af39d`; candidate `58c2995e` `20261022T005908Z-inventory-journey-d17608a1` | Both complete ten stages and retain three stale-cache transitions: same-animation CreateItem to +1, parsed TransformItem to +1, and reverse CreateItem to normal. Physical inventory changes while cached offhand item/enchantment remains stale. `cache-mismatch-observed` is a failing diagnostic result. |
| Cache-fix regression | Candidate `9aa69cd5`, `20261022T013442Z-inventory-journey-c1d6376f` | Ten stages complete with `journey-observed-cache-coherent`, no cache mismatches, no collected query mutations and no unstable repeated values. Candidate and protected Phase 0 inventories match before/after. This establishes the reproduced offhand fix, not every selected weapon/ammo/launcher/magic-slot replacement or original mutation-journey equivalence. |
| Menu/render traversal, 1024×768 | `20261022T010029Z-menu-run-bf0932e2/1024x768`, candidate `58c2995e` | Completed 124 steps / 67 captures, exit 1, **19 failed checks**. Seventeen Stats outcomes trace to callback argument handling; two mage-book outcomes trace to bypassing ordinary initialization in the harness. Dark inventory/record summaries are an additional visible production defect. The stage did not time out. |
| Menu/render traversal, 1280×960 | Same run, `1280x960` | **Timed out at 330 seconds**, 85/124 steps retained, no host completion result. Owned cleanup and private-game guards pass. The stage remains incomplete. |
| Candidate core suite | `runtime-candidate-58c2995e/phase0-local/results/20261021-175716-phase1-after-core-ee7ba7f1` | 227 passed, **one failed** (`StringTest.StringToUpper`, retained locale issue), nine skipped and six disabled; process exit 1. The suite is not green. |
| Candidate vanilla import/reload | Same runtime, `20261022T011356Z-phase1-after-vanilla-3eb08216` | All **24 assertions pass**; import, two reloads and repeat import exit 0. Persistence verdict remains `differences`: cycle 1 has two normalized differences, cycle 2 zero; repeat import has 26 current-area differences. Original fixture and copied input are unchanged. |
| Candidate ordinary GUI/save/reload | Same runtime, `20261022T011625Z-phase1-after-gui-bc2007a5` | All **20 assertions pass** (13 save, seven reload), processes exit 0. Persistence remains `differences`: party 180, stored NPCs zero, world metadata three, current area 268. Fixture and created-save hashes remain unchanged on reload. Callback/content success does not certify rendered UI or full save fidelity. |

The 24+20 native assertions are separate from core GoogleTest counts, Python tooling tests and menu traversal checks. Passing those 44 assertions does not erase persistence differences or the menu failures.

## Provenance and interpretation

The public [weapon query summary](../compatibility/evidence/phase1-weapon-query-lab.json) pins the preparation, independent original review, case receipts, before/after result/inventory hashes and native core. Both summarized result hashes were checked against the retained private files in this audit. Its candidate core is `4e64873cab7c872cbb5b2d626cb7f494fae1955e39f594cfedd87bdea0a96724`. The summary explicitly records `calling_thread_rng_observed: false` and `complete_combat_or_campaign_acceptance: false`. No hidden RNG purity or complete combat contract follows from the collected equality observations.

The cache-fix result SHA256 is `349523302076878810ae40b936d13b9c7a32505882a34b58abebaef1933a10be`. Its scope still records hidden state and original journey parity as unproven. The source correction refreshes initialized active weapon metadata after runtime item replacement; the three demonstrated stale transitions and their exact regression are documented in [cache invalidation](../compatibility/phase1-inventory-cache-invalidation.md). Earlier failed build, incomplete prefix and cache-mismatch receipts remain preserved.

The [menu defect report](phase1-menu-native-defects.md) separates production callback/color corrections from the external spellbook/close scenario correction. Source fixes are integrated, but the failed screenshots and timeout have not been relabelled as passes. A fresh bounded rerun is required to establish working controls, readable text, geometry and close behavior at both resolutions. Selected game font provider/face/size metadata does not by itself prove baseline/advance/overflow or original pixel fidelity.

## Remaining validation

The coordinator's 22-case comparison on candidate `9aa69cd5`, with the new noninitializing calling-thread RNG observer and failing draw control, is in progress at this checkpoint; no result is assigned here. The candidate `58c2995e` original-query match must not be silently transferred to a newer binary. Fresh paired normal-loop AI comparison, corrected menu captures, hotkey apply/cancel/default/conflict/dispatch/fresh-profile persistence journey, broader mutation paths, remaining save differences and campaign checkpoints remain distinct work. Plain-key hotkey support does not close modifier/function/international binding fidelity.

This documentation audit read integrated source/docs and retained JSON/log metadata only. It launched no tests, native hosts or game processes and changed no engine or runtime files. All result paths above are private under `C:/BGRedux/phase1-local/`; licensed game assets and screenshots are not included in this report.

## Candidate 9aa regression and isolation guard

The fresh candidate core run `20261021-184124-phase1-9aa-core-31d3c584`
has 229 passes, one retained locale failure, nine skips and six disabled tests.
Both new RNG snapshot tests execute and pass. Vanilla run
`20261022T014128Z-phase1-9aa-vanilla-68b7d20c` passes 24 assertions;
GUI run `20261022T014148Z-phase1-9aa-gui-59c92810` passes 20. Both retain
persistence `differences`. New inventory/record captures show readable summaries;
this alone does not accept every menu or original typography fidelity.

The broad runtime preservation receipt deliberately records `all_preserved: false`.
Its private-game preparation preceded the separate query/control runs, whose
library initialization still used the clean GamePath. The strict source guard
detects a changed `GemRB.log` and `gemrb_path.txt` timestamp; the exact delta is
retained in `runtime-candidate-9aa69cd5/clean-game-guard-failure.json`.
Candidate source/binaries, Phase 0 source/binaries/fixture and all 2,324 pinned
game assets pass their checks. The source-root guard failure is not waived.
The query hosts need private writable game roots and a fresh guarded rerun.

## Candidate 9aa query/RNG follow-up

The pending 22-case check above is now complete in `20261022T013614Z-phase1-weapon-query-af33ea1e`: execution and validation pass, all 22 selected original cases match, and all 1,100 observations (1,056 predicates plus 44 True/False controls) retain collected actor/cache state, stable repeated results and unchanged **calling-thread** RNG. Read-only review independently read every one of the 1,100 raw RNG before/after pairs: all were observed with the expected scope, and none changed initialization or serialized RNG state. The selected candidate core DLL is `79650612926d96a8748320bcf3d0f8f265f7d20747448a30a5ec8918b472ebb9`; result SHA256 is `10c440c1763c6eb6dc4bc50802acdf1e76a104e637effb00964e93e5b8023137`.

The separate deliberately failing draw control, `20261022T014027Z-phase1-weapon-query-02a6adef`, uses the same core, driver and candidate inventory. Its native process exits 0 and completes 14 observations, but validation and the top-level verdict remain **failed** with case verdict `calling-thread-rng-mutation`. At call 3, `WeaponEffectiveVs(Player2,MAINHAND)`, the requested external control performs a real RNG draw inside the measured interval. Raw serialized RNG state changes without an initialization change, while the raw actor and selected weapon-cache snapshot hashes remain identical. This establishes that actor/cache equality alone cannot detect that RNG consumption, and that this observer rejects the deliberate draw. It is not a query-caused RNG defect. Control result SHA256 is `aec050923a965c1cac08ed7ba55b3233de2787d41fbe2f575f293934b3353b7a`.

Both runs retain passing candidate and protected Phase 0 inventory guards. The new [public RNG summary](../compatibility/evidence/phase1-weapon-rng-lab.json) preserves exact result, driver, DLL and manifest identities without changing the earlier candidate58 summary. These are initialized-library observations with noninitializing state copies; other threads, hidden state, future scheduling, normal-loop combat, DPR, save fidelity and campaign coverage remain outside this result. No new process or test was launched for this review.
