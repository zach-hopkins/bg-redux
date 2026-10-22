# External native color save/reload journey

Status: source/test preparation only. No worker builds, test execution, native
launches or actual journeys were performed. The coordinator's prepared inputs
at `C:/BGRedux/phase1-local/results/20261022T021632Z-color-fixtures-c8e396c4/preparation.json`
are reused only after source/hash/control validation. Their nonce is1455348314;
preparation is not an execution receipt. Original comparison remains separate.

`redux/tools/phase1/saved_npc_color_journey.py` offers explicit `build` and `run`
modes. Both require `--project-root`, `--engine-source-root`, and
`--engine-build-root`. Build additionally requires a new `--output-dir`;
run requires `--build-receipt`, `--preparation`, and `--results-root`.
No engine build is invoked. A later coordinator invocation can begin with
`--cases controlled-high`; omitting cases selects all three declared controls.

## External host boundary

`native/phase0_gui_probe_snapshot.cpp` is a byte-identical source copy of
`C:/BGRedux/tools/phase0/native/gui_probe.cpp`, SHA256
`68142b1ef795995e145c2f4572d69a276d21dbf4a9500a1300a83fd191e65db4`.
The serializer copy remains identical to the Phase0 save probe, SHA256
`d4f332b73c5a0bf579538de5624add4172d460ed880ae73d1c1cdfd13a11ad1e`.
Neither Phase0 file is edited. Build requires both identities to agree with
their originals and freezes all native/runner/helper/startup sources.

The build generates a separate host source through four unique, checked
anchors: serializer filename, external hook include, required
`--save-after-clock 1`/live-clock mode, and one hook after the final paused clock
snapshot. Missing/duplicate anchors fail. The hook calls ordinary
CreateSaveGame with force=false and a screenshot preview, records before/after
save state, exact return code and the uniquely named output directory, then
lets the existing host exit. CanSave refusal or ambiguous/missing output fails;
no SetStat/SetGlobal success injection, forced save, loop rewrite or engine
instrumentation is added.

Build receipts bind the generated source, frozen source closure, compiler,
candidate source/header/core/plugin inventory and host binary. Run rejects
source/compiler/host/generated-input drift and mismatched candidate inventories.
This requires a fresh external color-host build; older GUI/query/cache receipts
are not interchangeable.

## Three genuinely separate processes

Each selected case runs serially through these fixed stages:

1. **create:** load the exact prepared save, which must contain no embedded
   RDXCOLOR; allow ordinary script creation, observe clocks/readiness/color,
   pause and perform the ordinary save.
2. **reload-1:** exit the first process, freeze its output save, copy that
   immutable save into a new profile, launch another process and observe/save.
3. **reload-2:** repeat with the second frozen save in a third fresh process.

Every launch has a new private GamePath wrapper, profile and cache. The case's
exact private table/CRE/BCS overrides remain the same throughout. Fresh resource
creation is required only in stage1; saved nonce/case/stage2/readiness must
prevent recreation on both reloads. Exactly one NPC is required after creation
and before/after both reload intervals. The first paused snapshot can precede
completion of ordinary creation; it is recorded without manufacturing readiness.

The default is40 running samples, bounded to8–80. Each host has five initially
paused samples, the requested running interval and four final paused samples.
The run timeout is positive and at most90 seconds **per process**: three such
budgets per case, never an unbounded retry loop. Owned timeout cleanup is provided
by the existing external baseline executor. There are no automatic retries.

## Evidence and interpretation

Actual NPC identity/runtime ID, base and modified stat212, low bytes, position,
inventory and effect records are retained at clock/save boundaries. The
paletted-human animation/race/neutral allegiance and exact case/nonce/stage/
readiness are guarded independently of any expected color. Monotonic clocks,
paused time, real progression, normal load/readiness events, completion,
non-stale outputs and ordinary save results are mandatory.

The serialized NPC color byte is independently read from the frozen SAV/ARE/CRE.
Saved GAM globals must retain case/nonce/readiness. Serialized bytes are not
called runtime colors. Both source and copied input saves, all previous native
output/frozen saves, configs, original overrides and copied overrides remain
manifest-checked. Save outputs must stay inside the owned profile and cannot
overwrite the copied input. Source preparation is rechecked at finalization.

Each case reports its actual color sequence and any difference across fresh
process reloads. Such a difference is a characterization result; it is not
declared an original compatibility failure or waived as correct. No expected
237/46/stock runtime result is encoded. First original execution must establish
the comparison contract. A process/setup/evidence failure remains failed even
if partial color snapshots exist. Blocked saves retain their actual native
return-code receipt and raw state.

Phase0 and candidate before/after inventories are separate guards. Private
wrapper source inventory/root hashes are validated even after failure. Run
manifests explicitly avoid traversing nested shared asset links while retaining
private root logs and all owned outputs. This is known-root-write isolation,
not a filesystem security boundary or a full linked-asset content hash claim.
All failures and generated inputs remain in unique result folders.

Focused test sources cover exact/missing/duplicate hook anchors, partial
creation versus required reload identity, actual changed colors without an
invented oracle, wrong nonce/readiness/NPC/palette, failed/forced/ambiguous saves,
clock disorder/type/coverage/pause failures, stale/missing/discontinuous evidence,
and nested private-wrapper manifest pruning. They are **unexecuted by the worker**.
Native compilation, focused/full unit execution and the first actual journey
remain coordinator gates before any result claim or engine fix.
