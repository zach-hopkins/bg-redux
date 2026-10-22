# BG2EE inn option implementation and native validation

October22,2026. Production change `19de56ed5` adds
`BG2EEConfirmation.ShouldPromptInnRest` and calls the existing `RentConfirm`
directly for affordable BG2EE rooms when Over Confirm Everything is zero.
The existing price-error check remains first. Other games retain the prompt,
and optionON retains its existing Cancel/Confirm callbacks. The direct path
clears a stale closed confirmation-window reference before calling the existing
rest callback; it does not add a second gold/rest implementation. Rest-script,
dream and movie behavior is not changed by this policy commit.

Five actual-source callback tests cover OFF direct charge/rest, ON prompt/Cancel,
ON Confirm, Classic prompt retention and insufficient funds before either policy.
The corrected BEFORE fixture has exactly one failing test (OFF still prompts);
AFTER passes all five. The initial BEFORE test used a single mock control for all
IDs, causing an additional harness-only Confirm failure; that log is retained as
`inn-confirmation-policy-before-20261022.log`, alongside corrected BEFORE-v2 and
AFTER logs. Do not classify the mock failure as an engine defect.

## Fresh candidate and general baseline

Candidate `20261022T192339Z-candidate-650b61c7` builds from source19de56ed5.
The build receipt reports all configure/build steps complete, source/support
unchanged during build and protected Phase0 source/binaries/fixture unchanged.
This is a fresh build, not a rewritten receipt for candidatee00bb8b5.

`20261022T192958Z-inn-base-d3fa6872/result.json` passes24/24 import/reload and20/20
GUI/save assertions, no skips, with all candidate/Phase0/input guards. The outer
wrapper intentionally exits1 for compatibility differences. Raw residual counts
are vanilla2/0/24 and GUI449/53. These differ from the preceding e00 counts
0/0/26 and451/55; their changing rows remain unreviewed, not a claimed persistence
improvement. Core CTest is separate from these external checks.

Final source tooling after checkbox correction passes556 tests in35.677 seconds:
`phase1-inn-checkpoint-tooling-1792699134123508300/result.json`, source80484c518.
Earlier556/36.451 and554-test receipts remain bound to their earlier versions.
No new independent worker audit is claimed.

## Preserved native attempts

- `20261022T193713Z-inn-off-first-30c1199f`: rejected. The actual Rent callback
  charges100→99 and advances33343→69343 game ticks, exactly eight game hours.
  The observer then incorrectly requires the rent window to remain open. While
  reporting that Python exception, legacy GUIScript::ExecString treats an
  exception instance as Unicode and aborts; owned PID13628 exits3221226505.
  No output save or end-to-end acceptance is claimed.
- `20261022T194321Z-inn-off-retry-67c7940b`: rejected with a controlled exit and
  preserved traceback/failure capture. Diagnostic-only exception handling avoids
  the legacy renderer assertion and identifies the actual mismatch: gold99,
  option0, no error/prompt, but store closed rather than the assumed open state.
  Production exception handling is unchanged.
- `20261022T194906Z-inn-off-branch-5183c1a8`: passes the bounded OFF rest/save
  probe. Owned PID4356 exits0 in90.053 seconds. Ordinary dialogue, room choice,
  one Rent, eight-hour advancement, gold100→99 and normal GUI save/wire match
  pass. All protected/candidate/input guards pass. This is not complete feature,
  original-parity, store/dream or full-world acceptance.
- `20261022T195450Z-inn-off-reload-16574684`: passes a fresh process load of only
  that frozen output. PID9348 exits0 in27.323 seconds. Initial loaded saved
  gold/party/quest/spellbook wire matches exactly, actual option0 and final gold99
  survive normal idle startup, and no additional rest or save is invoked. Saved
  area/store streams match the exact input SAV members. All preservation guards
  pass; no whole-world purity claim is made for the idle simulation period.
- `20261022T195121Z-inn-on-branch-14a1e19b`: rejected before talking/renting. The
  initial driver dispatched the checkbox's registered callback but not its
  intrinsic mouse toggle; actual draft remained0 and committed option remained0.
  The source setting implementation is not changed to accommodate this fixture.
  The replacement uses the previously validated Button MouseDown/MouseUp route,
  checks draft XOR actual value, then requires draft1 before ordinary Done and
  effective option1 afterward. The failed run and teardown traceback remain.
- `20261022T195552Z-inn-on-mouse-cfaa51db`: passes the bounded native ON ordinary
  setting/Cancel/Confirm/rest/save probe. PID14460 exits0 in117.080 seconds. The
  three prompt/Cancel/request callbacks at steps17,19,21 preserve exact captured
  world state apart from selection; Confirm charges100→99 and advances36000 ticks.
  The normal GUI save matches the final wire. The generated private INI contains
  option1, SHA256`a35121d4e11845e5da91bb344c8198bb729ae8eaf9554b7b8495aa8ee1588783`.
  All candidate/Phase0/input guards pass. Store/dream and whole-world parity
  remain outside this bounded pass.
- `20261022T195820Z-inn-on-reload-b7a2cc76`: passes fresh ON save/config reload.
  PID14740 exits0 in26.803 seconds. The actual UI-generated INI is copied
  byte-for-byte and remains unchanged. Initial saved gold/party/quest/spellbook
  wire matches, live option1 and final gold99 are observed after normal idle
  startup, and no second rest/save runs. All preservation guards pass.

## Explicit observation seam and remaining fidelity work

The new external host has OFF/ON/reload modes. It cannot invoke debug setup
commands; all modes start from the pinned accepted inn checkpoint87848de6 and
its preserved Minsc/Phase0 ancestry. Source/support/compiler/binary and relevant
stock/saved resource bindings remain frozen. Hosts1–4 are distinct preserved
build receipts; later source changes do not rewrite earlier host closures.

The rest runtime temporarily wraps the exported Python RestParty function in its
private process, delegates the original operation once, retains the exact result
and records arguments, gold and time in `rest-call.json`. This is declared
instrumentation, not a production engine change or proven RNG/whole-world
noninterference. The native callback snapshots independently measure the charge
before the wrapper is entered: RentConfirm debits first, so the trace itself
correctly starts at gold99. The trace records arguments18,1,1, successful result,
2400 compressed seconds and **Cutscene=true**. Other callbacks and wire evidence
remain separate from that trace.

Source `Game::RestParty` sets Cutscene true whenever PLAYER1D exists and invokes
PlayerDream; `GUISTORE.RentConfirm` closes the store on that return flag. The probe
therefore requires the corresponding exact branch: store closed for a true flag,
store retained for false. A store-Done callback is recorded only when the window
exists; it is never forced after cutscene closure. This validates current callback
behavior without declaring it faithful to the original. Whether a script actually
started a dream versus merely existing needs a separate matched comparison.

The native log also reports missing RESTINN.mve. Protected original assets contain
`movies/restinn.wbm`, which the original runtime plays. The current LAB build
disables libVLC; movie support and restoration remain explicit fidelity work,
not covered by an eight-hour time/charge pass. The [original OFF/ON reference](phase1-original-inn-confirmation-reference.md)
also retains companion-dialogue/journal differences rather than normalizing them.

The OFF/ON first-execution and both fresh reloads now pass their bounded checks.
Remaining: integrate a repository runner/validator for these currently private
first-execution probes, adding explicit runtime provider/byte bindings for the
newly used restheal/restmov tables, PLAYER1D and relevant rest text/movie resources.
The current inherited closure is bounded and does not certify all rest resources.
Compare actual post-rest store/dream/rest-script
behavior on matched original/native fixtures; preserve movie and broader save
residuals. Continue the higher-priority P1-03 inventory/record information work
after consolidating this slice, carrying these P1-06 blockers forward rather than
declaring them complete. Phase1 and the full inn fidelity requirement remain incomplete.
