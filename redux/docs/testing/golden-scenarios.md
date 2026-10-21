# Golden scenarios and validation design

Status: proposed acceptance suite at the [audit revision](../BG_REDUX_PHASE0_AUDIT.md), now with [executed baseline results](phase0-executed-baseline.md). Stock/importer tests and existing synthetic/live movement were run; the opening is human-verified playable with UI defects. The scenarios below are still acceptance specifications unless that result record explicitly supplies coverage. “Golden” must distinguish original BG2EE reference from current GemRB characterization: GemRB output is not automatically the correct original behavior.

Follow-up coverage: [normal GUI save/presentation tests](gui-save-and-presentation-results.md) execute stock load/create/cancel/overwrite/fresh-reload paths, with20/20 content/callback checks. Inventory/record captures and font comparisons characterize incomplete EE presentation; IMMCLOUD effect differences keep persistence acceptance open. These are partial B01/P01 evidence, not golden visual or complete save parity.

## Harness reuse

- Terrain path tests use synthetic TileProps/ASCII maps without Game/Interface/video [`gemrb/tests/core/Test_PathFinder.cpp:5`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/Test_PathFinder.cpp#L5).
- LiveGameTest bootstraps a demo engine, unpauses scripts and forces 0-worker immediate paths [`gemrb/tests/core/LiveGameFixture.h:24`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/LiveGameFixture.h#L24). Reuse for actor/map tests rather than creating another bootstrap.
- TestGameLoop::RunFrame calls selected engine phases [`gemrb/tests/core/TestGameMap.h:210`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/TestGameMap.h#L210); it is not the whole real-time Main/drawing loop. It resets GameTime to 1 before AdvanceTime(1) each frame to avoid the absent GUI clock callback. It therefore cannot establish long-duration effect/timer fidelity unchanged. Timing/render fidelity tests need the actual loop or a carefully specified new runner.
- Movement/save compilation has a platform/backend condition [`gemrb/tests/core/Test_Movement.cpp:8`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/Test_Movement.cpp#L8) [`gemrb/tests/core/Test_SaveGame.cpp:82`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/Test_SaveGame.cpp#L82). CI must report discovered tests and skipped fixtures. Asset tests can use licensed synthetic/demo resources; privately held game/save fixtures run only where available.

## Minimum suite

| ID / priority | Scenario and assertion | Headless feasibility | Reference and dependencies |
|---|---|---|---|
| B00 / P0 | Demo initialization, smoke and clean shutdown/reinitialization | Offscreen display likely; upstream Linux uses Xvfb | Binary/config/log; no original BG assets |
| B01 / P0 | BG2EE new game/load, opening dialogue/cutscene and transition | Logic partially; presentation check required | 2.7.3 manifest, disposable saves; expected quest/global state |
| R01 / P0 | KEY/override/language lookup collisions and missing resources | Importer/unit or initialized core | Synthetic collisions assert exact provider/bytes; cover typed versus descriptor lookup |
| M01 / P0 | Six actors doorway, wall/corner, dynamic door, sizes | Existing live/synthetic scaffolding | Assert no wall tunneling, bounded arrival, actual path and blocked ticks |
| M02 / P1 | Moving target, haste/slow, ally/enemy/charm, summon and cancellation/map unload | Live core, immediate plus queued/worker modes | Assert no stale path application or dead reference; delivered attack opportunity recorded |
| C01 / P0 | Stationary melee, hit/miss/critical, 0/0.5/1/1.5/2+ APR, haste | Live core proposed; needs controlled rolls/clock | Original/reference outcomes and long-run count/order; animation-linked delivery must be exercised |
| C02 / P0 | Cast, interruption, target death/allegiance change before release | Actual loop and live core | Assert slot consumption, damage and projectile target/release timing |
| F01 / P0 | MR vs saving throw vs opcode/block immunity | Live core proposed; start deterministic extreme cases | One branch at a time and stacked defenses; verify actual reached branch, never hypothetical blocker |
| F02 / P0 | Save-for-half, bounce, absorption, dispel/removal, multi-effect spells | Live core proposed | Per component outcome and resource counters; `FX_NOT_APPLIED` alone insufficient |
| F03 / P0 | Timed, delayed, permanent and equipped effects across refresh/load | Live core + private save | Derived/base stats and expiry; do not double-apply permanent effects |
| S01 / P0 | BCS Continue/Wait/ActionOverride, action interruption and object selectors | Live core proposed | Script/action sequence, state snapshots, globals; legacy immediate semantics preserved |
| S02 / P0 | Dialogue/cutscene pause, area scripts, timers and quest item checks | Live core partly; visual interaction required | Original game saves and authored sequence checks |
| I01 / P0 | Equip/unequip, stack/charge/bag, full target inventory, actor-specific transfer | Live core plus GUI interaction | Conservation of item count/charges, equipment effects, ownership query results and overflow behavior |
| P01 / P0 | Original BG2EE save import then Redux/current save-reload | Existing conditional save scaffold + new state comparisons | User choice: import fidelity; reverse executable export not initial requirement |
| P02 / P1 | Missing mod/resource/schema, duplicate actor keys and interrupted save | File/serializer harness proposed | Explicit rejection/recovery; no silent loss/overwrite of source save |
| T01 / P0 | Same orders under 30/60/high FPS, induced stall, pause/fade/shake/dialogue | Actual loop with offscreen render possible | Record simulation ticks, rolls, actions, releases, hits and states; timing source is under test |
| T02 / P0 | Repeat seeded/controlled scenario across immediate/queued/worker path modes | Live core proposed | Separate route choice from delivery timing; no cross-platform determinism promise |
| V01 / P1 | Palettes/alpha/wall occlusion/fog/projectiles/time-stop and high-res UI | Offscreen capture plus human image review | Fixed camera/viewport/save, software vs GL where available; selected tolerances per effect |
| X01 / P1 | Duplicate/mismatched/missing plugin and cleanup | Startup/offscreen | Assert error category and selected backend; requested missing driver fallback visible |
| U01 / P2 | Two unrelated UI extensions and listener teardown | Python/live UI | Both compose, failure isolated, no duplicate handlers after reload |

## Measurement and oracle rules

Record game/mod/binary/config/profile and fixture hashes. Use logical tick and monotonically ordered cause IDs for proposed traces. Record positions, action queue/current phase, HP/base/derived stats, charges, effect lifecycle, RNG control and path request/delivery ticks. Mask process addresses, wall timestamps and runtime IDs only through an explicit identity mapping; do not normalize away behavior differences.

Use a fixed roll sequence or controlled RNG stream before asserting exact stochastic outcomes. A seed alone does not establish portability: current RNG is time-seeded/thread-local [`gemrb/core/RNG.cpp:18`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/RNG.cpp#L18), presentation can consume randomness, and standard distribution behavior may need characterization across toolchains. Statistical reference tests need stated sample sizes/tolerances; do not invent thresholds without data.

For performance, capture phase CPU time, frame/update percentiles, resource/cache/texture memory, scheduler request latency and contention, and effect scan counts at fixed scenes/party sizes. Reuse upstream Tracy option [`CMakeLists.txt:5`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/CMakeLists.txt#L5) if dependencies can be pinned. No performance numbers or acceptance thresholds are available yet.

For AI-assisted development, every future task should name fixture IDs, actual source ingress and state owner, expected unchanged rules, rollback, and a bounded file set. Do not write assertions that merely mirror implementation branches; use observable game-state and item-conservation outcomes.

Validation still required: complete B00/B01 beyond the observed opening, extend the executed original-save import/reload client to deeper parity/normal-loop checks, capture original-reference artifacts and establish actual-loop timing evidence. Existing nine movement tests pass through the managed entry; they are partial M01 evidence, not the complete six-actor/door matrix. See the [AI-first harness design and implemented external runner](ai-first-harness.md). Passing synthetic movement is useful evidence, not a BG2EE campaign gate.
