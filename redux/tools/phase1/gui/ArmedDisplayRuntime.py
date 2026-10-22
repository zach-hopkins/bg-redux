"""Actual display API and Record/Inventory callbacks on bound armed fixtures."""
import importlib
import json
import GemRB
import MenuRuntime as menu

EXPECTED = None
PURE = None
REPEATS = 32


def Boundary():
    menu.record('armed.boundary', True)


def Matrix(phase):
    global PURE
    GemRB.SetVar('Phase1DisplayKind', 1)
    if GemRB.GetPartySize() != 2:
        raise RuntimeError('Armed display requires exactly two bound actors')
    samples = []
    for pc in (1, 2):
        for hand in (0, 1):
            before = GemRB.GetPlayerStat(pc, 7)
            values = [GemRB.GetCombatDetails(pc, hand, True) for _ in range(REPEATS)]
            details = values[0]
            slot = GemRB.GetSlotItem(pc, details['Slot'], 1) if details else None
            samples.append(dict(actor=pc, hand=hand, actor_name=GemRB.GetPlayerName(pc, 0),
                before=before, after=GemRB.GetPlayerStat(pc, 7),
                dual=bool(GemRB.IsDualWielding(pc)), item=slot['ItemResRef'] if slot else None,
                details=details, repeat_equal=all(value == details for value in values)))
    if phase == 'cold':
        PURE = samples
    menu.record('armed.matrix.'+phase, all(s['before']==s['after'] and s['repeat_equal'] and s['details'] for s in samples)
        and (phase == 'cold' or samples == PURE), samples=samples, api_calls=4*REPEATS, repeats=REPEATS)


def Legacy(explicit):
    GemRB.SetVar('Phase1DisplayKind', 3 if explicit else 2)
    samples = []
    for pc in (1, 2):
        for hand in (0, 1):
            before = GemRB.GetPlayerStat(pc, 7)
            details = GemRB.GetCombatDetails(pc, hand, False) if explicit else GemRB.GetCombatDetails(pc, hand)
            samples.append(dict(actor=pc,hand=hand,before=before,after=GemRB.GetPlayerStat(pc,7),details=details))
    equal = [s['details'] for s in samples] == [s['details'] for s in PURE]
    menu.record('armed.legacy-false' if explicit else 'armed.legacy-default', equal,
                samples=samples, equals_display_result=equal)


def Portrait(pc):
    button = menu.control('PORTWIN', 0, pc-1)
    if button.Value != pc:
        raise RuntimeError('Armed portrait does not bind requested actor')
    menu.press('PORTWIN', 0, pc-1)


def Observe(pack, pc):
    sheet = importlib.import_module('EECharacterSheet')
    model = sheet.ReadActor(pc)
    panels = sheet.PanelText(model)
    headline = '/'.join(str(h['thac0']) for h in model['hands']) or '—'
    ids = (53,54,55,56) if pack == 'GUIREC' else (77,78,79,80)
    actual = [menu.control(pack,2,cid).QueryText() for cid in ids]
    thac0 = menu.control(pack,2,0x10000040 if pack=='GUIREC' else 0x10000055).QueryText()
    expected = [s['details'] for s in PURE if s['actor']==pc]
    expected = expected if GemRB.IsDualWielding(pc) else expected[:1]
    menu.record('armed.sheet', GemRB.GameGetSelectedPCSingle()==pc and actual==panels
        and thac0==headline and [h['details'] for h in model['hands']]==expected,
        pack=pack,actor=pc,actor_name=GemRB.GetPlayerName(pc,0),
        panels=actual,headline=thac0,details=[h['details'] for h in model['hands']])


def RNGControl():
    GemRB.SetVar('Phase1DisplayKind', 5)
    value = GemRB.Roll(1,20,0)
    menu.record('armed.rng-control', 1 <= value <= 20, result=value)


def Configure(output, nonce):
    global EXPECTED, PURE
    PURE = None
    menu.Configure(output,nonce)
    EXPECTED = json.loads((menu.OUTPUT/'armed-input.json').read_text(encoding='utf8'))
    GemRB.SetVar('Phase1Display3EControl',0)
    menu.PLAN = [
        ('armed.before',Boundary,True),('armed.rng-control',RNGControl,False),
        ('armed.cold',lambda: Matrix('cold'),False),('armed.after-cold',Boundary,True),
        ('armed.record.open',lambda: menu.call('GUIREC','OpenRecordsWindow'),False),
        ('armed.record.actor1',lambda: Observe('GUIREC',1),True),
        ('armed.record.portrait2',lambda: Portrait(2),False),
        ('armed.record.actor2',lambda: Observe('GUIREC',2),True),
        ('armed.record.close',lambda: menu.call('GUICommonWindows','CloseTopWindow'),False),
        ('armed.inventory.open',lambda: menu.call('GUIINV','OpenInventoryWindow'),False),
        ('armed.inventory.portrait2',lambda: Portrait(2),False),
        ('armed.inventory.actor2',lambda: Observe('GUIINV',2),True),
        ('armed.inventory.portrait1',lambda: Portrait(1),False),
        ('armed.inventory.actor1',lambda: Observe('GUIINV',1),True),
        ('armed.inventory.close',lambda: menu.call('GUICommonWindows','CloseTopWindow'),False),
        ('armed.after-gui',Boundary,True),('armed.refreshed',lambda: Matrix('refreshed'),False),
        ('armed.legacy-default',lambda: Legacy(False),False),
        ('armed.legacy-false',lambda: Legacy(True),False),('armed.final',Boundary,True)]


def Step():
    GemRB.SetVar('Phase1DisplayKind',0)
    menu.Step()
