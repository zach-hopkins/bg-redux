# Phase 1: EE inventory and record assembly

October 21, 2026. This bounded P1-03 change implements missing BG2EE character-sheet assembly. **Native rendered validation is pending coordinator execution.** The fifteen focused tests below establish semantic/binding behavior, not visual fidelity or all-menu completion. No worker game/native process was launched, shared runtime changed, engine binary rebuilt or private fixture altered.

## Root cause and actual change

The retained Phase 0 inventory/record BMPs and control inventories in `20261021T011818Z-gui-stock-verified-fe7b575f/gui-save` show four empty detail areas on each screen, plus empty THAC0/damage labels. Font variants retained identical control-text hashes. `bg2/GUIINV.py` explicitly deferred the EE menu composition. Read-only inspection of the private original `ui.menu` confirms its normal inventory overlay is the **INVSTATS mosaic**, positioned at `(512,44,349,376)`, followed by AC, HP, THAC0 and damage detail text. It is not a missing TLK database and not a BAM overlay.

`EECharacterSheet.py` provides one actual-equipped-state snapshot and panel binding shared by inventory and record. Inventory adds the game mosaic behind existing CHU controls as disabled art; it does not intercept equipment/cursor operations. Both screens populate the previously empty details and headline THAC0/damage values. Main/offhand values remain distinct, fractional APR remains visible, and dead/missing-weapon results clear earlier values. Damage shows physical weapon dice plus the engine's aggregate damage bonus and separate strength bonus; header/launcher/proficiency bonuses are not counted twice. Extra typed/probabilistic damage remains separate in the tooltip. Unidentified weapons/ammunition do not expose damage headers/effects. No target-specific protection or hypothetical equipment outcome is inferred.

The record's secondary **Stats** region has Overview, Skills, Saves, Resists, Weapons and Abilities categories, with bounded previous/next pages for long records. It does not repeat headline attributes, AC, HP, THAC0, damage or APR. Unique ability information (doors, carrying capacity, reaction, HP/level, spell learning), weapon-style modifiers, bonus spells, class progress, status descriptions, skills, saving throws, proficiencies and resistances remain reachable. The old overview scrollbar is hidden; pages retain long lists instead of truncating them. Conservative text wrapping targets no scrolling; actual font fit must be inspected in the rendered candidate, including long/modded names and localization.

## Information and function coverage

| Information/function | Source and current binding | Required native evidence |
|---|---|---|
| Actor name, class, race, alignment, gender and six abilities | Existing ordinary record/inventory assembly retained, including exceptional Strength | Both PCs; base/modified values; dead/polymorphed actor where available |
| AC headline and details | `GetPlayerStat`, existing style-bonus calculation, native AC components and damage-type modifiers | Match runtime snapshot; shield/style change; visible details/tooltips |
| HP headline and details | Current/base maximum, current HP and net maximum adjustment; no invented cause attribution | Wounded/full actor; modified maximum; no value clipping |
| Main/offhand THAC0 | Each hand's native `ToHitStats`; breakdown tooltip | Single/dual hand; equipped change; current selected actor |
| Physical damage, additional effects and APR | Native dice/aggregate bonus/strength; separate conditional damage opcodes; half-attack units | Fist/melee/launcher-ammo; unidentified item/ammo; dual hand; no hidden-effect leak |
| Class progress, statuses, lore, reputation, AI | Stats Overview via existing record queries | Category selection, effect changes and page navigation |
| Skills, saves, proficiencies/styles, resistances, unique ability benefits/bonus spells | Existing record helpers, six Stats categories and bounded pages | All six categories; last/first page bounds; long list remains reachable |
| Equip, unequip, drag/drop, split, ground loot, item information/abilities, color pickers | Existing slot callbacks/transactions retained | Pointer hit testing/drop rollback and keyboard paths; actual state/item conservation |
| Level up, dual class, information, party reform, customization, export, kit description | Existing record callbacks and enabled-state policy retained | Each applicable button opens/closes its ordinary menu, including unavailable states |
| Options/save/load and other game menus | No menu implementation replaced by this slice | Fresh ordinary menu/callback regression and save/reload; usable labels/focus at supported sizes |

This table is a concrete integration checklist, not a declaration that unexecuted interactions passed. Complete all-menu and typography fidelity remains a Phase 1 requirement. This change does not implement Party Stash, Combat Pack, storage-policy changes, player combat knowledge, new rule formulas or a renderer replacement.

## Typography and layout boundaries

The GUI binds actual game font roles: `NORMAL` for prose/details/dice and new category buttons, `STONESML` for the Stats heading, and the existing numeric role for the THAC0 headline. Damage uses `NORMAL`, since a digits-only BAM role cannot represent a full dice expression. Existing heading/menu/art roles remain intact. No generic/system font or private experimental override is substituted, and no commercial font/art is committed.

Prior native evidence identifies game NORMAL as R PostAntiqua Roman, STONEBIG as Benevento and STONESML as AmericanUncial; role names are not proof of correct pixel metrics. Native `TTFFontManager::GetFont` ignores requested style/background; `Font::Print` advances by glyph bitmap width. Those limitations remain outside this GUI-only change and must not be called fixed by choosing a role or finding text in JSON. Fresh captures must judge original artistic character, readability, spacing/baselines, glyph coverage, clipping, button affordances and menus, at 1024×768 and another supported resolution. The record content viewport is 285×188, with at most twelve wrapped text rows per page. Conservative character wrapping is not a font measurement API.

## Observer behavior

The actual `GemRB_GetCombatDetails` export (`GUIScript.cpp:12089–12182`) calls the actor details query, APR lookup, strength bonus and item damage-opcode metadata. It does **not** call `ModifyWeaponDamage`, attack execution or a damage roll. `Item::GetDamageOpcodesDetails` reads effect metadata; it does not apply/roll it. `Actor::GetCombatDetails` (`Actor.cpp:6985`) does write cached ToHit components and weapon proficiency damage bonuses; BG2 `SetBaseAPRandAB` refreshes the ToHit base. This API is not claimed to be a pure immutable read.

The old inventory/record `DisplayAC` path already invokes this query through `GetACStyleBonus`. The EE path replaces that duplicate lookup with the shared snapshot, and `GetACStyleBonus` accepts an optional already-collected details dictionary without changing other callers. Normal single-hand refresh performs one main-hand combat query; dual-hand refresh performs main/offhand/main to restore the same main-hand cache orientation. Record supplemental assembly reuses that snapshot, including an empty/dead result, and does not query it again. Category navigation uses one main-hand query. No `usedLeftHand` assignment, action call, damage application or resource consumption is added; `usedLeftHand` writes in the inspected native code belong to `PerformAttack`, not the export.

Native validation must retain before/after actor/action/target/effect/ammunition/global state across repeated refresh/category/page operations and compare with the stock path. A rendered pause-preserved run alone does not establish hidden RNG-state identity or prove every transitive cache operation harmless. Source inspection finds no rolling call in this exported path, but that is distinguished from direct RNG sampling.

## Focused validation

Command from the UI worktree:

```powershell
& 'C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe' -B -m unittest discover -s redux/tools/phase1/tests -v
```

**15/15 passed**: aggregate damage/no double counting; conditional damage separation; unidentified weapon/ammunition limits; distinct dual hands/fractional APR; unavailable/dead values; refresh after equipment change; noninteractive mosaic composition; retained bounded long records/markup removal; real Stats callback section/page navigation and bounds; initialization before first refresh; supplemental unique information/no repeated headlines; snapshot reuse; exact native query counts and main-hand cache restoration. Tests execute the actual model and record page/callback functions with explicit native/control doubles. They do not launch the engine, sample RNG, verify fonts by pixels or exercise OS pointer/focus paths.

Coordinator must append fresh isolated native build/run results and captures before this slice is accepted as visually usable. Preserve prior baseline reports and actual failures rather than replacing their compatibility verdicts.

## Observed dark-text defect and narrow repair

The retained native inventory image `C:/BGRedux/phase1-local/results/20261022T010029Z-menu-run-bf0932e2/1024x768/capture-1.bmp` demonstrates that JSON content coverage did not establish usability: summary text was black against the dark stat art, with only dim initial letters visible. Its matching `.ui.json` contains populated GUIINV 77–80, each 252×80, so missing data was not the cause. The original `20261021T235241Z-weapon-oracle-ccf85085/original-inventory-case8.jpg` uses readable light serif text. The fixtures intentionally differ; their combat values are not compared here.

Read-only private resource inspection confirms that GUIINV 77–80 and GUIREC 53–56 are TextAreas with body RGB (0,0,0), initial RGB (64,64,64), and both fonts STONESML in the CHU. `CHUImporter::GetTextArea` applies these colors; `TextArea::SetFont(...,0)` changes only body font. Our first adapter changed that body font but retained the black palette and separate dim initial. `StyleTextPanel` now explicitly sets the actual game NORMAL role for both body and initials and ColorWhitish (215,215,215,255) for both foreground slots **before SetText reparses new spans**. Inventory/record summaries and the Stats body use it. Stats heading/page and pagination buttons receive explicit readable colors. No engine font/palette rasterizer, glyph metrics or underlying summary geometry changes.

The original GUIINV headline THAC0 and damage labels are authored as NORMAL in the private CHU. The initial implementation's forced NUMBER BAM for THAC0 was therefore an incorrect role substitution; it now restores NORMAL and explicit light color. AC/THAC0/damage values also receive explicit light label colors. Damage labels no longer reuse TLK 56910/56911, whose actual strings include “THAC0”; they use the same plain hand labels as the rest of this English presentation rather than mislabelling damage as THAC0. The test double now reflects those actual TLK strings.

**17 focused tests passed**, including inherited black-body/dim-initial restoration in both inventory and record before text parsing, retained game roles, existing semantic/query-count tests and actual-TLK damage-label separation. These checks establish the intended style binding; a fresh coordinator render at both resolutions must confirm contrast, full glyph visibility and fit. The failing before-images remain untouched. This repair does not establish overall typography/all-menu fidelity or fix the separately documented TTF advance/bearing limitations.
