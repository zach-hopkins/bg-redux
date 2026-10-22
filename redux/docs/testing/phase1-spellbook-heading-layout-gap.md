# Spellbook heading layout and readability gap

The current candidate's populated priest book passes actor/slot checks but its
“Memorized” heading is faint and detached from the memorized row. Coordinator
inspection of `20261022T064911Z-guarded-textarea-menu-run-eba67ffa` capture 25 at
1024×768 confirms this visible gap. Existing menu passes do not accept its
readability or exact typeface. The earlier [caster audit](phase1-caster-menu-native-audit.md)
already records the faint heading.

Read-only packaged-resource inspection on October 22 UTC found:

| Source | Memorized heading contract |
| --- | --- |
| GUIPR.CHU window 2, control `0x10000033` | Relative rectangle `(295,490,275,30)`, strref 11944, TOOLFONT, pale foreground bytes `(255,230,130,0)` |
| GUIMG.CHU window 2, same control | Relative rectangle `(295,489,275,33)`, same strref/font/colors |
| Shipped `ui.menu`, lines 8835–8841 | Priest page-info label rectangle `(272,598,276,40)`, `priestPageInfo()` and style `label` |
| Shipped `bgee.lua`, lines 2895–2903 | That style uses STONESML, point 12, centered alignment, color `B` |
| Shipped `bgee.lua`, line 2825 | Color `B` is `FFCECECE` |

`GUIPR.InitPriestWindow` moves the memorized buttons to relative y=644 for BG2EE,
but does not adapt this heading. `CHUImporter.GetLabel` imports its font/color,
forcing alpha to 255. The observed native control remains at the CHU rectangle.
This supports an incomplete EE screen-assembly explanation; it does not prove a
font rasterizer defect. The wizard heading has matching obsolete metadata, but
its visual impact still needs separate inspection.

Private reproducible metadata is retained at
`phase1-local/results/20261022T074600Z-spellbook-heading-source/report.json`
(SHA-256 `8d43f0e7215b3abce54bf729cbe7292101eb5511b3ecef1e5fe55d90078a445b`),
with `phase1-local/probe-spellbook-heading-20261022.py`. It hashes the native
capture/UI receipt, GUIPR/GUIMG CHUs, UI menu, styling resource and inspected
source. CHUs resolve to GUICHUI.bif; styling resolves to Patch2.bif. This reader
does not establish complete runtime provider precedence or render the original.

No production correction is applied by this investigation. Before changing the
adapter, compare the native and original panel coordinate systems, heading and
memorized-row backgrounds, and live page-info behavior. Retain readable game
font roles, label semantics and eligible-caster selection; verify both books at
both existing resolutions with captures and native operations. A global font or
palette change is not justified by this bounded finding. Original parity,
pointer input, memorization operations and complete menu fidelity remain open.

The subsequent [original runtime reference](phase1-original-spellbook-reference.md)
confirms the wizard heading/count on the lower dark strip and provides a dimmed
ineligible priest layout reference. It also records original no-confirmation
wizard removal and the actual re-prepared spell's saved ready flag. A normal
BG2EE heading correction is being prepared separately; Classic and spontaneous
caster behavior must remain unchanged.
