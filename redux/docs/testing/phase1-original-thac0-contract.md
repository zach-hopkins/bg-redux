# Original EE THAC0 stat contract and matched native divergence

## Measured result

Original BG2EE keeps script-visible stat7 at14 before and after opening Minsc's
Record. The same Record screen displays **Base THAC0:14** and **THAC0:12**, with
Strength18/93. The native combat-details query instead changes script-visible
stat7 from14 to12. A fresh native run using the **exact script-adjusted input
save bytes** reproduces that change. The calculated attack total and the
script-visible stat have distinct observed original contracts in this case.

| Actual stat trigger | Original before Record | Original after Record closes | Matched native before query | Native after query/repeat |
|---|---|---|---|---|
| CheckStat(Player4,14,7) | true | true | true | false |
| CheckStat(Player4,12,7) | false | false | false | true |
| CheckStatGT(Player4,13,7) | true | true | true | false |
| Missing Player6 threshold control | false | false | false | false |
| Unchanged Player1/value14 control | true | true | true | true |

The actual shipped trigger/object identifiers are bound to the earlier
recruitment host resources. [IESDP's primary stat reference](https://gibberlings3.github.io/iesdp/files/ids/bgee/stats.htm)
also identifies7 as THAC0 and names the CheckStat trigger family; it is context,
not a substitute for these executions.

## Controlled input and method

The four-party input comes from preserved native ordinary recruitment result
`20261022T075243Z-minsc-recruitment-072650e1`. This is a declared controlled
cross-engine fixture, **not an original campaign progression checkpoint**.
Only the twenty embedded party script slots are assigned: protagonist override
`RDXTHAC0`, other slots NONE. Reversing those exact byte ranges restores the
parent GAM byte for byte. No actor stat, item, effect or area content is edited.

The compiled observer checks the five predicates above using actual CheckStat/
CheckStatGT records with explicit Player4/Player6/Player1 targets and stat7.
Each true branch precedes its unconditional false fallback. Each query records
its Boolean, unique nonce and next stage. Sample completion requests a scripted
autosave. Existing globals are checked for collisions before preparation.

A private UI.menu adds two sample buttons to the world action bar. They only
queue the declared diagnostic stage through C:SetGlobal. They do not evaluate
triggers, rewrite original Record code, read THAC0 before the first sample or
change character stats. Removing the exact hook/menu addition recovers stock
UI.menu. The original executable is unchanged BG2EE2.7.3.0, SHA256
`b51093a49140b2b8a7c046b4652bb8e535be24ebbc12b1d735e0b94217a14d57`.

The coordinator used the Computer Use skill to load the declared input, queue
sample1, select Minsc through his portrait, open/close the ordinary Record and
queue sample2. The first autosave was frozen before sample2 could replace it.
The output globals contain nonce283056522, phase1/stage106 and phase2/stage206,
with explicit zero results for false predicates and a true control. Both saved
outputs retain the assigned observer identity. Screenshot05 independently shows
the original base14/adjusted12 distinction and selected actor.

## Preserved executions

Original result `20261022T211110Z-original-thac0-reference-e010858c` owns PID3044,
normal exit0. `frozen-before-record` and `frozen-after-record` retain all save
files. Closed verification checks nonce/stages, all ten Boolean observations,
script identities, input bytes, unchanged executable/overrides/private root,
clean-game inventory and protected Phase0 source/binary/fixture guards.

Matched native result `20261022T211801Z-paired-original-thac0-native-600426d0`
loads the exact prepared input and declared same observer BCS resource in a new
private profile. Its fixed query-only runtime calls GetCombatDetails(4,0) and
actual GameScript evaluator predicates. Before the first query stat7 is14;
afterward it is12 and a repeat is stable. Returned ToHitStats is Base14,
Ability−2, Total12. Preservation and bounded characterization checks pass;
`production_accepted` and `world_purity_passed` remain false. Positive evaluator
calls set LastTrigger; no evaluator-purity or AI execution claim is made.

The native runtime is a frozen query-only variation of the external menu host,
not a claimed normal-menu journey. Original uses compiled BCS predicates while
native uses the actual evaluator entry point with the same explicit predicates;
this is not an assertion that all execution timing or hidden state is identical.
Neither reference executes an attack. Original script sampling advances normal
game time and creates declared globals/autosaves, so it does not prove whole-world
or RNG conservation, combat parity, arbitrary save fidelity or fresh reload parity.

[Pinned comparison](../evidence/phase1-original-thac0-contract.json) binds original
preparation, closed verification, image/manifest hashes, both saved samples, exact
native input equality and actual evaluator results. Private rollup:
`original-thac0-contract-review-1792704250484502300/review.json`.

## Correction boundary and additional findings

The [preceding four-actor failures](phase1-stats-actors-query-side-effect.md)
remain rejected. The original reference now rules out warming all actors' script
stat7 to the adjusted attack total merely to make the guard pass. Presentation
must display the calculated12 while retaining the original script-stat behavior.
The full query writing path needs an audit before correction: it updates the
ToHit object/owned raw stat and weapon proficiency cache. Restoring just one
observed field would not establish safety. Inventory/record helpers, selection
refreshes, both hands, script checks, other query callers, effects and RNG scope
need appropriate before/after evidence. Preserve the explicit Classic boundary;
no broad combat-resolution or unmeasured 3E behavior change is implied.

Two additional observations are retained for separate investigation:

- Original Record shows Minsc **3/2 attacks per round**; the matched native API
  returns2 half-attacks and the current presentation shows1. Actual delivered
  attack timing/rate is unmeasured. Do not correct only the displayed fraction
  without establishing the runtime calculation.
- Original portraits show Jaheira51/51 versus native53/53 for this input family.
  The cause and effect/class/serialization relationship remain unestablished;
  this is not a newly accepted HP normalization rule.

No production engine/source/binary change was made in this reference slice.
Candidatebe5f907d/production sourcef8fbd45d9 remains current. The last unchanged
public tooling suite is584 tests at27cd16cdc; those tests do not validate these
private original-game preparers or replace the actual execution evidence.
Existing workers remain usage-limited; all review here is by the coordinator.
All owned original/native sessions are terminal and all results are preserved.
P1-03 and full P1-01..P1-07 remain incomplete.
