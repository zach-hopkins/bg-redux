# Four-actor Stats journey and observable THAC0 initialization

## Result and scope

**Both complete journeys remain rejected.** The new focused observer covers all
six Stats sections for the immutable four-party recruitment fixture. At1024×768
and1280×768, all77 runtime assertions pass, all24 actor/section contracts and40
page visits are captured, and92 dynamically planned steps complete. Each process
exits0 with45 captures and44 registered callbacks. The strict reader nevertheless
rejects both at its final whole-run conservation check. Process completion and
readable text are not whole-journey acceptance.

| Resolution | Preserved outer result | Owned PID | Strict result |
|---|---|---|---|
| 1024×768 | `20261022T204320Z-stats-actors-menu-run-7e89a03f` | 16828 | `Stats journey changed collected world` |
| 1280×768 | `20261022T205334Z-stats-actors-menu-run-7098280f` | 5908 | Same rejection |

All seven outer preservation guards pass. Engine source and binaries remain the
coherent `20261022T201023Z-candidate-be5f907d` / production source`f8fbd45d9`.
Only external tooling was changed/rebuilt in this slice. The current engine
baseline remains `20261022T202715Z-stats-base-4eeccc08`:24/24 import/reload and
20/20 GUI/save assertions, zero skips, compatibility differences4/0/24 and449/53.
It was not rerun or relabelled as a new baseline after external-only changes.

## Ordinary coverage

The observer opens the real Record window and dispatches the actual portrait
callbacks for the fighter, Imoen, Jaheira and Minsc. It retains the chosen Stats
section when changing portraits, checks page reset and fresh actor content
before another section click, then visits every natural page through registered
Next/Previous callbacks and returns to page one. Names, raw class/level stats,
HP and cached main-hand THAC0 are bound to actual captured actors. Raw level
fields are not a claim that every stored field represents an active class.

The reader checks saving throws, including base/current adjustments, and all
thirteen resistance rows against actual native snapshot statistics and actual
English TLK labels. Other section text is compared with the declared production
assembly/page contract; this is **not an independent class-mechanics oracle**.
It also rejects missing actors/sections/pages, wrong/stale callbacks, hidden or
wrong text, malformed captures, native callback errors and state changes.

Coordinator visual review includes Imoen's ability/chance-to-learn information,
Jaheira's multiclass overview and priest bonus-spell text, and Minsc's skills
with the resolved **Racial Enemy: Vampire** label. Selected text is readable at
both required sizes; exact original font/size parity is still unmeasured.
All four actors have empty portrait-state lists in this fixture, so it does not
cover active status-icon/effect presentation. Source-inferred formatting risks
are not silently treated as reproduced defects.

## Undeclared change

Complete before/after snapshots differ at exactly three paths:

- `/party/3/modified_stats/7`:14→12.
- `/current_area_actors/36/modified_stats/7`:14→12, the same Minsc runtime actor.
- `/selection`:1→4, the deliberate UI selection change.

Stat7 is `IE_TOHIT`. Base THAC0 stays14. Immediate native callback before/after
pairs pass their declared selection-only scope; the final whole-run guard still
catches deferred GUI refresh work between those immediate boundaries. This is
why callback-pair equality alone cannot establish journey conservation.

The separate `stats_failed_review.py` helper first reruns **all strict checks**.
It permits a completed forensic report only for this final world-difference
rejection. Its result always has`accepted=false`; it neither normalizes stat7 nor
turns the failed native results green. Review
`stats-actors-completed-failure-review-1792702897328430200` preserves complete raw
differences and hashes of accessed captures, callbacks, reader sources and TLK.

## Causal isolation and actual trigger observation

Fresh-process result `20261022T205135Z-minsc-stats-query-isolation-376e3659`
uses a frozen, fixed query-only variation of the external host. It loads the
same immutable fixture and calls actual `GemRB.GetCombatDetails(4,0)` without
opening Record, selecting a portrait, attacking, resting or saving. The first
call changes Minsc's raw modified THAC0 from14 to12; the second is stable at12.
Returned `ToHitStats` reports Base14, Ability−2, Total12, with other displayed
adjustments0. Other collected world fields match. This is characterization,
not production acceptance or a hidden-state non-interference proof.

Fresh result `20261022T205833Z-minsc-stats-trigger-isolation-c4e45d44` adds actual
GameScript evaluator calls with explicit Player4 targeting:

| Actual trigger | Before first combat-details query | After / repeat |
|---|---|---|
| `CheckStatGT(Player4,13,7)` | true | false |
| `CheckStat(Player4,14,7)` | true | false |
| `CheckStat(Player4,12,7)` | false | true |
| Missing Player6 threshold control | false | false |
| Unchanged Player1/value14 control | true | true |

Positive trigger evaluation itself sets the sender's LastTrigger; this diagnostic
does not claim evaluator purity, AI-script execution, attack parity or save
equivalence. Both query characterizations pass their bounded observation and
preservation checks while explicitly retaining`production_accepted=false` and
`world_purity_passed=false`. Their native host artifact uses the inherited menu
protocol name; the frozen runtime variation and driver explicitly identify the
query-only scope instead of claiming an ordinary menu journey.

## Source attribution and next correction

GUIScript's combat-details operation calls `Actor::GetCombatDetails`, which
updates ToHit components through the normal combat calculation. In
`CombatInfo.cpp`, `ToHitStats::RefreshTotal` writes the computed total into
`Owner->Modified[IE_TOHIT]`. The Actor combat-calculation source region is byte
identical to the protected Phase0 checkout; CombatInfo.cpp is byte identical too.
Its comment explicitly describes using GetCombatDetails for the full state.
This establishes an existing writing path, **not** a paired Phase0 runtime result,
original EE parity, proof of a new regression, or permission to waive the delta.

Next work must pair original EE THAC0 stat-trigger behavior before/after opening
Record with a nonzero ability adjustment, establish the presentation-query
contract and script/save/attack implications, then isolate an appropriate
correction. A calculated attack total and script-visible stat need not have the
same original contract. Hiding Modified[7], warming
the cache before the measured boundary, or restoring only one observed field
would not establish that all relevant state is safe. Broader effect/class cases,
independent mechanics, original typeface measurements, locales and physical
pointer coverage remain P1-03 work. Full P1-01..P1-07 remains incomplete.

## Tooling and preservation

Final external suite: **584 tests pass**,41.987 seconds at`27cd16cdc`, receipt
`phase1-stats-actors-review-tooling-1792702586761031600/result.json`. The previous
581-test receipts, early failed validator fixture, corrected actor-name metadata,
retained-section adjustment and unused earlier observer build are all retained.
The executed external observer is
`20261022T204234Z-stats-actors-menu-build-e36e35fd`; earlierc01f6d98 was build-only.

The [upstream GUI context](../compatibility/upstream-ee-gui-issue-context.md) was
consulted; these observations do not close its font/encoding or missing-panel
issues. [Pinned evidence](../evidence/phase1-stats-actors-query-side-effect.json)
binds both rejected journeys, completed-failure reviews, both query isolations,
actual trigger outcomes, baseline source correspondence and source tests.
Workers remain usage-limited; review is by the coordinator. All owned sessions
are terminal, and the baseline, fixtures, assets and all results are preserved.
