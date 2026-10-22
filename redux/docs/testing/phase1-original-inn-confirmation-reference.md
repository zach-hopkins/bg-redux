# Original inn confirmation reference

Subsequent production policy and bounded native OFF/ON/rest/save/fresh reload
evidence are recorded in [the implementation follow-up](phase1-inn-option-implementation.md).
The original reference below keeps its earlier scope and exclusions.

October22,2026. Two fresh private original BG2EE2.7.3.0 profiles load exact copies
of the same preserved, normally saved two-party AR0704 setup. No UI override is
installed in either reference. Prior debug area transfer/100-gold setup remains
explicit; this is not ordinary campaign travel. The executable remains SHA256
`b51093a49140b2b8a7c046b4652bb8e535be24ebbc12b1d735e0b94217a14d57`.

The coordinator used the original UI and physical-pointer automation. The user's
observation that the pointer was slightly too high resolved the initial talk
targeting problem: click near the keeper's feet and allow the normal approach
to complete. There is no reproduced original dialogue failure from those misses.

| Case | Preserved result |
|---|---|
| More Confirmation Prompts OFF | Feedback shows the unchecked option. Ordinary WINNKEEP dialogue/services/End opens Mithrest Inn. Select Peasant, price1, gold100. One Rent starts the rest movie directly, with no intervening confirmation click. |
| More Confirmation Prompts ON, Cancel | Ordinary Feedback toggles the option, Done applies it, reopening shows it checked. Rent opens “Are you sure you wish to rest?” with Cancel/Rest. Cancel retains the selected Peasant room, cost1 and gold100. |
| More Confirmation Prompts ON, Confirm | Reopen the inn, reselect Peasant, Rent opens the prompt again. One Rest starts the movie; the store then shows gold99 and successful rest/spell-preparation text. The room choice resets to cost0 after completed rest. |

OFF evidence: `20261022T183613Z-original-inn-stock-reload-aaaca1a0`, owned PID15824,
normal exit0. Normal GUI saves `000000026-b` and `000000027-c` are frozen as
`frozen-before-rent` and `frozen-after-off-rest`. Gold100→99; GAM time2726→5215,
delta2489. Displayed time changes from chapter1 two hours to ten hours. Imoen's
post-rest dialogue is completed with choices1,3,Continue,Continue,1,End, followed
by a journal update. Those quest/script changes are preserved, not normalized.

ON evidence: `20261022T190657Z-original-inn-on-reference-f63e470f`, owned PID14524,
normal exit0. Ordinary Quick Save after Cancel is frozen as `frozen-after-cancel`;
normal GUI save `000000026-c` after Confirm is frozen as `frozen-after-on-rest`.
The input has time2523/gold100, Cancel time2559/gold100, and Confirm output
time5036/gold99. Cancel advances only36 compressed seconds during ordinary
interaction; confirmed rest adds2477, including UI/play time. GAM stores
compressed seconds, with300 per game hour, not3600. The initial private decoder's
incorrect wall-clock-hour assertion is retained separately; its corrected version
records the actual raw times. Source authority: GAMImporter scales GAM time by
defaultTicksPerSec; Interface::ReadGameTimeTable uses hour_sec300; the original UI
also displays the eight-hour advance.

`original-reference-verification.json` binds both profiles, original inputs,
frozen/output save bytes, owned exits, unchanged clean-game inventory, unchanged
private root files, absence of UI overrides and all protected Phase0 hashes.
`prepared-readiness-check.json` verifies exact ordered saved spell readiness:
the initial/OFF-before/ON-Cancel lists are identical. Both completed rests have
exactly one saved readiness change: Imoen's mage type1/level3 entry1 `spwi408`
(Stoneskin), flags0→1. Armor `spwi102` remains0; the original AI's Armor cast is
visible after rest. This is not a claim that every slot remains charged afterward,
that healing was exercised (both actors were already at full HP), or that no
other world/effect/RNG state changes.

The ON screenshot after reopening Feedback and both actual prompts prove the live
setting. `option-on-after-cancel.lua` records Over Confirm Everything1 and the
separate Confirm Dialog0. The earlier `option-on-before-rent.lua` was copied before
the original flushed the updated file, so it still contains the seeded0 and must
not be used as persisted-ON evidence. The OFF default write can omit the key;
the observed unchecked UI and direct rest are retained rather than inventing an
explicit serialized zero. No original fresh-process configuration reload is
claimed from either case.

The ON world capture after store Done does not reproduce the OFF companion
conversation. Timing, AI and dialogue circumstances differ, so this is retained
as a bounded difference, not attributed to the confirmation setting. Full
rest-script/dream/cutscene fidelity needs its own controlled comparison. Native
inn checkpoint87848de6 proves its current forced prompt at optionOFF and Cancel,
but has not executed rest. The narrow next implementation is the BG2EE inn
confirmation consumer, followed by fresh OFF/ON/Cancel/Confirm/rest/save/reload
validation; this original reference does not justify waiving those checks.
