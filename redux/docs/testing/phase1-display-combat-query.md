# Read-only combat details for EE character sheets

The original-game comparison established that Minsc's script THAC0 remains14
before and after opening Record, while the adjusted display is12. The previous
native query changed script stat7 to12. The two earlier four-actor runs remain
rejected; their evidence is retained in
[the side-effect investigation](phase1-stats-actors-query-side-effect.md).

Production commit `cd83f1e48` introduces an optional third argument:
`GemRB.GetCombatDetails(pc, hand, True)`. It computes 2E display details using a
detached ToHit object and a local weapon-info copy. Shared calculation helpers
retain the existing combat arithmetic. The two-argument API and explicitFalse
retain their legacy behavior. Display mode rejects 3E rules before calculation.
EE character-sheet and supplemental callers use the display mode; Classic
callers keep the existing mode. No field is restored after a mutating query.

The 2E APR arithmetic is factored without correcting the separately observed
original3/2 versus native1 display discrepancy. Jaheira's original51/native53 HP
also remains a separate investigation. Neither discrepancy is accepted as an
intentional fidelity difference.

## Build provenance

The fresh candidate build `20261022T214712Z-candidate-a71c06f9` stopped when the
disk filled. After compression of closed object files, the same configured build
resumed and all remaining53 targets completed. The first resume verifier compared
a hash string against its frozen-copy metadata object and failed bookkeeping.
Both failed receipts and their logs are preserved unchanged.

A separate verifier checked source, compiler-support inputs, successful process
receipts, frozen failure records, all61 output binary identities, and protected
Phase0 inventories. Its receipt is
`20261022T220932Z-candidate-verified-faf62922/build-receipt.json`.
This is a verified resumed build, with output junctions to the original configured
directory; it is not a second build from an empty directory. Its status remains
`built-not-validated` until the required runtime checks are assessed.

## Diagnostic scope

The external display-query host runs the exact script-only input variation used
for the original THAC0 reference. It calls display mode144 times across four actors,
both hands, and128 repeated Minsc main-hand queries. Actual script-trigger results
must keep the original14/12 distinction. Native same-process comparisons cover
all party BaseStats, Modified stats, ToHit and weapon-info object bytes. Calling
thread RNG state is observed without creating or advancing its stream.

All eight samples in this controlled fixture resolve to slot10/proficiency254:
the four characters are unarmed. Both hand arguments are exercised, but this
does not cover a real dual-wield pair, launcher/ammo, weapon proficiency bonuses,
or armed/effect combinations. Extend the display-query evidence to those cases
before treating the correction as broadly runtime accepted. The separate weapon
predicate regression cannot substitute for that display-API matrix.

A deliberate die roll must change the RNG observation. The legacy default query
must expose the known14→12 mutation, while explicitFalse must retain result parity.
A temporary external-host 3E feature flag tests rejection and restoration without
running a 3E calculation. These controls intentionally mutate this diagnostic run;
only its display-query phase claims collected-world conservation. Observer scope
does not establish purity of every hidden field or every thread. Timing covers the
whole Python matrix step, including result serialization, rather than API latency.

The strict Stats reader separately requires raw world and cache conservation
through all four actors and all six sections. It compares displayed THAC0 against
the display result, while cached native ToHit must match script stat7. Visual,
font and physical pointer acceptance remain separate requirements.

## Current checks

The source tooling suite passes603 tests, including16 new negative-control
validator tests. The expected unsupported-3E error is accepted only once, inside
explicit native-host begin/end markers, with the independently observed flag
control and actual caught exception. Any extra or unbounded callback error fails.

The first native attempt stopped before save load because the resumed alias
lacked its configured `Shaders` directory. An additional byte-pinned junction
now exposes that same build's shaders; no resource or binary was changed. The
next attempt completed the matrix and sensitive controls, but its strict reader
rejected the expected unsupported-3E error log. Both attempts remain failed;
the marked-error-boundary host passed a separate fresh execution. An intermediate
external-host compile failure from a missing `<iostream>` include is also kept.

Native result `20261022T221720Z-display-query-contract-2cc042eb` passes the
bounded144-query contract, actual script triggers, byte/RNG conservation,
sensitive legacy/RNG controls, rejection/flag restoration, and all six outer
preservation guards. The matrix Python step took5,893,500ns; this includes
serialization and is not a per-call benchmark.

Both1024×768 and1280×768 stages of
`20261022T221812Z-display-fixed-stats-menu-run-51a7179d` pass92 steps,77 runtime
assertions,24 actor/section contracts,40 page visits,45 captures and44 callbacks
each. Strict world and cache conservation passes, with Minsc display12/script14.
All seven parent preservation guards pass. Capture34 at both resolutions was
inspected for visible Minsc THAC012; this does not establish full typography or
physical-pointer fidelity.

Fresh baseline `20261022T222836Z-display-base-6b4d1dd6` passes24/24 import/reload
and20/20 GUI/save checks, zero skips, and all preservation guards. Compatibility
remains **unreviewed differences**. Vanilla wire residuals matchbe5, but reload
and repeat-import color rows now number0/0/28 versus4/0/24. GUI residuals number
451/55 versus449/53; the only added rows are base/modified color210 on area
actor31,3435973836→875836468. All other GUI residual rows match. No color
normalization, causal attribution to this fix or conformance ruling is made.
The wrapper's exit1 reflects compatibility differences, not failed execution.

Source-bound core run `20261022T223102Z-source-bound-core-388048bf` passes231
tests, with9 skipped and6 disabled; none failed. These results do not erase
earlier Phase0 locale failures or establish coverage for the skipped cases.

Fresh weapon-predicate run `20261022T223310Z-phase1-weapon-query-521dfe4c` matches
all22 original cases, including dual weapons, empty/shield offhands, launcher/ammo
and defense combinations. Across1,056 repeated predicate calls and44 evaluator
controls, collected state, weapon caches and calling-thread RNG remain unchanged.
All preservation guards pass. This checks the existing predicate contract against
the refactored core; it does not exercise the new armed display API.

[Pinned evidence](../evidence/phase1-display-combat-correction.json) and private
review `20261022T223720Z-display-combat-review-03961c7d/review.json` bind these
results,603 source tests, screenshots and exact residual changes. The subsequent
[armed matrix and stock comparison](phase1-armed-display-validation.md) now pass
bounded armed query/GUI conservation, but expose a separate pre-existing
two-weapon THAC0 arithmetic mismatch. Full Phase1 remains incomplete.

## Separate APR follow-up

The successful API sample retains Minsc's native base/modified stat8 as2 and
returns APR2, slot10, proficiency254, range1, flags33, and a1d2 hit header.
`Actor::GetStyleExtraAPR` returns zero for proficiency254, with a comment about
monks, before the class/kit warrior-bonus lookup. This is a source-grounded lead
for the original3/2 versus native1 discrepancy, not a demonstrated cause or
permission to change all unarmed/monk attack rates. The next reference should
distinguish actual delivered attacks from display text and cover non-monk
warriors, monks, equipped melee/ranged weapons and relevant level boundaries.
