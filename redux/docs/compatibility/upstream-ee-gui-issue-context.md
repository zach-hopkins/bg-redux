# Upstream EE GUI issue and discussion context

Retrieved October 22, 2026 UTC from `gemrb/gemrb` using the connected GitHub
reader. The exact label is **`game: ees`**. The all-state search returned 55
issues: 18 open and 37 closed. All 55 issue records and their complete comment
lists were retrieved; the 132 returned comments match the reported counts.
The index below catalogs the full result set. The detailed synthesis focuses
on GUI, fonts and the ordinary operations most relevant to Phase 1.

This is upstream context, not a report that every issue reproduces in our fork.
Additional [dialogue and conversation discussion](upstream-dialogue-issue-context.md)
reviews four related issues outside the label and all fifteen of their comments.
Closed can mean resolved, superseded, or not reproducible; open can include
partially implemented work. Issue state alone does not establish whether a fix
exists in our pinned source, whether it was backported, or whether our tests
cover the original trigger. Recheck source and reproduce before editing.

The [structured snapshot index](evidence/upstream-ee-issues-20261022.json)
preserves issue state/reason, dates, exact labels, counts and every comment URL.
Private full connector responses are retained at
`phase1-local/results/20261022-upstream-ees-context/connector-snapshot.json`,
SHA-256 `50a82b03ab5402ae69433c00cb0095df6abf31285a5a0549e4e3dbbd8f1bc536`.
Attachments/videos are linked upstream; they were not downloaded or independently
played by this review. Some connector comment timestamps are unavailable, so
issue update dates must not be presented as individual comment dates.

## Findings that affect current work

### Font selection, decoding and scaling are separate problems

[#1924](https://github.com/gemrb/gemrb/issues/1924) is a useful example of the
discussion changing the diagnosis. Initial replies considered BAM character
indexing; later replies identified archived TTF resource discovery, and the final
reply moved the remaining character-display problem to #1929 after TTF loading
worked. [The resource-discovery comment](https://github.com/gemrb/gemrb/issues/1924#issuecomment-1747566118)
and [follow-up split](https://github.com/gemrb/gemrb/issues/1924#issuecomment-1766187182)
are better context than treating its initial title as a current diagnosis.

[#2490](https://github.com/gemrb/gemrb/issues/2490), closed, revisits font
selection: [the maintainer explains](https://github.com/gemrb/gemrb/issues/2490#issuecomment-4364499196)
that the BAM preference flag protected icon/state fonts, while explicitly
selecting TTF for text is appropriate. Preserve icon font exceptions; a blanket
BAM-to-TTF substitution is not justified.
[#1929](https://github.com/gemrb/gemrb/issues/1929) and
[#2478](https://github.com/gemrb/gemrb/issues/2478), both closed, separately concern
UTF-8 display, dashes, accented text and missing sections. The
[UTF-8 experiment](https://github.com/gemrb/gemrb/issues/2478#issuecomment-4345346220)
improved some text while making other sections disappear. Decoding, resource
selection, control styling and glyph layout need separate regressions.

[#2536](https://github.com/gemrb/gemrb/issues/2536), open, records EE 2.7
language/font-dependent button scaling: Japanese/Chinese examples use a factor
of 2; Korean/Russian examples use 1.6. The reported reverse engineering is
button-specific, not a reason to enlarge every control. The report also contains
a discrepancy between its Ukrainian configuration example and the font tested
by its pseudocode; verify the actual installation before implementing a table.
[#2537](https://github.com/gemrb/gemrb/issues/2537), open, tracks the independent
live font zoom setting and options slider. Neither English fixed-size captures
nor our CRT locale test fixture validates these features.

Our [missing-panel/font investigation](../testing/gui-save-and-presentation-results.md)
and [spellbook heading layout trace](../testing/phase1-spellbook-heading-layout-gap.md)
remain distinct. Actual TTF use is already observed in LAB; that does not prove
correct per-control face, point size, contrast, placement or non-English scaling.

### Spellbook appearance does not prove spell operations

[#2230](https://github.com/gemrb/gemrb/issues/2230), closed, originally proposed
copying Classic GUI resources into EE. Its discussion instead concludes that
remaining screens can be repaired directly. The
[concrete spellbook list](https://github.com/gemrb/gemrb/issues/2230#issuecomment-2555739383)
names control placement, BAM centering and shaman unmemorization; the
[later conclusion](https://github.com/gemrb/gemrb/issues/2230#issuecomment-2563678174)
also acknowledges the missing inventory panel. This supports inspecting missing
EE assembly without requiring a wholesale Lua GUI implementation. It does not
override our own information-completeness and fidelity requirements.

[#2494](https://github.com/gemrb/gemrb/issues/2494), closed, reports a displayed
spell selecting a different memorization entry. The
[discussion](https://github.com/gemrb/gemrb/issues/2494#issuecomment-4406954733)
points to recently introduced known-spell sorting, with reproduction also
reported in Classic BG2. Our populated caster checks bind the displayed slots
to expected resrefs and original indices, but they do not execute each
memorize/unmemorize callback. Add actual operation and saved-spellbook checks;
do not declare this upstream report covered by icon presence alone.

[#2298](https://github.com/gemrb/gemrb/issues/2298), closed, reports arrows changing
the spells while leaving the level tab wrong, plus a black rectangle.
Tab clicks, arrow navigation, shown level and selected tab must agree.
Our faint priest heading has an obsolete CHU position/style; no evidence here
establishes that it is the same cause as the historical rectangle.

### Inventory drag, equipment legality and previews need their own cases

[#2232](https://github.com/gemrb/gemrb/issues/2232), closed, records EE equipped
slots rejecting items. Its [follow-up](https://github.com/gemrb/gemrb/issues/2232#issuecomment-2543111924)
identifies an EE itemtype table whose meaning/layout differs from the internal
mapping. Inspect provider/table interpretation before changing slot IDs.

[#2317](https://github.com/gemrb/gemrb/issues/2317), open, reports EE allowing
stored two-handed and one-handed/offhand loadouts together where GemRB rejects
the offhand. Separate stored loadout legality from the actually active weapon.
Our SetSlotItemRes cache regressions are not physical drag/slot-admission parity.

[#2450](https://github.com/gemrb/gemrb/issues/2450), open, records portrait
highlights during item dragging and reverse-engineering notes about scratch
actor equipment and STATVAL scoring. These notes are an upstream research lead,
not measured original behavior in our fixture. Do not present current actor
stats as a hypothetical preview or assume query/RNG purity. The older Inventory
Redux preview research is relevant, but it does not prove this runtime path.

[#240](https://github.com/gemrb/gemrb/issues/240), open, discusses scroll pickup
images, Classic hardcoded folded frames, and EE assets that provide extra
cycles. [The EE scroll example](https://github.com/gemrb/gemrb/issues/240#issuecomment-534934067)
and later Classic confirmation distinguish asset versions and engine behavior.
Test held-cursor images and cancellation separately from item ownership.

### Modal input, quick loot and save/load need behavioral checks

[#848](https://github.com/gemrb/gemrb/issues/848), open, concerns stacked modal
windows and event blocking only below the modal. The
[later implementation note](https://github.com/gemrb/gemrb/issues/848#issuecomment-864455331)
says stacking was added in e3c4460 but leaves sufficiency uncertain. Test nested
modal close/cancel, tooltip/cursor routing, portrait/options access and blocked
world input. Our stale transparent-buffer correction does not certify these.

[#2301](https://github.com/gemrb/gemrb/issues/2301), open, reports missing Quick
Loot. A [later comment](https://github.com/gemrb/gemrb/issues/2301#issuecomment-4110497351)
describes routing the button to GemRB's merged visible-loot container. Verify
both the actual installed callback and conservation/ownership across multiple
piles. Our single-table SW1H04 journey is narrower.

[#2324](https://github.com/gemrb/gemrb/issues/2324), open, concerns a GUI quickload
entry and includes proposed code; the proposal is not accepted runtime evidence.
[#2299](https://github.com/gemrb/gemrb/issues/2299), closed, concerns quicksave
latency/stuttering; the [final disposition](https://github.com/gemrb/gemrb/issues/2299#issuecomment-3189857745)
is non-reproducibility, not proof of a performance correction. Our ordinary
GUI save/reload assertions do not measure quicksave latency or frame pacing.

[#1777](https://github.com/gemrb/gemrb/issues/1777), closed, discusses Windows DXT
artifacts and a platform-width-dependent bit mask. It is a separate rendering
mechanism from stale window-buffer contents. Do not combine unrelated alpha
symptoms into one fixed issue.

## How this changes the Phase 1 queue

1. Before a GUI correction, check this index and linked discussion, compare the
   relevant upstream source change to our pin, and retain a local reproduction.
2. Prioritize spellbook operation/level-navigation coverage alongside the visible
   heading repair; maintain original spell identity across sorting and saving.
3. Keep font provider, UTF-8, layout/style, live zoom and language-specific button
   scaling as separate checks. Do not solve the heading with a global font change.
4. Extend ordinary journeys to modal input/cancellation, drag legality, cursor
   visuals, quick loot, quickload and measured quicksave performance.
5. Carry worldmap/transition/save issues into campaign checkpoints; an opening
   recruitment and successful local reload do not establish those paths.

The full [Phase 1 backlog](../roadmap/phase1-backlog.md) and latest user decisions
remain authoritative. Upstream discussion is a source of cases and hypotheses,
not permission to weaken local requirements or automatically cherry-pick fixes.

## All labeled issues at retrieval

| Issue | State | Comments | Last updated (UTC) |
| --- | --- | ---: | --- |
| [#2536 EE: hardcoded font scaling for select non-English languages](https://github.com/gemrb/gemrb/issues/2536) | open | 0 | 2026-09-25 |
| [#2537 EE: live font scaling](https://github.com/gemrb/gemrb/issues/2537) | open | 0 | 2026-09-25 |
| [#240 [bug] BG2 Some wizard and priest scrolls do not fold when moving them in inventory](https://github.com/gemrb/gemrb/issues/240) | open | 12 | 2026-09-09 |
| [#2498 BG2 EE: Can't leave Waukeen's Promenade](https://github.com/gemrb/gemrb/issues/2498) | closed | 2 | 2026-08-04 |
| [#2492 EE: Damage message placeholders are not fully populated](https://github.com/gemrb/gemrb/issues/2492) | closed | 1 | 2026-06-30 |
| [#2444 EE worldmap updates often do not persist](https://github.com/gemrb/gemrb/issues/2444) | closed | 1 | 2026-05-31 |
| [#2321 Replace libvlc with ffmpeg libraries](https://github.com/gemrb/gemrb/issues/2321) | open | 3 | 2026-05-26 |
| [#2494 Selecting a spell in spellbook enables another spell](https://github.com/gemrb/gemrb/issues/2494) | closed | 2 | 2026-05-09 |
| [#2493 EE: rendering issues on closing doors](https://github.com/gemrb/gemrb/issues/2493) | closed | 0 | 2026-05-08 |
| [#2485 EE: Crash on loading a save](https://github.com/gemrb/gemrb/issues/2485) | closed | 9 | 2026-05-04 |
| [#2407 BG2 EE: Savegames from GemRB not working](https://github.com/gemrb/gemrb/issues/2407) | closed | 2 | 2026-05-04 |
| [#164 META: add missing EE bits and pieces](https://github.com/gemrb/gemrb/issues/164) | open | 8 | 2026-05-04 |
| [#2490 EE: TTF fonts not used](https://github.com/gemrb/gemrb/issues/2490) | closed | 2 | 2026-05-02 |
| [#2483 EE: Crash on death of PC](https://github.com/gemrb/gemrb/issues/2483) | closed | 3 | 2026-04-29 |
| [#1929 Unicode issue in EE item description - wrong dash](https://github.com/gemrb/gemrb/issues/1929) | closed | 0 | 2026-04-29 |
| [#2478 EE: encoding display issues](https://github.com/gemrb/gemrb/issues/2478) | closed | 4 | 2026-04-29 |
| [#2480 EE: Wrong mapping of classes to item usability](https://github.com/gemrb/gemrb/issues/2480) | closed | 4 | 2026-04-29 |
| [#2479 EE: language setting ignored for speech files](https://github.com/gemrb/gemrb/issues/2479) | closed | 0 | 2026-04-28 |
| [#2456 EE: VLC continues playing in background](https://github.com/gemrb/gemrb/issues/2456) | closed | 1 | 2026-04-02 |
| [#348 Which data files are we not using yet?](https://github.com/gemrb/gemrb/issues/348) | closed | 8 | 2026-04-01 |
| [#2450 EE portrait highlights on item drag](https://github.com/gemrb/gemrb/issues/2450) | open | 0 | 2026-03-24 |
| [#2301 BG2EE: Quick Loot window not present](https://github.com/gemrb/gemrb/issues/2301) | open | 1 | 2026-03-23 |
| [#2443 EE lightning bolt self-replicates until consuming all resources](https://github.com/gemrb/gemrb/issues/2443) | open | 0 | 2026-03-22 |
| [#2442 EE: Bad closed door tiles in the gates district](https://github.com/gemrb/gemrb/issues/2442) | open | 0 | 2026-03-17 |
| [#2298 BG2EE: Right left/arrows in Spell Book does not change "Spell Level Tab" at the top](https://github.com/gemrb/gemrb/issues/2298) | closed | 0 | 2026-03-04 |
| [#2324 EE: No gui quickload](https://github.com/gemrb/gemrb/issues/2324) | open | 0 | 2026-03-04 |
| [#2257 Syncronize and limit key IDS values](https://github.com/gemrb/gemrb/issues/2257) | closed | 1 | 2026-03-01 |
| [#383 We need individual speech channels](https://github.com/gemrb/gemrb/issues/383) | open | 7 | 2026-02-28 |
| [#2409 Entangle spell causes flooding of error messages](https://github.com/gemrb/gemrb/issues/2409) | closed | 3 | 2026-01-18 |
| [#2408 Assertion failure on casting some spells](https://github.com/gemrb/gemrb/issues/2408) | closed | 2 | 2026-01-18 |
| [#2116 Migrate avatars.2da to ini](https://github.com/gemrb/gemrb/issues/2116) | open | 0 | 2025-08-14 |
| [#2299 BG2EE: Quick Save freezes game](https://github.com/gemrb/gemrb/issues/2299) | closed | 16 | 2025-08-14 |
| [#2330 EE: add support for custom state icons](https://github.com/gemrb/gemrb/issues/2330) | open | 0 | 2025-02-12 |
| [#2328 Buggy WEBM support](https://github.com/gemrb/gemrb/issues/2328) | closed | 3 | 2025-02-11 |
| [#2317 BG2EE: Equipping both two handed weapons and single handed + off-hand items.](https://github.com/gemrb/gemrb/issues/2317) | open | 0 | 2025-02-02 |
| [#2271 Error on installation and](https://github.com/gemrb/gemrb/issues/2271) | closed | 6 | 2025-01-16 |
| [#2248 EEs: fully wire up Start.py / Start2.py](https://github.com/gemrb/gemrb/issues/2248) | closed | 0 | 2024-12-28 |
| [#2230 Enable playing EEs with the original's GUI](https://github.com/gemrb/gemrb/issues/2230) | closed | 2 | 2024-12-27 |
| [#2232 Cannot equip items into most EE inventory slots](https://github.com/gemrb/gemrb/issues/2232) | closed | 1 | 2024-12-14 |
| [#93 [feature] fully externalised char animations](https://github.com/gemrb/gemrb/issues/93) | open | 1 | 2024-08-21 |
| [#2080 Missing BMPv5 support](https://github.com/gemrb/gemrb/issues/2080) | closed | 0 | 2024-05-14 |
| [#1959 Static charge only damages caster.](https://github.com/gemrb/gemrb/issues/1959) | closed | 1 | 2023-12-09 |
| [#1924 Unicode issue in EE item description - TTF font not used](https://github.com/gemrb/gemrb/issues/1924) | closed | 11 | 2023-10-17 |
| [#831 Enhancement idea: forget about the load screens like EE does, but don't forget about them completely](https://github.com/gemrb/gemrb/issues/831) | open | 2 | 2023-09-30 |
| [#1874 Improve banter timing / add banttimg.2da support](https://github.com/gemrb/gemrb/issues/1874) | closed | 0 | 2023-08-31 |
| [#1777 Minor visual artifacts on DXT textures on Windows](https://github.com/gemrb/gemrb/issues/1777) | closed | 5 | 2023-01-23 |
| [#1099 Add support for PVRZ files](https://github.com/gemrb/gemrb/issues/1099) | closed | 1 | 2023-01-07 |
| [#547 [feature] check if anything is missing in our VEF support](https://github.com/gemrb/gemrb/issues/547) | open | 0 | 2022-08-14 |
| [#722 Ensure MakeGlobal works the same way as in the original](https://github.com/gemrb/gemrb/issues/722) | closed | 2 | 2022-01-13 |
| [#937 Check the old beamdog bg file format code](https://github.com/gemrb/gemrb/issues/937) | closed | 0 | 2021-08-05 |
| [#848 Proper implementation of modal windows](https://github.com/gemrb/gemrb/issues/848) | open | 5 | 2021-06-19 |
| [#902 Add middle-mouse viewport scrolling](https://github.com/gemrb/gemrb/issues/902) | closed | 0 | 2021-06-03 |
| [#90 [feature] nexttriggerobject / triggeroverride support](https://github.com/gemrb/gemrb/issues/90) | closed | 0 | 2019-10-10 |
| [#229 [subviews] VLC plugin needs update to new API](https://github.com/gemrb/gemrb/issues/229) | closed | 0 | 2019-09-14 |
| [#112 [enhancement] customizable weapon slot count](https://github.com/gemrb/gemrb/issues/112) | closed | 0 | 2019-02-16 |

