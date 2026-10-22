# Wizard sorted known-row identity regression test

`test_spellbook_known_info_index.py` is a resource-free CI regression for the measured native Erase identity defect. It extracts and executes the **actual** `UpdateMageWindow` known-row rendering loop containing the info metadata assignment. The extraction selects structure, not the assignment's expected expression, and fails closed if the production loop cannot be identified uniquely.

Fake controls capture real loop calls and the real right-press callback closure arguments. Identity, reversed, original-index-2-first and rotated display orders retain fixed original storage indices independently of displayed order. For each row, the test invokes the captured callback and requires the info spell's resref/`CurrentIndex` and left button value to agree with that independently fixed identity. It also checks icon, tooltip and callback role. The test does not rewrite or monkeypatch production callbacks, inspect a source text line for the fix, reproduce a new indexing helper, or import a native engine.

The native controlled BEFORE result `20261022T103610Z-spellbook-erase-name-control-ee-direct-2899b4c1/result.json` (SHA256 `4b2a1a15ce17b5b188f118b5664c6ea7ccdda513396a308e3495d5b94e2af010`) remains failed: the coordinator reports intended SPWI213 at original index 2/displayed index 0 but actual deletion of SPWI211, with SPWI213 and its memorized entries retained in the frozen wrong save. This fast test covers the GUI metadata dataflow responsible for that identity confusion; it does not replace the strict native callback/delta/save/reload diagnostic or establish original Erase parity.

Worker delivery is **test source only, unexecuted**. Coordinator command from the integrated checkout:

```powershell
python -B -m unittest discover -s redux/tools/phase1/tests -p test_spellbook_known_info_index.py
```

No production, helper, engine binary or prior result files are changed in this commit. The separate coordinator production correction and fresh source-bound engine build/native validation own the runtime outcome.
