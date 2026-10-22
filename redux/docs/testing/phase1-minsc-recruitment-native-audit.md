# Independent Minsc recruitment/save/reload audit

The measured **three-party checkpoint → stock Minsc conversation → four-party GUI save → fresh reload** passes independent raw-evidence review. This establishes the bounded native route below, including both Imoen interjections. It does not establish original-engine parity, the interjection-ineligible alternatives, OS pointer input or general conversation compatibility.

Run `20261022T075243Z-minsc-recruitment-072650e1`, result SHA256 `93401ec89b0896ae8c69a846f81314afec75a69af9e62b173fdcd7c4ea8c8e6c`; artifact-manifest SHA256 `cad14881c5aef6ef19d2396aa6ba68cc98be8855c94ddb92143ee7b78fb98252`. Native recruitment PID 788 exited 0 after 160.027s; fresh reload PID 14756 exited 0 after 27.861s. Both distinct nonce-bound launches terminated without timeout or cleanup intervention.

## Actual route and branch evidence

The input is the immutable output of `20261022T054005Z-cell-recruitment-ac33ed70`, not a newly fabricated Minsc setup. Its result/manifest pins, six save files and 741 parent artifact hashes match. The initial party order is protagonist/Imoen/Jaheira; Minsc is a stored NPC with `MINSCA`, talk count 0 and XP 90000. Cell01 is already open with flags 1633; Cell02 is locked/closed with flags 610.

The host observes natural stock AI startup and at least four consecutive idle samples before submitting **one parsed `MoveToPoint` approach command** to `[3909,2753]`. It mirrors the ordinary movement action route; no pointer hit test is claimed. The receipt records **zero host talk, door or dialogue-restart requests**. Stock dialogue begins after approach; a stock transition unlocks/opens Cell02 and starts the second conversation. Both starts retain the same actual Minsc identity and protagonist speaker. Registered response callbacks use `TextArea::SelectAvailableOption`; Continue/End use `Control::PerformAction` with actual capitalization-aware labels.

All 21 ordered branch tuples were independently checked against the actual selected DLG bytes: state strref, local transition, global transition, conditional flags and response prefixes. The measured sequence is:

`MINSCA 0,1,8,20 → IMOENJ 7 → MINSCA 43,32,34,38,39,26 → MINSCA 40,41,42,22,23,10,29 → IMOENJ 8 → MINSCA 13,15`.

At the two conditional states 20/29, selected transitions 40/50 have flags 2 and the actual `IsValidForPartyDialog("Imoen")` condition. The captured eligibility is true, and the next captured participant/state is Imoen in both cases. The false alternatives are source-described but unobserved in this run. Every NPC message matches independently decoded English TLK text, including protagonist gender-token expansion, and occurs once more than in the previous transcript. Numbered visible prefixes and the chosen local values match the DLG; visible response ordering is not inferred from raw transcript container order.

Transition 46's source action payload unlocks/opens Cell02 and restarts dialogue; observed door flags progress 610→609 and Minsc talk count 1→2. Transition 34 queues divided party XP before joining. The observed final XP changes **[90500, 96500,90000] → [91500,97500,91000,90000]**. Source ordering and the final allocation agree, but no intermediate timer sample proves the exact instant of allocation relative to JoinParty. The recruited checkpoint is idle before the ordinary GUI save callbacks.

## Independent binary persistence check

A separate PowerShell/.NET reader decoded GAM actor records, bounded/disjoint embedded CRE ranges, inventory records and 38 physical CRE slots; SAV inflation, area doors/container items; globals and journal entries. It did not call the Python wire decoder to derive the following results:

- Party order becomes protagonist/Imoen/Jaheira/Minsc. There is exactly one actor named `minsc` across party/stored tables, now party index 3 with `MINSCJ`, talk count 2 and XP 90000. Its final CRE SHA256 is `febe54796c45d3a34a42ae27f50e0500ebccd32c66305c448e668c392fc9fd9b`.
- Minsc retains one `MISC84` (Boo), physical CRE slot 18, usages [0,0,0], expired 0 and flags 1. No other party member owns Boo. **The original checkpoint also contains a separate stored `ttminsc` with its own MISC84**; that existing stored item remains unchanged. This is not a whole-GAM unique-Boo assertion.
- Cell02 serializes flags 609, empty key, untrapped and lock difficulty 100. Prior Cell01 remains flags 1633. The Jailkeep Table retains its ten expected non-key items; consumed MISC4B is absent from the table and party inventories.
- Journal entries are exactly 34089, 96383,47519,47518, without duplication. Prior fields are retained; new solved entry 47518 is chapter 1/section 2. The prior Jaheira release global remains 1 without hunt/jerk outcomes.

The seven output save files match the ordinary GUI save and its frozen copy. Fresh reload uses those exact bytes in a new private profile: its independent wire decode equals the frozen output, including Minsc CRE, Boo, XP, doors and full journal fields. Final GAM SHA256 is `31ed55776f08f3ef8b351b3eda8de02cda32dd6926fbb05a0808888d75070b7a`; SAV SHA256 is `ab927d4f5de8a8b707a964d51c806da68360cc5d1771f77c2d8fd4ee1f2d9754`. Reload records one registered load event, eight samples, no movement, dialogue, recruitment or save commands. This is persisted outcome evidence, not a second recruitment.

## Source, provider and preservation binding

Build `20261022T063419Z-candidate-24f35a4e` uses core DLL SHA256 `051c3ea9f1e2d582e62f3b8dad61d46c6fab04a093cd4bd9c8b865c8a920a26b`. The executed external host is `df93e7bb2cd7d0e3be079c708c87c50ddd1613bd4d6a7e731a4f21a52197d548`. Independent checks matched 3508 engine sources, 61 binaries, 5 build-support sources, 77 current/frozen build closure entries, 4 actual compiled sources, 96 frozen driver files and all 781 run artifacts. All 51 sample scene/world pairs were checked for clock/actor identity consistency, monotonic progression and the declared idle conditions.

Both processes' actual `GetResourceStream` provider receipts and copied resource bytes match ten expected resources per process: three DLGs, two scripts, three IDS files, PDIALOG and the exact GemRB gender table. The private `data`/`lang` junction mappings, selected provider-file hashes, English TLK/chitin pins and immutable copied root files match; this includes the wrapper-to-clean-installation path mapping. A provider filename alone was not accepted as content proof. No generic fallback font/table provider is inferred.

Candidate and Phase0 before/after guard JSONs are byte-identical; current protected Phase0 hashes independently match 3500 sources, 50 binaries and 6 fixture files. All input/frozen-save hashes remain intact. Private GamePath guards report only allowed log writes, with linked installation contents **not fully hashed** beyond the individually bound providers. The registered GUI callback route and observed saved files do not establish OS input, exact queue memory or hidden RNG noninterference. Static review of branch 1's BMP confirms readable current text/choices without the old-choice overprint in that selected capture; it is not a complete visual audit or EE typography comparison.

Private independent receipt and reproducible reader: `C:/BGRedux/phase1-local/results/20261022T075854Z-minsc-independent-audit-186e3491/`. Audit result SHA256 `aff5640bb69eeca2f9dafc03948c71f8ccebff8317c2c6a66b1284e36cbda3b0`; reader SHA256 `fc8a7fa5165c3f74808ec3a10fd5e586afb0c1f9eb07f842e73ed95402dd5dca`. No tests, build, native launch, engine or helper edits were performed by this audit. No material evidence-integrity gap was found within the declared route.

