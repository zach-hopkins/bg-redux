# Phase 1 external menu validation

`menu_probe.cpp` is a bounded full-loop observer, not an engine plugin or general RPC. `menu_harness.py` builds that external host against a nominated existing candidate build, then runs two fresh private profiles using the same source tree/game font resources. It does not build the engine or install font overrides. The coordinator owns LAB's single native/UI controller; do not run this concurrently with another native/UI test or rebuild source/binaries while a protected-input run is active.

The initial GUI assembly commit is `13dd6db7f`. Compile/runtime validation of this new menu adapter remains pending coordinator execution. Worker validation: **26/26 tests** (15 GUI semantics/bindings plus 11 menu plan/receipt checks); Python syntax and whitespace checks pass. No worker game or native process was launched.

## Coordinator invocation

Supply absolute paths for the selected fork worktree, completed candidate build, manifested UCRT prefix, private game/vanilla fixture and result root. The build tree must contain `gemrb/libgemrb_core.dll`, `gemrb/core/libgemrb_core.dll.a` and matching plugin/config headers. Source is the engine repository root containing `gemrb/core` and `gemrb/GUIScripts`.

```powershell
& $python -B redux/tools/phase1/menu_harness.py build --source $source --build $build --prefix $prefix --output-root $results
& $python -B redux/tools/phase1/menu_harness.py run --source $source --build $build --prefix $prefix --output-root $results --probe $menuProbe --fixture $vanillaSave --game $privateGame --resolutions 1024x768,1280x960
```

`$menuProbe` is the exact `Redux_menu_probe.exe` path printed in the build result. Run arguments must nominate the same candidate DLL/build as compilation. Configs, cache/home/profile/save copies and outputs get a unique timestamp/UUID directory; prior results are retained. Engine/game resources and baseline fixtures must remain under the coordinator's broader preservation inventory. This helper directly verifies its five adapter source inputs, selected engine DLL and copied/original save files; it does not claim to hash the entire checkout/plugin/game tree. Settings callbacks may rewrite the private test config; before/after config hashes are retained. Exit1 retains test failures, including the known unimplemented hotkey transition; it is not silently relabelled passed.

## Exercised behavior and evidence

Normal startup uses a private profile with exactly one copied save and the registered `GUILOAD` row callback. The host waits for the actual load boundary and runs `Interface::Main`; it does not substitute a library snapshot for real drawing. A timer separates each open/callback from its observation/capture. Actions use ordinary GUI loaders or registered native `Control::PerformAction`; they bypass pointer hit testing and keyboard focus traversal.

The plan covers inventory/record; all six Stats categories plus next/back when another page exists; record information, biography, customization, kit description and applicable export cancel; mage/priest book views; journal; area map and world-map view; options, video, audio, character sounds, gameplay, feedback, autopause, hotkeys; save picker cancel and load picker cancel. No save is created/overwritten by this plan and no world-map travel, spell memorization/cast, party removal, configuration value adjustment or character export is requested. The existing Phase 0 save/create/cancel/overwrite/fresh-reload runner remains required complementary evidence.

Every captured screen retains a BMP, full pack/control text/frame/visibility/disabled inventory, normalized raw world snapshot and separate cached-THAC0/action/target/attack-count observer. Registered callbacks retain unique before/after state and observer files. `fonts.json` records actual runtime font types, line heights, baselines and glyph/sample metrics. `menu-runtime.json` binds each named observation to its capture number and preserves assertions/errors; `menu-host-result.json` separately reports native completion. The wrapper rejects incomplete coverage, missing categories, duplicate captures, missing/malformed BMPs and missing structured evidence. It compares final/initial collected world state with only explicit test selection removed; no effect/time/global differences are masked. Hidden RNG identity remains unproven.

Assertions check actual selected actor name/HP, populated available weapon values, usable panel geometry, real window transitions and closes, correct selected Stats category, bounded content/page numbers and actual next/back state changes. They are stronger than a text-presence tally but **do not certify visible glyphs or pixel fit**. Inspect both resolutions' images for game typefaces/roles, artistic composition, readability, clipping/overlap/baselines, button affordance and all menu labels. Compare THAC0 text to the separately observed cached native value where applicable. Review callback before/after state for observer noninterference, especially used hand, current action/target/count, ammo/effects and globals. Do not infer those guarantees from process success.

Current source `GUIOPT.OpenHotkeyOptionsWindow` is a TODO, despite gameplay control51 dispatching it. The adapter requires a real window transition and retains that failure. A returned callback is not a working menu.

## Context that needs separate fixtures/journeys

Viewing an empty non-priest book does not test priest memorization/casting. Disabled export is labelled context-gated, not passed. Store/merchant, container/bag/loot, dialogue/cutscene, character generation, world travel, level-up/dual-class, sequencer/contingency, rest confirmation, party reform and editing submenus require applicable scenario/actor/context evidence. This general menu view plan cannot satisfy those journeys by force-opening synthetic windows or invoking unavailable actions. Pointer coordinates, focus/keyboard navigation, game-time progression and unpaused gameplay require separate tests.

Run focused tests without starting a game:

```powershell
& $python -B -m unittest discover -s redux/tools/phase1/tests -v
```
