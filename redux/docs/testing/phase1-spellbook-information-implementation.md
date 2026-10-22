# Ordinary BG2EE spellbook information slice

Status: **production source candidate, not executed or visually accepted**. This implements the first ordinary memorizing-book slice of the [information/interaction defect](phase1-spellbook-information-layout-gap.md). It does not close P1-03/P1-06, all spellbook layouts, typeface metrics, non-English fit or campaign fidelity. The coordinator owns coherent build, tests, actual callbacks, original comparison and both-resolution QA.

## Information and actions

New shared `EESpellbookInformation.py` is called after existing GUIMG/GUIPR known-spell enumeration/localized sorting. It handles ordinary BG2EE books only. Seven existing known icon controls (27–33) are reused as vertical icon/name rows; remaining old grid icons are hidden. The full known list remains in the read model, with actual previous/next page buttons and a visible page/range/total counter. There is no 24-entry truncation and no extra spell allocation. Names are persistent wrapping NORMAL buttons, not tooltip substitutes. The selected row is visibly distinguished by its text color, with its full localized name repeated in the scrollable description.

Name left-press selects/deselects information without calling a spell operation. It shows the selected full localized description, or the **whole configured-language TLK 39254 paragraph** when no row is selected; an ineligible book shows empty help. Missing/empty 39254 fails explicitly. This is the accepted existing-API alternative documented by the [localization investigation](phase1-localized-spellbook-help-source.md), not an exact reproduction of every locale's `SPELL_MEMORIZATION_HELP` Lua literal. No English-only fallback, substring extraction, Lua parser or new native API is added.

The separate action uses complete existing localized labels 17189/17224 (Mage/Priest spell memorization), because a standalone equivalent is not present in the measured TLK. Actual full label fit still needs native verification. It enables only for selected, live, eligible ordinary known identity with available capacity. The icon retains its legitimate immediate Memorize shortcut; at capacity it does not dispatch a mutation. Both routes delegate to the existing ordinary Memorize function using the row icon's original index, preserving its operation/sound/animation/update path. Right press on either icon or name opens the existing information modal, supplying the original index for wizard Erase. Prepared-row callbacks and heading/count/capacity calculations are unchanged by this slice.

## Logical geometry and font roles

All positions are relative to the existing BG2EE window; no window resize, renderer rewrite, generic font substitution or stock MOS stretch is introduced.

| Surface | Logical frame / behavior |
|---|---|
| Seven known icons | x112, y228 + 42×row, 44×40 |
| Corresponding names | x166, same y, 248×40; NORMAL, black on parchment, blue when selected |
| Known paging | up x112 / down x390, y530, 24×24; GUISCRCW stock up/down frame mapping |
| Page/range counter | x142, y530, 240×24; NORMAL |
| Separate action | x112, y566, 302×28; STONESML, light text on a dark opaque button region |
| Full information | x448, y198, 322×338; wrapping NORMAL, transparent background, black normal/initial colors |
| Information scrolling | up x714 / down x746, y542, 24×24; actual TextArea ScrollDelta callbacks, stock GUISCRCW arrows |
| Existing lower surfaces | heading starts y598; prepared row starts y644; neither is moved |

Information up/down buttons use the existing TextArea public scrolling API (positive content-origin delta moves toward top, negative toward bottom), so long descriptions/help are not reduced to their visible prefix. Native wrapping, actual scroll extent, hover/wheel behavior, page arrows, contrast, font providers/role metrics and long translated names/action labels must be inspected before acceptance. A seven-row source fixture is not pixel equivalence with the original's list.

## Identity, contexts and excluded books

Rows carry `(party handle, spell type, level, resref, original known index, localized name)`, independently of sorted position and page offset. Every interaction checks current selected party handle/name, actual level, ordinary-book eligibility, live known entry at that original index, active window and render generation. Old closures cannot act after repaint, paging, window reset or context change. Context/known-order changes clear selection and reset the page; paging clears selection and restores default help. Same-name spells keep separate original identities. Counts/capacity are checked live before mutation, including an already-enabled button whose world context changed. This uses existing Python party handles and window generations; it does not claim a new native global-ID/lifetime observation API.

Initialization resets the bounded per-pack panel owner. New controls can be reused on a retained window without duplicate allocation. On switching to a spontaneous priest book, helper controls are hidden, ordinary selection is discarded and original CHU known frames/flags/locked state are restored before existing assembly continues. Returning to an ordinary book starts fresh. Classic, separate Sorcerer and sequencer/contingency assembly are not replaced. The existing separate Sorcerer charge display remains its own implementation; no Shaman capacity or memorization policy is invented.

The touched wizard source retains the coordinator's original-index correction (`3f5cad097`) in its legacy known-row loop. The current BG2EE direct prepared-removal condition is preserved from root as a prior change, with its documented **observed option-off scope**; this commit does not fix More Confirmation Prompts or same-resref depleted preference. The separate option helper/consumer work remains independent.

## Verification sources and pending runtime gates

Thirteen new resource-free helper test methods exercise selection/deselection without mutation, separate/icon delegation, live capacity/eligibility/death/spontaneous gates, all 31 known identities across five pages, stale closures, actor/level/storage changes, Classic no-op, spontaneous hide/restore, localized help/full description plus real scroll callbacks, explicit missing-help rejection, priest action/identity, retained/closed window reuse, empty pages and duplicate names. Four existing identity-order tests now execute the actual new rendering/binding helper rather than an obsolete loop: identity, reversed, original-index-2-first and rotated orders. They independently check resref→original-index through both actual info closures and immediate actions. No source-expression assertion or copied binding algorithm is used.

These **17 test sources are unexecuted by the worker**. Coordinator examples from the integrated checkout:

```powershell
python -B -m unittest discover -s redux/tools/phase1/tests -p test_ee_spellbook_information.py
python -B -m unittest discover -s redux/tools/phase1/tests -p test_spellbook_known_info_index.py
```

Before acceptance, freeze the helper as part of the source/import closure and build a coherent candidate. Rerun real ordinary wizard and eligible priest menus at 1024×768 and 1280×768; bind actor/level, persistent row text, actual selected description/default help, page/count, original index and actionable control rectangles. Exercise actual name select/deselect (world unchanged), icon and separate Memorize, info→Erase→Cancel/Confirm, prepared removal under its declared option policy, stock and explicit name permutation, GUI save/fresh reload and all preservation guards. Retain any layout, API, identity or operation failures as failed receipts. Paging beyond 24 needs a declared native input with those genuine known entries before native reachability is claimed; the 31-entry fake test alone establishes only source behavior.

No worker tests, compiler, engine/game process or UI input were launched. Full native/font/localization/interaction fidelity remains pending, including spontaneous/Classic regression contexts outside this ordinary slice and original Erase parity.
