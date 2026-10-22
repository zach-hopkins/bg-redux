# P1-04 saved NPC color investigation

Status: read-only evidence/source investigation, not a fix approval. The later
[independent original reload audit](../testing/phase1-original-color-reload-audit.md)
now observes the controlled-high saved-byte sequence **237→46→46** across two
fresh-process original BG2EE reload/ordinary-save cycles. That transition is
not established as a candidate-only regression, and stable persisted high bytes
cannot be assumed to be the original contract. The historical native evidence
and source hypothesis below remain useful; they do not establish exact original
runtime palette memory or a universal stock-color rule. No engine edits,
builds, tests or native/game launches were performed by this investigation/audit.

## Exact preserved evidence

All directories below are relative to `C:/BGRedux/phase1-local/`. Each row
identifies the run's `result.json` and the diagnostic file inspected alongside
the raw snapshots. Hashes are SHA256 of existing files, not new run receipts.

| Label | Directory | Diagnostic file |
|---|---|---|
| BV | `runtime-baseline/phase0-local/results/20261021T234929Z-phase1-before-vanilla-6a4c9726` | `reload-1-semantic-diff.json` |
| CV | `runtime-candidate-58c2995e/phase0-local/results/20261022T011356Z-phase1-after-vanilla-3eb08216` | `reload-1-semantic-diff.json` |
| BG | `runtime-baseline/phase0-local/results/20261021T234944Z-phase1-before-gui-a5757621` | `legacy-semantic-differences.json` |
| CG | `runtime-candidate-58c2995e/phase0-local/results/20261022T011625Z-phase1-after-gui-bc2007a5` | `legacy-semantic-differences.json` |

| Label | result.json SHA256 | Diagnostic SHA256 |
|---|---|---|
| BV | `43c8b8139af993eb576480e86004c4c96321b9616518ddaa5280483c696268ad` | `d123767a996fd02d4b28ae531d53bc9147ff67a3bf3e4e368d7c675d21bceeb3` |
| CV | `23d46a6a7d25a13144adef2a0af6f683f8fae02160b7065725a8a113028c1c0b` | `97c4b4679d4e906e0e95d6399e152e2bfab0cbc5b0d330fa7bd6adb3166deca9` |
| BG | `1cdb878340f0525baaae96367fbe5a73bcaf492d8e199d7b8d0f7852b1c1131d` | `efdca9a0c3316e202d4d49c6036cd6bbf7d3f2b2241b00f8d5634ca62551cc1a` |
| CG | `6c3f5bbcff7f1913433738f4d4f0a3d2e5904c49611227fa2e7a5a93dccc357a` | `7f457e587613a0b623da5f660d4553a2e77d7f7b535fae72ae9b0ce81387a38e` |

Vanilla raw snapshots are `import/state.json` and `reload-1/state.json`.
GUI snapshots are `gui-save/overwrite-persisted.state.json` and
`gui-reload/00-game.state.json`. Semantic actor indices differ from raw
indices because `C:/BGRedux/tools/phase0/save_harness.py:51` defines the actor
identity and line73 sorts current-area actors.

| Run | Actor identity / position | Raw / semantic index | Base and modified color change |
|---|---|---|---|
| CV | Shadow Thief, CSThief1, AR0602 `[3945,2821]` | 29 / 7 | leather212: `0xEDEDEDED` to `0x2E2E2E2E` (237 to46) |
| BV | Goblin, None, AR0602 `[3189,1478]` | 12 / 31 | major210: `0xDEDEDEDE` to `0xC0C0C0C0` (222 to192) |
| CG | Shadow Thief, CSThief1, AR0602 `[2830,3125]` | 32 / 3 | minor209: `0xC9C9C9C9` to `0x0C0C0C0C` (201 to12) |

Stat names are defined in `gemrb/includes/ie_stats.h:507`, `:508`, and `:510`.
These are changed initialized palette stats, not arbitrary stat212 corruption
or a wire-only mismatch. Visual appearance was not independently verified.
Both vanilla runs have two semantic differences on reload1 (base/modified
color), zero on reload2, and26 repeat-import color differences. Different
affected actors in independent runs do not establish a candidate regression.

## Source hypothesis

Source anchors refer to this worker's repository paths; they were inspected
without modification:

- `gemrb/plugins/CREImporter/CREImporter.cpp:761`: SetupColor resolves random
  color indices through RANDCOLR, including a randomized fallback for unknown
  high indices. At `:849` to `:857`, GetActor reads each color byte, calls
  SetupColor and expands the result into the stat's four bytes.
- `gemrb/plugins/CREImporter/CREImporter.cpp:2039` to `:2045`: the writer stores
  the low byte of the current resolved BaseStats color for non-PST creatures.
- Stock `randcolr.2da`, read from `phase0-local/bg2ee-clean/data/Default.bif`,
  SHA256 `fadbc1a6b61cd3ec06105fc634e796c8a6393f0da326696636f571a0dc9b7a93`,
  declares indirection indices200 through255 and also produces palette values
  at least200, including237 and222. The read-only Phase0 KEY/BIFF reader was
  used; a full resource-provider precedence trace was not collected.

Together these support a collision: an already resolved high palette byte
written to a save is interpreted as a random selector again on reload. This
explains the observed class of changes but is not an independently instrumented
causal trace. `gemrb/core/InterfaceConfig.h:99` defaults SaveAsOriginal to1;
skipping random resolution only for GemRB CRE V0.0 would not cover the observed
compatible-save route.

## Separate residuals

Both GUI runs grow the same Smoke Mephit, None, AR0602 `[2573,2461]`, raw actor2
/ semantic actor27, from22 to29 effects. Seven IMMCLOUD timing1 effects are
added: opcode267 parameters14665,41616,40979,40969,41495 and opcode101
protection parameters134/216. Existing matching effects remain. This is real
queue growth in both runs, but effective immunity/removal behavior was not
tested. `gemrb/core/Item.cpp:45` regenerates equipping blocks;
`gemrb/core/Effect.cpp:150` excludes timing2 from saved effects but retains
timing1. Do not approve broad deduplication based on this observation alone.

Neither vanilla nor GUI collected reload differences contain changed flags.
Both vanilla wire oracles report315/351 checks and the same36 HP/item-record
differences. Those comparisons are original serialized inputs versus
initialized state, a separate boundary. Internal flags and the serialization
masks at `gemrb/plugins/CREImporter/CREImporter.cpp:1986` to `:2005` are not
proof of incorrect item behavior.

GUI time32717 to32715, variable-name case, and opcode187/special1/timing11 local
markers have the explicit representation contracts recorded in each run's
legacy_semantic_diagnostic. The markers explain Imoen's76 to78 and Assassin
ishaddud's5 to6 effect counts. They do not explain NPC color changes or the
seven IMMCLOUD additions. These categories must remain separately reported.

## Acceptance after the original controlled-high observation

The original audit binds one inert RDXCOLOR, case1/nonce1455348314/stage2/ready1,
the private selector mapping228→237 and237→46, exact preceding-save input hashes,
two owned fresh-process launches and ordinary save UI boundaries. The three
saved CRE leather bytes are237,46,46; saved NPC identity/position and zero
items/effects/five NONE scripts remain consistent. This supersedes the earlier
assumption that high-color stability itself is an original-compatibility gate.

Compare the native candidate against that same sequence and controlled inputs.
Retain low-color and fresh-resource selector controls, exact original/runtime
palette distinctions, and all other save residuals separately. A matching
237→46→46 sequence supports this bounded legacy behavior; it does not waive all
NPC color differences or approve broad importer changes. A future stable-color
policy would require a separate compatibility/product decision, not inference
from a candidate save difference alone.

## Historical next-validation hypothesis (superseded acceptance wording)

Prepare one isolated NPC with a controlled RANDCOLR result above199, retain
the exact input table/color bytes, and record initial versus two successive
save/reload palette stats plus visual evidence. Include an ordinary low-color
control, a fresh-resource random-selector control and the original-runtime
counterpart. Observe calling-thread RNG state where available without seeding
or resetting it. The earlier proposed stable-persisted-color acceptance was a
hypothesis; the later original237→46→46 observation supersedes it as a legacy
contract. Fresh resource indirection still needs its own intended-behavior check.

Only an independently demonstrated incompatibility would justify a narrow fix,
respecting compatible and native save formats and the observed original
transition. Do not recursively reroll high results, clamp colors below200,
whitelist all color-stat changes, or infer original compatibility from this
GemRB-only evidence. No fix is approved or implemented by this document.
