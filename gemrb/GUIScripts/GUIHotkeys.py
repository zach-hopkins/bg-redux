# SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
# SPDX-License-Identifier: GPL-2.0-or-later
"""Functional profile key editor over existing KeyMap/menu input routing."""
import GemRB
import GUIOPTExtra
import MenuWindow
from KeyBindingEditor import Draft, BindingConflict
from GUIDefines import *

Window = None
Editor = None
Names = []
Page = 0
Selected = 0
ROWS = 12


def Open():
	global Window, Editor, Names, Page, Selected
	if Window:
		Window.Focus()
		return
	Editor = Draft(GemRB.GetKeyBindings())
	Names = sorted(Editor.working)
	Page = Selected = 0
	Window = GUIOPTExtra.PrepareBlankWindow("Keyboard Shortcuts", "", [11, 14, 15, 16], [1, 16, 17])
	Window.AddAlias("WIN_KEYS")
	Window.OnClose(Closed)
	w, h = Window.GetFrame()["w"], Window.GetFrame()["h"]
	Window.GetControl(0x0fffffff).SetFont("STONESML")
	for cid, x, label, callback in ((11, w - 270, "Apply", Apply), (14, w - 140, "Cancel", Window.Close)):
		button = Window.GetControl(cid)
		button.SetFrame({"x": x, "y": h - 46, "w": 120, "h": 30})
		button.SetFont("STONESML")
		button.SetText(label)
		button.OnPress(callback)
	Window.GetControl(15).SetFrame({"x": 30, "y": h - 110, "w": w - 60, "h": 56})
	Window.GetControl(15).SetFont("NORMAL")
	Window.GetControl(16).SetVisible(False)
	for offset in range(ROWS):
		button = Window.CreateButton(5000 + offset, 40, 76 + offset * 30, w - 330, 28)
		button.SetFlags(IE_GUI_BUTTON_NO_IMAGE | IE_GUI_BUTTON_ALIGN_LEFT, OP_SET)
		button.SetFont("NORMAL")
		button.OnPress(lambda _control, row=offset: Select(Page * ROWS + row))
	Window.CreateLabel(6008, w - 270, 76, 230, 28, "NORMAL", "", IE_FONT_ALIGN_CENTER)
	edit = Window.CreateTextArea(6000, w - 245, 112, 180, 32, "NORMAL")
	edit.SetFlags(IE_GUI_TEXTAREA_EDITABLE, OP_OR)
	edit.SetColor(ColorWhitish, TA_COLOR_NORMAL)
	edit.SetBackground({'r': 0, 'g': 0, 'b': 0, 'a': 255})
	for cid, y, label, callback in ((6001, 158, "Assign", lambda _control: Assign()), (6002, 194, "Clear", Clear),
		(6003, 230, "Replace conflict", Replace), (6004, 266, "Defaults", Defaults)):
		button = Window.CreateButton(cid, w - 255, y, 200, 30)
		button.SetFlags(IE_GUI_BUTTON_NO_IMAGE, OP_SET)
		button.SetFont("STONESML")
		button.SetText(label)
		button.OnPress(callback)
	for cid, x, label, step in ((6005, 40, "< Previous", -1), (6006, 240, "Next >", 1)):
		button = Window.CreateButton(cid, x, 448, 150, 30)
		button.SetFlags(IE_GUI_BUTTON_NO_IMAGE, OP_SET)
		button.SetFont("NORMAL")
		button.SetText(label)
		button.OnPress(lambda _control, delta=step: TurnPage(delta))
	Window.CreateLabel(6007, 40, 486, w - 330, 24, "NORMAL", "", IE_FONT_ALIGN_CENTER)
	Render()
	Select(0)
	Status("Changes are staged until Apply. Fixed party/pause/function keys and modified shortcuts remain unchanged.")
	Window.ShowModal(MODAL_SHADOW_GRAY)


def Closed():
	global Window, Editor
	Window = Editor = None


def Status(text):
	Window.GetControl(15).SetText(text)


def Render():
	for row in range(ROWS):
		index = Page * ROWS + row
		button = Window.GetControl(5000 + row)
		button.SetVisible(index < len(Names))
		if index < len(Names):
			name = Names[index]
			button.SetText(name.replace("_", " ").title() + " : " + (Editor.working[name].upper() or "Unbound"))
			button.SetColor({'r': 255, 'g': 215, 'b': 128} if index == Selected else ColorWhitish)
	Window.GetControl(6007).SetText("%d / %d" % (Page + 1, max(1, (len(Names) + ROWS - 1) // ROWS)))
	Window.GetControl(6005).SetState(IE_GUI_BUTTON_ENABLED if Page else IE_GUI_BUTTON_DISABLED)
	Window.GetControl(6006).SetState(IE_GUI_BUTTON_ENABLED if (Page + 1) * ROWS < len(Names) else IE_GUI_BUTTON_DISABLED)


def Select(index):
	global Selected
	if not 0 <= index < len(Names): return
	Selected = index
	Window.GetControl(6008).SetText(Names[index].replace("_", " ").title())
	Window.GetControl(6000).SetText(Editor.working[Names[index]].upper())
	Window.GetControl(6000).Focus()
	Render()


def TurnPage(delta):
	global Page
	Page = max(0, min(max(0, (len(Names) - 1) // ROWS), Page + delta))
	Select(Page * ROWS)
	Render()


def Assign(replace=False):
	if not Names: return
	try:
		Editor.assign(Names[Selected], Window.GetControl(6000).QueryText(), replace)
		Render()
		Status("Binding staged. Apply to save, or Cancel to discard.")
	except (ValueError, BindingConflict) as error:
		Status(str(error))


def Clear():
	Window.GetControl(6000).SetText("")
	Assign()


def Replace():
	Assign(True)


def Defaults():
	Editor.reset()
	Render()
	Select(Selected)
	Status("Game defaults staged. Apply to save, or Cancel to discard.")


def Apply():
	try:
		Editor.apply(GemRB, GemRB.GetSystemVariable(SV_SAVEPATH), MenuWindow.RebindNamedKeys)
	except Exception as error:
		Status("Bindings were not saved: " + str(error))
		return
	Window.Close()
