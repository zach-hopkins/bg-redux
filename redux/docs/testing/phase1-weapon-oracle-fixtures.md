# Phase 1 extended weapon-query fixture preparation

`redux/tools/phase1/weapon_oracle_fixtures.py` prepares inputs only. It does
not launch either engine or claim an oracle outcome. All stock assets and
generated saves/scripts remain in private result/game/profile directories;
publication includes code, tests and this description only.

Coordinator invocation for the first eight hand cases:

```powershell
& C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe -B `
  C:/BGRedux/phase1-local/worktrees/weapon/redux/tools/phase1/weapon_oracle_fixtures.py `
  --project-root C:/BGRedux `
  --results-root C:/BGRedux/phase1-local/results `
  --group hands --prepare-original
```

Omit `--prepare-original` to generate private fixtures without a game copy
or Documents profile. Every invocation creates a fresh unique result
directory. With that explicit option it verifies/copies only manifested clean
game files into a fresh `phase1-local/original-weapon-game-*`, installs unique
scripts, binds `engine.lua` to `Documents/BGReduxP1/<run-id>`, creates the
private load list, disables cloud saves in that new profile, and retains the
optional copied Steam DLL under an inert filename. It never changes installed
game data or existing profiles. Partial/failed preparation receipts remain.

The explicit project root supplies the existing Phase 0 helpers by read-only
import from `C:/BGRedux/tools/phase0`. A root mismatch is rejected. Preparation
reuses the bounded embedded-CRE relocation, baseline fixture hash gate,
compiled-script action/trigger grammar, resource metadata reader and wire
reader. It does not modify those helpers or use their launch functions.

## Cases and questions

`--group hands` prepares eight cases in order:

| Case | Main / off hand | Target defense |
|---|---|---|
| 01-normal-plus-pfmw | SW1H01 / SW1H02 | Opcode120 magical |
| 02-plus-normal-pfmw | SW1H02 / SW1H01 | Opcode120 magical |
| 03-crush-slash-slash100 | HAMM01 / SW1H01 | Slashing100 |
| 04-slash-crush-slash100 | SW1H01 / HAMM01 | Slashing100 |
| 05-normal-empty | SW1H01 / empty | None |
| 06-normal-shield | SW1H01 / SHLD01 | None |
| 07-plus-empty-pfmw | SW1H02 / empty | Opcode120 magical |
| 08-normal-shield-pfmw | SW1H01 / SHLD01 | Opcode120 magical |

These distinguish explicit off-hand, empty/shield handling and BOTH's ANY/ALL
combination using asymmetric immunity or damage channels. No expected Boolean
table is invented before original execution.

`--group ammo` supplies eight cases: BOW01+AROW02 and BOW02+AROW01, each
against magical protection and enchantment thresholds0/1/2. Stock ITM hashes,
flags, enchantment and ability attack/damage types are recorded rather than
inferring their metadata from filenames. `--group damage` supplies HAMM01,
DAGG01 and BOW01+AROW01 against matching crushing/piercing/missile100, then
unrelated slashing100 controls. `--group all` includes22 cases.
`--cases <exact-id> ...` selects an explicit subset, overriding the group;
duplicates and unknown IDs fail.

## Evidence contract

Each fixture uses a unique eight-character BCS resource assigned to the
protagonist's primary CRE script. The script asks both actual triggers against
Player2 for HAND1/2/3, in six serialized stages. Every query writes an explicit
Boolean, including false, before advancing. The final stage requests ordinary
SaveGame0 after writing DONE1/STAGE7.

`RDXE1/RDXD1`, `RDXE2/RDXD2`, `RDXE3/RDXD3` are EffectiveVs/CanDamage for
the respective hand. `RDXCASE` is the run-local numeric case index and
`RDXNONCE` is a fresh positive31-bit run identity. Unique fixture folder
suffixes carry the same nonce in hex. Completion requires all six Boolean
globals, exact case/nonce, DONE1 and STAGE7; a stale chapter autosave cannot
stand in for results.

The receipt records the exact final six-file fixture inventory, script hash,
CRE physical slots and selected ability/ammo, GAM quick-slot assignment,
diagnostic defense and source item metadata. The initial fixture's precursor
manifest from the Phase 0 helper is labeled precursor; final `fixture_files`
is authoritative. Main weapon uses physical CREslot9; offhand/shield2;
ammo13; GAM quick-slot35 for melee or11 for ammo, ability0. The equipped bow
uses selected code-24 and exactly40 ammunition charges.

After an explicitly identified output save is obtained, import this module,
call `load_api(project)` then `inspect_output(api, gam_path, case_row)`.
It independently checks unique script, equipment, declared defense and all
query/identity globals. Only known opcode120 magical-protection Parameter1
normalization0/0xffffffff is permitted; other defense changes fail. Preserve
both engines' entire output folders and the returned hashes.

These are serialized input/output guards. They **do not establish the actual
cached runtime weapon selection**. Native validation must additionally capture
each `WeaponInfo[0/1]` item/header, itemflags, enchantment, slot, selected ammo,
ability and exact sender/target before calls, without stepping the main loop.
Repeated-call state comparisons and evaluator True/False controls are a
separate required acceptance gate. Neither a completed script nor a helper
unit test proves side-effect freedom or original parity.

## Checks performed here

The focused standard-library unit suite covers13 positive/negative cases:
six exact query branches and identity writes; stale/missing/incomplete/non-
Boolean outputs; physical slot/selection/header/ammunition mutations; duplicate
same-resref inventory instances; invalid declarations and bounded paths.

```powershell
& C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe -B `
  -m unittest discover -s redux/tools/phase1/tests -v
```

An initial12-test run found a cross-platform drive-path validation defect;
`PureWindowsPath` now rejects Windows drive/absolute/traversal forms even when
the bundled Python uses POSIX path semantics. No preparation, private game
copy, native query or original process was executed by the implementing worker.
