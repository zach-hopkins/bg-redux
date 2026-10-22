# Stale dialogue choice pixels

The user-observed red choices remain beneath the next white NPC response in
the successful callback/save journey `20261022T042747Z-jaheira-dialogue-30a50511`.
That result establishes callback and persistence behavior, not rendering fidelity.

External diagnostic `20261022T050052Z-jaheira-dialogue-1c9797c9` holds the second
NPC response without dispatching Continue. Eleven 250ms timer observations retain
the same transcript SHA256
`5ebdc8e9b44fb49021e2e32e3fe5f67ca5ffdc8997c960cf609aa564b7cd933b`.
The reachable runtime types no longer include option spans. Four ordinary delayed
window captures are byte-identical and still contain the previous choice pixels.
Three full-window `MarkDirty` repaint captures progressively attenuate them.
An explicitly cleared backing buffer followed by full repaint removes them.
Further dirty redraws change pixels again despite identical text.

The private `talk/render-comparison.json` records RGB comparisons against the
cleared reference for crop (80,12,690,100), excluding portrait and scrollbar:
ordinary frames differ at 8,864 pixels (maximum channel difference53); successive
dirty frames differ at 8,976/7,410/1,739 pixels (max11/4/4). After the clear,
repeated dirty frames differ at1,687 pixels (max4). This is a backing-surface
composition defect, not a delayed dialogue transition. BMP does not measure alpha.

The observed message window flags are268435470 (`0x1000000e`), including
`Window::AlphaChannel`. Its background is alpha-blended onto a persistent
backing target. Source investigation also found partial alpha in the shipped
MOS/PVRZ panel interior. Merely invalidating the TextArea does not supply a
clean composition surface.

Independent source/art evidence is retained in
`20261022T050133Z-dialogue-panel-alpha-audit-8fae679c`, including extracted MOS,
packed/decompressed PVR, exact provider hashes and reproducible alpha decoding.

Production commit `72846e74b` clears dirty window backing surfaces before the
complete repaint, including the separate scale surface. New isolated candidate
`20261022T050338Z-candidate-2f06ed29` is being built; this is not yet a validated
fix. Full, clipped and scaled render evidence is still required. The latest
external tooling suite passes297 tests (19.432s), recorded separately in
`phase1-integrated-tests-20261022T0508.log`.

The native diagnostic completes eleven samples, exits0, and makes one ordinary
talk request and one response selection. It performs no save. Its wrapper
deliberately reports `passed:false` with `Render diagnostic only; not a
dialogue/save acceptance run`. Phase0 source/binary/fixture, candidate and input
preservation checks pass. All earlier results remain intact.

Run with a fresh external dialogue host and `run --render-diagnostic` using
the standard isolated source/build arguments. This option is evidence gathering,
not a workaround to accept a broken renderer. A production correction must show
ordinary redraw equality to a cleared repaint and stable repeated redraws,
including transparent, opaque and scaled window paths, before acceptance.
