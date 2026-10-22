# Feedback confirmation row repair

The duplicate “Enable Confirmation” labels in native
`20261022T113936Z-inf-menu-run-918c978e` / nested
`20261022T113941Z-menu-run-c2b6f429`, 1024×768 capture 41, are a real assembly
defect. This source change binds the original right confirmation row, preserving
the left Colored Markers label. New native execution and visual review remain
required. Earlier wrong-placement receipts retain their original verdicts and
do not become visual-fidelity evidence for this repair.

The frozen stock GUIOPT.chu SHA256 is
`93cb75819024668829444aa38a9dd1144db73bf21c846ce10827b7f19b583571`.
Following CHUImporter's window-table/control-table/GetLabel format gives:

| Window 9 row | Checkbox | Buddy | Label | Original TLK | CHU font |
| --- | ---: | ---: | --- | ---: | --- |
| Left: Colored Markers | 38 | 39 | 0x10000028 | 77524 | STONESML |
| Right: confirmation | 41 | 40 | 0x10000029 | 102476 | STONESML |

The old helper overwrote label 0x10000028 with 102476 and bound 38/39, leaving
the original right label visible. The native snapshot contains both identical
labels; checkbox 38 has value 1 while checkbox 41 retains INVALID_VALUE. A label
alone does not establish a functioning independent option. Neither the current
GUIOPT script nor the raw CHU has a `ConfirmDialog` variable binding. The right
row must not be described as a functioning Confirm Dialog feature based on its
appearance. The original binary's distinct Confirm Dialog configuration field
remains documented in the [option binding investigation](phase1-confirmation-option-source-binding.md).

`BG2EEConfirmation.BeginFeedback` now uses 41/40/0x10000029. It preserves the
original frames, STONESML role and left label; Done/Cancel/persistence/policy
behavior is unchanged. This does not add a Colored Markers consumer or claim
that every existing Feedback row works. The external settings runtime requests
checkbox 41; its native MouseDown/MouseUp branch and independent dispatch guard
require that same right-hand control. Fresh observations require both the
localized confirmation label and unchanged localized Colored Markers label,
with TLK 77524 added to the frozen resource closure.

The authoritative original spelling “More Confirmation Prompts” is
`ENABLE_CONFIRMATION_LABEL` in packaged L_en_US.lua:278; its help is at 277.
The shipped ui.menu feedback table at 3381 maps that key to option 41, with
OPTIONS_FEEDBACK setting panel 9 at 3432. The table separately maps colored
markers to option 38. Packaged language SHA256 is
`9e8467d26c1e1a889eb916b678cf293475a06933020bdbae55ab18feec44ca62`;
ui.menu SHA256 is
`7987e9d38c9a1d8f4df949d880f260ad5a76dd623d08c7e7be6f0f6c8f2931fe`.

No exact English “More Confirmation Prompts” sequence exists in the pinned
English TLK bytes. TLK 102476 supplies the localized equivalent “Enable
Confirmation”; 102477 explicitly describes both prepared-spell removal and
inn-rest prompting, enabled versus disabled. TLK 77524 is “Colored Markers”.
The English TLK SHA256 is
`9e685225ff3c3436a8a35fa7022550620d24a92efe35436a062c02955d9f0952`.
This repair retains the existing localized TLK strategy; it does not hardcode
the English Lua literal or add a language-resource loader.

The actual-helper tests exercise right-row binding and preservation of the left
label across opening, Cancel, Done and reopening. Two new external negatives
reject the old left checkbox route, duplicated labels and swapped label context.
The focused helper gains one test and the journey gains two. They were not run
by this worker; no compiler, game, native host or runtime was launched.

Private read-only source audit:
`C:/BGRedux/phase1-local/worker-audits/20261022T122715Z-feedback-row-source-81ff1ef1/audit.json`.
It hashes the packaged source, TLK, frozen CHU, original native BMP/UI snapshot
and inspected current source. No licensed assets are copied into this repository.
The previous [source preparation](phase1-confirmation-setting-source-preparation.md)
is historical: its 38/39/0x10000028 placement is superseded here. Inn/rest remains
a separate consumer/reference gap; this layout correction does not implement it.
