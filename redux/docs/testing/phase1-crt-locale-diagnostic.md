# Standalone Windows CRT locale diagnostic

Executed LAB checkpoint: `20261022T053949Z-crt-locale-diagnostic-7f68a26d`
completes the standalone diagnostic with Phase0 and source/executable guards
passing. `C.utf8` is rejected (null return), leaves effective `C`, and fails the
exact Cyrillic uppercase mapping. `.UTF8` selects
`English_United States.utf8` and passes; native empty-string selection chooses
`English_United States.1252` and also passes. Explicit `C` fails the Unicode
mapping. Initial/final `LC_CTYPE` is `C`, with independent resets before every
case. This supports the unchecked test-setup diagnosis, not a production casing
correction or complete localized GUI acceptance.

The child reports its loaded `C:/Windows/System32/ucrtbase.dll`, independently
hashed as `dedb7611e1abc1ff3852dcac3d4c93a048d729e25b061973b9969f22698f14ca`;
the import listing and post-run file/version metadata are retained. Result
SHA256 is `012a446acc30db7dc2a38ce14bb90f0b9d40b68cb06c15355dc0dbf989ae2261`.
Independent worker review matched raw/embedded observations and all declared
source/compiler/import/child/executable/CRT bindings. The first preparation
attempt `20261022T053927Z-crt-locale-diagnostic-8e16175d` failed while freezing an
incorrect test-source path; no compiler or diagnostic launched. That partial
attempt and driver remain preserved.

Test-only corrections `61780eabf` and encoding refinement `5af04cdf7` are prepared
in the worker checkout but are **not integrated, built or tested**. The existing
candidate core still has its retained locale failure. A future fresh test build
must prove the fix.

The following design describes the diagnostic before execution:

This source-only diagnostic investigates the retained `StringTest.StringToUpper` failure. The corrected-CWD receipt is `phase1-local/results/20261022T051513Z-correct-cwd-core-e071d5bb/result.json`: normal exit1,229 passed, one Cyrillic casing failure, nine skipped and six disabled. It does not establish whether the unchecked `setlocale(LC_ALL,"C.utf8")` at `gemrb/tests/core/Strings/Test_String.cpp:317` selected a locale. `gemrb/core/Strings/String.h:186` uses `std::towupper` per UTF-16 code unit. Production `GemRB.cpp:19` uses the native empty-string locale; existing external native hosts request `.UTF8`.

`redux/tools/phase1/native/crt_locale_diagnostic.cpp` has no GemRB dependencies. It captures initial effective `LC_CTYPE` and mapping, then independently resets `LC_CTYPE` to `C` before each request: `C.utf8`, `.UTF8`, native empty string, and `C`. Every reset/request return and effective locale is recorded. The initial locale is copied and restored before exit. These are changes inside the diagnostic child process only; no OS settings, parent locale, engine, game assets or profile are changed.

The input is exactly `Закончить`, represented numerically as `[1047,1072,1082,1086,1085,1095,1080,1090,1100]`. The existing test expects `ЗАКОНЧИТЬ`, `[1047,1040,1050,1054,1053,1063,1048,1058,1068]`. The diagnostic records both full `wint_t` returns and UTF-16 destination units. JSON contains only ASCII; locale-name bytes are preserved numerically with an escaped preview, so console encoding cannot change the evidence.

The coordinator added read-only Windows loaded-module provenance: the child
records `GetModuleHandleW`/`GetModuleFileNameW`'s actual loaded ucrtbase path as
numeric UTF-16 units. Hash that returned file and retain the executable import
listing; do not infer the loaded path from a system-file listing alone. This
adds no engine dependency and changes no host setting.

The coordinator must compile and run serially after other guarded hosts finish. No compilation or execution was performed by the source author. Use the same pinned compiler as the engine, GNU++14 and default dynamic UCRT linkage. Do not add engine includes/libraries, `-static`, alternate CRT, or locale environment overrides. Example compiler argv (substitute a fresh private output directory):

```powershell
$cc = 'C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/g++.exe'
$src = 'C:/BGRedux/phase1-local/engine/redux/tools/phase1/native/crt_locale_diagnostic.cpp'
$out = 'C:/BGRedux/phase1-local/results/<unique-crt-locale-run>/crt_locale_diagnostic.exe'
$ccArgs = @('-std=gnu++14', '-O0', '-g', '-Wall', '-Wextra', $src, '-o', $out)
# Coordinator only: compile with a bounded child and preserve stdout/stderr/exit.
# Then run $out with these exact arguments through the bounded child runner:
$runArgs = @('--compiler-command', (ConvertTo-Json -Compress -InputObject (@($cc) + $ccArgs)))
```

Use a 15-second compile limit and 10-second run limit, preserving failed outputs, command arrays, CWD, child environment adjustments, exit/timeout/cleanup status and raw stdout/stderr in a unique result directory. Prepend only the same UCRT64 `bin` to the child's PATH. Freeze source, compiler and executable SHA256; capture `ucrtbase.dll` version/SHA and inspect the executable's import dependencies to bind the actual CRT selection. The observed system DLL at source review was `C:/Windows/System32/ucrtbase.dll` version `10.0.26100.9711`; that metadata alone does not prove which DLL a future process loads. The compiler-command argument is a declaration, explicitly unverified in JSON; the external build receipt and hashes provide its verification. `__VERSION__`, `__cplusplus` and scalar widths are also reported.

Exit0 means the diagnostic completed its reset/restoration and output operations. Rejected aliases and unmatched uppercase output remain explicit observations, never passes for the core assertion. Exit2 means usage/infrastructure/output failure. Reject non-JSON, incomplete output, missing cases, reset failures, wrong unit arrays or absent provenance. A rejected/ineffective `C.utf8` with successful expected mappings under `.UTF8` and the native locale supports a test-fixture diagnosis. Failure under actual production initialization instead warrants a separate production investigation. Neither outcome alone proves complete Unicode, localized GUI or original-game fidelity.

If fixture setup is confirmed, a narrow follow-up is a checked platform-supported test locale scoped to `LC_CTYPE`, with restoration; retain the Cyrillic assertion rather than skipping it. Add lowercasing and an actual `Button::SetText` CAPS regression under the declared locale. No production casing change is proposed by this diagnostic.
