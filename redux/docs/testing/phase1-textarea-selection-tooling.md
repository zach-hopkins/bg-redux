# Reproducible external TextArea selection tooling

`redux/tools/phase1/textarea_selection_journey.py` promotes the validated private v2 preparation into tracked source tooling. Its independent contract module retains the exact fifteen-case map used by the [native correction audit](phase1-textarea-native-correction-audit.md). The old v1/v2 packages, external hosts and BEFORE/AFTER receipts remain unchanged; this promotion creates new receipts and does not retroactively validate its new paths, names or build adapter.

The source consists of the Python journey/validation modules, `native/textarea_selection_probe.cpp`, the existing eleven-case `native/textarea_selection_regression.h`, additive `native/textarea_unnumbered_selection_regression.h`, and `tests/test_textarea_selection_journey.py`. No game assets, frozen binaries or private preparation directory are required in the repository. The coordinator supplies explicit project, source, engine build and external output roots; the tool must be invoked from the declared source checkout.

At build time, canonical inputs are read from the project's `tools/phase0/native/gui_probe.cpp`, `save_probe.cpp`, `tools/phase0/gui/ReduxStart.py`, and the declared source's fixture header. They are frozen with actual imported helper closure, relevant engine source, engine build receipt, compiler/CMake identities and independent validation source. Only the helper's single unused `int main(` declaration is renamed when generating `gui_helpers.cpp`; no global main macro is added. The build compiles only a new external host. Engine source, plugins and binaries are not rebuilt or changed.

Complete current non-redux source and binary inventories must match the successful preserved engine build receipt. Compiled support files must match both source and frozen build-support copies. A different source, stale build, extra plugin (including uppercase DLL extension), changed compiler/helper or altered compiled closure fails. New `bg-redux-textarea-selection-build/1` and `bg-redux-textarea-selection-run/1` schemas distinguish this adapter from historical private receipts.

Each requested case gets a fresh owned process, nonce, stock save copy, private GamePath wrapper, profile, cache and empty override. After ordinary GUI load and paused readiness, the native host executes exactly one fixture between full collected-world and sorted dictionary snapshots; AFTER snapshots are taken after fixture cleanup. The independent Python contract requires exact raw callback trace, final scalar value, event counts and the unnumbered invalidation prefix. Echoed native expectations or `passed:true` cannot replace that contract. Owned terminal receipts use actual `Popen.wait` exit results and the established cleanup field. Pending termination stops the batch; crashes, missing terminal observations, failed contracts and incomplete inventories remain failures.

Each process has a 90-second budget and 120-sample load bound. `--case all` requests exactly fifteen serial processes, with at most 1,350 seconds of child budgets plus preparation/hash work. A named subset can pass only that declared subset; `full_fifteen_executed` remains false. Every run copies its compiled and source closure, rechecks private inputs and source/build guards, and uses a unique result directory. An existing external build output directory is rejected.

Coordinator commands after integration and review, using a source-matching candidate:

```powershell
$py = 'C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe'
$source = 'C:/BGRedux/phase1-local/engine'
$build = 'C:/BGRedux/phase1-local/builds/20261022T063419Z-candidate-24f35a4e'
$tool = "$source/redux/tools/phase1/textarea_selection_journey.py"
$external = 'C:/BGRedux/phase1-local/weapon-query-probes/b49-textarea-promoted-1'
& $py -B -m unittest discover -s "$source/redux/tools/phase1/tests" -p test_textarea_selection_journey.py -v
& $py -B $tool build --project-root C:/BGRedux --source-root $source --build-root $build --output-dir $external --timeout 180
& $py -B $tool run --project-root C:/BGRedux --source-root $source --build-root $build --host-build "$external/build.json" --results-root C:/BGRedux/phase1-local/results --case all
```

The test source preserves eighteen private v2 validator methods and adds four canonical-helper/build-binding methods. They include forged native expectations, duplicate/missing callbacks, invalid final values, stale unnumbered Select, unproven cleanup, partial/wrong inventory, extra plugins, frozen-support drift and wrong build identity.

Coordinator validation on October 22 UTC passes: 22 focused methods and all 346 integrated external Python tests, followed by a successful external host build at `phase1-local/weapon-query-probes/b49-textarea-promoted-1/build.json`. Native run `20261022T073540Z-textarea-selection-807b6682` executes all fifteen requested cases in fifteen distinct owned processes, each exiting zero. Every exact independent callback/value contract and full collected-world/sorted-dictionary comparison passes. Phase 0 source/binaries/fixture, complete candidate build inventories, frozen launch closure and inputs remain preserved. The result SHA-256 is `e8bccca87e8038f689e68cfa94fc89baafbcf7636dd990c5c59501899955cc04`. These are new promoted-tool receipts; historical private package receipts retain their original identities.

This is a synthetic control fixture after ordinary load, not a gameplay journey. It proves neither hidden RNG purity, arbitrary immediate TextArea self-deletion, nested different-selection responder safety, physical pointer input, general dialogue behavior nor original-game parity. Real normal/direct dialogue, save/reload and menu evidence remain separate.
