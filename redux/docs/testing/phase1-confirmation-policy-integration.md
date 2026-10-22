# Prepared-spell confirmation and depleted-copy preference

Current production source integrates `BG2EEConfirmation` into ordinary wizard
and priest prepared-spell callbacks. This source is **not yet natively validated**.
The previous coherent Erase candidate and its passing results remain historical,
bound to their own frozen sources.

The [original physical reference](phase1-original-confirmation-option-independent.md)
now supplies more than the earlier option-OFF example: an actual Feedback toggle
sets Over Confirm Everything to 1 while Confirm Dialog stays 0. Charged-only
Cloud removal prompts; Cancel keeps it. A depleted Cloud removes directly. When
charged and depleted copies coexist, clicking the bright charged icon removes
the depleted copy and keeps the charge. Four ordinary saves independently confirm
the identities and flags. This is bounded wizard evidence, without priest,
inn-rest, fresh-process option reload or whole-world purity claims.

Both candidate controllers retain their charged/spontaneous branches and ask the
shared helper whether the option and live same-resref page require a prompt.
The actual removal callback separately resolves the original storage index of
an available depleted copy before calling the existing native UnmemorizeSpell.
Suppressing the prompt alone would incorrectly discard the clicked charge. The
resolved row also drives the existing removal animation. Classic returns its
clicked index and retains its charged prompt without querying the EE setting.
Invalid EE indices cannot remove an entry. Where multiple depleted copies exist,
the resolver chooses the first storage index; the original tie-break among
multiple depleted copies has not been measured.

The localized Feedback draft and defaults.ini whitelist wiring are described in
the [setting preparation](phase1-confirmation-setting-source-preparation.md).
Twenty focused helper/settings/resolver tests pass in 0.027 seconds; retained log
`phase1-local/results/phase1-confirmation-focused-20261022.log`. These fake-API
checks do not prove actual config-file writing/loading, window fit, native
callback integration, save/reload or inn-rest behavior. Independent controller
tests and fresh native option-OFF/ON, Cancel, mixed-copy and persistence journeys
remain required.

The earlier full information-source suite ran 475 tests in 35.026 seconds and
failed four heading fixtures with missing `EESpellbookInformation` bindings.
Receipt `phase1-information-source-tooling-1792667794430305000/result.json` stays
failed. The fixture update and subsequent full suite are separate evidence;
neither that failed run nor source-only layout work is promoted to a native pass.

The subsequent fixture/import-closure update and actual controller tests are
integrated. The full source-bound suite passes **486 tests** in 35.821 seconds,
receipt `phase1-information-policy-tooling-1792668246277886700/result.json`, with
source hashes unchanged during execution. The consumer tests execute both actual
Unmemorize callback bodies and the actual helper; they confirm preferred native
indices, retained charged rows, Classic behavior, invalid-index rejection and
live-page revalidation at modal confirmation. Native validation remains separate.
