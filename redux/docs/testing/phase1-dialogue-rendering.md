# Stale dialogue choice pixels

Current correction: `cb2c09f3b`, isolated candidate
`20261022T051113Z-candidate-df3a5c5e`. The held-response render and twelve
synthetic alpha/scale/clip cases pass their bounded comparisons. The ordinary
dialogue save/reload rerun and broader menu/world regression are still pending.
The external tooling suite passes301 tests in32.039s
(`phase1-integrated-tests-20261022T0520.log`).

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
`20261022T050338Z-candidate-2f06ed29` was built and subsequently rejected below.
The earlier external tooling checkpoint passed297 tests (19.432s), recorded in
`phase1-integrated-tests-20261022T0508.log`.

The new candidate's held-response diagnostic
`20261022T050739Z-jaheira-dialogue-57c244d2` completes all eleven observations:
every ordinary and dirty text-region RGB comparison exactly matches the clear
reference. Input/candidate/Phase0 guards pass. This fixes the observed full-draw
symptom, but is insufficient for accepting the broad renderer change.

Synthetic window run `20261022T051009Z-jaheira-dialogue-09e00275` confirms a
regression: all12 partial redraws erase cached pixels outside their clip, while
all removal/full/repeated-dirty comparisons match fresh reference windows.
Candidate `72846e74b` is therefore rejected. Narrow correction `cb2c09f3b` replaces
only the active target's repaint clip using a transparent, unblended fill, and
was built separately in `20261022T051113Z-candidate-df3a5c5e`.

That candidate's held-response run `20261022T051834Z-jaheira-dialogue-33323dfe`
has exact RGB text-region equality to the cleared reference for all ordinary and
dirty samples. The coordinator visually verified the ordinary capture: old
choices and overlapping old glyphs are absent.

The fixture's initial `.rgba` files do **not** measure target alpha: SDL20's
public screenshot API reads RGB24, so `GetPixel` synthesizes the fourth byte.
Those files establish RGB equality only, including on AlphaChannel windows.
The initial design's alpha-readback claim is superseded. No earlier artifacts
are rewritten.

Version2 synthetic run `20261022T051612Z-jaheira-dialogue-acc00b73` passes all216
direct/black/white image equality comparisons, including partial repaint, but
fails its opacity oracle. Two assumptions were incorrect: this SDL2 backend uses
the same native texture format for DISPLAY and DISPLAY_ALPHA; and probe(80,80)
crosses the old opaque rectangle in the75% case. Those failures remain retained.

Version3 run `20261022T052030Z-jaheira-dialogue-fb841cc0` moves the background
probe to(6,6), binds its expectations explicitly to the LAB SDL2 shared native
format, and passes all12 cases,216 image comparisons and96 opacity probes.
Every BMP is independently decoded and checked against its RGB companion.
The paired black/white backdrop differences measure transmission53 for alpha202
and0 for alpha255, within one channel rounding value. This is actual compositing
evidence, not direct texture-alpha readback. It covers unmanaged controls at
window origin0 with75/100/125% scale; dynamic GameControl rendering and nonzero
origin scaled copying remain separate regression requirements.

The first candidate CTest run (`phase1-core-tests-20261022T0507.log`) passes6/7
executables; the core executable crashes after the nine movement skips. This
is retained as a failure. Source review identifies the existing CTest CWD issue:
relative `../../tester.cfg` lookup fails, then failed fixture teardown dereferences
uninitialized core. Correct-CWD run `20261022T051513Z-correct-cwd-core-e071d5bb`
uses the established external harness environment and copied resources. It exits1
normally:229 passed,1 retained StringToUpper locale failure,9 skipped,6 disabled.
Preservation checks pass; this is not a green core suite.

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
