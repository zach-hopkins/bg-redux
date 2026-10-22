# Stock Jaheira dialogue, journal and reload audit

The bounded ordinary dialogue journey passed on LAB in `20261022T042747Z-jaheira-dialogue-30a50511`. Independent read-only review found no material contradiction in the completed receipts. This covers one shipped AR0602 Jaheira conversation, registered response/Continue/End/save/load callbacks, its actual journal and talk-counter effects, and loading that save in a fresh owned process. It does not establish all-dialogue coverage or original-engine parity.

The compact public receipt is [phase1-jaheira-dialogue-lab.json](../compatibility/evidence/phase1-jaheira-dialogue-lab.json). Private evidence stays under `C:/BGRedux/phase1-local/results/20261022T042747Z-jaheira-dialogue-30a50511`; no licensed dialogue text, assets or screenshots are published here. `result.json` SHA-256 is `d1d8a784ff203df8793bc4e0726deb67f95b6dd896c17095f6d6ce33f4a1bd3d`, and the artifact-manifest SHA-256 is `958f1cd894cb5acc14a0feb5b59943306566292ff40d59e062a79d92f8176a1b`.

## Actual route and outcome

Talk process PID 9448 exited 0 after 78.352 seconds within its 120-second bound. Seven natural startup idle samples preceded exactly one `GameControl::TryToTalk/NIDSpecial1` request to Jaheira runtime ID 10005 from leader 10002. There were 17 recorded events: one load callback, one talk request, 11 dialogue selections, and four options/save-name/save callbacks. No forced dialogue state or synthetic success globals were used.

The pinned DLG path was:

| DLG state | NPC strref | Global transition | Visible response index |
| --- | --- | --- | --- |
| 0 | 899 | 4 | 4 |
| 47 | 20128 | 94 | Continue |
| 5 | 909 | 9 | Continue |
| 51 | 20142 | 98 | Continue |
| 8 | 912 | 12 | Continue |
| 49 | 20132 | 96 | Continue |
| 50 | 20136 | 97 | Continue |
| 9 | 921 | 14 | 1 |
| 58 | 20176 | 105 | Continue |
| 59 | 20177 | 106 | Continue |
| 14 | 945 | 45 | End |

The two numbered response choices used `TextArea::SelectAvailableOption`, visible indices 4 and 1 (displayed numbers 5 and 2), with response strrefs 904 and 923. All nine Continue/End events used registered control actions. Their raw TLK labels and control flags were preserved; exact observed labels matched `Button::SetText`'s LOWERCASE-first, otherwise CAPS transformation. Static review of `branch-1.bmp` also confirms a visible uppercase Continue control. The earlier raw-label guard failure is not evidence of an engine capitalization defect.

All 11 branch checkpoints contain a fresh increase of the expected NPC text in the actual transcript, compared with the previous checkpoint. Independently parsed shipped TLK text matches all 15 referenced strrefs, including the numbered responses and Continue/End labels. Branch scenes retain the expected target/speaker identities, closed Cell01 and two-member party. DLG state numbers describe the pinned resource path inferred from this sequential text/response evidence; the observer does not sample the private dialogue state index. Text observation uses the declared GCC RTTI/public-container seam, not OCR or a guarantee about other toolchains.

The ordinary GUISAVE path wrote a real save. Independent GAM and decompressed SAV decoding confirms Jaheira's serialized TalkCount changed 0→1, exactly one journal strref 34105 was added in section 1/chapter 1, and the total journal count changed 2→3. Existing entries 34089 and 96383 remain. Cell01 flags remain 1634 (closed), the party remains two, and Jaheira remains unrecruited. Her saved CRE SHA-256 is `0f102b289685c14bc021442be2664dc7a00b3f45ee5d8b70b1a653a340b173d9`; its size changes from 3,008 to 3,272 bytes during ordinary serialization, so byte identity with the starting CRE is not claimed.

Fresh reload PID 14112 exited 0 after 18.320 seconds. It executed one registered GUILOAD callback, six startup idle samples, zero talk requests and zero saves. The loaded live observations retain the same target identity, counter, journal entry, party and closed door. Five save files match across the live output, frozen save and reload input (15 independently checked hashes). This proves persistence of the specified effects through this fresh-process load; it does not claim byte identity of all runtime state or absence of ordinary clock/AI progression.

## Pins and independent checks

All 567 listed artifact hashes and sizes matched, including 19 screenshots and frozen driver/source inputs. The external host SHA-256 is `c3dc4fb84d5ce8e1e69c3f5ca185cf385acb847e509b0b1ff87daa8194bab7d7`; the compiled dialogue source SHA-256 is `3efce63ac88475b7e0e1ad93ff6370b402d397dee5166960d179379cf2af396d`. The successful external build receipt SHA-256 is `fc2e78a66a1de4438bba7f53ce83772e261e3a23720a864de93800e19c9320c7`. Its three compiled sources and frozen helper closure remain bound to that build. All 39 source-closure entries match their live and frozen files (78 checks).

The candidate core DLL remains `79650612926d96a8748320bcf3d0f8f265f7d20747448a30a5ec8918b472ebb9`. All 3,507 recorded candidate source files and 48 build files still match; all 3,556 protected Phase 0 source/binary/fixture files still match. Before/after candidate and Phase 0 inventories agree. Both private-game receipts pass clean-game inventory/root and copied-immutable-input guards; only their declared private `GemRB.log` changes are allowed. Linked asset-tree contents are not comprehensively hashed by those receipts.

Independent KEY/BIF lookup resolves JAHEIRA.DLG from `data/DIALOG.BIF`, 8,272 bytes, SHA-256 `b121dc6d804e52e431c15a1d2dd372b5242f518a31d925ce403c3e633882bbc9`. The shipped TLK SHA-256 is `9e685225ff3c3436a8a35fa7022550620d24a92efe35436a062c02955d9f0952`. These resource-specific checks supplement the narrower private-root guards.

## Preserved failures and limits

Prior failed external builds, the direct `UpdateState` native assertion and debugger run, and selector4's label-guard failure remain failed historical evidence. The successful adapter follows the normal public selector route and exact source-defined button labels. It does not repair the separately documented [direct-public selection reentrancy defect](../compatibility/phase1-textarea-update-state-reentrancy.md).

This audit launched no tests, compiler, native host or game process and changed documentation only. Registered callback dispatch is not physical mouse/keyboard input. Original-engine dialogue parity, other dialogue branches, general rendering fidelity, arbitrary callback reentrancy safety and full linked-asset integrity remain outside this result.
