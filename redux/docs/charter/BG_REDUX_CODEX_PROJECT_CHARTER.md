# BG Redux — Engineering Charter & Codex Development Context

> **Document type:** Living project charter and coding-agent instructions  
> **Status:** Design direction, not a claim that implementation is complete  
> **Baseline date:** October 2026  
> **Primary target:** Baldur's Gate II: Enhanced Edition (BG2EE), then curated mods and the broader saga  
> **Preferred starting foundation:** Audit and potentially fork GemRB; do not pre-commit to preserving its internals  
> **Intended audience:** Codex and other AI coding agents working in this repository

## 0. Read this first — the actual product

**BG Redux is not a new Baldur's Gate-like RPG.** It is an effort to play the *existing* Baldur's Gate games through a modern, fully controllable Infinity Engine-compatible runtime, with an increasingly polished collection of optional or curated improvements.

Preserve the original games' authored content, party identity, combat feel, extraordinary abilities, and painterly visual presentation. Replace technical limitations and unnecessary management friction. Add new gameplay design only deliberately, after observing the effects of lower-level changes.

> **Project mission:** Preserve the game. Modernize the engine. Refine the experience.
>
> **Engineering rule:** Compatibility at the boundary; freedom behind the boundary.
>
> **Gameplay rule:** Remove chores, preserve meaningful choices.
>
> **Balance rule:** Change foundations before dependent mechanics, and measure consequences before compensating.

Do **not** interpret this as authorization to rewrite Baldur's Gate's rules, overhaul encounters, generate replacement artwork, or rebuild GemRB wholesale. **The first success condition is a working, trustworthy, testable runtime of the original game.**

---

## 1. How Codex should use this document

1. Treat this document as a **design charter and decision history**. Repository source, actual test results, and current upstream documentation are the authority for implementation facts. Do not pretend an architectural boundary already exists because it is proposed here.
2. **Before changing code**, identify whether the requested work is compatibility, engine correctness, presentation/interaction, rules, AI, balance, or experimental work. State expected effects and dependencies.
3. Favor **small, reversible, tested changes** over broad speculative refactors. Keep the game playable throughout modernization.
4. Preserve **the original game's behavior as the reference** unless a change is explicitly approved. A behavior-preserving engine refactor may still affect realized combat effectiveness; measure it.
5. Identify *unknowns* explicitly. When upstream capabilities, file semantics, save details, hooks, plugin APIs, or EE behavior are uncertain, inspect actual source and run a proof-of-concept. **Do not invent API names, compatibility claims, or test results.**
6. Differentiate **decided design**, **proposed direction**, and **unresolved questions**. Never silently promote an exploratory idea to a product requirement.
7. Favor deterministic or reproducible test fixtures, structured diagnostic events, repeatable builds, and documentation that allows other agents to work independently.
8. Do not optimize around universal mod support before establishing a **curated verified compatibility baseline**. Treat **Architecture & Extensibility** (§6) as its own workstream with evidence-based subsystem acceptance reviews, not an excuse for speculative rewrites.
9. Keep code licensing and game-asset rights in mind: GemRB is GPL-licensed; a derivative engine has corresponding obligations. Do not bundle or redistribute copyrighted game assets without authorization. Flag legal questions for human review rather than giving legal guarantees.
10. If a proposed improvement conflicts with the original feel, surface the conflict and test it. **Mathematically cleaner is not automatically more enjoyable.**

### Suggested agent workflow for each task

- **Locate:** Trace actual code paths, state ownership, file formats, and caller dependencies.
- **Classify:** Does the change preserve rules but alter execution, or intentionally alter rules?
- **Specify:** Provide before/after observable behavior, invariants, and failure cases.
- **Assess:** Identify upstream and downstream gameplay dependencies, mod assumptions, and save compatibility.
- **Implement:** Minimal isolatable change, feature-gated or behind a rules profile when appropriate.
- **Verify:** Unit tests, scenario tests, save/load tests, comparisons against baseline and representative modded cases.
- **Report:** Exact changes, measured behavior differences, test results, remaining uncertainty, and recommendations.

Suggested PR/change report headings: `Goal`, `Actual architecture discovered`, `Behavior changed / unchanged`, `Risk & downstream effects`, `Validation`, `Known limitations`, `Next decision`.

---

## 2. Product boundaries and what must survive

### This project **is**

- A modernized **engine/runtime for the existing Baldur's Gate games**, initially derived from and evaluated against GemRB.
- An interpretation layer for IE/EE resources: areas, actors, items, spells, dialogue, scripts, world state, quests, and cinematics as supported.
- A way to make deep engine changes without continued reliance on invasive patches to Beamdog's executable.
- A curated player experience with modern UI, navigation, usability, instrumentation, and eventually visual upgrades and optional balance revisions.
- A foundation where original content remains playable in a **Classic/reference rules profile**.

### This project **is not**

- A ground-up original RPG, a conversion to D&D 5E, or an excuse to standardize every unusual BG mechanic.
- A commitment to rewriting the whole engine in Rust. Existing C++ is acceptable; consider replacement subsystems only with a demonstrated advantage.
- A commitment to preserving GemRB's internal data structures indefinitely.
- A promise of drop-in compatibility with all BG mods, EEex binary hooks, EE GUI Lua, or arbitrary EET installations.
- A promise of perfect round-trip saves to unmodified BG2EE.
- A mandate to replace legacy artwork with AI-generated images. Human-authored artwork and original artistic composition are explicit priorities.
- A requirement to implement multiplayer, new combat systems, or an HD remaster before the original campaign runs reliably.

### The feel to preserve

- **Continuous autonomous real-time-with-pause combat**: six characters fight simultaneously and keep expressing their builds without constant orders.
- **Low-input, high-complexity actions**: click a target; intricate stats, timing, items, and abilities resolve underneath.
- **Decisive consequences**: fast kills, interruptions, dangerous spells, audible/visual hit feedback, meaningful deaths.
- **Transformative progression**: characters sometimes outgrow enemies; do not scale all encounters to identical difficulty.
- **Strange, powerful, expressive systemic interactions**: do not flatten unusual spells and equipment merely for symmetry.
- **World-first art direction**: locations are authored as believable, distinctive places where combat happens—not standardized arenas decorated as locations.

---

## 3. Product structure: related but independently deliverable layers

```text
User-owned BG/BG2/BG2EE game data + supported installed mods
                          |
         Legacy resource and behavior adapters
                          |
        BG Redux engine/runtime (GemRB-derived)
          |             |               |
      Simulation     Scripting         Persistence
      / combat       / quests          / saves
          |             |               |
       Navigation | Inventory | Structured events | UI contracts
                          |
        Presentation / modern asset pipeline
          |                               |
     Faithful classic mode          Enhanced visual mode
                          |
           Curated BG Redux launcher/build recipes
```

The diagram is a **target separation of concerns**, *not* a claim about GemRB's current modules.

**Engine track:** Compatibility, source-level control, rendering infrastructure, stable APIs, tooling.

**Gameplay track:** Native Pathfinding Redux, Inventory Redux, Combat Info Redux, action bar improvements, and future optional combat experiments.

**Visual track:** Faithful classic rendering first; enhanced formats and carefully authored restoration later.

**Distribution/build track:** User supplies legally obtained game data; verified, pinned supported mod compositions; reproducible builds and drift detection.

**Multiplayer track:** Future goal (Tactical Time and Independent Interaction), with early architectural awareness but no premature rewrite in its name.

---

## 4. Order of operations — the onion model

This order is the most important long-term constraint on balancing and redesign.

| Layer | Name | Authorized focus | Exit condition |
|---|---|---|---|
| **0** | **Compatibility and observation** | Play original content, baseline mechanics, test fixtures, telemetry | Representative encounters produce known, explainable behavior |
| **1** | **Engine correctness** | Fix broken movement, scheduling defects, save hazards, pathological edge cases | Corrections are stable; unintended changes measured |
| **2** | **Presentation and interaction** | UI, targeting, search, feedback, accessibility, rendering | Usability improves; rules deviations explicitly accounted for |
| **3** | **Fundamental combat rules** | Attack resolution, AC/THAC0, action timing/APR, defenses, damage | Explicitly selected foundations with coherent tests |
| **4** | **Classes, spells, and equipment** | Rebalance individual abilities against the selected foundations | Distinctive builds and counters work under revised rules |
| **5** | **AI, encounters, and difficulty** | SCS adaptation, boss composition, difficulty curves | Encounters tuned for mechanics that are no longer moving |

**This is a dependency hierarchy, not a ban on exploration.** Isolated combat sandboxes can investigate layer-3/4/5 ideas early, but they must not silently enter the main compatibility branch.

### Two complementary tracks

- **Stable track:** Faithful, playable engine modernization; versioned compatibility baseline and regression tests.
- **Experimental track:** Sandboxed alternative rules, targeted encounter redesigns, combat-feel prototypes. Results are evaluated; only deliberately accepted changes enter the stable track.

### Foundational versus dependent changes

Example: SCS mages appear to overuse Stoneskin. **Do not immediately nerf Stoneskin.** First consider attack hit rates, realized melee APR, collision/pathfinding, interruption rules, how SCS evaluates threat, and spell timing. A THAC0 or movement change may alter Stoneskin's practical value even if its resource definition is untouched.

**Impact scope is the ordering heuristic.** A new hit/armor model impacts nearly every creature, item, and on-hit effect; changing one spell is narrower. Decide the global model first, tune the spell afterward.

### Rules-preserving ≠ balance-neutral

For example, better allied pathfinding may increase delivered attacks per round without changing the APR formula. Record that as a real balance impact, even if rules remain identical.

### AI rules

- **AI compatibility early; AI optimization/balance late.** Existing SCS scripts must execute and behave competently enough for comparison.
- For any fundamental rules experiment, use an *adapted-opponent test* alongside mechanical correctness tests; don't declare a new ability overpowered solely because old AI doesn't understand it.
- Never perform final encounter tuning against an unstable underlying combat model.

---

## 5. Balance profiles and regression discipline

Maintain explicit, versioned profiles where practical:

| Profile | Purpose | Constraints |
|---|---|---|
| **Classic Rules** | Enduring reference | Reproduce original BG2EE rules except documented fixes; preferred for parity testing |
| **Redux Foundations** | Controlled systemic experiments | Alternate timing, engagement, interrupts, defenses, etc.; no implied encounter rebalancing |
| **Redux Balanced** | Possible future curated experience | Class/item/spell/AI/encounter adjustments made *after* foundations settle |

Avoid assuming all profiles can be swapped mid-save. New state, effects, and progression may require explicit migrations or separate saves.

### Tests and measurements worth adding

**Mechanics:** hit/miss/critical rates, realized APR, cast timings, interruptions, saves/MR, dispels, effect timing, stacking, spell-protection removal, weapon enchantment thresholds, action ordering.

**Execution:** time unable to attack, blocked pursuit, doorway passage, ally/enemy pathing, target death during an order, charm/allegiance transitions, pauses mid-cast, quickload mid-effect.

**Encounter outcomes:** time to kill, damage contribution, spell success/failure causes, attacks absorbed by Stoneskin, time PfMW blocks weapons, resource consumption, party deaths, AI choices.

**Experience:** does an easy fight still feel satisfying? Are outcomes understandable? Does the player get to enjoy autonomous characters? Are difficult fights demanding through decisions rather than bugs?

Vary fixtures across early BG1, mid-BG2, endgame BG2, and Throne of Bhaal once those campaigns are supported; include solo and full-party cases, unmodded and selected SCS/Ascension scenarios. No benchmark is meaningful without recorded game build, difficulty, mods, random seed (where relevant), and rules profile.

### Balance change review template

```markdown
## Proposed rule change
Problem observed:
Evidence / reproduction:
Alternative root causes:
Upstream dependencies:
Downstream dependencies:
Original behavior:
Proposed behavior:
AI/SCS assumptions affected:
Mechanics tests:
Encounter and feel tests:
Rollback / profile strategy:
Decision: experimental / accepted / deferred / rejected
```

Do not approve a global rewrite of THAC0, six-second rounds, spell protections, or damage merely because a modern system looks more intuitive. First identify the experienced problem and test a narrower solution.

---

## 6. Engine architecture: preserve compatibility, permit replacement

### First engineering question: how much of GemRB do we truly need?

Inspect actual upstream code and current support before making changes. In particular investigate the actor model, effect queue and opcode processing, action scheduling, scripts, render interfaces, inventory semantics, save serialization, and currently supported EE resources. GemRB plugin architecture **does not** imply every major combat subsystem is hot-swappable. Document specific coupling with call graphs, state ownership, and tests.

### Proposed architectural contracts

- **Legacy resource adapter:** Loads supported original ARE/WED/TIS/MOS/BAM, CRE, ITM, SPL, BCS, DLG, 2DA, TLK, and other formats into canonical runtime representations. This is a proposed responsibility boundary; specific support requires verification.
- **Legacy behavior adapter:** Preserves trigger/action semantics expected by old scripts, including item and actor ownership expectations; translates legacy requests into modern runtime commands.
- **Authoritative simulation:** Owns actor state, timing, actions, navigation intent, combat resolution, inventory transactions, world variables, and effect lifetimes.
- **Structured event bus:** Emits causal events from the *actual resolution branch*, not reconstructed English combat-log text. Includes visibility/knowledge and provenance metadata where justified.
- **Presentation API:** Receives visual state and events; implements animation cadence, sprite placement, occlusion, effects, UI and audio without dictating combat rules.
- **Versioned persistence:** Preserve legacy import where practical. Allow additional Redux-specific save state instead of forcing all new mechanics into old binary save layouts.

### Architecture & Extensibility — a formal project workstream

**Mission:** Transform the GemRB-derived foundation into a sensible, maintainable, modifiable BG runtime. Source availability alone is insufficient: normal changes should not require unrelated engine surgery, and non-native modders must have supported ways to extend the game. This is a first-class workstream alongside compatibility, **not** a mandate to rewrite the engine before the game runs.

> **Acceptance principle:** Preserve original BG data and semantics where needed, preserve observable game behavior as an initial baseline, but do **not** assume GemRB's internal organization or old asset formats are the correct permanent standard.
>
> **Review question:** Does accepting this implementation make the *next related modification* easier or harder?

#### Specific existing GemRB areas to challenge before accepting

The following are **audit candidates and design questions, not verified current defects**. Source locations, responsibilities, plugin boundaries and implementation size must be checked against the pinned upstream revision. GemRB's plugin support does **not** imply every core system is replaceable through plugins.

| Current area | What to question in actual source | Potential modernization direction |
| --- | --- | --- |
| `Interface` | Is the central engine object responsible for too much? Does orchestration also own unrelated mutable state? | Separate orchestration from clear subsystem state ownership and narrow interfaces. |
| `Actor` | Are stats, combat, effects, inventory and rendering/presentation overly coupled? How many callers reach into its internals? | Introduce explicit actor-state, combat, inventory, effects and presentation boundaries where the code justifies them. |
| `GameScript` | Can legacy BCS triggers/actions interact through stable, testable game operations rather than reaching into implementation details? | Preserve script semantics through a compatibility service and introduce a separate, documented modern scripting API. |
| `GUIScript` | Does the Python GUI model permit independently composable mods, or require whole-screen overrides and fragile bindings? | UI component registration, layout extension points and versioned scripted interfaces; preserve old GUI behavior as needed. |
| Effect/opcode system | Can new effects be defined without treating historic numeric opcodes and special cases as the only extensibility mechanism? | Unified effect definitions/registry and resolution contracts, with legacy opcode adapters. |
| Resource managers | Can modern imagery, animations, metadata and other assets coexist with original BAM/MOS/TIS/etc. without forced lossy conversions? | Canonical runtime asset interfaces with multiple format providers and explicit compatibility adapters. |
| Main loop/time | Are simulation time, visual frames, RNG, action order and in-flight actions independently controllable and testable? | Explicit simulation clock and ordered update phases; evaluate deterministic fixtures before promising deterministic runtime. |
| Save/load | Do original binary layouts constrain new persistent state or require hidden state duplication? | Versioned Redux state and migrations, with import/compatibility support as needed. |
| Plugin manager | Can extensions declare versions, dependencies, capabilities and conflicts, and survive lifecycle changes safely? | Versioned plugin manifests, defined lifecycle hooks, validation and conflict diagnostics. |

**Scrutinize `Actor` and `Interface` early**, because broad responsibilities are likely to create downstream coupling. Do **not** diagnose architecture from source-file length alone. Earlier discussions noted an approximately 12,000-line `Actor.cpp`, but Codex must measure the *pinned current revision* rather than repeat that number as a fresh fact. A big stable class may be preferable to many small classes coupled through hidden shared state. The **decisive evidence** is actual dependency tracing and a proof-of-change: how many unrelated files and systems must change safely to add one isolated feature?

#### Required subsystem acceptance review

For each major area, document:

1. **State ownership:** Who owns the authoritative state? Who can mutate it, and through what operations?
2. **Coupling:** What are the direct and indirect dependencies? Which unrelated systems must change for a narrow feature?
3. **Extension surface:** Can an external module customize it through a documented API, data file, or script rather than recompiling the engine?
4. **Legacy semantics:** Which resource, script, save and mod assumptions are observable compatibility contracts?
5. **Observability:** Can actual causes and outcomes be inspected through structured diagnostics rather than parsing log text?
6. **Testability:** Can behavior run in isolation or headlessly? Are golden scenarios and regression fixtures possible?
7. **Content-format flexibility:** Can modern assets or rules be added without masquerading as legacy formats?
8. **Persistence and identity:** Are stable IDs, runtime handles, object lifetimes, migrations and in-flight operations handled explicitly?
9. **Performance:** Can it be profiled and optimized without undermining extension contracts?
10. **Agent maintainability:** Could a coding agent make a bounded change with source documentation and tests, without understanding the whole engine?

The review must end with **one explicit disposition**:

- **Retain** — adequate and well bounded for the actual goals.
- **Wrap** — keep implementation, protect it behind a clear interface/adapter.
- **Refactor** — preserve useful behavior but reshape responsibilities or state ownership.
- **Replace** — only when evidence shows the architecture blocks a necessary goal and incremental refactoring would be worse.

Every disposition requires **source evidence, tradeoffs, compatibility cost, regression plan, and a small proof-of-change** when feasible. Never automatically choose Replace because code is old, C++, long, or unfamiliar.

#### Extensibility tiers and compatibility boundaries

Provide three *conceptual* extension tiers, expanding them only in response to real features:

- **Data-level:** Original IE resources and supported WeiDU-modified content; eventually clear declarative definitions and semantic patching for items, spells, creatures and other content.
- **Script/UI-level:** Documented, versioned access to structured events, queries, commands, UI components, filters and behaviors. A UI++-style change should not require replacing an entire screen when the change is local.
- **Native/system-level:** Carefully bounded modules for navigation algorithms, rendering backends, simulation and other deep changes; not the default requirement for ordinary mods.

Avoid arbitrary external code mutating internal state. Prefer **validated operations → authoritative state → structured events**. Plugin hooks need defined ordering, lifetimes, failure modes and permissions where applicable. Composition is a goal, not a promise that logically contradictory mods can coexist. Detect and explain conflicts rather than hiding them.

For legacy BG content, keep compatibility at deliberate adapter boundaries. A script requesting an item from a particular character must receive defined semantics even if Redux uses a shared stash; **do not** proliferate `if (redux_mode)` branches across unrelated modules. Original BG resources, scripts and modifications remain a supported input contract; modern internal representation and new extension APIs may evolve independently.

#### Prove architecture with real Redux features

Use the known initiatives as acceptance probes, **not** as justification to implement them before the baseline:

| Probe | Extension-quality acceptance question |
| --- | --- |
| Pathfinding Redux | Can traversal policy, obstacle collision, steering and attack positioning be changed independently while scripts still work? |
| Inventory Redux | Can an alternate storage/capacity model be implemented without modifying unrelated actor, AI, renderer and quest code? |
| Combat Info Redux | Can UI/mod listeners consume structured *causal* resolution events with correct visibility/knowledge scope? |
| UI customization | Can two unrelated inventory/character UI additions coexist without replacing a common monolithic screen? |
| Scripted effects | Can a new effect use a modern registration/resolution contract while existing numeric opcodes remain supported? |

**Don't build a speculative universal modding framework.** Implement a narrow extension contract when a real feature exposes the need; prove it with a second use case or explicit legacy boundary; then document and version it.

#### Architecture audit artifacts Codex must produce

- `docs/architecture/subsystem-acceptance-matrix.md`: each area above; Retain/Wrap/Refactor/Replace decision, source evidence, unknowns and reasoning.
- `docs/architecture/state-and-dependency-map.md`: authoritative state owners, mutations, actor/engine/core coupling, cross-system calls and diagrams.
- `docs/architecture/extensibility-contracts.md`: proposed compatibility adapters, modern extension tiers, API stability and event/command contracts; clearly label *proposed* versus *implemented*.
- `docs/architecture/proof-of-change.md`: one narrow real change showing which files were touched, why, test results and what it reveals about coupling.

**Stage gate:** No major subsystem redesign is accepted until this evidence exists. Audit findings can recommend *deferring* redesign. Do not let architecture work block all runnable compatibility improvements; sequence shared contracts alongside verified baseline work.

### Timing and future multiplayer

Audit current update loops, RNG ownership, action ordering, animation-linked game mutations, scripting frequency, serialization of in-flight actions, and time scaling. Prefer a clearly controlled simulation clock and reproducible tests. **Do not promise determinism or lockstep without proving it.** Server-authoritative multiplayer could be an alternative, with its own tradeoffs. Multiplayer is a later project but may affect how foundations are chosen.

### Rendering and asset pipeline

Legacy BAM palettes, area tiling, and sprite animation metadata are **inputs**, not the permanent runtime representation. In the future, support full-color assets and modern animation metadata directly, GPU texture caching/atlases/palette shaders where useful, more flexible effects/compositing, and high-resolution interfaces. **Audit the actual current renderer before replacing it**; benchmark rather than assuming an API upgrade alone increases performance.

Classic-mode rendering remains the fidelity reference. Enhanced mode is optional and art-directed. A new renderer cannot generate detail absent from original sprites or hidden geometry absent from fixed painted backgrounds. Human-authored restored art is a separate large effort from rendering engineering.

### Architectural flexibility over language preference

C++ is a valid high-performance core. Rust can be considered for bounded modules with clear ABI and ownership contracts, not as a mandate. A full rewrite solely to change languages is not approved. Prioritize correctness, stable boundaries, tests, and actual maintainability over novelty.

---

## 7. Compatibility and release strategy

**Initial target:** BG2EE unmodified. Validate its actual status against current GemRB sources and reproducible playthrough/test results; do not assume full parity.

**Next:** Curated BG2EE with SCS and Ascension. Distinguish content/resource-mod compatibility from EE-specific runtime features and binary extensions (e.g. EEex). Most EEex features will need new native implementations rather than transferred hooks. Extend toward BG1EE, Siege of Dragonspear, EET and other titles only after establishing a stable foundation.

**Verification matrix** should include:

- File/resource load and reference resolution.
- Area navigation/occlusion/transitions and environmental scripts.
- Dialogues, cutscenes, timers, world/global variables, quests.
- Combat formulas, effects, spell visuals, projectiles, summoning, AI scripts.
- Inventory/equipment/containers/merchant interfaces and scripted item transfer.
- Save/load/character export and content-specific edge cases.
- Curated mod install order, content hashes, upstream versions, and known incompatibilities.

**Do not advertise universal mod support.** Prefer pinned, verified builds, reproducible installation recipes, status checks, and a clearly identified `Custom / Unverified` path for advanced users. Keep compatibility failures explicit rather than silently altering content.

**Distribution:** Engine and tooling can be distributed subject to their licenses; original commercial game content must come from an authorized, user-owned source. Derived/remastered art and rights-holder permissions need separate review.

---

## 8. Known Redux designs — distinguish settled, proposed, and optional

### 8.1 Pathfinding Redux — established behavior target

**Design maxim:** *Traversal is permissive; spacing is intentional.*

The current EEex project prototypes ally pass-through, gentle post-movement separation, improved melee attack positions and optional enemy-allied pass-through. A GemRB-native rewrite should preserve behavioral lessons and fixtures, **not port hook addresses or assume identical internals**.

Validate player-controlled movement, AI pursuit, moving targets, haste/slow, doorways, summons, formations, allegiance transitions, save/load and scripted movement. Avoid improving melee positioning at the cost of making all narrow spaces trivial; record combat effectiveness changes.

### 8.2 Inventory Redux — latest explored direction (prototype, not final balance)

**Design:** One real shared Party Stash with meaningful *party-wide slot capacity*, no six separate backpack management screens. Starting capacity around **40 slots is a hypothesis**, not a fixed balance rule. Show current/remaining projected capacity while examining loot. Consolidate compatible stacks automatically. Standard loot remains selectable; deciding what to keep should matter.

**Progression:** Acquiring Bags of Holding and specialized containers should expand storage automatically without manually depositing items in bag windows. Explore general and category-specific capacity; do not assume exact container capacities until analyzed and playtested. Define nondestructive behavior for losing capacity (e.g. reversible over-capacity, block additional pickups; decision pending).

**Combat access:** Party Stash is locked during combat. Characters have **three personal Combat Pack slots** in addition to equipment, three Quick Weapons, three Ammo Slots and three Quick Items. Nearby eligible allied characters may transfer Combat Pack items; when both packs are full, user selects the recipient slot and an **atomic swap** occurs. Preserve locality and meaningful preparation without full personal backpacks. Do **not** insert a permanent combat-accessible shared overflow layer. No invented swap dialogs required; highlight destination slots and allow a second click. Charm/allegiance restrictions should be validated against intended rules. Combat Pack concept was reconsidered and accepted for further prototyping; **the exact three-slot count and lock-entry behavior still need testing**.

**UI:** Left character/equipment and compact quick slots; right unified searchable/sortable Party Stash with contextual details; equipment preview is state-driven. On item pickup show only changed derived stats, with expandable full stats. Item pickup uses native-feeling cursor semantics. Right click inspects; stack interaction conventions are left-click max, Shift+left half, Ctrl+left one, subject to capacity and stack limits. Do not force new modal dialogues for routine actions. Show APR decimals (e.g. `1.5`) rather than fractions, with optional explanation; lower THAC0/AC/saves is beneficial.

**Cautions:** Scripted items, quest checks for specific actor ownership, equipped items, item charges, containers, resurrection, charm, loot dropped during combat, capacity removal, merchant transactions, save migration, and interactions across legacy inventories may require a compatibility facade. UI design does not itself determine engine storage semantics.

### 8.3 Combat Info Redux — design principles and presentation

- **Mystery before evidence; clarity after evidence.**
- **Information follows resolution.**
- **Show outcomes where they happen. Show knowledge when requested. Keep the log authoritative.**
- **Observation should be rewarded, not repeatedly demanded.**
- **Known information can be remembered automatically; unknown information must be discovered.**

Produce authoritative cause-specific events: an effect stopped by Spell Trap, resisted by MR, saved against, blocked by enchantment threshold, suppressed by immunity, removed by a counter, or successful but with no applicable protections. Do not infer causes from translated combat-log strings. Resolve distinct components separately; never report speculative hypothetical blockers as actual causes.

Maintain an evidence-based knowledge layer by creature instance/archetype/family, with **fact-specific propagation**: inherit only genuinely guaranteed shared properties. Mods/SCS variants require conservative fallback. Distinguish currently observed, last-observed/uncertain, and explicitly confirmed removed effects. Do not reveal unobserved expirations, hidden recasts, intrinsic traits, or exact timers merely because the engine stores them.

Presentation: optional brief floating text for tactically consequential outcomes; detailed combat log; Shift-hover (or equivalent) inspect of observed defenses and earned knowledge; deeper explanation on demand. Avoid notification overload. Build causal instrumentation before the final UI.

### 8.4 Tactical Time and Independent Interaction — future, not MVP

Explore full pause and optional 20% tactical slow, with transparent control attribution. Test **unlimited pause/slow first** before introducing recharge meters, charges, or restrictive rules. Time scaling must preserve authoritative simulation semantics. Independent multiplayer dialogue/shop interaction may require shared/local world-state locks and careful scripting compatibility. Do not retrofit these via untested assumptions about current GemRB networking.

### 8.5 Combat and encounter refinements — experimental only

Potential directions: melee engagement, meaningful martial pressure and interrupts, better combat-defense counterplay, intelligent AI responses, and occasional ambitious, thematic boss encounters. Preserve powerful characters, exceptional spells, meaningful easy encounters and the existing game's overall identity. **Don't nerf individual spells as compensation for underlying movement/hit-rate/timing defects.** SCS and Ascension are optional reference points, not proof that harder encounters are always better.

---

## 9. Artistic direction and visual preservation

**Artistic charter:** *The world is not a set of gameplay arenas decorated as places; it is a set of authored places where gameplay happens.*

Favor irregular, specific, painterly environments with intentionally composed lighting, architecture and spatial relationships. Engine tools must accommodate unusual authored spaces when practical, without sacrificing basic navigation and interaction correctness. Reuse assets when it follows believable world history or artistic intent—not solely because the asset pipeline prefers uniform modular scenery.

Modern renderer ≠ modern-looking art. A fixed camera, pre-rendered/painted backgrounds, small expressive characters, restrained VFX, and sharp attack/death feedback may be deliberately retained. An enhanced visual profile should iterate beside faithful classic mode and be validated against original composition, color and animation feel. Artwork should be human authored; AI may assist technical workflows and validation.

Do **not** prematurely generate or replace art assets as part of an engineering task unless explicitly requested.

---

## 10. Development milestones and stage gates

### Phase 0 — Feasibility and evidence (START HERE)

- Pin upstream GemRB revision, build instructions, toolchain, and relevant licenses.
- Confirm actual current BG2EE support with reproducible fixtures rather than relying on summaries.
- Produce a source-level architecture map: actor/effects/action timing, scripting, navigation, inventory, rendering, persistence.
- Audit `Interface`, `Actor`, `GameScript`, `GUIScript`, effect/opcode handling, resources, main loop, saves and plugin management using the **Architecture & Extensibility acceptance review** in §6. Record Retain/Wrap/Refactor/Replace decisions with source evidence, not file-size heuristics.
- Establish automated build, smoke test and logging pipeline.
- Identify known incompatibilities against unmodded BG2EE and eventual SCS/Ascension.
- Decide fork strategy only after assessing coupling and change surface.

**Gate:** A working engine baseline, evidence-based compatibility report, prioritized risk register, and first repeatable tests.

### Phase 1 — Faithful playable BG2EE

- Improve BG2EE resource/script/effect parity enough to play and validate the campaign.
- Establish mechanical golden scenarios and representative game-state/save fixtures.
- Avoid redesigning gameplay in this phase.

**Gate:** Core campaign progression is repeatably playable and major compatibility failures are documented and decreasing.

### Phase 2 — Instrumentation and engine correctness

- Add authoritative structured events, profiling, and controlled test scenarios.
- Implement or prototype native Navigation Redux against known movement fixtures.
- Quantify effects on realized melee effectiveness and encounter outcomes.

**Gate:** Reproducible parity/correction evidence; no unexplained systemic balance shift.

### Phase 3 — User experience and first native modules

- UI infrastructure, Combat Info MVP, Inventory Redux proof of concept.
- Verify vanilla script and save compatibility for new storage semantics.
- Test interactions in ordinary play and SCS-style encounters.

**Gate:** Distinctly improved experience without unmeasured gameplay regressions.

### Phase 4 — Curated modded campaign

- Verify supported SCS/Ascension resource semantics, AI behavior and quests.
- Native replacements for selected EEex-dependent improvements as needed.
- Rebaseline combat feel before changing numerical rules.

**Gate:** Fully playable, tested curated challenging campaign.

### Phase 5 — Modern graphics infrastructure

- Audit and extend existing renderer; support modern direct asset formats and high-res UI.
- Maintain faithful original mode; prototype optional enhanced visual profile.
- Do not block stable gameplay on full HD artwork production.

**Gate:** Old content draws faithfully and new formats work correctly, with comparable behavior/performance.

### Phase 6 — Broader saga, optional rules, multiplayer, visual remaster

- Expand supported games and mods deliberately.
- Evaluate fundamental combat experiments, adjust dependent spells/classes/AI/encounters in the onion order.
- Pursue tactical multiplayer and human-led remaster only after architectural gates are satisfied.

**Gate:** Separate features ship when verified; no expectation of a single massive final rewrite.

Phases may overlap where independence is demonstrable; stage gates prevent speculative systems from entering the stable baseline prematurely.

---

## 11. Agent decision hierarchy and stop signs

When facing a tradeoff, generally prioritize:

1. **Existing game content remains functional.**
2. **The BG player experience and combat feel remain recognizable.**
3. **The requested change has clear observable semantics and tests.**
4. **Engine architecture remains comprehensible and replaceable.**
5. **Changes are incremental, documented, and reversible.**
6. **Performance is improved based on profiling, not assumptions.**
7. **Specific balance goals outrank generic modernization fashion.**

**Stop and request a design decision** before:

- Changing THAC0/AC, APR, six-second round semantics, foundational spell protections, stacking rules, or permanent character progression.
- Removing vanilla content or rewriting quests/encounters.
- Converting a user-facing convenience feature into unapproved power or information gain.
- Introducing a new persistence format that cannot import existing saves, without a transition plan.
- Committing to an engine-wide rewrite or language migration.
- Assuming use of proprietary Baldur's Gate assets or other copyrighted content in distributable builds.
- Quietly declaring unresolved compatibility scenarios fixed.

### Things we have deliberately *not* decided

- Exact BG2EE parity state of the chosen GemRB revision until audit.
- Whether full deterministic lockstep or server-authoritative multiplayer is desirable.
- Whether any fundamental combat mathematics should change at all.
- Whether combat engagement/interrupt rules should enter the main experience.
- Final Party Stash starting capacity, Bag of Holding capacity progression, category-specific allocation, and overflow semantics.
- Full Combat Pack UX and edge-case rules pending playtest.
- Scope and method of any HD restoration and ownership/distribution permissions.
- Whether source-level GemRB refactoring remains cheaper than selective replacement over the long term.

---

## 12. Working first assignment for Codex

**Do not implement major gameplay changes yet.** Begin with a source-level GemRB feasibility audit and reproducible BG2EE baseline.

Deliver:

1. `docs/architecture/current-system-map.md` — current code paths and dependency diagrams for engine loop, actor/action/effects, script interpreter, inventory, navigation, renderer and saves. Link exact source symbols/files and distinguish observations from guesses.
2. `docs/compatibility/bg2ee-baseline.md` — actual tested BG2EE capabilities, failures, repro instructions and versions. Do not claim full campaign support without evidence.
3. `docs/testing/golden-scenarios.md` — minimum mechanical, movement, script, save/load and visual fixtures; indicate which can run headlessly.
4. `docs/risks/modernization-risk-register.md` — highest coupling and migration risks, compatibility obligations and mitigation strategies.
5. `docs/roadmap/first-native-change.md` — a small, safe candidate improvement (prefer navigation or instrumentation) with test plan and estimated touch points.
6. `docs/architecture/subsystem-acceptance-matrix.md` — disposition and reasoning for all nine explicitly named architecture candidates in §6.
7. `docs/architecture/state-and-dependency-map.md` — source-grounded state ownership, coupling and mutation paths, especially `Actor` and `Interface`.
8. `docs/architecture/extensibility-contracts.md` — legacy compatibility versus proposed data/script/native extension layers; versioned APIs, commands and causal events.
9. `docs/architecture/proof-of-change.md` — one bounded architectural experiment and observed change surface, or a clearly justified reason it cannot yet be safely executed.

For each deliverable include **evidence, uncertainty, and validation steps**. Do not use fictional function names or assert capabilities without checking. Prefer upstream contribution-compatible changes where practical; a fork is a tool, not an end in itself.

---

## Final reminder

**BG Redux succeeds when the player can play Baldur's Gate itself—recognizably, faithfully, and joyfully—through an engine we can inspect and improve without fighting the original executable.**

Everything else is layered in deliberately: first compatibility, then trustworthy implementation, then a better interface, then carefully measured systemic improvements, and finally optional refinements in balance, encounters, graphics and multiplayer.

> **Modernize from the foundations outward. Keep a faithful reference. Explain the effect of every change. Never sacrifice Baldur's Gate's distinctive feel just to make the system look cleaner on paper.**
