# Bounded LAB baseline runner

Milestone 0B adds one entry point for the selected harness baseline. It uses the
existing pinned engine build, licensed test copy and registered original vanilla
fixture. It does not rebuild engine source, operate the original executable,
attach to a player's session or certify campaign compatibility.

From the materialized runtime workspace:

```powershell
& C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe -B C:\BGRedux\tools\phase0\baseline_runner.py --project-root C:\BGRedux
```

The explicit project root must contain `tools/phase0`, `docs`, `gemrb` and the
private `phase0-local` runtime. A published `redux/` directory alone is not a
complete runtime workspace. The script can also be executed from another source
checkout with the same explicit root; the selected runtime's tools are frozen
in the result directory alongside the runner actually executed.

## Selected execution and preserved evidence

Default steps run serially: harness unit suite, capabilities, vanilla opening
scenario, and stock GUI create/cancel/overwrite/fresh reload. `--steps units
capabilities` selects a subset; every unselected or selected-but-unrun step is
recorded explicitly. The GUI callback tests execute real normal-loop operations
but do not establish mouse hit testing or player-visible completeness.

The vanilla scenario includes import/resave, two fresh-process reloads, repeat
import, party selection, queries and 24 required assertions. The GUI scenario
requires both complete native stages and 20 content/callback assertions. Expected
stage order, native process exit/timeout, completion/state artifacts, BMP capture
signatures and comparison-file counts are checked independently of the parent
summary flags. Stale pre-existing result directories are excluded using the
pre-run inventory and unique unpredictable command name. Missing or contradictory
evidence fails rather than silently skipping.

An exclusive `phase0-local/baseline-runner.lock` prevents two copies of this runner
from sharing the guest. It records hostname, PID, run ID and ownership token. The
runner removes only its own lock. A pre-existing lock requires inspecting the
recorded process; absence of recent text output is not evidence that it is dead.
Other game operators must still respect the coordinator's single-controller rule.

Before launch, the runner checks the registered vanilla fixture against its full
manifest, the four baseline engine/test binary hashes, all 45 plugin hashes and
tracked engine paths against the pinned revision. Current external save/GUI
build receipts must match compiler, driver source, binary and engine DLL hashes.
Core/plugin/import-library, engine-source and original-fixture inventories are
recorded before and after. A preservation change forces failure. Python bytecode
writes are disabled.

Each invocation creates a unique `phase0-local/results/<UTC>-baseline-<id>/`
directory containing `result.json`, `REPORT.md`, raw command logs, command
receipts, machine unit counts, frozen external builds and tool sources,
before/after preservation manifests, native run paths and artifact
manifests for both the coordinator directory and newly created native runs.
Native saves, snapshots, comparisons and screenshots remain in their
own fresh harness result directories; they are not deleted or overwritten.
Historical host reports retain their original provenance.

`--rebuild-hosts` first archives the previous external output directories into
the new run, then invokes only `build-save-probe.py` and `build-gui-probe.py`.
It does not invoke CMake, relink the engine or reuse its copied cache for a build.
The default does not rebuild anything. A failed external build prevents launches.

Timeouts are bounded per operation: unit suite 90 seconds, each native save stage
90 seconds, each GUI stage 150 seconds, capabilities 30 seconds, external builds
240 seconds. Parent command budgets allow the expected stage count plus 30
seconds. Override `--unit-timeout`, `--native-timeout` and `--gui-timeout` when a
different explicitly recorded budget is necessary. Timeout cleanup targets only
the owned child process tree and records any pending termination.

## Verdicts and known differences

Execution, assertion coverage, compatibility/persistence, skips, expected failures,
timeouts and preservation are separate. A command returning `differences`/exit 1
can have successful native processes and assertions; it remains `differences`.
Unit skips or expected failures are visible and prevent an unqualified pass.
The runner exits 0 only for an overall `passed` result and exits 1 for differences,
incomplete/skipped coverage, failure or timeout. Do not use shell exit alone to
identify which of those occurred.

Without explicit references, differences are labeled `unreviewed-differences`.
To compare against independently reviewed frozen runs:

```powershell
& C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe -B C:\BGRedux\tools\phase0\baseline_runner.py --project-root C:\BGRedux --reference-vanilla C:\BGRedux\phase0-local\results\20261021T225226Z-lab-vanilla-import-reload-153ab16e --reference-gui C:\BGRedux\phase0-local\results\20261021T225329Z-lab-gui-save-d4748398
```

References must have complete successful native execution/assertions, the same
engine DLL, fixture and relevant observer-source provenance. Complete reference
run snapshots are copied into the new report. Vanilla known-difference labeling requires exact
wire and reload residuals; repeat-import variability is allowed only at the
previously characterized current-area NPC color-stat indices 208–214. GUI labels
require exact legacy residuals and persistence-scope counts. A changed effect
parameter, extra damage, new HP/item-record discrepancy or missing raw artifact
is not accepted merely because the total difference count looks familiar.

`known-differences` means a residual matches this explicit reference, not that
the residual is harmless or correct. It does not change compatibility verdict,
process exit or Phase 0 acceptance. Revised observer sources require a reviewed
new reference rather than quietly carrying an old label forward.

## Unit validation and milestone acceptance

```powershell
& C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe -B -m unittest discover -s C:\BGRedux\tools\phase0\tests -p test_baseline_runner.py -v
```

The mutation/negative tests cover stale run identity, missing native artifacts,
contradictory comparison counts, failed assertions, missing reloads, native and
owned-process timeouts, incomplete GUI completion/captures, changed source build
receipts, fixture drift and unexpected differences. They use temporary synthetic
records and an owned Python timeout process; they do not launch a game.

0B is complete only after a fresh integrated default run on LAB produces the
consolidated report, verifies preservation and correctly retains the known
non-green compatibility results. Tests of the report machinery alone do not
prove that integration run occurred. The runner explicitly leaves campaign
parity, original combat observation, input isolation, VMware recovery snapshots
and overall Phase 0 acceptance unproven.
