# Phase 1 implementation status

October 21, 2026. The user explicitly authorized engine changes and continuation
through Phase 1, using two bounded workers plus the coordinator. This supersedes
the Phase 0 engine freeze for new Phase 1 work; it does not authorize overwriting
the accepted Phase 0 baseline. Working menus, information completeness and correct
game typefaces are fidelity requirements. Modern UI direction remains approved.

## Requirements and order

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
  engine/assertion sources are unchanged in this before-build. Build/test evidence
  and candidate comparison are pending.
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
