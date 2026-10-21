# Inventory Redux

Status: the isolated solo prototype is playable, with native equipment,
three Quick Weapons, three ammunition slots, three Quick Items, always-available
stash transfers and verified fixture save/load. Combat Pack and danger locking
were removed by the user's later design amendments.
See the [prototype guide](prototype/README.md),
[transfer/performance gate](gate51/DECISION.md),
[owned preview snapshot gate](gate52/DECISION.md),
[native preview integration checkpoint](gate53/DECISION.md),
[loaded native fork and conservation checkpoint](gate54/DECISION.md),
[actual native RNG routing checkpoint](gate56/DECISION.md),
[stock detached-sprite route decision](gate58/DECISION.md),
[completed native local-table lifetime](gate66/GATE_DECISION.md),
[current owned-animation integration checkpoint](gate67/README.md),
[latest major prototype gate](gate31/GATE_DECISION.md),
[cursor/recovery and expanded testing correction](gate32/GATE_DECISION.md),
[accepted contextual layout](gate20/CONTEXTUAL_LAYOUT_ACCEPTANCE.md),
[earlier prototype gate](gate6/GATE_DECISION.md),
[earlier diagnostic gate](gate3/GATE_DECISION.md),
[native adapter and policy assessment](gate2/GATE_DECISION.md) and
[first feasibility gate](gate/GATE_DECISION.md).
This directory contains preserved design, research and diagnostic scripts.
The prototype has progressed through replacement, swaps, quantity handling,
native cursor/usability and automatic intake, with user-confirmed container
pickup. Gate51 records the latest reversible transfer trial and bounded
usability queries. Gate52 passes offline owned snapshot assembly; Gate54 loads
the disabled native fork and preserves observed inventory state. Gate56 passed
actual original/private RNG routing with equal observed pre/post item state.
Gate58 selects the engine's detached scratch-sprite workflow for a restricted
lifetime experiment; Gate59 prepares its routing and cleanup correction. Full hypothetical equipment previews, campaign
compatibility, a distributable installer and save migration remain future work.

Gate66 completed actual native local-table reconstruction and normal cleanup in
a disposable fixture. Gate67 now compiles dormant animation/resource ownership
adapters in the actual EEex source and tests the required allocation, argument,
resource and cleanup contracts. Gate67 has not yet executed native animation
construction, and does not enable hypothetical statistics in the playable UI.

## Preserved design sources

- [Full manifesto and programmer wireframe](../reference/inventory-redux/Inventory_Redux_Codex_Manifesto_and_Wireframe.md): original upload, preserved without edits; authority for system behavior and information hierarchy.
- [Programmer wireframe](../reference/inventory-redux/programmer-wireframe.jpg): grayscale structural reference for layout and interaction states.
- [GUI atmosphere preview](../reference/inventory-redux/gui-atmosphere-preview.jpg): painted visual reference for mood, materials, framing, and overall feel. Its generated text and item statistics are illustrative.

The user's later instructions supersede the preserved original manifesto.
Otherwise the written manifesto takes precedence where the pictures differ. In particular,
the painted preview's duplicated Gloves label does not add an equipment slot;
the illustrated 228/600 lbs display does not establish a stash capacity rule;
and sample Varscona properties are not game data. The final art specification
and design schema remain future work.

## Design baseline

Current user-approved design, superseding the original preparation policy:

- One queryable Party Stash replaces ordinary backpack bookkeeping. Storage,
  item ownership, and displayed grid positions remain separate concepts.
- Character Anchor stays on the left. The right workspace expands the stash
  while browsing and reveals Item Details on selection.
- The compact default character panel shows AC, THAC0, damage, APR, HP and six
  attributes. A pinned, scrollable Full Stats view starts with saves and
  resistances, including physical and magic resistance and casting-speed
  information. Accurate held-item projections remain a separate native gate;
  current actual stats must never be presented as hypothetical changes.
- Item Details holds intrinsic properties, usability reasons, qualitative
  effects and lore. Proficiencies belong on Character Record.
- Equipment concepts are exactly Helmet, Necklace, Cloak, Armor, Bracers/Gloves,
  Belt, Ring 1, Ring 2, Boots and Offhand, arranged anatomically around the
  centered paper doll. The selected Quick Weapon is the active weapon; no
  separate Primary Weapon slot is needed.
- User amendment, 2026-10-07: add three visible ammunition slots to the GUI.
  Preserve native ammunition/launcher behavior. This supplements the original
  equipment list; final layout remains unfrozen. Preserve the original uploads.
- Three Quick Weapons for every class, three ammunition slots and three Quick
  Items remain visible. There is no Combat Pack or strength-capacity policy.
- Party Stash is always available. Native custody, stale identity and transaction
  readiness still guard item operations; combat danger does not lock storage.
- Restock uses actual shared stock, preserves quantities and charges, and never
  takes from another character's prepared loadout without design authorization.
- Existing container contents and quest/script references must survive. Virtual
  flattening is the preferred research direction, not a proven implementation.
- Scope amendment, 2026-10-08: V1 is single-player. Multiplayer is a later
  feature, not a V1 acceptance gate. Its eventual design should support local
  browsing with host-authoritative mutations; Core reuse needs separate validation.

## Next authorized work boundary

User amendment, 2026-10-08: proceed with the next solo gate and use three
parallel agents for separable Inventory Redux work in general. The orchestrator
coordinates shared native execution; agents work on disjoint files. The user's
experience that Bag of Holding usually supports quest detection is an explicit
research lead: inspect existing native and installed mod behavior before adding
compatibility hooks.

The approved diagnostic phase included source inspection and controlled native
trials on disposable fixtures. Results are recorded in the gate decision and
individual reports. The current prototype and its limitations are documented
in the prototype guide. The latest native cursor spike proves ordinary whole
pickup, empty quick-item/ammo placement and reverse transfer, whole cancellation
and exact original-stack restoration after partial pickup without a new DLL.
The earlier provider18 GUI used the engine-owned cursor for bounded ordinary
potion/arrow routes, with cancellation, deferred closing and pinned handoff
identity. All three Quick Item and Ammo destinations are admitted for those
ordinary resources, including fully fitting compatible occupied stacks.
These are historical Gate28 limits; see later provider22/cursor49 decisions for
current transfers, swaps, usability and automatic intake.

The user's later amendments remove Combat Pack and threat locking, and authorize
uninterrupted native preview development until a genuine input gate. The playable
prototype is complete; accurate hypothetical stats still need native integration.

Native preview progress, 2026-10-11: [Gate64](gate64/GATE_DECISION.md) passed
an actual restricted inert clone lifetime with independent source/stash/registry
conservation. [Gate65](gate65/GATE_DECISION.md) also passed actual native copying
of Imoen's eight local variables followed by native cleanup and conservation.
[Gate66](gate66/GATE_DECISION.md) passed actual native reconstruction of an empty
clone table at capacity32, import of the PC's20 locals and complete cleanup and
conservation. Gate67 investigates owned animation and full-loader prerequisites.
Neither inert lifetime nor local reconstruction is an accurate equipment preview;
full loading, effect/animation containment and native baseline parity remain
required before showing hypothetical statistics to players.

Keep storage, equipment, Quick Slots, transaction readiness, item query,
Item Details, and character preview separate when implementation is authorized.
Existing [Core](../core/README.md) and [EEex GUI reference](../docs/gui-reference-b3timer.md)
provide local starting points; neither proves inventory feasibility.

## Decisions deliberately open

[Second-pass feasibility assessment and ordered spikes](FEASIBILITY_SECOND_PASS.md)
records the user's practicality audit follow-up, inspected source entry points,
and the proposed gates. The executable gate now adds scoped live evidence.

[Completed parallel source review](research/README.md) adds concrete slot/UI,
storage/transfer, and native-preview findings, including the existing native
item-rating copy path. Findings remain separate from live acceptance.

Storage backing and persistence beyond the tested fixture; container indexing
and nesting; stack/ammunition/charge compatibility; preview
calculation without actual equip; merchant integration; party departure and item
ownership; multiplayer arbitration and restock authority; supported game/UI/mod
combinations; final art and scaling. Identification remains a separate system.

## Future acceptance gates

Apply the current design to acceptance: ordinary loot to stash, contextual
equipment preview and equip, immediate access during combat, stock-limited
restock if retained, and intact Bag of Holding contents from old saves. The
original danger-lock and Combat Pack scenarios are historical superseded design.

V1 requires technical evidence for item identity/quantity/charge conservation,
save/load, party changes, area transition and UI reload/scaling. Simultaneous
multiplayer requests belong to the later multiplayer feature's acceptance gates.

[Recommended next solo milestone](gate2/NEXT_SOLO_GATE.md): reliable stash
operations and campaign compatibility before production GUI work.
Its [executed results](gate3/GATE_DECISION.md) now define the targeted native
and owner-preserving compatibility work required before promotion.

[Gate4 results](gate4/GATE_DECISION.md) implement and test precise native
container selection and owner-preserving shared indexing. Detached preview
remains unavailable pending native lifecycle isolation; this is the current
decision and next-gate scope.
