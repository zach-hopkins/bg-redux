"""Ordinary portrait/record callbacks across the immutable four-party fixture."""
import importlib
import GemRB
import MenuRuntime as menu
from ie_stats import IE_CLASS, IE_LEVEL, IE_LEVEL2, IE_LEVEL3


def Configure(output, nonce):
    menu.Configure(output, nonce)
    menu.PLAN = [('stats.prepare', Prepare, False)]


def Portrait(pc):
    button = menu.control('PORTWIN', 0, pc - 1)
    if button.Value != pc:
        raise RuntimeError('Portrait control does not bind requested party member')
    menu.press('PORTWIN', 0, pc - 1)


def Selected(pc):
    menu.record('stats.actor-selected', GemRB.GameGetSelectedPCSingle() == pc
        and GemRB.GetVar('ReduxStatsSection') == 0 and GemRB.GetVar('ReduxStatsPage') == 0,
        actor=pc, actor_name=GemRB.GetPlayerName(pc, 0),
        actor_class=GemRB.GetPlayerStat(pc, IE_CLASS),
        levels=[GemRB.GetPlayerStat(pc, stat) for stat in (IE_LEVEL, IE_LEVEL2, IE_LEVEL3)],
        states=list(GemRB.GetPlayerStates(pc)))
    menu.inspect_sheet('GUIREC')


def Observe(pc, section, page, pages):
    text = menu.control('GUIREC', 2, 45).QueryText()
    label = menu.control('GUIREC', 2, 0x7fff0201).QueryText()
    menu.record('stats.actor-page', GemRB.GameGetSelectedPCSingle() == pc
        and GemRB.GetVar('ReduxStatsSection') == section
        and GemRB.GetVar('ReduxStatsPage') == page
        and text == pages[page] and label == '%d / %d' % (page + 1, len(pages)),
        actor=pc, section=section, page=page, pages=len(pages), content=text)


def Section(pc, section):
    rec = importlib.import_module('GUIREC')
    sheet = importlib.import_module('EECharacterSheet')
    raw = rec.GetSupplementalStats(pc)[section]
    pages = sheet.Pages(raw)
    menu.ROWS.append(dict(name='stats.actor-section-contract', actor=pc, section=section,
                          raw=raw, pages=pages))
    Observe(pc, section, 0, pages)
    steps = []
    sequence = list(range(1, len(pages))) + list(range(len(pages) - 2, -1, -1))
    for index, target in enumerate(sequence):
        cid = 0x7fff0203 if index < len(pages) - 1 else 0x7fff0202
        label = 'stats.actor-%d.section-%d.page-%d.visit-%d' % (pc, section, target, index)
        steps.extend([(label + '.press', lambda cid=cid: menu.press('GUIREC', 2, cid), False),
                      (label + '.observed', lambda target=target: Observe(pc, section, target, pages), True)])
    menu.PLAN[menu.INDEX + 1:menu.INDEX + 1] = steps


def Prepare():
    if GemRB.GetPartySize() != 4:
        raise RuntimeError('Stats journey requires the bound four-party fixture')
    menu.PLAN.append(('stats.record.open', lambda: menu.call('GUIREC', 'OpenRecordsWindow'), False))
    for pc in range(1, 5):
        menu.PLAN.extend([
            ('stats.actor-%d.portrait' % pc, lambda pc=pc: Portrait(pc), False),
            ('stats.actor-%d.selected' % pc, lambda pc=pc: Selected(pc), True)])
        for section in range(6):
            prefix = 'stats.actor-%d.section-%d' % (pc, section)
            menu.PLAN.extend([
                (prefix + '.select', lambda section=section: menu.press('GUIREC', 2, 0x7fff0210 + section), False),
                (prefix + '.observed', lambda pc=pc, section=section: Section(pc, section), True)])
    menu.PLAN.extend([
        ('stats.record.close', lambda: menu.call('GUICommonWindows', 'CloseTopWindow'), False),
        ('stats.record.closed', lambda: menu.expect_window('stats.closed', 'GUIREC', 2, True), True)])


Step = menu.Step
