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
