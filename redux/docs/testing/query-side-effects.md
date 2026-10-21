# Fixed EE query side-effect characterization

October 21 LAB continuation: [final coverage and limits](phase0-expanded-coverage.md) and [release evidence](../PHASE0_RELEASE.md) supersede historical pending-run statements below. Original live branch/combat capture, repeated-query state observations and the 151-test consolidated baseline are now executed; known differences remain.

This external observer characterizes the existing `WeaponEffectiveVs` and
`WeaponCanDamage` stubs without implementing them or editing the engine. It uses
the same eight declared equipped/defense fixtures as the paired query work:
normal/+1 sword baseline, normal/+1 sword against synthetic magical-weapon
protection, normal slashing against 100% slashing resistance, +1 against three
Stoneskins, +1 against three mirror images, and bow with forty normal arrows.

## Build and run

From the materialized runtime workspace, after coordinator review:

```powershell
& C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe -B C:\BGRedux\tools\phase0\build-query-side-effects.py --project-root C:\BGRedux
```

The command prints the fresh private `build.json` path. Supply that exact path:

```powershell
& C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe -B C:\BGRedux\tools\phase0\query_side_effects.py --project-root C:\BGRedux --build-receipt C:\BGRedux\phase0-local\query-side-effect-probes\BUILD_ID\build.json
```

The build script links a new external host to the preserved core import library
and DLL; it does not invoke CMake or change the existing save/GUI hosts. Every
default build destination is unique. An explicit nonempty `--output-dir` is
refused. Compiler/driver/source/DLL hashes, command, process result and a frozen
source copy accompany the new executable. Compilation has a 240-second bound.

The Python runner requires the existing `baseline_runner.py` preservation/process
helpers. It validates the pinned engine binaries/plugins, tracked engine source,
all manifested game files and the original six-file vanilla fixture before
constructing the private cases. Native launches are serialized, with isolated
profiles/caches and 120 seconds per case by default. Only the coordinator should
launch it; it must not overlap another controller of the LAB game session.

## Exact observation contract

The native host includes the established external snapshot serializer under
`REDUX_GUI_HOST`, suppressing its original main function. Library-mode import,
party consolidation, game-control creation and area attachment complete before
the measured state surface begins. There is no normal render/main loop,
simulation tick stepping, game save or original-executable execution.

Before measurement, both fixed query strings must parse through the exported
`GenerateTrigger` function as trigger IDs `0xec`/`0xf2` with MAINHAND=1.
`GetAllObjects` must resolve Player2 to exactly the initialized second party
actor. Actual sender/target IDs are recorded. The initialized snapshot must show
the selected protagonist, two party actors in AR0602, Imoen as target, the exact
weapon in internal slot35, selected weapon code0/ability0 for swords or ammo
code-24 plus AROW01 in slot11 with forty charges for the bow. Synthetic defense
opcode/mode/magnitude and the corresponding derived resistance/image/skin stat
are independently checked. The documented opcode120 Parameter1 normalization is
allowed only for that precondition; it is not a comparison mask.

The driver evaluates `True()` and `False()` as positive/negative controls, then
alternates `WeaponEffectiveVs(Player2,MAINHAND)` and
`WeaponCanDamage(Player2,MAINHAND)` for eight repetitions by default. Every call
uses the actual public `GameScript::EvaluateString` path and writes complete
before/after JSON snapshots. The runner checks all eighteen observations per
case, order, explicit Boolean values, control outcomes, snapshot continuity,
native equality against independently calculated leaf differences and the final
snapshot against the last observation. Repeats may be explicitly set to1–32.

The frozen implementations log only after resolving Actor sender/target. The
runner therefore also requires exactly eight actual stub diagnostics per query
at the default repetition count. Unknown-trigger or missing-target zero results
cannot substitute for successful invocation. Unexpected nonzero values are
reported separately from state invariance and do not pass the frozen-stub gate.

No field normalization is applied to the same-process comparisons: collected
base/modified stats, inventory slots/charges/flags, effect fields/order, globals,
locals, spellbooks, identities, positions, journal and game time remain visible.
Any observed mutation is retained with the exact call and raw leaf differences.
New unique result directories preserve captures, fixture construction, logs,
configuration, native commands, frozen observer sources/binary/build receipt,
before/after protected-file inventories and artifact hashes. The original
fixture, engine source, four engine/test binaries, 45 plugins, import library and
manifested game files are rechecked after execution.

## Limits and acceptance

`characterized-no-collected-state-mutation` establishes only this sampled
surface around these fixed current-stub calls after library-mode initialization.
It does not establish hidden/internal RNG state, caches, action queues, all
possible engine state, normal-loop behavior or future predicate implementation
side-effect freedom. A zero result still reproduces a missing compatibility
predicate; it is not a defense correctness pass or original-runtime parity.

The worker compiled the host successfully against the frozen LAB DLL and ran
sixteen focused mutation/negative tests without launching the native observer.
Fresh native execution remains a coordinator acceptance step. Tests challenge
fists/wrong ability, missing/exhausted ammo, missing derived defense, wrong target,
zero parse failures, wrong parsed hand, failed evaluator controls, missing repeat,
stale case ID, understated mutations, discontinuous snapshots and incomplete
state surfaces. Full raw snapshots distinguish observed invariance from omitted
or normalized state.

```powershell
& C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe -B -m unittest discover -s C:\BGRedux\tools\phase0\tests -p test_query_side_effects.py -v
```
