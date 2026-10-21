# Multiplayer Redux — manager summary

**Status: Core and the combined dialogue/Time laboratory runtime passed their targeted paired gate. The next scene-wait candidate passed offline/native solo checks and is staged on both machines for its paired gate. No public V1 release or broad compatibility claim yet.**
**Test platform:** two physical PCs running disposable BG2EE 2.6.6.0 copies with EEex/InfinityLoader. The active EET and Steam installations were not changed. EET and broader mod compatibility remain design targets, not tested claims.

## Latest design update — 2026-10-09

Tactical Time now targets unlimited Slow at 25% (26.7% after native rounding) and two banked combat Hard Pauses,
with a ten-simulated-second recharge per charge (increased after the GUI gate;
the current running session still uses the earlier five-second value). Ordinary exploration
pausing stays unrestricted. Source regressions, bundle parsing and installer rollback passed on Zach-PC.
The focused paired bank/speed gate passed after a native pause acknowledgement
retry fix; matching permanent bundles are now installed on both closed copies.
Fresh startup of that bundle and the separate scene-wait gate remain pending.
See [paired bank results and limitations](tactical-time-paired-gate-2026-10-09.md).
See [new defaults and remaining verification](tactical-time-defaults-2026-10-09.md).

**Preview/release UI requirement:** Tactical Time needs clear mode/speed and
requester indicators before its next user-facing preview/V1. Optional sound
cues, restrained later color/border polish, authority rules and grouped GUI
acceptance checks are recorded in the [feedback plan](tactical-time-feedback-plan.md).
The initial Tactical Time panel and mouse controls are now implemented. Native
offline callback checks passed on Zach-PC; visual/mouse QA and the paired GUI
gate remain pending. See [GUI results and next gate](tactical-time-gui-offline-2026-10-09.md).

## Latest verified milestone — 2026-09-29, after the combined gate

The combined paired session passed fresh host-owned guarded dialogue, native
fallback in combat, per-player Slow aggregation, Hard Pause/Ready/Unready,
recharge, stale Ready rejection, departure resume, load cleanup and ordinary
one-click/parallel-dialogue regressions. A session-width bug was corrected.
Details: [combined paired results](combined-paired-gate-2026-09-29.md).

The following autonomous offline chunk ran on Zach-PC. It proved that a reviewed
sprite scene command and its trailing actions can wait while dialogue finishes,
then resume once. Canonical waiting/Ready rules and an explicit client dialogue-
opened acknowledgement are implemented. The full native solo cycle and source,
carrier and installer tests passed. Quiet solo combat tracing recorded no active
combat; the earlier paired combat-epoch observation remains open.

Both disposable copies now have matching scene-wait lab bytes. The next grouped
human session checks actual two-screen waiting, readiness, shared control takeover
and lifecycle cleanup. This candidate enrolls only an explicitly armed synthetic
MRDXA sequence; general scene completion, area/global script boundaries,
relocation, stores, GUI and campaign rollout remain work.
See [offline results and next gate](offline-scene-wait-report-2026-09-29.md).

The dated preview/spike notes below retain the development history; their old
"not implemented" and "next gate" statements are superseded by this milestone.

**Content update:** preview 0.1.3 adds an optional four-resource terminal
dialogue component. It passed isolated WeiDU patch/rollback and changed-mod
skip checks. Its runtime remains the paired-tested 0.1.2 runtime; campaign
play-through coverage is still limited. See [review and results](../mod/audit/content-coverage.md).

## Current engineering update: 2026-09-29

The earlier spike limitations below are historical. Core MRDX3 now passed paired
hidden control traffic with ordinary chat preserved, committed revisions,
paused transport, reconnect/load epochs, stale rejection and duplicate handling.
The installed 0.1.2 Interaction preview passed one-click natural dialogue,
same-target exclusion, independent different targets, automatic release and the
tested explicit scripted resource path. The old second-click defect was fixed.

New offline/solo work proved nearby hostiles can be detected before combat;
combat-counter idle alone is insufficient. A per-invocation native flag-return
hook then proved temporary pausing/independent selection while leaving the DLG
unchanged. Exact selected-resource mismatch retained native pause. This could
replace broad file patches after paired propagation and policy integration pass.

The 0.1.4 candidate fixes stale multiplayer arbitration interfering with solo
dialogue. The new context sampler, mode authorization and native mode publisher
are staged source only. They are not included in the installer. Their offline
tests cover missing context, nearby threat, authority, exact identity, expiry,
replay and changed context; they do not establish a deployed encounter guard.

The grouped 0.1.4 paired regression and native mode propagation gate now passed:
one-click interaction and locks retained their behavior; one exact authorized
conversation left the client free; mismatch and disarming retained/restored
shared pause. Both worlds advanced during independent dialogue and final locks
cleared. The mode diagnostic is still excluded from the installer.

Next: host-owned context/eligibility integration, safe takeover while another
dialogue is open, and broader campaign coverage. Stores, observation UI and
Tactical Time's installable implementation remain later work. See
[mode evidence and limits](dialogue-mode-feasibility.md).

Host context/eligibility integration is now implemented in a separate lab build:
canonical resuming ownership, actual actor control, expiry and fresh checks at
native entry. Offline LuaJIT, EEex generator/frame and assembly checks passed.
Its guarded callback and nearby-enemy fallback need the next grouped multiplayer
gate before campaign enrollment. See [integration notes](../interaction/guarded-mode-integration.md).

## What we set out to prove

### Offline batch update — 2026-09-29

A separate combined lab candidate now integrates the guarded host-mode controller
and Tactical Time's Core-backed runtime. Offline tests cover the actual framed
carrier with both feature namespaces, stale Ready epochs, reconnect/load reset,
native observation normalization, and atomic scene preparation ACKs. The combined
bundle parses in the installed LuaJIT and passes isolated WeiDU backup/rollback
without changing TLK. Neither running game has received this candidate yet.

Prepared UI work is a read-only display model and a renderer-independent portrait
presenter, including importance labels, reload cleanup and throttling. No visible
menu or functioning observer control is installed. Shared takeover has tested
barrier rules and a cancellation audit fixture. Native no-response closure now
passes the disposable solo audit; it preserves prior reply effects and skips
the exit reply. Pending-order discard remains unproven, so automatic takeover
is not enabled. The new Time runtime and native guard callback also passed real
solo engine checks on Zach-PC; they still require the paired integration gate.
See [the offline engine report](offline-engine-report-2026-09-29.md).

The next observations are grouped in [the batch plan](offline-batch-plan.md).
Older prototype limitations below describe the original spikes; several have
since been resolved by the paired Core and Interaction gates recorded above.

**Current offline research:** the campaign inventory now combines guide
descriptions with extracted dialogue/script evidence. Narlen's BG1 side quest
confirms distinct quiet negotiation, scripted meeting, combat and rescue paths
within shared resources. External dialogue transitions and globals consumed by
scripts must be reviewed; plot significance alone does not require takeover.
See [the branch review](encounter-narlen-review.md) and
[the interaction/reset goals](interaction-policy.md). These are design and
coverage findings, not newly implemented engine behavior.

Multiplayer Redux has a shared **Core** and two separately useful mods. **Independent Interaction** should let players explore and converse independently, while protecting shared NPCs and global scenes. **Tactical Time** should replace constant multiplayer pause contention with synchronized slowdown, a deliberate Hard Pause, and Ready/Unready coordination. The project order was intentionally driven by engine risk: prove identity and messaging, then independent dialogue and ownership, then synchronized time, before building UI or broad content analysis.

## What we learned and demonstrated

| Area | Paired finding | Meaning |
| --- | --- | --- |
| Core identity and transport | Directly setting an EEex global integer stayed local. We traced native message paths, then sent bounded requests through the game's multiplayer chat transport. The host identified the sender from the active engine player slot, assigned revisions, and broadcast authoritative state. Client and host requests worked, including while the game was paused. | A small, host-authoritative Core is feasible on the existing engine. Native chat is the leading V1 carrier for low-volume control messages; a new `CMessage` is a fallback rather than a prerequisite. |
| Independent dialogue | Changing the non-pausing flag in two disposable DLG resources allowed one player to remain in Jaheira's dialogue while the other moved, used inventory, and held a separate Golem dialogue. Both conversations advanced and ended independently. | The core interaction model works in a real two-player world. The flag is a DLG-level resource setting, not a per-line switch; production should patch selected installed resources with WeiDU, not ship an override for every NPC. |
| Same-NPC ownership | The native engine allowed simultaneous conversations with the same Jaheira. Our host-authoritative target lock denied a competing start, allowed different-NPC conversations, released on dialogue close, and cleared a departed player's host lock. | Same-target serialization is necessary and technically feasible. The diagnostic client gate sometimes requires a second click after grant; a real mod must replay or preserve the original talk order. |
| Global escalation | A synthetic local dialogue branch that called `StartCutScene` alone played a fade while the other player kept moving. Adding `StartCutSceneMode()` produced a genuine shared lock and restored control afterward. | Global scenes require explicit engine escalation. A general classifier for scripted or mod-added branches is still needed; uncertain dialogues should stay native/global in V1. |
| Tactical Slow | EEex's mutable AI update rate changed from 30 to 8 on both peers through host-approved state. Measured game time fell from about 15 to about 4 ticks per real second on each PC, then returned to baseline. Host-triggered and client-triggered transitions worked. A roughly two-minute slow combat run stayed visually synchronized; the probe's safety timer then restored normal speed. | Synchronized simulation slowdown is practical. Rate 8 is about 27% of rate 30, an integer approximation used for the spike; V1's default and configuration remain to be chosen. |
| Hard Pause and Ready | Native multiplayer pause entered from host and client requests. During Hard Pause, the client measured zero game-time advance over about 11 real seconds. Host Ready/Unready and client Ready updates arrived in order; both players Ready resumed the game once. A four-simulated-second recharge rejected an immediate repeat request. When an unready client left, the Ready host resumed. | The coordination state machine is feasible with the Core transport. The current code is a test harness, without combat detection or final UI. |

We tested on a separate `MRDX Lock Lab` save containing two repeatable neutral dialogue targets. This let us repeat ownership and release checks without changing the original `test` save. All experimental game changes stayed in disposable copies.

## What is still prototype work

- **Core:** the first tagged chat packet can still appear in multiplayer chat. We need reliable filtering from startup, preservation of ordinary chat, one versioned protocol envelope, bounded queues, and explicit state reset on leave/rejoin/load. The departed client retained a stale local planning flag in one test, even though the host cleared its lock and resumed.
- **Independent Interaction:** automatic dialogue-close release worked in the tested BG2EE UI, but scripted cancellation, global escalation across real quest content, UI replacements, stores, observer mode, and general mod-added dialogue classification remain. The second-click-after-grant behavior is a usability defect to fix before V1.
- **Tactical Time:** slow intent must be stored per player and aggregated by the host; combat detection, in-combat pause policy, final recharge rules, and UI are not built. The combat observation was visual, not a quantified trace of casting durations, projectile positions, or AI decisions. Human-paced close-together pause requests worked, but truly simultaneous network races were not stress-tested.
- **Compatibility:** only two peers and disposable BG2EE 2.6.6.0 were tested. EET, other EEex/game builds, third-player fanout, and interaction with a broad mod stack need later validation. The diagnostic Ctrl+Shift+2 status shortcut collided with another shortcut and caused a black fade; it has been remapped in the staged future probe and is not part of the product design.

## Decision and next delivery sequence

The central engine risks have favorable answers. Keep chat as the provisional V1 carrier behind a transport-neutral Core API. Formalize player identity, host requests, revisions, per-player state, ownership, events, and disconnect/rejoin cleanup; harden the carrier before freezing its wire format. Then build **Independent Interaction V1** with a conservative set of non-pausing dialogues, same-target locks, and safe global escalation. Build **Tactical Time V1** on that hardened Core, beginning with combat detection, per-player Slow intent, synchronized speed, Hard Pause recharge, and Ready/Unready. Add stores, observer UI, dialogue dependency analysis, and advanced combat visualization after those paths are stable.

The current result supports moving from feasibility spikes into Core design and V1 implementation. It does not yet support a public compatibility or release-readiness claim.




