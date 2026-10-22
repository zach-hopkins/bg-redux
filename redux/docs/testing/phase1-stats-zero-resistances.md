# EE Stats: explicit zero resistances

## Reproduction and requirement

P1-03 requires a visible, correctly labelled value for every required protection.
Opening Record → Stats → Resists on the four-party ordinary-menu fixture instead
shows only the heading **Resistances**. A player cannot distinguish zero
protection from missing information. The preserved native reproduction is
`20261022T124438Z-row-menu-run-c59be7e9`, nested
`20261022T124443Z-menu-run-f644f5e5/1024x768/capture-9.bmp` and matching UI/state
JSON. Its runtime `stats.bounded-page` check passed despite the empty section.
This demonstrates why a nonempty heading cannot establish information completeness.

The [upstream EE GUI context](../compatibility/upstream-ee-gui-issue-context.md)
was consulted, especially #2230's missing inventory information and the separate
font/encoding investigations. None supplies this reproduction or establishes that
zero values are missing because of font rendering. The
[dialogue context](../compatibility/upstream-dialogue-issue-context.md) remains
separate; no conversation code changes are involved.

## Narrow correction

Production source commit `f8fbd45d9` adds an opt-in `showZero` argument to the
existing record formatter and resistance assembler. Only the EE supplemental
Stats assembly requests it. The legacy overview/default formatter still omits
zero-valued percentage rows. No actor statistics, combat operations, save data,
item ownership, effects or game assets are changed by this presentation option.

All thirteen existing BG2 resistance labels and their existing actor-stat
operations remain authoritative: fire, magic fire, cold, magic cold, electricity,
acid, magic, magic damage, missile, slashing, piercing, crushing and poison.
Zero is displayed as `0%`; negative values and values over 100 are preserved.
Values are not inferred from equipment descriptions or combat logs.

The menu observer now visits every naturally present Stats page through the
registered Next/Previous callbacks, checks exact content and actor/section
identity on each page, and returns through every page to page one. This replaces
the earlier first-page/one-Next/Back scope. Expected content is obtained separately
from the current visible control, but shares production assembly; the coordinator
numeric review therefore additionally compares the thirteen displayed resistance
rows with native actor snapshot statistics and the actual English TLK labels.
Neither mechanism is an original-game font or combat-parity oracle.

## Source evidence

Five actual-source resistance tests preserve
`C:/BGRedux/phase1-local/results/ee-stats-zero-before-20261022.log`: one assertion
fails and two calls error because the opt-in API does not yet exist. After the
correction all five pass in `ee-stats-zero-after-20261022.log`. Default omission,
explicit-zero rows, negative/over-100 values and the EE caller are covered.
The existing seventeen character-sheet tests pass; four new observer tests cover
all-page traversal, single-page disabled-boundary avoidance, later-page text
corruption and actor mismatch.

Full external source tooling: **565 tests pass**, 34.584 seconds, source
`f8fbd45d979bcd6fb9b0021ff619b15ae2197cac`, receipt
`phase1-stats-zero-tooling-1792699847692313400/result.json`. Its source inventory
also binds GUIREC.py, GUIRECCommon.py and EECharacterSheet.py. These source tests
are distinct from native validation and historical engine CTest results.

## Native validation

Fresh complete Debug/Ninja candidate
`20261022T201023Z-candidate-be5f907d` builds from `f8fbd45d9`. Its receipt retains
`built-not-validated`; source/support and protected Phase0 source/binary/fixture
guards pass. External menu host build
`20261022T201434Z-stats-menu-build-754a7649` passes against that candidate.

Both native runs pass: `20261022T201520Z-stats-menu-run-8f0f646e` at 1024×768
and `20261022T202136Z-stats-menu-run-efa0530e` at 1280×768. Each records **156
checks, 111 planned/completed steps, 53 captures and 41 actual callbacks**. Owned
PIDs 5304/16956 exit zero with authoritative cleanup. All seven outer preservation
guards pass, and collected callback/whole-run world state is unchanged apart
from the declared selection scope. This is not hidden RNG or whole-world purity.

The Resists tab has two readable pages: ten resistance rows on page one and
piercing/crushing/poison on page two. The coordinator viewed all four actual BMPs
without clipping in the selected English case. Registered callback traversal
reaches every natural page in all six Stats sections and returns to page one.

`stats-resistance-review-1792700834950436300/review.json` passes a separate raw
numeric/content review. It imports neither production assembly/formatting nor
the menu validator, reads the actual TLK labels and captured actor statistics,
compares all thirteen resistance rows at both resolutions, checks captured
visible-control text and exact page traversal, hashes accessed JSON/images and
rehashes the accessed JSON before acceptance. It remains coordinator review,
not a new independent worker audit. The fixture's thirteen values are all zero.

Fresh general baseline `20261022T202715Z-stats-base-4eeccc08` completes: **24/24
import/reload and 20/20 GUI/save assertions**, zero skips, protected Phase0,
candidate and input guards pass. Execution is passed; compatibility remains
**differences**, so the wrapper's exit1 is intentional. Residual counts are
vanilla4/0/24 and GUI449/53. Reload-one's four rows are actor3 minor color209
(3873892070→2139062143) and actor7 leather color212 (3520188881→1566399837),
base and modified. The preceding650 run had two actor31/stat210 rows. These
field identifications do not establish a cause, improvement or compatibility.
Repeat-import and other changed residual rows remain unreviewed.

[Pinned evidence](../evidence/phase1-stats-zero-resistances.json) binds the build,
source tests, both native receipts, numeric review/frozen reviewer and exact
baseline rows. All owned build/native/baseline sessions have terminal receipts.

## Limits and next acceptance work

The correction does not complete P1-03 or Phase1. Required remaining work includes
broader actor/effect/class cases, exact original typeface/size measurement,
non-English layouts and actual pointer hit testing. A zero-only native fixture
does not establish native negative/over-100 rendering, although the actual-source
assembly tests cover those values. Registered callbacks are not physical mouse
coverage. The independent workers remain limited; coordinator review must not be
labelled a fresh independent worker audit.

The rollback is the isolated production commit; saved-game schemas and profiles
need no migration. All before/after failures, candidate builds, captures and
storage-preservation receipts remain retained. Historical persistence residuals,
inn store/dream/movie fidelity and campaign gates remain open.
