# LAB native runtime validation — October 21, 2026

External save and GUI hosts were rebuilt successfully on LAB with the transferred
UCRT64 toolchain. Engine source and engine/plugin binaries were not rebuilt or
edited. Capabilities, vanilla import/reload and normal GUI/save execution are now
independently observed in the guest.

| Check | Execution | Assertions | Compatibility result |
|---|---|---|---|
| Capabilities | Exit 0; protocol declaration captured | Declaration only | Does not itself establish every advertised operation |
| Vanilla import/resave, two fresh reloads, repeat import | Four native processes exit 0, no timeout | 24/24 pass | Both reloads have zero normalized differences; overall `differences` |
| Normal GUI create/cancel/overwrite and fresh reload | Two native processes exit 0, no timeout | 20/20 pass | Overall `differences`; presentation remains incomplete |

## Persistence and presentation observations

Vanilla reloads each retain 140 raw leaf differences and zero normalized
differences. The independent original wire reader matches 315/351 checks; its
36 HP/item-record observations remain visible. Repeat import has 24 differing
area-NPC color-stat fields, with party/stored-NPC/world scopes matching. No RNG
or full save-fidelity claim follows. The first import took 52.810 seconds without
an early stdout log, but completed within its 60-second budget; subsequent stages
took about three seconds each. No loader failure or timeout was observed.

GUI persistence has 449 differences under the basic normalization. The separate,
documented legacy diagnostic leaves 53, all under one Smoke Mephit effect list.
For the actor at [2573,2461], IMMCLOUD records grow
20 to 27; total collected
effects grow 22 to 29.
Within IMMCLOUD, timing-1 permanent records grow
14 to 21.
This reproduces the previously characterized accumulation and is not newly
classified as a GemRB-only defect. Raw comparisons and diagnostic contracts remain
separate. Both harness commands correctly return exit 1 for `differences`, while
their native processes and scenario assertions pass.

The stock callbacks refused an empty save name, created a named save, cancelled
an overwrite without changing its bytes, overwrote successfully, then reloaded
in a fresh GUI process. The created save remained unchanged during reload.
Inventory and record screenshots were visually inspected; missing panel content
and typography issues remain. This is rendering execution, not presentation
parity or pointer/input hit-testing acceptance.

Renderer observed in the actual GUI process:

`[SDL 2 GL Driver]: OpenGL version: 4.3 (Compatibility Profile) Mesa 24.1.0, renderer: SVGA3D; build: RELEASE;  LLVM;, vendor: VMware, Inc.`

## Preservation and reproducibility

Before/after inventories match for all 3,652 source-checkout files inspected,
four baseline engine/test binaries, 45 plugins, the core import library and all
six original vanilla fixture files. Binary inputs also match the original base
transfer manifest. No CMake engine rebuild was invoked. Python bytecode writes
were disabled. The existing fork's prior documentation/tool changes were retained.

Historical host results and the earlier guest transfer/unit runs remain intact.
New commands, stdout logs, native process logs, configurations, raw states, diffs,
saves and screenshots are retained in unique guest directories. External build
receipts and copies of the built hosts are frozen in the validation run, so later
rebuilds do not silently replace this run's provenance.
The complete external tool sources are also copied into `tool-source/` in that
run, excluding Python bytecode caches.

Fresh run directories under `C:/BGRedux/phase0-local/results/`:

- `20261021T225115Z-lab-native-validation-d3a4ff65/`: commands, frozen builds, protected-file inventories, consolidated summary and artifact hashes.
- `20261021T225226Z-lab-vanilla-import-reload-153ab16e/`: original-vanilla scenario and all four native stages.
- `20261021T225329Z-lab-gui-save-d4748398/`: normal GUI save/reload and presentation artifacts.

The machine-readable consolidation is `validation-summary.json` in the first
directory. Full engine/campaign/mod parity, deterministic stepping and the
original-executable oracle are not established by these bounded tests. Physical
input isolation and independently verified clean/validated VMware snapshots
remain pending; overall migration acceptance is not marked complete.
