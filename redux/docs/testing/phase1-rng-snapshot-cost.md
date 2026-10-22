# External RNG snapshot cost observation

Status: **source and validator prepared; not compiled, executed or tested**. No measured cost is claimed. The coordinator must run this separately after the active native guard finishes. This P1-05 diagnostic changes no engine code and does not initialize a game, renderer, configuration or asset loader.

`redux/tools/phase1/native/rng_snapshot_cost.cpp` links the selected candidate core through its import archive. A genuinely fresh `std::thread` first calls the existing `RNG::TrySnapshotState` 100,000 times by default. It records the number reporting an initialized engine, unchanged caller-owned output and a final noninitializing availability probe. Acceptance requires all absent calls false, no output change and no live initialization. It then invokes ordinary `RNG::getInstance()` once, with no seed/reset calls.

Three trials each perform 100,000 snapshot calls by default. Each trial records raw `steady_clock` nanoseconds, iterations, successful-copy count and serialized live-before/live-after/final-copy states. Serialization, equality comparison and file output occur **outside** the timed section. The measured loop includes the API calls and loop/count overhead; it is not an isolated instruction cost. There is no per-call sink, copied-engine draw, reseeding or reset. A separate single genuine `RAND<uint64_t>()` invocation must change the live state after the last trial; a RAND invocation can consume more than one underlying generator value. The process shuts down logging with `ToggleLogging(false, true)` after joining the worker.

The Python validator independently compares complete serialized mt19937_64 states, copied engine size, per-trial continuity, exact counts and fresh nonce/owned PID. It rejects unavailable initialization, absent-output mutation, live trial mutation, incorrect copied state, missing/duplicate/partial trials, malformed states, missing/disconnected draw control, stale output and incomplete processes. Raw nanoseconds and derived nanoseconds/copy remain descriptive: **no speed threshold is applied**. They do not measure the full query observer, serialization/file IO, frame time, combat, other threads or campaign performance.

## Coordinator invocation

Use an explicit candidate source/build pair and fresh result parent. Build and run are separate commands; neither rebuilds the engine:

```powershell
$costTool = 'C:/BGRedux/phase1-local/engine/redux/tools/phase1/rng_snapshot_cost.py'
$costSource = 'C:/BGRedux/phase1-local/engine'
$costBuild = 'C:/BGRedux/phase1-local/builds/20261022T012223Z-candidate-9aa69cd5'
$costPrefix = 'C:/BGRedux/phase0-local/toolchain/msys64/ucrt64'
$costArgs = @('--project-root','C:/BGRedux','--engine-source-root',$costSource,'--engine-build-root',$costBuild,'--prefix',$costPrefix,'--results-root','C:/BGRedux/phase1-local/results')
& "$costPrefix/bin/python.exe" -B $costTool build @costArgs --timeout 180
# Substitute the newly returned unique build directory, never a guessed receipt.
& "$costPrefix/bin/python.exe" -B $costTool run @costArgs --build-receipt '<new-build-directory>/build.json' --iterations 100000 --time-limit-ms 30000 --timeout 90
```

The runner requires a receipt-bound **Debug** CMake cache and compiles the external host with `-g -O0`. It binds full candidate source/binary inventories separately from protected Phase 0 preflight/inventories, plus the exact DLL/import archive, CMake cache/config, compiler, API/header implementation and external helper sources. Run mode requires the successful build receipt, unchanged candidate/tool/compiler inputs and exact host binary hash. It freezes these inputs and uses a fresh private profile and owned PID, rather than attaching to another process. The build identity and all failed outputs remain in unique result directories.

Native iteration count is bounded to 1–1,000,000, with exactly three initialized trials. The default is the requested 100,000 absent calls plus three 100,000-copy trials. A native elapsed budget (default 30 seconds, maximum 60) is checked between bounded phases; it is not a preemptive per-call deadline. Python additionally enforces an owned process timeout (default 90 seconds, maximum 120 for runs), preserves timeout/failure receipts and requires cleanup. Compilation has a separate bounded timeout. Raw timing totals must fit the requested phase-boundary budget; that completion guard is not a performance acceptance threshold. Source/build destinations cannot contain the result directory, and the protected Phase 0 source/build cannot be used as the candidate.

Focused negative/acceptance **test sources** cover absent mutation/initialization, copied/live mismatch, continuity, owned identity, missing/duplicate/count mismatch, malformed engine words/index, timing/budget types and real control detection. They have not been run. Native compilation and execution must establish build/API compatibility and actual costs before any public measured-cost summary is written.
