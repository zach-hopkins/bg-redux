# Wizard sorted known-row identity regression test

`test_spellbook_known_info_index.py` is a resource-free CI regression for the measured native Erase identity defect. Its original version extracted and executed the actual `UpdateMageWindow` known-row loop; those independently recorded BEFORE/AFTER results retain that historical source scope. With the ordinary BG2EE assembly moved into `EESpellbookInformation`, the current four tests execute that actual rendering/binding helper and invoke its real info/action closures through fake controls. The legacy GUIMG loop retains the original-index correction.

Fake controls capture real helper calls and right-press callback closure arguments. Identity, reversed, original-index-2-first and rotated display orders retain fixed original storage indices independently of displayed order. For each row, the test invokes the captured callback and requires the info spell's resref/`CurrentIndex` and left button value to agree with that independently fixed identity; it also dispatches the actual immediate action closure. It checks icon, tooltip and callback role. The test does not rewrite or monkeypatch production callbacks, inspect a source text line for the fix, reproduce a new indexing helper, or import a native engine.

The native controlled BEFORE result `20261022T103610Z-spellbook-erase-name-control-ee-direct-2899b4c1/result.json` (SHA256 `4b2a1a15ce17b5b188f118b5664c6ea7ccdda513396a308e3495d5b94e2af010`) remains failed: the coordinator reports intended SPWI213 at original index 2/displayed index 0 but actual deletion of SPWI211, with SPWI213 and its memorized entries retained in the frozen wrong save. This fast test covers the GUI metadata dataflow responsible for that identity confusion; it does not replace the strict native callback/delta/save/reload diagnostic or establish original Erase parity.

Coordinator execution on October 22: before the production correction, four tests ran with eleven failing subtests across the reordered cases. After commit `3f5cad097`, all four pass. Logs are retained at `phase1-local/results/phase1-known-info-before-20261022.log` and `phase1-known-info-after-20261022.log`. The full source-bound external tooling suite passes **447 tests** in 34.599 seconds; receipt `phase1-local/results/phase1-known-info-tooling-1792665863856746800/result.json` binds unchanged inputs. This is separate from native AFTER validation.

Coordinator command from the integrated checkout:

```powershell
python -B -m unittest discover -s redux/tools/phase1/tests -p test_spellbook_known_info_index.py
```

The original test-only delivery changed no production, helper, engine binary or prior result files. The later ordinary-layout delivery updates this test to exercise its new production helper; its native verification is still separate. Coordinator source-bound builds and actual callback/save runs own the runtime outcome.
