# Inventory Redux — GUI designer brief and delivery contract

## Your task

Design the polished visual layer for Inventory Redux, a Baldur’s Gate Enhanced Edition inventory redesign. The project owner will separately provide the desired look, theme, and example images. Use those instructions as the art direction. This document defines gameplay, layout, interaction, and delivery requirements.

Deliver a modular design system and implementation-ready assets, alongside convincing screen compositions. The development team will integrate the design with the existing native game and EEex/Lua prototype. Do not change gameplay or invent functionality to make a mockup attractive.

## Recommended approach

Build reusable components and theme tokens first; compose screens from them. Keep ornamental artwork separate from interactive content and states. A flattened screenshot is useful as a preview, but is not a sufficient implementation deliverable.

Use an editable vector/component source where your tools allow it. Supply transparent raster exports for artwork the game must display. Prefer separate corner, edge, and center assets with specified stretch rules for resizable frames. Specify fixed-size artwork when stretching would damage its appearance. Avoid requiring a web browser, HTML layout, or a new rendering engine to reproduce the design.

## Source material and authority

The owner will supply images and artistic guidance. Earlier reference images express atmosphere and composition, but contain inaccurate or invented text. Use real labels from this brief in final mockups.

The atmospheric reference is `reference/inventory-redux/gui-atmosphere-preview.jpg` in the supplied project. The monochrome wireframe is an earlier design. Current prototype screenshots, if supplied, show functioning controls but provisional artwork. This brief supersedes older references where gameplay differs.

Current decisions:

- Party Stash is always accessible; no danger/combat lock or availability banner.
- Combat Pack has been removed. Do not reserve space for it.
- No separate Primary Weapon slot. The active weapon occupies one of three Quick Weapon slots.
- Every class has three Quick Weapons, three Ammunition slots, and three Quick Items.
- Multiplayer is a later feature; do not design multiplayer management controls for this screen.
- Hypothetical stat preview is planned but is not currently functional. Show proposed comparison states clearly as future states, separately from implemented baseline states.

## Viewport and layout

Design floor: **1280 × 720** viewport, with a **1200 × 660** central inventory panel. At the floor, the panel is centered at x=40, y=30, leaving modest framing around it. Verify readability at this actual size, not only on a large presentation canvas.

The existing implementation scales a common 1280 × 720 logical canvas uniformly to fit larger viewports and centers it. Native paper-doll rendering has separate size constraints. Provide previews at 1280 × 720, 1920 × 1080, and 2560 × 1440. Propose alternate higher-resolution spacing separately if useful; do not assume an arbitrary responsive web layout is already supported.

Use three clear regions: a narrow party portrait rail; a character/loadout region; and a larger Party Stash/Item Details workspace. The current left character workspace is approximately x=128–532 and the right workspace begins around x=544. These are starting proportions, not immutable coordinates. Any proposed geometry change must preserve usable hit targets and fit the 720p floor.

Minimize permanent chrome. No large Inventory heading consuming a full row. A compact overlapping corner X closes the screen. Keep character identity within the paper-doll panel. Decorative borders must not obscure icons, counts, labels, or click areas.

## Design freedom: what you may change

**You are authorized to redesign component geometry. The prototype coordinates are a starting point, not a layout template you must trace.** Keep the 1280 × 720 logical canvas and centered 1200 × 660 panel fixed. You may change the geometry inside that panel without seeking approval for each adjustment.

You may resize item tiles, change grid density/column count, rebalance character versus stash width, change section heights, reorganize quick-slot groups, refine the anatomical slot positions, relocate labels/buttons, and adjust padding, typography, ornamentation, and borders. You may propose tab, overlay, or scrolling treatments for secondary information where they preserve the required behavior. Native character/item artwork must remain separate from the surrounding layout.

These freedoms have the following boundaries:

- Preserve all ten worn slots and all nine quick targets. Preserve their gameplay identities and distinct destinations, even if their positions change.
- Keep the party rail, live search, filters, sort, inspection, quantity controls, Close, and access to Full Stats discoverable. Do not silently remove a capability to make space.
- Maintain the anatomical relationship between equipment and the centered character. The entire equipment panel remains a drop target; stash gaps and empty space remain drop targets.
- Keep interactive targets comfortably usable at actual 720p. Tile size is adjustable; excessively small hit targets or illegible counts are not acceptable. Specify visible bounds and hit bounds separately. Larger hit bounds must not overlap competing destinations.
- Maintain stable equipment/quick-slot geometry across idle, held-item, pending, and Full Stats states. The deliberate stash browsing/inspection transition may change grid height and row count; document it. Avoid layout movement on each individual item pickup.
- Design independent active-weapon, inspected, compatible-drop, unusable, and held-source states. Never merge their meanings because they share a border or color.
- Include room for long names, current/max HP, fractional APR, exceptional Strength, charges, and large stash quantities. Use documented overflow rules instead of baked-in short examples.
- Keep artwork, layout, and theme definitions independent. New dimensions must be supplied as explicit logical rectangles/anchors, not left for the developer to infer from pixels.
- Respect native rendering constraints. Do not assume that enlarging a paper-doll rectangle enlarges the native sprite, or that stretching a slot should stretch its item icon. If a composition needs an engine capability not established here, flag it as a proposal and provide a feasible fallback.

Include a short geometry change log explaining the important choices and their 720p implications. Visual/layout adjustments within these rules are permitted; gameplay changes, a different canvas/panel size, or new engine requirements must be clearly identified as proposals.

## Character and equipment

Center the character model in a portrait-shaped composition. Put name, class/kit, and level within its upper region. Keep equipment slots anatomically arranged around the model, with small subordinate labels:

| Placement | Slot |
| --- | --- |
| Upper left / upper right | Helmet / Necklace |
| Left / right near upper torso | Cloak / Armor |
| Left / right near arms/waist | Gloves / Bracers / Belt |
| Left / right lower torso | Ring 1 / Ring 2 |
| Bottom left / bottom right | Boots / Offhand |

There are ten worn equipment slots. Gloves / Bracers is one slot, not two. Offhand stays distinct from the three Quick Weapon slots.

The entire equipment panel is a forgiving drop-to-equip area. A player should not need to hit the model or the precise intended equipment slot. Show compatible destinations contextually while holding an item; preserve clear individual targets for explicit choices such as rings and weapons. Do not add opaque decorative layers that intercept clicks.

Below equipment, group nine square targets:

```
Quick Weapons         Ammunition           Quick Items
 [1] [2] [3]           [1] [2] [3]           [1] [2] [3]
```

Prioritize readable item icons and quantity overlays over verbose slot captions. Maintain icon aspect ratios: a shield, potion, wand, and sword must not all be stretched into the same silhouette. The active Quick Weapon must have a distinct marker, separate from hover, inspection selection, and compatible-drop highlighting. Successfully placing or replacing a weapon activates that slot. Picking a weapon up and returning it to its own slot also activates it.

## Character statistics

Keep a fixed character-information region so controls do not move under the pointer. Default state shows **AC, THAC0, Damage, APR, HP**, visually emphasized, plus compact attributes:

```
STR  DEX  CON
INT  WIS  CHA
```

Allow exceptional Strength and unfamiliar/modded values without overlap. Damage may be a range; APR may be a fraction; HP should fit current/max values.

Full Stats is an explicit toggle/pinned view within the same region, scrolling if needed. Start with saving throws and resistances because headline stats are already prominent in the default view. Include saves vs Death, Wands, Polymorph, Breath, and Spells; elemental resistances; physical Slashing, Crushing, Piercing, Missile; Magic Resistance; and casting information. Unknown or inapplicable data must have a clear neutral presentation, such as N/A. Do not invent a universal casting-speed value.

Future held-item comparison replaces default information with affected-stat rows only, using current → projected values. A pinned Full Stats view stays expanded and highlights changes instead. Show improvement/reduction using both visual indicators and color; lower AC/THAC0/saving-throw values can be improvements. Do not assume “higher is better” for all numbers. Supply neutral, improved, worsened, unavailable, and no-change styles. Clearly mark these comparison mockups as planned functionality.

## Party Stash and details

Keep one clear Party Stash title, a generous live-search input, category filters, sort control, and compact pagination. No separate Search button or “Party Stash available” line. Use real categories: All, Weapons, Armor, Potions, Scrolls, Quest, Misc.

Browsing: the stash fills the right workspace. Inspecting: a consistent Item Details panel appears below, and the grid contracts. Avoid changing the details height for each item. Current prototype shows seven columns, six rows while browsing (42 cards), and three rows while inspecting (21 cards). A different density can be proposed, but preserve readability and distinguish it from the current implementation.

The entire stash rectangle accepts a returned item, including empty cells and gaps. Show an appropriate drop state for the panel as a whole.

Item Details must accommodate a real item name, icon, type, relevant equipment slot when useful, charges or quantity, requirements/usability, description, and effects. Avoid inventing item bonuses. Include a visually secondary exact-quantity control for stacks: minus, editable quantity, plus, and Pick Up [quantity]. It is part of Details, not an ordinary-transfer modal.

Stash quantity can exceed equipped stack limits and reach multiple digits. Charge counts and total quantities are different concepts. Design their presentation so a wand’s charges cannot be mistaken for a potion stack count.

## Interaction and state requirements

Native-style click-to-pick-up/click-to-place is the primary interaction. Pointer artwork becomes the held item icon; there must be one visually aligned click position. Preserve icon aspect ratio and give the held count a clear anchor. The source shows a ghost while held.

| Input | Behavior |
| --- | --- |
| Left-click | Pick up / place the largest legal amount |
| Shift + left-click | Half of the applicable legal quantity, rounded up |
| Ctrl + left-click | One |
| Right-click | Inspect without transfer |
| Escape | Cancel / return held item safely |

Installed native stack limits govern equipped stacks. Stash aggregation may be larger. Partial placement leaves the remainder held and updates both counts immediately after native acknowledgement.

Replacing a weapon places the new one in the destination, activates it, and returns the displaced weapon to Party Stash. Preserve a temporary stash card at the incoming item’s previous visible position so reversal is easy, even if filters would normally hide it.

Design distinct states for empty, occupied, hover, inspected, active weapon, compatible target, incompatible/unusable, held source ghost, transaction pending, and actionable recovery. Incompatible items have a clear red treatment plus a non-color cue. Pending visuals must not pretend that an unacknowledged transfer succeeded. Recovery messages should fit a small status region without moving the layout.

## Deliverables

Provide the package using this structure or an equivalent clearly documented mapping:

```
inventory-redux-design/
  README.md
  source/                 editable layered/component source
  tokens/theme.json       colors, typography, spacing, borders, state styles
  layout/layout.json      logical rectangles, anchors, hit areas, scaling rules
  components/             reusable component specifications
  assets/frames/          corners, edges, centers; stretch/slice guidance
  assets/surfaces/        textures and panel backgrounds
  assets/controls/        tabs, buttons, toggles, state overlays
  assets/icons/           custom UI glyphs; native item artwork stays dynamic
  previews/               complete compositions at required resolutions
  integration.md          asset-to-component map and implementation notes
  asset-manifest.json     file names, dimensions, intended use, license/source
```

Use meaningful names; never bake character names, item names, quantities, or stats into background art. Prefer RGBA PNG for raster assets, editable SVG/vector originals where practical, and documented optional high-resolution variants. Fonts need names, sizes at the logical floor, fallbacks, and redistribution/license information; do not assume arbitrary external fonts can be loaded by the game. Final game resource conversion is the developer’s responsibility.

Theme tokens should separate semantic roles from literal colors, for example `surface.panel`, `text.primary`, `text.muted`, `border.frame`, `state.activeWeapon`, `state.compatible`, `state.unusable`, `stat.improved`, `stat.worsened`. Include alpha, line widths, texture references, and text-shadow guidance where needed. A new theme should replace tokens and assets without rewriting inventory logic.

For each component provide its logical bounds, content bounds, safe padding, label behavior, overflow/truncation rules, hit area, states, layering, and asset references. Mark what scales uniformly, what tiles/stretches, and what keeps a fixed size. Use one coordinate system and specify its origin.

Required compositions: browsing; item inspection; item held with compatible targets and ghost; unusable items; active weapon plus inactive weapons; successful replacement/reversal card; Full Stats; and future affected-stat comparison. Use identical control geometry across these states except the deliberate browsing/inspection grid change.

Include a state contact sheet and a clean annotated 720p layout with dimensions. Supply at least one long-name example, a large stash quantity, a narrow/tall item icon, and a character with substantial stats. Do not use tiny text simply to make the screenshot fit.

## Separate future action-bar work

Do not spend inventory-screen space on the bottom action bar. It is a related, separate deliverable if the owner requests it. Preserve UI++ ordering and direct class-action access. The proposed hybrid row contains **15 controls**: Talk; Quick Weapons 1–3; three direct thief/class actions; Cast Spells; Item Ability; Quick Items 1–3; two bindable quick-spell actions; Innate Abilities. This is +1 weapon control and +2 spell-binding controls relative to the supplied 12-control hybrid example. Class-specific rows will require separate mappings.

For V1 the two bindable controls use quick-spell-like assignment/casting only. Do not portray arbitrary innate, item, or class-ability binding as implemented. Keep the inventory and action-bar theme compatible without combining their implementation scope.

## Completion criteria

The result must read well at actual 1280 × 720; preserve nine quick targets and ten worn equipment targets; keep the paper doll centered; differentiate active, inspected, and compatible states; maintain stable interaction geometry; and arrive as editable source plus individual assets and integration specifications. Explain any deliberate geometry changes or engine assumptions. The owner’s artistic instructions determine the look; this contract determines whether the package can be integrated and maintained.
