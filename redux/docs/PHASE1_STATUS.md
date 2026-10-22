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
their bounded checks. External tooling now passes 301 Python tests. Original
controlled-color ordinary saves and candidate fresh-process saves both show
237 to 46 to 46; the independently audited comparison establishes shared
behavior for this controlled input, not a candidate-only persistence defect.
See the [paired color audit](testing/phase1-paired-color-audit.md).
The [original control audit](testing/phase1-original-color-controls-audit.md)
adds low-color stability and separately recorded stock random outcomes. New
main/ammo/launcher mutation coverage passes 14 native stages and 196 queries;
the [independent raw audit](testing/phase1-active-slot-journey.md) confirms the
bounded pass, including 588 equal query state/cache/RNG pairs. Deliberate
inventory mutations consumed RNG at three boundaries; this is not a whole-journey
RNG preservation claim. The stock-container gameplay journey now passes its
bounded native route: after observed stock startup, one UseContainer command
opens the table, shipped GUI callbacks transfer SW1H04 and close it, and ordinary
save/fresh-process reload/save preserves ownership. Both processes and all
preservation checks pass in `20261022T040338Z-container-loot-journey-25ffdf30`.
The [independent loot audit](testing/phase1-container-loot-audit.md) confirms
both serialized output saves and 500 retained artifacts. Earlier three
native failures and the readiness adapter's failed compilation remain retained.
This is external callback coverage; original parity and OS pointer input are
unobserved, and no engine correction was needed for this route.
The [stock Jaheira dialogue journey](testing/phase1-jaheira-dialogue-journey.md)
also passes its one-request, eleven-branch route and GUI save/fresh reload,
preserving the expected talk counter, unique journal entry, closed cell and
two-member party; its [independent audit](testing/phase1-jaheira-dialogue-lab-audit.md)
confirms 567 retained artifacts and the saved/reloaded effects.
Its [dialogue rendering defect](testing/phase1-dialogue-rendering.md) now has a
bounded correction: repainting replaces only the active buffer's clip before
drawing the translucent background. The corrected held response and twelve
synthetic alpha/scale/clip cases pass, including216 image comparisons and96
opacity probes. The first broad-clear correction and two fixture-oracle errors
are preserved. The ordinary eleven-branch dialogue/save/fresh-reload regression
also passes on the new candidate. The broader two-resolution menu rerun passes
its existing107 checks and51 captures per resolution with preservation guards;
its [independent audit](testing/phase1-renderer-menu-rerun-audit.md) records scope.
A follow-up [spellbook caster gap](testing/phase1-spellbook-caster-validation-gap.md)
rejects eligible-caster content coverage: the observer selected only the GUI
single actor, then top-window initialization restored the walking leader. An
external portrait-callback/content correction and rerun remain pending.
The [independent renderer audit](testing/phase1-window-render-lab-audit.md)
rechecks the synthetic captures, preservation pins and ordinary-run artifact chain.
A direct public TextArea selection entry separately exposes
a [reentrancy defect](compatibility/phase1-textarea-update-state-reentrancy.md);
the normal selection route passes without an engine change. The bounded
[Imoen Armor cast](testing/phase1-spell-cast-journey.md) also passes one ordinary
cast, actual effects and depletion, GUI save/fresh reload/second save, with no
reload cast. Transitions, broader spell/combat behavior and campaign
checkpoints remain open.
The source-only [key/door/recruitment adapter](testing/phase1-cell-recruitment-journey.md)
is now built and passes the chained key/Cell01/stock auto-dialogue/Jaheira join,
GUI save and fresh reload in `20261022T054005Z-cell-recruitment-ac33ed70`.
The [independent recruitment audit](testing/phase1-cell-recruitment-audit.md)
confirms three-party membership, consumed key, open door, solved quest and actual
XP persistence. This opening-area checkpoint does not satisfy the campaign gate.
The dialogue renderer correction has a fresh isolated build with
native full/clipped/scaled verification; broader runtime regressions remain open.
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
