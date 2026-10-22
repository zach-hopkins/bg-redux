# Armed display queries and ordinary sheet refreshes

This extends [the detached display correction](phase1-display-combat-query.md)
beyond its initial all-unarmed fixture. Production source and candidate binaries
remain unchanged atcd83f1e48 / verified resumed buildfaf62922. Only the external
host, runtime plan and strict reader are extended.

The normal-loop host loads a fresh copied save through GUILOAD, executes128 actual
Python display queries across both actors and both hand arguments, opens Record
and Inventory, switches their portraits through registered callbacks, and repeats
the128-query matrix. Four actual sheet captures bind visible names, THAC0
headlines and text panels to the returned details. Before/after raw snapshots and
observer captures require world/cache conservation through this presentation
phase, allowing only the declared portrait selection. Native object-byte checks
cover party base/modified stats, ToHit and both WeaponInfo objects; existing
calling-thread RNG snapshots must remain unchanged during each query matrix.

The deliberate die roll must change the RNG observation. Omitted-third-argument
and explicitFalse legacy queries run only after the presentation phase and must
return identical details. Their known actor/cache mutations are recorded as
controls, not normalized into a whole-run conservation claim. If independently
captured final state/cache differs, the byte observer must detect that mutation.

## Input and scope

Inputs come from the immutable22-case weapon preparationccf85085. Each private
copy changes exactly8 GAM bytes: the protagonist's observer-script assignment is
changed toNONE to prevent the query/autosave script from running during GUI work.
Restoring those8 bytes recovers the original GAM exactly. Equipment, stats,
effects, selected headers and ammo counts are unchanged. Both actors' other file
scripts were alreadyNONE. The reader reuses the established runtime equipment
and defense guard against an independent native weapon-cache capture.

This is controlled equipment/effect testing, not an ordinary campaign checkpoint.
Legacy-result parity is a regression check, not an original combat-math oracle.
Full hidden-state/other-thread purity, typography and physical-pointer acceptance
are not established by the result booleans.

## Preserved setup failures

First run7ff074d7 completed the API matrices and legacy controls but failed its
Inventory/Imoen expectation. Captures show selection1 and protagonist values;
the test had closed Record and assumed its non-walking selection survived.
`GUICommonWindows.SetSelectionChangeHandler` deliberately picks the first walking
selection when opening a new top window. The corrected plan explicitly clicks
Imoen inside Inventory and then clicks the protagonist. No production behavior
was changed to accommodate the test. The failed run remains rejected.

Batch589f2ec6 completed the reverse dual-wield case, then its launcher called
`harness.environment(out)` again and failed recreating profile/Documents before
the next process launched. Its partial result, original launcher and separate
launcher-error record remain intact. The v2 launcher creates the isolated
environment once and continues only the unexecuted cases.

## Current evidence

Source tooling passes619 tests, including16 armed-reader negative-control tests.
Accepted normal/+1 run4193f3c1 and reverse-order run49fb375e exercise actual dual
weapons. The serialized v2 matrixbc5ad878 passes all seven remaining runs: hammer/
sword, empty/shield offhand, enchanted ammo, enchanted launcher, and dual/ranged
cases at1280×768. All nine runs pass their seven outer preservation guards.
Together they execute2,304 display-matrix calls,36 actual sheet observations and
27 registered portrait callbacks. The expected legacy mutation is detected.

## Stock original comparison: armed math is still wrong

Exact-input stock reference729193e0 completed with normal owned exit0. Record,
its Combat Stats breakdown, Inventory and refreshed Record consistently show:

| Value | Stock original EE | Current native |
|---|---|---|
| Base THAC0 | 14 | 14 |
| Main-hand THAC0 | 18 | 6 |
| Offhand THAC0 | 21 | 9 |
| Two-weapon contribution | +4 main / +8 off | −8 main / −4 off in proficiency component |
| Offhand weapon bonus | −1 | −1 |
| Attacks per round | 5/2 | 2½ |
| Physical weapon dice | 2d4 / 2d4+1 | 2d4 / 2d4+1 |

The stock UI is unmodified. Its input save is byte-identical to the accepted
native fixture. Closed verification confirms original executable/private-root
bytes, input saves, protected Phase0 and clean-game inventory remain unchanged.
Screenshots04–08 and `observed-combat-values.json` preserve the actual display;
this is a coordinator visual reading, not OCR, live script-stat sampling or
measurement of delivered attacks. The native screenshot was also inspected.

The native normal/+1 fixture displays6/9 from Base14, with
proficiency components−8/−4 and an offhand weapon component−1. Source inspection
shows `WSB::THAC0Left` precedes `THAC0Right`, whereas the GameData name array lists
RIGHT beforeLEFT. The shipped stylbonu table stores positive two-weapon values,
and the shared calculation reverses its aggregate proficiency sign. These are
pre-existing paths that explain the observed reversed/swapped style terms.
GameData.h/cpp and the style helper are byte-identical to the protected baseline;
the aggregate calculation differs only in its ToHit receiver name after the
detached-query refactor. This arithmetic defect was not introduced by the
read-only correction. A production correction is not implemented yet, and actual
delivered attack behavior remains unmeasured. The malformed-signature warning also has a
separate concrete input: the shipped header contains spacing between2DA andV1.0.
No parser change or causal claim about that warning is made here.

[Pinned evidence](../evidence/phase1-armed-display-validation.json) and private
review `20261022T231334Z-armed-display-review-27b1506f/review.json` bind the nine
runs, stock comparison, frozen screenshots and source equivalence checks.

The next priority is a narrowly scoped correction to the shared combat
calculation and column mapping, with an explicit Classic/other-game boundary.
Then repeat the exact18/21 reference, both weapon orders, style ranks, armed GUI
refreshes and baseline/predicate guards. Do not patch only the displayed text or
relabel parity with the existing calculation as original fidelity. Self attack
effects and nonzero proficiency bonuses also need their own display cases.

Full Phase1 remains incomplete. Preserve the fresh baseline/color residuals and
core skip/disabled counts reported by the preceding correction evidence.
