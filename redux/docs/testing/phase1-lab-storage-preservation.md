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
