# Phase 1 implementation backlog

October 21, 2026. This is a dependency-ordered recommendation, not authorization to edit the engine. Phase 0 acceptance and a separate explicit implementation authorization precede every engine change below. The goal is faithful BG2EE; UI and compatibility defects may enter Phase 1 with reproducible cases instead of being fixed during the engine freeze.

Authority and invariants: [current handoff](../handoff/BG_REDUX_COMPLETE_CONTEXT.md), [contract decisions](../architecture/phase0-contract-decisions.md), [risk register](../risks/modernization-risk-register.md). Preserve the original reference and Classic behavior. Do not equate successful process execution with compatibility, reconstruct combat causes from English logs, or make both EE weapon predicates the same damage forecast.

Operational gate amendment: the user has explicitly removed VM recovery snapshots from acceptance and has confirmed guest/host input isolation. Preserve the latter as user-observed confirmation, without claiming an independently traced input test. This supersedes older snapshot prerequisites; it does not relax native preservation, evidence freshness, or compatibility checks.

## Dependency order

| ID / priority | Concrete problem and working slice | Depends on | Acceptance evidence |
|---|---|---|---|
| P1-01 / P0 | Preserve a repeatable baseline while making the first change. Carry forward exact game/toolchain/build/fixture identity, normal-loop and import/reload runs, required/optional test status and unchanged-input checks. | Phase 0 accepted; baseline runner independently rerun/reviewed; implementation authority | A fresh before/after report preserves locale failure/skips and known wire/color/equip differences, rejects missing required input and stale receipts, and identifies every changed engine file/binary. |
| P1-02 / P0 | Implement each missing EE weapon predicate against its own measured contract, using the existing dispatch path rather than changing combat resolution. | P1-01; expanded paired hand/weapon/ammo/defense and query-side-effect evidence | All positive/negative fixture guards pass; expected original Booleans match the characterized matrix; repeated queries leave resources/effects/RNG consumption unchanged within a defined observable scope. Imoen/default AI preferred/fallback decisions and actual action/target are rechecked. Unsupported semantics are explicit. |
| P1-03 / P0 | Restore usable inventory and record information through a semantic view model over existing actor operations; separate content assembly from font/scaling work. | P1-01; ADR-01/02/06; information inventory and ordinary-operation mapping | Each required attribute/combat/equipment/spell/protection value has a source and a visible, correctly labelled presentation. Name the secondary panel **Stats**, avoid duplicated attributes/combat values there, and target no scrolling. Compare runtime model and screenshots at agreed resolutions, clipping/focus/cursor paths and error states. Missing panels cannot pass because an internal string exists. No stash, balance or EE Lua interpreter dependency is implied. |
| P1-04 / P1 | Characterize and correct a specific save-import/runtime mismatch only after distinguishing representation from behavior. Keep original import and explicit identity/remapping boundaries. | P1-01; ADR-02/05; original behavior evidence for the chosen mismatch | Reproduction demonstrates the selected divergence, the narrow correction, ordinary and library load/save behavior, repeated fresh reloads, item/effect/world conservation and negative-version/content handling. Do not deduplicate IMMCLOUD globally: accumulation alone is shared with the original reference. |
| P1-05 / P1 | Add the smallest observation seam required for an actual compatibility correction: explicit readiness, command outcome or an enforced causal branch. | P1-01; ADR-01/02/03/06; one concrete consumer and non-interference fixture | Actual branch/outcome is observed with stable run/target identity; sink off/on has no unexplained state/order/RNG difference; deletion/load/cancel cases are safe; bounds and measured cost are recorded. MR diagnostics, if selected, retain sequencer and save-for-half distinctions and do not expose raw data to players. |
| P1-06 / P1 | Validate representative ordinary gameplay journeys and fix the narrow blockers found. Cover dialogue/cutscene, transitions, loot/container/store, equip/quick bindings, spell/effect/AI and save/reload paths. | P1-02/03 plus relevant P1-04/05 fixes; golden scenario specification | Each journey has declared start/end state, normal user operations, preserved fixture/assets, observed world/quest/inventory effects, save checkpoint and reference disposition. A query-only synthetic case is not an ordinary gameplay journey. Failures produce reproducible defect records. |
| P1-07 / P1 | Establish campaign progression checkpoints and a faithful playable release candidate. | P1-06; compatibility matrix; reproducible build/package instructions | Repeatable progression through declared BG2EE campaign checkpoints with recorded quests/scripts/areas/encounters/save recovery; independent rerun/review; remaining defects explicitly scoped and prioritized. Opening-area success cannot satisfy this gate. |

P1-02 and P1-03 may proceed in isolated worktrees once their independent prerequisites are satisfied. Integration, resource installation and native/GUI session control remain serialized. P1-04 is selected from demonstrated mismatches; it is not a blanket serializer rewrite. P1-05 is the smallest needed seam, not a required general event bus before every compatibility fix.

## Required defect record

Before changing an EE GUI or conversation path, consult the
[upstream EE issue and discussion index](../compatibility/upstream-ee-gui-issue-context.md)
and [dialogue context](../compatibility/upstream-dialogue-issue-context.md).
The October 22 snapshot catalogs all 55 `game: ees` issues and their 132 comments,
plus four related dialogue issues. Compare relevant upstream fixes with the pinned
source and obtain a local reproduction; an upstream open/closed state does not
replace native acceptance evidence. Known spellbook operations, input/modal,
font/encoding/scaling and quick save/load gaps should inform P1-03/P1-06 fixtures.

Each candidate carries: user-visible trigger and expected/observed behavior; exact input/build/content hashes; paired original/GemRB evidence where relevant; raw output location; invalid-setup and unsupported-content controls; source-grounded root-cause candidates; uncertainty and affected scope; smallest proposed change; normal-path and negative regression scenarios; rollback/profile implications; and the authority required to execute it. A mismatch that is only source-inferred remains a hypothesis until reproduced.

## Carry-forward findings

- `WeaponEffectiveVs` and `WeaponCanDamage` are current [stubs](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GameScript/Triggers.cpp#L4740). Existing equipped evidence distinguishes protection from magical weapons (`0/1` for the +1 sword) from 100% slashing resistance (`1/0` for the normal sword); all-zero GemRB results do not establish a defense contract. [Current investigation](../testing/equipped-defenses-and-ai-fallback.md).
- Inventory/record assembly is incomplete; font variants alter metrics/pixels without restoring the missing information. A modern UI is approved, but replacing the renderer or enabling future storage semantics is not a prerequisite to displaying correct information. [Presentation evidence](../testing/gui-save-and-presentation-results.md).
- Wire HP/item flags, repeat-import NPC colors, legacy time/variable representation and equipped-effect growth are separate observations. LAB import/reload assertions and normal GUI callbacks pass while overall persistence still reports differences. Full save fidelity remains open. [Persistence report](../testing/save-import-and-harness-results.md).
- Native isolated AI tails execute an attack fallback; this does not establish whole-script target selection, damage parity, completion of a save action or campaign behavior. Original combat observation must be independent of save admission. [AI limits](../testing/equipped-defenses-and-ai-fallback.md).
- Fresh LAB characterization extends this: all four original nonce-tagged live captures show response entry plus combat feedback without requiring saves. Paired native inputs/scripts match; original stock branches 115/307 differ from native fallback 118/310, while controls agree at 115/307. Original queue completion, exact target/action memory and DPR remain unproven. Private runs: `20261021T230944Z-original-live-6efa5f54` and `20261021T232434Z-paired-ai-live-1437dd9a`.
- The eight-case side-effect run `20261021T232241Z-query-side-effects-74613e6e` observes 144 evaluator calls (128 weapon predicates plus 16 controls) without collected-state mutation. Hidden RNG/caches/action queues and original query side effects are unobserved. This constrains regression tests for P1-02 but cannot certify the future implementation's non-interference.
- Historical core tests include a locale failure, required-fixture/comparator skips and disabled cases; 71 external harness tests are a different suite. Do not erase those distinctions when integrating the first change. [Executed baseline](../testing/phase0-executed-baseline.md).

## Deliberately later decisions

Navigation Redux requires measured delivered attacks/timing as well as arrival; combat event foundations and controlled RNG/clock observation belong to the staged instrumentation work. Party Stash is always available in the approved future design, with no Combat Pack/combat lock; legacy ownership, capacity progression and overflow need their own transaction/migration decision before implementation. Combat Info must filter authoritative events through earned player knowledge. SCS/Ascension use a pinned later installation, not a universal-mod promise. Multiplayer, rules changes, renderer replacement and human-led visual restoration remain separate workstreams and approvals.


## October 22 spellbook follow-up

The [heading repair](../testing/phase1-ee-spellbook-heading-repair.md) now passes
both menu resolutions and actual depleted-slot updates. Explicit direct-removal
stock and private nonidentity-name journeys pass GUI save/fresh reload on the
coherent new candidate; compatibility differences from the fresh baseline stay
unwaived. This completes a bounded ordinary spellbook slice, not P1-03/P1-06.

Next concrete fidelity work is the
[information/selection assembly gap](../testing/phase1-spellbook-information-layout-gap.md):
persistent localized spell names, help/description content, information-only
name selection and a separately gated Memorize action, while retaining the
original's icon shortcut. A source-inferred info-to-Erase displayed/original
index risk requires its own controlled native reproduction before correction.
Do not infer erase coverage from successful known-icon Memorize tests.
