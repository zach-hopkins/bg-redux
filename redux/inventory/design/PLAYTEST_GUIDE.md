# Inventory Redux — one-session prototype playtest

Double-click `inventory/design/fixture/Launch Inventory Redux.cmd` to launch the latest build. Close any running isolated game first. The launcher preserves prior receipts and clears only acknowledged test commands.

Use the isolated `scratch/inventory-visual68-game` fixture and its synthetic save, not your campaign or Personal installation. F11 opens Redux. This guide covers the current interaction prototype; campaign compatibility and multiplayer are later gates.

Allow about 25–40 minutes. Keep one list of failures using the IDs below. Continue unrelated tests after a normal refusal. If an item disappears, duplicates, or remains stuck in pending/recovery, stop item movement and report the last action before restarting: further movement can obscure the evidence.

## Record before starting

- Character, screen resolution, UI++ skin, and whether the window is maximized.
- For arrows, note each equipped stack quantity and the total shown in stash. The fixture's installed native limit is 80; a different installed limit should be respected instead.
- Note the weapon names currently in all three quick slots and which has the active marker.
- Note the stash quantities of any potion or charged wand you test. Do not expect a wand's charges to behave like a potion stack count.

Use existing synthetic test items. Avoid adding campaign items or changing stack-limit mods during this pass.

## A. Opening, layout and inspection

1. **A01 — Open/close:** Open F11, close with X, reopen, then close with Escape while idle. No invisible pointer, duplicate menu, trapped mouse, or missing top bar.
2. **A02 — Party selection:** Switch between PC and Imoen several times. Name, portrait, doll, equipped items and actual stats must all refer to the selected person. Stash stays available.
3. **A03 — Details:** Right-click small shield, armor, dagger and a scroll. The description starts at its first line. Scroll to the end and back. Closing Details expands the stash from 30 to 70 cells without moving equipment controls.
4. **A04 — Search/filter/sort:** Type part of an item name; results filter live. Clear it, choose Weapons, then Armor, then All. Change sort and page if enough rows exist. No repeated item, lost item, or selection of a different item than the clicked icon.
5. **A05 — Stats:** Choose Stats. Check saves, physical and elemental resistances, magic resistance/damage, poison and casting information without scrolling. Combat values and attributes remain in Summary rather than repeating here. Return to Summary. Actual values should agree with Character Record where it reports the same statistic. Unavailable casting values should not become fabricated zeros.
6. **A06 — Visuals:** Check long names, all nine quick slots, quantities, anatomical slot positions and paper doll centering. At the native 1280×720 floor, note any overlap or unreadably small text. Do not change the canvas target to compensate.

## B. Pickup, cancellation and legal equipment

7. **B01 — Cursor:** Pick up a potion and move across both panels. Pointer stays visible and the held icon follows the real click location without stretching. Escape returns it. No item remains held.
8. **B02 — Stash return area:** Lift an equipped ordinary item and return it to empty space near each edge of the stash rectangle. The whole rectangle accepts return, including empty cells.
9. **B03 — Anatomical auto-equip:** Hold a ring and click several places in the equipment box, including near helmet and armor. It chooses a legal ring slot. Repeat with gloves/bracers, boots and armor. The whole main equipment box is the target; quick-slot groups have their own destinations.
10. **B04 — Incompatible item:** Select someone who cannot use an existing test item. Its unusable cue should be visible; ordinary left-click must not begin pickup. Right-click still inspects it. Change to a legal user and retry.
11. **B05 — Wrong destination:** Try armor or a ring in a quick-item, ammo or quick-weapon slot below the doll area. It must not auto-equip elsewhere. Try a ring on Helmet within the doll area: it should still auto-route to a ring slot. For the incompatible quick-bar case, Expect a clear refusal with intact source/cursor custody. Escape or return-to-stash must restore the item exactly once.
12. **B06 — Offhand:** Equip a shield, then activate a two-handed weapon. Offhand remains accessible; native weapon rules determine whether its effects apply. Switch back to a one-handed weapon and check the actual AC baseline.

## C. Three weapons, replacement and reversal

13. **C01 — Third slot:** On Imoen, place the stash dagger into quick weapon 3. It lands, becomes active, and actual baseline stats update. Pick it up and put it back in the same slot; it stays equipped and becomes active again.
14. **C02 — Inactive replacement:** Activate slot 1, then replace the weapon in occupied slot 2 with an ordinary stash weapon. Slot 2 becomes active. The displaced item returns into the incoming item's former stash cell, with a returned cue even if the filter would otherwise hide it.
15. **C03 — Actor-slot swap:** Move weapon 1 onto weapon 2. They exchange positions without disappearing or duplicating; the destination becomes active. Try slots 2 and 3 as well.
16. **C04 — Undo offer:** Replace the already-active quick weapon with a different identified, nonstackable weapon. Choose a displaced weapon that has no identical stash copy (Imoen's Long Sword into Short Sword worked in the native test). If an Undo toast is offered, immediately click the right-hand Undo button (the left caption now says Equipment replaced). Original equipment and stash ownership return through acknowledged native steps. No success should be announced while pending. Undo currently has a deliberately limited admission profile; absence of an offer outside that profile, including ambiguous identical stash copies, is expected, not a loss of the underlying replacement feature.
17. **C05 — Undo expiry:** Repeat an eligible replacement, then change character or filter, close/reopen, or make another item move. A stale Undo must not reverse the wrong item. Test Ctrl+Z only when the build exposes the Undo keyboard binding and no text field has focus.

## D. Stack arithmetic

18. **D01 — Maximum:** With an arrow total greater than 80 in stash, plain click picks up at most the installed native limit, not the entire aggregate. Escape restores the total.
19. **D02 — One/half:** Ctrl-click picks up one. Shift-click picks up half of the legal pickup amount, rounded up for odd quantities. Repeat with a potion stack. Ordinary Ctrl/Shift alone must not start multi-selection.
20. **D03 — Merge remainder:** Make a destination ammo stack 79. Hold more than one arrow and click it. Equipped quantity becomes 80 immediately; the cursor loses exactly one and retains the rest. Return the remainder. Recheck combined totals.
21. **D04 — Same-slot return:** Lift a full 80-arrow equipped stack and return it to its own empty slot. Then Ctrl-click one arrow and put it back. Both return paths work and counts update immediately.
22. **D05 — Other slot:** Move one arrow into another compatible ammo slot. Merge compatible stacks with room. Exchange incompatible whole stacks where permitted. No silently discarded excess or automatic unexpected extra stack.
23. **D06 — Exact quantity:** Inspect a stack, set a small exact quantity in Details and choose Pick Up. It respects available quantity and native limits. Try zero, nonnumeric text, and an amount above availability; expect safe clamping/refusal rather than item loss.

## E. Selection and designed controls

24. **E01 — Multi-select:** Ctrl+Shift+left-click two stash items. Both get a gold selected cue/check badge. Footer says 2 selected and Actions (2). This gesture must not pick either item up.
25. **E02 — Clear:** Open Actions and choose Clear Selection. Repeat, then press Escape: first dismiss the Actions menu, next clear selection, then close inventory. Plain click while selected clears selection without picking up an item; another ordinary click can pick it up.
26. **E03 — Context changes:** Select an item, change character/filter/search, close/reopen, or move an item through another operation. Selection must never silently point at an unrelated replacement row.
27. **E04 — Ground availability:** Drop on Ground is displayed as unavailable until a native adapter with complete ownership acknowledgement is admitted. Do not interpret the row as a working disposal action in this build. Selection and clearing remain testable.

## F. Delays and interrupted operations

28. **F01 — Idle comparison:** Inspect a weapon, wait 10–15 seconds, then pick up dagger. Cancel. Repeat for short sword, then arrows. Record whether delay occurs at pickup, during cursor appearance, on placement, or only when stats update. Repeat once after a longer idle period.
29. **F02 — Third-slot delay:** Place dagger into Imoen's third slot after waiting. A modest native stats-refresh delay may remain; report freezes, worsening over time, or repeated multi-second stalls.
30. **F03 — Close while held:** Pick up ordinary stash item and press X or Escape. Return/cancellation must settle before closing. Reopen and verify the item and quantities.
31. **F04 — Switch while held:** Try changing character while holding an item. It must either safely resolve the current operation first or refuse the switch clearly. No wrong-owner placement.
32. **F05 — Rapid inputs:** During an acknowledged pending transfer, click another item, another destination and Close. Only the admitted operation may proceed; no duplicate request or fake success. Avoid killing the process mid-write in this pass.
33. **F06 — Acquisition:** In the synthetic test area, pick up an ordinary item from a container and then from ground, using the normal world UI. Let automatic intake settle, then open Redux: it should appear in stash once. Equipment already assigned to native slots should remain equipped.

## G. Equipment comparison status

At-rest statistics are real native values. The new comparison consumer/model is tested with synthetic receipts, but no fully validated native hypothetical-stat provider exists yet. While holding an item, **Planned** and unchanged current statistics remain expected in this build. Do not report missing green/red hypothetical values as a regression, and do not use the existing values as a promised preview.

Once the real provider is enabled, add a separate pass with a sword, armor, protection cloak, strength item and resistance ring: compare projected values to the actual settled values after equip, check lower-is-better AC/THAC0/saves, exceptional Strength, APR decimals, mixed damage bounds and Stats comparisons. The live actor must never be temporarily equipped solely to generate a preview.

## One batch report

Copy this template for each issue, then send all issues together:

```text
Build/date:
Test ID:
Character / resolution / skin:
Item name and quantity/charges:
Starting source and destination:
Exact clicks/modifiers, including any wait:
Expected:
Actual (include footer message verbatim):
Final location/quantity; still held or pending?:
Repeats: always / sometimes / once
Screenshot or short clip, if useful:
```

Also list passed IDs and tests skipped because a required test item was unavailable. This makes the next bug-fix batch reproducible and separates visual polish from ownership, arithmetic and performance failures.

## October 12 focused recheck

- Inspect both identified and unidentified wands in stash and equipped quick-item slots. The question-mark cue and identification notice must follow the actual identification flag; unidentified properties stay hidden.
- Identified charge counts appear beside a charge star at the top left, separate from stack quantity. A + means additional charged abilities: inspect Details or the native tooltip for separate Ability N charge counts. A zero remains visibly zero, not a slash fraction.
- Move a charged item, cancel, replace, then return it. Charge and quantity presentation must update without consuming charges.
- Gear sound playback remains pending the reviewed native sound resolver; arrow audio remains native.
