# Proposed Minsc cage-release checkpoint (source-only)

This is a bounded next AR0602 checkpoint design, not executed evidence or implementation approval for engine changes. It continues only from the measured three-party save at `phase1-local/results/20261022T054005Z-cell-recruitment-ac33ed70/recruit/frozen-save`. It does not replace the remaining Phase1 scope.

Private independent KEY/BIFF/TLK/DLG and saved GAME/SAV/CRE/ARE inspection: `phase1-local/results/20261022T072157Z-minsc-source-design-77a6ef41/mapping.json`, SHA-256 `9abf6102117d251d98ef70dd9a4107b8240bd8b978833056f69dceed3092132a`. It records exact provider/resource hashes, parent result/manifest and six save files, the full private dialogue mapping, selected transition rows, initial actors/doors, and frozen relevant engine-source copies. Original game assets remain private. No build, test, runtime, original-game process, or production edit was performed for this design.

## Exact starting contract

Parent result SHA-256 is `73479cf269f2aa27e3651db75dec2bc6779b2b2c051a44569f96fdc5ed2bba55`. The saved GAM/SAV hashes are `64e5833d97499b2ffb6186640667bc1b24844ee7bb946cd28b7f1f99e24deae5` and `aee7d02f2d641456dce7eb25aef14cc0356d2c3e685de41f2196f4b225a62e2f`.

Party: leader (3816,2706), Imoen (3720,2826), Jaheira (3898,2676). Minsc is one stored NPC in AR0602 at (4029,2759), dialog **MINSCA**, TalkCount 0, XP 90000, with Boo item MISC84. His embedded CRE SHA-256 is `da0e2339074ab4b7742512e05be191a6b123b6e450b2195be9220c3c574cb089`; scripts include override MINSC, general MINSCX and default DPLAYER. Cell02 has flags 610, no key resref and lock difficulty 100. Cell01 is already open/unlocked (1633), Jaheira is already party member 3 with dialog JAHEIRAJ/TalkCount 2, and quest 47519 is solved. Those prior outcomes must remain intact.

## Natural initiation and uncertainty

MINSC.BCS's first block is `NumTimesTalkedTo(0)` plus `Range(Player1,6)`, followed by action 198 (`StartDialogueNoSet(Player1)`, verified against shipped ACTION.IDS). A user-style talk command can race that auto-initiation while approaching. Prefer a separately declared zero-host-dialogue-request version: after normal startup readiness, issue exactly one ordinary movement command toward the previously exercised corridor near (3909,2753), then wait for actual Minsc/leader dialogue. Do not teleport, move the NPC, alter AI, retry the command, or manually start dialogue on timeout. The endpoint's reachability and actual final range remain unmeasured for this new route; failure must be retained.

`GameScript::Range` uses searchmap coordinates and a `(6+1)^2` comparison (`Triggers.cpp:1536`); searchmap tile conversion is in `Region.h:96`. Exact actor radius/line-of-sight and movement outcomes must be observed rather than inferred from pixel distance. A source-supported auto-initiation claim is appropriate; an exact traced action-198 cause requires an actual sample.

Imoen's two interjections are conditional on `IsValidForPartyDialog("Imoen")`. Party membership alone is insufficient: `Triggers.cpp:270` also checks current dialogue participation, interrupt eligibility and visibility. The primary route below assumes that condition is observed true. A declared alternative may omit the two interjections when the actual condition is false: MINSCA 20 uses local0/global39 directly to state32; MINSCA29 uses local0/global49 directly to state13. Never silently reinterpret a wrong speaker/strref as the expected branch. Imoen's actual eligibility from this checkpoint has not yet been measured.

## Resource-derived primary response path

Rows name the dialogue resource, internal source state, displayed NPC strref and selected **local/global source transition**. These indices are source mappings, not observed private engine-state indices. Numbered selections must use the normal `SelectAvailableOption` route only after the actual visible text/value mapping is checked; unnumbered transitions use the actual Continue/End callback. Never assume a conditional local index equals a visible choice index.

| DLG state | NPC strref | local/global | response strref / action |
| --- | --- | --- | --- |
| MINSCA 0 | 2306 | 0/0 | 2356 |
| MINSCA 1 | 2364 | 2/6 | 2395 |
| MINSCA 8 | 2524 | 0/22 | Continue |
| MINSCA 20 | 19993 | 1/40 | conditional Continue to IMOENJ7 |
| IMOENJ 7 | 38539 | 0/9 | Continue to MINSCA43 |
| MINSCA 43 | 38542 | 0/75 | Continue |
| MINSCA 32 | 25066 | 0/54 | 25067 |
| MINSCA 34 | 25071 | 1/59 | 25091 |
| MINSCA 38 | 25101 | 0/66 | 25102 |
| MINSCA 39 | 25105 | 0/69 | Continue |
| MINSCA 26 | 20008 | 0/46 | End; ordinary script unlock/open/restart |
| MINSCA 40 | 25106 | 0/70 | Continue; solved quest 47518, erase 34106 |
| MINSCA 41 | 25107 | 0/71 | Continue |
| MINSCA 42 | 25108 | 1/73 | 25110 |
| MINSCA 22 | 20001 | 0/42 | Continue |
| MINSCA 23 | 20002 | 0/43 | Continue |
| MINSCA 10 | 2530 | 0/25 | 2548 |
| MINSCA 29 | 20018 | 1/50 | conditional Continue to IMOENJ8 |
| IMOENJ 8 | 38543 | 0/10 | Continue to MINSCA13 |
| MINSCA 13 | 2547 | 1/31 | 2557 |
| MINSCA 15 | 2564 | 0/34 | End; AddExperienceParty(3000), then JoinParty |

State26's final transition queues `Unlock("Cell02")`, `OpenDoor("Cell02")`, then `StartDialogueNoSet([PC])`. Wait for actual flags/open state and fresh restarted dialogue; send zero host door commands and zero manual restart requests. State40 has the initial condition `OpenState("Cell02",TRUE)` and transition flags 276 (journal/solved/action); state0's NumTimesTalkedTo(0) no longer applies. No key acquisition or consumption belongs to this route.

## Proposed observations and persistence acceptance

Allow a bounded 180-second live phase plus 90-second fresh reload, under a total parent timeout. Startup must be naturally ready; retain initial, command-before, every branch, before/after script restart, joined, before-save and final snapshots. Bind real speaker/target IDs (including Imoen interjections), names/dialog resrefs, freshly appended sentence occurrences, numbered choice text/values, Continue/End labels, callback count, current/next actions and clock samples. Capture each boundary. Do not require an instantaneous action to appear at a slower observer sample rate.

After final End, wait for actual JoinParty and queued effects. Source-derived expectations: party 3→4 with the same Minsc identity exactly once; MINSCJ assigned via shipped PDIALOG; Cell02 locked/closed 610→unlocked/open 609 while unrelated bits remain; prior three party identities and solved47519/prior journals retained; solved47518 section2/chapter1 present, unsolved34106 absent. This selected route never adds34106 first, so absence alone is not proof that EraseJournalEntry executed. No new forced quest global is justified by these DLG actions. Minsc TalkCount2 is source-expected from two real starts, pending actual observation.

Record actual XP at each boundary. `AddExperienceParty` uses divided ShareXP before JoinParty (`Actions.cpp:2988`, `Game.cpp:1228`); it does not grant 3000 to each new member. Three eligible existing party members would nominally receive 1000 each; eligibility/scaling and actual values must be recorded. Minsc's existing90000 and Boo ownership must be preserved unless a real stock action explains a change. No combat or hidden-RNG purity claim follows.

Use ordinary GUI Save callbacks, freeze the resulting save, then load it in a new owned process with a distinct nonce. A new bounded four-party GAME/CRE/SAV parser and PORTRT3 manifest are needed in separate files; do not loosen the shared two-/three-party validators. Verify party/dialog/TalkCount/XP, Cell02/Cell01, quest journal, Boo and prior inventory across serialized bytes and fresh runtime. A screen saying the cage is open is insufficient without door/party/save evidence.

Pin MINSCA/IMOENJ/MINSCJ, MINSC/MINSCX scripts, ACTION/TRIGGER/OBJECT IDS, PDIALOG, TLK/KEY and actual runtime provider streams. Preserve private GamePath wrappers, parent/Phase0/candidate/build/compiler/source closures, immutable source saves and all failure prefixes. Provider precedence from runtime is still a required observation; archive extraction here is not a substitute for actual provider binding.

Focused negative validator cases should reject a wrong parent/nonce, already-open Cell02, missing/duplicate Minsc, false fresh-text evidence, wrong conditional speaker/response value, duplicate movement/dialogue/door requests, fabricated restart without actual state changes, party4 without solved quest, XP assigned as per-member3000, missing fourth portrait, mismatched reload input and stale build/provider closure. This is a proposed source design only. Actual callback execution, original-game reference parity, physical pointer input and campaign completion remain unobserved.
