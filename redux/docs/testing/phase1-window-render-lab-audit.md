# LAB dirty-window rendering audit

Independent read-only audit supports the bounded synthetic renderer pass in `20261022T052030Z-jaheira-dialogue-fb841cc0` on the corrected candidate core. All 12 declared LAB window cases match their clean final rendering after child removal, repeated dirty draws and clipped repaint. Paired black/white compositions also reproduce the declared backend-specific transmission. This is evidence for unmanaged Window controls at origin (0,0), not GameControl rendering, nonzero-origin scaled copies or full-campaign fidelity.

The diagnostic's top-level dialogue receipt remains `passed:false` with the explicit reason “Render diagnostic only; not a dialogue/save acceptance run.” Its external window comparison passes; these two outcomes serve different purposes and must not be relabeled.

## Independent checks and provenance

A separate audit script and result are frozen privately at `C:/BGRedux/phase1-local/results/20261022T052240Z-window3-independent-audit-61d91aae`. This audit used PowerShell/.NET file decoding and hashing; it launched no tests, compiler, engine DLL or game. Private audit result SHA-256 is `3910731822ec42ba308cc73de41ce80fddb25ccba50380261cdb16c8cead65bd`; audit script SHA-256 is `1e546486e5f37f033457f91c31ffa39f432ccc4cf7c458c55c3e159e087decb0`.

| Bound input | SHA-256 |
| --- | --- |
| Native diagnostic result | `bfbe8e39323cc340cb8142a931d93419322c226e0341e0dc31f5501106bf91c4` |
| Original artifact manifest | `f2290655a38128f45ca4cb73495680e2662c283d9f2715d33e8c4b86c5b99c13` |
| Fixture v3 receipt | `ee8a75b92db0b0878b46e31f6ca1edc2a573e684c2906d4b899e8e9174ef6fb7` |
| External comparison | `87137e008723861b66292eb65c30e28afc98b2884629630a806d376a4da51eff` |
| External host build receipt | `df6de6a2a399cd48162aeb9eb74ed8765d3bf008e3f58b80b13bfa140340342e` |
| External host executable | `a761a9c620d3a01825c6047f609cdee37132ce70ebbec90c86e8c0fa67f1efac` |
| Compiled fixture header | `619f0da65e4ef670366c401d05caaa68b2673d79662099e52e0d2e0cceb74c81` |
| Candidate core DLL | `a7a5bc65a34fcee8b2f0a8b47d14531d00e48a7cbeed7734a63ee3dc7227df76` |

All 933 artifacts in the native manifest match their hashes and sizes. The external comparison JSON was produced after that manifest and is **not** an entry in it; the independent audit separately hashes it above. All 3,507 candidate source files, 48 candidate build files and 3,556 protected Phase 0 source/binary/fixture files still match their pins. Before/after inventories agree. All 40 source-closure entries match their live and frozen copies (80 checks), and the compiled-source copies match the build receipt. Diagnostic PID 6368 exited 0 after 38.044 seconds within its 180-second bound.

## What the pixels prove

The fixture covers background alpha 202/255 × requested Window AlphaChannel off/on × scale 75/100/125: 12 cases. Each has eight checkpoints with direct RGB plus composition over separate opaque black/white targets. Independent BMP decoding checked every pixel in all 288 BMP/RGB pairs, including file dimensions, lengths, BGR/RGB order and orientation. All canonical RGB files have 57,600 bytes. There is no direct alpha readback: the screenshot implementation is BGR24 with no alpha mask.

All 216 required image comparisons match byte-for-byte: removed-final, three dirty repeats, partial-dirty and full-after-partial each equal fresh-final for direct, black-composed and white-composed RGB. All 12 old scenes differ from their final reference. Clip metadata is exactly (8,20,60,50), with declared sentinel (130,90,15,15). The clipped capture is read after one window draw, before a second draw could repair a lost region. This proves preservation of the actual fresh-reference image under the declared partial repaint.

Sentinel coverage has a concrete limit: fresh references contain 225 pure-green pixels at 100% and 144 at 125%, but zero at 75%; the blue replacement is visible at all scales. The four 75% cases therefore establish preservation of their actual background/replacement image, not survival of a visible green sentinel. Scaled geometry/fidelity beyond this reference comparison remains unproven.

All 96 composition probes are independently recomputed from actual black/white RGB at (6,6), bound to their JSON values, and satisfy the declared transmission within one unit. On this pinned LAB SDL20 backend, DISPLAY and DISPLAY_ALPHA select the same renderer-native format; both requested flag states retain alpha. Alpha-202 backgrounds transmit approximately 53 RGB units, alpha-255 backgrounds 0. This is a background-probe compositing measurement plus whole-image compositing stability, not an entire alpha map or a portable claim about other renderer formats.

The engine change in `cb2c09f3b` clears the current repaint clip on the active target with transparent color and NONE blending, after pushing backBuffer and any scaleBuffer. It avoids accumulating translucent art over removed pixels and preserves pixels outside the clip. The synthetic results support that bounded behavior. They do not independently establish every scaled-buffer source/destination mapping.

## Ordinary dialogue regression and retained history

The separate ordinary run `20261022T052139Z-jaheira-dialogue-82159919` passes using the same external build receipt and core DLL. Result SHA-256 is `2e266d89a2f378fa0b5e983fdc0374a419329074a3f2080ec335c201581f6824`. Independent review matched all 568 listed artifacts, read the native summaries and inspected the static branch-1 BMP (`a1f6120eee576b54cbd550568b02956424003a67fcab91b2716dbf43c9d7d743`). Old red choices are absent; new NPC text and Continue remain visible, with the world visible through the translucent panel.

Talk PID 7568 exited 0 after 77.218 seconds, recording one TryToTalk, 11 branches and 17 events. Fresh reload PID 2844 exited 0 after 18.349 seconds with one load callback and zero talk requests. The receipt reports the expected real save and persisted TalkCount 1, three journal entries and closed Cell01 flags 1634; preservation guards pass. This follow-up audit binds the receipt/native summaries/artifacts and image, without repeating the earlier independent raw wire decoding. It supports the bounded callback/save/reload regression, not original-engine parity or physical input coverage.

Earlier stale-choice captures, whole-clear partial failures, the v1 synthetic-alpha misstatement and the v2 opacity/probe oracle failures remain historical evidence. The [fixture design and supersession record](phase1-window-render-regression-design.md) explains those boundaries. None of this marks all menus, typography, renderer paths or Phase 1 complete.
