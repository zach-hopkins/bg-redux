# Stock Imoen spell cast and persistence audit

Independent read-only review supports the bounded pass in `20261022T043347Z-spell-cast-journey-3dd76c87`: existing party member Imoen casts her existing memorized SPWI102 through registered portrait/Cast/spell-icon callbacks, consumes exactly one ready instance, gains the sourced effects, saves through GUISAVE, and retains depletion and the specified effects after a fresh-process load and second GUI save. This establishes one stock self-cast journey, not general spell or original-engine parity.

The compact public receipt is [phase1-spell-cast-lab.json](../compatibility/evidence/phase1-spell-cast-lab.json). Private evidence remains under `C:/BGRedux/phase1-local/results/20261022T043347Z-spell-cast-journey-3dd76c87`. Result SHA-256 is `2a5cda2eb97749ac0869667d00cbdbf7de90fcf94bdd28274427da9c1208f25a`; artifact-manifest SHA-256 is `5e10a2c95b5f790d9b314962891eb0db61176818923f79efb338970bf354c754`. No licensed assets or screenshots are published.

## Action and observed release

Owned cast PID 13524 exited 0 after 71.239 seconds within its 90-second budget. The portrait control was bound to party member 2 and selected only Imoen (runtime ID 10003). Four consecutive eligible running observations preceded opening the registered Cast control at sample 9. At sample 10, one enabled resref-bound icon dispatched `ActionsWindow.SpellPressed`: SPWI102, mage type 1/level 0, memorized slot 0, header 0, casting time 9, self-target type 5, one ready instance. Static inspection of `spell-icons.bmp` confirms the spell-icon row was displayed; this is not a full visual-fidelity assessment.

The post-callback sample contains a queued action 75, resref SPWI102, target mode -1 and target ID 10003. Independently extracted shipped ACTION.IDS identifies 75 as `NIDSpecial6`; the diagnostic parser's own action object is never queued. Samples 11–30 observe the real casting action, SPWI102 casting resource and self `LastSpellTarget`. The ready instance is depleted by sample 11. Sample 31 observes an empty current/next queue plus the newly sourced effects. This proves the declared release conditions, rather than treating callback dispatch alone as completion.

The required effects are AC opcode 0 with parameters (6,16) and portrait-icon opcode 142 with parameters (0,12), source SPWI102, caster 10003 at release. Modified AC changes 6→2. Their absolute expiry tick is 73325; both remain active at cast-end game tick 33038 (40287 ticks remaining). No preexisting SPWI102 effects are present at the command boundary. The adapter also checks memorization/known-slot and inventory conservation, including unchanged other-party memorization and items. The spell stays as a depleted record rather than disappearing: raw CRE decoding finds 14 memorized records before and after, with SPWI102 flags 1→0.

All 89 focused action diagnostics in each process match the corresponding clock sample's game time, actor identity, action and target fields: 80 running and nine paused observations per process, 178 total. One cast command and one Cast-menu opening occur in the first process; neither occurs during reload. These samples demonstrate normal-loop progression under this external harness. They are not an RNG noninterference measurement or a proof about unsampled actions between checkpoints.

## Save chain and fresh process

The first GUI save produced GAM SHA-256 `a14a4c59c295f880967a93d153614ee101a4a146d4c5dc760efd68cb7475e51b` and SAV SHA-256 `45a52966008a46e7bc362a3ad89f4d50754ea1a72eae8881acaf388b9a49fc9e`. Five output files match the live save, frozen copy and reload input. Fresh owned PID 11952 exited 0 after 50.975 seconds within its 90-second budget, performed zero Cast/spell-icon callbacks, retained depletion and AC 2, then wrote a second ordinary GUI save. Live/frozen output checks for both saves plus reload input total 25 matching hashes. The recorded save callback is `GUISAVE.ConfirmedSaveGame`; its return code was not observed (`save_return_code_observed=false`). Actual files and decoded state establish the bounded save outcome.

Independent PowerShell/.NET parsing of the embedded CRE tables in the protected input, first frozen save, reload input and second frozen save reproduces Imoen's identity, SPWI102 depletion and sourced persistent effects. Each saved CRE contains 12 serialized effects, including four sourced SPWI102 effects (0,142,282,174). This is not the total live expanded effect queue: the final live snapshots contain 80 effects. The required AC/icon timing is 4096 with expiry 73325 in both saved files. After reload, the live required effects have caster ID 0, so full effect-record/caster-identity preservation is explicitly not claimed. Source, opcode, parameters, timing, expiry, depletion and observed AC remain the asserted contract.

At reload-end tick 33355 the required effects have 39970 ticks remaining. The clock advanced and remaining lifetime decreased; the run did not reach natural expiry or test expiration/removal behavior. Before/after GUI-save gameplay snapshots have no reported differences within each process. The second save differs in bytes as ordinary runtime progression continues; cross-process byte identity is not required.

## Resource and build provenance

All 565 artifact hashes/sizes matched, including 15 screenshots, frozen helper inputs, raw diagnostics and both saves. All 3,507 candidate source files, 48 candidate build files and 3,556 protected Phase 0 source/binary/fixture files still match their recorded pins. All 53 source-closure entries match both live and frozen files (106 checks). Both private-game receipts pass clean-game inventory/root and copied-immutable-input guards, allowing only declared private `GemRB.log` changes. They do not hash the complete linked asset tree.

The external host SHA-256 is `9592d7141cccbf7158ea2d000565f46577deac3647e7ab0920a3e470ef4349f4`; its successful build receipt SHA-256 is `0bed7d0dbdaa8e6595dff42abe4c4feb09c16bd4ebfce0f125808deced67d891`. Compiled GUI source is `4eb24ba42906ce93f6490e6cc493a956af62a7976b5b79b4c307f093281e5349`, journey header `7687ea1826fb451fcbfd311fed6f81dca3a0ac4c174db5a59d403f140c408512`, and candidate core DLL `79650612926d96a8748320bcf3d0f8f265f7d20747448a30a5ec8918b472ebb9`.

Independent KEY/BIF extraction reproduces all five shipped resource hashes: AR0602.BCS, BDDEFAI.BCS, DPLAYER3.BCS, ACTION.IDS and the 442-byte SPWI102.SPL (`7525db308f6d76b6e31587623fe9b19cfe2a8b49f0b1fdb43b6df57906974b70`). Both build/run frozen resource copies match. The two stock engine tables are separately proven by actual `GetResourceStream` paths and frozen returned bytes in both fresh processes:

| Resource | Selected provider | Bytes | SHA-256 |
| --- | --- | --- | --- |
| spldisp | `gemrb/unhardcoded/shared/spldisp.2da` | 852 | `5848ec7e0ac0c5678b7b1b39ae5d19ebf2d003f8d78883914140b6281109b122` |
| guibtact | `gemrb/unhardcoded/bg2ee/guibtact.2da` | 3054 | `d9732249ab3e71ac805587f35370005961903e4daba7254e9ad18dc72a73e144` |

These are actual selected resource streams, not an assumption that a particular source directory wins. Earlier resource-provider and link/build failures remain failed historical evidence; only the corrected external public3 host generated this pass. No engine change is implied by those external corrections.

This audit changed documentation only and launched no tests, compiler, native host or game. Physical pointer/keyboard input, original-engine spell parity, RNG behavior, other targets/spells, interruption/failure cases, full effect lifetime and general UI fidelity remain unobserved by this journey.
