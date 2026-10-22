# Original confirmation option: static binding and GemRB configuration gap

For the pinned BG2EE executable, the supported static mapping of **More Confirmation Prompts / Infinity_GetOption(41,9)** is `[Game Options] Over Confirm Everything`, not `Confirm Dialog`. This follows the original binary's registration, getter dispatch and configuration field accesses; it is not inferred from similar names. A physical toggle/save/relaunch comparison remains unmeasured.

[Evidence](../evidence/phase1-confirmation-option-source-binding.json), SHA-256 `2d07329ac29e118bd3bb5c75070c025bce6191b856e958ae77c3b9547584fac7`, binds the private read-only receipt `phase1-local/results/20261022T103308Z-confirmation-option-source-45542118/result.json`, SHA-256 `f8759ee2f3e51adf211a12e9a75ae78086d456216c8b8df9544099f7d00bc460`. The executable is SHA-256 `b51093a49140b2b8a7c046b4652bb8e535be24ebbc12b1d735e0b94217a14d57`; its bytes are unchanged before/after static analysis. The standard-library source reader pins itself and the objdump utility/commands/output hashes. Objdump disassembles the file; the original executable was never launched. No engine runtime, UI, tests or build ran, and no root/engine/configuration file was edited.

## Static trace, specific to this executable

Addresses below are preferred-image VAs with base 0x140000000, not live ASLR observations:

1. Registration at 0x1403d9dc0 pushes wrapper 0x1403c94d0, then at 0x1403d9dd6 supplies the name Infinity_GetOption (string VA 0x1405b1c30).
2. The wrapper reads its two numeric arguments, puts the first in EDX and second in R8D, and calls 0x1401ed070 at 0x1403c951d.
3. Panel 9 reaches 0x1401ed1ab. The option selector subtracts 8; option 41 indexes the remap at RVA 0x1ed7f4 with index 33, producing jump index 9. The table at RVA 0x1ed7b8 then selects VA 0x1401ed281.
4. That case reads the game object's integer field +0x7dc4 and returns it. The exact instruction bytes are `41 8b 99 c4 7d 00 00`.
5. The configuration reader at 0x14028201c references ASCII Over Confirm Everything (VA 0x1405a0040) under Game Options (0x14058dcb8), calls the same integer configuration reader used for neighboring keys, then stores EAX at object +0x7dc4 (0x140282035). The configuration writer reads +0x7dc4 around 0x14028b6ff and writes under that same key at 0x14028b71a.
6. Confirm Dialog is a distinct string (0x1405a0098), read at 0x1402820be and stored at +0x7eb4 at 0x1402820de; its writer uses that separate field around 0x14028b789/0x14028b7a4. No behavior is assigned to this other setting merely from its name.

This is strong version-specific source/static-image evidence for the binding. It is not a measured live option read, default-value guarantee for other platforms/releases, or a substitute for actual user-toggle behavior.

The preserved private original profile has both Over Confirm Everything=0 and Confirm Dialog=0. Its hash and exact extracted values are in the receipt. Therefore the file alone cannot distinguish which option controlled the observed no-prompt removal; the static chain resolves that ambiguity. Shipped ui.menu maps the feedback control 41/panel 9 to ENABLE_CONFIRMATION_LABEL/HELP, whose English label is More Confirmation Prompts. Its prepared-row callers condition the popup on the option being nonzero and no existing uncastable entry of the same resref. Those conditions remain broader than the measured default/no-prompt case.

## Existing GemRB configuration behavior

- GUIScript.cpp:3955 `SetVar` stores a numeric/None value in the core dictionary; :4053 `GetVar` reads it and returns None for missing entries. A dictionary assignment alone neither creates a supported option consumer nor guarantees persistence.
- Interface.cpp:427–447 selects a gem-prefixed INI from SavePath first, then GamePath, otherwise the original INI. It calls InitializeVarsWithINI; no general original Baldur.lua option importer is present in this path. The two original Lua settings cannot be assumed to enter the GemRB dictionary automatically.
- InitializeVarsWithINI at :2310–2350 iterates keys from resource defaults.ini, with configuration variables taking priority and INI overrides read only for those default keys. InterfaceConfig.cpp:354–356 can put remaining explicit GemRB.cfg keys into numeric variables, but that does not whitelist them for SaveConfig.
- Interface.cpp:2386–2427 SaveConfig serializes the **defaults.ini whitelist**, writing gem-prefixed INI under writable GamePath or falling back to SavePath. Neither Over Confirm Everything nor Confirm Dialog is currently in shared defaults.ini. Adding an arbitrary dictionary value would not add it to this serialized key set.
- GUIOPT.py:342–370 opens the feedback window with two feedback sliders and six checkboxes for Effect Text Level bits 1/2/4/8/16/32 (plus the existing bit-64 adjustment). It does not bind a More Confirmation Prompts checkbox or either candidate key. GUIOPTControls.OptCheckbox supports ordinary bound checkbox controls via SetVarAssoc, including a handler/help text, but no new control layout or localized label binding has been implemented here.
- The feedback Done/Cancel paths currently both close the window. CloseGameplayOptionsWindow (:286–290) invokes SaveConfig, and both gameplay Done/Cancel use that path. The helpers do not provide an evident generic snapshot/rollback transaction. A future option must declare and test its actual Cancel/Done/persistence semantics rather than infer them from button captions.

The current GUIMG/GUIPR source implements unconditional direct charged removal for BG2EE while preserving the previous non-BG2EE charged confirmation. It has no More Confirmation Prompts consumer. Existing successful AFTER stock/control receipts prove that direct path for their measured setup; they do not prove option-on fidelity or rest-at-inn confirmation behavior. Classic runtime behavior remains a separate verification question despite preserved source branches.

## Next decisive validation, not executed here

Use an owned private original profile and ordinary Options→Feedback toggle. Freeze before/after Baldur.lua plus screenshots and the full configuration diff, establish whether only Over Confirm Everything changes, quit normally and relaunch to prove persistence. On a fresh declared fixture with a charged prepared target and no depleted same-resref instance, observe option-on popup/cancel and option-off direct removal. The same-resref depleted-instance preference needs its own explicit case. Keep exact selected resref, charge flags, saved bytes, actions and caller conditions bound; do not infer state from a checkbox image alone.

A future native implementation can reuse dictionary/INI/checkbox mechanisms but requires an explicit default/whitelisted persistence key, localized UI label/help, a BG2EE-only consumer matching the confirmed policy and independent original/native option-on/off/reload/cancel evidence. Those changes and validations were not performed by this source investigation. No global compatibility closure is claimed.
