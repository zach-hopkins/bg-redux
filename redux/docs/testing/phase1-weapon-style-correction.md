# BG2EE two-weapon THAC0 correction

The [exact-input armed comparison](phase1-armed-display-validation.md) shows
stock original EE main18/off21 while the existing runtime returns6/9. Both have
Base14, one Bastard Sword proficiency point, no two-weapon style points, normal
main/+1 offhand weapons, and matching APR5/2/physical dice. The original breakdown
identifies+4/+8 style penalties and a−1 offhand weapon bonus.

Before correction, `original-armed-math-check-a5eebb60/result.json` explicitly
rejects the passed native query/GUI run against that stock reference: actual6/9,
expected18/21. This distinguishes data-preservation success from combat fidelity.

## Correction and compatibility boundary

The appended `WeaponStyleTHAC0Penalties` profile feature defaults off and is
enabled only in bg2ee/gemrb.ini. No existing feature ID is renumbered. With this
feature and2E rules, GameData selects THAC0_RIGHT/LEFT by their names, avoiding
the historical enum-order/name-array mismatch. Actor's two-weapon contribution
is treated as a penalty in the intermediate bonus sum, before the existing
ReverseToHit conversion. Thus+4/+8 worsen descending THAC0; racial, ordinary
weapon-proficiency and weapon bonuses retain their existing ordering.

The correction is in the shared actor calculation used by combat and display
queries. UI text is not adjusted to conceal the wrong engine values. The WSB
enum order and default mapping remain unchanged for profiles that omit the new
feature. The3E path remains outside this correction, even if a profile sets the
feature accidentally. This preserves the existing Classic/other-game paths;
it is not evidence that every historical Classic behavior is correct.

The external armed host has an isolated `--legacy-style-control` mode that clears
only this feature before loading the fixture. Its receipt must show the feature
loaded from BG2EE, then disabled by the explicit control. The expected6/9 result
tests preservation of the former path against the new core. This is a
flag-off branch control on the same content, not a real Classic installation.

## Current validation

The three changed C++ implementation files pass syntax-only compilation using
the existing configured compiler flags, with no old artifacts written:
`weapon-style-syntax-1792711625141377100/result.json`.
The external source suite passes625 tests, including missing/unrequested feature
controls, a declared flag-off control, and explicit stat/effect/proficiency
validation. The log is `weapon-style-final-tooling-20261022.log`.

Production commit `139fbcac4` completed a fresh 288-target build:
`20261022T233409Z-candidate-15cbd18d`. Its receipt reports unchanged source/support
inputs and preserved Phase0 source, binaries and fixture. The separate menu host
was rebuilt against this core in
`20261022T234130Z-style-stats-menu-build-ed8813eb`.

The exact original fixture now returns main18/off21 in
`20261022T234439Z-style-armed-8b431f06/result.json`. The independent comparison
`20261022T234635Z-original-armed-math-check-7554cf38/result.json` accepts these
values against the frozen stock reference, after the earlier6/9 rejection.
The rendered 1024x768 inventory capture also shows18/21. All seven preservation
guards pass. The isolated flag-off run
`20261022T234636Z-style-armed-1d2bb6cd/result.json` returns the former6/9 values,
with the feature reported loaded and then explicitly disabled.

The serial follow-up batch is recorded in
`20261022T235211Z-style-followups-60777a28/result.json`: all14 cases passed.
The cases include reversed hands, other weapons, empty/shield offhands,
launcher/ammunition, both resolutions, style ranks1/2/3, and four-point longsword
proficiency. Rank-only values16/19,14/17 and14/15 match the loaded style table;
these are not separately measured stock-game references. Longsword proficiency
produces15/18 with damage bonuses4/4. The declared+1 attack modifier alone
produces17/20; rank3 plus longswords plus that effect produces10/11 with damage
bonuses4/4. Each run uses fresh writable cache/input copies and verifies all
seven preservation guards before archiving its completed cache.

The combined case also has an exact-input stock2.7.3.0 reference:
`20261023T001642Z-original-style-reference-0c22df3d`. Unmodified stock Record and
Inventory show10/11, stable after reopening Record. The combat breakdown shows
four longsword points, three two-weapon points, attack modifier−1, ordinary
proficiency THAC0−3, offhand style+2 and weapon−1, and proficiency damage+4.
Stock APR3 and damage1d8+4 /1d8+5 also match native details. The separate
`20261023T002553Z-original-style-details-check-1be7040e/result.json` verifies
both hands' totals, base, modifiers, APR and damage against these observations.
The private original process exited0, and closure verifies unchanged executable,
input saves, private root bytes, clean game inventory and protected Phase0.

The fresh core suite passes231 tests, skips9 and reports6 disabled, with zero
failures: `20261023T000532Z-source-bound-core-fac6226c/result.json`.

The fresh read-only query diagnostic passes144 calls, original script14/display12
comparison, legacy/RNG positive controls and unsupported3E rejection:
`20261023T000600Z-style-display-query-contract-94575fd7/result.json`. Its pure
phase preserves actor/cache bytes and calling-thread RNG; declared mutation
controls mean the whole diagnostic is deliberately not unchanged.

Full four-character Stats refreshes pass at1024x768 and1280x768 in
`20261023T000637Z-style-stats-menu-run-ae3e21f0/result.json`. Each resolution
collects24 actor sections,40 page visits and45 captures with world conservation
and all seven outer preservation guards. Fresh capture34 was visually inspected
at both resolutions; it shows Minsc's display THAC0 at12 and the still-unresolved
unarmed APR at1. This sample inspection does not accept complete typography or
physical pointer hit testing.

The fresh22-case weapon-predicate regression matches all selected original
references in `20261023T001501Z-phase1-weapon-query-c72efd5f/result.json`.
The external-host baseline completes capabilities,24 import/reload assertions
and20 GUI/save assertions in `20261023T001833Z-style-base-2b9a469d/result.json`.
Execution and preservation pass; compatibility remains `differences` (process
exit1 reflects that compatibility verdict).

The consecutive-build review is
`20261023T002052Z-style-baseline-residual-review-16b80246/result.json`, with exact
row disposition in `20261023T002506Z-style-baseline-residual-disposition-d338d08f/result.json`.
Vanilla wire residuals are unchanged, both reloads have zero semantic differences,
and repeat-import differences remain confined to color stats (26 versus28).
GUI persistence/legacy counts are449/53 versus451/55: no rows were added, and
only the prior actor31 base/modified color210 rows3435973836→875836468 are absent.
Every remaining GUI row matches exactly. This is observed variation, not proof
of a color correction, palette parity or a compatibility waiver.

[Pinned evidence](../evidence/phase1-weapon-style-correction.json) binds these
terminal results. Original delivered attacks remain unmeasured. Matching the
two stock display cases does not establish complete combat or Phase1 fidelity.

All earlier candidates, results and failures remain preserved. Space recovery
uses verified content-preserving compression of closed Phase1 binaries/objects;
the protected Phase0 checkout/build/fixtures and current old candidate are
excluded. Full Phase1 remains active and incomplete.
