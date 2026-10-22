# Phase 1 LAB validation status

Evidence checkpoint: October 22, 2026 UTC, after the completed candidate `9aa69cd5` inventory journey. Phase 1 engine work is authorized; the accepted Phase 0 source/build/results remain protected. This report updates the earlier first-batch pending descriptions. It does not declare Phase 1, all menus, combat or campaign fidelity complete.

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
