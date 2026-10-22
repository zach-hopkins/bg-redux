# SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Ordinary BG2EE known rows, information selection and existing spell actions.

Control identities are stable; row identities include original storage index.
Paging never drops entries or changes spell storage. Classic/spontaneous books
continue through their existing assembly after Deactivate restores CHU frames.
"""
import GemRB
import GameCheck
import GUICommon
import Spellbook
from GUIDefines import *

ROWS = 7
NAME_BASE = 0x7fff0400
PAGE_UP = 0x7fff0410
PAGE_DOWN = 0x7fff0411
PAGE_INFO = 0x7fff0412
MEMORIZE = 0x7fff0413
INFORMATION = 0x7fff0414
INFO_UP = 0x7fff0415
INFO_DOWN = 0x7fff0416
HELP = 39254
BLACK = {'r': 0, 'g': 0, 'b': 0, 'a': 255}
SELECTED = {'r': 30, 'g': 40, 'b': 120, 'a': 255}
LIGHT = {'r': 206, 'g': 206, 'b': 206, 'a': 255}
TRANSPARENT = {'r': 0, 'g': 0, 'b': 0, 'a': 0}
Panels = {}


def Reset(Window, pack):
    # Called on actual window initialization, including a reused scripting ID.
    panel = Panels.get(pack)
    if panel and panel.window.ID == Window.ID and Window.GetControl(INFORMATION):
        panel.Deactivate()
    Panels.pop(pack, None)


def Update(Window, pack, pc, kind, level, known, spontaneous, memorize, info, current_level):
    if not GameCheck.IsBG2EE():
        return False
    panel = Panels.get(pack)
    if spontaneous or Spellbook.HasSorcererBook(pc):
        if panel and panel.window.ID == Window.ID:
            panel.Deactivate()
        return False
    if not panel or panel.window.ID != Window.ID or not Window.GetControl(INFORMATION):
        panel = Panel(Window, pack)
        Panels[pack] = panel
    panel.Update(pc, kind, level, known, memorize, info, current_level)
    return True


class Panel:
    def __init__(self, Window, pack):
        self.window, self.pack = Window, pack
        self.context = None
        self.rows = []
        self.top = 0
        self.selected = None
        self.generation = 0
        self.active = False
        self.frames = {i: dict(Window.GetControl(27+i).GetFrame()) for i in range(24)}
        self.flags = {i: Window.GetControl(27+i).Flags for i in range(24)}
        self.created = []
        for row in range(ROWS):
            button = Window.GetControl(NAME_BASE+row) or Window.CreateButton(NAME_BASE+row, 166, 228+42*row, 248, 40)
            button.SetFlags(IE_GUI_BUTTON_NO_IMAGE | IE_GUI_BUTTON_ALIGN_LEFT, OP_SET)
            button.SetFont('NORMAL')
            button.SetColor(TRANSPARENT, TA_COLOR_BACKGROUND)
            self.created.append(NAME_BASE+row)
        for cid, x, y, down in ((PAGE_UP,112,530,False), (PAGE_DOWN,390,530,True),
                                 (INFO_UP,714,542,False), (INFO_DOWN,746,542,True)):
            button = Window.GetControl(cid) or Window.CreateButton(cid, x, y, 24, 24)
            # Same bg2ee scrollbar BAM/state mapping used by CreateScrollBar.
            normal, pressed = (2,3) if down else (0,1)
            button.SetSprites('GUISCRCW', 0, normal, pressed, normal, pressed)
            self.created.append(cid)
        label = Window.GetControl(PAGE_INFO) or Window.CreateLabel(PAGE_INFO, 142, 530, 240, 24, 'NORMAL', '', IE_FONT_ALIGN_CENTER)
        label.SetColor(BLACK)
        button = Window.GetControl(MEMORIZE) or Window.CreateButton(MEMORIZE, 112, 566, 302, 28)
        button.SetFlags(IE_GUI_BUTTON_NO_IMAGE, OP_SET)
        button.SetBackground({'r':35, 'g':22, 'b':13, 'a':255})
        button.SetFont('STONESML')
        button.SetColor(LIGHT)
        text = Window.GetControl(INFORMATION) or Window.CreateTextArea(INFORMATION, 448, 198, 322, 338, 'NORMAL')
        text.SetColor(BLACK, TA_COLOR_NORMAL)
        text.SetColor(BLACK, TA_COLOR_INITIALS)
        text.SetColor(TRANSPARENT, TA_COLOR_BACKGROUND)
        self.created += [PAGE_INFO, MEMORIZE, INFORMATION]

    def Deactivate(self):
        self.generation += 1
        self.active = False
        self.context = None
        self.selected = None
        for cid in self.created:
            self.window.GetControl(cid).SetVisible(False)
        for row, frame in self.frames.items():
            button = self.window.GetControl(27+row)
            button.SetFrame(frame)
            button.SetFlags(self.flags[row], OP_SET)
            button.SetState(IE_GUI_BUTTON_LOCKED)
            button.SetVisible(True)

    def Update(self, pc, kind, level, known, memorize, info, current_level):
        rows = []
        for record, original in known:
            ref = record['SpellResRef']
            spell = GemRB.GetSpell(ref)
            rows.append((pc, kind, level, ref, original, GemRB.GetString(spell['SpellName'])))
        context = (pc, kind, level, GemRB.GetPlayerName(pc,0), tuple(rows))
        if context != self.context:
            self.top, self.selected = 0, None
        self.context, self.rows = context, rows
        self.memorize, self.info, self.current_level = memorize, info, current_level
        self.active = True
        self.Render()

    def Live(self, generation, identity=None):
        if not self.active or Panels.get(self.pack) is not self or self.generation != generation:
            return False
        window = GemRB.GetView(self.pack,2)
        if not window or window.ID != self.window.ID or not window.IsVisible():
            return False
        pc, kind, level, name, _ = self.context
        if GemRB.GameGetSelectedPCSingle() != pc or self.current_level() != level or GemRB.GetPlayerName(pc,0) != name:
            return False
        if Spellbook.HasSorcererBook(pc) or GUICommon.CantUseSpellbookWindow(pc, kind == IE_SPELL_TYPE_PRIEST):
            return False
        if not GemRB.ValidTarget(pc, GA_SELECT | GA_NO_DEAD):
            return False
        if identity is not None:
            if identity not in self.rows or identity[:3] != (pc,kind,level):
                return False
            index = identity[4]
            if index >= GemRB.GetKnownSpellsCount(pc,kind,level):
                return False
            actual = GemRB.GetKnownSpell(pc,kind,level,index)
            if not actual or actual['SpellResRef'] != identity[3]:
                return False
        return True

    def CanMemorize(self, generation, identity):
        if identity is None or not self.Live(generation, identity):
            return False
        pc,kind,level = identity[:3]
        return GemRB.GetMemorizedSpellsCount(pc,kind,level,False) < GemRB.GetMemorizableSpellsCount(pc,kind,level,1)

    def Select(self, identity, generation):
        if not self.Live(generation, identity):
            return
        self.selected = None if self.selected == identity else identity
        self.Render()

    def Move(self, down, generation):
        if not self.Live(generation):
            return
        last = max(0, ((len(self.rows)-1)//ROWS)*ROWS)
        top = min(last, self.top+ROWS) if down else max(0,self.top-ROWS)
        if top != self.top:
            self.top, self.selected = top, None
            self.Render()

    def Memorize(self, identity, generation, icon):
        if self.CanMemorize(generation, identity):
            # Existing ordinary callback owns operation, sound, animation/update.
            self.memorize(icon)

    def Information(self, identity, generation):
        if not self.Live(generation, identity):
            return
        spell = GemRB.GetSpell(identity[3])
        spell['CurrentIndex'] = identity[4]
        if self.pack == 'GUIMG':
            self.info(spell, 'Known')
        else:
            self.info(spell)

    def Scroll(self, delta, generation):
        if self.Live(generation):
            self.window.GetControl(INFORMATION).ScrollDelta(0,delta)

    def Render(self):
        self.generation += 1
        generation = self.generation
        for cid in self.created:
            self.window.GetControl(cid).SetVisible(True)
        for row in range(24):
            icon = self.window.GetControl(27+row)
            icon.SetVisible(row < ROWS and self.top+row < len(self.rows))
            if row >= ROWS:
                icon.OnPress(None)
                icon.OnRightPress(None)
                continue
            name = self.window.GetControl(NAME_BASE+row)
            used = self.top+row < len(self.rows)
            name.SetVisible(used)
            if not used:
                icon.OnPress(None); icon.OnRightPress(None)
                name.OnPress(None); name.OnRightPress(None)
                name.SetText('')
                continue
            identity = self.rows[self.top+row]
            icon.SetFrame({'x':112,'y':228+42*row,'w':44,'h':40})
            icon.SetFlags(IE_GUI_BUTTON_NO_IMAGE | IE_GUI_BUTTON_PICTURE, OP_SET)
            icon.SetState(IE_GUI_BUTTON_ENABLED)
            icon.SetValue(identity[4])
            icon.SetSpellIcon(identity[3],0)
            icon.SetTooltip(identity[5])
            icon.OnPress(lambda button, key=identity, g=generation: self.Memorize(key,g,button))
            icon.OnRightPress(lambda _button, key=identity, g=generation: self.Information(key,g))
            name.SetState(IE_GUI_BUTTON_ENABLED)
            name.SetValue(identity[4])
            name.SetText(identity[5])
            name.SetTooltip(identity[5])
            name.SetColor(SELECTED if identity == self.selected else BLACK)
            name.OnPress(lambda _button, key=identity, g=generation: self.Select(key,g))
            name.OnRightPress(lambda _button, key=identity, g=generation: self.Information(key,g))
        total = len(self.rows)
        self.window.GetControl(PAGE_INFO).SetText('%d/%d (%d-%d/%d)' % (self.top//ROWS+1,max(1,(total+ROWS-1)//ROWS),self.top+1 if total else 0,min(total,self.top+ROWS),total))
        for cid, down, enabled in ((PAGE_UP,False,self.top>0), (PAGE_DOWN,True,self.top+ROWS<total)):
            button = self.window.GetControl(cid)
            button.SetState(IE_GUI_BUTTON_ENABLED if enabled else IE_GUI_BUTTON_DISABLED)
            button.OnPress(lambda _button, d=down, g=generation:self.Move(d,g))
        action = self.window.GetControl(MEMORIZE)
        # Complete localized phrases; no English-only standalone label fallback.
        action.SetText(17189 if self.pack == 'GUIMG' else 17224)
        enabled = self.CanMemorize(generation,self.selected)
        action.SetState(IE_GUI_BUTTON_ENABLED if enabled else IE_GUI_BUTTON_DISABLED)
        action.SetValue(self.selected[4] if self.selected else 0)
        icon = self.window.GetControl(27+self.rows.index(self.selected)-self.top) if self.selected else None
        action.OnPress(lambda _button, key=self.selected, g=generation, target=icon:self.Memorize(key,g,target))
        text = self.window.GetControl(INFORMATION)
        if self.selected:
            spell = GemRB.GetSpell(self.selected[3])
            description = GemRB.GetString(spell['SpellDesc'])
            text.SetText(self.selected[5]+'\n\n'+description)
        else:
            # Instructions remain visible for a disabled book and during its
            # initial hidden render; Live still gates every spell action.
            if not GemRB.GetString(HELP):
                raise RuntimeError('BG2EE spellbook help strref 39254 is missing or empty')
            text.SetText(HELP)
        text.ScrollTo(0,0)
        for cid, delta in ((INFO_UP,250), (INFO_DOWN,-250)):
            self.window.GetControl(cid).OnPress(lambda _button, amount=delta, g=generation:self.Scroll(amount,g))
