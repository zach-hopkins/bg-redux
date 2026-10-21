# Phase 0 — normal GUI saves and presentation investigation

Executed October 20, 2026 PDT (artifact timestamps October 21 UTC), against GemRB `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351` and the manifested BG2EE 2.7.3.0 copy. **Engine source and engine/plugin binaries are unchanged.** Only external harness programs/scripts, private configurations and documentation changed. The approved modern UI direction remains in effect.

The normal GUI path now runs without menu clicking. Create, cancel, overwrite and fresh-process GUI reload execute successfully. Presentation remains incomplete, and a remaining effect difference prevents a save-fidelity pass. [Machine-readable run receipts](../compatibility/evidence/gui-harness-results.json), [presentation observations](../compatibility/evidence/gui-presentation-results.json) and [usage](../../tools/phase0/README.md) contain reproducible details.

## What actually runs

`Redux_gui_probe.exe` links the existing core DLL with **UseAsLibrary=0**, initializes the stock GUI/rendering stack and runs `Interface::Main`. A small external startup module supplies the campaign settings and switches normally to `GUILOAD`. The stock load-row callback performs `LoadGame`, loading-screen setup and `EnterGame`. Stock `Game.EnterGame` and inventory/record/options/save modules execute. The adapter does not replace their implementations. See [load callback](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/GUIScripts/GUILOAD.py#L135) and [real timer/game/render loop](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Interface.cpp#L1030).

The host opens inventory and record screens through their stock window loaders, opens options, and dispatches registered `Control::PerformAction` callbacks for options → save → new row → name edit → confirm. It then reopens save, cancels an overwrite, and confirms an overwrite. Semantic scrolling positions the requested row; screenshots, control text/rectangles/flags and state snapshots come from the engine. This exercises callbacks and save guards, **not pointer hit testing, keyboard focus traversal or an OS input path**. [Control callback dispatch](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GUI/Control.cpp#L70), [save confirmation](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/GUIScripts/GUISAVE.py#L175).

Every process owns a private home/profile/cache and copied input fixture. The observation scenario reasserts ordinary pause after GUI callbacks restore their saved pause state. It does not control the initial entry tick, provide deterministic stepping/RNG, or establish unpaused campaign behavior. It uses ordinary save guards and a real game preview; `force=true` is never used. There is no attachment to a player session or computer-use menu automation.

## Executed results

| Run | Process results | Content/callback assertions | Persistence result |
|---|---|---|---|
| Stock configuration `20261021T011818Z-gui-stock-verified-fe7b575f` | GUI save exits0 in61.926s; fresh GUI reload exits0 in20.396s | **20/20**:13 save-side,7 reload-side |449 strict normalized snapshot differences; overall `differences` |
| Private BAM-preference comparison `20261021T011949Z-gui-bam-comparison-e78fdd08` | Both processes exit0 | **20/20** |453 strict differences; overall `differences` |
| Private18px TTF screen comparison `20261021T012253Z-gui-ttf18-screens-7882c2b9` | GUI load/inventory/record exits0 | **7/7** |Screens only; no save or reload claim |
| Missing required fixture | No native process launched | Fails before import |`failed`, no skip |
| Deliberate10ms deadline | Owned child tree terminates; cleanup recorded |No success claimed |`timeout`, exit1 |
| Library client regression check | Native import/query exits0 |2/2; `/selection` returns2 |No reload requested; existing wire observations keep overall `differences` |

The full GUI tests check area/party, populated inventory/record names and HP, record overview and visibility; presence of the requested load/create/overwrite callbacks; disabled empty-name save refusing its callback; and byte-identical created-save files after cancelling overwrite. Stock and BAM runs create one `Redux GUI Baseline` save, with valid GAM/SAV, portraits and a **204×153 BMP preview**, discover it again in the save picker and reload it through the stock load callback in a separate process. Input fixtures and the created save used for reload retain their hashes. Fifteen mutation tests pass, including missing/blank GUI controls, HP loss, changed globals, unmatched variable markers and extra elapsed time. These are content checks, not visual-parity assertions.

Development failures are retained in the evidence inventory. The first host used the wrong shader cwd; the next called GUILOAD outside its normal script/global initialization; a30s deadline was insufficient. GDB identified an adapter crash dereferencing a closed window's removed primary scripting reference. A later adapter cleanup crash destroyed video before GUI sprites. Null checks and the [stock destruction order](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/GemRB.cpp#L51) fixed those external-host defects; subsequent stock/BAM/screen runs exit0. **These crashes are not counted as GemRB product defects.**

## Save differences: established contracts versus unresolved behavior

**Subsequent investigation:** [IMMCLOUD lifecycle results](immcloud-lifecycle-investigation.md) identify equip/persistence accumulation and reproduce it over four stock cycles. A private timing-only item control stops growth. The counts below preserve the earlier GUI observation; the cause is now characterized, while original-runtime parity and a production fix remain open.

The raw strict comparison is retained.449 JSON leaf differences do not mean449 engine bugs: effect insertion shifts list indices, and party actors also appear in the area snapshot.

A separate, explicit diagnostic applies three source-verified representation contracts:

- GAMEV2 writes integer seconds and reads them back as15Hz ticks. Stock pre-save time32717 reloads as32715. Only pre-save time is rounded for this diagnostic. [Writer](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/GAMImporter/GAMImporter.cpp#L776), [reader](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/GAMImporter/GAMImporter.cpp#L83).
- Script variable names are case-insensitive; the writer uppercases them. Observed `bd_chapter_save`/`BD_CHAPTER_SAVE` and `movescreen`/`MOVESCREEN` retain their values. [Variable type](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/includes/ie_types.h#L103).
- Actor locals are stored as opcode187 marker effects. The diagnostic recognizes only observed opcode187/special1/timing11 records whose name/value independently match the collected actor locals; it continues comparing those locals and all other effects/order. Imoen's two additional records represent `HASBEENINPARTY=1` and `BD_JOINXP=1`. [CRE variable writer](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/CREImporter/CREImporter.cpp#L2541).

After these declared conversions, the stock comparison retains **53 leaf differences**, all in the Smoke Mephit at `[2573,2461]`: seven additional effects from **IMMCLOUD**, five opcode267 string protections and two opcode101 protections (parameters134/216). No effects disappear in the multiset comparison. In this collected state, party, stored NPCs, variable values and other non-effect fields match under those contracts. The BAM run retains the same53 differences plus4 NPC color differences. **The cause and gameplay impact of IMMCLOUD reapplication remain unverified.** Keep this as a minimal normal-mode reload fixture; trace effect construction/application before calling it harmless or fixing it. Do not mask it to obtain a green save result.

These results strengthen the earlier [library-mode tests](save-import-and-harness-results.md) but do not replace an original-executable runtime oracle, complete SAV/area/container/world-map comparisons or timed-effect/campaign fixtures. Versioned Redux saves should explicitly decide whether to preserve subsecond ticks; this legacy-format rounding does not mandate precision loss in the future format.

## Missing information and fonts

The stock, BAM and18px TTF experiments produce **identical control-text JSON hashes** for the inspected inventory and record screens. Font configuration changes pixels and metrics, not their empty content.

| Screen | Runtime observations | Interpretation |
|---|---|---|
| Inventory |15 labels,13 nonempty, none hidden; labels `0x10000055`/`56` empty; text areas77–80 empty; feedback area64 empty |Names/class/HP and section headings exist. Missing THAC0/damage/detail assembly is distinct from glyph rendering. Feedback may legitimately be empty |
| Record |26 labels,21 nonempty, none hidden; five additional labels `0x1000003d`–`41` empty; text areas53–56 empty; overview45 contains483 characters |The record is partially populated. Blank panels cannot be explained by wholesale TLK failure |

The earlier CHU/TLK metadata report counted strings present at resource indices, including placeholder index0. **That was not proof that every label should display its raw TLK entry.** Runtime control observations supersede that inference. No missing general text database or missing system-font directory is established as the root cause.

For inventory, the existing script explicitly leaves EE assembly incomplete: [GUIINV TODO](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/GUIScripts/bg2/GUIINV.py#L83). The actual BG2EE `ui.menu` from `data/Patch2.bif` places `INVSTATS` at line5852 and adds AC/HP details and THAC0/damage elements around it. Its record menu uses `GUIREC2` at line643 and a different menu composition. The stock GemRB CHU/GUIScript screens do not execute that Lua composition. This is verified missing screen assembly, not evidence that GemRB needs an EE Lua interpreter or that the renderer must be replaced. [CHU label import](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/CHUImporter/CHUImporter.cpp#L291).

Font selection is now observed at runtime:

| Font | Stock type/line height | BAM experiment |18px TTF experiment |
|---|---|---|---|
| NORMAL |TTF /13px |BAM /13px |TTF /17px |
| STONEBIG |TTF /18px |BAM /16px |TTF /23px |
| STONESML |TTF /14px |BAM /16px |TTF /18px |
| NUMBER, STONSML |BAM /14px |BAM /14px |BAM /14px |

Stock loads seven TTF fonts and seven BAM fonts. Game TTF assets include NORMAL's `R PostAntiqua Roman`, STONEBIG's `Benevento` and STONESML's `AmericanUncial`; hashes and font name records are preserved in metadata, without extracting game assets into documentation. This does not provide a complete runtime provider trace. [Font table loader and preferred type](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Interface.cpp#L1249).

Verified font limitations: the [TTF manager ignores requested style/background](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/TTFImporter/TTFFontManager.cpp#L87); the [BAM manager ignores requested size/style](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/BAMImporter/BAMFontManager.cpp#L34); text advances use [glyph bitmap width](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GUI/TextSystem/Font.cpp#L482), with kerning, rather than a separately represented typographic advance. These are relevant to typography and scaling, but their contribution to every reported visual defect is not quantified. Larger TTF text is visibly larger; record text occupies more space. BAM preference changes the look and includes stippled small labels. **Neither experiment restores blank panels or qualifies as a font fix.** No override is installed into the normal player configuration.

## Prioritized next decisions and work

1. **Persistence:** isolate the IMMCLOUD delta with before-import/after-init/after-entry traces; add original saves with timed effects, equipment and containers. Keep variable-marker and clock contracts explicit, with raw diffs retained.
2. **UI completeness:** build a field/function coverage map for inventory and record: source data, derived calculations, tooltips and interactions. Use it to specify the approved modern UI view models. Refactor screen assembly; retain CHU importing as a compatibility adapter rather than reproducing every EE layout.
3. **Typography:** define scalable font roles, measured advances/line metrics, fallback and glyph coverage, overflow/scroll policy and readable sizes. Retain resource import and SDL/OpenGL initially; wrap font selection/measurement and characterize individual defects before replacing any component. Add human-approved reference captures and pixel-region checks; text presence alone cannot certify readability.
4. **AI harness:** preserve the working external adapter and bounded commands. Specify stable semantic IDs, command completion/error states and update/observation boundaries before adding move/wait/tick/RNG commands. Current discovery is scoped to named packs and controls; universal UI traversal, active-session RPC and automated campaign coverage remain future work.

Phase0 remains open. Existing core locale failure, skipped cases, movement-feel investigation and portable CI remain unchanged; this turn did not rerun or repair the engine's baseline suite.
