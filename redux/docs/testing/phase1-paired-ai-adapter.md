# Candidate paired AI adapter

`redux/tools/phase1/paired_ai_live.py` is an external coordinator-run adapter. It does not rebuild the engine or test host. It launches four serial, bounded, owned processes only when invoked in run mode. The worker validated retained evidence and unit tests; no candidate native run is claimed here.

## Frozen comparison

The authorized oracle is exactly `C:/BGRedux/phase0-local/results/20261021T230944Z-original-live-6efa5f54/preparation.json`, nonce `E1AEF966`, and its four `*-observed.json` files. Preparation and observation hashes are pinned in the adapter. The existing original capture validator verifies screenshot signatures/hashes, explicit operator visual attestations, executable/private TLK/engine.lua/script hashes, final `row.fixture_files`, private-window/launch/load boundaries, case/nonce/branch and combat feedback. The earlier `construction.input_files` manifest precedes the unique script resref change and is not the fixture authority.

| Case | Original visually observed branch | Prior native branch | Candidate target |
| --- | --- | --- | --- |
| Imoen stock | 115 | 118 | 115 |
| Imoen no query | 115 | 115 | 115 |
| Default stock | 307 | 310 | 307 |
| Default no query | 307 | 307 | 307 |

The prior native reference is exactly `C:/BGRedux/phase0-local/results/20261021T232434Z-paired-ai-live-1437dd9a`. Its result and preparation hashes are pinned, along with a deterministic hash inventory of its retained driver/build receipt, four historical tool sources, and sixteen clock/state/result files. Native branch, action and target evidence is revalidated before comparison. Those samples are separate from the original visual attestations: original exact action/target memory, queue completion, timing, whole AI behavior and DPR equivalence remain unproven. HP deltas are reported descriptively and are not a DPR acceptance test.

## Invocation

Read-only validation (no new result directory or native process):

```powershell
$oracle = 'C:/BGRedux/phase0-local/results/20261021T230944Z-original-live-6efa5f54'
$observations = @('ai-imoen-stock','ai-imoen-noquery','ai-default-stock','ai-default-noquery') | ForEach-Object { "$oracle/$_-observed.json" }
& C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe -B redux/tools/phase1/paired_ai_live.py --verify-only --project-root C:/BGRedux --preparation "$oracle/preparation.json" --reference C:/BGRedux/phase0-local/results/20261021T232434Z-paired-ai-live-1437dd9a --observations $observations
```

For a coordinator-owned candidate run, remove `--verify-only` and supply **all** of:

```text
--engine-source-root <candidate checkout root containing gemrb/>
--engine-build-root <candidate CMake build root containing config.h and gemrb/>
--probe-source-root <root used by relative sources in the external GUI build receipt>
--probe-build-receipt <successful candidate external gui_probe.cpp build.json>
--probe <matching Redux_gui_probe.exe>
--prefix <UCRT toolchain prefix>
--results-root <private result parent outside source/build roots>
```

The probe must be the normal-loop `gui_probe.cpp` host, not `menu_probe.cpp`. Its receipt must pin the binary, candidate core DLL, compiler and both GUI/serializer sources. The adapter performs protected Phase 0 preflight separately from candidate source/binary inventories. Candidate roots cannot be the protected Phase 0 roots.

Each case receives a fresh profile, cache and private writable GamePath wrapper, an exact final fixture copy, an independently named window, and one owned process with a 90-second budget. The executable, script, private TLK and engine.lua remain exact original inputs. The wrapper copies root files and links assets; this isolates known config writes, not arbitrary filesystem access. Source root hashes and recursive names/size/mtime inventory are checked, plus full hashes for the explicitly bound inputs.

The normal GUI load/readiness sequence must complete, followed by 89 ordered samples: five initially paused, eighty running, four finally paused. Both snapshots and running samples must identify the declared foe and sender consistently; AttackOneRound (105) must target the declared foe in a running sample with that same foe identity visible. Correct markers alone, an autosave alone, stale timestamps, Python callback tracebacks or an incomplete process do not satisfy this requirement. A sampled stock fallback remains an execution observation but fails original branch compatibility.

Every run has a unique directory. It copies bound original inputs/attestations, scripts, validation/driver sources, the driver executable/build receipt and historical native reference files; candidate source/binary content is bound by before/after hash inventories. It preserves case failures, command/config identity, private wrapper receipts and outputs. No canonical or historical result is overwritten. Final acceptance requires all four original branches to match and all preservation checks to pass.

## Validation performed

Read-only verification against the exact four original observations and historical native reference passed, returning original `115/115/307/307` and historical native `118/115/310/307`. The 28 focused Python tests pass. They cover wrong preparation/nonce/case/attestation, missing load/completion evidence, stale or disordered clock boundaries, missing/ambiguous/wrong action targets, weapon and identity mismatch, valid fallback differences, unchanged HP without a DPR claim, frozen-input collision/change, unsafe manifest members, and failed/wrong/stale driver/core/serializer provenance.

Fresh candidate four-case native execution is pending coordinator integration and a coherent candidate host build. Unit tests and retained Phase 0 evidence do not substitute for that run.
