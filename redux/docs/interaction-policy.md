# Interaction policy and background UX goals

Agreed direction, 2026-09-29. Design goals below are not claims of implemented
runtime support. This supersedes any suggestion to force shared dialogue solely
because a conversation advances the main plot.

## Eligibility and compatibility

Aim for broad automatic eligibility based on installed dialogue paths and
relevant scripts, with a small explicit exception registry. Do not maintain a
permanent manual whitelist of every NPC, or unlock all unknown resources by
default. Unsupported/ambiguous content stays native. Reassess modified resources
instead of assuming vanilla state indices. Quiet branches of mixed resources
are a future context-sensitive goal; conservatively retain native behavior until
that branch policy and escalation are verified.

Mandatory native/shared behavior follows mechanical dependencies: combat,
hostile encounter branches, party relocation, coordinated scenes and other
unsafe independent execution. Plot importance alone is presentation metadata,
not a reason to pause or lock another player. The existing non-pausing DLG flag
does not certify eligibility and also controls hostile-interruption reactions.

## Narrative participation

- Eligible main-story dialogue may remain independent.
- Show who is conversing, the target, and an option to observe.
- Important dialogue receives an emphasized notification (red plus an icon or
  label, so color is not the sole distinction).
- Offer **Follow important dialogue by default**. Following should not interrupt
  the player's existing independent conversation; join afterward if still open.
- Consider recent dialogue history for missed content.
- An optional shared-dialogue preference may serve first-time groups. Automatic
  observation and pausing everyone are separate choices requiring UI feasibility.
- The initiating player retains response ownership unless explicitly redesigned.
- Importance classification errors should affect notification, not engine safety.

## Preferred shared-scene coordination: finish current conversations

Updated user direction, 2026-09-29: prefer waiting for existing independent
conversations to finish normally before a mandatory shared scene proceeds.
Forced cancellation remains a fallback research goal, not the default path.

- Notify participants that a shared scene is waiting; identify its initiator.
- Let active conversations finish normally and release their locks.
- Ready expresses willingness to proceed; it must not bypass an open interface.
- Prevent new independent conversations once the host has accepted a pending
  shared transition, so the group can become ready without indefinite churn.
- Start the shared scene only when all required participants are clear and ready.
- Investigate whether a small number of common native entry points can safely
  hold scene or relocation execution. Do not build a separate interception layer
  for every dialogue branch or scripted encounter.
- Crucial gate: holding the scene command must not let subsequent script actions
  run ahead. A callable entry point alone is insufficient evidence.
- If a reliable common boundary is unavailable, use targeted support for reviewed
  encounters and retain native behavior for unsupported dependent content.
- Do not freeze the entire simulation while waiting if that prevents the other
  conversation from completing. Combat and urgent encounters need explicit
  native fallback; waiting must not become an unconditional encounter policy.

This is recorded design direction, not implemented runtime behavior. The first
research step is entry-point and script-order inspection offline; native solo
fixtures must demonstrate the hold before a paired overlap gate is scheduled.

## Fallback: interrupting independent interactions for mandatory takeover

Fallback sequence: host marks takeover pending, prevents new local interactions,
quiesces current interfaces safely, releases their locks, then executes the
native shared dialogue/scene and restores controls after it finishes.

The user's preferred outcome is a **fresh interaction after interruption**, as
close to never having started the conversation as safely possible:

- Close without selecting a response or executing an artificial exit branch.
- Discard unfinished responses, stale replay context and queued talk orders.
- Clear ownership and observer state.
- Do not reopen the old dialogue automatically after the scene or teleport.
- A subsequent click starts against current world state.
- Completed dialogue actions remain committed. Do not roll back arbitrary
  quest variables, items, party changes or effects on shared NPCs.
- Investigate talk counters and entry-time effects before promising full reset.
- Store interruption must wait for committed transaction handling; it is not
  proven by dialogue cancellation and stores are not yet supported.

## Focused acceptance gates, when implementation is ready

Preferred waiting path:

1. A holds an independent dialogue; B reaches a reviewed shared-scene boundary.
2. The scene and its following actions remain pending; A can still finish.
3. Notifications and readiness reflect the host's canonical pending transition.
4. After A closes and the required participants are ready, the scene runs once.
5. Cancellation, disconnect and load invalidate the pending transition safely.

Fallback cancellation path:

1. A holds a looping independent dialogue; B starts a mandatory shared scene.
2. Verify safe cancellation without choosing a reply, shared native behavior,
   ownership cleanup and restored controls.
3. Re-enter A's conversation: no stale screen, actor/resource or replay order.
4. Repeat with relocation; old target must not be resumed remotely afterward.
5. Verify committed earlier effects remain, unfinished effects do not execute.
6. Add store overlap once concurrent store support exists.

Current evidence proves synthetic local-dialogue escalation while the other
peer moves or uses inventory. Overlap with a second active independent dialogue
or store, and safe reset semantics, remain unverified. Native engine behavior
must be observed before choosing how much explicit coordination to add.

## Native enemy-context evidence

The [solo feasibility check](enemy-context-feasibility.md) detected a nearby
hostile for both party portraits while `CombatCounter(0)` still returned true.
Eligibility therefore needs both nearby-threat context and combat state; an idle
combat counter does not establish that non-pausing dialogue is safe. Threat
range, relevant area/actors, changing hostility and host-authoritative fallback
remain implementation work.

The [per-invocation mode proof](dialogue-mode-feasibility.md) now demonstrates
solo pausing and non-pausing selection without mutating the installed DLG.
Resource binding and paired propagation remain gates before adopting it.
