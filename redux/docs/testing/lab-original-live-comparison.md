# LAB original combat observation and paired AI tails

October 21, 2026. This is a bounded observation channel, independent of saving
during combat. It uses an unmodified BG2EE 2.7.3 executable in a private game copy
and a unique private profile. Installed game files and personal saves are not
edited. The private copy appends nonce strings to the TLK and adds four named
fixture scripts; these resource changes are declared instrumentation.

## Executed evidence

Preparation `20261021T230944Z-original-live-6efa5f54` records nonce `E1AEF966`,
executable/TLK/script hashes, final fixture manifests, and private paths. The
launch receipt binds PID 5376 to that executable. `load-boundary.jpg/json` shows
the actual Load Game boundary with the four nonce-labelled cases. Each case has
its own CRE script assignment, preventing a case change from retaining the
previous case's override script. Original stock tail conditions/actions are
retained; controls remove the six weapon queries. Added markers identify SEEN
and selected response ENTER; they do not certify completion of Attack.

Four observed screenshots retain SEEN, the nonce/case/branch ENTER marker and
subsequent attack/hit/miss feedback. Combat saving was not used as the observation
channel. No RETURN marker was captured. The owned original process was stopped
after the last capture; cleanup is recorded. These are explicit operator visual
attestations, not OCR or an original executable memory sampler.

| Case | Original selected branch | Native selected branch | Disposition |
|---|---:|---:|---|
| Imoen stock tail | 115 | 118 | Reproducible branch mismatch |
| Imoen without weapon queries | 115 | 115 | Selected-branch agreement |
| Default stock tail | 307 | 310 | Reproducible branch mismatch |
| Default without weapon queries | 307 | 307 | Selected-branch agreement |

Native run `20261021T232434Z-paired-ai-live-1437dd9a` uses the exact final fixture,
script and TLK inputs recorded by preparation. All four processes complete with
exit 0. Normal-loop action 105 samples bind the native attack target to RDXFOE's
runtime ID; those samples are a stronger native-only observation and must not be
attributed to the original. Native source/binary/fixture preservation checks pass.
This isolates the branch mismatch sufficiently for a Phase 1 predicate task;
it does not establish all AI semantics, timing, DPR or damage equivalence.

## Reproduction and evidence validation

Materialize the licensed private runtime as described in the guest handoff. Run
`tools/phase0/original_live.py` with the pinned UCRT Python to prepare a new
private copy/profile. It prints a unique preparation path. Launch only that
receipt's private executable, confirm the actual Load Game boundary, load each
named case and retain screenshots containing its fresh SEEN/ENTER markers and
combat feedback. Record executable/window identity, UTC timestamp, screenshot
hash, branch and explicit observation limits in a case observation JSON. Inspect
the existing receipts as the schema examples; never reuse their nonce as fresh
evidence. Only one coordinator controls the game at a time.

`original_live_capture.py finalize --preparation PREPARATION --observation OBS`
accepts repeated observation arguments. It validates and freezes each receipt in
a unique result directory, preserving failed captures too. It checks nonce,
case/phase/branch, freshness, executable/window/profile binding, screenshot hash
and image signature, private TLK/scripts/Lua/retained DLL, final CRE assignment
and final fixture manifest. It does not recognize screenshot text automatically.
Thirty-one negative/freeze tests pass; thirteen TLK/stock-tail tests also pass.

Validated captures are `20261021T232721Z-original-live-capture-223a9dc3`,
`20261021T232721Z-original-live-capture-f5e4fedd`,
`20261021T232721Z-original-live-capture-71268361` and
`20261021T232722Z-original-live-capture-df6e47b4`. All paths are under private
`phase0-local/results/`. Exact original target memory, queue completion, hidden
RNG and fully unattended observation remain unproven.

Run `paired_ai_live.py --preparation PREPARATION` for fresh native paired cases
after reviewing the original capture. It rejects fixture/script drift and uses
the existing external GUI host against the frozen core. It does not rebuild the
engine. Preserve preparation, captures, logs and failed runs together.
