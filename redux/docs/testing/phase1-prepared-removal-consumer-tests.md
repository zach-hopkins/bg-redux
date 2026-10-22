# Prepared-removal consumer regression tests

Source-only test adaptation for the coordinator's `BG2EEConfirmation` consumer integration; no production script/helper is edited here. The previous three-method callback fixture assumed all BG2EE charged removal was direct. That assertion is superseded by seven methods executing the actual conditional AST, actual helper implementation and actual `OnMageUnmemorizeSpell` / `OnPriestUnmemorizeSpell` function bodies against a fake mutable page.

Both books cover Classic versus BG2EE, option off/on, charged/depleted clicked entry, same-resref depleted copy and unrelated depleted copy. The actual controller tests require the native removal call's precise preferred index and resulting retained charged copies; Classic retains the clicked index. They also require invalid EE indices to produce no native removal or animation, and an already-open confirmation callback to reevaluate the live page after a depleted copy appears. A fake native operation removes only the index actually supplied; expected retained rows and original identity are independent assertions.

The focused heading fixture supplies only a `ShouldPromptPreparedRemoval=False` stub because it owns heading/count lifecycle, not policy behavior. It never dispatches the prepared operation. The actual policy/controller tests above carry those behavioral assertions instead; neither source fixture is native GUI, persistence or original parity evidence.

The file now has **seven test methods (four additional methods)**; they were not executed by this worker. Coordinator command after integrating the real helper/consumer source:

```powershell
python -B -m unittest discover -s redux/tools/phase1/tests -p test_spellbook_confirmation_policy.py
```

Existing recorded BEFORE/AFTER direct-policy tests retain their historical source and observed option-off scope. New actual option-on/duplicate-copy/modal/save-reload verification remains the coordinator's separate native journey.
