# Phase 1 typography: source and independent metric audit

2026-10-22 UTC. This audit demonstrates TTF metric losses; it does not certify original EE pixel fidelity, change fonts, or implement a renderer replacement. No game/native test host was launched. The private font bytes remained in the licensed fixture and process memory. Published evidence contains numeric metrics, font family names and hashes only.

## Reproducible evidence

`redux/tools/phase1/font_metrics.py` reads the actual requested resource, pixel size, style, background and BAM preference from `gemrb/unhardcoded/bg2ee/fonts.2da`. That table's SHA-256 is `6a803da7dcd28782b5732f802dd9c9acd0bf6346973eb78418fc9179c27d3ccd`: all listed TTF roles request 14 px; STONEBIG/STONESML/STONSML request style 1 (BOLD). STATES/STATES2 explicitly prefer BAM. A TTF candidate existing for STATES2 does **not** imply the engine loaded it.

The committed [metric receipt](evidence/phase1-font-metrics-bound.json) records the exact KEY, resource byte hashes, candidate archive, table and FreeType DLL hashes/version. It calls FreeType with the engine's Unicode charmap, `FT_LOAD_DEFAULT | FT_LOAD_TARGET_MONO`, then `FT_RENDER_MODE_NORMAL`. It cross-checks the glyph slot's 26.6 advance against `FT_Get_Advance`'s 16.16 result for every present sampled glyph, measures bitmap bearings, kerning, actual y_ppem and the engine's baseline/line-height formula. The adapter is restricted to this Windows ABI and uncompressed KEY/BIFF fixture; it is not a replacement provider resolver.

```powershell
& 'C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe' -B redux/tools/phase1/font_metrics.py --game C:/BGRedux/phase0-local/bg2ee-clean --fonts-table gemrb/unhardcoded/bg2ee/fonts.2da --freetype C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/libfreetype-6.dll --runtime-fonts C:/BGRedux/phase0-local/results/20261021T011818Z-gui-stock-verified-fe7b575f/gui-save/fonts.json --output <new-receipt-path>
```

The independent prediction matches **all seven** historical runtime TTF roles: baseline, line height, `Strength Armor Class 123` width, and all five observed glyph sizes/positions. The historical receipt itself is hash-bound. This is a strong numeric fingerprint of the same candidate metrics, but the old observer did not expose actual resource stream provenance. `actual_engine_provider_observed=false` and each comparison's `actual_provider_proven=false` are intentional. A source table and matching pixels cannot establish the selected provider's path. Fresh runtime provenance remains to collect.

## Actual font roles and measured losses

The inspected private candidates reside in `data/Patch2.bif`. Provider precedence may select a different loose/resource provider, so these are candidate identities until the fresh binding below.

| Role | Candidate family | Baseline / line height | Current predicted sample width / hinted advance |
|---|---|---:|---:|
| NORMAL | R PostAntiqua Roman | 11 / 13 | 147 / 151 |
| FLOATTXT | Tahoma | 14 / 16 | 159 / 180 |
| REALMS | Sherwood | 13 / 16 | 195 / 202 |
| STONEBIG | Benevento | 13 / 18 | 157 / 162 |
| STONESML | AmericanUncial | 11 / 14 | 202 / 204 |
| TOOLFONT / TOOLTIP | Goudy | 11 / 14 | 155 / 153 |

The sample is `Strength Armor Class 123`. Pen advance and ink bounds are different quantities; these values alone do not determine the original EE's placement or hinting policy. Native numeric roles NUMBER/NUMBER2/NUMBER3, INITIALS, STONSML and STATES were observed as BAM in the historical run. BAM initials can span multiple lines and state fonts are icons. Their metrics must not be replaced with TTF assumptions.

Source trace, verified in this worktree:

- `gemrb/core/Interface.cpp`, `Interface::LoadFonts`: reads requested table values and asks ResourceManager for a FontManager, preferring BAM only for the flag. `gemrb/core/ResourceManager.cpp`, resource descriptor resolution: resource type preference participates in selection; table names alone do not identify the loaded file.
- `gemrb/plugins/TTFImporter/TTFFontManager.cpp`, `Import` / `GetFont`: opens a retained DataStream-backed FreeType face; sets pixel size and computes scaled face ascent/descent. Requested style and background are ignored. A matching family is not evidence that requested BOLD was honored. Original visual reference is needed before deciding whether synthetic bold is appropriate.
- `gemrb/plugins/TTFImporter/TTFFont.cpp`, `GetGlyph`: stores rendered bitmap width/rows and supplies bitmap_left/top in the sprite frame. It never stores horizontal advance. Constructor synthesizes spaces from `LineHeight * .25`, tab four times that; missing glyphs alias the space.
- `gemrb/core/GUI/TextSystem/Font.cpp`, `CreateGlyphForCharSprite`: discards sprite Frame.x, sets glyph x to zero, and derives y from baseline minus bitmap_top. `Glyph` in `Font.h` has no separate advance. `RenderLine`, `StringSizeWidth` and `StringSize` advance by bitmap width. Atlas storage and blitting legitimately need bitmap dimensions; changing all size.w uses would corrupt the atlas.
- `Font::StringSize`: applies kerning when `lineW > 0`, so the first word skips it. `RenderLine`: applies kerning at each word's `i > 0`. This is a separate measurement/drawing inconsistency. The independent NORMAL AV pair has -64/64 = -1 px kerning. From the inspected algorithm, bitmap widths 13+12 yield measured width 25 versus drawing pen movement 24; FreeType's advances 12+11 with kerning yield 22. These 25/24 values are **source-derived predictions**, pending an actual native `StringSize("AV")` / pen observation.
- `gemrb/plugins/BAMImporter/BAMFontManager.cpp`: obtains line height/baseline from magic cycles; numeric roles map frames to digits, with special state-icon origins. Existing frame/alias semantics are a compatibility constraint.

Specific independently measured examples at the requested 14 px:

| NORMAL glyph | Ink width | Hinted advance | bitmap_left |
|---|---:|---:|---:|
| A | 13 | 12 | -1 |
| a | 6 | 7 | 0 |
| g | 7 | 6 | 0 |
| j | 4 | 3 | -1 |
| W | 16 | 15 | 0 |
| space | 0 | 4 | 0 |

Current NORMAL synthetic space is 3 px. TOOLFONT g ink width is 8 but advance is 6, left bearing -1. A bare bitmap-width replacement cannot retain these independent quantities. Negative bearings/descenders are valid; a glyph extending beyond a nominal line box is not by itself proof of erroneous metrics.

FreeType's primary definitions distinguish bitmap pixel dimensions/bearings from hinted advances, and define DEFAULT kerning as grid-fitted: [glyph retrieval](https://freetype.org/freetype2/docs/reference/ft2-glyph_retrieval.html), [advance units](https://freetype.org/freetype2/docs/reference/ft2-quick_advance.html), [hinted metric rounding](https://freetype.org/freetype2/docs/reference/ft2-sizing_and_scaling.html). This audit uses these API contracts, not a third-party screenshot approximation.

## Narrow proposed correction, after preserved before-images

No behavioral font patch is included in this audit. Separate ink extent/bearing from horizontal advance in `Glyph`; default new advance to existing width and preserve the existing zero x origin for all BAM construction and aliases. Add an explicit TTF construction path supplying the measured signed bitmap_left and hinted advance, including blank spaces. Keep atlas packing/pixel pitch/ink drawing dimensions based on bitmap size. Empty ink must still advance the pen; do not lose spaces through the current null-pixels early-continue path. Keep encoding/zerospace policy explicit, with zerospace translations retaining their intentional special spacing.

Update pen movement, measurement, forced-break counts and whitespace accumulation together, using signed intermediates for kerning/zero-advance glyphs. Fix first-word kerning with the same preceding-character rule used for drawing; do not apply kerning across a hard line break. Record both pen width and ink union where alignment/clipping depends on them. Preserve the baseline formula for the first patch; there is no independent evidence here that changing it or swapping faces is correct. Synthetic styles need a distinct original-reference decision.

Review the canvas path before enabling negative horizontal bearings: `RenderLine` currently passes an already position-adjusted point to `BlitGlyphToCanvas`, which adds glyph.pos again. Direct atlas drawing and canvas drawing therefore need a test of the same nonzero-position glyph; this is a source-indicated placement risk, not a newly captured visual failure. Atlas insertion intentionally subtracts x before that helper and must retain its separate packing behavior. Do not repair bearings by padding every glyph bitmap or moving atlas slices.

Meaningful native tests for those demonstrated defects, once implemented:

1. Unequal advance/bitmap/negative bearing (actual NORMAL A/a/g/j/W), zero-ink space and repeated `gggg`/`WWW`: measured pen equals the independent hinted advance plus kerning, while ink begins at pen+bearing. Native render/canvas endpoint and measurement must agree; API-only `GetGlyph` assertions are insufficient.
2. NORMAL `AV` and `To` as first word, after whitespace, after newline and at exact wrap thresholds: identical within-line kerning and correct returned character count/line count; no unsigned underflow with zero advance.
3. Synthetic BAM fixture with nonzero frame x plus real numeric/initial/state aliases: before/after widths, baseline, positions and raster remain identical. Do not change numeric fallback behavior under the guise of TTF fidelity.
4. Original/candidate matched captures at 1024×768 and a second supported size: role/face/size provenance, pen/baseline/ink bounds, live label/value clipping, button/cursor spacing and text reachability. Preserve failures and compare original artistic appearance; metric correctness is not an EE screenshot equivalence claim.

No mock test is claimed to validate an unimplemented metric correction. The read-only adapter run succeeded and checked both independent FreeType advance APIs plus the seven historical fingerprints. Existing 39 UI/menu/hotkey Python tests concern other changes, not typography acceptance.

## Fresh external observer contract

Existing `redux/tools/phase0/native/gui_probe.cpp::FontsJSON` gives role/runtime C++ type, line height, baseline, five glyph sizes/positions and one sample width. These fields cannot certify provider/face/size or detect fallback glyphs. Extend the external menu observer and narrowly expose immutable diagnostic data from loaded fonts:

| Field | Authoritative collection point / assertion |
|---|---|
| requested role, resource, px, style, background, preferBAM; loaded fonts-table path/hash | Actual `Interface::LoadFonts` request and selected table stream, not a later source-file guess |
| selected provider, stream originalfile/filename, resource length/hash | Imported stream at `TTFFontManager::Import` or BAM import; KEY sets resref filename, SlicedStream preserves originalfile. Hash the **resource slice**, not only its containing BIFF. If archive provenance is compressed/cache-derived, preserve both origins |
| actual importer, family, face style/flags, actual x/y_ppem, face index, applied style, FreeType version/DLL hash | Retained actual FT_Face and size, not requested table values; BAM explicitly reports embedded metrics and no FT face |
| codepoint, resolved glyph index or explicit alias/fallback, ink size, left/top, advance, kerning pair and signed pen movement | Actual loaded font; `GetGlyph` returning something is not glyph availability. Numeric BAM letters must not be accepted merely because a fallback digit rendered |
| menu/window/control ID, font role, text/hash, value, actual content rectangle, clip rectangle, measured lines/characters and ink union, scroll/page state | Visible controls after ordinary callback completion; assert required text remains reachable and full single-line labels fit the actual clip rectangle. Overflow must name the control and string |
| screenshot hash/dimensions, run nonce, engine/module/table/fixture hashes, selected actor and observer before/after | Same normal-loop capture as controls; no cross-run mixing. Readiness, callback entry, visible completion and pixel review are distinct observations |

For Stats, validate all six categories and every necessary page with distinct heading/main attributes excluded from the secondary panel, and report the remaining pagination/scroll requirement rather than calling a bounded page budget a no-scroll proof. For Options and hotkeys, observe the live game-font roles, actual entered text/cursor/focus and full button labels. Applicable standard menus and context-gated menus remain separate coverage families. These diagnostics must not mutate game state or install a generic fallback font.

## Implemented read-only import seam (separate follow-up)

`Font::ImportProvenance` now owns copies of the actual imported stream's `originalfile`, `filename` and resource length. TTF and BAM managers copy them before stream ownership transfers or import-time decompression. `GetFont` records the actual request. TTF additionally snapshots the actual retained face's family, face style, face index, intrinsic style flags and x/y ppem after the existing size-selection call. BAM explicitly reports no FreeType face metrics and zero ppem; its existing embedded baseline/line height and glyph geometry remain untouched. Requested style and intrinsic face style are separate; synthesized style remains zero, reflecting the existing lack of synthesis. The getter performs no stream reads/seeks, glyph generation, FT size changes or game operations. All strings are owned copies, with no borrowed stream/face pointers exposed after importer destruction.

External `FontsJSON` emits `bg-redux-fonts/2` with `import_provenance` for each actual loaded role. A manually constructed font or uninstrumented importer leaves empty/unknown fields; it does not guess a provider. The seam adds no resource-byte hash and emits `resource_hash_observed=false`. This changes the Font class layout and requires a coherent core/plugin/external-host rebuild; mixing an old binary with these headers is unsupported. No compiler or native test host was run for this follow-up.

`font_metrics.py --provenance-only` additionally records both TTF and BAM candidate origins, byte lengths/hashes and actual x/y ppem in a compact expected receipt. [The private candidate identity receipt](evidence/phase1-font-import-candidates.json) preserves this metadata without publishing font bytes. The earlier full numeric receipt remains unchanged. To generate a fresh compact receipt, use the earlier command with `--provenance-only`, a new output path and no historical runtime argument.

After coordinator captures a new schema-2 runtime `fonts.json`, run:

```powershell
& 'C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe' -B redux/tools/phase1/font_provenance.py --fonts <fresh-run/fonts.json> --expected redux/docs/testing/evidence/phase1-font-import-candidates.json --output <new-validation-receipt.json>
```

The validator requires every expected role exactly once, a loaded instrumented font, known importer, the full actual absolute source path (not just a basename), resource name/length, actual requested values and actual face identity/size. It rejects an available preferred candidate being bypassed, and treats BAM as embedded glyph data rather than a 14-px TTF. It rejects missing/unknown provenance and unsupported resource-hash claims. The result certifies **import metadata binding** only: resource-byte identity, applied requested-style fidelity and original EE pixels remain explicitly unproven. Loaded resource hashing and selected fonts-table stream provenance remain separate future observer fields from the contract above.

**12 targeted adapter tests passed**: unknown/absent/old-schema provenance; generic fallback with the expected role; wrong provider with identical archive basename; missing/duplicate/extra role; wrong resource/length; requested size with a different actual size; alternate face/index/style; preferred importer bypass; BAM preserving embedded metrics; unsupported hash claims; and successful metadata binding retaining all proof limitations. A test removes every critical observed field individually to ensure a missing value cannot inherit a convenient default. These tests use independent evidence inputs, and do not claim native ABI, runtime-import or rendered validation. Coordinator compilation and a fresh same-run font receipt are pending.

The first native schema-2 receipt, `20261022T010029Z-menu-run-bf0932e2/1024x768/fonts.json`, supplies actual face/size metadata but exposes a path representation detail: KEY-derived archive `original_file` strings retain a single terminal NUL. `KEYImporter::Open` resizes and reads `ASCIIZLen` bytes, including the terminator; its language-BIF lookup explicitly comments that BIF names have a trailing NUL. BIF/archive stream opening retains the supplied path, and `SlicedStream` copies originalfile. The diagnostic seam preserves that raw string rather than silently editing it.

External validation now permits **only one terminal NUL on a `.bif` archive source matching the expected archive origin**, records that representation explicitly, and compares the remaining path through the same strict original/wrapper binding. It does not split arbitrary strings at NUL or accept a new provider. Embedded NUL, multiple NUL, suffix data after NUL, a nonarchive terminated path and a wrong provider remain rejected; generic filesystem identity normalization rejects NUL outright. `--private-game <stage/private-game-preparation.json>` validates current source inventory/root hashes, wrapper link targets and copied inputs before mapping the actual private GamePath to the trusted source candidate. The output pins that preparation receipt hash; raw `fonts.json` remains unchanged. **15 provenance tests pass** including this representation handling and wrapper mapping. This is metadata/provider binding, with resource-byte identity, style and pixel-equivalence proof limits retained.
