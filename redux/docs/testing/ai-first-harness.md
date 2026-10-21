# AI-first testing harness — Phase 0 architecture and working first layer

October 21 LAB continuation: [final coverage and limits](phase0-expanded-coverage.md) and [release evidence](../PHASE0_RELEASE.md) supersede historical pending-run statements below. Original live branch/combat capture, repeated-query state observations and the 151-test consolidated baseline are now executed; known differences remain.

Decision: automated testing should be a first-class runtime client. Agents need structured capabilities, bounded semantic commands, state observations and reproducible artifacts. Pixel/menu automation should be reserved for presentation/input coverage and selected human checks. An agent should be able to diagnose a failed item transfer or path request without repeatedly clicking through character creation.

**Implemented now:** bounded existing tests plus an external native host for save import, ordinary resave, fresh-process reload, engine-state snapshots, JSON Pointer queries, party selection and declarative scenario assertions. Profiles/caches/inputs are isolated and hashed. A separate test entry closes the logger before DLL shutdown. **Also implemented:** a separate full-loop GUI host with stock load/save callbacks, scoped control text/geometry, font metrics and engine-buffer screenshots. Create/cancel/overwrite and fresh GUI reload pass20/20 content/callback checks; full fidelity remains red. [GUI results](gui-save-and-presentation-results.md). **Proposed only:** interactive engine RPC, universal semantic UI traversal, controlled stepping/RNG and automated campaign scenarios. No engine source was changed; no active player session is attached. [Actual results](save-import-and-harness-results.md) and [tool usage](../../tools/phase0/README.md).

## Existing reusable seams and their limits

| Source boundary | Reuse | Required care |
|---|---|---|
| [LiveGameFixture](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/LiveGameFixture.h#L24) | Interface/demo bootstrap, game control and actor/map fixture construction | Runs immediate paths with 0 workers; assertions do not cover worker delivery or full BG2EE data |
| [TestGameLoop::RunFrame](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/TestGameMap.h#L210) | Bounded synthetic movement | Resets GameTime to1 each frame; omits the complete timer/drawing loop. Cannot establish duration/fade/combat fidelity |
| [Interface UseAsLibrary paths](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Interface.cpp#L404) | Initialized engine services without normal GUI startup | Skips GUI scripting/display/fonts/window manager. Not a complete headless version of normal play |
| GUIScript and GUI Control/Window objects | Existing semantic operations, control IDs and events; useful adapters for inventory/record interaction | Current binding set is not a remote test protocol, stable automation schema or universal composable UI model |
| SaveGameMgr / SaveGameIterator | Private fixture loading and save checkpoints | Stock Windows scaffold skips the configured fixture; comparator can succeed without IEDIFF. Require actual load plus state/comparison receipts |
| ResourceManager and plugin loading | Record lookup/provider/dependency evidence | Current ordinary font logs omit selected type/provider. Add observational tracing at the actual successful selection boundary later |
| Main / GlobalTimer / drawing | Real lifecycle and time behavior | Attack release depends on animation state advanced through drawing. Do not replace it with invented `step()` semantics |

The [executed baseline](phase0-executed-baseline.md) demonstrates why structured outcomes matter: nine movement assertions passed while the process hung; an original-save test exited0 while skipping everything; an OpenGL build silently excluded Windows live tests. These must be three different outcomes in machine-readable output.

## Layer 0: usable external runner today

From the workspace root:

```powershell
python tools/phase0/harness.py capabilities
python tools/phase0/harness.py core --managed --filter 'MovementTest.*' --name movement --timeout 15
python tools/phase0/harness.py core --managed --filter '*' --name expanded-core --timeout 30
```

The managed executable is separately linked; `--managed` is explicit. It runs the upstream assertions with the external `managed-test-main.cpp` cleanup, not a modified engine. Current expanded full result remains one assertion failure, not green. `core` without `--managed` invokes the original entry and can hang after live tests. `ctest` exercises upstream CTest wiring, including its known cwd defect; it is not silently repaired.

Each run gets a unique directory under `phase0-local/results/` with command/cwd, process PID/exit/timeout/cleanup, assertion counts and exceptions, logs, reports, source revision and hashes. An all-skipped or empty core run is `incomplete`. Timeouts override successful assertion output; missing reports are never interpreted as passes. Windows termination is bounded and reports a still-pending process rather than waiting forever. The first implementation's timeout cleanup itself waited too long on an already terminating process; the corrected version records that condition and returns.

Verified mechanisms: two selected string tests pass and exit0; movement9/9 with managed entry exits0; full expanded core exits1 with the known locale failure; configured BG2EE save is classified incomplete; a deliberately interrupted movement run is timeout with terminated child tree. These checks validate orchestration only. Required-scenario completeness, rich error schemas, parallel build/fixture allocation, portable provisioning and report upload remain future runner work.

Build adaptations live in `tools/phase0/cmake/`. `enable-live-tests.cmake` enables existing guarded tests; `managed-live-tests.cmake` additionally compiles the external cleanup entry. Configure using CMAKE_PROJECT_TOP_LEVEL_INCLUDES. `link-managed-tests.py` links the existing compiled test objects to `Redux_phase0_core.exe` without overwriting the mapped engine DLL or original test binary. A future dedicated CMake test project should make this less machine-specific. Do not reconfigure/relink a build currently used for manual play; allocate a second build directory.

## Layer 1: proposed local engine test bridge

The Phase 0 external native host now implements a narrow initialized-state client using existing core APIs. It is stateless between processes. After Phase 0, extend that into a documented test adapter and local pipe/stdio interface if needed. No mandatory web/browser runtime or external agent framework. Agent tooling can consume JSON through a CLI; an MCP adapter is optional later. Existing C++/Python engine operations should remain authoritative.

Proposed responsibilities:

```mermaid
flowchart LR
  A[Agent or CI scenario] --> B[External runner and fixture registry]
  B --> C[Validated local command/query adapter]
  C --> D[Engine main-thread operations]
  D --> E[State snapshots and ordered diagnostics]
  E --> F[Independent assertions and evidence bundle]
```

- `capabilities`: protocol/schema version, enabled command set, rules/data/engine versions, fixture availability and unsupported features. Never make agents discover missing APIs by guessing.
- `load_fixture`: immutable fixture manifest ID, private writable copy, game/profile and expected resource hashes. One game type per process initially, given upstream static-state warnings.
- `query_state`: schema-versioned actor/party/map/inventory/effect/timer observations. Distinguish authoritative committed state, derived state during refresh and UI view-model state. Runtime handles carry generation/lifetime information; persistent identity is a separate unresolved contract.
- `command`: typed move, select, attack, cast, interact, inventory transfer and pause commands routed through the same authoritative operations as normal input. No direct stat teleport/write presented as an end-user test action. Explicit fixture-construction commands have a different role.
- `advance_until`: a bounded condition with tick/time/iteration limits, cancellation and phase label. Never `sleep(10)` as an oracle. Design the actual update boundary first; include timer, script, path delivery, actor and presentation-linked phases needed by that scenario.
- `snapshot` / `save_reload`: normalized state plus identity mapping and manifest references; never hide meaningful differences by masking them as nondeterminism.
- `trace`: ordered action/effect/path/resource events with scenario and cause IDs. Define budgets/overflow reporting, listener lifetime and no-mutation semantics. Do not infer causal outcomes from generic effect return codes.

Mutations must execute at documented safe main-thread boundaries. Return explicit refused, invalid-handle, stale-scene, unsupported, timed-out and completed outcomes, with actual postconditions. Bound message size and queues; launch with the test bridge disabled for normal player builds. A trusted local harness is sufficient initially; an arbitrary network Python-eval endpoint is unnecessary.

**Reproducibility gate:** select controlled clock and RNG injection/state capture semantics before advertising deterministic replay. Current RNG is time-seeded/thread-local and drawing can consume it; a seed is insufficient by itself. Cover immediate, queued and worker path delivery separately. Keep Classic rules and cosmetic draw frequency distinct, but only after tracing current order. Deterministic combat replays and multiplayer lockstep are not implemented promises.

## Layer 2: semantic UI plus rendering evidence

An external adapter now enumerates controls in the named load/inventory/record/options/save packs, dispatches existing save callbacks, and captures text, rectangles, flags, font metrics and engine-buffer images. [Executed results](gui-save-and-presentation-results.md) distinguish content coverage from appearance and retain unexplained save differences. This scoped discovery is useful today; the universal model below remains a proposal.

Expose a queryable semantic tree/view model: stable logical ID, role, visible/enabled state, localized text/string reference, accessible name, selected/held item, count versus charges, bounds, active actor, transaction state and action reason. Logical IDs should survive layout/skin changes; keep legacy CHU IDs as an adapter where useful.

For a modern Inventory Redux screen, an agent should be able to discover `inventory.stats.toggle`, invoke it through the normal UI event, inspect the resulting labels, and verify selected actor/current state. These IDs are illustrative **proposals**, not APIs present today. UI commands should return acknowledgements tied to a UI revision so a stale response cannot be mistaken for a completed new action.

Semantic presence is necessary but insufficient: text can exist while clipped, transparent or outside its control. Pair text/glyph-coverage assertions with fixed-camera screenshots, font metrics, control bounds and image review at supported resolutions. Compare tolerant regions explicitly; do not bless the current incorrect fonts as golden. Test pointer/drag/cursor and keyboard paths through the real input route where relevant.

Reuse the existing Inventory Redux *requirements* and useful scenario cases, not its EEex memory offsets/ownership machinery as an engine architecture. The earlier prototype's launcher/mailbox friction reinforces keeping immutable source manifests separate from mutable run state and acknowledged commands. No manual confirmation ritual should be required for ordinary disposable automated runs.

## First scenarios and priorities

1. **Harness reliability:** lifecycle exit, missing fixture/report, all-skipped required case, timeout, stale response and crash artifacts. Required fixture skips must fail that gate even if optional upstream cases remain skipped.
2. **Opening/UI text:** load an opening checkpoint; assert actor identity, inventory/record labels and values, no unexpected Python exception, screenshot readability. Human reference confirms intended look.
3. **Save:** original clean BG2EE fixture import → snapshot → versioned/current save → fresh-process reload → semantic comparison. Missing IEDIFF is unavailable equivalence, never identical-save success.
4. **Movement/timing:** doorway, blocked destination, cancellation/map unload; compare movement smoothness separately from logical route success. Then actual-loop FPS/stall/pause/fade/haste/attack-release traces against the original game.
5. **Inventory/Combat Info:** item conservation and charges, ownership-sensitive quests, active/inactive equipment; factual MR/save/immunity branches with a player-knowledge filter. No premature shared-stash/rules changes.

Original BG2EE reference execution is a separate adapter and oracle, not supplied by GemRB tests. Existing EEex laboratory reports establish prior-project results only. Curated mod, paired multiplayer and full-campaign tests follow vanilla gates. [Golden scenarios](golden-scenarios.md) define the larger backlog.

The initialized fixture/query/select/save boundary now works externally. The next engine design decision is the authoritative update/observation boundary needed for move/wait/clock/RNG tests and semantic UI state. Normal-loop GUI execution is now distinct from the initialized-state host; neither establishes original-runtime parity or deterministic simulation stepping. Keep the original MR causal-trace probe as the first combat-observation extension after that foundation.

## Implemented effect lifecycle case

The external `harness.py effects` scenario now combines normal GUI load/EnterGame, paused state/protection queries, two same-session refreshes, ordinary native saving and independent saved-area/CRE inspection. Four stock reload/save cycles and three timing-only private item controls characterize IMMCLOUD accumulation. Nine scenario observations and twenty harness tests pass; `characterized` means the observed accumulation is explained, not that compatibility passes. [Results and next gate](immcloud-lifecycle-investigation.md). No generic effect mutation API, deterministic clock or engine instrumentation was added.

## Exposure and original-reference client

`equip-scan` combines read-only item metadata with reviewed private carrier experiments. `original-reference` freeze-copies user-created original saves and compares bounded saved effect records, separating missing fixtures, corruption, file observations and human execution provenance. [Actual status](equip-exposure-and-original-reference.md): wider scan/contrasts execute; original BG2EE GUI reference now shows matching count growth7→14→21, with opcode267 Parameter2 differences kept visible. Operator observation receipts bind executable/save hashes;28 harness tests pass. Full runtime parity remains open. Synthetic reference-gate tests are not original-runtime evidence.

## Behavior and live-clock clients

`string-challenge` observes actual message output after controlled effect applications/removal in three disposable fixtures:48/48 checks. `live-clock` observes actual main-loop pause/resume after LOADWIN closure:10/10 checks across two render caps; configured tick rate is kept separate from measured progression. `cre-loadouts` inventories4,735 packaged creatures, without claiming runtime equipping. [Executed results and limitations](behavior-and-live-clock.md) include startup readiness failure and correction,39 passing harness tests, and the remaining clock/RNG boundary. Neither deterministic stepping nor original-runtime behavior challenge is implemented.

## Generated-script original comparison

`script-query` runs generated BCS predicates and records completion/results through an ordinary scripted autosave. `capture-original-query` freezes and checks a separately observed BG2EE execution using the identical input/script. [Executed comparison](original-script-query-results.md): original weapon queries1/1 versus GemRB0/0 in one fists/MAINHAND case;52 unit tests pass. Missing globals/stages, chapter autosaves and receipt/file drift fail the result gate. This establishes a bounded original-runtime query case; it does not supply original launch automation, controlled clocks or the broader combat contract. Private profile isolation must be checked after opening Load Game because cloud imports occurred later than startup.

`query-matrix` and `capture-original-matrix` extend this to eight per-load queries. Main/both-hand positives differ; empty-offhand and absent-Player6 negatives match. Both saved states require all values and final completion;56 tests pass. Original GUI loading is still observed, while query execution and saving are script-driven. Equipped weapons, defenses and query side-effect checks remain open.

Document validation now preserves historical execution flags instead of rewriting them to success. Its report states that it does not execute builds/tests; the recorded evidence hash stays unchanged. Preserve this distinction between a valid report, an executed experiment, a passing process and compatible behavior in future agent-facing commands.

## Equipped/defense and AI action observations

[Executed extension](equipped-defenses-and-ai-fallback.md) adds eight input/output/runtime equipment checks and four normal-loop AI attack-tail cases. Original equipped queries execute through observed GUI loads and script autosaves; independent rereads show14/16 predicate mismatches. Native AI results require actual action105 against the named foe, not just branch markers or save files. Original AI branch capture remains incomplete because no completed probe save was obtained; manual save reports combat. Per-run build receipts and driver source copies are frozen before launching.71 unit tests pass. Prioritize a read-only observation channel independent of save restrictions, explicit action-queue completion and target identity before broad agent commands. Controlled RNG/stepping remains unimplemented.
