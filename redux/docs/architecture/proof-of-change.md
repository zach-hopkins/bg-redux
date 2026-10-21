# Proof-of-change — source-only bounded probe

Status: **static change-surface assessment only; no engine change executed**. The user's explicit instruction prohibits engine code modifications in this task. The charter permits a justified deferral when a safe experiment cannot yet be executed. A Windows build and test baseline, vanilla save/reload fixtures, normal GUI callbacks, equipped-effect observations and bounded pause/resume measurements are now available, including fresh LAB execution. Those do not supply the full MR-specific acceptance matrix: deterministic extreme-value MR, sequencer exceptions, block-versus-component immunity, saves/half-damage, observer non-interference and lifecycle-safe causal records remain to be tested. This report therefore does not claim an observed implementation change surface or passed MR instrumentation tests. Implementation requires separate authorization after Phase 0.

## Probe: one authoritative MR rejection diagnostic

Question: can Combat Info consume one factual cause without modifying Actor layout, script actions, resource importers, saves or GUI screens? This probes observation extensibility; it does not validate Inventory Redux, navigation policy or a complete event architecture.

### Observed paths

1. Spell/item/projectile blocks enter effect processing; block immunity can reject or bounce before per-effect checks [`gemrb/core/EffectQueue.cpp:2277`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L2277). Direct effect application is another ingress. These paths must be distinguished.
2. First application passes through `EffectQueue::ApplyEffect` and `CheckResistances` [`gemrb/core/EffectQueue.cpp:1127`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1127) [`gemrb/core/EffectQueue.cpp:1078`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1078). The latter checks probability, level, opcode immunity, MR and saves.
3. `CheckMagicResistance` has the source-local “resisted effect” rejection branch [`gemrb/core/EffectQueue.cpp:987`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L987). It already has access to actor/effect and computes resistance; this is a factual observation point.
4. The caller has a sequencer exception to the MR result [`gemrb/core/EffectQueue.cpp:1078`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/EffectQueue.cpp#L1078). Therefore a raw record from the check must say “MR check resisted”; a final “component rejected by MR” record belongs at the enforcing return after accounting for that exception. Native opcode completion can also return `FX_NOT_APPLIED`; result-only inference is invalid.
5. Actor refresh and queued/load-time effects reuse effect processing [`gemrb/core/Scriptable/Actor.cpp:2740`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Actor.cpp#L2740). First-apply gating and lifecycle identity are essential to avoid repeating “new rejection” events during refresh/load.

### Expected future touch points — estimate, not observed diff

| File / boundary | Why it might change | Bound |
|---|---|---|
| `gemrb/core/EffectQueue.cpp` | Emit a typed diagnostic at actual enforced MR rejection, preserving branch/exception behavior | Required resolution edit |
| `gemrb/core/EffectQueue.h` or a small diagnostics header | Define a tiny immutable record/sink seam; avoid a public general bus | Design choice; choose only one place |
| `gemrb/tests/core/` new effect fixture | Construct target/caster/effect cases, verify actual state and trace | New tests, use existing bootstrap |
| `gemrb/CMakeLists.txt` | Register new test source with current core test target [`gemrb/CMakeLists.txt:205`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/CMakeLists.txt#L205) | Test wiring |
| One existing logging/diagnostic adapter or test-only sink | Store records without translated-text parsing | Optional; do not require a UI consumer yet |

Expected surface: roughly 3–6 files depending on record/sink placement, **not measured implementation churn**. Stop and reassess if it requires Actor serialization changes, new globals used across unrelated systems, UI changes or widespread opcode edits merely to expose MR rejection. Full spell-protection diagnosis would necessarily touch more resolution branches and should be a later task.

### Validation and rollback

- 100%/0% MR and controlled effect probability; non-resistible effect; opcode immunity before MR; saving throw after MR; save-for-half; sequencer exception. Assert the branch reached, actual HP/stats/effect state, component count and no invented later blocker.
- Trace enabled/disabled must leave RNG draws, state and ordering equal. Listeners cannot modify state or retain dead pointers. No allocations/formatted strings on disabled path; measure enabled overhead rather than assuming zero cost.
- Assert refresh/load does not duplicate a first-application rejection. Test two consumers only after one record is correct; filter hidden information before any player UI exposure.
- Rollback: remove the optional sink/record integration; no file format, numeric opcode, rules or persistent state changes.

**Observed results in this task:** source paths and enforcing exception traced; no engine source files touched. The separate [baseline build/tests](../testing/phase0-executed-baseline.md) ran; this MR observation probe itself remains unimplemented and unexecuted. The general architecture remains provisional until a real implemented probe records actual files, tests, overhead and second-consumer change surface. This deferral obeys the Phase 0 scope rather than silently doing engine work.
