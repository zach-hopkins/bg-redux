# Phase 0 executed baseline — October 20, 2026

**Outcome: built and playable through the opening; not yet native-like or a passed compatibility gate.** Engine revision `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351` is unchanged. Builds, external test adapters, private data/configuration and documentation were added outside the engine checkout. The game was left available for manual play; no further menu automation was used after the user took over. That session subsequently ended with launcher-observed exit0.

**Later Phase 0 update:** the [native save/harness report](save-import-and-harness-results.md) supersedes the unvalidated-save status below. A fresh human-created vanilla fixture imports/resaves/reloads;24/24 scenario assertions pass. The old upstream-test skips and earlier failed attempts remain historical evidence. Full fidelity remains open.

## Data and build provenance

The nominated Steam BG2EE **2.7.3.0**, app 257350, build 23534562, English installation was copied into `phase0-local/bg2ee-clean`. All **2,324 files / 3,888,110,389 bytes** matched source SHA256 hashes. Post-run verification still matches every original manifest member. GemRB added `GemRB.log`, `gem-baldur.ini`, `gemrb_console.txt` and `gemrb_path.txt` to the disposable copy. This is an exact copy of the nominated installation, not independent Steam-depot integrity verification. No active EET/personal game install was used as vanilla data.

The [complete content manifest](../compatibility/evidence/bg2ee-copy-manifest.json) and [run/binary inventory](../compatibility/evidence/baseline-results.json) contain hashes. Licensed game resources, saves, screenshots, binaries and toolchain stay under ignored `phase0-local/`.

| Component | Executed configuration |
|---|---|
| Toolchain | Workspace-local MSYS2 UCRT64, GCC 16.2.0-6, CMake 4.4.4-3, Ninja 1.13.2-1 |
| Dependencies | Python 3.14.8-1, SDL2 2.32.10-1, SDL2_mixer 2.8.2-1, GLEW 2.3.1-4, GTest 1.18.0-1, OpenAL 1.25.2-1, FreeType 2.15.0-1, libpng 1.6.59-1 |
| Engine | Debug; SDL2/OpenGL; tests enabled; Werror disabled; libVLC disabled |
| GPU runtime | Radeon RX 9070 XT; OpenGL 4.6 compatibility, driver string 26.8.1.260810; GLSL 4.60 |
| Initial BG2EE config | 1024×768, CapFPS=30, 0-worker immediate pathfinding, OpenAL, English |
| Writable state | Separate caches/saves and a child-process private Windows home/Documents profile |

Build succeeded in `phase0-local/build`. The initial obstacles were dependency discovery and Windows tooling: CMake's GLEW finder did not expose the modern MSYS2 imported target correctly; Python discovery selected a different system Python; windres mishandled the compiler path containing spaces. External CMake discovery adapter, explicit matching Python and short-path resource-compiler arguments resolved them. No engine source patch was needed. Reproduction entry: `tools/phase0/build-msys.sh`; exact package inventory and attempt logs are under `phase0-local/logs/`. The script is machine-specific and package versions are recorded, not a portable/reproducible dependency lock yet.

Successful log: `build-windres-config.log`, followed by `build-live-tests.log`. A later test-entry build attempted to relink the engine DLL while the user was playing and correctly failed on the mapped DLL. The running engine was left alone. Already compiled test objects were linked into a **separate** `Redux_phase0_core.exe` using `tools/phase0/link-managed-tests.py`; the engine DLL hash remained unchanged. Do full rebuilds with that engine instance closed, or use a separate build directory.

## Executed tests and honest coverage

These are distinct runs, not additive test counts.

| Run | Actual result | Limitation |
|---|---|---|
| Stock CTest, seven executables | **6/7 executables pass**; core fails. Core: 197 run, 195 pass, 1 skip, 1 fail; 4 disabled. Other executables: 61 tests pass | Windows stock excludes live movement/map/save tests despite OpenGL renderer selection |
| Existing live tests enabled externally, default CTest cwd | Core crashes after failing to find `../../tester.cfg`; other six executables pass | Test-runner path/failed-setup teardown defect; not evidence that ordinary gameplay movement crashes |
| Corrected cwd, original test entry | Movement **9/9** assertions; focused map/path/VFS **84/84**; full core **229 run: 219 pass, 9 skip, 1 fail**, 6 disabled | Assertions/XML complete, then process hangs; cannot label process pass |
| Separate managed test entry + corrected cwd | Full core: **219 pass, 9 skip, 1 fail**, 6 disabled; normal exit **1**, no timeout. Movement: **9/9**, normal exit **0** | Only explicit logger cleanup added to entry; unchanged test assertions and engine DLL |
| Configured original-save fixture | Designated BG2EE case still **skipped**, process 0, external verdict **incomplete** | No import/resave/equivalence established |
| External runner timeout probe | 50 ms budget deliberately interrupts a live run; verdict **timeout**, child tree terminates, missing XML is not a pass | Runner-mechanism test, not movement regression result |
| Bundled minimal startup | Exit **3221226505 / 0xC0000409**; Debug assertion reading empty string | Minimal TLK fixture is 19 bytes; invalid strref-1 seek then unchecked `back()`; not a BG2EE TLK failure |

Stock XML: `phase0-local/results/stock/`. Expanded default CTest: `results/live-enabled/`. Corrected historical runs: `movement-corrected-cwd`, `map-path-corrected-cwd`, `full-core-corrected-cwd`. Bounded results have timestamped run directories containing `result.json`, `process.log` and GoogleTest XML; IDs and hashes are in [baseline-results.json](../compatibility/evidence/baseline-results.json).

**Confirmed test infrastructure defects:**

1. [SDLVideo's OpenGL define is PRIVATE](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/SDLVideo/CMakeLists.txt#L17), while [Windows live tests guard on that define](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/Test_Movement.cpp#L8). External CMake includes enable the existing code on the test target only.
2. The [live fixture](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/LiveGameFixture.h#L38) expects core-directory cwd; Windows CTest chooses the core DLL directory one level above it. External runner supplies the expected cwd/resources.
3. GDB captured full-core shutdown waiting in `Logger::~Logger`, `loggingThread.join()`, reached through the static logger destructor during DLL CRT process shutdown. Backtrace: `phase0-local/logs/core-shutdown-backtrace.log`. [Logger teardown](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Logging/Logger.cpp#L25) and [static ownership](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Logging/Logging.cpp#L26) match that trace. Explicit `ToggleLogging(false, true)` before returning from an external test main eliminates the observed hang. This localizes teardown ordering; it does not establish every Windows exit path is repaired. Termination was requested only for owned test/debugger processes; some old processes remained pending Windows teardown.
4. The only expanded-suite assertion failure is [StringTest.StringToUpper](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/Strings/Test_String.cpp#L302). It requests `C.utf8` on MinGW. A direct local UCRT probe rejects that locale name and leaves Cyrillic lowercase, while `.UTF8` uppercases it. Strong evidence of locale portability/setup failure, not an explanation of all in-game typography.
5. After assigning a real BG2EE GamePath and copying a disposable original-format Chapter 1 Start save, the save case still says unconfigured. [Setup inserts a PathJoinExt-created key; lookup hardcodes `./bg2ee.cfg`](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/tests/core/Test_SaveGame.cpp#L65); [Windows delimiter is backslash](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/System/VFS.h#L49). Config generation was verified on disk. This mismatch explains the pre-load skip. The copied save's mod/creation provenance is unknown, so it would remain exploratory even after loading. IEDIFF equivalence was not run.

## Human-verified BG2EE opening

The game launched, character creation completed, and the user reported: **intro video played; movement works but looks janky/unsmooth; fonts look wrong; inventory lacks labels; character profile lacks most text; overall playable**. Runtime logs show the opening area/dialogue resources and inventory/record/map/journal scripts being exercised. Two GemRB-generated autosaves exist in the private profile. These are not original BG2EE save imports and have not been independently reloaded/compared.

The configuration requests SkipIntroVideos=1 and this build omits libVLC. Preserve the user's playback observation, but do not infer complete movie-decoder/WebM coverage or identify which cinematic path was used. No combat/campaign completion, area-transition gate, performance benchmark, original-executable comparison or localization pass is claimed.

## Presentation findings: observation versus cause

- **Verified missing implementation:** [GUIINV.py explicitly notes the missing EE INVSTATS overlay and AC/HP/THAC0/damage button backgrounds supplied by ui.menu](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/GUIScripts/bg2/GUIINV.py#L83). This can explain part of inventory presentation; it does not establish the cause of every missing label.
- **Verified data:** the read-only [UI metadata probe](../compatibility/evidence/ui-resource-probe.json) finds 13 labels in main GUIINV window 2 and 26 in GUIREC window 2, all with valid, nonempty English TLK entries. It inventories 62,575 KEY entries and 103,599 TLK entries. It does not emulate full runtime resource precedence or script/menu-generated text. A general “missing English TLK” explanation is insufficient.
- **Verified font paths:** many named fonts exist as both TTF and BAM in the data. [fonts.2da](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/unhardcoded/bg2ee/fonts.2da) requests size14 for the listed fonts; [Interface](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/Interface.cpp#L1249) prefers TTF except flagged BAM icon fonts. [BAM font creation ignores requested size/style](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/plugins/BAMImporter/BAMFontManager.cpp#L34), while TTF uses size but ignores the style parameter. Startup reports all configured font names loaded. The normal log does **not** identify the chosen type/provider per font; do not assert that every font actually used BAM, fallback or an absent system font.
- **Verified noisy diagnostic:** seven inspected “Bad 2DA signature” tables start with whitespace-padded `2DA ... V1.0`. The importer compares a literal first-eight-byte string, warns, then continues parsing. These warnings alone do not prove broken table contents or explain missing labels.
- **Unresolved:** selected font resource/type, glyph metrics, CHU control geometry, text/foreground state and EE menu-generated headings need per-control tracing plus screenshots. No repair has been made. Movement smoothness needs frame/update/path/animation traces; the initial 30 FPS Debug profile is a confounder, not a demonstrated cause.

Startup also reports unassigned action entries including `FollowPath`, `DisableAI`, `ContinueGame`, `WaitForVoiceChannel` and `PlaySoundThroughVoice`. IDS registration warnings establish missing dispatch entries, not that the opening exercised them. Join those to actually used BCS actions before assigning campaign severity.

**Additional verified runtime compatibility gap:** the later opening-area log reports `WeaponEffectiveVs has not been implemented yet!` twice. Unlike startup IDS registration warnings, this proves the trigger was evaluated in the actual run. [The registered implementation logs and returns0 for valid actor/target pairs](https://github.com/gemrb/gemrb/blob/bcb5cfaa9f19ffbe8a51f25a3c014fa344173351/gemrb/core/GameScript/Triggers.cpp#L4736); neighboring `WeaponCanDamage` is also a source-level stub but was not observed firing. Add a reference fixture before implementing their exact protection/enchantment semantics. The log does not identify the responsible BCS resource/caller or establish the resulting tactical difference; trace that next. This is a compatibility fix candidate, not a reason to redesign enemy AI.

## Next gate

1. Establish a usable UI baseline and trace the user's missing-text cases; keep screenshots and semantic label assertions. Modern UI is approved, so prioritize complete information/functions over reproducing EE Lua screen internals.
2. Repair/replace the external save test path/comparison plumbing, then import a known original clean fixture and compare normalized state after reload. Do not suppress skips/comparator gaps.
3. Expose controlled engine observation/commands as proposed in the [AI-first harness plan](ai-first-harness.md), before gameplay enhancements. Keep actual-loop timing tests distinct from synthetic movement.
4. Capture original-vs-GemRB movement/combat timelines, then investigate demonstrated differences. Execute the high-impact fixtures in the [upstream issue roadmap](../compatibility/upstream-issue-roadmap.md).
