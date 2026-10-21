# BG Redux — current status

Updated October 21, 2026 on LAB. Phase 0 technical deliverables are accepted after independent review under the existing engine-source/binary freeze. The user's plan
names milestones 0A–0F; 0D alone is not treated as full phase closure. Engine
implementation remains separately authorized work after phase acceptance.

## Verified evidence

- LAB shell, VMware identity/Tools, six cores/12 GiB and SVGA3D are verified.
- Base and context packages are transferred, with 57,092 final manifest members
  matching. The active fork was preserved; historical provenance remains intact.
- Transferred UCRT64 Python runs all 71 original harness tests successfully.
- External hosts rebuilt in the guest. Vanilla import/reload passes 24/24
  assertions and GUI/save/reload passes 20/20. Both preserve compatibility
  `differences`; native process success does not certify full fidelity.
- Engine source, four baseline binaries, 45 plugins, core import archive and
  original vanilla fixture remained unchanged in the native-validation run.

See [release evidence](PHASE0_RELEASE.md), [expanded coverage](testing/phase0-expanded-coverage.md), [original live comparison](testing/lab-original-live-comparison.md), [native validation](testing/lab-native-runtime-validation.md) and
[guest transfer](testing/lab-guest-bringup.md). Raw results remain private under
`phase0-local/results/`; the latest consolidated run is
`20261021T232725Z-baseline-c11bb92c`; the external-host rebuild archive is
`20261021T225115Z-lab-native-validation-d3a4ff65`.

## Current work and gates

| Milestone | State | Next evidence |
|---|---|---|
| 0A LAB operational | Runtime checks verified; user confirms host input isolation | Snapshots explicitly removed as an acceptance requirement by user on October 21; retain fresh guest evidence and source/binary preservation |
| 0B Reliable baseline runner | Implemented, adversarially tested and freshly executed | `20261021T232725Z-baseline-c11bb92c`: 151/151 units; capabilities; 24 vanilla and 20 GUI assertions; execution passed, compatibility differences preserved |
| 0C Original combat observation | Four isolated original live captures validated and frozen | Fresh nonce/case/branch/combat feedback; exact original target memory, queue completion and DPR explicitly unproven |
| 0D Compatibility characterization | Declared matrix executed | Eight paired equipped cases, four exact-input AI pairs, eight repeated-query cases/144 calls, persistence and save-callback interactions; see coverage/dispositions |
| 0E Architecture contracts | Six ADRs and prioritized backlog reviewed | Current versus proposed behavior distinguished; source-only MR proof deferred under engine freeze |
| 0F Phase 0 release package | Technically accepted after both independent reviews | [Release record](PHASE0_RELEASE.md), requirement audit, preserved receipts and publication sources |

Only the coordinator controls the game session. Two isolated worker worktrees
provided baseline-runner tooling and architecture/audit documents; both final reviews are complete. Shared runtime
changes and integration are serialized. No engine code changes are authorized.

Known compatibility findings remain visible: missing weapon predicates,
repeat-import area-NPC colors, raw HP/item representation differences, equipped
effect accumulation also observed in original BG2EE, and incomplete inventory/
record presentation. None is waived merely to close the phase.

## Latest authority decisions

- October 21: user confirms guest automation does not interfere with physical
  mouse/keyboard use. This is a user-observed isolation result, not an independent
  host input trace.
- October 21: user explicitly states VM snapshots are not required. Remove both
  clean-install and validated snapshot gates from Phase 0 acceptance. Preserve
  package manifests, existing files, run artifacts and engine hashes as before.
  Older snapshot requirements in historical handoffs are superseded.

Coordinator technical acceptance is recorded in [the release](PHASE0_RELEASE.md).
Phase 0 is complete within its declared characterization scope. Phase 1 engine
implementation remains unapproved. All private results and worktrees are retained.
