# Phase 1 implementation status

October 21, 2026. The user explicitly authorized engine changes and continuation
through Phase 1, using two bounded workers plus the coordinator. This supersedes
the Phase 0 engine freeze for new Phase 1 work; it does not authorize overwriting
the accepted Phase 0 baseline. Working menus, information completeness and correct
game typefaces are fidelity requirements. Modern UI direction remains approved.

## Requirements and order

Latest LAB checkpoint (October 22 UTC): see the [executed validation report](testing/phase1-lab-validation.md).
Candidate `9aa69cd5` matches all 22 selected original weapon cases, completes the
ten-stage inventory replacement regression, and matches the four original AI
branches with native attack/target samples. Its calling-thread RNG observer
detects the deliberate draw and observes no changes in 1,100 normal calls.
The native import/GUI scenarios pass 44 assertions with persistence differences
retained. Fresh private-folder query/cache/control and import/GUI reruns pass
their preservation guards; the earlier diagnostic-write failure is retained.
Both selected menu resolutions complete 107 checks and 51 captures. The opaque
plain-key editor journey and measured calling-thread RNG snapshot cost pass
their bounded checks. External tooling now passes 212 Python tests. Original
controlled-color ordinary saves show 237 to 46 across a fresh-process reload;
that transition is shared behavior, not an established candidate-only defect.
The batch descriptions below are
historical checkpoints, superseded by the linked executed report where stated.

The full [Phase 1 backlog](roadmap/phase1-backlog.md) remains the scope: preserve
reproducible before/after evidence (P1-01); implement distinct EE weapon predicates
(P1-02); restore inventory/record information and ordinary UI operations (P1-03);
resolve demonstrated persistence divergences (P1-04); add only necessary observable
outcome seams (P1-05); validate ordinary gameplay journeys (P1-06); establish
campaign checkpoints and a faithful playable candidate (P1-07). Completing the
first predicate or UI slice will not complete Phase 1.

## Baseline and isolation

Accepted Phase 0 commit: `2cc14fbd0a41ff4e99f62ebda365a71d92c078a5` on
`codex/phase0-audit`. Original source checkout `C:\BGRedux\gemrb`, build
`C:\BGRedux\phase0-local\build`, fixtures, private game and all prior results
remain preserved. Release evidence is indexed by
`20261021T233508Z-phase0-release-e292c68d`. Its original reference includes known
compatibility differences, historical core locale failure/skips, 151 external
unit tests and 44 native scenario assertions; those are distinct test suites.

Coordinator source: `C:\BGRedux\phase1-local\engine` (`codex/phase1-engine`).
Worker source worktrees: `phase1-local/worktrees/weapon` and `worktrees/ui`.
No worker launches a shared native/game session. Integration and native/original
game control are serialized through the coordinator. Baseline results and failed
attempts are immutable evidence; new builds/results use separate destinations.

## Current batch

- P1-01: fresh Debug/Ninja build configured from the accepted source in
  `phase1-local/builds/baseline-lab-20261021`, using the transferred UCRT64 compiler
  and dependencies. It does not use or rewrite the copied historical CMake cache.
  Existing external managed test entry enables logger shutdown and guarded tests;
  engine/assertion sources are unchanged in this before-build. Before-build and
  baseline runs are complete as recorded below; candidate runtime comparison is pending.
- P1-02: worker implementing distinct immunity/enchantment and damage-resistance
  predicates through existing dispatch and cached weapon data. Querying must not
  roll, attack, consume ammunition or apply effects. Additional offhand/both-hand,
  ammunition/enchantment and damage-type oracle boundaries remain to verify.
- P1-03: worker tracing missing EE inventory/record assembly and adding semantic
  content using existing actor operations. Actual game font roles are retained;
  text presence is insufficient evidence for clipping, readability, focus or menu
  functionality. Missing content and typography defects are separate.

All engine changes are unaccepted until built and verified against the relevant
original behavior, normal-loop operations, import/reload and preservation checks.
Broader campaign/menu fidelity remains incomplete. No Phase 1 completion claim.


## Executed first-batch evidence

The isolated before-build completed all 285 Ninja steps. Receipt:
`phase1-local/builds/baseline-lab-20261021/before-build-receipt.json`; 61 binaries
are copied under its `frozen-before-binaries`. Core run
`20261021-164807-phase1-before-core-3ca310db` reproduces 219 pass, one locale
failure, nine skips and six disabled tests. Before vanilla
`20261021T234929Z-phase1-before-vanilla-6a4c9726` and GUI
`20261021T234944Z-phase1-before-gui-a5757621` execute successfully with all 44
assertions and retain compatibility differences. Those results live under
`phase1-local/runtime-baseline/phase0-local/results`.

Candidate build `20261021T235026Z-candidate-1c6316a3` completed, then integrated
the UI/resource changes and a comment correction through an incremental build.
Both initial and integrated receipts/logs are preserved, including the prior
candidate binaries under `pre-ui-revision`. Current candidate DLL SHA256:
`1073429c5af42e7ffd8e8bd88dc000b187014e0f3afef9ab70c231d81b39acab`.
The integrated Python suite passes 63/63 tests. The six-query observer and menu
host compile; neither has yet been executed against this candidate.

Original preparation `20261021T235241Z-weapon-oracle-ccf85085` has 22 cases,
six queries per case, nonce 690073517 (`2921AFAD`). Fresh original captures so
far cover cases 22, 4, 3 and 7. Both opposite slashing/crushing configurations
support the any-effective-hand damage result; the protected enchanted main hand
with empty offhand gives effectiveness 0/0/0 and damage 1/0/1. No universal
predicate contract is inferred from this partial batch. All remaining cases,
actual candidate state invariance, native AI pairs and rendered UI checks remain
pending.

The original launch without a game working directory crashed before the menu;
its dump/receipt are preserved. Relaunch with the explicit private game cwd
succeeded. An original save reordered the item table while retaining exact
physical equipment: the rejected reader result and raw save are preserved; a
reviewed multiset-plus-slot guard now accepts this representation and still
rejects missing/extra/wrong-slot items. Eight actual-evidence adversarial capture
checks reject stale/wrong nonce, case, window, image and fixture observations.
The Phase 0 protected source/binaries/fixture still match the accepted release.

A separate cache investigation and functional hotkey editor are in progress.
All Phase 1 work remains unaccepted pending runtime/journey/campaign evidence;
this status does not replace the full backlog completion requirements.

## October 22 UTC continuation

The hotkey editor now supports the existing plain-key binding surface, with
atomic validation/apply, cancel/defaults and explicit conflict replacement.
Modifiers, international combinations and full EE hotkey fidelity remain open.
Fresh candidate `20261022T002042Z-candidate-e825e411` failed during GUIScript
compilation because a transitional Python string wrapper has no `MakeString`.
Its complete build log and preservation receipt are retained. The correction
copies `PyUnicode_AsUTF8AndSize` into an owned, length-delimited string; native
rebuild is pending. The integrated Python suite passes 94 tests in
`phase1-local/results/phase1-integrated-tests-20261022T0034.log`.

Read-only font import provenance now records the selected stream and actual
FreeType face/size for the external observer. It does not change rendering or
BAM metrics. Independent numeric fingerprints match seven historical TTF roles,
but actual provider metadata and original visual fidelity still require fresh
native observations. See [typography audit](testing/phase1-typography-audit.md).

All eight original ammunition cases (9–16) are frozen and independently reviewed.
At enchantment threshold zero, normal bow/+1 arrows is effective while +1 bow/
normal arrows is ineffective. PFMW blocks the enchanted arrows but permits the
normal arrows. Thresholds one and two reject both configurations. Damage queries
remain true for the occupied main hand in these cases. These are query contracts,
not authority to change combat hit/damage resolution. Before-fix native comparison
uses the preserved `1c6316a3` build and a detached source snapshot at `987aad4de`;
all 3,503 recorded source hashes match. Its external query host compiles, with no
execution while the original session is active.

The inventory mutation observer initially failed compilation on three implicit
`const char*` conversions to explicit `ResRef`; that attempt is retained under
`weapon-query-probes/baseline-cache-20261022`. Explicit construction fixes the
external host, which now compiles against the unchanged baseline as
`baseline-cache-fixed-20261022`. The suspected same-animation item cache issue
still needs runtime reproduction before any engine correction.
