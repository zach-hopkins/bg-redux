# LAB evidence storage preservation

During the corrected candidate's two-resolution menu run on October 22 UTC, C: fell below 70 MB free. The coordinator used reversible NTFS `compact /C` compression on completed evidence and an older rejected build's generated object files. No files were deleted, moved or logically edited. The running menu scenario subsequently passed both resolutions and every preservation guard.

Verification retains exact content identity for:

- 838 BMP files from five completed runs, checked against their existing artifact hashes or the original game-copy manifest.
- 234 object files from rejected candidate `20261022T050338Z-candidate-2f06ed29`, checked against an explicit pre-compression size/hash inventory.
- 2,825 manifest-pinned JSON/log/text files from four completed menu runs, hashed before and after compression.
- A further 1,118 generated object files from five completed archived candidate builds (`1c6316a3`, `e825e411`, `58c2995e`, `9aa69cd5` and `df3a5c5e`). Complete file names, lengths and SHA-256 inventories match before and after compression, and their build receipts remain unchanged. The current `24f35a4e` build was excluded.

The recursive BMP operation also reached shared German/Spanish language override BMPs through old private-game directory links. Their logical bytes match the original game-copy manifest. Active candidate source/binaries and the current capture directory were not compression targets. Compression attributes and physical allocation can change; the evidence checks establish unchanged logical content, not identical filesystem allocation metadata.

Private receipts are `phase1-local/results/storage-compression-verification-20261022T0654.json` and `phase1-local/results/storage-text-compression-1792652466705247800/result.json`. The former retains two failed verification-preparation assumptions: linked BMP coverage and mixed historical manifest formats. Neither was a byte-hash mismatch. Compression logs, the object inventory, and both verification scripts remain beside the other private LAB tooling/results. Storage remains finite; preserve all results and check headroom before another full build or large capture batch.

The additional archived-object pass is recorded in `phase1-local/results/storage-archived-objects-1792653301889028600/result.json`, with its script `phase1-local/compress-completed-build-objects-20261022.py`. This also compresses in place without deletion or movement; engine DLLs and executables are excluded.

After the promoted fifteen-case TextArea run completed, another 276 manifest-pinned text files (35,309,971 logical bytes) were compressed and verified byte-for-byte. Receipt: `phase1-local/results/storage-promoted-textarea-compression-1792654781756124100/result.json`. The operation required the complete case inventory and all owned process terminal receipts before starting.

A later pass verifies 962 completed b49-menu/Minsc text files (258,381,977 logical
bytes) before/after compression in
`storage-completed-b49-text-compression-1792658592009211800/result.json`.
Two unsuccessful preparation attempts are retained: recursively treating a frozen
parent manifest as a local inventory, then assuming the outer menu wrapper had a
top-level manifest. Neither attempt began compression. The corrected operation
uses the actual native menu manifest and top-level Minsc manifest explicitly.

After the coherent b49 engine build completed, its 234 generated objects and the
separate Phase1 before-build's 231 generated objects were also compressed in
place with exact before/after name/length/hash equality and unchanged build
receipts. Runtime DLLs/executables and Phase0 files were excluded. Receipt:
`storage-completed-engine-objects-1792659009746664400/result.json`. This later
operation includes b49 objects that were explicitly excluded from earlier passes;
it changes allocation only, not compiled object contents.


A further 681 completed spellbook evidence text/BMP files were compressed and
verified with unchanged names, lengths and hashes. Receipt:
`storage-completed-spellbook-evidence-1792660180936283600/result.json`.
New spellbook runs use the compressed directory
`results/compressed-spellbook-20261022`; individual files inherit compression.

The archived-binary preparation attempt
`storage-archived-phase1-binaries-1792660390559727500/result.json` failed a
historical receipt hash check before any compression. Its failure is retained;
it does not establish that those historical binaries match that receipt.
A separate verified selection contains only completed archived builds
`20261022T012223Z-candidate-9aa69cd5` and
`20261022T051113Z-candidate-df3a5c5e`. All 122 receipt-pinned binary/support
files matched before compression, and their exact lengths/hashes and both build
receipts matched afterward. Receipt:
`storage-archived-phase1-binaries-1792660672394588700/result.json`.
Phase0 and the current b49 runtime build were excluded. No files were deleted,
moved, or changed in logical content.


A third receipt-matching archived build, `20261022T003854Z-candidate-58c2995e`,
has 61 additional binary/support files verified before/after compression in
`storage-archived-phase1-binaries-1792660996350160200/result.json`.
The oldest archived build (`1c6316a3`) instead has 60 preexisting historical
receipt mismatches. Its **actual current bytes** were independently inventoried
and preserved exactly during a separate compression operation; this does not
certify that historical build's coherence. Its historical receipt also remains
unchanged: `storage-historical-build-1792661127689289400/result.json`.

A further 199 previously uncompressed binary/object files in the completed
Phase1 before-build and failed `2f06ed29` build were inventoried and compressed,
with exact actual before/after lengths/hashes and unchanged receipt files:
`storage-reference-binaries-1792661210670941900/result.json`. This storage
operation does not promote the failed build or claim historical receipt
coherence. The current candidate and Phase0 were excluded from these targets.


After both spellbook BEFORE runs were terminal, the completed b49 candidate's
61 receipt-pinned binary/support files were compressed with exact hashes and
lengths unchanged, as was its receipt:
`storage-archived-phase1-binaries-1792661421165600900/result.json`.
This changes physical allocation only; all earlier binary identity pins remain
valid. The builds parent directory now requests inherited compression for new
builds, without recursively changing existing files.

A final completed-result BMP pass skips every directory junction/symlink and
hardlinked file. All 2,690 previously uncompressed BMPs (1,671,673,914 logical
bytes), plus preexisting result/artifact receipt hashes, match before/after:
`storage-completed-result-bmps-1792661483761551500/result.json`.
No native session was active. This recovered headroom for a fresh build while
retaining all evidence in place; about 2.27 GB was free afterward.


The next full candidate build completed, but baseline run
`20261022T093528Z-spellbook-native-baseline-08493d1d` exhausted C: during GUI
evidence writing. Its raw result remains failed, including incomplete files.
A separate UTF-8 recovery check proves protected Phase0 and candidate byte
inventories still equal their pre-run snapshots:
`disk-exhaustion-recovery-utf8-1792662483858653400/result.json`.
The earlier recovery reader used the Windows default encoding and misdecoded
Unicode fixture paths; its failed receipt is retained separately.

Windows COMPACT LZX was explored against an archived DLL. The pilot's exact
bytes/receipt remain equal (`storage-archived-lzx-pilot-1792661807128431900/result.json`);
a later allocation query reports 54,071,296 allocated bytes for 270,637,879
logical bytes. The follow-up batch failed while writing its initial inventory
under disk exhaustion, before its compression loop:
`storage-archived-phase1-lzx-1792661841435548300/result.json`.
COMPACT's quiet/continue mode and exit zero alone do not prove reclaimed space;
logical before/after hashes establish preservation, not an allocation result
for every requested file. Failed emergency compression attempts are retained.

Recovery then atomically replaced exact duplicate archived bytes with NTFS
hardlinks. All original file paths remain readable with identical lengths and
SHA-256 values; this does not preserve independent physical allocation/inodes.
One archived external-host pair is recorded in
`storage-identical-host-link-1792662070508501600/result.json`.
An initial 1,112-file cache inventory/993 duplicate pairs is recorded in
`storage-identical-archived-caches-1792662192663312800/result.json`.
The complete pass inventories 22,451 closed-session cache PVRZ files and shares
21,199 duplicate paths, with all logical bytes verified afterward:
`storage-identical-completed-caches-1792662245010672100/result.json`.
All directory junctions/symlinks are skipped; engine sources/binaries, Phase0,
original assets and live sessions are excluded. No logical result file is lost.
About 9.5 GB was free after that pass. The 258 shared cache inodes were then
marked read-only and rehashed to prevent accidental writes across aliases:
`storage-shared-cache-readonly-1792662832877889600/result.json`.
Archived profiles must remain archived; all new tests use fresh private caches.

A later pass ran only after all owned native sessions were terminal. Receipt
`storage-identical-completed-caches-readonly-1792669011654661600/result.json`
pins 26,674 completed cache files, shares 4,222 additional identical paths,
and verifies the retained bytes and read-only aliases. Free space increased from
1,842,335,744 to 4,864,077,824 bytes. No result path was removed. New tests continue
to use fresh private caches; archived caches must not be reused for writes.

Before the Feedback-row rebuild, completed historical spellbook builds 5a60a03d,
3f8cf4a0 and e52511e1 had their generated object files losslessly compressed.
Receipt `storage-completed-spellbook-objects-1792672437951426500/result.json`
verifies all 702 object files and unchanged build receipts before/after; no file
was deleted or moved. The then-current ced237a2 build was explicitly excluded.

After ced237a2's native journeys were terminal, receipt
`storage-completed-help-objects-1792672734147921200/result.json` similarly verifies
its 234 generated objects before/after compression; current e00bb8b5 was excluded.
While the subsequent e00 menu run was active, its entire result subtree
`20261022T124438Z-row-menu-run-c59be7e9` was excluded from a closed-cache pass.
Receipt `storage-closed-caches-excluding-row-menu-1792673168282717600/result.json`
pins 28,460 completed PVRZ files and shares 1,786 identical paths, preserving all
bytes and marking new shared aliases read-only. Only completed caches were
eligible; the active result was never traversed. Free space after that pass was
2,204,131,328 bytes. All archived cache profiles remain unsuitable for reuse.

The results parent now requests inherited compression without recursion. A
baseline retry nested in the longer compressed-container path failed while
copying a 273-character Windows destination, before the GUI stages began.
That failed run is retained under
`compressed-spellbook-20261022/20261022T094643Z-spellbook-native-baseline-f2dae382`.
The separate short-name run `20261022T094904Z-sb-base-4565dad5` passes all 44
baseline assertions and preservation guards while keeping its compatibility
differences explicit. See the [fresh baseline audit](phase1-heading-policy-fresh-baseline-audit.md).
