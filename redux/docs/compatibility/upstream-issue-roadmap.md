# Upstream issue roadmap toward a native-like BG2EE runtime

Snapshot date: October 20, 2026. This is an upstream-reported risk map, not a list of locally reproduced bugs. Engine baseline remains `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351`; issue bodies/comments can discuss other revisions. Open issues may describe partially implemented behavior, workarounds, old bugs or research questions. Test each against the pinned build before fixing it.

## Scope and evidence

GitHub connector searches covered open issues partitioned by creation date (before 2023, 2023–2024, 2025 onward), plus `EE` keyword and `game: ees` label searches. The date partitions returned 96, 45 and 45 issues respectively; the EE label query returned 18, while keyword search returned 50. These are retrieval counts, not an assertion that every issue is relevant or that the tracker is an exhaustive compatibility specification. Raw query results and selected issue/comment snapshots are in [evidence](evidence/upstream-open-issues.json). The unpartitioned search capped at 100 even when requesting 300, so it was not used alone.

The current [1.0 discussion #2535](https://github.com/gemrb/gemrb/issues/2535) explicitly includes moving BG2EE out of experimental status, verifying ToB completion, attack timing, scripting/dialogue work and projectile bugs. A [maintainer comment](https://github.com/gemrb/gemrb/issues/2535#issuecomment-6086246312) identifies the EE GUI strategy as a major remaining question and notes the shipped classic CHU files already work. This supports keeping compatibility and UI architecture as separate workstreams; it does not establish full campaign parity.

For Redux, **native-like** should mean a faithful, reliable BG2EE SoA/ToB experience with documented intentional UI differences, not merely successful launch or zero open GitHub issues. Require quest/cutscene continuity, combat timing and protections, save import and reliable reload, resource/presentation fidelity, usable input/UI and bounded performance. The original executable's exact UI implementation, Black Pits, other games, EEex hooks and universal mods are separate scope decisions.

## Priority 0: trust, campaign continuity and mechanics

| Upstream report | Relevance and current caveat | Required Redux evidence |
|---|---|---|
| [#92: bitmap-based combat timing](https://github.com/gemrb/gemrb/issues/92) | Describes missing RNDBASE timing behavior, fractional APR and animation/projectile cadence. Directly relevant to recognizable combat feel; do not treat it as permission to change rules | Original-vs-GemRB attack/launch/hit timelines for melee/ranged, fractional APR, haste/slow and cosmetic swings; controlled FPS/stall scenarios |
| [#1665: dialogue queue semantics](https://github.com/gemrb/gemrb/issues/1665) | Initial repro is BG1, but the shared queue/interpreter dependency warrants BG2 regression coverage. Not a proven BG2EE failure here | Interrupt a moving/acting NPC with dialogue; verify action payload timing and cutscene reentry against original |
| [#2345: fade interactions](https://github.com/gemrb/gemrb/issues/2345) | Shared timer research; example is PST. Current source freezes time during fades; game-specific semantics require reference tests | BG2 opening, scripted fades/waits, area transitions, actors/effects during fade, no hangs or hidden payload reorder |
| [#2443: EE lightning bolt replication](https://github.com/gemrb/gemrb/issues/2443) | High-severity projectile report, **already mitigated upstream by a shipped `override/bg2ee/lightb.pro`** at this revision. Do not label the workaround absent or disable override directories | Confirm selected projectile provenance; bounded actor/projectile counts, damage and bounce/secondary-target behavior. Preserve workaround until a demonstrated compatible replacement |
| [#318: SoA-to-ToB import](https://github.com/gemrb/gemrb/issues/318) | Campaign transition/import UI report; open since 2019, not automatically proof of current failure | End-SoA save selection/import, correct party/items/globals and ToB start; separate legacy import from campaign migration |
| [#1404: original save compatibility](https://github.com/gemrb/gemrb/issues/1404) | Mainly asks whether GemRB saves load back in original executables. Redux initially requires import and reliable Redux saves, so reverse export is **not** the first gate | Import private original saves, resave/reload, normalized world/actor/item/effect comparisons; label reverse-export tests optional |

The [save-test maintainer notes](https://github.com/gemrb/gemrb/issues/1404#issuecomment-4353115084) describe remaining BG2EE effect/spellbook/portrait differences and warn about file-static initialization across game types. Run designated BG2EE save tests in a separate process; a mixed-game test suite pass is insufficient.

Local source/runtime findings supplement this upstream map: the opening-area run actually evaluated `WeaponEffectiveVs`, whose [handler is a stub returning0](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GameScript/Triggers.cpp#L4736). Prioritize tracing the caller and original-reference weapon/protection semantics. `WeaponCanDamage` is a neighboring source stub, not yet locally observed. No specific upstream issue is assigned without verifying a matching report.

## Priority 1: EE resources, equipment and presentation

| Upstream report | Relevance / boundary | Fixture |
|---|---|---|
| [#164: missing EE features meta](https://github.com/gemrb/gemrb/issues/164) | Completed sections include modern image formats and several identifiers. Open items include water overlay transparency, CRE fields, TOHv2, autogenerated minimaps/new areas, WBM area animations and campaign/engine tables. Some apply to SoD/BGEE/PSTEE rather than BG2EE | Scan actual 2.7.3 resource usage and parameter modes; rank used semantics, not unchecked checklist length |
| [#2442: Gates District closed doors and night docks](https://github.com/gemrb/gemrb/issues/2442) | EE-specific tiles/PVR bounds report; likely high-value visual/collision test locations, not yet reproduced here | AR0020 open/closed doors and docks day/night; screenshot, collision/LOS and importer diagnostics |
| [#2317: two-handed and off-hand equipment availability](https://github.com/gemrb/gemrb/issues/2317) | EE loadout semantics differ from classic restrictions; distinguish stored inactive weapon choices from simultaneously active equipment | Equip/switch bow/two-handed versus one-handed+shield/off-hand sets, assert active effects and no item loss |
| [#93: externalized character animation](https://github.com/gemrb/gemrb/issues/93), [#2116: avatars.ini migration](https://github.com/gemrb/gemrb/issues/2116) | Modern/EE animation metadata and fallback behavior; not a reason to replace the renderer | New EE creature animation IDs, missing-ID fallback, palette and stance fidelity, effect-driven animation changes |
| [#2330: custom state icons](https://github.com/gemrb/gemrb/issues/2330) | Extra statdesc.2da source column; presentation and mod compatibility | Custom icon frame source, portrait/inspection consistency and missing-resource diagnostics |
| [#897: spell effects under walls](https://github.com/gemrb/gemrb/issues/897), [#896: Fire Storm/Meteor Swarm impacts](https://github.com/gemrb/gemrb/issues/896) | Shared visual fidelity work, independently of attack formulas | Fixed-camera wall/roof occlusion and spell component/VFX references |
| [#2077: circle sizes](https://github.com/gemrb/gemrb/issues/2077), [#2161: door LOS](https://github.com/gemrb/gemrb/issues/2161), [#2355: searchmap checks](https://github.com/gemrb/gemrb/issues/2355) | Shared navigation/collision research. Later source may already cover parts; verify current implementation | Different creature sizes, narrow doorway, changing allegiance, exact path footprint/LOS and delivered APR |

## Priority 2: usability, UI policy and deployment

| Upstream report | Avoid misleading conclusions | Acceptance |
|---|---|---|
| [#2301: EE Quick Loot](https://github.com/gemrb/gemrb/issues/2301) | Open title says absent, but [maintainer comment](https://github.com/gemrb/gemrb/issues/2301#issuecomment-4110497351) says the button now opens GemRB's merged/sorted container solution. Classify as alternative behavior to verify, not wholly missing functionality | Button and Ctrl+W work; loot selection/transfers preserve ownership, quantities and proximity |
| [#2324: GUI quickload](https://github.com/gemrb/gemrb/issues/2324) | Startup resume semantics include ContinueGame, not just picking the newest file | Correct last-save behavior and explicit disabled state; gameplay quickload separately tested |
| [#2450: portrait item-drag highlights](https://github.com/gemrb/gemrb/issues/2450) | Usability gap, lower priority than correct transfer/equip semantics | Valid/invalid recipients and failure without loss |
| [#2546: independent UI scaling](https://github.com/gemrb/gemrb/issues/2546) | Resolution and world viewport are not the same as legible scalable controls | 1080p/1440p/4K layout, fonts, cursor and input mapping; faithful default and documented differences |
| [#2536: language font scaling](https://github.com/gemrb/gemrb/issues/2536), [#2537: live font scaling](https://github.com/gemrb/gemrb/issues/2537), [#1895: font meta](https://github.com/gemrb/gemrb/issues/1895) | English smoke does not prove localization; these do not block the first English engine launch | Supported languages, no clipping/missing glyphs; measure layout before selecting a replacement font backend |
| [#383: individual speech channels](https://github.com/gemrb/gemrb/issues/383), [#2321: video dependency replacement](https://github.com/gemrb/gemrb/issues/2321) | Audio/movie fidelity is separate from game-state correctness; disabling playback is a test-build limitation, not a fix | Concurrent speech and interruption, movie decode/audio sync and complete packaged dependencies |

## Prioritization rules

1. First reproduce crashes, runaway resource use, lost progress/items and broken required progression. Retain shipped workarounds in the baseline and record them.
2. Then fix verified mechanics/timing/protection and script-order differences before balancing abilities or encounters.
3. Address commonly used EE resource/animation/equipment semantics before rare formats not used by the initial campaign.
4. UI policy is now decided: modern UI preserving BG2EE information/functions, inspired by existing Redux work and Infinity UI++. The local run has missing inventory/record text and incorrect typography, so common-screen information completeness is an immediate P0/P1 issue. Polish quickload, scaling, drag feedback and localization after that baseline. Do not equate reproducing EE Lua UI with preserving authored quests/rules. See [project context](../architecture/redux-project-context.md) and [executed results](../testing/phase0-executed-baseline.md).
5. Add pinned SCS/Ascension recipes only after vanilla baseline gates. Do not import IWD2/PST-specific bugs wholesale into the BG2EE blocker count.

A useful roadmap issue entry records: source issue and update date; affected game/version; relevant source symbol; local fixture/run ID; reported/reproduced/mitigated/needs-retest status; severity; observable acceptance; patch/workaround provenance; dependencies and regression tests. Closing the upstream tracker is neither necessary nor sufficient for a native-like Redux release.
