# External Minsc recruitment checkpoint

Coordinator execution on October 22 UTC passes in
`20261022T075243Z-minsc-recruitment-072650e1` (result SHA-256
`93401ec89b0896ae8c69a846f81314afec75a69af9e62b173fdcd7c4ea8c8e6c`).
The 22 focused tests pass, the external host builds, and the complete external
suite passes 368 tests (`phase1-integrated-tests-20261022T0758.log`). Native
recruitment PID 788 exits zero after 160.027 seconds, with all 21 branches,
both Imoen interjections, one approach command and two observed stock dialogue
starts. Zero host talk, door or restart commands are issued. The three prior
party members' XP changes from `[90500,96500,90000]` to
`[91500,97500,91000]`; newly joined Minsc retains 90000. Cell02 opens, Boo and
prior solved quests persist, and an ordinary GUI save produces the exact
four-member file inventory. Fresh reload PID 14756 exits zero after 27.861
seconds with no new gameplay command. Source/binary, Phase0 and input guards
pass. The [independent artifact/wire audit](phase1-minsc-recruitment-native-audit.md)
also passes, including actual provider mappings and all 21 DLG branches. Boo
ownership is scoped to recruited Minsc and party ownership: a separate stored
TTMINSC already carries its own copy in the parent save. The coordinator viewed
the recruited capture showing four portraits and the party experience message;
this selected visual check does not establish complete layout fidelity.

The source-only delivery description below retains its original proposed
boundaries; the executed evidence above supersedes its pending execution status.

`minsc_recruitment_journey.py` implements the separate checkpoint described in `phase1-minsc-recruitment-design.md`. It starts only from the exact measured three-party `054005Z-cell-recruitment-ac33ed70/recruit/frozen-save`; its parent result, complete artifact manifest, frozen GAM/SAV and Phase0 ancestor are revalidated. No licensed game assets are published.

The new native adapter issues one ordinary `MoveToPoint([3909.2753])` command, mirroring `GameControl::CreateMovement`, after four naturally idle samples and two seconds of normal clock progression with observed BD_DEFAI/BDDEFAI startup. It records the parsed action, current/next queues, actual motion, changed leader position and source-defined searchmap range at auto-initiation. It issues zero host talk, door, restart, quest-global, stat, join or spell injections and has no retry/fallback route. The actual endpoint and stock auto-initiation remain to be measured; an unreachable or insufficient route fails at the bound.

The exact 21-state primary route has actual Minsc/Imoen participant checks and fresh NPC sentence occurrences. Only two source-declared conditional skips are accepted: MINSCA20 can jump directly to32 when Imoen is actually ineligible, and MINSCA29 can jump directly to13. All visible numbered prefixes are pinned to the actual DLG bytes and checked before normal `SelectAvailableOption`; Continue/End uses its registered callback with capitalization-aware label checks. The two protagonist token expansions bind the actual bg2ee gender.2da provider, TLK pronouns and captured protagonist sex. The raw resource provider streams are captured and hash-matched, including MINSCA, IMOENJ, MINSCJ, MINSC/MINSCX, IDS and PDIALOG.

Cell02 is opened/restarted solely by the shipped dialogue action chain. The adapter observes the real door and two real dialogue starts, then requires party4/MINSCJ/TalkCount2, unique Minsc removal from stored NPCs, retained Boo ownership, solved47518 and prior47519/journals, and completed queued actions. XP is measured before the final End and after joining: the declared three living prior members must gain1000 each while Minsc retains his prior XP, matching divided3000 before JoinParty. No intermediate allocation timer sample or exact action198 sample is invented.

The GUI-created ordinary save is frozen, has exactly seven files (GAM/SAV/BMP plus PORTRT0..3), and is loaded in a distinct owned process with no extra gameplay command. A separate strict three-/four-party wire decoder checks embedded CRE/table bounds, nonoverlap, complete SAV streams, Minsc membership/dialog/counter/Boo, Cell02/retained Cell01 and quests. Existing two-/three-party helpers are unchanged. Runtime party identity/inventory/XP/journal is bound back to those save bytes.

Build and run validate the complete engine build receipt equivalently to the promoted TextArea runner: full non-redux Git source inventory, complete engine DLL/EXE/import-library inventory, and every current/frozen compiled-support file. The receipt and support sources enter the frozen external closure; checks repeat before launch and in final preservation. Declared candidate paths and imported helper modules must match the candidate source root. Private GamePath wrappers protect the clean game; Phase0, candidate, providers, compiler/CMake, copied inputs, driver and immutable output guards remain enforced. Existing failed results are never reused or overwritten.

The frozen serializer/dialogue helper copy has its sole main renamed before inclusion; neither that legacy main nor the protected GUI/save helper mains are invoked. The running entry point is only `native/minsc_journey.cpp`.

Coordinator commands (use a new output directory and the current source-bound candidate build):

```powershell
$python = 'C:\BGRedux\phase0-local\toolchain\msys64\ucrt64\bin\python.exe'
$tool = 'C:\BGRedux\phase1-local\engine\redux\tools\phase1\minsc_recruitment_journey.py'
$engineBuild = 'C:\BGRedux\phase1-local\builds\20261022T063419Z-candidate-24f35a4e'
& $python -B -m unittest discover -s C:\BGRedux\phase1-local\engine\redux\tools\phase1\tests -p test_minsc_recruitment_journey.py
& $python -B $tool build --project-root C:\BGRedux --engine-source-root C:\BGRedux\phase1-local\engine --engine-build-root $engineBuild --output-dir C:\BGRedux\phase1-local\weapon-query-probes\promoted-minsc-1 --timeout 240
& $python -B $tool run --project-root C:\BGRedux --engine-source-root C:\BGRedux\phase1-local\engine --engine-build-root $engineBuild --host-build C:\BGRedux\phase1-local\weapon-query-probes\promoted-minsc-1\build.json --results-root C:\BGRedux\phase1-local\results
```

Live/reload limits are180/90 seconds, with720/360 timer samples and240 samples per phase. Failed/timeout prefixes and receipts are preserved. The delivery adds22 focused synthetic validator/parser tests, including stale/missing nonce/forced evidence, participant/value-prefix/conditional errors, duplicate commands, absent actual movement, XP/Boo/quest corruption, exact fourth-portrait inventory, binary section overlap/truncated SAV and stale engine/source/support closures. Only source syntax was parsed here; no tests, compiler, host or game were run by the worker. Coordinator review, tests, compilation and actual serial execution are pending.

This is callback/native actor-command evidence, not OS pointer hit testing. Original Minsc parity, hidden RNG purity, whole-world invariance and full Phase1/campaign completion are outside this case. Incidental normal AI behavior can cause a genuine failure rather than authorize a synthetic correction.
