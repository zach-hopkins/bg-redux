# Inn confirmation: source boundary and minimal ordinary journey

The BG2EE More Confirmation Prompts option still has an unimplemented inn-rest
consumer. The current native `GUISTORE.RentRoom` always opens the confirmation
modal after its price check, regardless of `Over Confirm Everything`. Existing
spellbook/settings success does not establish inn parity. This note inspects
protected shipped resources and current source only; no game, native host,
compiler or tests were launched.

## Authoritative option and trigger evidence

Packaged ui.menu:3381 maps `ENABLE_CONFIRMATION_LABEL/HELP` to feedback option
41, panel 9. English L_en_US.lua:277–278 describes prepared-spell removal and
inn rest, and supplies the label “More Confirmation Prompts”. There is no exact
English TLK entry for that label in the pinned bytes; localized TLK 102476/102477
supplies the existing equivalent label/help. The latter explicitly specifies a
confirmation when enabled and no confirmation when disabled for inn resting.
The distinct `Confirm Dialog` key is not this setting: the version-specific
[binary/configuration binding](phase1-confirmation-option-source-binding.md)
and [physical original option reference](phase1-original-confirmation-option-independent.md)
identify `Over Confirm Everything`. The separate
[Feedback row correction](phase1-confirmation-feedback-row-repair.md) preserves
this distinction and the original Colored Markers row.

The original inn Rent button at ui.menu:10482–10487 invokes
`storeScreen:OnRentRoomButtonClick()`. Its original compiled implementation is
opaque to this Lua source. Consequently, the explicit help establishes the
intended option contract, but source inspection here does **not** establish all
original affordability, rest-eligibility, cutscene or cancellation conditions.
Those need an ordinary original run or a separately pinned binary trace.

In current GemRB source:

- GUISTORE.py:890–964 initializes room choice, binds room buttons and Rent, and
  disables Rent if no room is selected. For BG2EE the rent window is 7, room
  icons 0–3/buddy buttons 4–7, and Rent is control 11.
- GUIScript.cpp's `storebuttons` entry for type 2 (Inn) puts RoomRent first,
  unconditionally. `OpenStoreWindow` opens that first store view. A fresh actual
  WINNKEEP store should therefore enter the rent view directly; the observer must
  verify actual `StoreType`, `StoreButtons[0] == 6` and current window/alias.
- `RentRoom`, currently at 1965, reads RentIndex and price, checks party gold,
  and always loads GUISTORE window 11. Control 0 calls `RentConfirm`, control 1
  closes the modal; text control 3 uses strref 15358. These are distinct from
  ordinary wilderness-rest controls and options.
- `RentConfirm`, currently at 1935, debits the selected room price, reads
  `restheal` at the room row, then calls `RestParty(18, 1, healFor)`. Its comment
  identifies the flags as proximity checking without repeated rests, and still
  has a TODO for `RunRestScripts`. Error and cutscene handling follow this call.
  It does not itself consult the confirmation option. Debit precedes the error
  result, so invalid-rest cases must not be assumed to refund or match original
  behavior. This note does not change that order or authorize a broad rest fix.

## Concrete stock fixture and conversation

Use a coherent, fresh owned save in **AR0704**, with the party together, no
combat/dialogue/cutscene, and at least one legitimately present gold. The current
four-party AR0602 parent is not such a fixture. An actual ordinary travel/save
or a separately declared fixture-construction control is required; replacing
the area or granting gold must never be silently called ordinary campaign
progression or original parity.

The protected stock chain is particularly small:

| Resource | Exact stock identity | SHA256 |
| --- | --- | --- |
| AR0704 ARE | Actor record 0, name `Innkeeper`, CRE `WINNKEEP`, position (786,408) | `c8061c51f2e009917a0b95ba537456da7adf3b308de4d202bbbdc8f8b41d1d32` |
| WINNKEEP CRE | CRE V1.0, name ref 30197, dialog `winnkeep`, script name `None` | `a42acbb669745443db9a263c09634474b406644642d2cf346d191bced2d9e851` |
| WINNKEEP DLG | State 0 has `True()` trigger | `7500056e91ebf0abbd8e43f4045aae119d4ba44c396855110a6c71614029d98e` |
| WINNKEEP STO | Store type 2, rooms bitmask 15, raw prices [1,6,10,16] | `d76502ca4a177d8c52eb0d1699b6d54d4b5004d9cbc2b9830b78c86d5cd559d4` |

ARE/CRE/DLG/STO providers are protected clean `data/Areas.bif`, `Creature.bif`,
`DIALOG.BIF` and `STORES.BIF`, respectively. These are static provider findings;
future execution must prove actual runtime stream path/bytes, declared wrapper
mapping and copied save overlays rather than assume stock providers won.

Request ordinary talk with that actual actor once. Because the CRE's script name
is `None`, do not identify it merely by that nonunique name. Bind the loaded area,
actor census/runtime identity, original actor record/position, dialog, name ref
and resource provenance before issuing the target action. The exact dialogue
route is:

1. State 0, NPC strref 28755, first visible response: local/global transition 0,
   response strref 28763, flags 1, leading to state 1 in WINNKEEP.
2. State 1, NPC strref 28771, final transition local 0/global 3, flags 12
   (action + final), executing `StartStore("winnkeep",LastTalkedToBy())`.
   Observe the actual Continue/End transition through the registered stock
   control; do not equate response dispatch with store readiness.
3. Once actual WINNKEEP store/rent controls are ready, select room index 0 using
   its bound ordinary control and press Rent (GUISTORE/7/11). Verify actual price
   and gold first; the raw cheapest room costs one gold.

This avoids Bernard's Jaheira, Lehtinan-death/discount and quest-conditioned
store choices. It is a proposed route grounded in parsed stock resources, not an
already observed conversation or assumption about all live save states.

## Bounded original/native acceptance

Start OFF and ON from separate immutable copies of the same valid inn save and
fresh private profiles. Establish the real option through ordinary Feedback
controls, freeze configuration bytes, and retain the current private GamePath,
source/build, original executable and resource guards.

- OFF: after ordinary Rent, the intended contract is direct rest without the
  inn confirmation modal. Observe several completed draws, actual gold/time,
  prepared readiness/healing/effects and terminal store/rest state. A single
  absent window capture alone cannot prove completion.
- ON: ordinary Rent should open the modal before rest/charge. Cancel must not
  rest or charge; record whether the selected room is retained and compare the
  actual original/native behavior. Then request Rent again and confirm exactly
  once. Observe one charge and the actual resulting rest.
- Freeze exact source and original control identities, localized strings,
  selected room, effective price, actor/party readiness, modal labels and each
  callback/world boundary. Use a uniquely named ordinary GUI save and a fresh
  owned process to check saved gold, time, spells/effects and config persistence.
  Do not normalize arbitrary rest randomness, dreams or cutscene outcomes.

Disabled room/Rent controls must be reported as context-gated rather than forced
with `PerformAction`. Missing gold, stale store contents, split/dead party,
hostile/cutscene conditions, unexpected dialogue branch or provider, failed rest,
and unavailable coherent AR0704 input remain explicit unsupported/blocking
conditions for that case. Classic games, wilderness rest, temples, stores,
bags, full rest-script parity and price/refund failure policy need separate
coverage. A future narrow BG2EE option consumer can reuse the existing real
`RentConfirm` completion route, but must be reviewed against these lifecycle and
failure conditions; this note introduces no production implementation.

## Private reproducible evidence

Read-only resource inspection scripts and receipts are retained under
`C:/BGRedux/phase1-local/worker-audits/20261022T122715Z-feedback-row-source-81ff1ef1/`:
`inspect-inn.ps1`/`inn-resources.json`,
`inspect-simple-inn-area.ps1`/`simple-inn-area.json`,
`inspect-winnkeep-route.ps1`/`winnkeep-route.json`, and
`inspect-winnkeep-cre.ps1`/`winnkeep-cre.json`.
They parse protected KEY/BIF/ARE/CRE/DLG/STO bytes and write new private JSON;
they do not launch GemRB/Baldur, modify a save, enter a store, or publish licensed
assets. The broader area scan is recorded explicitly. No test or engine build
was executed for this source note.
