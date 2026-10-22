# Fresh Erase candidate baseline audit

Fresh baseline `20261022T105238Z-erase-base-4ec5c4f2` has independently verified passing execution: 24/24 vanilla and 20/20 GUI assertions, no skips, and all six actual native children exiting zero. Compatibility remains **differences**, with both cross-build comparisons explicitly `unreviewed-differences`. The two outer harness exits remain 1; they are not reinterpreted as compatibility passes.

The [compact evidence](../evidence/phase1-erase-candidate-fresh-baseline-audit.json) binds raw result SHA-256 `c39b468d4454870aab651ee309f41e605ea73bfc495d6c9e86a14332864b6cf3`, independent reader, private full artifact inventory, build receipt and exact residuals. The standard-library reader imports no harness validators. It evaluates vanilla assertions against actual snapshot values, GUI content/event/cancel-byte assertions against raw UI/world snapshots and native events, and independently reconstructs the existing declared semantic normalization and differences. This is bounded content coverage, not comprehensive world or visual correctness.

| Residual | Fresh Erase candidate | Previous 5a baseline | Earlier b49 | Exact observation |
| --- | ---: | ---: | ---: | --- |
| Vanilla reload 1 | 2 | 4 | 0 | Changed color-stat values/paths |
| Vanilla reload 2 | 0 | 0 | 0 | Equal empty rows |
| Repeat import | 26 | 22 | 24 | Changed color-stat values/paths |
| GUI reload | 449 | 449 | 449 | Entire rows exactly equal |
| GUI legacy diagnostic | 53 | 53 | 53 | Entire rows exactly equal |

Immediate predecessor is `20261022T094904Z-sb-base-4565dad5`; b49 is `20261022T072341Z-b49-native-baseline-b6faf631`. Reload-1 now retains current-area normalized actor 31 stat 210, 4109694196 to 2896997548 in both base and modified arrays. The previous actor-3 stat-209 reload rows are absent. Repeat-import adds paths for actor 7 stat 208, actor 24 stat 209 and actor 31 stat 210, and loses actor 5 stat 212 paths relative to 5a; other values also vary. All 26 exact rows, both reload rows, file hashes and added/lost paths remain in the public evidence. No color change is silently waived, assigned an unmeasured cause or promoted to a compatibility rule. The identical 449/53 GUI residuals also remain differences, including their existing representation/effect-growth fields.

Four vanilla child PIDs 1472/9884/17184/1360 and GUI child PIDs 14632/6448 exited zero without timeout or required cleanup; their bounded process receipts remain separate from outer PIDs 15708/5684 exiting 1. Config hashes, private GamePath, probe source/binary/core bindings, actual GUI cancel/save files and fresh reload snapshots agree. External save/GUI hosts were rebuilt; capabilities is the declared harness protocol, not a new engine feature proof.

Candidate `20261022T104353Z-candidate-3f8cf4a0` binds source commit `3f5cad09776168c11946963332b5a96602365a93` and core SHA-256 `004f807928cba3453cf13fcc82e89c6c2135d10c2c044aee7405d92e7d34e923`. All 3509 actual source files, 61 binaries and five build-support files match its receipt. Five frozen top-level sources, 75 runtime inputs, canonical fixture bytes and 1017 inner-run artifacts were independently hashed. Candidate and Phase0 before/after inventories match; private-wrapper source-root and copied-input guards pass. Linked game asset contents are not all hashed, and the wrapper is not a security boundary.

No tests, compiler, engine or original-game processes were launched for this audit; no historical evidence was modified. Earlier failed infrastructure attempts remain failed and are covered by their separate historical audit. This fresh baseline does not itself exercise the corrected Erase callback or certify typography; those have separate bounded receipts. Campaign, physical pointer input, original parity and broader compatibility remain outside this result.
