# BG2EE baseline — executed Windows opening and outstanding gates

Date/revision: October 20, 2026, `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351`. **Built and opening playable; presentation defects and unresolved save-fidelity/campaign gates prevent a native-like claim.** See the [full executed report](../testing/phase0-executed-baseline.md) for commands, counts, failures, provenance and limitations.

## Established input

- Nominated Steam installation: `C:/Program Files (x86)/Steam/steamapps/common/Baldur's Gate II Enhanced Edition`; executable2.7.3.0, app257350, build23534562, English/public. Local depot manifests3152121405399028813 and4737130585273772372 identify installed input, not globally latest content.
- Fresh workspace copy `phase0-local/bg2ee-clean`: 2,324 files, 3,888,110,389 bytes, all SHA256 source/copy matches. No WeiDU.log found; independent depot-content verification was not performed. [Complete manifest](evidence/bg2ee-copy-manifest.json).
- Post-run all original manifest members still match. GemRB added a log, gem-baldur.ini, gemrb_console.txt and gemrb_path.txt to the disposable copy. Private cache/save/config/profile trees are separate; source Steam/personal installations were not changed.
- [Binary/run inventory](evidence/baseline-results.json) records source/binary hashes, raw result locations and data verification. Private assets/saves/toolchain remain ignored under phase0-local.

## Established execution

| Gate | Result |
|---|---|
| Windows engine build | Success, Debug SDL2/OpenGL via MSYS2 UCRT64; no engine source changes |
| Opening | User verified character creation, playback and playability; logs show opening/dialogue and inventory/record screens; session exited0 |
| Presentation | Missing screen content reproduced through runtime controls/captures. Font experiments change typography, not empty panels. See [GUI investigation](../testing/gui-save-and-presentation-results.md) |
| Stock CTest | 6/7 executables pass; core has one Cyrillic-uppercase locale failure and omitted Windows live tests |
| Expanded managed core | 229 run: 219 pass, 9 skip, 1 fail; six disabled. Explicit external logger cleanup gives normal exit1 |
| Movement | Existing demo-backed nine tests pass with normal exit0 through managed test entry |
| Minimal startup | Fails Debug assertion on tiny TLK fixture/empty string; not a BG2EE result |
| Original save import | Executed with the user’s fresh Steam BG2EE save through the external native host. Two fresh-process reloads succeed; scenario 24/24 passes. Full fidelity remains open |
| GemRB save/reload | Library checkpoint tests plus stock GUI create/cancel/overwrite/fresh reload execute. GUI20/20 checks pass; IMMCLOUD effect delta and color variability keep fidelity open |
| Combat / transitions / campaign | Required gates outstanding; playable opening is insufficient |
| Performance / smoothness | No benchmark; human observation only; Debug/30FPS is not a causal diagnosis |
| SCS / Ascension / EET / EEex | No GemRB validation. Do not transfer prior original-executable laboratory claims |
| Linux / portable CI | Not executed |

## Source and upstream exposure

The profile still calls BG2EE experimental. Modern image importers and ordinary BG2-compatible GUI scripts exist; source support alone does not establish fidelity. The actual opening-area run evaluated the stubbed `WeaponEffectiveVs` trigger twice, a concrete compatibility case to trace; neighboring `WeaponCanDamage` is a source stub not yet observed firing. Startup unknown action entries must be joined to actual compiled-script usage. The initial metadata probe inventories 62,575 KEY resources, 103,599 TLK strings, fonts and main inventory/record labels; it is not a complete opcode/action/resource-semantic scan.

[Upstream issue roadmap](upstream-issue-roadmap.md) prioritizes combat timing, dialogue/fades, projectiles, campaign import, equipment, EE resource rendering and usability. Open issues are reports to reproduce, not a ready-made blocker count. Preserve the shipped lightning workaround and recognize Quick Loot's implemented alternative.

Verified source limits from the initial audit remain relevant: opcode342 parameter2=4 personal-space handling and TODOs365/366 require used-content tracing before severity assignment. Save comparisons can exit0 without IEDIFF. Classify skipped/unavailable evidence explicitly.

## Next acceptance work

1. Trace fonts/visible text per control and complete the information baseline. Modern UI is approved; use [existing Redux requirements](../architecture/redux-project-context.md) without porting EE Lua/hooks wholesale.
2. Extend the working native import/resave/reload client: validate HP/flag representation, archived world/area/container state, normal-mode effect serialization and color variability. Reverse export to the original executable is optional initially.
3. Establish the [AI-first command/query and observation boundary](../testing/ai-first-harness.md). Fresh-process native state queries, party selection, snapshots and assertions now work; interactive RPC, full-loop stepping and semantic UI traversal remain proposed.
4. Execute opening progression, combat, transitions and timing under controlled actual-loop scenarios, then relevant upstream issue fixtures. Add curated mods only afterward.

Use exact run IDs, source/binary/config/data/fixture hashes, worker mode, RNG-control status, observed/expected outcomes, process exit, assertion skips and evidence. A green process alone is insufficient.

## Effect lifecycle follow-up

The [IMMCLOUD investigation](../testing/immcloud-lifecycle-investigation.md) reproduces growth of seven saved permanent equip effects per reload/save cycle and stops it with a timing-only private item control. It establishes the mechanism and growing serialized state; original BG2EE behavior, combat impact and the correct production remedy remain unverified. No data override was installed into the normal profile.
