# Stock container loot journey

Executed follow-up: [independent LAB audit](phase1-container-loot-audit.md) confirms
the corrected bounded route in `20261022T040338Z-container-loot-journey-25ffdf30`.
One command at sample 9 reaches the real stock callbacks at sample 31; ownership
persists through ordinary save, fresh-process reload, and another ordinary save.
Both processes and preservation checks pass. External tooling passes 243 tests,
including 21 focused loot tests. Readiness build `candidate-9aa-ui1-loot-ready4`
remains failed; fresh `ready5` fixes the external comparison with explicit
`StringView(name)` and compiles successfully. Earlier failed runs below retain
their verdicts. No engine change or original-parity claim is made; existing
GUI/color/inventory hosts are unchanged.

Coordinator follow-up: 15 focused tests and the then-current 227-test integrated
suite pass. The first native run `20261022T032531Z-container-loot-journey-c3703e13`
and diagnostic rerun `20261022T032917Z-container-loot-journey-eff5ffad` both remain
failed before transfer. The external host compared the stored ARE name with the
runtime script name. `Scriptable::SetScriptName` removes internal spaces, while
`AREImporter::GetContainer` retains the original name in `OriginalName`.
The host now requires both exact stored identity `Jailkeep Table` and normalized
runtime identity `jailkeeptable`, retaining all position/type/lock/trap guards.
Fresh external compilation and execution are required; no engine correction is
implied by this adapter defect.

The protected stock saved fixture contains the unlocked, untrapped **Jailkeep Table** in AR0602 at (3109,2829). Its eleven items begin with SW1H04; the leader starts at (3741,2801) without that item. The tool copies this exact saved fixture, without changing GAM/ARE/CRE, adding items, or inserting success globals/scripts. It rejects other fixture roots and records exact source, copied input, and output manifests. The source table's complete item order, position, type, flags, and trap state are guarded.

The first fresh host process selects the leader through `GemRB.GameSelectPC` and lets ordinary startup run before issuing a command. It requires four consecutive running samples with observed BD_DEFAI=1, actual SCR_CLASS script BDDEFAI, no current/next action, no movement, the same selected leader, and no current container. It then sets the real current container and queues parsed `UseContainer()` through `Actor::CommandActor` **once**. This is the ordinary operation pair in `GameControl::HandleContainer`; mouse hit testing and its clicked trigger are outside this adapter. The normal running loop performs movement, proximity/unlock checks, and opening. The adapter waits for the shipped container window, sets the UI selection parameter LeftIndex=0, invokes control 0's real `Container.TakeItemContainer` callback, and invokes control 51's real `Container.LeaveContainer` callback. It never calls `ChangeContainerItem` directly. The action ID is bound to shipped ACTION.IDS and the callback sources are frozen.

This observes **actor operations and stock callback dispatch**, with sampled leader action/position traces. It does not observe OS pointer input, hit testing, every intervening action, or original behavior. No force item/stat/global APIs substitute for the actual result. Failure to reach/open/take/close in the bound remains a failure; there is no teleport, unlock, inventory insertion, or alternate direct transfer fallback.

The declared outcome is conservation: the exact SW1H04 record leaves the table and enters the leader's real inventory, the other records remain, and the table retains ten items. Expiration/charges and flags are checked within the runtime transfer, masking only the source-grounded transient acquired flag 0x10 (`Inventory.h` / `Inventory::AddSlotItem`); raw flags remain in the receipts. No general wire/runtime flag equivalence is asserted. FIST is excluded only using the runtime inventory's explicit fist slot; serialized inventory checks use the independent GAM reader.

After ordinary clock progression, the host pauses, takes full and focused snapshots, and calls ordinary unforced `CreateSaveGame`. Return 0, one new owned save, unchanged before/after-save snapshots, exact serialized leader/table ownership, and immutable copied input are required. A second fresh process loads that frozen output, inspects both sides without another transfer, runs the normal clock, saves again, and verifies the same ownership. No runtime ID equality is assumed across processes. The combined budget remains two processes × at most 90 seconds; exactly 80 running samples are preceded by five paused and followed by four paused samples. Readiness consumes this same budget; insufficient readiness or approach time is a preserved failure.

Source closure includes independent byte-identical frozen Phase0 GUI/serializer copies, the new external hook, relevant stock GUI/core sources, current helper modules and Phase0 validators. External build outputs must be in a separate private Phase1 folder, outside source/build roots. A successful host receipt must still match core/plugins/headers, compiler, executable, generated source, all source/frozen copies, and Phase0 preservation inventories. Every run freezes that closure and ACTION.IDS again. Per-process private GamePath wrappers isolate runtime log writes; all wrappers, configurations, empty overrides, input saves and frozen/native output saves are checked after the journey. Raw failed prefixes and process/error logs remain in unique results directories. Wrapper guards compare linked asset inventory/metadata and root hashes; they do not fully hash all linked asset contents.

Coordinator commands after integrating these files (PowerShell):

```powershell
$python = 'C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe'
$tool = 'C:\BGRedux\phase1-local\engine\redux\tools\phase1\container_loot_journey.py'
& $python -B -m unittest discover -s C:\BGRedux\phase1-local\engine\redux\tools\phase1\tests -p test_container_loot_journey.py -v
& $python -B $tool build --project-root C:\BGRedux --engine-source-root C:\BGRedux\phase1-local\engine --engine-build-root C:\BGRedux\phase1-local\builds\20261022T012223Z-candidate-9aa69cd5 --output-dir C:\BGRedux\phase1-local\weapon-query-probes\candidate-9aa-ui1-loot --timeout 180
& $python -B $tool run --project-root C:\BGRedux --engine-source-root C:\BGRedux\phase1-local\engine --engine-build-root C:\BGRedux\phase1-local\builds\20261022T012223Z-candidate-9aa69cd5 --host-build C:\BGRedux\phase1-local\weapon-query-probes\candidate-9aa-ui1-loot\build.json --fixture C:\BGRedux\phase0-local\fixtures\original-bg2ee-20261020\GemRB --results-root C:\BGRedux\phase1-local\results --running-samples 80 --timeout 90
```

The build command rebuilds only this external host. The output folder must not already exist; use a new name for every rebuild. Run is explicit and serial under coordinator ownership. Unit sources cover conserved/missing/duplicate/wrong-item transfers, charges and stolen flags, wrong actors, reload mutation, duplicate slots, stale/missing evidence, fabricated completion/callback/save metadata, frozen clocks, save-state mutation, focused/full disagreement, bounded ARE parsing, and missing/ambiguous host instrumentation anchors. They have not been executed by the implementing worker.

The readiness correction is grounded in failed run `20261022T033328Z-container-loot-journey-42d3a11e`, which remains failed. Its sample 5 contains UseContainer action 112, followed by no current action while the existing movement path continues to the table; sampled dialogue flags never include DF_IN_CONTAINER=32. Stock AR0602.BCS (`29c1d6d4b57787341a735532f126f1ae0e5bc1b5c8b5497f1502e83732c8f6d6`, Scripts.bif) initializes BD_DEFAI/BDAI_RESET_TIMERS and issues ActionOverride(Player1,ChangeAIScript(BDDEFAI,4)). `GameScript::HandleActionOverride` clears non-overridden actions while `Scriptable::ClearActions` does not clear the movement path, supporting the observed interruption mechanism. The new run must independently establish whether waiting resolves that failure; this is not an engine fix or a claim that this cause was directly instrumented in the old run.

Initial `clock-before`/`loot-before` and later `loot-command-before` full/focused snapshots are distinct. The validator permits natural initialization between them while requiring leader/table inventory conservation, the guarded identities, and the first SW1H04 slot. Loot outcome and approach movement are measured from command-before. No initialization globals are written, no AI is disabled, and no command is retried. BDAI_RESET_TIMERS is observed without requiring zero: disabled party AI can leave that reset pending. Per-sample diagnostics retain both before/after contexts, actual eight script names, current/next action, movement, party-AI control status, global values, selected/current/target IDs, dialogue flags, and all candidate Window8 pack visibility states. The validator recomputes the four-sample streak and one-command count, requires a real queued action/target after dispatch, and binds the callback boundary to an engine-open container flag and visible enabled stock window.

The changed external closure additionally freezes `GameScript.cpp`, `Scriptable.cpp`, `Interface.cpp`, and private copies of AR0602/BDDEFAI/DPLAYER3 script resources extracted read-only from the clean game. Their bytes, origins, and hashes are rechecked before/after execution and at finalization. No resource bytes are installed as overrides or published with this tool. New negative test sources reject absent/false readiness, early/late/duplicate commands, missing command snapshots/diagnostics, no observed queued action, pre-command inventory change, fake open boundaries, and startup resource drift. A fresh external host build is mandatory after this correction.

Dialogue/quest progression, locked or trapped containers, multi-item/stack merging, full inventory, alternate saves, OS pointer routing, and measured original parity remain unsupported by this bounded route. Successful native execution would establish this particular inventory/world persistence journey; it would not complete P1-06 or general gameplay compatibility by itself.
