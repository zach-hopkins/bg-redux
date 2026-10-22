# Dirty-window render regression fixture

This is a source-only fixture and review proposal. No build or native result is claimed for the new header. The callback/save passes for the Jaheira journey remain valid within their stated scope; the visible stale choices are a separate rendering defect.

## Source and private resource evidence

In the successful Jaheira run `20261022T042747Z-jaheira-dialogue-30a50511`, branch 1 no longer exposes the old numbered choice strings or OptSpan containers, while its BMP visibly retains the dim red choices behind the new NPC text. `ClearSelectOptions` deletes the old selector; the mismatch concerns retained pixels, not a proven retained semantic option. `WindowManager::GetScreenshot(nullptr)` already invokes DrawWindows and SwapBuffers, so that image includes a draw attempt.

Independent KEY/BIF/PVR decoding is frozen privately at `C:/BGRedux/phase1-local/results/20261022T050133Z-dialogue-panel-alpha-audit-8fae679c`. It contains raw licensed resources, decoded PVR, the standalone `reproduce.ps1`, resource/BIF hashes and the exact DXT5 calculations. It loads no engine DLL or game. The script accepts a new output directory under `phase1-local/results` and rejects overwriting an existing result.

| Input | SHA-256 |
| --- | --- |
| chitin.key | `1818ffebb2424992fb39fb13509e7f629ac819b08a553c2dd4ac25f2e40a979f` |
| guwbtp30.mos | `6530f5d55602103394d540886d98cd246e728ace98810a5b5462e75f46b94021` |
| mos0178.pvrz | `cceeff3a7bda9cf1c3208966dba2d2e496cfa93a43891c961e0aaf8f3e012a3c` |
| decompressed mos0178 PVR | `8be2ebd1494bce926fe430d135e2427619623d18d6e16eef8ca4ca5d0a79131b` |
| independent decoder | `92e7feecc1b18058250737a3a5284a6e0e1da61725673554c63517516b9b736f` |

The native log resolves GUIW10 and guwbtp30. The 808×300 MOS V2 interior uses page 178, source origin (1,1), destination origin (0,64), size 808×236. MOS coordinates (200,80), (400,100), (150,150), (500,200) independently decode to DXT5 alpha 202. These are four sampled pixels, not a complete alpha map. The actual diagnostic MSGWIN flags `0x1000000e` include AlphaChannel; an earlier opaque-window assumption is superseded.

`MOSImporter` preserves PVR alpha. `Video::BlitSprite(Point)` adds BLENDED, and the SDL path uses SDL_BLENDMODE_BLEND. Backgrounds therefore blend onto persistent window surfaces. Clearing removed views alone does not restore the old pixels. Root's separately retained ordinary/dirty/explicit-clear diagnostic is the runtime discriminator; this document does not promote the new synthetic fixture to measured evidence.

## Review of the initial clear proposal

Commit `72846e74b` caches NeedsDraw, clears backBuffer on a dirty window, pushes it, then clears/pushes scaleBuffer when present. Dirty-only clearing is necessary: a clean draw reuses retained child pixels. For a complete repaint the ordering is consistent with the existing view-tree invalidation, and transparent clearing preserves AlphaChannel art instead of imposing an opaque black panel.

With scaling, scaleBuffer is the active source of drawing; clearing backBuffer alone cannot fix retained source pixels. DidDraw copies scaleBuffer into backBuffer with NONE blending. Clearing both is redundant when that copy fully replaces the destination, but the synthetic scaled cases must establish actual behavior rather than assume complete replacement or correct source/destination rectangles.

The remaining concern is clipping. View::Draw intersects the caller clip and repaints within it, whereas SDLTextureVideoBuffer::Clear() clears the entire texture. Whole-surface clearing can erase pixels outside a partial repaint. Either clear the actual target-local repaint region through the existing region overload, or establish an explicit full repaint before whole-target clearing. Do not widen a caller clip or multiply scaled coordinates without demonstrating their mapping. Preserve the buffer stack and restore the caller's VideoDriver clip on all exits.

## Standalone fixture interface and acceptance

Include [window_render_regression.h](../../tools/phase1/native/window_render_regression.h) and call `WindowRenderRegression(out)` once after normal engine/video initialization. The function uses unmanaged synthetic Window objects and public View/Window/Video APIs; it neither registers gameplay windows nor requests game callbacks, resource changes or actor mutations. The enclosing host must freeze the header, its own source and build identity, retain before/after gameplay evidence, and own the bounded process. Build/run belongs to the coordinator.

The function creates a fresh `out/window-render-regression` directory, rejecting reuse. It emits 12 cases: background alpha 202/255 × window AlphaChannel off/on × scale 100/75/125. Each case draws a large red child, removes it through the public hierarchy, and adds a small blue replacement. A separate fresh Window constructs the identical final semantic scene. A green rectangle outside the partial clip acts as a retained-pixel sentinel. Colored regions deliberately isolate composition from font selection, glyph metrics and licensed art.

Each case emits eight BMPs and eight canonical 160×120 RGBA readbacks: old scene, removed-final, fresh-final, three repeated dirty repaints, one partial dirty repaint, and full repaint after the partial one. Canonical RGBA is top-to-bottom, four bytes per pixel, 76,800 bytes per file; it preserves alpha and avoids BMP orientation/padding differences. Readback follows exactly one DrawWithoutComposition call. In particular, no second window screenshot is allowed to repaint and hide a clipped-clear defect.

`fixture.json` records exact case settings and comparison pairs with `passed:null`. An external comparator must require all 12 cases, all 96 BMP/RGBA pairs and complete file lengths/signatures, then check:

1. Old-child RGBA differs from fresh-final, proving that the removed region was actually rendered.
2. Removed-final and all three dirty repeats exactly equal fresh-final in RGBA, including alpha.
3. Partial-dirty exactly equals the same reference: semantics are unchanged, so the outside green sentinel and background must survive the clipped repaint. A whole-target clear followed by clipped rendering must fail this check.
4. Full-after-partial exactly equals fresh-final, recording recovery separately from the partial result.

Keep full, repeated, partial and scaled outcomes separate in reports. An unsupported export, readback, scale or capture failure is a retained failure/incomplete case, never a pass or implicit skip. Exact synthetic equality is appropriate because no game animations, text, clock or random data enter these unmanaged surfaces. It does not replace the fresh native dialogue visual comparison against the original engine.
