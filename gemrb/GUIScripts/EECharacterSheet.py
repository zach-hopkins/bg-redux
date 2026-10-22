# SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
# SPDX-License-Identifier: GPL-2.0-or-later

"""Actual equipped-state presentation for the EE inventory/record CHU adapter.

The EE dragging CHUs leave stat panels empty: ui.menu normally assembles them.
These queries use the same engine operations as the legacy character record.
They are not hypothetical equip previews or target-specific combat forecasts.
"""

import GemRB
import GUICommon
import re
import textwrap
from GUIDefines import *
from ie_stats import *


def Signed(value):
	return "%+d" % value


def StyleTextPanel(control):
	"""EE CHU placeholders have black body/dim initials; ui.menu styles them.

	Both parser fonts/colors must change before SetText creates fresh spans.
	Keeping the imported initial font makes the first letter a different face.
	"""
	control.SetFont("NORMAL")
	control.SetFont("NORMAL", 1)
	control.SetColor(ColorWhitish, TA_COLOR_NORMAL)
	control.SetColor(ColorWhitish, TA_COLOR_INITIALS)


def AttacksText(halfAttacks):
	# GetCombatDetails APR is in half-attacks, not a rounded integer.
	return str(halfAttacks // 2) + ("½" if halfAttacks % 2 else "")


def Pages(content, width=36, rows=12):
	"""Bound a Stats page; never discard long class/proficiency/effect lists.

	Character wrapping is conservative for the game NORMAL role, not a glyph
	measurement API. Fresh rendered captures still determine readability/fit.
	"""
	plain = content.replace("[/p]", "\n").replace("[p]", "\n")
	plain = re.sub(r"\[(?:/?(?:color|cap|int)[^]]*)\]", "", plain)
	lines = []
	for line in plain.splitlines():
		lines.extend(textwrap.wrap(line, width=width) or [""])
	while lines and not lines[-1]:
		lines.pop()
	return ["\n".join(lines[i:i + rows]) for i in range(0, len(lines), rows)] or ["—"]


def DamageText(details, identified=True):
	"""Base physical weapon dice before target resistance/conditional effects.

	DamageBonus already includes header, launcher, proficiency, effects and style;
	adding those named components again would double count them. Strength is
	returned separately by GUIScript and is applied by the attack path separately.
	Additional damage opcodes have their own probability/type and stay separate.
	"""
	if not details:
		return "—"
	if not identified:
		return "?"
	count = details["HitHeaderNumDice"]
	sides = details["HitHeaderDiceSides"]
	bonus = details["DamageBonus"] + details["WeaponStrBonus"]
	if count and sides:
		return "%dd%d%s" % (count, sides, Signed(bonus) if bonus else "")
	return str(bonus)


def ReadActor(pc):
	"""Re-query on refresh; never retain actor pointers, hands or selected PC."""
	main = GemRB.GetCombatDetails(pc, 0, True)
	dual = bool(main) and GemRB.IsDualWielding(pc)
	hands = []
	for index, details in enumerate([main, GemRB.GetCombatDetails(pc, 1, True)] if dual else [main]):
		if not details:
			continue
		slot = GemRB.GetSlotItem(pc, details["Slot"], 1)
		# Fists have no inventory item. A real unidentified weapon retains '?'.
		identified = not slot or bool(slot["Flags"] & IE_INV_ITEM_IDENTIFIED)
		if not index and details.get("Flags", 0) & 15 == 2:
			# Ranged hitting headers belong to the ammunition, not the launcher.
			ammoSlot = GemRB.GetEquippedAmmunition(pc)
			ammo = GemRB.GetSlotItem(pc, ammoSlot) if ammoSlot != -1 else None
			identified = identified and (not ammo or bool(ammo["Flags"] & IE_INV_ITEM_IDENTIFIED))
		hands.append({"hand": index, "details": details, "identified": identified,
			"damage": DamageText(details, identified),
			"thac0": details["ToHitStats"]["Total"]})
	return {
		"pc": pc, "hands": hands,
		"ac": GemRB.GetPlayerStat(pc, IE_ARMORCLASS) + GUICommon.GetACStyleBonus(pc, main),
		"base_ac": GemRB.GetPlayerStat(pc, IE_ARMORCLASS, 1),
		"hp": GemRB.GetPlayerStat(pc, IE_HITPOINTS),
		"max_hp": GemRB.GetPlayerStat(pc, IE_MAXHITPOINTS),
		"base_max_hp": GemRB.GetPlayerStat(pc, IE_MAXHITPOINTS, 1),
		"ac_modifiers": [(label, GemRB.GetPlayerStat(pc, stat)) for label, stat in (
			(11770, IE_ACCRUSHINGMOD), (11767, IE_ACMISSILEMOD),
			(11769, IE_ACPIERCINGMOD), (11768, IE_ACSLASHINGMOD))],
		"apr": AttacksText(main["APR"]) if main else "—",
	}


def PanelText(model):
	"""Four bounded summaries plus full tooltips, without made-up cause labels."""
	text = GemRB.GetString
	ac = [text(17183), "Base: %d" % model["base_ac"],
		"Current adjustment: %s" % Signed(model["ac"] - model["base_ac"])]
	hp = [text(17184), "Base maximum: %d" % model["base_max_hp"],
		"Maximum adjustment: %s" % Signed(model["max_hp"] - model["base_max_hp"]),
		"Damage taken: %d" % max(0, model["max_hp"] - model["hp"])]
	tohit = [text(9457)]
	damage = [text(10336)]
	for hand in model["hands"]:
		label = text(56910 if hand["hand"] else 56911)
		tohit.append("%s: %d" % (label, hand["thac0"]))
		# 56910/56911 include 'THAC0' in the actual TLK, so they are not
		# generic hand labels for damage (the prior double hid this mismatch).
		damage.append("%s: %s" % ("Off hand" if hand["hand"] else "Main hand", hand["damage"]))
	damage.append("%s: %s" % (text(9458), model["apr"]))
	if not model["hands"]:
		tohit.append("—")
		damage.insert(1, "—")
	return ["\n".join(lines) for lines in (ac, hp, tohit, damage)]


def CombatTooltip(model):
	"""Keep extra/conditional damage separate from the physical dice summary."""
	lines = ["Equipped-state values; target defenses are not included."]
	for hand in model["hands"]:
		if not hand["identified"]:
			lines.append("Unidentified item: details unknown")
			continue
		details = hand["details"]
		lines.append("%s: %s" % ("Off hand" if hand["hand"] else "Main hand", hand["damage"]))
		for key, value in details["ToHitStats"].items():
			lines.append("THAC0 %s: %d" % (key, value))
		for effect in details.get("DamageOpcodes", ()):
			lines.append("%s: %dd%d%s (%d%%)" % (effect["TypeName"], effect["NumDice"],
				effect["DiceSides"], Signed(effect["DiceBonus"]), effect["Chance"]))
	return "\n".join(lines)


def InitInventory(Window):
	# INVSTATS is an EE MOS, not a BAM. The EE menu positions it here.
	# CreateSubview inserts behind existing CHU controls. Disabled art neither
	# captures inventory drops nor replaces the original slot/control callbacks.
	art = Window.CreateButton(0x7FFF0100, 512, 44, 349, 376)
	art.SetFlags(IE_GUI_BUTTON_NO_IMAGE, OP_SET)
	art.SetBackground("INVSTATS")
	art.SetDisabled(True)
	for cid in (77, 78, 79, 80):
		StyleTextPanel(Window.GetControl(cid))
	for cid in (0x10000055, 0x10000056):
		# Both EE labels are authored as NORMAL in GUIINV.CHU. NUMBER is a
		# legacy BAM role, not the face used by these EE headline fields.
		Window.GetControl(cid).SetFont("NORMAL")
		Window.GetControl(cid).SetColor(ColorWhitish)


def Update(Window, pc, record=False):
	model = ReadActor(pc)
	acLabel = Window.GetControl(0x10000028 if record else 0x10000038)
	acLabel.SetColor(ColorWhitish)
	acLabel.SetText(str(model["ac"]))
	acLabel.SetTooltip(17183)
	panels = (53, 54, 55, 56) if record else (77, 78, 79, 80)
	for cid, content in zip(panels, PanelText(model)):
		control = Window.GetControl(cid)
		StyleTextPanel(control)
		control.SetText(content)
		control.SetTooltip(content if cid in panels[:2] else CombatTooltip(model))
	acTooltip = PanelText(model)[0] + "\n" + "\n".join(
		"%s: %s" % (GemRB.GetString(label), Signed(value)) for label, value in model["ac_modifiers"])
	if model["hands"]:
		acTooltip += "\n" + "\n".join("%s: %d" % item for item in model["hands"][0]["details"].get("AC", {}).items())
	Window.GetControl(panels[0]).SetTooltip(acTooltip)
	thac = Window.GetControl(0x10000040 if record else 0x10000055)
	damage = Window.GetControl(0x10000041 if record else 0x10000056)
	damage.SetFont("NORMAL")
	thac.SetColor(ColorWhitish)
	damage.SetColor(ColorWhitish)
	frame = damage.GetFrame()
	frame.update({"x": 520, "w": 78})
	damage.SetFrame(frame)
	thac.SetText("/".join(str(h["thac0"]) for h in model["hands"]) or "—")
	damage.SetText("\n".join(h["damage"] for h in model["hands"]) or "—")
	thac.SetTooltip(PanelText(model)[2])
	damage.SetTooltip(CombatTooltip(model))
	return model
