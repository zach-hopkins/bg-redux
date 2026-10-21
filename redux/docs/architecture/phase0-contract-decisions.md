# Phase 0 contract decisions

October 21, 2026. These are planning decisions for the next implementation slices, not claims that the APIs exist. Engine baseline: `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351`. The current phase permits documentation, characterization and external tooling; engine source and engine/plugin binaries remain frozen. Phase 1 implementation requires separate authorization after Phase 0 acceptance.

The [state map](state-and-dependency-map.md), [subsystem review](subsystem-acceptance-matrix.md) and [extension proposals](extensibility-contracts.md) remain supporting evidence. Later accepted product decisions govern older proposals: BG2EE import followed by versioned Redux saves; a modern UI preserving information/functions; Party Stash always available, no Combat Pack or combat lock; distinct equipment and quick bindings; original artistic composition; hidden combat state separated from earned knowledge. Storage capacity, overflow and legacy actor-ownership policy remain open.

Latest operational authority supersedes the older migration checklist: the user explicitly removed the VM recovery-snapshot requirement and confirmed that guest automation does not interfere with physical-host mouse/keyboard use. Record that input isolation as user-observed evidence, not an independent input trace. VM snapshots are not a Phase 0 gate. References below to state snapshots or supported save points concern runtime observation/persistence, not VM recovery requirements.

## New characterization evidence supporting these decisions

Private LAB run `20261021T232241Z-query-side-effects-74613e6e` completes eight preflighted equipment/defense cases and 144 evaluator calls: 128 weapon-predicate calls plus 16 True/False controls. Collected same-process state is unchanged around every call and at the final comparison; all observed query values remain the frozen stubs' zero results. This is library-mode observation of the collected surface, not proof of hidden RNG/cache/action-queue non-interference or original query behavior. Keep those unknowns visible when implementing ADR-01/03.

Original run `20261021T230944Z-original-live-6efa5f54` now has four nonce E1AEF966 case captures, checked against launch/load-boundary/window, screenshots, executable, private TLK, live scripts and final fixture manifests. Stock Imoen/default tails select 115/307; query-removed controls select 115/307. Native paired run `20261021T232434Z-paired-ai-live-1437dd9a` uses identical final fixture/script inputs and selects 118/310 for stock, 115/307 for controls, with actual action105/declared-target samples. This distinguishes response selection from action/target observation as required by ADR-02/06. Original ENTER markers plus visible combat feedback do not prove a RETURN/queue completion, exact native action/target memory, causally attributed damage or DPR. The original portraits/labels may repeat actor names, so log display names alone are not durable actor identity.

## ADR-01 — preserve operation semantics while introducing mutation boundaries

**Decision:** wrap one authoritative operation at a time, keeping existing synchronous BCS semantics and actor/effect ordering. A future command facade validates intent and calls the compatible operation; it does not grant extensions raw mutable actor storage. Retain import/initialization and deliberate no-callback operations as separately named modes.

**Evidence:** [Actor::SetStat](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Actor.cpp#L2524) clamps and conditionally invokes a post-change callback. [SetBase](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Actor.cpp#L2555) preserves the modified/base delta and can run that callback. [Scriptable::AddAction](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Scriptable.cpp#L377) can execute an instant action before enqueueing. Therefore raw assignment and universally deferred command delivery would change observable semantics.

**Alternatives/tradeoffs:** a wholesale service extraction would clarify names before proving ownership and increases change surface; a public actor-state structure is convenient but cannot enforce callback/order invariants. Incremental wrapping leaves temporary coupling and requires ingress-point inventories, but allows narrow comparisons and upstream review.

**Validation/first consumers:** characterize one read-only predicate and one inventory transfer before moving their ingress points. Compare callbacks, HP/death/charm, action interruption, item conservation and effect order through script and ordinary UI paths. Read-only queries must not consume RNG, ammunition, charges, images, skins or effects. Query side-effect freedom is a required measurement, not inferred from a Boolean return. No generalized command bus or Actor rewrite is selected.

## ADR-02 — scope identity to lifetime and reject stale work

**Decision:** future external commands and observations carry a run/session identifier and load epoch. Long-lived runtime references need a generation/lifetime check; Redux persistent IDs require explicit import/save remapping. Party indices, names, ResRefs and pointers are selectors or observations, not durable identity. Cancel or reject commands/async results after target removal, map replacement or load, and report the reason.

**Evidence:** [Scriptable construction](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Scriptable.cpp#L39) allocates a process counter ID. The [UsedExit comment](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Actor.h#L493) explicitly warns about ID stability after area load. The existing [path scheduler contract](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/PathFinderScheduler.h#L95) already distinguishes request IDs, completion, cancellation and map lifetimes. Reuse those protections instead of bypassing them.

**Alternatives/tradeoffs:** pointer IDs are cheap but expose lifetime hazards; a ResRef/name key aliases repeated creatures; assigning UUIDs everywhere now requires an unproven migration. A scoped runtime handle plus a later persistent mapping avoids that schema commitment, at the cost of explicit stale-reference outcomes.

**Validation/first consumers:** duplicate ResRefs, summons/clones, party reordering, map unload, death/resurrection and load must not retarget an old request. Two fresh-process reloads must bind to the expected logical actor without asserting runtime-ID equality. The complete ownership/deletion graph remains unproven; no smart-pointer conversion is authorized by this ADR.

## ADR-03 — characterize clocks, RNG and delivery before changing scheduling

**Decision:** keep the Classic timing model and current RNG behavior as the reference. Record simulation time, monotonic observation time, update phase and path execution mode separately. Controlled stepping and RNG snapshot/restore are future test capabilities, not substitutes for the real main loop. Do not introduce catch-up scheduling, tick-rate changes or cosmetic RNG separation during Phase 0.

**Evidence:** [Interface main loop](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Interface.cpp#L1053) gates updates by elapsed wall time. [Game::UpdateScripts](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Game.cpp#L1599) drains path completions before map scripts. [Map drawing](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Map.cpp#L1049) advances actor drawing state, and [Actor drawing state](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Actor.cpp#L7915) releases a pending attack projectile at an animation frame. [RNG construction and instance](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/RNG.cpp#L18) use timestamp seeding and thread-local storage. These establish coupling, not an FPS-induced damage defect or determinism.

**Alternatives/tradeoffs:** fixed-step simulation and separated RNG streams could improve testability but may alter draw/order semantics and delivered attacks; a seed alone cannot control worker delivery or animation-linked mutations. Measurement preserves compatibility while delaying convenient replay.

**Validation/first consumers:** bounded pause/resume, loading closure, render-cap/stall, haste/slow, time-stop, missile and melee scenarios; record actual action/target, delivery and elapsed time. Compare immediate, queued and worker path modes, including cancellation. Determine the smallest observation seam before selecting clock/RNG APIs. Multiplayer authority/transport and lockstep remain undecided.

## ADR-04 — preserve resource selection and expose provenance

**Decision:** retain providers/importers and wrap lookup with an explicit requested resource/type, selected format/provider, ordered search context and content digest. Cache keys and invalidation must include the relevant lookup context. New formats may coexist behind adapters; they do not silently supersede legacy precedence.

**Evidence:** [GetResourceStream](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/ResourceManager.cpp#L166) searches paths for one type. [GetResource](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/ResourceManager.cpp#L185) orders resource descriptors, optionally preferring a type, then searches paths. Treating these as the same precedence rule could choose different mod content.

**Alternatives/tradeoffs:** replacing all formats with one canonical file type simplifies tooling but risks loss and unverified precedence; preserving opaque caches makes failures hard to reproduce. Provenance costs bounded metadata and logging, so collect it on lookup/diagnostic paths rather than formatting on every draw.

**Validation/first consumers:** synthetic same-ResRef collisions across loose override/archive, supported descriptors and preferred formats; assert which bytes are selected, repeat under cache reuse and changed provider context. Original game assets stay private. Renderer retention remains the default; modern assets, scaling and art restoration require their own fidelity/performance evidence.

## ADR-05 — legacy import plus explicit, versioned persistence

**Decision:** retain BG2EE parsers as import adapters, inventory the collected/omitted state and preserve raw comparisons. Design a Redux save envelope with schema/profile/module/content compatibility and persistent identity migration before implementing it. Choose atomic commit/recovery behavior and supported snapshot points explicitly; do not grow uncoordinated sidecars or encode new state into undocumented spare legacy fields. Reverse export to unmodified BG2EE is outside initial acceptance.

**Evidence:** ordinary save admission is conditional in [CanSave](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/SaveGameIterator.cpp#L453). [GAM serialization](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/GAMImporter/GAMImporter.cpp#L776) converts runtime ticks to file seconds. [EFF serialization](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/EFFImporter/EFFImporter.cpp#L248) differs in library mode. A successful import/library resave is therefore insufficient proof of normal GUI or all in-flight-state persistence.

**Alternatives/tradeoffs:** universal legacy round trips constrain new state and are not required; immediate invention of a new save format precedes the state inventory. A versioned envelope permits deliberate evolution but needs deterministic failure/migration rules and recoverable writes.

**Validation/first consumers:** preserved original import, normal GUI create/cancel/overwrite, fresh reloads, actor/item/effect/world identities, unsupported versions/modules/profiles, interrupted writes and non-mutating preview/query checks. Distinguish wire conversion, runtime semantics, repeat-import variation and actual behavior differences. IMMCLOUD accumulation also occurs in the original reference; a global deduplication fix is not justified by growth alone.

## ADR-06 — semantic UI and test observations over ordinary operations

**Decision:** use named semantic queries/commands and immutable observations as the future shared surface for UI and automation; retain existing controls/rendering until a measured need proves replacement. Player view models receive only permitted/earned information. Diagnostic observations may be omniscient, but must not be exposed through player listeners. Hypothetical equipment previews must calculate hypothetical state without committing it or consuming resources/RNG.

**Evidence:** [LoadWindow binding](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/GUIScript/GUIScript.cpp#L520) constructs resource-defined windows. Current GUI scripts assemble information on these primitives; blank EE panels are not proof that the renderer or font files are absent. [Effect resistance branches](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1078) and [application result handling](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1123) do not make one generic result code an authoritative causal outcome. Use actual enforced branches for future Combat Info events.

**Alternatives/tradeoffs:** pixel automation tests hit testing but is fragile as an assertion surface; raw actor access is convenient but leaks hidden state and couples consumers to storage; wholesale EE Lua/toolkit replacement expands scope. Semantic operations can test common behavior while screenshots and input tests remain independent requirements.

**Validation/first consumers:** complete inventory/record information and normal save/load operations, then two independently composed UI additions. Test keyboard focus, scale/clipping, drag/cursor semantics and cancellation separately from callback dispatch. Preserve explicit actor ownership until a stash compatibility facade is decided. Modern UI design approval does not enable shared-storage semantics in Classic.

The accepted secondary-panel name is **Stats**, with no duplicated attributes/combat values and a no-scroll target. These are information-design requirements for the future UI slice, not evidence that current incomplete panels satisfy them.

## Harness readiness, completion and observation contract

This is the required contract for external Phase 0 tools and the next semantic adapter. Existing bounded process hosts implement subsets; no live RPC, universal UI tree, controlled stepping or campaign runner is claimed.

| Contract | Required behavior and evidence |
|---|---|
| Run identity | Unique run ID, environment/source/build/tool/fixture hashes, immutable input copy, command/config and bounded process identity. Historical host paths remain historical; fresh guest receipts identify LAB. |
| Readiness | Declare the prerequisite for the requested operation: initialized import, area attached, actual loading window closed, requested screen present, intended pause state. A process start, timer delay, or one cached screenshot is insufficient. Readiness is revalidated after load/modal/epoch changes. |
| Command lifecycle | Distinguish rejected, admitted, executing, completed, failed, cancelled and observation-timeout outcomes. Admission/response entry/queued action are not completion. Timeout is not proof of termination or failure of an underlying action; record owned-process cleanup independently. |
| Completion observation | Pair a fresh scenario/command marker with the actual requested outcome and target identity. For attacks, branch entry alone is insufficient: observe selected action/target and separately queue completion or terminal state. Combat saves are optional observations, not the completion channel. |
| Snapshot consistency | Identify phase/time/epoch and whether state is before area attachment, after recalculation or a completed prior snapshot. Do not mix fields from separate loads as one state. Missing fields remain missing; unknown is not false. |
| Comparison | Separate process, assertion, persistence, repeat-import, rendering and reference-provenance verdicts. Preserve raw and normalized diffs and named normalization contracts. A known difference remains a difference; a missing fixture/report or required skipped test cannot pass. |
| Player knowledge | Diagnostic traces may see hidden state. Player observations must pass a separately tested visibility/earned-knowledge policy; no unobserved expiration, recast or exact timer leaks. |
| Failure/lifetime | Reject stale run/epoch/target, drifted build/fixture and incomplete/stale reference capture. Bound commands and artifact sizes; preserve failed/timeout runs and report cleanup still pending. Serialize use of the LAB game session. |

Validation requires fresh positive and adversarial runs: delayed LOADWIN close, stale output, wrong marker/target, same-name duplicate actor, changed input/build, missing result, incomplete action, timeout with pending cleanup and negative player-knowledge cases. Merely documenting this table does not prove an adapter satisfies it.

## Decision review and continuation

No complete subsystem is selected for replacement. Native plugin ABI/capability manifests, causal MR instrumentation and lifetime-safe command APIs remain implementation candidates rather than installed foundations. The first two authorized implementation slices must report files touched, external consumers, regression scope and measured overhead; reassess the dispositions if the second slice still needs unrelated engine surgery. The [Phase 1 backlog](../roadmap/phase1-backlog.md) sequences those proofs. The [completion audit](../testing/phase0-completion-audit.md) keeps unresolved Phase 0 gates visible.
