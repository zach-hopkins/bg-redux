# Redux project context and UI direction

Recorded October 20, 2026 during Phase 0. **Current user decision: build a modern UI preserving BG2EE's information and gameplay functions, closely inspired by Infinity UI++ and existing Inventory Redux work.** Pixel-identical Enhanced Edition screens and executing its Lua UI implementation are not acceptance requirements. Usable, complete information, faithful underlying game behavior and the original artistic character remain requirements.

The [engine charter](../charter/BG_REDUX_CODEX_PROJECT_CHARTER.md) and current conversation govern this audit. Other project chats/specifications provide design context. Their older implementation instructions, EEex offsets, test counts and launch procedures do not authorize new engine work here and are not GemRB validation results.

## Context reviewed

Recent relevant exchanges were read from the inventory, Combat Info, movement, buff-preset, visual-remaster and reconstruction-estimate project conversations. This was targeted familiarization, not a claim to have read every historical tool output. Preserved specifications and latest amended playtest notes were checked where they explain current intent:

| Workstream | Existing context | Foundation implication for GemRB |
|---|---|---|
| Inventory Redux | [Current project summary](../../inventory/README.md), [original manifesto](../../reference/inventory-redux/Inventory_Redux_Codex_Manifesto_and_Wireframe.md), [designer brief](../Inventory_Redux_GUI_Designer_Brief.md), [latest playtest guide](../../inventory/design/PLAYTEST_GUIDE.md) | Separate storage/ownership, equipped state, quick bindings, cursor transactions, query/view model and previews. Reuse product behavior and conservation tests; avoid porting original-executable memory hooks |
| Combat Info Redux | Conversation intent and [discovered-defense state policy](../../combat/research/DISCOVERED_DEFENSE_STATE_POLICY.md) | Authoritative causal observations, learned facts, temporary-state lifecycle and player-visible filtering are different concerns. The diagnostic oracle may see hidden state; player UI must reveal only earned knowledge |
| Pathfinding Redux | Movement conversation, including ordinary-movement/haste ambiguity and dependency-version support failures | Keep route planning, movement execution, animation speed and combat approach separate. Capability/version diagnostics and actual speed traces avoid confusing a dependency failure or visual stop with changed haste mechanics |
| Buff/preset work | Recipient-first planning, concurrent independent casters, explicit shared-item dependencies, simple duration sorting and mixed execution | Command queues need acknowledgements and observable timing; dependencies should express actual shared resources. Duration compression is an explicitly designed gameplay option, not a baseline engine refactor |
| Multiplayer / Independent Interaction / Tactical Time | [Manager summary](../manager-summary.md), [interaction policy](../interaction-policy.md), [time defaults](../tactical-time-defaults-2026-10-09.md) | Future authority, session/load epochs, per-player intent, script continuations and simulation-time accounting matter. Existing two-PC EEex results do not prove GemRB multiplayer. Defer network-model choice while preserving explicit authoritative mutation boundaries |
| Visual modernization | Earlier remaster discussion and current charter | Preserve authored map proportions/world composition and classic compatibility; treat UI scaling, high-resolution assets and world-coordinate changes separately. No renderer replacement or art conversion is justified by the present font failures |

Conversation IDs reviewed: `01a11a16-2dd2-7ae2-8ae1-5b9ddde8206e`, `01a11c25-a57d-7380-883c-eb97795ff103`, `01a0e244-e05a-7532-b953-aac814bbb5ce`, `01a1563b-060f-7391-8956-f12b427021a7`, `01a140f4-8e5c-7f83-a5b8-e462020d087a`, `01a13924-6759-75c1-be51-01dbec5ad10a`. No messages were sent and those projects were not modified.

## Resolve older inventory contradictions explicitly

Later user amendments supersede the preserved original manifesto: **Party Stash always available; no Combat Pack; no threat/danger lock**. Equipment and three quick weapons/ammo/items remain distinct from stash. The current playtest calls the secondary panel **Stats**, excludes repeated attributes/combat values there and targets no scrolling. This supersedes the older designer brief's “Full Stats” wording/scrolling allowance. Accurate hypothetical equipment previews remain future work; existing actual stats are not a hypothetical preview.

These are long-term feature requirements, not changes to enable in the Phase 0 Classic baseline. Shared storage still needs a documented legacy ownership policy for actor-specific quest/item checks. Class/slot changes and always-available stash are intentional future gameplay/usability choices, not automatic consequences of replacing a UI.

## Infinity UI++: reference, not assumed portability

The primary [InfinityUI repository](https://github.com/Renegade0/InfinityUI) describes an EE UI overhaul. Its [showcase](https://github.com/Renegade0/InfinityUI/issues/39) illustrates inventory/bags, stores, spell selection, character information and dialogue. These are useful interaction and composition references; the showcase is not a GemRB implementation contract. Upstream [GemRB UI discussion](https://github.com/gemrb/gemrb/issues/2535) and local GUIINV source expose the classic CHU/Python versus EE menu assembly gap.

Recommended direction: a **native semantic UI/view-model layer over narrow engine operations**, with theme/layout/art separated from item transactions and rule resolution. First prove one inventory/record view on existing rendering/input primitives and measure layout/font adequacy. Retain useful CHU loaders as compatibility adapters. Do not select a browser stack, wholesale GUI toolkit rewrite or EE Lua interpreter merely because a modern layout is desired.

Before choosing whether to retain or replace particular controls/layout infrastructure, measure Unicode glyph coverage, font metrics, scaling at the 720p floor and 1080p/1440p/4K, clipping, keyboard focus, cursor/drag semantics, event lifetime, accessibility and agent traversal. Missing labels are a current correctness failure; polishing borders is later work.

## Decisions carried into the roadmap

1. Preserve authored content/rules through explicit legacy adapters; provide freedom behind those boundaries.
2. Make normal user operations queryable and commandable for the [AI-first harness](../testing/ai-first-harness.md), with renderer/input checks remaining independent evidence.
3. Keep item conservation, ownership, actual/preview state and transaction acknowledgement explicit. UI success must follow authoritative success.
4. Keep omniscient test traces separate from player-earned combat knowledge.
5. Use native engine seams to avoid repeating the original-executable hook/clone-lifetime complexity, while still proving RNG/effect/lifetime non-interference for previews.
6. Maintain an unchanged compatibility reference while optional Redux mechanics are developed later. No previous mod feature or test result closes a GemRB compatibility gate.
