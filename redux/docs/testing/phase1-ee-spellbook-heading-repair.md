# BG2EE ordinary spellbook heading repair

Status: **integrated; focused/integrated tests and both native menu resolutions pass**. This is a bounded heading assembly repair, not complete spellbook, typography or EE visual acceptance. The earlier [layout gap](phase1-spellbook-heading-layout-gap.md) and its historical captures remain evidence of the defect.

## Reference and cause

The original BG2EE captures under `C:/BGRedux/phase1-local/results/20261022T082351Z-original-spellbook-installation-4de00a9c/` were inspected statically:

- `original-mage-level1.jpg`, SHA256 `a28ca9f325d02d9b9195a3462195ada60c19248f4f0c721b9504bd655614b5da`, shows a gray Memorized 4/4 heading centered in the dark strip immediately above the prepared spells.
- `original-priest-ineligible-level1.jpg`, SHA256 `e17faf06b16061b9a765466d7136da5c12ba2adff1b8de81dd075ebd9edaecf9`, shows the corresponding 0/0 field on the dimmed, unavailable priest page for Imoen. This is not an eligible priest-operation reference.

The resource audit binds `ui.menu:8835–8841` to the page-info area `(272,598,276,40)` and `bgee.lua` style `label` to centered STONESML point 12/color B=`FFCECECE`. Imported GUIPR/GUIMG CHU label `0x10000033` instead uses TOOLFONT and pale color at relative y490/489. GUIPR moves prepared buttons to y644 without moving that label. GUIMG goes further: its ordinary BG2EE initialization deletes this label while retaining the prepared row. These are local screen-assembly causes supported by source and packaged metadata; no font-rasterizer defect is inferred.

## Narrow source change

`EESpellbookHeading.py` shares the ordinary BG2EE layout and text update. GUIMG retains the imported label; both normal books place it at relative y598/height40, preserve its existing x/width and imported center/middle alignment, select the shipped STONESML role, and set opaque RGB 206 gray. The heading ends at 638, leaving six relative pixels before the prepared row starts at 644. With the existing panel origin, the intended heading remains in the dark strip and inside the window. Window/display origins are not added to these relative coordinates.

The displayed prefix comes from localized strref 11944, with allocated memorization entries and the existing capacity: `localized heading: memorized/capacity`. Counts use the caller's existing `GetMemorizedSpellsCount(..., False)` result, including spent slots, rather than only currently ready spells. Capacity uses the already computed `max_mem_cnt`; GUIScript's optional Bonus parameter defaults 1, so the priest's existing three-argument query already includes bonuses. No capacity calculation or slot-enabling policy changes. Over-capacity values are displayed faithfully rather than clamped. Updates refresh the selected actor/level's values and reapply the ordinary layout.

Classic game paths are untouched. Selecting a spontaneous priest hides this ordinary-count label, preventing a stale previous priest count; returning to an ordinary priest restores the label with current counts. No Shaman capacity is invented. A separate Sorcerer window without this control is handled without creating a label. Existing Sorcerer controls and casts-remaining text, prepared-slot suppression, spell callbacks, memorization/unmemorization operations and confirmation behavior are not changed. Full Shaman/Sorcerer count presentation remains a separate fidelity gap.

## Reviewable validation and limits

Focused test source `redux/tools/phase1/tests/test_ee_spellbook_heading.py` covers copied frame ownership and preserved horizontal geometry, bounds above the prepared row, origin-independent relative positioning, role/color selection, localization, zero/over-capacity updates and Classic gating, spontaneous visibility transitions and missing-control handling. It executes the real Init/Update function bodies with fake engine queries to check that ordinary wizard initialization retains the label, live count updates use allocated entries, priest capacity plumbing remains unchanged and Classic paths do not mutate the heading, a same-window ordinary→spontaneous→ordinary sequence hides/restores current counts, and separate Sorcerer windows tolerate the absent ordinary label. Other controls/callbacks are inert in those tests; they do not prove native dispatch or font rendering. **The worker has not executed these tests.**

Coordinator validation should use a fresh coherent source-bound candidate: run focused/integrated tests; capture both normal wizard and eligible priest books at 1024×768 and 1280×768; assert the actual selected actor, localized live heading, relative label frame/font/provider/color, capacity and prepared slots after level/actor changes and spent-slot changes. Inspect clipping/contrast in the dark strip and retain before/after images. The unavailable priest page is a separate context. The original confirmation-policy difference remains a separate defect.

STONESML is selected through the existing game resource role. The current BG2EE fonts table requests that role at 14px; original style metadata says point 12. This change does not equate points with pixels or prove matching advances, baselines, rasterization, long-localization overflow or provider metrics. Those require actual native provider/metric receipts and original image comparison; neither generic fallback fonts nor a font engine change is introduced here.


## Executed coordinator validation

Coherent candidate `20261022T093226Z-candidate-5a60a03d` contains the heading
and separate direct-removal policy (3,509 source files/61 binaries/five support
files). The final source-bound tooling suite passes 424 tests in 34.768 seconds;
receipt `phase1-local/results/phase1-tooling-final-1792664175947971600/result.json`
pins the test/tool inputs, log and unchanged source bytes.
The fresh [baseline audit](phase1-heading-policy-fresh-baseline-audit.md)
confirms 24 vanilla and 20 GUI assertions, with compatibility differences retained.

Guarded native menu run `20261022T095203Z-sb-menu-run-bc1642be` passes both
1024x768 and 1280x768: 196 checks and 51 captures each. Both ordinary spellbooks
are required and observed; live allocated counts/bonus capacities, selected
actor/level, visible heading rectangle and prepared-row/window bounds pass.
All Phase0/candidate/game/source/probe/parent/coherent-build guards pass.
This observer does not perform the new direct-removal journey.

Coordinator inspection of captures 23/25 at both resolutions shows readable gray
`Memorized: 4/4` for Imoen and `Memorized: 5/5` for Jaheira in the dark strip above
the prepared row. Selected-frame review and hashes:
`phase1-local/results/20261022T100431Z-sb-heading-visual-89f9390e/review.json`.
Separate imported font-provider/face/size metadata validation passes both stages:
`phase1-local/results/20261022T100239Z-sb-fonts-3f253289/result.json`.
STONESML is observed as AmericanUncial, 14px, from Patch2.bif/stonesml.ttf.
The validator preserves its resource-byte identity, style and pixel-fidelity
limits; role metadata does not prove per-label assignment.

Comparison with the original mage screenshot also exposes a separate missing
assembly: persistent known-spell names and right-page help are absent from the
native icon grid. This repair does not close that information gap or the
original count-frame/layout differences. Exact typography and long-localization
coverage also remain open.


The separate [EE-direct stock audit](phase1-ee-direct-stock-independent-audit.md)
now validates heading updates during real operations, not just all-ready menu
pages. Across 44 observed frames, wizard allocated counts change 3/3 -> 2/3 ->
3/3 while ready counts end at 2; priest counts change 5/5 -> 4/5 -> 5/5 while
ready counts end at 4. GUI save and fresh-process reload preserve the depleted
instances and correct headings. The declared private name control also passes
on this candidate. The [information-layout defect record](phase1-spellbook-information-layout-gap.md)
separates the remaining names/help/selection and erasure-index work.


The [independent two-resolution menu audit](phase1-ordinary-heading-menu-independent-audit.md)
confirms actual caster/page/geometry and raw provenance. The
[independent EE-direct name-control audit](phase1-ee-direct-name-control-independent-audit.md)
also confirms the changing count labels and correct original-index operations
under nonidentity display order. None of these audits approves exact original
pixels or the missing spell information/selection assembly.
