# Stock Jaheira dialogue, journal and fresh-process reload journey

Coordinator checkpoint: **12 focused tests and the 272-test integrated tooling
suite pass**. Corrected ordinary run
`20261022T042747Z-jaheira-dialogue-30a50511` passes both processes: one talk
request, all eleven displayed branches and seventeen registered operations,
GUI-created save, then fresh-process reload with no new talk request. Saved
TalkCount is 1, journal34105 is uniquely present in section1/chapter1, the party
remains two and Cell01 remains closed. Input/candidate/Phase0 preservation checks
pass. The talk/reload processes exit zero in 78.352/18.320 seconds. The first direct
selection run and separate debugger trace expose a
[public UpdateState reentrancy defect](../compatibility/phase1-textarea-update-state-reentrancy.md).
The ordinary selector rerun `20261022T042240Z-jaheira-dialogue-946305e3`
successfully dispatches the first response, then fails the external raw-label
guard at Continue. `Button::SetText` applies the shipped capitalization flags;
the corrected adapter records raw TLK label, flags, expected transformed label
and actual label and requires exact agreement. Fresh `jaheira-label6` build and
the successful run above execute this correction. Failed builds/runs remain preserved. This
separate adapter changes no engine, existing helper, resource or saved fixture.
Original-engine parity remains unobserved.

## Exact starting contract

Use only the protected stock save `phase0-local/fixtures/original-bg2ee-20261020/GemRB`, copied intact into a fresh private profile. Its original GAM SHA256 is `d8da451c8765f209cadbbab8a274be0e218c17d2b4718b8b43b76fb10b030414`; SAV is `4c5953f573ebed530c4718c0e960ca388bf3ba2897babf2fa666f3658de6ebfb`. The baseline preflight and full protected inventories bind all six fixture files. No synthetic actor, variable, quest marker, dialogue state or area edit is permitted.

| Guard | Required stock identity |
| --- | --- |
| Party/area | Leader and Imoen; two members in AR0602; leader selected |
| Original positions | Leader (3741,2801), Imoen (3720,2826), Jaheira (3898,2676) |
| Jaheira stored NPC | GAM NPC index1, record6888; embedded CRE offset16180, length3008; script name `jaheira`, dialog `JAHEIRA`, TalkCount0 at BG2 NPC record+0xe0 |
| Jaheira CRE SHA256 | `e85c3c724407f9f6cd65b055fd1e3922133c7df67fa691bd4b43f8639b8349fb` |
| Saved AR0602 SHA256 | `11fe9bce9ecce5d75ef05f6947da9d872b58a868898ba0935307b7ea8c4914b5` |
| Cell01 | Saved door index7, flags1634, closed; remains closed throughout |
| Key | No MISC4B in party inventory; leader inventory empty and Imoen has only IMOENHP1 in the protected wire input |
| Journal | Existing refs34089 and96383; no34105 entry |
| Shipped JAHEIRA DLG | 8,272 bytes; SHA256 `b121dc6d804e52e431c15a1d2dd372b5242f518a31d925ce403c3e633882bbc9` |
| English dialog.tlk SHA256 | `9e685225ff3c3436a8a35fa7022550620d24a92efe35436a062c02955d9f0952` |

The original source is never the runtime save folder. Both processes use their own private GamePath wrapper, empty ModPath, profile, cache and captured launch nonce. The exact original fixture is checked before the first launch; ordinary saved output is copied, hashed and frozen before it becomes the second process's sole load input. SaveAsOriginal=1 and bounded GAMEV2.0/SAV/CRE/ARE parsers verify the real saved TalkCount, NPC/dialog identity, door and journal without assuming complete binary round-trip equality.

## Ordinary route and required effect

After ordinary load-control dispatch, let stock AI start naturally. Record current and pending actions, movement and full world snapshots on each startup sample. Require at least two game seconds and four consecutive idle samples for both party actors and Jaheira, with no dialogue active. `Scriptable::GetNextAction()` is a const front/empty observation; the adapter never pops or clears actions. Only then send **one** `GameControl::TryToTalk(leader,Jaheira)` request. The production route queues NIDSpecial1 with normal target/distance checks. Do not teleport, repeat the request, cancel stock startup actions, unlock the cage or inject dialogue globals.

| State / NPC strref | Global transition / local index | Actual stock control route | Next state |
| --- | --- | --- | --- |
| 0 /899 | 4 /4 | Registered TextArea Select, response904 | 47 |
| 47 /20128 | 94 /0 | Continue | 5 |
| 5 /909 | 9 /0 | Continue | 51 |
| 51 /20142 | 98 /0 | Continue | 8 |
| 8 /912 | 12 /0 | Continue | 49 |
| 49 /20132 | 96 /0 | Continue | 50 |
| 50 /20136 | 97 /0 | Continue | 9 |
| 9 /921 | 14 /1 | Registered TextArea Select, response923 | 58 |
| 58 /20176 | 105 /0 | Continue | 59 |
| 59 /20177 | 106 /0 | Continue | 14 |
| 14 /945 | 45 /0 | End | Dialogue ends |

State0 requires `NumTimesTalkedTo(0)` and leader party slot0. State9's chosen response additionally requires closed Cell01 and no MISC4B. All selected transition action lists are empty. Transition45 has flags88: final, journal and unsolved, adding journal34105 in Unsolved section1. The expected effects are therefore TalkCount0→1, journal count2→3 with exactly one34105 entry in chapter1, party still2, Jaheira still outside the party and Cell01 still closed. JaheiraJerk and JaheiraReleased must remain zero/absent. Existing journal entries must retain their complete captured fields.

Response selection uses public `TextArea::SelectAvailableOption`, the same
selector entry used by number keys and mouse selection, reaching the registered
Select callback. The two guarded states expose visible indices 4 and 1; exact
numbered response text is required before selection, and both the entry method
and visible index are recorded. Visible index is not generally interchangeable
with local transition index. Continue/End require visible, enabled stock
window9/control0 and label9372/9371 transformed by actual Button capitalization
flags, then perform the registered button action. Actual dialogue speaker/target
IDs are sampled through DialogHandler's public getters. Each accepted branch
records focused/world snapshots, screenshot, NPC/response strrefs, transition
mapping, text evidence and callback sequence.

After dialogue ends, use GUIOPT save control, GUISAVE new-row control, actual name ValueChange and GUISAVE confirmation callbacks. Require a unique `Redux Jaheira Dialogue` save inside the private profile, without overwriting the copied input. Freeze its exact file manifest, verify saved NPC TalkCount1 and journal34105, then launch a **different owned process** with that frozen save copied intact. The reload stage repeats natural startup/idle observations and verifies the persisted identity/counter/journal/door/party without another talk request or resave. The first process has a planned17-event sequence; these are expected counts, not executed evidence.

## Observation boundary and failure policy

TextArea::QueryText returns the selected response or empty while options exist. The adapter instead scans the message widget's bounded public geometry using View::SubviewAt, recognizes the pinned GCC RTTI names for TextContainer and TextArea::SpanSelector::OptSpan, then reads public inline Contents()/Text() accessors. TextArea.h explicitly defines OptSpan as deriving from TextContainer; TextContainer.h defines the corresponding public accessors. No private member offset, engine export, renderer change or linked replacement implementation is introduced. This is a **toolchain-specific external observation**, with no renderer/private-layout portability guarantee. If no recognized text is reachable, no branch is accepted; bounded waiting retains runtime type/text diagnostics and ends in failure.

State labels are inferred from sequential, independently pinned English TLK text observed in those actual containers; **DialogHandler's private state index is not sampled**. Each NPC text occurrence must increase relative to the immediately preceding callback checkpoint (or pre-request transcript). The validator checks that continuity and independently decodes the pinned TLK, so stale prior text or a self-declared invented expected string cannot satisfy the next branch. Read-only inspection confirms the exact three expected RTTI name strings occur in the candidate DLL; live reachability is still unobserved. Screenshots remain necessary native evidence. Geometry scanning does not dispatch a pointer event and establishes no OS pointer/hit-target fidelity or original-engine parity.

Missing callbacks, wrong participant/branch/response, repeated requests, forced-state flags, fabricated counter/journal, duplicate entries, changed door/party/key, incomplete natural readiness, stale nonce/timestamps, inaccessible text or mismatched wire persistence fail. Full helper and relevant source/header closures, compiled translation units, compiler, CMake cache, candidate binaries/source, protected Phase0 and private wrapper inventories are pinned. Before/after captures and failed receipts are retained under unique output directories; no historical result is relabeled. Existing protected serializer/startup/helper sources are frozen inputs and remain unchanged. Broad world equality across running AI is not required; relevant state, prior journal fields, save boundary and reload persistence are explicit checks.

## Coordinator invocation

After integrating this source-only commit and outside another native guard:

```powershell
$dialoguePython = 'C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe'
$dialogueTool = 'C:/BGRedux/phase1-local/engine/redux/tools/phase1/jaheira_dialogue_journey.py'
$dialogueRoots = @('--project-root','C:/BGRedux','--engine-source-root','C:/BGRedux/phase1-local/engine','--engine-build-root','C:/BGRedux/phase1-local/builds/20261022T012223Z-candidate-9aa69cd5','--timeout','240')
$dialogueBuild = 'C:/BGRedux/phase1-local/results/' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '-jaheira-build-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
& $dialoguePython -B $dialogueTool build @dialogueRoots --output-dir $dialogueBuild
& $dialoguePython -B $dialogueTool run @dialogueRoots --host-build "$dialogueBuild/build.json" --results-root 'C:/BGRedux/phase1-local/results'
```

Build/run timeouts are bounded to1–300 seconds per owned operation; the native host separately bounds timer callbacks to1,000. The new ten test methods cover valid schema, wrong/missing branch callbacks, repeated/forced requests, stale nonce/time, fabricated counter/target/journal, duplicate journal entry, wrong door/party/key, queued-action readiness and stale/invented text. They have not been executed by this worker. Buildability, actual message-container reachability, normal approach/branch completion, GUI save success and fresh-process reload persistence remain unverified until coordinator execution.
