# External RNG snapshot cost observation

Status: **coordinator build and bounded native observation complete**; the measured result and independent read-only review are recorded below. The source preparation and invocation details describe the tested instrument. This P1-05 diagnostic changes no engine code and does not initialize a game, renderer, configuration or asset loader.

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

Focused negative/acceptance tests cover absent mutation/initialization, copied/live mismatch, continuity, owned identity, missing/duplicate/count mismatch, malformed engine words/index, timing/budget types and real control detection. The coordinator reports all 13 passed; the implementing worker originally prepared their sources without execution. The separate native receipt below establishes build/API compatibility and the measured costs.

## Actual bounded Debug observation

The coordinator completed `20261022T023525Z-rng-cost-run-15ba419e` with an owned process (PID 3460), exit 0, no timeout and complete cleanup. Result SHA256 is `4a14cc17bb19714b82691485b8301532d6d6789fda64a6ef914e1ef6a5cdb7bf`; raw native SHA256 is `5afcd5b5a483529cb98d2f88eea4983218459e48c2bd33362c0bab48ed2c86f4`. The [public cost summary](../compatibility/evidence/phase1-rng-cost-lab.json) binds the driver, Debug core DLL/import archive, compiler, cache, manifest and result identities. The coordinator also reports all 13 focused validator tests passed; this worker launched no test or native process.

The fresh thread's 100,000 absent snapshots all return false; its caller-owned output is unchanged and the subsequent availability probe remains false. After normal initialization, all three 100,000-call trials return true on every call. The copied engine is 2,504 bytes. Raw timings are **1,570,800 / 1,578,900 / 1,533,500 ns**, or **15.708 / 15.789 / 15.335 ns per snapshot**. Live before/after states and the last copied state match in each trial; inter-trial state continuity also matches. The separate actual RAND control starts from the final live state and changes it. The 30-second phase-boundary budget remains a completion bound, not a speed threshold.

Independent read-only review checked native schema/nonce/PID, all 13 serialized state records (313 words each), absence/trial/control equality and continuity, raw timing divisions, driver hash and all 14 live plus 14 frozen input pins, including core/import archive/compiler/API/helper sources. No pin differs; candidate, protected Phase 0 and bound-input guards pass. The benchmark uses core `79650612926d96a8748320bcf3d0f8f265f7d20747448a30a5ec8918b472ebb9` and external host `114dc5bf138bfcc79ce39c274611a5d4625af472b0f4d3b7988edb255e7c5752`.

These three measurements describe one LAB Debug API-call loop with loop/count overhead. Serialization, equality comparisons and file IO occur outside the measured sections. They are not the full observer cost, an optimized-build result, a cross-platform comparison or a frame/combat performance claim. No performance pass threshold or Phase 1 completion follows from them.
