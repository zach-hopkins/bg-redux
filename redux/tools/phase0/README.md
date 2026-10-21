# Phase 0 native test tools

These tools live outside the pinned engine checkout. They use the existing
workspace-local Windows UCRT64 build and licensed data under `phase0-local/`.
No player menus, input injection or attachment to a running player session.

The GUI host owns a separate test window and dispatches stock control callbacks.
It captures engine buffers directly; it does not operate your desktop menus.

```powershell
python tools/phase0/build-save-probe.py
python tools/phase0/build-gui-probe.py
python tools/phase0/harness.py capabilities
python tools/phase0/harness.py save --fixture original-vanilla --name vanilla
python tools/phase0/harness.py scenario --scenario tools/phase0/scenarios/vanilla-opening.json --name opening
python tools/phase0/harness.py inspect --fixture original-vanilla --select 2 --query /selection --query /party/1/script_name
python -m unittest discover -s tools/phase0/tests -v
```

Normal GUI load/save and presentation tests:

```powershell
python tools/phase0/harness.py gui --name gui-baseline --timeout 100
python tools/phase0/harness.py gui --font-mode bam --name bam-comparison --timeout 100
python tools/phase0/harness.py gui --screens-only --font-mode ttf-18 --name larger-text --timeout 45
```

`gui` uses `UseAsLibrary=0` and the actual main/render loop. It loads a private copy
of the pinned vanilla fixture through GUILOAD, opens inventory/record/options,
dispatches save-row/name-edit/confirmation callbacks, checks empty-name refusal,
creates a save, cancels overwrite without changing save bytes, overwrites, and
loads the result through GUILOAD in a fresh process. Screens-only performs load
and inventory/record captures without saving. Scoped UI JSON, font metrics and
BMP screenshots accompany state/process/hash receipts. `--debug` wraps the owned
process in GDB and captures crash stacks; debugger exit0 alone never passes a run.

The scenario reasserts pause after callbacks. It does not promise tick stepping,
RNG control, input hit testing, a universal UI tree or visual parity. BAM/18px
font overrides exist only in that run's private ModPath. Default player settings
and engine assets are untouched. Full stock/BAM GUI runs pass20/20 content and
callback checks but retain save differences, including extra IMMCLOUD effects;
overall exit1/`differences` is intentional. The representation-aware diagnostic
is separate and never erases raw comparisons. [Detailed GUI results](../../docs/testing/gui-save-and-presentation-results.md).

Effect lifecycle investigation:

```powershell
python tools/phase0/build-gui-probe.py
python tools/phase0/harness.py effects
```

This fixed scenario runs four stock and three control cycles in fresh processes.
Each uses the normal GUI load/EnterGame path, then paused observations, two effect
refreshes and an ordinary non-forced native save. It independently reads the
saved area's embedded creature effects. The control changes seven item timing
bytes only in a disposable ModPath. Neither original assets nor the normal
player configuration change. It returns `characterized` when nine observations
hold, including the **expected stock accumulation**; that is not a compatibility
pass. Full state, logs and private saves remain under the new result directory.
See [IMMCLOUD findings](../../docs/testing/immcloud-lifecycle-investigation.md).

Wider exposure and original-engine reference:

```powershell
python tools/phase0/harness.py equip-scan
python tools/phase0/harness.py original-reference
```

The scan inventories all KEY item equip blocks, then runs two reviewed private
carrier contrasts. Its32 candidate items are not32 verified bugs. The original
reference command reads/freeze-copies the user-created “Redux EE Reload 1/2”
saves; it does not control the original game. Missing inputs return pending/exit2.
After the user confirms clean original execution, record that attestation with
`--human-confirmed-clean`; it is distinct from independently observed launch
provenance. Use `--first <folder> --second <folder>` for nonstandard locations.
The comparison command does not change source saves or profiles. For agent-created UI references, use `--execution-receipt <json>`; the receipt binds executable/save hashes and records operator limitations, without claiming module attestation. `--gemrb-evidence <lifecycle-results.json>` separately compares counts and full reported signatures. The executed UI sequence created r1/r2; use explicit paths for these short names. [Exposure/reference results](../../docs/testing/equip-exposure-and-original-reference.md).

`save` runs original import/resave, fresh-process reload/resave, a second reload,
and an independent repeat import. Every stage has a separate private home/cache.
It uses ordinary save guards (`force=false`). `inspect` imports/initializes the
area and returns state; it does not resave. `scenario` adds fixture-specific
assertions and queries, with optional one-based party selection. Selection is
applied explicitly in every stage, so it is not a persistence assertion.

Use `--fixture-dir <folder>` for an unregistered disposable fixture. Both nonempty
`baldur.gam` and `baldur.sav` with valid signatures are required. The input is
copied and hashed before use. Registered `original-vanilla` has a pinned manifest;
drift is refused. Missing fixtures are failures. The old EEex fixture is retained
as an unsupported-content negative case; its effects are never stripped.

Artifacts: unique `phase0-local/results/<run>/` directory with `result.json`, raw
and normalized state/diffs, before-area snapshots, wire-field oracle, commands,
process/log/config records and source/copy immutability results. Full private
state and game assets remain ignored. Known results: [save/harness report](../../docs/testing/save-import-and-harness-results.md).

`execution_verdict`, `assertion_verdict`, `persistence_verdict`, repeat-import and
wire-oracle observations are separate. The overall verdict is conservative and
can be `differences` with every native process exiting0. Exit0 means overall pass;
exit1 includes differences, failed assertion, unsupported fixture or timeout.
Read the JSON rather than assuming every nonzero result is a crash. Inspect/query
may return differences due to raw wire/runtime representations even when the
query succeeds. `wire_oracle` is a limited file-field check, not full engine parity.

JSON Pointer queries use paths such as `/party/0/base_stats/0` (current HP),
`/party/1/inventory`, `/globals/CHAPTER`, `/journal` and `/current_area_actors`.
Stats are the pinned engine's 256 indices; see its `ie_stats.h`. Assertions support
`eq`, `ge`, `length_eq`, `length_ge` and `exists`. No arbitrary Python/BCS eval is
exposed. Failed/missing paths cannot pass an assertion.

The independent Python wire reader currently supports GAMEV2.0 with embedded
CRE V1.0. Future versions need explicit support; unsupported formats fail this
oracle, not silently pass. The native host uses `UseAsLibrary=1`, which changes
some effect serialization handling and skips normal GUI/render initialization.
It does not execute simulation ticks. NPC color randomness remains visible.

The host build receipt pins probe source, binary, compiler and engine DLL hashes.
Rebuild on drift. This ABI is tied to the pinned C++ toolchain/engine headers,
not a stable third-party plugin contract. Existing core tests remain available:

```powershell
python tools/phase0/harness.py core --managed --filter 'MovementTest.*' --name movement
```

Full semantic UI traversal, real-loop stepping, controlled RNG, original-runtime
observation and campaign automation remain future work. See the [harness design](../../docs/testing/ai-first-harness.md).

Additional bounded Phase0 observations:

```powershell
python tools/phase0/harness.py string-challenge
python tools/phase0/harness.py live-clock
python tools/phase0/harness.py cre-loadouts
```

The string challenge explicitly constructs/removes effects only in disposable fixtures; it observes message text rather than trusting handler return codes. Live clock waits for the stock loading window to close, then observes pause/resume at render caps30/60 without synthetic stepping or achieved-FPS claims. CRE loadouts report packaged references/raw slots, not runtime equipment. The common native launcher refuses failed builds and source/binary/core-DLL drift. [Actual results](../../docs/testing/behavior-and-live-clock.md).

`python tools/phase0/harness.py weapon-triggers` scans two verified EE weapon-query stubs in packaged compiled BCS. Results include hand/negation, containing response action IDs, later fallback metadata and baseline party file assignments. It refuses unsupported records and does not claim a runtime decision trace. [Assessment](../../docs/testing/weapon-query-exposure.md).
# Script query/autosave comparison

`python tools/phase0/harness.py script-query` constructs the declared private BCS/CRE fixture and runs its GemRB query/autosave case. `python tools/phase0/harness.py capture-original-query` verifies/freeze-copies the separately observed original-game result using its operator receipt. Neither command launches original BG2EE. Preparation helpers refuse existing destinations; do not rerun them over a prior experiment. See [executed comparison and isolation history](../../docs/testing/original-script-query-results.md) before reproducing. The single observed fists case differs1/1 versus0/0; it is not the full trigger contract. Engine code remains unchanged.

`query-matrix` / `capture-original-matrix` batch eight hand/target cases per load, with explicit saved completion and Booleans. The original fists MAINHAND/BOTH cases differ; empty OFFHAND and absent Player6 controls match. `query_matrix.prepare_original()` prepares a fresh profile and script in the already isolated private copy, refusing existing destinations. Original GUI load remains an observed operator step. The harness suite has56 tests; full weapon/defense characterization remains open.


## Equipped weapons, defenses and AI tails

Run `python tools/phase0/equipped_defenses.py` for eight disposable normal-loop query cases, and `python tools/phase0/ai_fallback.py` for four isolated stock/control AI tails. These launch external test hosts against unchanged engine binaries. The original private fixture preparation is recorded in `docs/compatibility/evidence/original-equipped-preparation.json`; observe each named original GUI load and completion before `python tools/phase0/capture_equipped_original.py CASE --window-id ID`. Never capture a stale save as a result. `python tools/phase0/collect-equipped-evidence.py` rechecks frozen outputs, input equality and setup before comparing; it launches no game.

Current results: eight original/native equipped cases complete with14/16 differing predicate values. Four native AI cases sample action105 targeting the declared foe. Original AI attacks visibly but lacks a completed branch save. AI action tests do not imply autosave success, deterministic timing, damage parity or full AI parity. See `docs/testing/equipped-defenses-and-ai-fallback.md`.
