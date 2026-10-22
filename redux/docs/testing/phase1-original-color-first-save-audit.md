# First original color save: independent audit

The first original BG2EE controlled-high save is bound to the prepared inputs.
It contains exactly one RDXCOLOR, serialized leather byte237, zero items/effects
and five NONE scripts. Saved GAM markers are case1, nonce1455348314, stage2 and
ready1. This establishes the first **saved byte**, not an exact original
runtime-memory palette or original reload behavior.

Evidence root:
`C:/BGRedux/phase1-local/results/20261022T022308Z-original-color-installation-08d20bb7/controlled-high-observation/ordinary-save-1`.
The [independent receipt](../compatibility/evidence/phase1-original-color-first-save-audit.json)
records exact installation/preparation/installer/observation, final input,
override, output, launch and screenshot hashes. Receipt SHA256:
`7bd765ee7465400be0d2f3bd005754d8fe23fe9db3bd6e46ad24f7880632337d`.

Read-only rehashing confirmed prepared and installed six-file inputs, all three
private override files, the five frozen/live output files, original executable
and immutable installed root files. The input contains no embedded RDXCOLOR.
Clean source root hashes and recursive metadata inventory remain unchanged;
linked asset contents were not fully rehashed by this audit.

All seven screenshot hashes and recorded window boundaries agree. Independent
static inspection shows CONTROLLED-HIGH selected under the exact private
profile/version title, the loaded map, ordinary overwrite confirmation for the
preserved Chapter 1 Start slot, then “Save successful”. Thus this receipt has
ordinary-save UI evidence beyond the incidental chapter slot name. No screenshot
proves numeric palette237. The failed hidden launch and its cleanup receipt
remain distinct from the visible PID9296/window189990134 session. Normal exit
was reported by the coordinator, not independently process-queried here.

The copied controlled-high input is unchanged. The whole profile is **mutable**:
Baldur.lua changed from744ab0a9… to697fe47b…, and it contains Auto-Save and Chapter
1 Start outputs as well as the original input. Do not claim an unchanged whole
profile. Actual NPC position `[3712,2844]` differs from the requested
`[3781,2801]`; ordinary collision-adjusted creation placement is recorded.

Original fresh-process reload remains unobserved at this boundary. No color
stability, production fix or complete original/native equivalence is approved.
No tests, builds, native/game launches, engine edits or existing evidence
mutations were performed by the audit.
