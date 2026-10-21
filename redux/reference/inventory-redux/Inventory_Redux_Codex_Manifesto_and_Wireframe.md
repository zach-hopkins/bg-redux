# Inventory Redux — Programmer Wireframe & Codex Manifesto

> **Purpose:** Programmer-facing implementation reference and project manifesto for Codex.  
> This is **not** a final visual-art specification. Preserve the information hierarchy, interaction model, state behavior, and design principles. Final GUI styling can be designed later.

---

# Part I — Programmer Wireframe

## 1. Core screen model

The inventory screen has **two conceptual regions**:

1. **Character Anchor** — fixed on the left.
2. **Inventory Workspace** — adaptive on the right.

The character panel is the **live equipment-preview surface**.

There is **no separate stat-comparison panel**.

When the player highlights/selects an equippable item, projected changes appear directly in the character's Combat Summary.

---

## 2. Desktop wireframe — selected item state

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ INVENTORY                                                                                  [Threat/State] [X] │
├───────┬───────────────────────────────────┬──────────────────────────────────────────────────────────────────┤
│ PARTY │ CHARACTER ANCHOR                  │ INVENTORY WORKSPACE                                               │
│       │                                   │                                                                  │
│ [P1]  │ Keldorn                           │ PARTY STASH                                      [Search________] │
│ [P2]  │ Level 13 Inquisitor               │ [All][Weapons][Armor][Potions][Scrolls][Quest][Misc] [Sort ▼]   │
│ [P3]  │                                   │                                                                  │
│ [P4]  │ ┌──────── EQUIPMENT ────────────┐ │ ┌──────────────────────────────────────────────────────────────┐ │
│ [P5]  │ │ Helmet        Necklace        │ │ │ [item][item][item][item][item][item][item][item]          │ │
│ [P6]  │ │ Cloak         Armor           │ │ │ [item][item][item][item][item][item][item][item]          │ │
│       │ │ Bracers/Gloves Belt           │ │ │ [item][item][item][item][item][item][item][item]          │ │
│       │ │ Ring 1        Ring 2           │ │ │ [item][item][item][item][item][item][item][item]          │ │
│       │ │ Boots                          │ │ └──────────────────────────────────────────────────────────────┘ │
│       │ │ Primary       Offhand          │ │                                            [◀] Page 1/4 [▶] │
│       │ └───────────────────────────────┘ │                                                                  │
│       │                                   │ ┌──────────────── ITEM DETAILS — selected item ───────────────┐ │
│       │ QUICK SLOTS (3)                   │ │ [Details] [Effects] [Lore]                                  │ │
│       │ [1] [2] [3]                       │ │                                                              │ │
│       │                                   │ │ [icon]  Varscona +1                                         │ │
│       │ COMBAT PACK (base 3; STR-mod.)    │ │         Long Sword                                          │ │
│       │ [1] [2] [3] [+ if STR grants]     │ │         requirements / usability / base properties          │ │
│       │                                   │ │                                                              │ │
│       │ ┌──────── COMBAT SUMMARY ───────┐ │ │ Special Effects                                             │ │
│       │ │            NOW   PREVIEW Δ    │ │ │ • +1 hit/damage                                             │ │
│       │ │ AC          -7 → -8     +     │ │ │ • +2 vs. Shapechangers                                     │ │
│       │ │ THAC0        7 →  5     +     │ │ │ • Fear chance                                               │ │
│       │ │ Damage   14-23 →16-26   +     │ │ │                                                              │ │
│       │ │ APR        3/2 →3/2     —     │ │ │ Flavor / descriptive text                                  │ │
│       │ │ HP     126/126→126/126  —     │ │ └──────────────────────────────────────────────────────────────┘ │
│       │ │ Save Death  10 →10      —     │ │                                                                  │
│       │ │ Save Wands  12 →12      —     │ │                                                                  │
│       │ │ Save Poly   11 →11      —     │ │                                                                  │
│       │ │ Save Breath 12 →12      —     │ │                                                                  │
│       │ │ Save Spell  13 →13      —     │ │                                                                  │
│       │ │ MR           0 →10%     +     │ │                                                                  │
│       │ └───────────────────────────────┘ │                                                                  │
│       │                                   │                                                                  │
│       │ ATTRIBUTES (secondary)            │                                                                  │
│       │ STR 18 DEX 14 CON 16              │                                                                  │
│       │ INT 10 WIS 13 CHA 17              │                                                                  │
│       │                                   │                                                                  │
│       │ RESISTANCES (secondary)           │                                                                  │
│       │ Fire 0  Cold 0  Acid 0            │                                                                  │
│       │ Elec 0  Magic 0  Poison 0         │                                                                  │
├───────┴───────────────────────────────────┴──────────────────────────────────────────────────────────────────┤
│ [Character Record] [Reform Party]                                                     [Close / ESC]         │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Important
- **Do not show proficiencies here.** They belong on the Character Record screen.
- The **Combat Summary is the comparison UI**.
- Item Details explains the item; it does **not** duplicate a second comparison table.

---

## 3. Desktop wireframe — browse/default state

When no item is selected, Item Details should disappear or collapse and the Party Stash should use the recovered space.

```text
┌──────────────────────────── Character Anchor ───────────────────────────┬─────────────────────────────────────┐
│                                                                        │ PARTY STASH                         │
│ Equipment                                                              │ [Search__________________________] │
│ Quick Slots                                                            │ [Filters...]          [Sort ▼]     │
│ Combat Pack                                                            │                                     │
│ Combat Summary (current values only)                                   │                                     │
│ Attributes / Resistances                                               │         LARGE STASH GRID             │
│                                                                        │                                     │
│                                                                        │                                     │
│                                                                        │                                     │
│                                                                        │                          Page 1 / N │
└────────────────────────────────────────────────────────────────────────┴─────────────────────────────────────┘
```

**Goal:** browsing feels like querying one inventory, not managing six backpacks.

---

## 4. Character equipment slots — exact list

Exactly these equipment concepts:

1. Helmet
2. Necklace
3. Cloak
4. Armor
5. Bracers / Gloves
6. Belt
7. Ring 1
8. Ring 2
9. Boots
10. Primary Weapon
11. Offhand
   - shield, second weapon, or other legal offhand item

Do not invent extra character inventory/equipment slots.

---

## 5. Carried-item model

### Quick Slots
- Base: **3**
- Character-specific.
- Immediate-use slots.
- Preserve the familiar BG concept.

### Combat Pack
- Base: **3**
- Character-specific.
- Capacity may increase with Strength.
- Exact Strength curve is **not yet frozen**.
- Contains items intentionally carried into danger.
- Possible contents:
  - spare weapon;
  - potion;
  - wand;
  - scroll;
  - utility item;
  - ammunition if needed by final design.

### Party Stash
- Shared across the active party.
- Intended to be effectively invisible storage.
- Searchable / filterable / sortable.
- Current philosophy: **do not preserve general stash encumbrance merely for tradition**.
- If weight/capacity remains at all, it must justify a meaningful gameplay purpose.
- Do not build the architecture around a party-weight cap.

---

## 6. Access state machine

Do **not** rely solely on BG's raw "combat mode" or "cannot save" state.

Use a more robust concept of **meaningful nearby hostile threat**.

```text
SAFE
  Party Stash = READ/WRITE
  Equipment = usable
  Quick Slots = usable
  Combat Pack = usable
  Auto-restock = allowed

        │ qualifying nearby hostile threat
        ▼

THREAT / DANGER
  Party Stash = VISIBLE, SEARCHABLE, READ-ONLY
  Equipment already on character = usable
  Quick Slots = usable
  Combat Pack = usable
  Items cannot be pulled from Party Stash
  Auto-restock = suspended

        │ no qualifying threat for short grace period
        ▼

SAFE
  Party Stash = READ/WRITE
  Auto-restock may run
```

Threat detection should avoid false locks caused by:
- lingering Web / Entangle / Cloudkill-type effects;
- a combat-music flag that has not cleared;
- accidental friendly clicks;
- a hostile actor many rooms away that is not meaningfully engaged;
- stale engine state after combat.

The exact threat predicate must be researched and playtested.

---

## 7. Item selection behavior

Selecting/highlighting an equippable item should:

1. Populate **Item Details** in the adaptive workspace.
2. Determine the relevant equipment slot.
3. Calculate the hypothetical character state if equipped.
4. Update **Combat Summary** live:
   - current value;
   - projected value;
   - positive/negative/no-change indicator.
5. Update any relevant resistance values.
6. Leave base Attributes visually secondary.
7. Never require a separate comparison panel.

If an item is unusable:
- show why in Item Details;
- do not pretend to preview an illegal state unless deliberately supported.

---

## 8. Combat Summary — minimum fields

Primary:
- Armor Class
- THAC0 / attack value
- Damage
- Attacks per Round
- Hit Points

Saving throws:
- Death
- Wands
- Polymorph
- Breath
- Spells

Other:
- Magic Resistance

Secondary resistance area:
- Fire
- Cold
- Acid
- Electricity
- Magic / Magic Damage as technically appropriate
- Poison
- expand later if worthwhile

Only show preview emphasis where values actually change.

---

## 9. Stash query tools

Required:
- text search;
- category tabs;
- sorting;
- pagination or scrolling;
- item grid/list;
- selected-item highlight.

Initial categories:
- All
- Weapons
- Armor
- Potions
- Scrolls
- Quest
- Misc

Possible later filters:
- usable by selected character;
- equippable now;
- enchantment;
- damage type;
- recently acquired;
- value;
- alphabetic;
- consumables;
- ammo.

Do not overbuild filters before the basic query flow is proven.

---

## 10. Auto-restock concept

The player may define desired carried quantities/loadouts.

Example:

```text
Jaheira
Quick Slots
  Potion of Extra Healing x2
  Antidote x1

Combat Pack
  Wand of Heavens x1
  Spare Club x1
  Potion of Magic Shielding x1
```

When the party returns to SAFE state:
- attempt to refill missing configured items from Party Stash;
- never duplicate items;
- never fabricate unavailable items;
- clearly handle partial stock;
- avoid repeated player micromanagement after every encounter.

Exact UX/configuration can be designed later.

---

## 11. Bags of Holding / item containers

**Bags of Holding are functionally irrelevant to Inventory Redux.**

Do not build bag micromanagement into the core UI.

Desired conceptual behavior:
- Party Stash replaces the logistical reason Bags of Holding exist.
- Existing Bags of Holding / gem bags / scroll cases / potion cases may need compatibility handling so old saves and modded content remain safe.
- Their contents should remain accessible and migrate/flatten safely if technically feasible.
- A bag may remain as a world/lore item, but should not require the player to manually open a second inventory inside the inventory.
- Do not delete or invalidate quest/script checks merely because the UI no longer needs the container.

Compatibility research is required before choosing migration semantics.

---

## 12. Programmer principle

Keep these concepts separate in code:

```text
STORAGE
  What the party owns.

EQUIPMENT
  What the character is wearing/wielding.

QUICK SLOTS
  Familiar immediate-use slots.

COMBAT PACK
  What the character deliberately carries into danger.

ACCESS POLICY
  Whether Party Stash may currently mutate.

ITEM QUERY
  Search/filter/sort/browse.

ITEM DETAILS
  What the selected item is.

CHARACTER PREVIEW
  What the selected item would do to this character.
```

Do not let UI layout collapse these into one monolithic inventory-state implementation.

---

# Part II — Inventory Redux Codex Manifesto

## 1. Project thesis

Classic Baldur's Gate inventory mixes together two very different jobs:

1. **storage** — where all the party's accumulated stuff happens to live;
2. **combat preparation** — which items a specific character actually has available when things go wrong.

Most of the first job is bookkeeping. The second can be meaningful gameplay.

Inventory Redux should therefore make **storage nearly invisible** while making **combat loadout intentional**.

> **Storage should be invisible. Loadout should be intentional.**

The project is not trying to turn Baldur's Gate into an inventory-survival game. It is trying to remove the question:

> "Which of six backpacks did I put this in?"

and preserve or improve the question:

> "Who did I prepare to carry this into the fight?"

---

## 2. Design goals

### 2.1 Remove bookkeeping

The player should not routinely need to:
- distribute general loot across six backpacks;
- move heavy junk to the strongest party member;
- remember which character holds a quest item;
- hunt through Bags of Holding, potion cases, scroll cases, gem bags, and nested containers;
- transfer an item merely to compare or equip it;
- manually replenish the same potion loadout after every battle.

Those actions are administrative unless they create an actual decision.

### 2.2 Preserve meaningful preparation

Character-specific inventory matters when it represents **what that character can access during danger**.

Preparation can create real choices:
- Who carries the emergency healing potion?
- Who brings the Wand of Spell Striking?
- Does Jaheira carry a backup blunt weapon?
- Does the low-Strength mage spend one of their few Combat Pack slots on a defensive potion?
- Is the spare bow worth carrying into this dungeon?

That is inventory gameplay worth preserving.

### 2.3 Keep inventory legible

The inventory should behave more like a searchable database of party-owned items than a warehouse simulator.

The player should be able to ask:
- show me swords;
- show me potions;
- find Carsomyr;
- show items usable by Keldorn;
- what happens to Keldorn if I equip this?
- what items do we own that solve this problem?

The UI should answer directly.

---

## 3. Core system model

### Shared Party Stash

One shared pool represents the party's general possessions.

Outside danger:
- fully accessible;
- searchable;
- sortable;
- filterable;
- equippable directly onto party members.

The stash should be effectively unconstrained unless research demonstrates that a capacity limit creates genuinely useful gameplay.

Do **not** preserve general party encumbrance automatically just because vanilla has it.

The burden of proof is reversed:

> If a restriction does not create an interesting decision, remove it.

### Personal Equipment

Equipment remains character-specific.

Exact equipment concepts:
- Helmet
- Necklace
- Cloak
- Armor
- Bracers / Gloves
- Belt
- Ring 1
- Ring 2
- Boots
- Primary Weapon
- Offhand

### Quick Slots

- Preserve familiar BG Quick Slots.
- Base count: **3**.
- Character-specific.
- Immediately available during danger.

### Combat Pack

A new small character-specific carried inventory.

- Base count: **3**.
- Strength modifies capacity.
- Exact Strength progression remains an open balance question.
- Represents what the character physically prepared to carry into danger.
- Available during nearby hostile threat.
- Small enough to create choices without recreating six-backpack bookkeeping.

This is where carrying capacity becomes interesting.

Strength should affect **combat readiness**, not the party's ability to hoard vendor trash.

---

## 4. Access philosophy

The shared stash is not magically available in the middle of an active fight.

However, access must not be keyed to a brittle vanilla "combat flag."

Baldur's Gate can remain technically in combat because:
- Web or Entangle remains on the floor;
- combat music has not cleared;
- a distant hostile exists somewhere irrelevant;
- the player accidentally targeted an ally;
- engine state has not reset cleanly.

Inventory Redux should instead detect a **meaningful nearby hostile threat**.

### Safe state

Party Stash:
- full read/write access.

Character:
- equipment usable;
- Quick Slots usable;
- Combat Pack usable.

Auto-restock:
- permitted.

### Danger state

Party Stash:
- remains visible;
- remains searchable;
- **read-only**.

Character:
- equipment already on the character remains available;
- Quick Slots remain available;
- Combat Pack remains available.

The player may look at the stash and realize:

> "Damn, the potion I need is in storage."

That is useful information.

They simply cannot teleport it into someone's hand during combat.

### Leaving danger

After no qualifying hostile threat remains for a short grace period:
- unlock Party Stash;
- permit auto-restock;
- return to normal inventory behavior.

The grace period should prevent flicker and transient state changes.

---

## 5. Character panel philosophy

The selected character is the stable anchor of the inventory screen.

The most important question when browsing equipment is:

> **"What does this do to my character?"**

Therefore the character's own stats should become the preview surface.

Do **not** require the player to:
1. inspect an item;
2. read a separate comparison table;
3. mentally transfer those changes back to the character sheet.

Instead, selecting an item should temporarily preview the result directly on the character.

### Combat Summary is primary

Prominent:
- Armor Class;
- THAC0 / attack;
- Damage;
- Attacks per Round;
- Hit Points;
- Saving Throws;
- Magic Resistance;
- relevant resistances.

Display:

```text
THAC0     7  →  5
Damage   14-23 → 16-26
Fire      0% → 50%
```

Use clear positive/negative/no-change visual treatment.

### Attributes are secondary

STR / DEX / CON / INT / WIS / CHA remain visible because they are useful context, but they should not dominate the inventory decision surface.

### Resistances are secondary but immediately available

Inventory choices can substantially affect:
- fire resistance;
- cold resistance;
- acid resistance;
- electricity resistance;
- magic resistance;
- poison;
- other relevant defensive categories.

They deserve visible space, but less emphasis than the central combat summary.

### Proficiencies are omitted

Proficiencies belong on the Character Record screen.

They influence outcomes indirectly; the inventory screen should show the final resulting combat numbers instead.

---

## 6. Item-details philosophy

Item Details answers:

> **"What is this item?"**

Character Preview answers:

> **"What does this item do to me?"**

Do not duplicate these jobs.

Item Details may contain:
- item name;
- type;
- icon/art;
- base properties;
- requirements;
- usability;
- special effects;
- description;
- lore.

Tabs such as:
- Details
- Effects
- Lore

are acceptable.

Do **not** build a second large comparison panel if the Character Combat Summary already previews the effect.

---

## 7. Adaptive workspace

The inventory workspace should change based on what the player is doing.

### Browse state

When no item is selected:
- Party Stash gets maximum space;
- search/filter/sort/grid dominate;
- details area may collapse or disappear.

### Selected-item state

When an item is selected:
- stash condenses enough to reveal Item Details;
- the character panel previews stat changes;
- Item Details shows the item's intrinsic information.

Conceptually the screen remains only two major regions:

1. character;
2. inventory workspace.

Avoid turning the screen into three independent competing dashboards.

Minimal eye travel is a design goal.

---

## 8. Search, filtering, and comparison

These are core features, not polish.

At minimum:
- text search;
- category filters;
- sorting;
- selected-character context;
- pagination/scrolling;
- item usability feedback.

Potential future filters:
- usable by selected character;
- equippable now;
- weapon category;
- enchantment;
- damage type;
- newest;
- value;
- recently acquired.

Do not overdesign the filtering system before the basic interaction is validated.

The ideal experience is:

> "I want a sword."

Search/filter returns swords.

Select one.

Keldorn's Combat Summary immediately previews the result.

That is the whole loop.

---

## 9. Auto-restock

Preparation should create decisions.

Replenishment should not create chores.

Allow a character to remember desired carried items.

Example:

```text
Anomen Combat Pack
- Potion of Extra Healing x2
- Antidote x1
- Wand of Heavens x1
```

When safe:
- automatically refill missing configured items from Party Stash;
- only use items actually owned;
- handle insufficient stock gracefully;
- never duplicate consumables.

This preserves:
- who carries what;
- how many Combat Pack slots are committed;
- resource scarcity.

It removes:
- dragging the same potion onto Anomen after every fight.

> **Preserve the decision. Automate the repetition.**

---

## 10. Bags of Holding and other containers

Bags of Holding are no longer part of the desired inventory gameplay loop.

They currently exist largely because vanilla storage is restrictive.

Inventory Redux removes the need for that workaround.

Therefore:

> **Bags of Holding are functionally irrelevant.**

The same reasoning applies to:
- potion cases;
- scroll cases;
- gem bags;
- similar logistical containers.

However, compatibility matters.

Do not simply delete container resources or assume nothing references them.

Research:
- savegame storage semantics;
- script checks;
- quest checks;
- mod dependencies;
- nested container contents;
- merchant/container interactions.

Ideal end state:
- contents are surfaced through Party Stash;
- no nested inventory micromanagement is required;
- old saves remain safe;
- mods do not break;
- the physical bag can remain as flavor/world content if needed.

---

## 11. Encumbrance philosophy

General inventory encumbrance is currently **not assumed to be valuable**.

Vanilla players already defeat much of it through:
- Bags of Holding;
- multiple characters;
- specialized containers;
- dropping/stashing items elsewhere.

The result is often more clicks rather than meaningful scarcity.

Leaving an item behind in a long CRPG can also produce anxiety because the player may not know whether it is:
- unique;
- upgradeable;
- quest-relevant;
- needed hours later;
- impossible to reacquire.

Do not retain encumbrance solely for realism.

If a capacity mechanic exists, it should create meaningful choices.

The current preferred place for capacity is the **Combat Pack**, where Strength can influence how prepared a character can be.

This converts Strength from:

> "who carries the pile of vendor armor?"

into:

> "who can bring more tactical tools into danger?"

That is a much stronger gameplay role.

---

## 12. Lore abstraction

A shared stash is mechanically abstract.

That is acceptable.

Forgotten Realms provides endless diegetic explanations if one is desired:
- enchanted traveling cache;
- extradimensional party chest;
- magical satchel;
- Gorion-provided storage artifact;
- camp/familiar/porter abstraction.

This is third-order polish.

Do not compromise the system design to solve the lore question.

The lore should explain the mechanic, not dictate worse UX.

---

## 13. Research phase before implementation

Before rewriting the inventory UI, Codex should map how the existing game actually works.

Research:

### UI layer
- existing BG2EE inventory Lua;
- EEex inventory UI implementations;
- cross-party inventory mods;
- store UI;
- bag/container UI;
- character equipment UI;
- drag/drop behavior;
- selection state;
- quick slots.

### Engine/data layer
- inventory slot structures;
- item ownership;
- equipment ownership;
- transfer restrictions;
- item stacking;
- container stores;
- Bags of Holding;
- weight calculation;
- item usability;
- class/race/alignment restrictions;
- equipped-item stat recomputation;
- combat-state indicators;
- hostile proximity / engagement state;
- multiplayer ownership and synchronization.

### Compatibility
- EET;
- EEex;
- common inventory/container tweaks;
- item randomizers;
- mod-added containers;
- mod-added equipment slots if any;
- multiplayer implications.

Document findings before choosing implementation shortcuts.

---

## 14. Recommended implementation phases

### Phase A — Inventory model research

Deliverable:
`INVENTORY_ENGINE_MAP.md`

Document:
- where items live;
- how transfers work;
- how bags work;
- how equipped stats recalculate;
- what can safely be virtualized.

### Phase B — Shared stash prototype

Goal:
- display all party-owned non-equipped items in one queryable pool;
- move/equip items from that pool outside danger;
- preserve item identity and quantities.

No fancy art required.

### Phase C — Live character preview

Goal:
- select a candidate item;
- determine the equipment slot it would occupy;
- validate whether the selected character can legally equip it;
- calculate the resulting character state without actually committing the equip;
- surface the result directly in the Character Combat Summary.

Acceptance criteria:
- changed stats update immediately;
- unchanged stats remain visually quiet;
- improvements and reductions are clearly distinguishable;
- resistances update when relevant;
- illegal equipment states explain why the item cannot be equipped;
- no second comparison panel is necessary.

This is a critical architectural milestone because the character panel itself is the comparison surface.

### Phase D — Combat Pack prototype

Goal:
- add the new per-character Combat Pack;
- base capacity of 3;
- capacity extensible through Strength;
- items in the Combat Pack remain character-specific;
- items can be moved between Party Stash and Combat Pack while safe.

Research before freezing behavior:
- whether stacks count as one slot;
- how ammunition should behave;
- whether wands with charges require special treatment;
- whether weapons of different physical size should matter;
- exact Strength-to-capacity curve.

Do not overcomplicate V1.

The first useful prototype is simply:

> **Three carried slots that become the character's additional combat inventory.**

### Phase E — Threat-based stash locking

Goal:
- full stash access while safe;
- read-only stash while a meaningful hostile threat is nearby;
- Combat Pack / Quick Slots / equipped items remain usable.

Do not implement this using a single vanilla combat boolean unless testing proves it sufficiently reliable.

Build a test matrix for:
- normal combat;
- combat ending normally;
- Web after all enemies die;
- Entangle after all enemies die;
- Cloudkill or other persistent AoE;
- distant hostile in the same area;
- invisible hostile;
- charmed creature;
- unconscious hostile;
- accidental ally targeting;
- cutscene combat;
- scripted hostility that has not yet engaged;
- summoned enemies;
- save/load during danger;
- area transition immediately after combat.

The player's mental model should be:

> **Enemies are meaningfully threatening us, so the camp/stash is unavailable.**

Not:

> **Some obscure engine bit is currently set to 1.**

### Phase F — Auto-restock

Goal:
- let the player define what each character should normally carry;
- refill missing items automatically from Party Stash when safe.

Start simple.

Example internal representation:

```text
Character: Jaheira

QuickSlot1:
  resource = POTN52
  desired_count = 3

CombatPack1:
  resource = WAND12
  desired_count = 1

CombatPack2:
  resource = POTN14
  desired_count = 2
```

On entering SAFE state:

```text
for each configured slot:
    current = quantity currently carried
    desired = configured desired quantity
    available = quantity in Party Stash

    transfer min(desired - current, available)
```

Important:
- never fabricate items;
- never duplicate charges;
- never silently consume from another character's prepared loadout unless the item is actually in shared storage;
- provide a clean indication when a loadout is partially unfilled.

Later UX can make this much prettier.

### Phase G — Search / filter / query UX

Once the underlying shared stash works, make it pleasant.

Required first:
- search by item name;
- basic category tabs;
- sort;
- selected-character usability filter;
- direct equip from stash.

Then consider:
- "usable by Keldorn";
- "weapons Keldorn is proficient with";
- damage type;
- enchantment level;
- newest acquired;
- value;
- quest items;
- magical vs mundane;
- consumables;
- ammo;
- item source / mod origin for debugging.

Do not bury the core experience under dozens of filters.

The primary flow should stay:

> search → select → see character impact → equip.

### Phase H — Container migration / compatibility

Only after the shared stash is functioning correctly.

Research existing container semantics:
- Bag of Holding;
- Gem Bag;
- Potion Case;
- Scroll Case;
- Ammo Belt;
- mod-added containers;
- stores implemented as containers;
- quest/script checks involving container resources.

The UI goal is:

> **The player should not have to care which bag an item lives in.**

But the implementation cannot simply flatten everything blindly if scripts rely on those stores/resources.

Potential approaches, in order of preference:

1. **Virtual flattening**
   - Leave underlying containers intact.
   - Party Stash query indexes their contents transparently.
   - Player never needs to manually open the bags.

2. **Automatic migration**
   - Move contents into a unified storage representation.
   - Preserve compatibility metadata.
   - Higher implementation risk.

3. **Legacy compatibility mode**
   - Existing bag remains technically usable through a compatibility panel.
   - Avoid unless necessary.

The preferred architecture is likely **virtual flattening**, because it changes the player's experience without aggressively rewriting save-state ownership.

---

## 15. Inventory as a query system

A major conceptual shift in Inventory Redux is:

> **The inventory is not primarily a grid of places where objects live. It is a query interface over objects the party owns.**

The UI should therefore optimize for questions.

Examples:

> Show me every longsword.

> Show me items Keldorn can equip.

> Show me fire resistance gear.

> Show me healing consumables.

> Show me everything we recently picked up.

> Show me what increases Jaheira's AC.

The exact advanced query language is not a V1 requirement.

But the underlying model should not make it difficult to add such features later.

Do not tightly couple:
- item ownership;
- screen slot position;
- presentation order.

The physical slot grid is a **view**, not the canonical data model.

---

## 16. Character comparison is contextual, not intrinsic

An item is not simply "better" or "worse."

Its value depends on:
- selected character;
- existing equipment;
- proficiencies;
- class restrictions;
- kit restrictions;
- attributes;
- active effects;
- dual-wielding setup;
- APR;
- resistances;
- other equipped effects.

Therefore do not attempt to assign simplistic global ratings such as:

> +12 upgrade

Instead show:

> **what changes for this character right now.**

This is why the live Character Combat Summary is central.

If the same sword is selected while viewing:
- Keldorn;
- Jaheira;
- Haer'Dalis;

the preview may look completely different.

That is desirable.

---

## 17. Do not hide important secondary effects

The live Combat Summary will capture numerical changes well, but many items have effects that cannot be summarized as one stat.

Examples:
- Free Action;
- immunity to charm;
- regeneration;
- extra spell slots;
- on-hit effects;
- immunity to level drain;
- casting speed;
- elemental damage;
- dispel-on-hit;
- weapon-specific bonuses.

These belong in **Item Details / Effects**.

If an effect changes a relevant numerical stat, reflect it in Combat Summary as well.

If it is qualitative, do not invent a fake numerical comparison.

Example:

```text
Combat Summary
AC      -7 → -8

Effects
+ Immunity to Level Drain
+ Dispel Magic on hit
```

This keeps the roles clear.

---

## 18. Combat Pack capacity and Strength

This idea is promising specifically because it gives carrying capacity a tactical purpose.

Do not automatically use vanilla encumbrance formulas.

The desired experience is easy to understand:

> stronger characters can bring somewhat more gear into combat.

The scaling should be shallow enough that:
- low-Strength characters remain playable;
- high Strength feels useful;
- the system does not become another min-max tax.

Possible conceptual ranges:

```text
Low STR       2-3 slots
Average STR   3 slots
High STR      4 slots
Exceptional   5 slots
```

or simply:

```text
Base 3
+1 at meaningful Strength breakpoint
+1 at exceptional Strength breakpoint
```

Do not freeze numbers until actual playtesting.

A simple rule players can remember is much better than a mathematically elaborate one.

---

## 19. What happens to ordinary backpack slots?

The current direction is:

> **They disappear as general-purpose storage.**

That is intentional.

Vanilla backpack slots currently serve both:
- storage;
- combat accessibility.

Inventory Redux splits those responsibilities.

Their replacements are:

```text
GENERAL STORAGE
    → Party Stash

PERSONAL IMMEDIATE ITEMS
    → Quick Slots

PERSONAL PREPARED INVENTORY
    → Combat Pack
```

Do not preserve sixteen backpack squares merely because players expect sixteen backpack squares.

If playtesting reveals a missing gameplay function, solve that function explicitly.

---

## 20. Ground loot

Ground/container looting should integrate cleanly with the shared stash philosophy.

Outside danger, preferred behavior:

> loot item → Party Stash.

Avoid forcing the player to choose which character receives ordinary loot.

Potential UI:
- Take
- Take All
- Take & Equip
- maybe Take to Combat Pack

During danger, this needs explicit design.

Possible conservative V1 rule:
- items looted during threat go to the looting character's available carried space;
- if no space exists, looting is restricted.

Alternative:
- newly acquired items enter an inaccessible "pending loot" section until safe.

Research before deciding.

Do not accidentally create magical mid-combat stash access through looting.

---

## 21. Merchants

Merchants should use the shared Party Stash.

The player should not have to:
- move sale items onto the party leader;
- transfer purchases to the eventual user;
- juggle empty backpack slots before shopping.

Preferred flow:

```text
STORE
  Party Stash available as sale inventory.

Buy:
  item → Party Stash

Sell:
  item ← Party Stash
```

Equipment comparison should still use the currently selected party member.

This creates a very strong merchant experience:

> select Keldorn → browse merchant sword → Keldorn's stats preview → buy → Party Stash / equip.

Charisma / reputation / merchant pricing remain separate systems and should not be broken by shared storage.

---

## 22. Identification

Identification should be evaluated separately from storage.

Questions:
- Is unidentified-item discovery meaningful?
- Is repeatedly casting Identify / visiting merchants meaningful?
- Does identification mostly delay access to already-owned information?

Do not automatically remove the unidentified mechanic as part of Inventory Redux.

However, the shared stash should make unidentified items easy to:
- filter;
- find;
- batch inspect;
- identify through whatever final identification system is chosen.

Possible later project:
- identify multiple items in one action if sufficient resources are available;
- retain resource cost;
- remove repetitive UI operation.

Keep this modular.

---

## 23. Multiplayer implications

Inventory Redux affects shared state heavily.

Do not treat multiplayer as an afterthought.

Research:
- who currently owns inventory actions;
- synchronization of item transfers;
- simultaneous equip attempts;
- simultaneous store actions;
- shared stash mutation races;
- two players trying to take the same item;
- combat-pack configuration ownership;
- auto-restock authority.

Likely principle:

> **Host-authoritative inventory mutations, local browsing.**

Browsing/searching/filtering need not be synchronized.

Actual mutations must be.

Examples:
- equip;
- consume;
- transfer;
- sell;
- buy;
- restock.

This may eventually reuse Multiplayer Redux Core.

Solo implementation should not create architecture that makes multiplayer impossible later.

---

## 24. Failure modes to avoid

### Inventory becomes another spreadsheet

If the redesign produces:
- excessive configuration;
- dozens of required filters;
- six complex loadout templates;
- constant warnings;
- constant auto-restock popups;

then the project has failed.

The target is **less interaction**, not more.

### Combat Pack recreates six backpacks

If players spend substantial time micromanaging every Combat Pack after every encounter, the system has failed.

Auto-restock and small capacity exist specifically to prevent that.

### Shared stash becomes omnipotent combat storage

If any party member can magically pull any item from storage while fighting, the preparation layer disappears.

Avoid that unless playtesting proves the restriction is not worthwhile.

### Threat detection creates annoyance

If:
- one distant gibberling;
- a Web spell;
- stale combat music;

keeps the stash locked, the mechanic will feel terrible.

Bias toward unlocking rather than false-positive locking.

### The UI duplicates information

Do not show:
- Character stat preview on left;
- another stat comparison in Item Details;
- another tooltip comparison on the stash item.

One truth, one primary presentation layer.

---

## 25. Acceptance scenarios

### Scenario A — ordinary loot

Player opens a chest.

Clicks Take All.

Items enter Party Stash.

No character backpack management occurs.

### Scenario B — equipment discovery

Player searches:

> sword

Selects Varscona.

Keldorn's Combat Summary immediately shows projected changes.

Item Details explains Varscona's special effects.

Player clicks Equip.

Done.

### Scenario C — preparing for undead

Player selects Anomen.

Combat Pack has 3 slots.

Adds:
- Protection from Undead scroll;
- Wand of Heavens;
- Potion of Extra Healing.

Those choices now matter when the fight begins.

### Scenario D — forgotten potion

Combat begins.

Jaheira needs a Potion of Magic Shielding.

Player presses Inventory.

Party Stash is visible.

Potion can be found via search.

But stash is read-only because hostile threat is active.

Potion was not prepared on Jaheira.

Player now has to solve the situation another way.

That is intentional gameplay.

### Scenario E — combat ends strangely

All enemies are dead.

Web remains active on the floor.

After a short threat-clear grace period, Party Stash unlocks anyway.

Correct.

### Scenario F — auto-restock

Jaheira used two of her three configured healing potions.

Combat ends.

Party Stash contains five.

System silently refills her configured loadout to three.

No drag/drop chores.

### Scenario G — Bag of Holding from an old save

Player loads an existing save with dozens of items in a Bag of Holding.

Inventory Redux does not lose them.

Ideally they simply appear in Party Stash query results without requiring the bag to be opened manually.

---

## 26. Definition of success

Inventory Redux succeeds when the player mostly stops thinking about **where items are**.

Instead, they think about:
- what they own;
- what a character can use;
- what an item does;
- what they deliberately prepared for danger.

A typical inventory interaction should feel like:

> **Search → inspect impact → equip / prepare → leave.**

Not:

> select character → find bag → open bag → transfer item → inventory full → move junk → switch character → compare weapon → transfer it again.

The final experience should make inventory almost invisible during ordinary adventuring while making pre-combat preparation **more** meaningful than vanilla.

---

# Final design principle

> **Storage is infrastructure. Preparation is gameplay.**

Everything in Inventory Redux should be judged against that sentence.
