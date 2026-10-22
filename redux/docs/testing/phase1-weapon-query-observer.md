# Phase 1 six-hand query observer

This external observer evaluates the actual GameScript handlers for
EffectiveVs/CanDamage against Player2 with MAINHAND1, OFFHAND2 and BOTH3. It
does not simulate an attack, step the normal game loop, save or run either
original UI. Compilation and owned bounded launches require an explicit CLI
invocation; the implementing worker has not compiled or launched it.

## Explicit roots and coordinator commands

Run the new tool from the integrated source tree after the coordinator owns
the candidate build. All four roots are explicit; the Phase 0 engine/build
remain separate. The example candidate path is the existing first candidate,
not an instruction to reuse it after core source changes.

```powershell
$tool = 'C:/BGRedux/phase1-local/engine/redux/tools/phase1/weapon_query_observer.py'
$python = 'C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe'
$candidate = 'C:/BGRedux/phase1-local/builds/20261021T235026Z-candidate-1c6316a3'
& $python -B $tool build --project-root C:/BGRedux `
  --engine-source-root C:/BGRedux/phase1-local/engine `
  --engine-build-root $candidate `
  --output-dir C:/BGRedux/phase1-local/weapon-query-hosts/first-candidate

& $python -B $tool run --project-root C:/BGRedux `
  --engine-source-root C:/BGRedux/phase1-local/engine `
  --engine-build-root $candidate `
  --build-receipt C:/BGRedux/phase1-local/weapon-query-hosts/first-candidate/build.json `
  --preparation C:/BGRedux/phase1-local/results/20261021T235241Z-weapon-oracle-ccf85085/preparation.json `
  --results-root C:/BGRedux/phase1-local/results --repeats 8
```

The build destination must be new. The run creates a unique timestamp/UUID
directory. `--cases` selects exact prepared case IDs; unselected cases are
reported. `--timeout` bounds each build or owned native process; timeouts and
nonzero native exits fail execution, even if partial snapshots exist.

Add `--original-receipts <result.json> ...` to compare selected cases with
explicit original captures. Missing references are **not compared**. A run
with no complete original comparison returns an observation-only status,
`not-fully-compared`, rather than claiming compatibility. Differences,
mutations, unstable repeated values, setup/evidence failures and timeouts
return a failing status. Execution and compatibility are separate fields.

The original GUI launch itself must use the private game's directory as its
working directory. An earlier coordinator launch without that directory
crashed before menus; that launch failure is not a predicate observation.
This observer's owned native process uses the explicit candidate build as cwd
and puts its DLL directory first on PATH.

## Observed surfaces and controls

Initialization is the prior Phase 0 library-mode path: load the exact copied
six-file fixture, validate effects, consolidate the party, create game
control/map and select PC1. Before queries, require exactly two actors in
AR0602 and distinct PC0/Player2 runtime IDs. Each of the six compiled query
parses must have the expected trigger ID and hand, and resolve exactly the
declared Player2 pointer/runtime ID. True()/False() are separate controls.

Each case has eight repeats of all six queries by default:48 predicate calls
plus two controls. Every call writes independent full-state and weapon-cache
before/after files, with native equality flags. Python checks exact file/call
identity, continuity, native flags against independently computed diffs,
complete state surfaces and final snapshots. It rejects missing files, reused
call paths, incomplete controls, unexpected stale artifacts or contradictory
equality claims. Mutations are retained with concrete paths and raw values;
they are not normalized away.

The copied serializer is byte-identical to
`C:/BGRedux/tools/phase0/native/save_probe.cpp`, SHA256
`d4f332b73c5a0bf579538de5624add4172d460ed880ae73d1c1cdfd13a11ad1e`.
It captures256 base/modified stats per actor, inventory, effects, spellbooks,
locals/globals, identity, positions, game time and journal. The new observer
also captures both **actual cached** `WeaponInfo` entries: item resource,
item/CRE flags, base and adjusted cache enchantment, slot/mode, selected header
index and header attack/location/damage/dice/charge fields.

Runtime guards require exact equipped ability0, main/off-hand/ammo slots,
40 ammo charges, item references, cached item/header identity, raw flags,
cached enchantment and derived diagnostic resistances. The range combination
guard uses the existing engine cache's max launcher/ammo enchantment as a
setup assertion; original-query semantics are compared independently against
the captured reference. Empty/shield off-hand cannot silently borrow main-hand
cache. Inventory-table order may differ on EE export, but item multiplicity,
physical slot mapping and selected ability/ammo remain exact.

The state claim is limited to collected same-process state and the captured
weapon caches after library initialization. Hidden state, RNG internals,
uncaptured caches and future normal-loop scheduling are not proven unchanged.
No old stub log-count or all-zero expected-value rule is used.

## Frozen provenance and original references

Build and run record Phase 0 preflight and before/after source/binary/fixture
inventories separately from candidate tracked source/core/plugins/import
library/config inventories. A candidate change after the external host build
invalidates that host receipt. The compiler, observer/serializer/validator/
generator sources, external binary and build receipt are hash-bound and
frozen. Clean game files are verified before/after native runs. Every result
keeps raw logs, configs, inputs, per-call snapshots, reports and an artifact
inventory, including failed attempts.

Original references use schema
`bg-redux-phase1-original-weapon-case/1`. Require observation success, exact
preparation SHA, case/index/nonce, original executable SHA, unique BCS SHA and
all six final input files. Rehash the entire frozen autosave and independently
read its GAM using `inspect_output`; its six values must equal the receipt.
Window/profile/loaded-fixture provenance is required but remains an operator
observation, not automatic OCR or exact original runtime-memory sampling.

The original capture's artifact inventory, preparation, case script,
load-boundary screenshot, selected/loaded screenshots, observation and launch
receipts are independently cross-checked and copied in full into the native
run. Rewriting a Boolean in the result JSON cannot override frozen wire
evidence. Duplicate/unselected references are rejected.

## Checks performed by implementing worker

Python standard-library suite:37 tests total (16 fixture/ingestion tests and
21 native-observation/reference/build-receipt tests). They cover actual six
query order, controls, cached flags/header/enchantment/off-hand, launcher/ammo,
derived resistance, missing/stale/raw evidence, timeout/nonzero receipts,
continuity, independent state/cache mutations and contradictory equality,
repeat instability, expected-value binding and original frozen-wire drift.

```powershell
& C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe -B `
  -m unittest discover -s redux/tools/phase1/tests -v
```

Read-only ingestion of actual original case22
`20261021T235959Z-original-weapon-case-a929b033` independently checked its five
frozen save files,15 capture artifacts and all bindings; values were
`1,1,0,0,1,1`. This validates receipt compatibility only. It is not a native
candidate result. No C++ compilation, native observer process or original
game process was performed by this worker for this assignment.
