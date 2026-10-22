# Ordinary spellbook page observation contract

This source-only update replaces the external adapters' assumption that every
known spell has a simultaneously visible icon. Ordinary BG2EE information panels
have seven reusable icon/name rows. The full independently enumerated known list
remains part of every book observation; a visible row must match the exact sorted
slice, original known index, resref and localized name.

`bg-redux-book-observation/2` carries
`bg-redux-known-information-page/1`. Menu observations explicitly distinguish
`ordinary-information/1` from `legacy-spontaneous/1`. Unknown or missing versions
fail. Historical frozen drivers and receipts retain their original contracts.

The operation and Erase adapters bind the production helper's imported path to
the sibling of the independently checked GUI provider. Their resource receipts
also pin the complete localized help at TLK strref 39254. The menu adapter binds
actual helper rows to its full API enumeration and frozen production sources.
All three inspect actual native icon and persistent name controls, page/range
labels, navigation bounds, information text, and the disabled unselected separate
Memorize action. Their current plans require page offset zero and no selected
name: no navigation or selected-description coverage is inferred from opening a
book. Targets outside the visible page fail explicitly.

The new validator is frozen as actual bytes in menu, operation and Erase source
closures. Existing complete imported GUI/defaults pins remain in force. New
builds are required; previous native captures cannot establish this contract.

Default help must remain complete even for an empty ordinary book. Blank text is
not an accepted ineligible-actor policy: the original ineligible priest reference
shows help. The current production `Live` guard may leave that surface blank;
this update deliberately retains a failure if native evidence demonstrates it.
It does not repair that production behavior.

Focused negative test sources cover wrong layouts, offsets, actor/provider,
identity, hidden or nonrendered icons, missing names, blank/truncated help,
unobserved selection and an enabled unselected action. A 31-entry synthetic list
tests each page's slice without claiming that native navigation occurred. The
empty ordinary book case requires localized help. Heading-only runtime fixtures
stub information assembly explicitly; actual page assembly has its own contract.

No tests, builds or native processes were executed by this worker for this
change. Native paging, selection/deselection, description scrolling, capacity
gates, callback mutations, persistence and screenshots remain for the dedicated
information journey and coordinator execution. Per-label font/color and pixel
legibility are unobserved by this metadata seam; existing global font provenance
and subsequent screenshot review remain separate evidence.
