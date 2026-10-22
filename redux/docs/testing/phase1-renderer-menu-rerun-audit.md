# Corrected-renderer broad menu rerun audit

Follow-up limitation: the [spellbook caster validation gap](phase1-spellbook-caster-validation-gap.md)
was found by inspecting actual captured selection/name. The checks audited below
establish window/callback presence, not correct eligible-caster spell content.
Those stronger claims require the corrected external portrait-selection route
and content oracle; prior raw results remain retained.

Independent read-only audit supports the bounded pass in `20261022T052939Z-guarded-renderer-menu-run-35f95c1d`, with nested native run `native/20261022T052943Z-menu-run-ce0b8b58`. Both 1024×768 and 1280×960 complete the declared 107-step menu plan, pass 107 validation checks and retain 51 captures. This is normal-loop menu/callback and collected-state regression evidence on the corrected renderer; it does not mark all menus, typography or Phase 1 complete.

The independent script/result and additional build/visual bindings are private at `C:/BGRedux/phase1-local/results/20261022T054226Z-renderer-menu-independent-audit-483c7e2f`. Private audit result SHA-256 is `fb770aafcb74360dbedcc42a2be26c50a9423712c20925576e25123915342ddf`; successful audit script SHA-256 is `8c145a71734ec00fd21301735e395d911418353a1996d854f56bc59f2a1ff157`. The audit launched no compiler, tests, native host or game and changed no engine/helper inputs.

## Build, process and preservation bindings

| Evidence | SHA-256 |
| --- | --- |
| Guarded build result | `c02779b66c59d9f24946b937e67783b66c4b8df6ae4c39926eb6976dd53484d3` |
| External native build receipt | `d3e2a27b652f29bc0d73ac55f1caafb27298f36a56eeefaf95b874dd349bc580` |
| Guarded run result | `5bce854fdb7c3bf52d0cd54537980eab07ade7bbc17a327bcc45cc8b3580568f` |
| Nested native result | `f4d84b3237015ce7ba2b1c6e86233ba9a0b872bb89e9ad210da9a6ed9058d8a3` |
| Native artifact manifest | `ade6300e0461d5f72c9cdaa66cf9a10edae27d4d0807163a9730c1f5c42a834e` |
| Menu host executable | `613958c3615efcc74224ee3c3438e697c1ca69135d5e80f416b76c14dd411d9c` |
| Corrected candidate core DLL | `a7a5bc65a34fcee8b2f0a8b47d14531d00e48a7cbeed7734a63ee3dc7227df76` |

The host build and both native process commands bind the same executable; build/run DLL identities agree. The import library and compiler still match their build pins. All six build-receipt source files match, all eight guarded source-closure hashes agree between build and run, and live/frozen copies match (16 checks). Both guarded build/run results report Phase 0, candidate, game, closure and probe preservation.

Wrapper PID 1276 exited 0 after 568.026 seconds within its 1,350-second bound. Native PIDs 5444 (1024×768) and 13640 (1280×960) each have exit 0, no timeout, cleanup complete and a completed native host receipt. Each native receipt records 36 callback dispatches, 51 captures, 111 timer ticks and zero native key events. These are historical owned-process terminal receipts, not an inference from whether a PID is currently absent.

All 1,233 native manifest files match their hashes. All 3,507 recorded candidate source files, 48 build files and 3,556 protected Phase 0 source/binary/fixture files still match. Candidate, Phase 0 and game before/after inventories agree. Nine clean-game root file content hashes and 2,457 recursive kind/size/mtime inventory entries independently match current files. Recursive inventory is metadata, not comprehensive asset-content hashing. Both private-game validations preserve immutable inputs and allow their declared private INI/log writes; clean game files remain outside those write roots. Stage config hashes and copied/original fixture guards pass.

## Raw coverage and assertions

Per resolution, the runtime log contains 107 unique step records and 100 explicit boolean UI assertions, all passing. Validation adds one Python-callback-log check and six native inventory/record field checks, producing 107 validation checks. The distinction prevents conflating steps, callbacks and assertions. All 36 individual registered callback receipts report performed:true. The six sheet checks were independently recomputed from visible UI controls, full actor snapshots and the native cached-THAC0 observer: name, current HP and main-hand THAC0 for inventory and record.

All 51 captures per resolution have the requested dimensions, BMP signature/declared file length and companion UI/state/observer files. Collected world state before/after is independently equal after removing **only** the explicitly changed selection field. Before/after native observer files also match byte-for-byte. This does not measure hidden RNG state; the result correctly leaves `hidden_rng_unchanged:null` and pointer hit testing false.

The plan covers inventory; record and six Stats categories with next/previous paging; information/biography/customization/kit/export transitions; an eligible mage spellbook; journal; area/world-map viewing; and options including video, audio, character sounds, gameplay, feedback, autopause, hotkey-editor transition, save/load cancellation and closure. Mage-book applicability identifies Imoen (party member 2, 23 known spells and 12 slots); the fighter is not forced through a mage callback. Priest-book applicability is explicitly context-gated because neither party member has priest spells/slots. An applicability gate is not a passing priest memorization/casting test.

Store/merchant, container/loot, dialogue/cutscene, character generation, travel, level-up/dual-class, sequencer/contingency, rest confirmation and deeper export/customization functions remain separately context-dependent. This plan's hotkey opening and save/load cancellation do not substitute for the separate hotkey apply/persistence or actual save/reload journeys.

## Selected visual review and limits

Independent static inspection of 1024×768 capture 1 (inventory) and 1280×960 capture 7 (Stats/record) shows readable sheet text and no stale glyphs in those inspected views. Coordinator-selected inspection additionally covers 1024 captures 3/4 and 1280 capture 1. This is selected visual QA, not review of every one of the 102 captured frames, original-engine pixel equivalence, or a general font-metric/overflow guarantee. The automated result appropriately retains visual_acceptance:false. Font-role/provider/metric receipts are preserved under game-resources-no-override mode; their presence alone is not full typography acceptance.

The earlier failed/incomplete menu runs and renderer diagnostics remain historical evidence. This corrected-candidate rerun adds bounded regression coverage and does not overwrite or relabel those failures. Physical mouse/keyboard routing, hidden RNG noninterference, nonzero-origin scaled GameControl rendering and full-campaign compatibility remain outside this audit.
