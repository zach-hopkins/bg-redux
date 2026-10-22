# Original BG2EE spellbook reference

On October 22 UTC the coordinator used the computer-use skill to run original
BG2EE 2.7.3.0 in a new private game/profile, load a copy of the protected
two-party save and inspect Imoen's wizard book. No gameplay cheat, rest, cast,
party edit or content override was issued. Original startup AI independently
cast Stoneskin, so this is not whole-world parity with the paused native case.

Private evidence root:
`phase1-local/results/20261022T082351Z-original-spellbook-installation-4de00a9c`.
The executable remains SHA-256
`b51093a49140b2b8a7c046b4652bb8e535be24ebbc12b1d735e0b94217a14d57`.
The owned interactive process, PID 5040, exited zero after ordinary Quit.
`verification.json` SHA-256 is
`34d97aaa69cc1583614423556e5681499709ac81ade9487b54cd246f9212fc5e`.
Clean-game inventory/root hashes, private prelaunch game-root files, original
fixture and copied input are unchanged. Linked archive content was not fully
rehashed; private profile/config and new saves are permitted outputs.

## Heading and placement

`original-mage-level1.jpg` shows the ordinary wizard book with known names on
parchment and **Memorized: 4/4** in gray on a dark strip immediately above the
prepared row. Level 2 shows **3/3** in that same region. This confirms that the
native priest heading's pale text at obsolete CHU y=490 is misplaced, rather
than establishing a general font-renderer failure. The actual original menu
style is STONESML, point 12, color B (`FFCECECE`); native role metrics still need
rendered verification. A resource role match alone is not exact typography.

`original-priest-ineligible-level1.jpg` also shows **Memorized: 0/0** in the lower
strip, but the screen is dimmed because Imoen has no priest book. This is a
layout observation only, not eligible priest readability/operation evidence.
The [packaged source trace](phase1-spellbook-heading-layout-gap.md) binds its
menu rectangle and style. Mage and priest runtime eligibility must remain
separate from screen presence.

## Prepared spell operation and saved bytes

At wizard level 2, the visible prepared row initially contains Stinking Cloud,
Strength and Web, with count 3/3. One ordinary left click on prepared Stinking
Cloud immediately removes it, shows 2/3 and opens **no confirmation**. Selecting
the known Stinking Cloud row and pressing Memorize restores count 3/3, with its
icon visibly dark/unready. The coordinator then creates a new ordinary save,
`000000026-a`, and freezes its five files without replacing the input.

An independent bounded GAME/CRE reader compares the protected input and frozen
original output. Imoen's level-2 spell page has capacity 3 throughout:

| Boundary | Serialized prepared entries, in order |
| --- | --- |
| Protected original input | SPWI213 ready=1; SPWI214 ready=1; SPWI215 ready=1 |
| Original GUI save after remove/reprepare | SPWI214 ready=1; SPWI215 ready=1; SPWI213 ready=0 |

Thus preparation does not restore the expended/removed ready charge. The original
displayed prepared icons remain visually sorted despite serialized append order;
do not equate screen order with CRE record order. `original-wire-spellbook.json`
SHA-256 is `3d548c81080561a5c3d3188da3d5883aa1da28225b5756c2ec85869dff3d98e2`.
The reproducible reader is
`phase1-local/decode-original-spellbook-reference-v2-20261022.py`. Its first
version's wrong Strength resref expectation (219 instead of observed 214) is
retained as a failed assertion; frozen save bytes were unchanged.

The shipped `ui.menu` functions at lines 7808 and 8589 directly unmemorize the
chosen wizard/priest entry. Their source hashes and short function excerpts are
in `original-menu-operation-source.json`. Priest no-confirmation behavior is
source-supported here but not independently exercised in the original runtime.
Current GemRB's charged-entry confirmation path therefore differs from this
measured wizard behavior; its external BEFORE journey must not approve that
prompt as an EE contract. Classic confirmation policy is a separate requirement.

## Retained setup failures and limits

The first launch through the window launcher failed before the menu with a
default-profile crash; its dump is preserved. A subsequent hidden launch exposed
no targetable window and was explicitly cancelled (owned exit -1). The successful
interactive launch uses the private game's working directory. Both unsuccessful
attempts remain evidence; no source/binary correction was needed to launch.

The `type_text` save-name attempt produced no visible characters; an observed
single `a` key press succeeded. This does not certify general Unicode input.
Original fresh-process reload/resave of the new checkpoint, eligible priest
operations, nonidentity spell sorting, all spell levels, pointer cancellation,
full visual metrics and campaign parity remain unverified.
