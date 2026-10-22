# Original wizard confirmation and depleted-first reference

The owned original BG2EE 2.7.3.0 session `20261022T105910Z-original-confirmation-installation-19dc70e7` provides bounded physical-UI evidence for the confirmation option and same-resref depleted preference. Independent GAME/CRE parsing, screenshots, configuration and preservation checks agree. [Compact evidence](../evidence/phase1-original-confirmation-option-independent.json) binds the private standard-library reader and all raw receipts; no project decoder or validator was imported.

## Physical option and charged-only target

The private profile was explicitly seeded with both Over Confirm Everything and Confirm Dialog zero. The off-screen capture and operator record show ordinary Options→Gameplay→Feedback, then More Confirmation Prompts off→on and Done/Done. Frozen Baldur-option-on.lua records Over Confirm Everything=1 while Confirm Dialog remains zero. This operationally supports the earlier [version-specific static mapping](phase1-confirmation-option-source-binding.md); it is not a factory-default claim or a fresh-process config-load proof.

With Imoen's level-2 SPWI213 charged and no depleted same-resref copy, an ordinary prepared-icon click opens the Remove/Cancel modal. Cancel leaves the observed count 3/3; Remove changes it to 2/3. Selecting the known name shows its description without changing 2/3; the separate Memorize button adds the depleted copy. The icon shortcut also adds a depleted copy in the later mixed setup. Those are measured original routes, distinct from merely displaying icons.

## Four independent serialized boundaries

The independent bounds-checked parser reads the two-party GAME embedded CRE known/page/memorized tables. Known order, page/type/level identities and both slot counts remain exactly canonical in all four saves. Level-2 memo order and charge flags are:

| Frozen ordinary save | Serialized memorized entries, in order |
| --- | --- |
| 000000026-a / frozen-depleted-save | SPWI214 ready1, SPWI215 ready1, SPWI213 ready0 |
| 000000027-b / frozen-depleted-removal-save | SPWI214 ready1, SPWI215 ready1 |
| 000000028-c / frozen-mixed-save | SPWI213 ready1, SPWI215 ready1, SPWI213 ready0 |
| 000000029-d / frozen-mixed-removal-save | SPWI213 ready1, SPWI215 ready1 |

Each frozen folder exactly matches its actual GUI-created profile save, including file sets and hashes. Pairwise comparison shows only the depleted SPWI213 memo row removed; all other spellbook rows/order/flags/pages remain identical within each pair. This independently confirms target identity and surviving charge state rather than trusting 3/3→2/3 text alone.

For the mixed case the operator reloads HarnessInput within the same process, confirms removing Strength, then clicks the known Cloud icon to add a depleted copy. Captures show three separate prepared icons: dark Cloud, bright Cloud, Web. The recorded physical click at (205,733) selects the bright Cloud. No modal is observed; count becomes 2/3, the bright Cloud remains and the dark one disappears. The wire pair proves that the ready SPWI213 survives while its depleted copy is removed. This demonstrates depleted-first redirection for this measured mixed pair, not merely suppression of confirmation. It does not prove a tie-break among multiple depleted copies.

## Source relationship and next API boundary

The independently extracted shipped ui.menu hashes to `7987e9d38c9a1d8f4df949d880f260ad5a76dd623d08c7e7be6f0f6c8f2931fe` in pinned Patch2.bif. At 8185 the caller prompts only if no same-resref uncastable entry exists and option 41/panel 9 is nonzero. Its no-prompt branch at 8188 still passes currentBottomSpell to unmemorizeMageSpell; line 7810 maps that slot to its memorizedIndex. The exact original binary redirection mechanism was not traced. The related findMemorizedUncastable/source animation search scans for a depleted same-resref entry; it does not alone prove the engine's complete selection policy.

A Boolean ShouldPromptPreparedRemoval helper is therefore insufficient if its consumer continues to remove the clicked charged index in this mixed case. A future shared resolver should return a validated original memo index plus the prompt decision, preserving selected resref/type/level and preferring an observed depleted same-resref entry before mutation. Keep Classic behavior and spontaneous restrictions separate. Add negative/native cases for wrong resref/level/charge/index and explicitly measure any multiple-depleted tie-break rather than assuming universal original ordering. No production/helper change is made by this audit.

## Provenance and limits

All 58 coordinator-manifest files were rehashed, including 16 screenshot/metadata pairs and four frozen saves. Metadata binds the exact private executable/window title; selected option/modal/depleted/mixed images were independently viewed. The six canonical and private input files, nine private prelaunch root files, nine clean-root hashes and all 2457 clean-source inventory entries remain unchanged. The private executable is SHA-256 `b51093a49140b2b8a7c046b4652bb8e535be24ebbc12b1d735e0b94217a14d57`; private engine identity/Steam rename are declared preparation changes, and there is no override folder. Owned PID 17348 matches the launch receipt and exits normally with code zero. The full private audit hashes 59 artifacts including verification.json; source archive content is not universally hashed.

Compared with canonical input, every saved boundary also has SPWI102 and SPWI408 charge flags 1→0 on Imoen's other pages. These exact deltas are preserved in the evidence, consistent with the operator's reported natural Armor/Stoneskin actions; this audit does not independently trace those action causes. No whole-world, AI or RNG purity is asserted. Absence of a transient modal relies on the operator's physical-input observation together with captured frames and saved charge identity.

This is original wizard evidence from one owned process. There is no eligible priest case, inn-rest case, original fresh-process reload or universal confirmation/default/reset claim. No tests, compiler, native/GemRB or original-game process was launched by the audit; all earlier provisional/private receipts remain preserved.
