# Wizard information → Erase identity diagnostic

Status: **native wrong-spell Erase reproduced; narrow production correction applied, native AFTER validation pending**. Original Erase parity remains unmeasured. Historical operation/menu results retain their prior scope.

## Source reason and exact acceptance

Before correction, `GUIMG.UpdateMageWindow` sorted known entries by localized name and assigned each icon's value to its original known index, but its right-press info closure stored the displayed position. Info window 3's Erase control 6 passed that position through confirmation window 101/control 0 into `OnMageRemoveSpell` and `GemRB.RemoveSpell(pc, type, level, index)`. The controlled native run below confirms wrong deletion, separate from the already tested Memorize callback. Commit `3f5cad097` changes only the info metadata to carry the original known index, matching the icon value.

## Executed BEFORE and correction

Stock result `20261022T103257Z-spellbook-erase-ee-direct-05d986b6` passes intended SPWI213 removal, GUI save and fresh reload. Its result SHA256 is `28ca5af36013ddb91e0f635788a3bd8ea480bb3db7925bbc9f2411e22855947e`.

Controlled result `20261022T103610Z-spellbook-erase-name-control-ee-direct-2899b4c1` **fails** intended identity (result SHA256 `4b2a1a15ce17b5b188f118b5664c6ea7ccdda513396a308e3495d5b94e2af010`). The information window shows SPWI213, original index 2/displayed index 0. Confirming Erase actually removes SPWI211 from known entries and leaves SPWI213 plus its memorized copy intact. The ordinary GUI save is preserved in `operate/diagnostic-frozen-save` and independently decoded before acceptance fails. No reload is launched after that failure. Candidate, protected baseline and input preservation guards pass.

The resource-free regression executes the actual known-row rendering loop in four display orders: BEFORE has eleven failing subtests; AFTER all four tests pass. The full external tooling suite passes 447 tests, with source-bound receipt `phase1-known-info-tooling-1792665863856746800/result.json`. Native AFTER must still establish callback, save and reload correctness; fast tests alone do not close this defect.

`GUIScript.cpp`'s indexed `RemoveSpell` first resolves `GetKnownSpell(type, level, index)`. `Spellbook::RemoveSpell(const CREKnownSpell*)` erases that single known entry and calls `RemoveMemorization` for **all copies of that resref on that same page**, preserving the order and flags of unrelated memorized entries, then clears cached spell information. Therefore correct acceptance requires deleting the intended known SPWI213 and every same-page SPWI213 memorization. A count decrease, or deleting a different known spell with matching counts, is insufficient. Slot capacities, other pages/actors and collected world fields must remain unchanged, allowing ordinary selection changes only after natural startup readiness.

## External route and evidence

New `spellbook_erase_journey.py`, `SpellbookEraseRuntime.py`, `SpellbookEraseStart.py`, native host and independent validation module reuse the existing read-only serializers, private wrapper, provider reader, four-party wire decoder and source-bound build receipt checks. Existing helper and historical closure files are not edited. These canonical dependency files must be present in the integrated source checkout; a worker checkout lacking recent root-only tooling is not a runnable installation.

Each invocation uses the exact immutable Minsc parent `20261022T075243Z-minsc-recruitment-072650e1` (result, manifest, GAM and SAV pinned by the adapter), a new owned profile and fresh 32-hex nonce. It loads through the registered GUILOAD callback with factual null pre-game snapshots, waits for natural stock startup plus four idle samples, pauses, then uses actual registered portrait/toolbar/level callbacks. It right-presses the known SPWI213 icon, checks the shown info name and full description against selected SPL/TLK inputs, dispatches Erase → Cancel without mutation, then Erase → Confirm. RightPress uses the public packed `Control::Click`, `GEM_MB_MENU`, single-click action key matching `GUIClasses.OnRightPress`; it does not call the production Python function directly or simulate OS pointer input.

The stock and `spellname-permutation` modes are separate invocations. The latter reuses the existing **exact four SPL SpellName-field-only exchange**; TLK and every other byte remain pinned. Actual target original index must be 2; the declared control additionally requires displayed index 0. Imoen's other known names, the exact UI tooltip/value/control and modal identity are observed, not inferred from a requested index. This control changes presentation only and makes no original parity claim.

The normal GUI save chain executes even when deletion proves wrong: the native host completes the actual callback sequence without deciding that wrong deletion is acceptable. The external adapter freezes the produced save and decodes its actual wire state **before** strict intended-resref acceptance. A wrong deletion remains failed with diagnostic frozen save, callbacks, before/after snapshots, screenshots, providers, process log and manifests retained. Only a correctly accepted operation proceeds to a second owned fresh process loading the frozen save; it navigates/observes the same wizard page without any Erase or save callback. No rest, cast, grants, gameplay setters, cheats or callback monkeypatching are used. Reload is deliberately not attempted after failed intended-resref validation.

Build/run guards freeze the imported external Python closure, compiled native/helper sources, production GUI/core/importer/policy sources, build receipt/support, compiler, candidate source/binaries, parent proof and selected resource bytes/provider hashes. The private wrapper and copied input/override/config/driver/frozen outputs are checked again on completion/failure; protected Phase 0 source/binaries/fixture are independently checked. Runtime provider path/bytes and source module identity remain strict. Existing Color/loot/native journeys are not modified.

## Coordinator commands (not executed by this worker)

Use the coordinator's configured Python executable, with the integrated source checkout as working directory. These example paths select the coherent heading/policy candidate; build receipt validation rejects a stale source/build combination rather than substituting an older engine.

```powershell
$src = 'C:/BGRedux/phase1-local/engine'
$build = 'C:/BGRedux/phase1-local/builds/20261022T093226Z-candidate-5a60a03d'
$hostOut = 'C:/BGRedux/phase1-local/weapon-query-probes/heading-erase-1'
python -B redux/tools/phase1/spellbook_erase_journey.py build --project-root C:/BGRedux --engine-source-root $src --engine-build-root $build --output-dir $hostOut
python -B redux/tools/phase1/spellbook_erase_journey.py run --project-root C:/BGRedux --engine-source-root $src --engine-build-root $build --host-build "$hostOut/build.json" --results-root C:/BGRedux/phase1-local/results --confirmation-policy ee-direct --presentation-control stock
python -B redux/tools/phase1/spellbook_erase_journey.py run --project-root C:/BGRedux --engine-source-root $src --engine-build-root $build --host-build "$hostOut/build.json" --results-root C:/BGRedux/phase1-local/results --confirmation-policy ee-direct --presentation-control spellname-permutation
python -B -m unittest discover -s redux/tools/phase1/tests -p test_spellbook_erase_journey.py
```

Source-only negative tests cover wrong known ref/index, duplicate target, retained target memorization, changed unrelated ready flags/capacity, reversed wire ordering, wrong actor/world/journal changes, mutation during Cancel, displayed/original index confusion, wrong action/control/tooltip, stale nonce, truncated plan and wrong confirmation route. They have not been executed here; compile/API and actual native outcomes remain pending coordinator validation. Screenshots are retained for QA, not an automatic pixel fidelity oracle; exact original Erase behavior, physical pointer routing, hidden RNG and complete spontaneous/Classic book behavior remain unmeasured.

## Bounded gender-token correction (source-only follow-up)

The first stock attempt `20261022T102210Z-spellbook-erase-ee-direct-1bd64447` remains **failed**, including its preserved diagnostic save. The coordinator reports an otherwise correctly named Stinking Cloud information modal rejected because its 719-character frozen raw description contains `<PRO_HISHER>`, whereas the actual 710-character description expands that token to `his`. This is a validator limitation, not evidence that the information modal selected another spell. No old receipt is relabeled by this correction, and subsequent Erase identity acceptance remains strict.

The new contract supports only the exact `<PRO_HISHER>` token and exact `gender.2da` row `PRO_HISHER 0 27486 27487`. `TLKImporter` loads that table into its token map; `GetActorFromSlot(0)` selects `GetPC(0,false)` (protagonist), independently of the selected Imoen. `GenderStrRef` uses modified `IE_SEX` stat 35: female 2 selects TLK 27487; otherwise male 27486. This diagnostic deliberately accepts only male 1/female 2 and rejects other sex states, missing/duplicate actors, conflicting party/area observations, unsupported/nested/malformed tokens, wrong slot/refs and missing word entries. It does not implement generic token evaluation, stripping or English substitution.

Build/resource guards now freeze the selected bg2ee fallback gender table, TLK words at both refs, and the importer/stat/table source. Higher-priority engine/game shadows are rejected; every fresh native process independently freezes `GetResourceStream("gender", IE_2DA_CLASS_ID)` path and complete bytes, which must match the selected provider. The runtime table row is parsed independently again for description validation. Frozen TLK words are recomputed against the pinned full TLK file on source/resource checks. No internal importer token-map sampling is claimed: the source-bound importer, unchanged provider configuration, actual resource stream and exact observed control description jointly bind this narrow resolution. Successful observations record protagonist runtime ID/name/sex, selected word ref/text and occurrence count.

Five additional test sources cover both supported sexes, unsupported tokens, wrong/duplicate table rows, wrong TLK keys/nested words and wrong/incoherent protagonist sex. No tests, builds or native processes were executed for this follow-up. A fresh external host build is required; use a new output path such as `heading-erase-2` with the same explicit source/coherent engine receipt arguments above.


## First coordinator execution and text-contract correction

The initial external build and 14 focused methods passed. Stock native run
`20261022T102210Z-spellbook-erase-ee-direct-1bd64447` completed the callback/save
route (PID 3544, exit 0, 60.845 seconds), retaining its diagnostic frozen output,
but its strict outer validator failed on a description representation mismatch.
The frozen raw TLK text contains `<PRO_HISHER>`; normal engine resolution displays
`his`. The name and other description bytes match. This failed result remains
failed, without a fresh reload claim, and all preservation guards pass.

The separate adapter correction binds exactly that token to the captured
protagonist sex, exact gender table row/provider, frozen TLK pronoun refs and
runtime resource stream. It rejects unsupported substitutions rather than
stripping tokens. All 19 focused tests pass after integration; a fresh external
build/run is required. No production source or binaries were changed for this
adapter correction. The broader suite previously passed 438 tests before the
five additional token tests; a new total must be measured separately.


External `erase-before-2` stopped before compilation because its source manifest
named nonexistent `core/TableMgr.cpp`; the failure and preservation receipt are
retained. The manifest now pins the actual `core/TableMgr.h` and
`plugins/2DAImporter/2DAImporter.cpp`. External `erase-before-3` builds successfully
with all candidate/Phase0 guards; fresh stock execution is separate evidence.
