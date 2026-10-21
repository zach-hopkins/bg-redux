# Phase 0 — original-engine scripted query comparison

October 20, 2026 PDT / October 21 UTC. Engine source and GemRB engine/plugin binaries remain unchanged.

## Executed result

The same generated BCS script and declared input save ran in GemRB and a private copy of original BG2EE **2.7.3.0**. The script queries the protagonist's MAINHAND against Player2 (Imoen), writes each Boolean to a separate global, writes a completion marker/final stage and calls `SaveGame(0)`. An independent GAMEV2.0 reader checks the new autosave. No attack or movement was issued.

| Saved observation | Original BG2EE | GemRB |
|---|---:|---:|
| `RDXVE`: WeaponEffectiveVs(Player2, MAINHAND) | 1 | 0 |
| `RDXVD`: WeaponCanDamage(Player2, MAINHAND) | 1 | 0 |
| `RDXDONE`: completion marker | 1 | 1 |
| `RDXSTAGE`: final stage | 3 | 3 |

**This is an observed compatibility difference for one fixture.** It corroborates the verified false-returning stubs described in the [source/exposure assessment](weapon-query-exposure.md). It does not establish their complete original contract or quantify companion combat degradation. In particular, packaged AI scripts have later fallback attack branches.

GemRB run: `20261021T034359Z-script-query-3549b2a7`, normal-loop external host, process exit0. Original comparison capture: `20261021T035930Z-original-script-query-2b6652e5`. [Machine comparison](../compatibility/evidence/original-script-query-results.json), [GemRB execution](../compatibility/evidence/script-query-results.json), [operator observation](../compatibility/evidence/original-query-observation.json).

## Fixture and provenance

The baseline is copied into a disposable fixture. Ten embedded CRE script assignment fields are changed: protagonist override becomes RDXQPROB; all other five file script slots across both party actors become NONE. Stats, inventory and effect bytes are unchanged in the constructed input. The protagonist has no inventory item; this is the **fists case**, not an ordinary sword, ranged or enchantment test. Imoen retains her baseline IMOENHP1 item. Area scripts/effects remain active, and the input opening checkpoint causes a chapter autosave too.

The generated script is 2,056 bytes, SHA256 `89632bda590c9325bc88ade44d3e8a35d75d2fdc1cecf5d2d9aaed823cdb3758`. Its two positive query branches each have an explicit false fallback. Completion requires both explicit Booleans, `RDXDONE=1` and final stage3. The original positive results also demonstrate that the generated object/query encoding can succeed; GemRB's zero values are not inferred from a missing global.

The original executable SHA256 is `b51093a49140b2b8a7c046b4652bb8e535be24ebbc12b1d735e0b94217a14d57`. All 2,324 source-manifest files were copied initially and verified. After execution, 2,323 original files were checked again with zero hash mismatches, mapping the retained optional Steam DLL to its original entry. The excluded engine.lua intentionally names the private Documents profile; the sole additional override is RDXQPROB.bcs. This establishes file provenance, not loaded-module attestation or an independently verified Steam depot.

Computer Use observed launch from the private game folder, Shadows of Amn → Single Player → Load Game → Redux Query → Load, followed by an automatically created completed autosave. The capture tool verifies the operator receipt against exact executable/script/input/output hashes and freezes the output. The receipt is an operator-authored observation, not self-generated proof that a game ran. Both the frozen baseline and the user's ordinary GemRB baseline save remained unchanged.

## Isolation and failed attempts retained

The first private profile imported Steam cloud copies of Auto-Save/GemRB/r1/r2. No diagnostic input was loaded in that session. A fresh profile with `Program Options / Cloud Saves Enabled=0` initially looked isolated, but opening Load Game imported the same cloud copies. **Startup folder inspection alone is insufficient.** No test autosave was allowed in either of those profiles.

In the successful private copy, the unmodified optional `steam_api64.dll` was retained under the inert filename `steam_api64.dll.phase0-retained`; the installed game and Steam account settings were untouched. The game launched from its folder, and Load Game showed only Redux Query. Its completed run created Auto-Save and Chapter 1 Start locally, with no imported cloud reference folders. This is observed profile isolation; no network attestation is claimed. The private copy deliberately lacks optional Steam integration and is not a stock Steam-integrated execution claim. [Isolation history](../compatibility/evidence/original-query-isolation.json).

Two direct `sky.launch_app` attempts produced startup crash dialogs, with the DLL absent and restored respectively. Folder launch succeeded in both later configurations. A working-directory dependency is suspected, not proved; the first crash cannot be attributed to library omission alone. Use the observed folder launch route. All private diagnostic sessions were closed; other running game sessions were left alone.

The first GemRB prototype used too short a running window: chapter saves existed but no completion marker did. It failed rather than counting those saves as query execution. Increasing only the external host's measured running samples allowed the script to finish. This is ordinary simulation progression, not deterministic stepping.

## Harness and next gate

`harness.py script-query` prepares/runs the GemRB case. `harness.py capture-original-query` checks and freezes the separately observed original result; it never launches or controls BG2EE. `prepare_original_query.py` and `isolate_original_query.py` prepare private inputs and refuse to overwrite existing destinations. Reproduction still needs an observed original GUI load. This is a reusable BCS/autosave diagnostic route, not an unattended original playthrough adapter or engine RPC.

The suite now has **52 passing harness unit tests**. New guards reject missing Booleans, chapter autosaves, incomplete stages, invalid values and receipt/executable/output drift. Historical runtime receipts retain their actual source hashes; later oracle hardening is not retroactively described as executed native evidence.

Prioritize a batched original/GemRB truth table next: missing/invalid actor controls; ordinary melee and ranged launcher/ammo; main/off/both hands; enchantment and physical immunity; secondary elemental damage; Stoneskin, mirror image and protection from magical weapons. Record the selected weapon/target and query side effects separately. Then observe BDIMOENC/BDDEFAI branch/action selection, including fallback. Propose a narrow read-only predicate only after those cases distinguish can-hit from can-damage. No engine fix is authorized or implemented during Phase 0.

## Follow-up: eight-case batch executed

The same route now executes eight sequential queries per load with a single completion autosave. Packaged hand.ids supplies MAINHAND=1, OFFHAND=2, BOTH=3; object.ids supplies Player2=22 and Player6=26. The two-actor fixture has no Player6. Inventory remains unchanged; this is still fists with an empty off hand.

| Target / hand | Original EffectiveVs / CanDamage | GemRB EffectiveVs / CanDamage |
|---|---|---|
| Imoen / MAINHAND | 1 / 1 | 0 / 0 |
| Imoen / OFFHAND | 0 / 0 | 0 / 0 |
| Imoen / BOTH | 1 / 1 | 0 / 0 |
| Absent Player6 / MAINHAND | 0 / 0 | 0 / 0 |

Both autosaves explicitly contain all eight Boolean globals, `RDXMDONE=1` and final stage9. The batch has **four mismatches and four matching negative controls**; this is not a compatibility percentage. BOTH=true is observed in this fists fixture, not proof of how BOTH combines two actual equipped weapons. Queries occur sequentially under normal running simulation; their side-effect freedom and stable world state are not established by this test.

GemRB batch run: `20261021T040139Z-query-matrix-2aa0d729`, [machine execution receipt](../compatibility/evidence/query-matrix-results.json), process exit0 after32.235s including startup and measured intervals. Original capture: `20261021T040510Z-original-query-matrix-8c822bba`; [comparison and frozen-save provenance](../compatibility/evidence/original-query-matrix-results.json), [operator receipt](../compatibility/evidence/original-matrix-observation.json). The batch script SHA256 is `98638f2e3d5245e2a004b9a34f25838d48f6a734c1dcce1e97cc8097813bee8b`.

`harness.py query-matrix` runs GemRB; `harness.py capture-original-matrix` checks the independently observed original result. The latter rereads the exact hash-bound GemRB autosave too; it does not invent completion markers from summary values. `query_matrix.prepare_original()` prepares the new private profile/script and refuses to overwrite prior runs. The original load list again contained only the declared fixture, and the completed private session was closed.

The suite now has **56 passing tests**, including rejection of incomplete batches and missing negative controls. The immediate next truth-table work is ordinary equipped melee/ranged weapons and defense contrasts; missing-target/hand controls are now executed for the baseline fists case. Retain invalid-sender, side-effect and actual AI fallback/action tracing as separate unfinished gates.

## Equipped-weapon preflight and reporting hardening

[Candidate input metadata](../compatibility/evidence/weapon-query-next-inputs.json) records packaged SW1H01/SW1H02 item hashes and enchantment0/1, plus the actual action.ids records for CreateItem82, EquipItem11 and SelectWeaponAbility92. These equipped cases are **not executed yet**. Use normal script actions in a disposable fixture, then verify item ownership, physical slot, selected weapon/ability and launcher/ammo before counting the predicate output as a sword/ranged result. A successful script response alone could otherwise leave fists selected and produce misleading positive evidence. The [item importer](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/ITMImporter/ITMImporter.cpp#L182), [EquipItem](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GameScript/Actions.cpp#L4466), [weapon ability selection](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GameScript/Actions.cpp#L6786) and [CRE equipped selection reader](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/CREImporter/CREImporter.cpp#L1091) identify the next fixture/observation dependencies. Query success is not proof of inventory setup correctness.

The audit validator previously rewrote historical build/test flags to true during document validation. Those runs are independently recorded, so this did not create the observed runtime results, but it could mislabel future evidence. The validator now reads the recorded flags without changing them and explicitly labels them historical. A before/after SHA256 check confirmed phase0-evidence.json remained byte-identical when validation ran. Missing or empty GAM files in generated-query output now go through the existing bounded member validator rather than escaping as an unrecorded StopIteration.

The [preservation check](../compatibility/evidence/phase0-preservation-check.json) verifies four baseline binaries and45 plugin DLLs with zero mismatches, a clean engine checkout, and unchanged frozen/personal baseline saves. These guards validate the Phase0 constraint; they do not certify gameplay or save parity.
