# External native heading validation

Status: **45 focused Python tests pass; external build and native run pending**. This adapter validates the [ordinary BG2EE heading repair](phase1-ee-spellbook-heading-repair.md), separately from that production commit and the original confirmation-policy difference. Historical menu receipts remain unchanged and retain the validator/source identities with which they were produced.

`MenuRuntime.inspect_spellbook` now records localized strref 11944, the actual allocated entry count including spent spells, bonus-aware capacity, current module level, current SPELLLEVEL token and localized displayed-level text. The native host already captures the independently serialized actor spellbook pages and actual visible label text/relative rectangles. The validator checks:

- Selected actor/name and level/type select exactly one native world page; allocated count equals the complete native memorized-entry list, and capacity equals `slots_with_bonus`.
- Actual heading text equals the localized prefix and those live counts. The displayed level matches the current level token and actual native level-label text.
- The visible label has relative rectangle `[295,598,275,40]`, retaining the measured CHU x/width while moving into the dark strip. It fits inside the actual enabled window and ends before all prepared slots at y644; prepared controls also remain inside that window.
- Existing known/memorized slot, tooltip, actor-selection, callback/nonce, capture, menu coverage and collected-world preservation checks remain in force.

New `--require-ordinary-spellbooks` requires both ordinary wizard and eligible priest contracts. A context-gated priest screen or spontaneous book cannot satisfy this acceptance mode. Without the flag, ordinary menu context gating is retained and the returned `ordinary_spellbook_heading_coverage_complete` field remains false if either ordinary book was not observed. The four-party frozen Minsc checkpoint contains Imoen and Jaheira for the intended two-book route. No cast, rest or memorization operation is added by this menu adapter.

Per-label font, color and alignment are **not observed**: Label keeps those members private without public getters. No new engine seam, private-memory inspection or inferred pixel oracle is added. The receipt explicitly reports that limitation. Existing `fonts.json` provider/face/size/advance evidence must still be validated separately with the pinned font-provenance workflow; loaded STONESML role presence does not prove that a particular label uses it. Readability, actual gray foreground, clipping appearance and typography need coordinator screenshot QA after the coherent build.

Source identities now explicitly include the menu validator itself, runtime/startup/native serializers and private-game helper, plus GUIMG/GUIPR, EESpellbookHeading, Spellbook, GameCheck and GUIDefines from the selected engine source root. Both build and run freeze those bytes and verify current/frozen copies at completion. Complete candidate/transitive engine protection remains the coordinator's source-bound build/inventory guard; this explicit input list is not advertised as an inventory of every imported engine module.

Fourteen new test methods bring the focused menu file to 45 methods. Negative cases cover stale or forged counts despite matching label text, missing/duplicate/wrong-type pages, wrong displayed level/token, hidden/missing/duplicate headings, obsolete/overlapping/clipped geometry, disabled/missing windows, context-gated priest acceptance and invented per-label style claims. Collector tests distinguish allocated entries from ready charges, and source-copy tests reject a missing helper and detect changed current/frozen bytes. All 45 pass in 2.684s with Python `-B`; these unit results are not native pass evidence. The first attempt retained one existing hotkey-nonce test error from a stale worker dependency; syncing the already-integrated root caller resolved it. Both outcomes and source hashes are retained at `C:/BGRedux/phase1-local/results/20261022T094705Z-heading-menu-focused-1bca41a0/result.json`.

## Coordinator commands

Use the integrated tool, a successfully completed coherent candidate build and the usual outer preservation guards. The existing CLI default second resolution remains 1280×960; pass the requested 1280×768 explicitly. No command below was executed by the worker.

```powershell
& 'C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe' -B `
  'C:\BGRedux\phase1-local\engine\redux\tools\phase1\menu_harness.py' build `
  --source 'C:\BGRedux\phase1-local\engine' `
  --build 'C:\BGRedux\phase1-local\builds\20261022T093226Z-candidate-5a60a03d' `
  --prefix 'C:\BGRedux\phase0-local\toolchain\msys64\ucrt64' `
  --output-root 'C:\BGRedux\phase1-local\results' --timeout 120
```

Bind `$menuBuildReceipt` to that exact newly completed external build's `result.json`; verify its passed process, DLL/source pins and binary hash before taking its `binary` field. Do not select an unrelated older host by recency alone.

```powershell
$menuProbe = (Get-Content -LiteralPath $menuBuildReceipt -Raw | ConvertFrom-Json).binary
& 'C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe' -B `
  'C:\BGRedux\phase1-local\engine\redux\tools\phase1\menu_harness.py' run `
  --source 'C:\BGRedux\phase1-local\engine' `
  --build 'C:\BGRedux\phase1-local\builds\20261022T093226Z-candidate-5a60a03d' `
  --prefix 'C:\BGRedux\phase0-local\toolchain\msys64\ucrt64' `
  --output-root 'C:\BGRedux\phase1-local\results' --probe $menuProbe `
  --fixture 'C:\BGRedux\phase1-local\results\20261022T075243Z-minsc-recruitment-072650e1\recruit\frozen-save' `
  --game 'C:\BGRedux\phase0-local\bg2ee-clean' `
  --resolutions '1024x768,1280x768' --require-ordinary-spellbooks --timeout 650
```

Acceptance needs both terminal stages, required-both-books coverage true, unchanged collected worlds and all outer source/binary/fixture/private-root guards. Retain any failed receipts and all raw captures. No complete menu, Shaman/Sorcerer layout, original parity, OS pointer or hidden RNG claim follows from these heading assertions.
