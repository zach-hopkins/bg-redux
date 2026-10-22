# First confirmation-setting native attempt

Candidate `20261022T115526Z-candidate-ced237a2` has unchanged Phase0 guards,
source/support build guards, and 3511 source / 61 binary / 5 support pins.
External host `spellbook-probes/confirmation-setting-2/build.json` runs under
`results/20261022T120547Z-confirmation-setting-mixed-d8efb6d2`.

The actual first process completes 74 ticks, 36 callbacks, 22 captures and a
normal GUI save. The overall result is **failed**: its validator directly compares
uppercase Python prepared-spell observations with lowercase imported native
prepared entries. No fresh reload stage is accepted. All candidate, protected
baseline and input preservation guards pass. The failed receipt remains unchanged.

The diagnostic now compares resource identities case-insensitively at the
observation boundary while retaining exact ordered native world deltas. Raw
callback snapshots demonstrate that a newly memorized entry uses the uppercase
known ref, while imported existing prepared entries stay lowercase. An initial
attempt to copy the old entry's case was contradicted by that evidence and
corrected. Focused known-case regression has a retained failing BEFORE and
19-pass AFTER (`phase1-confirmation-knowncase-before-20261022.log` and
`phase1-confirmation-knowncase-after-20261022.log`). Wrong resource, readiness,
order, unrelated world changes and missing configuration remain rejected.

Diagnostic-only reanalysis
`confirmation-case-reanalysis-1792671151217122800/result.json` passes the complete
first-process capture validation with all old result bytes unchanged. It checks
the actual checkbox route, Cancel draft discard, Done writing the owned INI,
charged-target Cancel, filler Confirm, mixed-copy depleted-first removal in both
books, and final ordinary GUI save. This reanalysis does not replace the failed
native receipt and cannot prove persistence in a fresh process. A fresh host and
two-process journey remain required. Duplicate Feedback labels, inn-rest option
consumption, pointer hit testing and wider settings remain separate open work.
