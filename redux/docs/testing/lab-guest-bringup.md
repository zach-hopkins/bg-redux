# LAB guest bring-up — October 21, 2026

Guest execution is now independently verified. This continuation runs in
`C:\BGRedux` on LAB as `Lab\labuser`, VMware20,1, Windows 11 Pro build 26300,
12 GiB RAM and six cores. VMware Tools is running; the display is VMware SVGA
3D, driver 9.17.11.3. A Computer Use capture of the guest workspace was observed.
That capture does not establish physical-host input isolation or game rendering.

The fork was cloned into `C:\BGRedux\gemrb` at
`5f0653a672b7d5d4e700379ecb6ab8575caaf9b1`, branch `codex/phase0-audit`.
Its engine paths match baseline `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351`;
published additions are `redux/` and `README_BG_REDUX.md`. Docs and tools were
copied into the outer workspace as required by the existing harness layout.
No engine source or binaries were changed.

## Executed checks

Steam reports BG2EE build 23534562; Baldur.exe reports 2.7.3.0. All 2,324 files
in the historical game manifest match by length and SHA256. Those manifested
files were copied into private `phase0-local/bg2ee-clean`, then independently
hashed again: zero mismatches. This establishes reference-file equality, not
independent Steam depot cleanliness or runtime parity.

Private raw guest receipts:

- `phase0-local/results/20261021T211120Z-guest-preflight-82c3f5d4/`: installed-game hashes and machine/source checks.
- `phase0-local/results/20261021T211208Z-guest-preflight-127a9045/`: independent test-copy hashes and machine/source checks.
- `phase0-local/results/20261021T211139Z-guest-harness-unit/`: initial incomplete setup; 9 tests ran, 11 errors including import/setup errors. Retained.
- `phase0-local/results/20261021T211208Z-guest-harness-unit-game-copy/`: after creating the game copy, 51 tests ran: 46 passed and five errored, plus three class setup errors. Exit 1. All eight errors report missing vanilla fixture or executed historical oracle inputs.

Those initial unit runs used the available bundled CPython 3.12, not the then-missing historical
UCRT64 Python. They are partial harness checks, not the historical 71-test pass,
engine tests or guest native execution. Missing test inputs were not fabricated
or skipped. Preserve both failed runs when transferring the historical evidence.

## Verified private transfer

The user supplied `\\vmware-host\Shared Folders\ReduxBase` and
`\\vmware-host\Shared Folders\ReduxContext`. The base was staged, read-back
verified, copied and destination-verified before the context companion was
overlaid. All 43,358 base entries (6,488,245,518 bytes) and all 18,445 context
entries (4,318,656,805 bytes) match their original manifests.

The full historical base checkout, including `.git`, remains separately under
`phase0-local/transfers/20261021T211457Z/base/BGRedux/gemrb`. Its 3,533 entries
were verified there instead of overwriting the active fork. Inventories of all
3,716 active-fork files, including Git metadata and prior local edits, match
exactly before and after transfer. No files in the active fork were edited by
this transfer. This report update is in the outer workspace only.

Five existing destination files were backed up before base replacement and
seven before context replacement. Backups are under each package's
`previous-destination` directory. Existing guest results and historical host
receipts retain their original provenance. Both original manifests and complete
verified package snapshots are preserved privately.

VMware rejected reads for 57 context members (53 cloud metadata files and four
portraits). Each was recovered from an accessible byte-identical package member,
checked against the destination entry's exact SHA256 and length. Every alias,
original read error and expected digest is recorded; no unresolved files remain.
The initial interrupted copy and first context read failure are retained.

An independent final check applies context precedence to the base manifest:
57,092 installed files / 10,484,814,211 bytes, zero mismatches. The original
historical checkout is accounted for separately as described above. The four
preserved engine/test binaries and all 45 plugins are covered by these checks.

Private receipts under `phase0-local/transfers/20261021T211457Z/`:

- `result.json`: sequential package verification, destination counts and fork preservation.
- `base/transfer-manifest.json` and `context/context-manifest.json`: original manifest bytes.
- `base/destination-map.json` and `context/destination-map.json`: per-member destinations and copy actions.
- `context/exact-hash-recoveries.json`: all 57 exact-content alias recoveries.
- `final-composed-verification.json`: independent final base-plus-context check.
- `fork-before.json` and `fork-after.json`: complete active-checkout hash inventories.

The restored UCRT64 Python 3.14.8 ran all 71 harness tests on LAB: 71 passed,
zero failures/errors, exit 0. The fresh receipt and full log are under
`phase0-local/results/20261021T213204Z-guest-harness-unit-restored/`.
These are harness tests, not native engine execution. The earlier failed guest
runs remain intact; no fixture was substituted with a new save.

## Completed native continuation

External hosts were rebuilt on LAB; capabilities, vanilla import/reload and GUI/save
have fresh results. See [native validation](lab-native-runtime-validation.md) and
[Phase 0 release](../PHASE0_RELEASE.md). The final consolidated run executes all
151 harness tests and both native suites, preserving known compatibility differences.
Engine source/binaries and the original fixture remain unchanged. Physical input
isolation is user-confirmed. VM snapshots are optional under the user's explicit
amendment and are excluded from acceptance; no snapshot was created.

`tools/phase0/guest-preflight.ps1` repeats the guest, source and game-file checks,
writing unique private receipts. A successful exit means those checks passed;
it explicitly leaves runtime, transfer integrity and migration acceptance false.
