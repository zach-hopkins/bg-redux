# Phase 1 implementation status

October 21, 2026. The user explicitly authorized engine changes and continuation
through Phase 1, using two bounded workers plus the coordinator. This supersedes
the Phase 0 engine freeze for new Phase 1 work; it does not authorize overwriting
the accepted Phase 0 baseline. Working menus, information completeness and correct
game typefaces are fidelity requirements. Modern UI direction remains approved.

## Requirements and order

Current October 22 checkpoint: **Phase1 remains incomplete**. Coherent candidate
`20261022T123435Z-candidate-e00bb8b5` builds from source `9b30077b7`, with protected
Phase0 source/binaries/fixtures unchanged. New Phase1 work remains isolated in
`C:/BGRedux/phase1-local/engine`. All completed results, including failures, remain
preserved. See the full [backlog](roadmap/phase1-backlog.md).

| Bounded evidence | Current result and scope |
|---|---|
| Source tooling | **534 tests pass**, 56.465 seconds, `phase1-feedback-row-tooling-1792672463250707300/result.json`. This is distinct from engine CTest and native game validation. |
| Fresh general baseline | `20261022T125410Z-row-base-2d8ec7ed`: **24/24 import/reload + 20/20 GUI/save assertions**, zero skips, all preservation guards. Execution passes; compatibility remains **differences**, so the outer wrapper exits one intentionally. [Independent raw audit](testing/phase1-right-row-baseline-independent.md). |
| Menus at both required sizes | `20261022T124438Z-row-menu-run-c59be7e9`: **148 checks, 51 captures, 39 callbacks and 107 steps per resolution**, 1024x768 and 1280x768. [Independent audit](testing/phase1-right-row-menu-independent.md) verifies both processes and all seven guards. |
| Correct Feedback setting | `20261022T123904Z-confirmation-setting-mixed-e9957e50`: right checkbox 41/buddy 40/label 29; left Colored Markers label retained. Actual Cancel/Done, owned INI write, byte-exact configuration transfer, fresh-process option-one loading, both books' charged prompts and depleted-first mixed-copy removal, normal GUI save/wire/fresh reload pass. [Independent audit](testing/phase1-confirmation-right-row-independent.md). |
| Spellbook information | Earlier candidate ced237a2, `20261022T122217Z-spellbook-information-ee-direct-97f61bc1`: both owned processes pass, visiting 13 natural ordinary-book pages each with 65/55 captures and 80/67 callbacks. [Independent 120-capture audit](testing/phase1-information-journey-independent.md) verifies names, selection/deselection, paging, actor/level resets, help/descriptions, scroll movement/exact return, spell actions/capacity guards, GUI save and fresh reload. This historical receipt does not certify later changed helper files. |

The information helper now keeps complete localized help for ineligible and
initially hidden books while still blocking spell actions. Actual-helper BEFORE
has two failures of fifteen; AFTER passes fifteen
(`phase1-disabled-help-before-20261022.log` / `phase1-disabled-help-after-20261022.log`). The
[Feedback-row repair](testing/phase1-confirmation-feedback-row-repair.md) corrects
the initial binding to the Colored Markers row: its new tests fail twice against
the old helper (`feedback-row-before-1792672185705967100/result.json`) and all
twenty-one pass after correction. Earlier wrong-row persistence passes establish
behavior only, not accepted placement.

Failed information journey90991fb5 remains failed: unsupported diagnostic pronoun
tokens and a short description could not establish the intended coverage. The
replacement binds the actual gender table/TLK words and uses naturally known
Remove Magic and Dispel Magic for strict scroll proof. Failed confirmation
journeyd8efb6d2 also remains failed; its Python/native resource-case comparison
was corrected without normalizing unrelated world state. [First-attempt analysis](testing/phase1-confirmation-native-first-attempt.md)
retains the exact native mixed-case storage distinction. Diagnostic-only
reanalysis does not replace a fresh native pass. The physical original
[option-ON/depleted-first reference](testing/phase1-original-confirmation-option-independent.md)
remains separately pinned and bounded.

Current baseline residuals are vanilla **0/0/26** and GUI **451/55**. Their counts
match the preceding help baseline, but some actor/color paths and values change;
they are not identical results and are not waived. The targeted setting audit
also preserves 885 broader fresh-import world/effect/time/selection residuals.
Passing targeted spell/config checks does not establish whole-world save purity,
RNG non-interference, original operation parity or complete campaign fidelity.

Remaining work includes the source-grounded [inn confirmation gap](testing/phase1-inn-confirmation-source-and-journey.md),
the existing unbound Colored Markers control, save/color differences, exact
typeface metrics, physical pointer/focus/clipping paths, alternate native locales,
native female-protagonist token coverage, spontaneous books and broader menus and
campaign journeys. The natural spell lists reach twelve entries, not above
twenty-four; synthetic thirty-one-entry coverage does not prove that native case.
The coordinator retains native-session ownership; the same two workers continue
source preparation and independent audits. [Storage preservation](testing/phase1-lab-storage-preservation.md)
records lossless compression and completed-cache sharing; no result is deleted.

The paragraphs below retain **historical checkpoints**. Their pending/unvalidated
statements describe those frozen versions, not the current summary above.

The wizard information-window Erase route now has a confirmed native wrong-spell
failure when localized names reorder known entries. The stock route passes, but
the controlled BEFORE deletes SPWI211 instead of the displayed SPWI213 and saves
that wrong state. [Diagnostic evidence](testing/phase1-spellbook-erase-diagnostic.md)
is retained. Commit `3f5cad097` carries the original known index into the information
callback; all four fast regression cases and the full 447-test external tooling
suite pass. Fresh candidate `20261022T104353Z-candidate-3f8cf4a0` builds with protected
Phase0 inputs unchanged. Stock AFTER `20261022T104723Z-spellbook-erase-ee-direct-e0270854`
and controlled AFTER `20261022T105032Z-spellbook-erase-name-control-ee-direct-1dd9a81c`
pass intended removal, GUI save and fresh reload. The [independent AFTER audit](testing/phase1-spellbook-erase-after-independent.md)
confirms selected SPWI213 removal with unrelated SPWI211 retained. Fresh general
baseline `20261022T105238Z-erase-base-4ec5c4f2` passes 24/24 import/reload and 20/20
GUI/save assertions, zero skips, with all baseline/candidate/input guards. Its
compatibility verdict remains **differences**, with cross-build residuals
unreviewed. The [independent general-baseline audit](testing/phase1-erase-candidate-fresh-baseline-audit.md)
confirms all assertions and preservation guards: GUI residuals are exactly the
prior 449/53 rows; vanilla reload/repeat-import color differences remain open.

The [upstream fidelity follow-up](compatibility/upstream-fidelity-followup-context.md)
now records a fresh `game: ees` issue index check, fourteen targeted issues,
all fifty-seven comments and four linked patches. It distinguishes older layout/
portrait/scrollbar overlap from our measured retained-pixel and reentrancy faults;
upstream closed status is not treated as candidate acceptance.

The original game's [More Confirmation Prompts option binding](testing/phase1-confirmation-option-source-binding.md)
also establishes an open fidelity gap: unconditional direct EE removal covers the
measured option-OFF case only. The later physical original option-ON/depleted-first
reference is now independently verified above. The candidate setting and callback
integration still require native config/persistence/mixed-copy validation.
Persistent spell names/localized help, other menus and broader campaign gates
remain part of the full Phase1 scope.

New heading/direct-removal candidate `20261022T093226Z-candidate-5a60a03d`
passes the fresh 44-assertion baseline (known differences retained), with an
[independent audit](testing/phase1-heading-policy-fresh-baseline-audit.md).
Its [heading repair](testing/phase1-ee-spellbook-heading-repair.md) passes
196 native menu checks and 51 captures at both 1024x768 and 1280x768.
Audited stock and controlled-name spellbook BEFORE operation/save/reload journeys
also pass. Explicit EE-direct stock and private name-control AFTER operation/save/reload
journeys now pass; the [stock independent audit](testing/phase1-ee-direct-stock-independent-audit.md)
also binds 44 changing heading observations, including allocated versus ready counts.
Persistent spell-name/help assembly, exact typography and the full Phase1
backlog remain open. The following paragraphs retain earlier checkpoints.

Candidate `9aa69cd5` matches all 22 selected original weapon cases, completes the
ten-stage inventory replacement regression, and matches the four original AI
branches with native attack/target samples. Its calling-thread RNG observer
detects the deliberate draw and observes no changes in 1,100 normal calls.
The native import/GUI scenarios pass 44 assertions with persistence differences
retained. Fresh private-folder query/cache/control and import/GUI reruns pass
their preservation guards; the earlier diagnostic-write failure is retained.
Both selected menu resolutions complete 107 checks and 51 captures. The opaque
plain-key editor journey and measured calling-thread RNG snapshot cost pass
their bounded checks. External tooling now passes 424 Python tests (final source-bound run: 34.768 seconds;
receipt `phase1-local/results/phase1-tooling-final-1792664175947971600/result.json`). Original
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
external portrait-callback/content correction now passes both resolutions with
187 checks and51 captures each in `20261022T061926Z-guarded-recruited-menu-run-0a25d610`;
the [executed correction](testing/phase1-spellbook-display-selection.md) records
the prior missing-nonce failure, fresh callback identity, content checks and scope.
The [independent artifact audit](testing/phase1-caster-menu-native-audit.md)
passes and retains the faint priest-heading observation and visual scope limits.
The [heading layout investigation](testing/phase1-spellbook-heading-layout-gap.md)
binds that readability issue to obsolete CHU placement/styling versus the shipped
EE menu assembly. Its bounded repair now passes both native menu resolutions;
original information assembly and exact typography remain open.
The [independent renderer audit](testing/phase1-window-render-lab-audit.md)
rechecks the synthetic captures, preservation pins and ordinary-run artifact chain.
A direct public TextArea selection entry separately exposes
a [reentrancy defect](compatibility/phase1-textarea-update-state-reentrancy.md);
the complete fifteen-case BEFORE matrix has three passes, seven crashes and five
contract failures. A reviewed generation/context correction is now applied and
built in isolated candidate `20261022T063419Z-candidate-24f35a4e`; its fifteen-case
AFTER matrix passes exact traces/values and world/dictionary preservation.
The ordinary eleven-branch Jaheira/GUI save/fresh-reload regression also passes
in `20261022T064605Z-jaheira-dialogue-dbcdba69`, with all preservation guards.
The [independent fifteen-case AFTER audit](testing/phase1-textarea-native-correction-audit.md)
passes. The [real-dialogue direct-API regression](testing/phase1-jaheira-direct-selection-regression.md)
also passes both public UpdateState responses, all eleven branches, GUI save and
fresh reload in `20261022T070508Z-jaheira-dialogue-direct-83a17bf8`. The fresh
two-resolution menu run `20261022T064911Z-guarded-textarea-menu-run-eba67ffa`
passes187 checks and51 captures each, with all preservation guards. Independent
raw audits now pass for the [normal dialogue and menus](testing/phase1-b49-normal-dialogue-menu-audit.md)
and [direct selection dialogue](testing/phase1-jaheira-direct-selection-native-audit.md).
That fresh candidate's
[checked string-test locale setup](testing/phase1-string-locale-fixture-fix.md)
passes the three focused casing tests and the full corrected-CWD core suite:
231 passed, zero failed, nine skips and six disabled tests. The six other CTest
executables also pass; the [independent core audit](testing/phase1-source-bound-core-audit.md)
confirms their counts and source/config/resource binding. The historical locale
and wrong-CWD failures remain preserved. The bounded
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
The subsequent [Minsc checkpoint](testing/phase1-minsc-recruitment-host.md)
passes all 21 stock dialogue branches, the script-driven second cage opening,
four-party recruitment, measured XP, GUI save and fresh reload with all guards.
The [independent raw audit](testing/phase1-minsc-recruitment-native-audit.md)
passes; this also remains an opening-area checkpoint.
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
