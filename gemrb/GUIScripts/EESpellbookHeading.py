# SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""BG2EE ordinary memorizing-book heading; spell operations stay in GUIMG/GUIPR."""

import GemRB
import GameCheck


def Init (Window, spontaneous=False):
	if not GameCheck.IsBG2EE ():
		return False

	Label = Window.GetControl (0x10000033)
	# The separate Sorcerer window need not contain this ordinary-book label.
	if not Label:
		return False
	Label.SetVisible (not spontaneous)
	if spontaneous:
		return False

	# EE's page-info strip ends before the prepared spell row at relative y=644.
	# Keep the CHU's horizontal center, width and label alignment.
	frame = dict(Label.GetFrame ())
	frame.update ({"y": 598, "h": 40})
	Label.SetFrame (frame)
	Label.SetFont ("STONESML")
	Label.SetColor ({"r": 206, "g": 206, "b": 206, "a": 255})
	return True


def Update (Window, memorized, capacity, spontaneous=False):
	# Init also handles a change from a spontaneous to an ordinary selected book.
	if not Init (Window, spontaneous):
		return False

	Label = Window.GetControl (0x10000033)
	Label.SetText ("%s: %d/%d" % (GemRB.GetString (11944), memorized, capacity))
	return True
