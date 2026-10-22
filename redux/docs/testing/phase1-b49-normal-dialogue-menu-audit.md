# b49 normal dialogue and recruited-party menu audit

Read-only independent review on LAB, 2026-10-22. No runtime, build, test, or production source changes were performed by this review. No material blocker was found within the recorded scope.

The private audit is `phase1-local/results/20261022T071512Z-b49-dialogue-menu-audit-fdc5fe89/audit.json`, SHA-256 `ff2bf7558141818dd5016b580b9af896c69ff8600f25e06981246599800dfecb`. Its pinned independent stdlib decoder checks GAME/CRE/SAV/ARE lengths and complete zlib streams; it does not import journey validators. The auditor source is preserved beside the results as `b49-dialogue-menu-audit-20261022-worker.py`.

## Normal dialogue

Raw root: `phase1-local/results/20261022T064605Z-jaheira-dialogue-dbcdba69`.

| Receipt | SHA-256 |
| --- | --- |
| result.json | `7f805a14863d8f987254e74ab18d8189a221d85c9a7e6382ba07bcb1e72e435a` |
| artifact-manifest.json | `d862a6bb5c39e542337ce123558c6e102c0e2a4c3ee1bf54e2d2281d887ca3cb` |
| driver/build.json | `ce93f21b7014d3e136fde13d2c2b1dd0e642f5a0c324732e5a1ae60f32720dac` |

All 568 declared artifacts and 40 historical frozen source pairs were rehashed. Historical sources were checked against their frozen build/run copies; later authorized external adapter changes do not invalidate those historical inputs.

PID 9200 exited 0 after 80.575 seconds; fresh reload PID 4644 exited 0 after 18.722 seconds. Distinct caller nonces bind both processes. The talk trace contains exactly one ordinary talk request, two `TextArea::SelectAvailableOption` responses, nine Continue/End callbacks, and the GUI save callbacks (17 total events). The eleven expected NPC strrefs are 899, 20128, 909, 20142, 912, 20132, 20136, 921, 20176, 20177, and 945. Every raw transcript has exactly one newly appended occurrence of that branch's NPC sentence, with actual Jaheira/leader dialogue participants. This supports sequential displayed-state identity, not direct observation of the private dialogue-state index.

Independent saved-byte decoding confirms party count 2, Jaheira still a stored NPC with dialog JAHEIRA and TalkCount 1, Cell01 flags 1634, and journals 34089/96383 retained plus unsolved 34105. The immutable GUI-created save matches the fresh reload input exactly; reload issues no talk request and reproduces the quest/door/actor checkpoint. This case does not recruit Jaheira. Source, binaries, fixture, candidate and per-process private-game guard outcomes remain true.

## Menu run

Outer root: `phase1-local/results/20261022T064911Z-guarded-textarea-menu-run-eba67ffa`; native child `native/20261022T064915Z-menu-run-6b2edba0`.

| Receipt | SHA-256 |
| --- | --- |
| outer result.json | `fa7b31da4526a08b70ce0ce0b623c980be1206e1cb4e6dea1ebe919d50459150` |
| native result.json | `b087ba6e6ea6815291916040a6e384d70b1d1b5f7bb3e01836d218ba743461f5` |
| native artifact-manifest.json | `f2248f027522f0eec4b9968f8140f6fe59b6db8650f7c59790a2e05eafdfa7cb` |

All 1,263 declared native artifacts were rehashed, including all 102 BMP lengths and requested dimensions. Both resolutions (1024x768 and 1280x960) complete 107 planned steps, 39 callbacks and 51 captures in distinct owned processes (8212 and 2304), with exit 0, no timeout and completed cleanup. Each has 187 reported checks: 104 raw runtime assertions plus 83 additional validation checks. The review independently checked raw runtime assertions, actor/content bindings, all 72 populated/empty spell controls per resolution, capture inventory and exact collected-world equality after removing only selection.

The exact six-file three-party fixture is bound to the previously measured recruitment result (`73479cf269f2aa27e3651db75dec2bc6779b2b2c051a44569f96fdc5ed2bba55`). Imoen is selected for the mage book and Jaheira for the priest book. Captured actor spellbook resrefs and ready flags agree with the content contracts; populated controls have their exact slot values/tooltips and pictures, and empty controls expose no stale displayed spell. Sprite resource identity is not exposed by this observer.

Caller nonces match launch pins, native host and runtime receipts; configs retain their before/after hashes. Six separate preservation outcomes (Phase0, candidate, game, source closure, probe, recruitment parent) pass; complete before/after inventories agree. Frozen external sources match the host build receipt, and build/run engine-DLL hashes agree. Lossless compression of other completed artifacts does not establish corruption: the artifacts used here still have their declared logical hashes.

## Selected visual scope and limits

Four static BMPs were inspected directly: dialogue `talk/capture/branch-0.bmp` and `branch-10.bmp`, menu `1024x768/capture-25.bmp` (Jaheira priest book) and `1280x960/capture-23.bmp` (Imoen mage book). The opening dialogue shows the fresh sentence and five choices; the final frame shows its new sentence and End Dialogue without the earlier choices overlaying it. The selected spellbook frames show the expected actor names and populated known/memorized icons. This is selected-frame evidence, not blanket visual acceptance or a pointer-hit-test claim.

All operations are callback/native-command observations, not physical OS pointer input. Menu equality concerns collected fields only; hidden RNG state was not sampled. No original parity, complete gameplay coverage, or Phase1/campaign completion is asserted. Other context-sensitive menus remain separate work; the generic context list must not erase the actual populated priest-book coverage measured here.
