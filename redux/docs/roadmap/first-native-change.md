# First native change candidate — causal resistance diagnostics

Classification: **instrumentation and engine observation**, with no intended rules, balance, content or save-format change. Status: future proposal only. The current task remains Phase 0 research/planning; implementation requires a subsequent authorized task after runnable prerequisites.

## Problem and resulting behavior

Current effect processing has separate block immunity, probability/opcode immunity, MR and save branches, but shared return codes do not carry an authoritative cause [`gemrb/core/EffectQueue.cpp:2277`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L2277) [`gemrb/core/EffectQueue.cpp:1078`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1078) [`gemrb/core/EffectQueue.cpp:1127`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1127). A future Combat Info UI cannot safely reconstruct the cause from those codes or translated logs.

Before: diagnostics/log messages exist, but a consumer cannot rely on a typed “this component was actually rejected by MR” record. Proposed after: an opt-in immutable diagnostic for that one enforced branch, with logical ordering and source/component/target identity. Gameplay and player information remain unchanged. This is the smallest useful native seam; a complete event bus is not required.

## Prerequisites

1. Successful pinned build/demo smoke and at least one BG2EE actor/effect fixture, with no unaccounted required-test skips.
2. Deterministic extreme-value MR fixture or explicit RNG control; baseline state and draw counts recorded.
3. Confirm the event contract, branch versus final enforcement distinction, per-game lifetime and diagnostic-only access. The MR sequencer exception must be represented correctly [`gemrb/core/EffectQueue.cpp:1078`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1078).
4. Preserve Classic behavior and current save import. User-approved versioned Redux saves do not require changing persistence for this probe.

## Implementation boundary to evaluate later

See [proof-of-change](../architecture/proof-of-change.md) for the inspected trace and estimated 3–6-file scope. Prefer a local sink seam and test record to adding a global public mutable event bus. Keep the legacy callback/return behavior. Do not touch Actor layout, combat math, numeric effects or GUI screens for the first rejection record.

## Acceptance and validation

Use F01/F02/F03 and T01/T02 in [golden scenarios](../testing/golden-scenarios.md). Require exact MR/no-MR/irresistible/immunity/save/half-damage/sequencer cases, no duplicate refresh/load record, no later hypothetical cause, no RNG/order/state difference with sink off/on and lifetime-safe consumption. Benchmark bounded diagnostic overhead on a representative effect-heavy scene only after correctness. No estimated performance improvement is claimed.

Reviewer receives actual diff/touched-file count, before/after semantic state, raw test results including skips, observer-information policy and rollback instructions. If the first implementation needs unrelated actor/save/GUI surgery, reassess the seam rather than expanding the task invisibly.

## Why navigation follows instead of leading

The current source already contains snapshot-based multithreaded pathfinding, cancellation and movement fixtures [`gemrb/core/PathFinderScheduler.h:95`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/PathFinderScheduler.h#L95) [`gemrb/tests/core/LiveGameFixture.h:24`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/LiveGameFixture.h#L24). Establish their behavior and async delivery first. Navigation Redux changes can alter delivered melee attacks without changing formulas; instrumentation provides a better measuring foundation. Next bounded probe can expose traversal policy independently of steering/spacing, backed by M01/M02 plus APR evidence. Shared stash, tactical time and multiplayer remain deferred.

## Updated sequencing after executed baseline

The [native testing client](../testing/ai-first-harness.md) now implements fixture lifecycle, state queries/selection and import/resave/reload outside engine source. Prioritize controlled full-loop stepping/RNG and semantic UI state before this MR probe, alongside missing-text diagnosis and deeper save fidelity. The MR proposal remains the first combat-causality extension, not a requirement to instrument combat before establishing trustworthy execution. Modern UI preserves information/functions rather than exact EE layouts; [existing Redux context](../architecture/redux-project-context.md) supplies requirements. No gameplay enhancement is authorized by this sequence.

## Native save/harness execution update

[Executed save results](../testing/save-import-and-harness-results.md): the new human-created vanilla BG2EE fixture imports and reloads twice through an external host, with 24/24 scenario assertions. Party/stored NPC/world metadata is stable in those reloads; repeat original import varies NPC colors. Raw HP/flag representation and library-mode serializer differences require reference validation. The earlier EEex save is retained as an unsupported negative fixture. Fixture lifecycle, native queries/selection/snapshots now work outside engine source; prioritize deeper fidelity, controlled stepping/RNG and semantic UI.

## Compatibility priority after original query execution

The [original-script comparison](../testing/original-script-query-results.md) now demonstrates missing EE weapon predicates with positive/negative hand/target controls. A narrow compatibility predicate implementation is a separate candidate from the first combat-causality instrumentation seam. Do not let the MR proposal block a characterized compatibility fix, or substitute new combat resolution for a read-only query. Complete equipped-weapon/defense characterization and side-effect constraints before choosing its implementation scope. Phase0 has not authorized engine edits.
