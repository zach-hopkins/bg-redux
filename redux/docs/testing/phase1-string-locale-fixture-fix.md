# Checked locale setup for string casing tests

The standalone diagnostic `phase1-local/results/20261022T053949Z-crt-locale-diagnostic-7f68a26d/result.json` has SHA256 `012a446acc30db7dc2a38ce14bb90f0b9d40b68cb06c15355dc0dbf989ae2261`. Independent read-only review rehashed all five frozen/current source pins, compiler, diagnostic executable, raw child output, import listing and actual loaded UCRT. The raw child JSON equals the observation embedded in the result. Initial and final `LC_CTYPE` are both `C`; each case independently reset to `C`.

| Requested locale | Return/effective locale | Exact Cyrillic uppercase |
| --- | --- | --- |
| `C.utf8` | null return; effective `C` | unchanged, fails |
| `.UTF8` | `English_United States.utf8` | expected units, passes |
| Native empty string | `English_United States.1252` | expected units, passes |
| `C` | `C` | unchanged, fails |

The executable SHA256 is `9ec11f68e1f6991abbfb1d881dcf51a87982d75192e32bc90ba8c340a75dc596`; child JSON `89727570c151c9b1b9ecc7906268f23f23adc2dd2918030c1b8037b2836abf13`; import listing `c3d01c580c1fb3273e0d9a99a5ff226e364e5200c42afb2650161bd2bad26ae2`. The child reports its actual loaded `C:/WINDOWS/System32/ucrtbase.dll`, SHA256 `dedb7611e1abc1ff3852dcac3d4c93a048d729e25b061973b9969f22698f14ca`. The compiler command uses the pinned UCRT64 GCC with GNU++14 and no GemRB linkage. Compile and child both exited0 within their bounds. The earlier failed path-freezing attempt ending `8e16175d` remains a failed preparation attempt, not a native observation.

This establishes an unsupported, unchecked locale request in the retained test on this Windows runtime. It does not demonstrate faulty production Cyrillic casing: the same standard CRT operation produces the exact expected values under the measured native-empty initialization used by `GemRB.cpp`. It does not establish complete Unicode, language-specific casing, GUI rendering or original-game parity.

The change is confined to `gemrb/tests/core/Strings/Test_String.cpp`: a test-local guard captures `LC_CTYPE`, selects checked `.UTF8` on Windows or the existing `C.utf8` on other supported platforms, and restores the previous category even when a fatal assertion returns early. It leaves unrelated locale categories alone. Unsupported selection fails explicitly instead of weakening or skipping the assertion. The exact existing `Закончить`→`ЗАКОНЧИТЬ` assertion remains. The old Apple exclusion remains; Windows MSVC can now exercise the supported alias rather than being excluded. A new `ЗАКОНЧИТЬ`→`закончить` case adds missing non-ASCII lowercase coverage and explicitly checks restoration after the guard's scope.

No production casing code, engine entry point, shared harness or installed locale setting changes. This commit was not compiled or executed by its author. After the coordinator's active guarded run terminates, rebuild an isolated candidate and run `StringTest.StringToUpper:StringTest.StringToLower:StringTest.StringToLowerUnicodeCType`, then the existing full corrected-CWD core command with XML and bounded child cleanup. Retain the previous failed core receipts and any new failure. The standalone diagnostic is not a replacement for these engine assertions. A future actual `Button::SetText` CAPS-path test needs an appropriate GUI fixture and remains separate from this test-locale correction.
