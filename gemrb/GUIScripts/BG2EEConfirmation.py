# SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""BG2EE prepared-removal policy and its persistent Feedback setting.

Callers retain their charged/spontaneous eligibility checks. This module does
not remove spells, change spellbook state, or implement inn-rest confirmation.
"""

import GemRB
import GameCheck
import GUIOPTControls

OPTION = "Over Confirm Everything"
DRAFT = "BG2EE Confirmation Draft"
DEFAULT = 0
LABEL_STRREF = 102476
HELP_STRREF = 102477


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
	# GUIOPT window 9 already contains this unused checkbox/buddy-label row.
	# Keep its CHU font/frame and use the localized TLK, not English literals.
	window.GetControl (0x10000028).SetText (LABEL_STRREF)
	GUIOPTControls.OptCheckbox (HELP_STRREF, 38, 39, LABEL_STRREF, DRAFT)

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
