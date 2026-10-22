# Saved NPC color characterization inputs

Status: source and test preparation only. No actual fixtures have been generated
with this tool, tests have not been executed by the worker, and no native or
original-game behavior is claimed. The
[investigation](../compatibility/phase1-saved-npc-color-investigation.md)
motivates this experiment; it does not approve a production fix.

`redux/tools/phase1/saved_npc_color_fixtures.py` has one explicit `prepare` mode.
It never launches a process, installs an original game/profile, performs an
autosave, or simulates a reload. A coordinator can later invoke it with
`--project-root C:/BGRedux`, an explicit `--source-save` containing the reviewed
six-file vanilla save, and `--results-root C:/BGRedux/phase1-local/results`.
The results root must remain under that private directory. Preflight errors
before output allocation must be retained in the coordinator's command log.
Once construction starts, partial fixtures and a failed preparation receipt
are retained rather than deleted or relabeled as executed.

## Decisive controls

Writing raw CRE color237 into an embedded actor is insufficient: it may be
interpreted as a random selector before any initial observation. Instead the
tool supplies a **fresh CRE resource**, RDXCOLOR, created by ordinary scripted
CreateCreature action7 after the initial save load. It verifies that action's
signature against the shipped ACTION.IDS and records its source hash. BCS
field order follows `gemrb/core/GameScript/ParseBCS.cpp:243`; the normal action
uses `gemrb/core/GameScript/Actions.cpp:757` and CreateCreatureCore. Actual
original/native parser and creation behavior still require execution evidence.

| Case | Fresh CRE leather byte | Private RANDCOLR input | Characterization purpose |
|---|---|---|---|
| controlled-high | 228 | Every outcome of verified Leather selector228 is237; every outcome of verified selector237 is46 | Observe fresh creation, first save wire byte, fresh reload and second save wire byte |
| ordinary-low | 46 | Same controlled table | Low-color and private-table control |
| stock-fresh-selector | 228 | Byte-identical stock table | Fresh stock random-selector control; no fixed outcome asserted |

The controlled table changes only those two outcome columns. Header names,
selector IDs, row labels, whitespace and other columns remain intact. Source
and override hashes, stock output sets and controlled column metadata are
recorded. If Leather228 or selector237 cannot be verified, preparation fails;
there is no unreviewed random fallback. The original stock table is read only.
The high-case 237-to46 chain is an experimental input model, not an asserted
original result or a production table change.

The fresh NPC is cloned from the reviewed party0 CRE: paletted human animation
0x6100/race1, neutral allegiance128, no five file scripts, no dialog, no item
records and no effect records. Other color channels remain from the source.
Obsolete table bytes remain unreferenced; they are not silently stripped.
The intended spawn point is40 pixels right of party0. Actual placement can be
adjusted by ordinary collision checks and must be observed rather than assumed.

One embedded Mephit at `[2573,2461]` is replaced with a distinct low-color inert
RDXIDLE placeholder, including clearing its ARE dialog/script overrides.
**RDXCOLOR is not embedded in the input area.** The append-only replacement
changes only declared actor-row ranges and appends the placeholder CRE. Other
compressed SAV members remain byte-identical. Other area actors/scripts remain
in the experiment and can interfere; failure to create/save safely is a failed
experiment, not permission to weaken guards.

Party file scripts are explicitly replaced: party0 receives the unique case
script, its other four scripts and party1's five scripts are NONE. The script
sets case/nonce/stage markers, creates RDXCOLOR once, then marks readiness only
after See("rdxcolor"). Persisted stage2 prevents recreation after load. Ready
does not mean saved, reloaded or color-correct. The input fixture and override
each have exact final file manifests; every case records its unique script,
nonce, raw NPC input guard and the unchanged source-save manifest.

## Required coordinator/original boundaries

1. Review preparation and independently verify final manifests, the resource,
   NPC/placeholder input guards, controlled table and parsed creation action.
   Use a separate private game/profile per case and runtime; install overrides
   only there. Never copy the experimental table into the clean source game.
   Both original and candidate must receive identical case fixture/override bytes.
2. Start a fresh process, observe the exact private profile/load boundary, load
   the case once, allow normal script creation, then pause. Verify exactly one
   RDXCOLOR and the case/nonce/ready markers. Capture available **actual runtime**
   colors, actor identity/position/equipment/effects and visual appearance.
   Original screenshots or saved bytes alone are not exact runtime-memory color
   samples; explicitly label any unavailable original observation.
3. Perform an ordinary named save. Freeze/hash the complete output before
   further gameplay, read the embedded NPC's leather byte independently, and
   retain the original executable/window/save provenance. The supplied
   inspect_npc_wire function reports only a serialized byte, never a runtime
   palette. Validate persisted case/nonce separately from the output GAM.
4. Exit and verify that process is gone. Start another fresh process with the
   same private overrides and load the frozen save. Observe the already saved
   NPC and no duplicate creation; capture actual colors and save/freeze again.
   Repeated same-process snapshots or refreshes are not fresh reloads.

Record whatever both runtimes actually do, including creation failure, save
restriction, changed or stable colors and unavailable exact observations.
First original characterization determines the comparison contract; no
original high-color stability assumption is encoded as a pass rule. Do not
advance an engine fix, broad color whitelist or claimed original parity from
fixture preparation alone. Calling-thread RNG observations, when available,
must not seed/reset/advance the live generator just to inspect it.

## Parser and evidence guards

The source save must be flat, symlink-free and have exactly the reviewed six
files. GAME/CRE ranges, table counts and physical item references are bounded;
overlapping party CREs, invalid palettes and unsupported formats fail. SAV
member names cannot contain traversal/drive paths, embedded NULs or duplicates.
Declared compressed sizes, total counts and bounded decompression reject bombs,
truncation and trailing streams. ARE actor tables and target uniqueness are
checked; existing diagnostic identities are rejected. No SAV members are
extracted to paths. Only the declared GAM script fields and SAV area changes
are allowed; four other save files remain byte-identical.

Focused test sources cover those negative cases, exact two-column table
changes, inert creation inputs, wire/runtime distinction and fresh-create
readiness without save/reload actions. They remain **unexecuted** in this worker
turn. All actual preparation, tests and runtime validation await the coordinator.
