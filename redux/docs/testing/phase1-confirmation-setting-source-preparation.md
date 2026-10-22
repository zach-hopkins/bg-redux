# Persistent BG2EE confirmation setting: source preparation

This change adds a localized BG2EE Feedback checkbox and a real defaults-INI persistence key, plus a prepared-removal policy helper. It is source-only preparation: tests, builds, runtime settings save/relaunch, original physical option-on behavior and consumer integration are not yet validated. GUIMG/GUIPR are intentionally untouched because their integration is owned separately.

## Configuration and control

`[Game Options] Over Confirm Everything = 0` joins shared defaults.ini. Interface::InitializeVarsWithINI iterates this whitelist, loading the configured INI value unless an explicit GemRB.cfg dictionary value already has priority. Interface::SaveConfig serializes this same whitelist into the gem-prefixed INI under writable GamePath, falling back to SavePath. This is not merely a SetVar assignment, and it does not import or rewrite original Baldur.lua. Confirm Dialog is a separate option and is not used.

Default zero preserves the already measured native direct-removal setup and matches the pinned original private profile. It is a declared compatibility default, not a claim about every original release/platform's factory default. An absent key uses zero; no Reset button or general reset implementation is added. Explicit configuration keeps the existing engine precedence rules. Existing SaveConfig atomicity/error-reporting limits remain; this change does not redesign its writer.

Only BG2EE Feedback initializes the existing unused GUIOPT window-9 row: checkbox 38 at (235,258,44,44), buddy 39 and label 0x10000028 at (45,243,180,59). The CHU supplies the font and placement; no licensed asset is changed. The label and contextual help use TLK 102476/102477, respectively. English is “Enable Confirmation” and the full localized equivalent explains prepared-spell and inn-rest confirmation. Both references are nonempty in all 12 installed locale TLKs; [source evidence](../evidence/phase1-confirmation-setting-source-preparation.json) binds their hashes and the CHU. There is no English fallback, Lua interpreter, or language-dependent truncation. Other game types retain their existing Feedback handlers and do not access these added controls.

The original Lua label “More Confirmation Prompts” has no exact English TLK entry; this control deliberately uses the shipped localized equivalent. The help includes inn-rest behavior, but **no inn-rest consumer is implemented in this slice**. That advertised behavior must be implemented and measured separately before treating the full original option as complete.

## Done, Cancel and escape

BeginFeedback copies the actual option into a nonpersistent draft checkbox variable. Done publishes its Boolean value and calls GemRB.SaveConfig before closing. A reported save failure restores the previous dictionary value and leaves the dialog/draft open. Cancel, including its existing MakeEscape binding, discards the draft and closes without changing or saving this option. Closing by another route cannot publish the draft; reopening overwrites any stale draft from the real option. The draft is absent from the persistence whitelist.

This narrow transaction applies only to the new setting. Existing sliders/Effect Text Level controls still update their actual variables immediately; their old Cancel behavior is not rewritten. Done's existing global whitelist writer can also persist those current legacy values. Gameplay Done/Cancel and their existing SaveConfig behavior remain unchanged. This intentional new-option Cancel behavior is not claimed as measured original Cancel parity.

## Consumer contract, not yet wired here

`BG2EEConfirmation.ShouldPromptPreparedRemoval(pc, spelltype, level, resref)` returns true for non-BG2EE without querying the setting/page, preserving existing Classic charged-prompt behavior. For BG2EE it returns true only when the option is nonzero and the actual page has no same-resref memorized record with Flags zero. Comparisons are case-insensitive and inspect the requested actor/type/level; the helper performs no mutation, unmemorization, save, action or RNG operation.

The intended integration retains the caller's charged and spontaneous eligibility checks:

```python
if ms['Flags'] and BG2EEConfirmation.ShouldPromptPreparedRemoval(pc, spelltype, level, ms['SpellResRef']):
    # existing confirmation callback
else:
    # existing ordinary removal callback
```

This Boolean API decides whether to prompt; it does not choose which duplicate record to remove. Original depleted-same-resref removal preference, selection identity and prompt cancel/save outcomes still need explicit native/original cases. Option-on is source-supported by shipped ui.menu plus the version-specific static 41/panel-9 mapping in [the binding investigation](phase1-confirmation-option-source-binding.md), not independently observed through an original physical toggle. No universal original or Classic runtime parity is claimed.

## Prepared validation

Fifteen unexecuted tests use fake APIs to cover missing/off/on options, depleted same/other refs, case, nonzero Flags, actor/page access, Classic preservation, localized row binding, Done on/off, Cancel, failure rollback, stale-draft reopening, game gating, defaults whitelist persistence and GUIOPT handler wiring. They do not write a real INI or initialize the engine.

Coordinator command from the integrated engine checkout:

```powershell
& C:/BGRedux/phase0-local/toolchain/msys64/ucrt64/bin/python.exe -B -m unittest discover -s redux/tools/phase1/tests -p test_bg2ee_confirmation_setting.py -v
```

After review/integration, obtain a fresh coherent source/build receipt and run ordinary Options→Gameplay→Feedback checkbox toggles, Done/Cancel/escape and fresh-process config reload in a private game/profile. Then measure explicit option-off direct removal, option-on prompt/cancel/confirm, same-resref depleted cases and unaffected other books/games without synthetic success markers. Preserve real INI before/after bytes and process ownership. The original option-on physical toggle and inn-rest path remain separate required reference work.
