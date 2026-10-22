# Spellbook caster selection gap in the menu observer

The corrected-renderer broad menu runs pass their existing callback/window and
sheet assertions, but do not establish correct displayed spellbook content.
Follow-up capture inspection found an external scenario defect: it identifies an
eligible caster and sets only `GameSelectPCSingle`, then opens a top window from
the walking context. `GUICommonWindows.SetSelectionChangeHandler` intentionally
initializes the single selection from the first actual walking-selected actor.
The test's eligible caster is therefore replaced by the leader.

The initial two-member rerun `20261022T052939Z-guarded-renderer-menu-run-35f95c1d`
has Mage capture23 with actual selection1 and name `wfsdf`, despite identifying
Imoen/actor2 as eligible. The later recruited-party run
`20261022T054632Z-guarded-recruited-menu-run-a098a21f` likewise shows selection1
and `wfsdf` in both Mage capture23 and Priest capture25 at1024×768. Its intended
casters are actor2/Imoen and actor3/Jaheira; Jaheira has40 known priest spells and
11 slots. The priest window is disabled/empty for the displayed fighter. This
cannot count as a successful eligible-priest test merely because the window exists.

The private post-analysis `spellbook-semantic-review-1024.json` records the false
semantic verdict and hashes the screenshots/state/UI receipts. The earlier raw
results and their weaker checks remain unchanged. The broad renderer audit's
world/preservation/sheet/callback findings remain valid; the spellbook caster and
content claim is explicitly unproven. The working actual-Imoen Armor casting
journey uses its own verified portrait callback and is a separate result.

The correction is external-only: dispatch the actual portrait callback with its
normal actor binding before the sidebar callback; verify actual walking/single
selection and the displayed caster name after opening. Content observations must
also bind visible known/memorized controls to actual spell names/resrefs using
public tooltip, flags and value metadata. Wrong caster, blank or stale content
must fail. No engine selection behavior change is justified by this scenario bug.
The revised observer, its negative tests and native rerun are still pending.
