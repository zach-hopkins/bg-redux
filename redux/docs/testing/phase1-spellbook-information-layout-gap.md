# Spellbook known-name and persistent information gap

Status: **confirmed missing screen information; source-only investigation, no production repair applied here**. The repaired heading is readable, but ordinary spellbooks still omit persistent known-spell names and the inline help/description panel. This remains P1-03/P1-06 work under the approved modern UI scope. Functional icon/heading checks do not close information-completeness or visual fidelity.

## Bound observations

Original `20261022T082351Z-original-spellbook-installation-4de00a9c/original-mage-level1.jpg` shows Imoen's four known spells as vertical icon-and-name rows, plus persistent memorization/rest help on the right page. Its SHA256 is `a28ca9f325d02d9b9195a3462195ada60c19248f4f0c721b9504bd655614b5da`.

The new candidate's completed 1024×768 stage at `20261022T095203Z-sb-menu-run-bc1642be/native/20261022T095208Z-menu-run-266c1980/1024x768/` passes its existing menu assertions, including both headings. Static inspection of capture 23 (Imoen, wizard level 0) and capture 25 (Jaheira, priest level 0), together with their native UI/state JSON and runtime contracts, confirms:

| Content | Wizard | Priest |
|---|---|---|
| Actual known entries | Armor, Chromatic Orb, Identify, Magic Missile | Armor of Faith, Bless, Cure Light Wounds, Detect Evil, Doom, Entangle, Shillelagh |
| Known controls 27+ | Icons in a grid; each control's text is empty; names exist only in tooltips | Same omission, across seven populated icons |
| Visible body text | Only level/known headings and actor name; no inline help/description | Same omission |
| Repaired heading | Memorized 4/4, readable | Memorized 5/5, readable |

The captured GUIMG/GUIPR window 2 controls have only button/type 0 and label/type 6 entries; no body text-area control is assembled. Both right parchment regions remain empty. These selected captures establish this gap without claiming acceptance of the still separately managed whole two-resolution run. The original eligible-priest runtime has not been captured: priest parity here is source-supported, while the saved original priest image is ineligible Imoen and supports layout only.

## Source/resource explanation

Current `GUIMG.UpdateMageWindow` and `GUIPR.UpdatePriestWindow` build sorted `(known spell, original index)` records, then set icon, localized tooltip and callbacks on CHU buttons 27+. They do not assemble persistent name controls or an inline help/description control. `GetGUISpellButtonCount` retains a fixed 24-control assumption for these games. Existing spell information is available through a right-click modal using `GetSpell(...)["SpellDesc"]`; that modal does not supply the missing persistent page information.

The locally extracted shipped resources bind the intended information:

- `ui.menu:7986–8017` defines mage icon/name columns, localized names through the spell name reference, `normal_parchment` styling, row height 40 and a scrollbar. Normal on-open handling at 7839–7846 changes its list to `(112,186,302,384)`; the description becomes `(448,186,322,384)`.
- `mageBookDescription` at 7565–7584 returns the selected spell's description, or `SPELL_MEMORIZATION_HELP` when no ordinary row is selected. The information control is at 8131–8138.
- Priest list/name assembly at 8723–8753 uses `(82,182,326,370)`, row height 40 and a scrollbar; the description at 8773–8779 uses `(438,182,340,370)`. `priestBookDescription` at 8508–8517 similarly selects description/help and returns empty text for an unavailable book.
- `bgee.lua:2857–2865` defines `normal_parchment` as NORMAL, point 12, top/left alignment, color 5; color 5 at 2819 is opaque black. `SPELL_MEMORIZATION_HELP` is a **localized UI-language string**, not heading strref 11944: English `L_en_US.lua:692` contains the rest/memorization guidance and the Sorcerer/Shaman exception. Do not substitute a hardcoded English sentence or assume it is a TLK heading reference.

Resource SHA256s: ui.menu `7987e9d38c9a1d8f4df949d880f260ad5a76dd623d08c7e7be6f0f6c8f2931fe`; bgee.lua `0c368dc8f82730e1f3b0c42f209f1e10b00733e59f15001bbde28f2064bb97e0`; L_en_US.lua `9e8467d26c1e1a889eb916b678cf293475a06933020bdbae55ab18feec44ca62`. All selected resources resolve through clean Patch2.bif in this bounded KEY/BIF reader. This is not a complete runtime resource-precedence proof.

Absent label/text assembly is sufficient to explain these missing names/help. The screenshots do not justify a global font replacement, advance/baseline correction or renderer rewrite. NORMAL role metadata and actual provider/metrics must still be checked during a repair; role selection alone does not prove the original's point/pixel correspondence.

## Separate selection and memorization route

The original operator record `original-wizard-operation-observation.json` observes known Stinking Cloud selection followed by the separate Memorize button, restoring the visible count from 2/3 to 3/3. This is bounded wizard operation evidence; it does not measure an eligible priest operation or every original state gate.

Shipped `ui.menu:8018–8039` distinguishes mage icon cell 1, which immediately calls Memorize in ordinary book mode, from name cell 2, which selects/deselects without memorizing. The separate button at 8218–8239 requires a selected row and spare capacity, is enabled for an eligible mage book (or its separate sequencing mode), and passes the selected spell's original level/index. Priest cells at 8755–8768 and the button at 8843–8860 follow the same distinction; the priest button additionally requires `hasClericBook`, with capacity from `maxMemorized`.

Current native known-icon left press calls Memorize directly. That shortcut also exists in the original. The missing interaction is the information-only name selection followed by a separate, gated Memorize action; adding visible names/help alone would not restore it. Approved modern presentation does not establish original action parity for a replacement gesture. Preserve explicit ordinary versus sequencing/spontaneous gates rather than copying one action into every book mode.

## Upstream context and index boundaries

The saved October 22 upstream snapshot includes both complete two-comment discussions. [#2230](https://github.com/gemrb/gemrb/issues/2230) was closed 2024-12-27 after proposing Classic GUI transplantation. Its [specific spellbook list](https://github.com/gemrb/gemrb/issues/2230#issuecomment-2555739383) mentions placement, BAM centering and Shaman behavior; the [conclusion](https://github.com/gemrb/gemrb/issues/2230#issuecomment-2563678174) favors direct repairs over a wholesale Lua implementation. Its functional threshold does not waive Redux's visible information/typeface requirements. Neither transplanting Classic assets nor implementing the entire original Lua GUI is necessary to fill this bounded gap.

[#2494](https://github.com/gemrb/gemrb/issues/2494), closed 2026-05-09, reports displayed spells selecting different entries; its [comments](https://github.com/gemrb/gemrb/issues/2494#issuecomment-4406954733) identify recent known-name sorting and confirm Classic BG2 reproduction too. This is related index-risk context, not proof that the current missing-name defect is the same bug. The current Memorize route uses original known index through `btn.Value`; the separate name-permutation journey validates that bounded operation. New rows must retain `(actor, book type, level, resref, original known index)` independently of sorted position and scroll offset. Duplicate localized names cannot become identity keys.

A separate source risk remains: wizard update stores `spell['CurrentIndex']=i` as display index; the info→Erase callback passes it through `OpenMageSpellRemoveWindow` to `GemRB.RemoveSpell`, which expects a known index. This investigation does not reproduce that route or approve a fix; it must not be assumed covered by Memorize's permutation evidence. Prepared-entry indices, known-entry indices and displayed sorted order also remain distinct.

## Narrow implementation options

**Reference-shaped rows and right information panel (preferred first slice).** Reuse existing known spell callbacks/icons and add adjacent localized name/select controls in a vertical list. Use a bounded visible row pool plus an ordinary scrollbar or explicit paging so all known entries remain reachable, rather than stretching 24 rows into the parchment or silently truncating them. Preserve original indices on recycled controls. A name selection updates the right description without memorizing. Add the separate selected-row Memorize button with eligibility/capacity/selection gates; preserve the existing icon shortcut, matching the reference's distinct text/icon cells. Show localized help when nothing is selected, and preserve the existing right-click information modal and prepared-row behavior. This needs GUI assembly/read-model work, not an engine renderer seam.

**Approved modern arrangement with equal information.** A compact card/list arrangement may differ from original coordinates, but must keep names persistently readable, expose selected spell description/default help, retain all entries through navigation and preserve action/index semantics. Tooltips alone or an empty decorative parchment do not satisfy this option. Retain the game's body font role; a generic replacement does not meet the typeface requirement.

Both options should share ordinary wizard/priest data/layout logic where practical and invalidate selected-row information on actor or level changes. Do not reuse stale row closures for another actor/page. Sorcerer window 8, Shaman spontaneous books and sequencer/contingency layouts have distinct controls/counts/actions and need separate context contracts; do not add memorization to them or declare their layouts complete. Keep Classic behavior untouched in the first BG2EE slice. Localized UI-language help needs a safe, explicit data mapping/reader or translatable resource path, not arbitrary execution of Lua or English-only fallback.

## Acceptance before claiming repair

1. At 1024×768 and 1280×768, capture real Imoen wizard and eligible Jaheira priest pages before hover: each visible icon has its localized persistent name, information/help text is readable, the prepared row and repaired heading remain unobstructed, and every known entry is reachable. Include long localized names/descriptions, empty pages and more entries than one visible page; retain explicit bounds beyond the existing 24-control assumption.
2. Validate native actor/level/type, actual name/help/description text, visible control rectangles and row-to-resref/original-index bindings. Selecting a name changes information only; the separate Memorize button applies only to that selected identity and is unavailable without selection, room or an eligible book. Exercise both that route and the icon shortcut, plus prepared Unmemorize, through actual registered callbacks and the measured policy. Preserve existing source/provider/nonce/world guards and extend the existing menu oracle for paged/hidden rows rather than weakening it.
3. Rerun stock and declared nonidentity-name controls through actual operations and frozen GUI save/fresh reload. Confirm the targeted resref and duplicate/prepared order changes, unchanged unrelated entries and no cross-actor/page mutation. Known-spell erasure requires its own explicit context/test; do not infer it from these results.
4. Reset selection/help correctly on actor, level, scroll and availability changes. Verify no stale description, inaccessible final page, overlap, clipped long text or unintended spontaneous-book action. Use existing public control observations and rendered QA; per-label font/color assignment remains unobserved by the current native seam.

Private source/hash/control report and reproducible resource readers: `C:/BGRedux/phase1-local/results/20261022T095920Z-spellbook-information-gap-468c30da/report.json`, SHA256 `e03d53f3d95319450c3becba287e5b31bc6868cd235413b0315e39ed44f0dc86`. It binds both captures/UI/state records, the runtime contract, five GUI source files, the original operation observation and the saved upstream snapshot. No tests, builds, native/UI launches or engine/helper source edits were performed for this investigation.
