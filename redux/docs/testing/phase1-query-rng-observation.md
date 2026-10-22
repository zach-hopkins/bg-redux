# Calling-thread RNG observation for weapon queries

Status: implementation and evidence tests ready; native compilation and runs
are reserved for the coordinator. This diagnostic consumer covers repeated
WeaponEffectiveVs/WeaponCanDamage calls on the calling thread only. It does
not establish deterministic replay, combat parity, other-thread RNG purity,
or freedom from all hidden side effects.

## Engine API

`RNG::TrySnapshotState(std::mt19937_64& output)` returns false when this thread
has no normally initialized RNG and leaves output untouched. It does not call
getInstance. A nullable thread-local pointer is assigned only after the
unchanged constructor's normal engine.seed call and cleared at destruction.
An existing engine is copied by value; no live engine reference, seed/set/reset
API, draw counter or per-roll instrumentation is exposed. RAND, randPct,
distributions and the timestamp seed formula are unchanged.

The output is a caller-owned standard engine copy, suitable for equality and
private same-process diagnostic serialization. Constructing this copy does
not construct, seed or advance the live GemRB singleton. The API and tests use
C++14. Header feature macro `GEMRB_RNG_TRY_SNAPSHOT_STATE` allows the external
observer to compile against older source/build pairs without referencing the
new exported symbol.

The native tests use fresh threads to prove two absent observations leave
both absence and the caller's output unchanged. After ordinary initialization,
eight observations preserve state. A real ordinary draw matches the same
distribution applied to the copied engine; the resulting live state differs
from before and equals the independently advanced copy. A second fresh thread
remains absent while its parent thread is initialized. These tests require
coordinator compilation/execution; Python evidence tests do not substitute
for those native assertions.

## External evidence and controls

The six-query observer writes initialized/final RNG files plus distinct
before/after RNG files for every True/False control and repeated hand query.
Each contains strict observed/initialized flags, calling-thread scope, and
private raw state when initialized. API-unavailable builds report observed
false with null initialized/state fields. A present API can observe absence;
false-to-true initialization is itself a mutation. No RNG is initialized just
to take a snapshot.

The Python validator independently compares raw states and initialization,
checks per-call filenames, availability, native equality flags and continuity
across all boundaries, and rejects missing/extra/partial evidence. Older
captures without RNG files remain readable with rng_unchanged null. Hidden
state remains explicitly unknown even if observed RNG equality holds.

For the corrected candidate, add `--require-rng-observed` to the existing
`weapon_query_observer.py run` command. Missing/unavailable evidence then fails
validation. Normal query runs must retain no collected-state mutations, no
calling-thread RNG mutations, stable repeated values and the selected
original-reference matches. Existing source/build/preparation/protection
arguments, owned timeout, unique output directories and artifact manifests
remain mandatory.

For a separate intentionally failing run, add both `--require-rng-observed`
and `--rng-control-draw`. The external host performs one real RAND draw after
the first weapon query (call 3), inside that call's observed interval. It
records the controlled-draw identity; the runner binds it to the requested
mode. A detected change yields `calling-thread-rng-mutation` and exit 1;
missing draw evidence yields `rng-control-not-detected` or an evidence error,
also failing. The negative control never seeds/resets the singleton and never
runs in normal observation mode. Preserve this failed result alongside the
normal run rather than treating it as an overall pass.

Raw RNG files remain private laboratory results, with no player UI or replay
format guarantee. Recompiled hosts built against a new header must use the
matching engine binary; existing source/binary provenance guards remain in
force. No worker native build or launch was performed for this change.

Focused Python tests cover initialized/absent/unavailable observations,
controlled draw and lazy initialization detection, forged equality,
missing/reused files, continuity/final boundaries, strict schema and mode
binding. The full Phase 1 Python suite passed 56 tests; git diff --check passed.
