# Phase 0 LAB release and technical acceptance

October 21, 2026. This package completes the bounded compatibility research,
external harness and architecture deliverables for Phase 0 (0A–0F). Coordinator technical acceptance is recorded below after independent review.
Engine implementation remains outside this release's authority.

## Evidence index

Private paths are relative to `C:\BGRedux\phase0-local\results` unless stated.
Raw saves, game content, screenshots, executables and toolchains remain private.
Public documentation and external tool sources are additive under `redux/` in
the existing fork; upstream engine code and license notices are preserved.

| Evidence | Canonical location | Finding |
|---|---|---|
| Base/context transfer | `../transfers/20261021T211457Z` | 57,092 final manifest members match; original active checkout preserved |
| Guest native validation and external rebuilds | `20261021T225115Z-lab-native-validation-d3a4ff65` | Fresh capabilities, vanilla and GUI/save validation; archived builds and preservation manifests |
| Fresh consolidated baseline | `20261021T232725Z-baseline-c11bb92c` | Execution passed; 151/151 tests, capabilities, 24 vanilla and 20 GUI assertions; compatibility remains differences |
| Vanilla child run | `20261021T232732Z-baseline-a613b0790dec-vanilla-e751dfde` | Fresh import/resave/reloads/repeat import; residuals match reviewed reference rules |
| GUI child run | `20261021T232748Z-baseline-a613b0790dec-gui-ec88115c` | Create/refuse-empty/cancel/overwrite/reload; exact legacy residual/persistence scopes match reference |
| Original combat observation | `20261021T230944Z-original-live-6efa5f54` and four frozen `232721Z/232722Z-original-live-capture-*` runs | Four nonce-bound selected responses and visible combat feedback, independent of save admission |
| Matched native AI | `20261021T232434Z-paired-ai-live-1437dd9a` | Four identical-input cases; two stock branch mismatches and two agreeing controls |
| Repeated query side effects | `20261021T232241Z-query-side-effects-74613e6e` | Eight cases, 144 calls, no collected-state mutation; hidden state remains unproven |
| Earlier equipped pairs | [equipped results](testing/equipped-defenses-and-ai-fallback.md) and its frozen public summaries | Eight matched cases, 14/16 differing predicate values; failed setup attempts retained |

The fresh baseline preserves raw differences and exits 1 for compatibility
`differences`; native execution success is a separate verdict. Known residuals
are bound to explicit reference evidence, not waived by their counts. Engine
source, four protected baseline binaries, 45 plugins, core import archive and
original six-file fixture match their before/after inventories in the final
baseline. The pinned core DLL SHA256 is
`5b8719d3f3257404f4611927826af1ae9cdeb2c735fc0ed6d1afc981eb14c99f`;
engine revision is `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351`.

## What is accepted and what remains open

The [completion audit](testing/phase0-completion-audit.md) maps all milestones and
nine charter deliverables. The [coverage matrix](testing/phase0-expanded-coverage.md)
declares the tested boundaries and explicit unknowns. The [original comparison](testing/lab-original-live-comparison.md)
separates visual response entry/combat feedback from native target-memory samples.
Neither a response ENTER marker nor a save file proves action-queue completion.
Some damage feedback names Smoke Mephit while attack feedback retains a cloned
PC display name; it is not evidence binding original damage to RDXFOE.

Missing weapon predicates, incomplete inventory/record information, HP/item wire
representation, area-NPC color variation and equipped-effect accumulation have
documented dispositions. Campaign parity, SCS/Ascension, exact original target
memory, original query side effects, hidden RNG and broad spell/dual-wield
semantics remain unproven. Historical core-test failures/skips are not replaced
by the separate 151-test external suite.

Six [architecture decisions](architecture/phase0-contract-decisions.md) distinguish
current code from future mutation, identity, clock/RNG, resource, persistence and
semantic UI contracts. The MR [proof-of-change](architecture/proof-of-change.md)
is explicitly deferred under the engine freeze; no implemented seam or measured
overhead is claimed. The [Phase 1 backlog](roadmap/phase1-backlog.md) supplies
dependencies, regression criteria and the authority required for each change.

The user confirmed physical host input remains usable during guest automation.
This is user-observed evidence. VM snapshots are optional under the user's
explicit amendment and are excluded from Phase 0 gates. No snapshot was created.

## Reproduce, preserve and recover

Follow [guest bring-up](testing/lab-guest-bringup.md) and the original package
manifests: verify/copy base first, overlay context, preserve the fork checkout.
The materialized root contains `docs`, `tools`, `gemrb` and private `phase0-local`.
The published `redux` subtree alone does not contain a runnable licensed runtime.
Use the transferred UCRT64 Python and pinned external-host build receipts;
never rebuild the engine from the copied CMake cache.

Run the [baseline entry point](testing/baseline-runner.md), optionally with the
documented explicit known-difference references. Rebuild external hosts only
when needed with `--rebuild-hosts`; previous host outputs are archived first.
Use [query side-effect instructions](testing/query-side-effects.md) and the
original-live report for the additional cases. Serialize game sessions, retain
owned PID/timeout receipts and preserve failures. A quiet log is not a stopped
process. Inspect lock ownership before removing a stale baseline lock.

Every fresh invocation uses unique result directories. Keep source copies,
build receipts, original preparations, observation JSON, screenshots, comparisons
and before/after inventories together. The final release receipt hashes the
selected artifact trees and public release sources. Recovery means restoring
the manifested packages and private inputs into a fresh workspace, verifying
hashes and rerunning; it does not promise restoration of the whole guest OS.
No commercial resources or raw private evidence are included in the Git commit.

## Independent review and closure

The runner author did not execute the fresh consolidated LAB run; the coordinator
ran it against the final integrated external tools. Two bounded workers review
actual receipts, capture limitations, source anchors and contract/coverage claims.
Final review findings and coordinator technical acceptance are appended after
resolution. This phase does not authorize Phase 1 engine or gameplay changes.


### Coordinator technical acceptance — October 21, 2026

Accepted under the user's active Phase 0 completion authority: milestones 0A–0F
are complete within the declared research/characterization scope. Both independent
reviews found no material blockers after corrections. The baseline reviewer
rehashed 1,111 coordinator and 1,016 native artifacts, recomputed all 44 assertions
and exact known-difference dispositions, and verified current protected inputs.
The contracts reviewer inspected all nine charter deliverables, 20 pinned source
anchors and 27 local links. Both reviewed the four original captures and their
observation limits; the runtime reviewer independently recomputed eight side-effect
cases and four paired native action/target traces. No reviewer launched a game or
changed shared runtime files.

Resolved review findings: stale MR fixture wording now states the precise deferred
matrix; Phase 1 UI criteria include Stats/no duplicates/no-scrolling; the old Combat
Pack proposal is superseded by the approved stash policy. Known compatibility
failures remain explicit defects. This accepts Phase 0 technical deliverables,
not campaign fidelity or a production runtime. Phase 1 remains unapproved.

The private final release manifest is stored in the unique
`phase0-local/results/*-phase0-release-*/` directory. It indexes the preserved
selected raw evidence and freezes public tools/docs with their SHA256 identities.
