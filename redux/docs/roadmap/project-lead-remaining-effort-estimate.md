# Project lead estimate of remaining effort

Estimate date: October22,2026. This is a planning judgment based on the accepted
Phase0 work, current bounded Phase1 results, the Phase1 backlog and the user's
Phase0-through6 goal sheet. It is not a measured productivity forecast or a
promise of completion dates. No reliable cumulative labor or compute ledger is
available, so the multipliers are relative effort units, not billed hours.

**Plan for about30 times as much remaining work as all work completed so far.**
Use a broad15-to60-times range for the full roadmap. Treat completed work as one
block; the central estimate is about30 additional blocks, or31 blocks total.
The broad range reflects unresolved campaign compatibility and later scope.

| Finish line | Estimated additional work, compared with everything completed so far |
|---|---|
| Phase1: faithful, repeatably playable BG2EE campaign | 3–6 times |
| Through Phase3: engine observation/correctness foundations and integrated modern UI/Redux modules | 8–18 times |
| Through Phase5: curated modded campaign plus graphics infrastructure | 15–30 times |
| Full Phase0–6 roadmap, with bounded later initiatives | About30 times; planning range15–60 times |

These are cumulative finish lines, not rows to add together. The ranges overlap
because later scope and reuse are uncertain. Phase6 currently groups additional
games, tactical multiplayer, optional rules and human-led visual restoration;
it has no finite acceptance scope for each initiative. An expansive version can
exceed60 times. That is a scope decision, not covered by a hard upper bound.

In plain English: we have set up the workshop, built useful measuring tools and
fixed several real game problems. We still need to prove the whole adventure
works, finish major screens and systems, and then build the optional features.
A successful opening area or a large passing test count does not mean an equal
share of the campaign is finished.

The testing and packaging foundation should make later work faster. Conversely,
campaign coverage can uncover new script, effect, save and interaction problems;
mods and multiplayer add combinations that current narrow tests do not cover.
This estimate includes implementation, investigation, regression checks,
integration and release validation, not just writing feature code.

Recommended planning: fund and assess the next3–6 blocks toward the faithful
BG2EE release. Re-estimate after several repeatable campaign checkpoints, at
Phase1 acceptance, and when Phase3/6 scope is fixed. More agents may shorten some
elapsed time, but shared LAB sessions and integration remain serial. Do not
multiply elapsed days to date by30 as a delivery-date commitment.

Evidence anchors: [current status](../PHASE1_STATUS.md),
[Phase1 backlog](phase1-backlog.md),
[continuation context](../handoff/BG_REDUX_COMPLETE_CONTEXT.md).
