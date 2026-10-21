# BG2EE save import, reload and native harness — executed results

October 20, 2026 (America/Los_Angeles). Engine `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351`, tracked engine checkout unchanged. **The fresh vanilla BG2EE save imports, resaves through the ordinary save API, and reloads in separate processes. Menu-free state queries, party selection and scenario assertions now work. Full save fidelity/determinism is not certified.**

## Fixture and execution

The user created a new save named **GemRB** in response to the request to use the clean Steam executable. It was found at `Documents/Baldur's Gate II - Enhanced Edition/save/000000033-GemRB`, then copied to `phase0-local/fixtures/original-bg2ee-20261020/GemRB`. GAMEV2.0; no EEex markers. The [six-file manifest](../compatibility/evidence/vanilla-save-fixture.json) pins every byte, including GAM/SAV and previews. The staged copy matched the human source folder after testing. User-reported creation provenance plus the manifested BG2EE 2.7.3 dataset establishes this fixture's scope; absence of an EEex string is not a universal cleanliness test.

An external C++ host under `tools/phase0/native/` links the **existing engine DLL**. It calls the real `Interface::LoadGame`, `StartGameControl` / `ChangeMap`, and non-forced `SaveGameIterator::CreateSaveGame`. Every stage has a new process, cache, private Windows home and writable output. No keyboard/mouse input, menu traversal or running-player-session attachment. Original and copied input hashes are checked after use.

| Executed case | Actual result |
|---|---|
| Fresh vanilla import → resave → reload/resave → second reload → repeat original import | Four processes exit0. Both reload comparisons have **zero differences** in the collected normalized state for the latest full run |
| Vanilla scenario, selecting party member2 through `Game::SelectPCSingle` | **24/24 assertions pass** across import and both reloads; current area AR0602, party2, Imoen selected and inspectable |
| Fresh-process repeat of original vanilla import | Party, stored NPCs and world metadata match; **26 differing fields in area-NPC color stats**, so overall verdict remains `differences` |
| Earlier vanilla characterization | Two color-stat differences in first reload, none in second; shows a single zero-difference run cannot establish deterministic fidelity |
| GemRB-created autosave fixture | Import/resave/two reloads all exit0; color changes detected in both reloads and independent repeat |
| Existing Chapter1 save with EEex payload | Before guard: native effect initialization asserts with0xC0000409. Current external host rejects the unsupported payload before area/effect initialization, exits1 normally; no effects stripped |
| Deliberately missing fixture | Structured failure, no native process, no silent skip |
| Deliberately wrong expected area | Native import succeeds; expected-state assertion fails (2/3 pass). Overall nonzero, not green |
| Native timeout probe (10ms budget) | `timeout`, owned child tree terminated; input unchanged |
| Oracle mutation checks | **8/8 pass**: detect HP damage, charge loss, wrong global, missing actor, color change, effect-duration change, missing query and wrong expectation |

Latest complete vanilla run: `20261020T230658Z-vanilla-oracle-f6a33b02`. Earlier vanilla run: `20261020T230342Z-vanilla-import-reload-ebc1b334`. Successful final query: `20261020T231037Z-final-native-query-4317acc5`, returning selection2 and `Imoen`. [Machine-readable evidence](../compatibility/evidence/save-harness-results.json) records run IDs, process results, assertions, comparisons, hashes and 45 plugin binaries. Private full states/diffs/logs remain under `phase0-local/results/`.

The latest vanilla snapshot contains **2 party actors, 21 stored NPCs, 37 current-area actors, 14 globals and 2 journal entries**, with 256 base and 256 modified stats per actor, item slots/charges/flags, spellbook pages, effect fields, positions, portraits and locals. Journal contents, not just their count, are included. This is a useful state surface, not the entire engine/world state.

## What the comparisons mean

Raw JSON differences are retained. The persistence comparison removes process-specific actor handles, maps observed caster handles to actor identity, excludes the non-serialized cached `Effect::RandomValue`, and sorts current-area actors by explicit identity fields. It **does not mask color stats, HP, items, spell/effect ordering, globals or positions**. Party/stored-NPC ordering is retained. Unresolved caster IDs remain visible. No RNG seed or reproducibility claim is made.

The independent Python wire reader decodes selected original GAMEV2.0 / CRE V1.0 fields without invoking GemRB. The relevant layout references are [IESDP GAM](https://gibberlings3.github.io/iesdp/file_formats/ie_formats/gam_v2.0.htm) and [CRE](https://gibberlings3.github.io/iesdp/file_formats/ie_formats/cre_v1.htm). It checks time (file seconds → engine 15Hz ticks), gold/reputation/globals, actor counts/areas/positions, selected stats and carried item records. This is a limited file oracle, not original-executable runtime observation.

In the latest run, **315/351 raw wire-field checks match**. The36 observations comprise 17 current-HP and 19 item-flag comparisons. These are **not 36 proven compatibility bugs**: [Actor initialization explicitly adds Constitution HP adjustment](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Scriptable/Actor.cpp#L6197), [inventory flags include runtime/cache extensions](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Inventory.h#L71), and [the CRE writer masks flags](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/CREImporter/CREImporter.cpp#L1986). Example: Imoen's file HP41 becomes native current HP57, with derived max57 after equipment/effects initialize. Establish corresponding original-runtime values before deciding whether a conversion is faithful. The raw observations remain visible and conservatively keep the overall characterization verdict non-green. Virtual engine fist entries are explicitly separated from real source items.

**Color variability is observed, not suppressed.** [CREImporter::SetupColor](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/CREImporter/CREImporter.cpp#L761) uses RANDCOLR/RNG while loading color indices; [the CRE writer emits the low color byte](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/CREImporter/CREImporter.cpp#L2038). These are source-backed mechanisms relevant to the observed changes. Their exact original-engine parity, random-table ranges and whether resolved saved colors can be reinterpreted as random selectors need a controlled reference fixture. Do not call it harmless or rewrite RNG based on this report alone.

## Why the earlier save test never established import

The unchanged upstream Windows scaffold still has the path-key mismatch and its shell comparator can skip equivalence. The external host replaces that execution path for these checks; no upstream test is falsely reported repaired.

Two further obstacles were actually reproduced:

- The old Chapter1 snapshot contains 23 `EEex` marker records. Their parsed effect opcode is 2019902789 (`0x78654545`, bytes`EEex`), beyond the 512-opcode registry. Area/effect initialization asserts. The new guard reports unsupported content; direct player/engine import is **not** fixed. The current user Documents Chapter1 file was subsequently replaced by the user's fresh vanilla game; the old frozen snapshot remains the negative fixture.
- The old snapshot has no preview BMP. [SaveGameIterator's picker scan excludes such slots](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/SaveGameIterator.cpp#L233). The native host constructs an explicit save-resource handle and calls the loader, so missing UI artwork cannot silently skip a required GAM/SAV import. It does not manufacture source previews.

A first host attempt called inline `Globals::Get().Init(true)` like the multi-game test scaffold; the host/DLL module-local registry initialization then clashed. Removing that extra initialization and running one game per process resolved the host error. This is evidence to prefer core-owned initialization APIs over leaking inline singleton ownership across a future extension ABI.

## Capabilities and remaining limits

Working commands and examples are in the [tool README](../../tools/phase0/README.md). `harness.py save`, `inspect` and `scenario` return separate execution/assertion/persistence verdicts, structured state and artifact paths. `--query` uses JSON Pointer; scenarios use explicit assertions and an optional one-based selection command. Missing paths fail assertions; arbitrary code/script evaluation is not exposed. The build receipt checks source/binary/engine-DLL hashes before launch, and registered fixture drift is refused.

These tests use **UseAsLibrary=1**. They skip normal GUI/render startup and do not run the full simulation loop. [EFF serialization explicitly handles Parameter5/FirstApply differently in library mode](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/EFFImporter/EFFImporter.cpp#L250). This prevents claiming normal interactive save equivalence from library-mode success. Output GAM is GAMEV2.0 under current save settings; no new Redux schema was introduced. Synthetic/empty preview handling does not establish screenshot/portrait fidelity.

Follow-up: [normal GUI load/save tests](gui-save-and-presentation-results.md) now execute separately with UseAsLibrary=0. Create/cancel/overwrite/fresh GUI reload pass20/20 content/callback checks; an IMMCLOUD effect delta remains. This report preserves the earlier library-mode results.

Not yet covered: full SAV/world-map/area/container semantic equality, every effect field, ongoing script/action/timer state, full rules equivalence, unpaused normal-loop behavior, original executable reload, multi-area campaign fixtures, localized UI, deterministic ticks/RNG, and multiplayer. Original-executable reverse export remains outside the initial requirement.

## Next Phase 0 priorities

1. Specify engine-owned update/observation boundaries and controlled clock/RNG semantics. Keep real-loop testing distinct from this initialized-state client.
2. Verify HP/flag representation against original-runtime observations; expand the file oracle to spellbooks, effects and archived world/area/container state.
3. Add distinct original fixtures for timed effects, spells/items/charges/bags, dead/charmed actors, area transitions and SoA/ToB progression. Keep failures reproducible and skips explicit.
4. Trace color randomization and normal-mode effect serialization before declaring save fidelity closed.
5. Extend the now-working scoped GUI adapter into stable view models and visual/font assertions. Runtime control captures diagnose empty EE panels; universal traversal and campaign automation remain open.
