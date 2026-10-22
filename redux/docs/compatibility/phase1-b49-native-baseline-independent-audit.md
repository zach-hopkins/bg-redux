# b49 native baseline: independent residual disposition

The fresh LAB baseline executed successfully, with all **44 native assertions passed**, while compatibility remains **`differences`**. This audit separately dispositions the changed residual set. It does not change the raw `unreviewed-differences` comparator receipts, normalize additional fields, or certify complete save fidelity.

Run: `20261022T072341Z-b49-native-baseline-b6faf631`; result SHA256 `a9b5abb83ecfce153f58063ce5c63284fe58b02368e85c0b3b84963829048ee7`. Build: `20261022T063419Z-candidate-24f35a4e`, source commit `b49d68b09bd4b41857f69cc4b06d5e86333820ce`, core DLL SHA256 `051c3ea9f1e2d582e62f3b8dad61d46c6fab04a093cd4bd9c8b865c8a920a26b`. Reference runs are `20261022T021035Z-phase1-9aa-guarded-vanilla-60ea184f` and `20261022T021057Z-phase1-9aa-guarded-gui-c6ac9bbf`, core `79650612926d96a8748320bcf3d0f8f265f7d20747448a30a5ec8918b472ebb9`.

## Exact comparison

| Evidence | Reference | Fresh b49 | Independent disposition |
|---|---:|---:|---|
| Vanilla wire oracle residuals | 36 | 36 | Entire ordered difference arrays equal; no added or changed wire residual. |
| Vanilla reload-1 semantic residuals | 2 | 0 | Only prior base/modified leather-color rows for the same Shadow Thief are absent. |
| Vanilla reload-2 semantic residuals | 2 | 0 | Same two paths; fresh snapshot chain stays equal. |
| Repeat-import semantic residuals | 24 | 24 | Different sampled values/paths; every reported path independently bound to a source actor's stock random palette selector, rather than accepted only by a stat-number pattern. |
| GUI legacy semantic residuals | 57 | 53 | Exact subset: four specified color rows removed, zero additions or changed retained rows. |
| GUI full persistence residuals | 453 | 449 | The same exact four rows removed, zero additions or changed retained rows. |

The GUI rows removed from both arrays are `/current_area_actors/7/{base_stats,modified_stats}/212` and `/current_area_actors/31/{base_stats,modified_stats}/210`. Semantic actor ordering follows script name, area, position and name; it is not the raw area actor-record index.

## Bounded color provenance

The independent reader inflated the protected SAV's `AR0602.are`, matched actors by script and exact coordinates, and decoded their CRE palette bytes. It independently read the selected stock KEY/BIF `RANDCOLR` resource and checked membership in the applicable selector columns. No licensed payload is published here.

| Actor and source selector | Prior GUI palette chain | Fresh GUI palette chain |
|---|---|---|
| `CSThief1`, Shadow Thief, AR0602 `[3945,2821]`, leather/stat212, source selector209 | 237 → 170 | 93 → 93 |
| `None`, Goblin, AR0602 `[3189,1478]`, major/stat210, source selector242 | 222 → 79 | 64 → 64 |

The prior vanilla Shadow Thief leather chain is **227 → 218 → 2**; the fresh chain is **91 → 91 → 91**. Initial values belong to the actor's original selector column. When an imported byte is itself a high selector, the observed reload value belongs to that byte's selector column; low bytes remain unchanged in these observations. Each base value repeats its palette byte across the dword. The Shadow Thief's modified color retains its separate effect-adjusted low bytes; those fields were checked independently rather than assumed identical to base stats.

This matches the pinned importer mechanism: [`CREImporter.cpp`](../../../gemrb/plugins/CREImporter/CREImporter.cpp) `SetupColor` at line761 loads `randcolr`, palette import at849–857 resolves and expands bytes, and serialization at2039–2045 writes the low byte for this format. The stock area SHA256 is `11fe9bce9ecce5d75ef05f6947da9d872b58a868898ba0935307b7ea8c4914b5`; RANDCOLR from clean `data/Default.bif` is `fadbc1a6b61cd3ec06105fc634e796c8a6393f0da326696636f571a0dc9b7a93`. The affected source CRE hashes are `f018f7df59f157d71a960b84e28e6c6b9de81625c2a3ab3494edfd62c700c2e0` and `7db5f8c08f9575ad798384500af6df48dba8f2e9a06350ba53b656c78cfbe38e` respectively.

The earlier original-engine controlled observation **237 → 46 → 46** remains scoped as documented in [the saved NPC color investigation](phase1-saved-npc-color-investigation.md). It does not establish exact stock palette equality, authorize an importer change, or prove that arbitrary color differences are harmless. No RNG-state parity is asserted by this baseline.

## Execution and preservation

Four vanilla native processes exited 0: import 9572, reload 11380, reload 11896 and repeat-import 13844. GUI save 11584 and fresh reload 9920 also exited 0. All six were distinct, bounded processes without timeout or cleanup intervention. The scenario wrappers exited 1 because their compatibility verdicts remain `differences`; that exit was retained. Vanilla contributed 24 assertions; GUI save/reload contributed 13+7. The GUI created save's five files still match its recorded hashes and reload reports the created save unchanged.

Independent current/frozen hash checks covered 3508 build sources, 61 build binaries, 5 build-support files, 75 copied runtime inputs, 5 frozen runner/helper/build-receipt inputs, 8 frozen reference inputs, the two compiled GUI probe source pins and 3 GUI helper pins. Both probes' actual executable hashes and DLL provenance match their receipts. Before/after candidate and Phase0 guard JSONs are byte-identical. Current protected Phase0 hashes match 3500 sources, 50 binaries and 6 fixture files; candidate guard maps match 3507 sources and 48 executable/DLL entries, separately from the broader build receipt inventory. The fixture's six files also match the private copy.

The private GamePath receipt reports clean root inventory/hash preservation and unchanged copied immutable inputs, with only the declared `GemRB.log` and `gemrb_path.txt` private-root writes. Linked asset contents were **not fully hashed** by that guard. The independent audit additionally hashed 2032 files across the fresh and reference scenario trees; it does not convert that limited private-game guard into a complete licensed-installation content audit.

## Disposition and retained limits

**Reviewed bounded change:** the changed reload/GUI residual set contains only the specifically identified absent color rows, with no added GUI or wire residual. Their absence is consistent with these fresh low-byte palette samples, rather than evidence of a new color persistence fix. Repeat-import differences remain explicitly limited to independently bound random-selector actors/fields. Retain the 36 wire residuals and 53 legacy/449 full GUI residuals as unresolved compatibility differences under their existing scope.

`baseline_runner.py:197–210` requires exact reload arrays and exact GUI residuals/scopes against the reference; therefore a smaller residual set still produces `unreviewed-differences`. That strict raw outcome is accurate and unchanged. This document supplies a human-reviewed disposition alongside it, without adding a blanket random-color exemption, rewriting historical results, or claiming full menu, campaign, visual, or persistence parity. No engine, helper, test, compiler or native process was run or modified by this audit.

Private reproducible audit: `C:/BGRedux/phase1-local/results/20261022T074317Z-b49-baseline-independent-audit-409352ea/`. `result.json` SHA256 `69686ef1f4166e8fde218119a9f805064cea70117c84ffc52d1881c086acfd59`; `audit.ps1` SHA256 `2a9b83c137532f31bdc3c22dbbe352a61226590d990e23285681b1ed6df4f4b6`; `scenario-artifacts.json` SHA256 `f14a920b65a9bc0a134265ebad0a8fb0e8cad9b08c045e9d52753a59211d9610`. It retains exact removed arrays, all affected palette identities, both repeat-import actor/selector bindings, and the six terminal process identities.

