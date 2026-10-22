# SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""BG2EE prepared-removal/inn prompt policy and persistent Feedback setting.

Callers retain their charged/spontaneous eligibility checks. This module does
not remove spells, change spellbook state, or perform rest operations.
"""

import GemRB
import GameCheck
import GUIOPTControls

OPTION = "Over Confirm Everything"
DRAFT = "BG2EE Confirmation Draft"
DEFAULT = 0
LABEL_STRREF = 102476
HELP_STRREF = 102477


def ShouldPromptInnRest ():
	# Other games retain their existing inn confirmation behavior.
	return not GameCheck.IsBG2EE () or bool (GemRB.GetVar (OPTION))


def PreparedRemovalIndex (pc, spelltype, level, index):
	"""Prefer an uncharged copy of the clicked spell, retaining storage identity."""
	if not GameCheck.IsBG2EE ():
		return index
	count = GemRB.GetMemorizedSpellsCount (pc, spelltype, level, False)
	if index < 0 or index >= count:
		return None
	clicked = GemRB.GetMemorizedSpell (pc, spelltype, level, index)
	for candidate in range (count):
		spell = GemRB.GetMemorizedSpell (pc, spelltype, level, candidate)
		if spell['SpellResRef'].casefold () == clicked['SpellResRef'].casefold () and spell['Flags'] == 0:
			return candidate
	return index


def ShouldPromptPreparedRemoval (pc, spelltype, level, resref):
	# Preserve the existing charged-removal prompt for other games.
	if not GameCheck.IsBG2EE ():
		return True
	if not GemRB.GetVar (OPTION):
		return False
	for index in range (GemRB.GetMemorizedSpellsCount (pc, spelltype, level, False)):
		spell = GemRB.GetMemorizedSpell (pc, spelltype, level, index)
		if spell['SpellResRef'].casefold () == resref.casefold () and spell['Flags'] == 0:
			return False
	return True


def BeginFeedback (window):
	"""Bind a draft checkbox; return explicit Done and Cancel handlers.

	Only Done publishes the new option and invokes the defaults.ini whitelist
	writer. Existing Feedback controls retain their existing immediate semantics.
	"""
	if not GameCheck.IsBG2EE ():
		raise ValueError ("BG2EE confirmation control requires BG2EE")
	GemRB.SetVar (DRAFT, int (bool (GemRB.GetVar (OPTION))))
	# GUIOPT window 9's right row is confirmation (41/40/0x10000029).
	# Preserve the left Colored Markers row and both existing CHU font/frames.
	window.GetControl (0x10000029).SetText (LABEL_STRREF)
	GUIOPTControls.OptCheckbox (HELP_STRREF, 41, 40, LABEL_STRREF, DRAFT)

	def Done ():
		previous = GemRB.GetVar (OPTION)
		GemRB.SetVar (OPTION, int (bool (GemRB.GetVar (DRAFT))))
		if not GemRB.SaveConfig ():
			GemRB.SetVar (OPTION, previous)
			print ("Could not save configuration; confirmation option was not committed")
			return
		GemRB.SetVar (DRAFT, None)
		window.Close ()

	def Cancel ():
		GemRB.SetVar (DRAFT, None)
		window.Close ()

	return Done, Cancel
