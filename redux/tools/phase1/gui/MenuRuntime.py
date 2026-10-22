"""Bounded normal-loop menu plan. Native host dispatches registered callbacks.

No gameplay cheats, item/effect mutation or generic RPC. Every observation is
separated from its action by a timer/render boundary. Failures remain failures;
known-unimplemented/context-required menus do not become passes.
"""
import importlib
import json
from pathlib import Path
import GemRB
from ie_stats import IE_HITPOINTS
from GUIDefines import IE_SPELL_TYPE_PRIEST, IE_SPELL_TYPE_WIZARD

PACKS = ("GUIOPT", "GUIREC", "GUISAVE", "GUILOAD", "GUIMAP", "GUIWMAP", "GUIJRNL", "GUIMG", "GUIPR", "WIN_KEYS", "OPTWIN", "PORTWIN")
OUTPUT = None
PLAN = []
ROWS = []
INDEX = 0
CAPTURE = 0
SPELL_ACTORS = {}
NONCE = None


def view(pack, wid):
    result = GemRB.GetView(pack, wid)
    return result if result and result.IsVisible() else None


def control(pack, wid, cid):
    window = view(pack, wid)
    if not window:
        raise RuntimeError("Required visible window absent: %s/%d" % (pack, wid))
    result = window.GetControl(cid)
    if not result or not result.IsVisible():
        raise RuntimeError("Required visible control absent: %s/%d/%d" % (pack, wid, cid))
    return result


def record(name, passed, **details):
    ROWS.append(dict(name=name, passed=bool(passed), **details))


def call(module, function):
    return getattr(importlib.import_module(module), function)()


def press(pack, wid, cid):
    item = control(pack, wid, cid)
    if item.Flags & (1 << 29):
        raise RuntimeError("Requested callback is disabled")
    # The native host consumes this request through Control::PerformAction.
    GemRB.SetVar("Phase1PressPack", PACKS.index(pack) + 1)
    GemRB.SetVar("Phase1PressWindow", wid)
    GemRB.SetVar("Phase1PressControl", cid)


def expect_window(name, pack, wid, closed=False):
    window = view(pack, wid)
    record(name, bool(window) != closed, pack=pack, window=wid, expected_closed=closed)
    if window and not closed:
        frame = window.GetFrame()
        record(name + ".positive-area", frame["w"] > 0 and frame["h"] > 0, frame=frame)


def inspect_sheet(pack):
    pc = GemRB.GameGetSelectedPCSingle()
    inv = pack == "GUIINV"
    ids = dict(name=0x10000032 if inv else 0x1000000e,
               hp=0x10000039 if inv else 0x10000029,
               thac0=0x10000055 if inv else 0x10000040,
               damage=0x10000056 if inv else 0x10000041)
    fields = {}
    for name, cid in ids.items():
        item = control(pack, 2, cid)
        fields[name] = dict(text=item.QueryText(), frame=item.GetFrame())
    record(pack + ".selected-name", fields["name"]["text"] == GemRB.GetPlayerName(pc, 0), fields=fields)
    record(pack + ".actual-hp", fields["hp"]["text"] == str(GemRB.GetPlayerStat(pc, IE_HITPOINTS)))
    for name in ("thac0", "damage"):
        record(pack + "." + name + ".available", bool(fields[name]["text"]) and fields[name]["text"] != "—")
    for cid in ((77, 78, 79, 80) if inv else (53, 54, 55, 56)):
        item = control(pack, 2, cid)
        frame = item.GetFrame()
        record(pack + ".detail-%d" % cid, bool(item.QueryText()) and frame["w"] > 0 and frame["h"] > 0,
               text=item.QueryText(), frame=frame)


def inspect_stats(section):
    record("stats.category-%d" % section, GemRB.GetVar("ReduxStatsSection") == section)
    text = control("GUIREC", 2, 45).QueryText()
    record("stats.bounded-page", len(text.splitlines()) <= 12 and bool(text), content=text)
    label = control("GUIREC", 2, 0x7fff0201).QueryText()
    page, total = (int(value.strip()) for value in label.split("/"))
    record("stats.page-state", 1 <= page <= total, page=page, total=total)
    # Probe next/back only when there really is another page. Do not call a
    # disabled callback and then misclassify its refusal as a product failure.
    if total > 1 and page == 1:
        PLAN[INDEX + 1:INDEX + 1] = [
            ("stats.next", lambda: press("GUIREC", 2, 0x7fff0203), False),
            ("stats.next-observed", lambda: expect_page(2), True),
            ("stats.previous", lambda: press("GUIREC", 2, 0x7fff0202), False),
            ("stats.previous-observed", lambda: expect_page(1), True)]


def expect_page(expected):
    actual = control("GUIREC", 2, 0x7fff0201).QueryText()
    record("stats.page-transition", int(actual.split("/")[0]) == expected, actual=actual, expected=expected)


def select_spell_actor(name, kind, required):
    candidates=[]
    for pc in range(1, GemRB.GetPartySize() + 1):
        known=sum(GemRB.GetKnownSpellsCount(pc, kind, level) for level in range(9 if kind==IE_SPELL_TYPE_WIZARD else 7))
        slots=sum(GemRB.GetMemorizableSpellsCount(pc, kind, level, 1) for level in range(9 if kind==IE_SPELL_TYPE_WIZARD else 7))
        candidates.append(dict(pc=pc, name=GemRB.GetPlayerName(pc,0), known=known, slots=slots))
    eligible=[row for row in candidates if row['known'] or row['slots']]
    SPELL_ACTORS[name]=eligible[0]['pc'] if eligible else None
    ROWS.append(dict(name=name+'.applicability', applicable=bool(eligible), candidates=candidates,
                     selected_actor=SPELL_ACTORS[name], status='applicable' if eligible else 'context-gated'))
    if not eligible:
        if required: raise RuntimeError('Required real spellbook actor absent: '+name)
        return
    pc = SPELL_ACTORS[name]
    # A top-window loader resets single selection from walking selection.
    # Use the actual portrait callback first, on a separate timer boundary.
    if GemRB.GameControlGetTargetMode() != 0:
        raise RuntimeError('Portrait would target instead of select')
    portrait = control('PORTWIN', 0, pc - 1)
    if portrait.Value != pc:
        raise RuntimeError('Portrait actor binding differs from eligible actor')
    if importlib.import_module('GUICommonWindows').SelectionChangeHandler:
        raise RuntimeError('Spellbook preparation requires ordinary walking portrait selection')
    press('PORTWIN', 0, pc - 1)


def open_spellbook(name, cid):
    if SPELL_ACTORS.get(name):
        pc = SPELL_ACTORS[name]
        if GemRB.GameGetFirstSelectedPC() != pc:
            raise RuntimeError('Portrait callback did not select eligible walking actor')
        # ToggleSpellWindow consults this channel before the loader (Sorcerer).
        GemRB.GameSelectPCSingle(pc)
        # Wizard_Spells invokes ToggleSpellWindow, which initializes Sorcerer.
        # Direct OpenMageWindow bypasses this ordinary entry point.
        press('OPTWIN',0,cid)


def observe_known_page(pack, pc, kind, level, shown):
    helper=importlib.import_module('EESpellbookInformation')
    panel=helper.Panels.get(pack)
    if not panel or not panel.active or panel.context[:3]!=(pc,kind,level):
        raise RuntimeError('Actual ordinary information panel context absent')
    canonical=lambda r:dict(original_index=r[4],resref=r[3].upper(),name=r[5])
    if [canonical(r)for r in panel.rows]!=shown:
        raise RuntimeError('Helper rows disagree with independent full known-spell API list')
    selected=canonical(panel.selected)if panel.selected else None
    description_ref=GemRB.GetSpell(selected['resref'])['SpellDesc']if selected else None
    action=control(pack,2,0x7fff0413)
    return dict(schema='bg-redux-known-information-page/1',module=helper.__file__,pack=pack,actor=pc,kind=kind,level=level,
        page_size=7,top=panel.top,visible_rows=shown[panel.top:panel.top+7],selected=selected,
        default_help_strref=39254,resolved_help=GemRB.GetString(39254),
        selected_description_ref=description_ref,selected_description=GemRB.GetString(description_ref)if selected else None,
        information_text=control(pack,2,0x7fff0414).QueryText(),
        page_text=control(pack,2,0x7fff0412).QueryText(),
        action_strref=17189 if pack=='GUIMG'else 17224,
        resolved_action_label=GemRB.GetString(17189 if pack=='GUIMG'else 17224),
        action_text=action.QueryText(),action_value=action.Value,action_disabled=bool(action.Flags&(1<<29)),
        all_pages_visited=False,per_label_style_observed=False)

def inspect_spellbook(name, pack):
    if SPELL_ACTORS.get(name):
        expect_window(name,pack,2)
        pc = SPELL_ACTORS[name]
        actual = GemRB.GameGetSelectedPCSingle()
        if actual != pc:
            raise RuntimeError('Spellbook reset to a different actor')
        kind = IE_SPELL_TYPE_WIZARD if pack == 'GUIMG' else IE_SPELL_TYPE_PRIEST
        module = importlib.import_module(pack)
        level = module.MageSpellLevel if pack == 'GUIMG' else module.PriestSpellLevel
        actor_name = GemRB.GetPlayerName(pc, 0)
        shown_name = control(pack, 2, 0x10000035).QueryText()
        record(name+'.displayed-actor', shown_name == actor_name, expected_actor=pc,
               actual_actor=actual, expected_name=actor_name, actual_name=shown_name)
        known = []
        for index in range(GemRB.GetKnownSpellsCount(pc, kind, level)):
            spell = GemRB.GetKnownSpell(pc, kind, level, index)
            resref = spell['SpellResRef']
            known.append(dict(resref=resref, value=index,
                tooltip=GemRB.GetString(GemRB.GetSpell(resref)['SpellName'])))
        known.sort(key=lambda row: row['tooltip'])
        memorized = []
        sorcerer = (bool(getattr(module, 'Sorcerer', False)) if pack == 'GUIMG' else
                    bool(importlib.import_module('Spellbook').HasSorcererBook(pc)))
        if not sorcerer:
            for index in range(min(12, GemRB.GetMemorizedSpellsCount(pc, kind, level, False))):
                spell = GemRB.GetMemorizedSpell(pc, kind, level, index)
                resref = spell['SpellResRef']
                memorized.append(dict(resref=resref, value=index, ready=spell['Flags'],
                    tooltip=GemRB.GetString(GemRB.GetSpell(resref)['SpellName'])))
        if not known and not memorized:
            raise RuntimeError('Displayed spell level has no content; populated-book coverage unproven')
        heading = None
        if not sorcerer:
            heading = dict(schema='bg-redux-ordinary-spellbook-heading/1', strref=11944,
                localized_prefix=GemRB.GetString(11944),
                allocated_count=GemRB.GetMemorizedSpellsCount(pc, kind, level, False),
                capacity=GemRB.GetMemorizableSpellsCount(pc, kind, level, 1),
                level_text=GemRB.GetString(10345), level_token=GemRB.GetToken('SPELLLEVEL'),
                per_label_style_observed=False)
        ROWS.append(dict(name=name+'.content-contract', pack=pack, actor=pc,
            actor_name=actor_name, level=level, sorcerer=sorcerer,
            known=known, memorized=memorized, known_capacity=24 if sorcerer else 7,
            memorized_capacity=0 if sorcerer else 12,
            heading=heading,
            layout_mode='legacy-spontaneous/1' if sorcerer else 'ordinary-information/1',
            information_page=None if sorcerer else observe_known_page(pack,pc,kind,level,
                [dict(original_index=r['value'],resref=r['resref'].upper(),name=r['tooltip'])for r in known]),
            sprite_resource_identity_observed=False))
    else:
        ROWS.append(dict(name=name, passed=None, status='context-gated',
                         reason='No party actor has this actual spellbook; no direct opener bypass'))


def Configure(output, nonce):
    global OUTPUT, PLAN, ROWS, INDEX, CAPTURE, SPELL_ACTORS, NONCE
    if not isinstance(nonce, str) or len(nonce) != 32 or any(c not in '0123456789abcdef' for c in nonce):
        raise ValueError('Menu run requires a fresh 32-digit lowercase hex nonce')
    NONCE = nonce
    OUTPUT, PLAN, ROWS, INDEX, CAPTURE = Path(output), [], [], 0, 0
    SPELL_ACTORS={}
    for key in ("Phase1MenuComplete", "Phase1MenuCapture", "Phase1PressPack", "Phase1FailedChecks", "Phase1DispatchKey", "Phase1NativeKeys", "Phase1NativeCallbacks"):
        GemRB.SetVar(key, 0)
    def add(name, action, capture=False): PLAN.append((name, action, capture))
    def top(name, module, opener, pack, wid=2, inspector=None):
        add(name + ".open", lambda: call(module, opener))
        add(name + ".observed", lambda: (expect_window(name, pack, wid), inspector() if inspector else None), True)
        add(name + ".close", lambda: call("GUICommonWindows", "CloseTopWindow"))
        add(name + ".closed", lambda: expect_window(name + ".closed", pack, wid, True), True)
    add("pause-and-select", lambda: (GemRB.GamePause(1, 3), GemRB.GameSelectPCSingle(1)))
    top("inventory", "GUIINV", "OpenInventoryWindow", "GUIINV", inspector=lambda: inspect_sheet("GUIINV"))
    add("record.open", lambda: call("GUIREC", "OpenRecordsWindow"))
    add("record.observed", lambda: (expect_window("record", "GUIREC", 2), inspect_sheet("GUIREC")), True)
    for section in range(6):
        add("stats.select-%d" % section, lambda section=section: press("GUIREC", 2, 0x7fff0210 + section))
        add("stats.observed-%d" % section, lambda section=section: inspect_stats(section), True)
    for name, button, wid, close in (("information", 1, 4, 24), ("customization", 50, 17, 8), ("kit-description", 52, 24, 2)):
        add(name + ".open-callback", lambda button=button: press("GUIREC", 2, button))
        add(name + ".observed", lambda name=name, wid=wid: expect_window(name, "GUIREC", wid), True)
        if name == "information":
            add("biography.open-callback", lambda: press("GUIREC", 4, 26))
            add("biography.observed", lambda: expect_window("biography", "GUIREC", 12), True)
            add("biography.close-callback", lambda: press("GUIREC", 12, 2))
            add("biography.closed", lambda: expect_window("biography.closed", "GUIREC", 12, True), True)
        add(name + ".close-callback", lambda wid=wid, close=close: press("GUIREC", wid, close))
        add(name + ".closed", lambda name=name, wid=wid: expect_window(name + ".closed", "GUIREC", wid, True), True)
    add("export.open-if-applicable", export_open)
    add("export.observed", export_observe, True)
    add("export.cancel-if-applicable", lambda: press("GUIREC", 13, 5) if view("GUIREC", 13) else None)
    add("export.closed", lambda: expect_window("export.closed", "GUIREC", 13, True), True)
    add("record.close", lambda: call("GUICommonWindows", "CloseTopWindow"))
    add("record.closed", lambda: expect_window("record.closed", "GUIREC", 2, True), True)
    for name,kind,cid,pack,required in (('mage-book',IE_SPELL_TYPE_WIZARD,5,'GUIMG',True),
                                      ('priest-book',IE_SPELL_TYPE_PRIEST,6,'GUIPR',False)):
        add(name+'.select-eligible',lambda name=name,kind=kind,required=required:select_spell_actor(name,kind,required))
        add(name+'.open',lambda name=name,cid=cid:open_spellbook(name,cid))
        add(name+'.observed',lambda name=name,pack=pack:inspect_spellbook(name,pack),True)
        add(name+'.close',lambda name=name:call('GUICommonWindows','CloseTopWindow') if SPELL_ACTORS.get(name) else None)
        add(name+'.closed',lambda name=name,pack=pack:expect_window(name+'.closed',pack,2,True),True)
    add("select-main", lambda: GemRB.GameSelectPCSingle(1))
    top("journal", "GUIJRNL", "OpenJournalWindow", "GUIJRNL")
    top("area-map", "GUIMA", "OpenMapWindow", "GUIMAP")
    top("world-map-view", "GUIMA", "OpenTravelMapWindow", "GUIWMAP", 0)
    add("options.open", lambda: call("GUIOPT", "OpenOptionsWindow"))
    add("options.observed", lambda: expect_window("options", "GUIOPT", 2), True)
    for name, opener, wid, done in (("video", 7, 6, 21), ("audio", 8, 7, 24), ("gameplay", 9, 8, 7)):
        add(name + ".open-callback", lambda opener=opener: press("GUIOPT", 2, opener))
        add(name + ".observed", lambda name=name, wid=wid: expect_window(name, "GUIOPT", wid), True)
        children = {"audio": (("character-sounds", 13, 12, 24),),
                    "gameplay": (("feedback", 5, 9, 26), ("autopause", 6, 10, 11))}.get(name, ())
        for child, button, childwid, childdone in children:
            add(child + ".open-callback", lambda wid=wid, button=button: press("GUIOPT", wid, button))
            add(child + ".observed", lambda child=child, childwid=childwid: expect_window(child, "GUIOPT", childwid), True)
            add(child + ".close-callback", lambda childwid=childwid, childdone=childdone: press("GUIOPT", childwid, childdone))
            add(child + ".closed", lambda child=child, childwid=childwid: expect_window(child + ".closed", "GUIOPT", childwid, True), True)
        if name == "gameplay":
            add("hotkeys.callback", lambda: press("GUIOPT", 8, 51))
            add("hotkeys.transition", inspect_hotkeys, True)
        add(name + ".close-callback", lambda wid=wid, done=done: press("GUIOPT", wid, done))
        add(name + ".closed", lambda name=name, wid=wid: expect_window(name + ".closed", "GUIOPT", wid, True), True)
    add("save.open-callback", lambda: press("GUIOPT", 2, 6))
    add("save.observed", lambda: expect_window("save", "GUISAVE", 0), True)
    add("save.cancel-callback", lambda: press("GUISAVE", 0, 34))
    add("save.closed", lambda: expect_window("save.closed", "GUISAVE", 0, True), True)
    add("options.reopen", lambda: call("GUIOPT", "OpenOptionsWindow"))
    add("load.open-callback", lambda: press("GUIOPT", 2, 5))
    add("load.observed", lambda: expect_window("load", "GUILOAD", 0), True)
    add("load.cancel-callback", lambda: press("GUILOAD", 0, 34))
    add("load.closed", lambda: expect_window("load.closed", "GUILOAD", 0, True), True)
    # Finish ordinary window close callbacks while GameControl still exists,
    # rather than invoking TopWindowClosed during Interface destruction.
    add('finish.close-top',lambda:call('GUICommonWindows','CloseTopWindow'))
    add('finish.closed',lambda:[expect_window('finish.'+pack,pack,wid,True)
        for pack,wid in (('GUIOPT',2),('GUIMG',2),('GUIPR',2))],True)


def inspect_hotkeys():
    # Current source is a TODO. A successful dispatch alone cannot pass it.
    window = GemRB.GetView("SUB_WIN", 1)
    record("hotkeys.opens-real-window", bool(window and window.IsVisible()),
           source_status="GUIOPT.OpenHotkeyOptionsWindow TODO at initial implementation")
    if window and window.IsVisible(): window.Close()


def export_open():
    eligible = importlib.import_module("GUIREC").Exportable(GemRB.GameGetSelectedPCSingle())
    ROWS.append(dict(name="export.applicability", applicable=eligible,
                     status="applicable" if eligible else "context-gated"))
    if eligible: press("GUIREC", 2, 36)


def export_observe():
    eligible = importlib.import_module("GUIREC").Exportable(GemRB.GameGetSelectedPCSingle())
    if eligible: expect_window("export", "GUIREC", 13)
    else: ROWS.append(dict(name="export", status="context-gated", passed=None))


def Step():
    global INDEX, CAPTURE
    GemRB.SetVar("Phase1MenuCapture", 0)
    GemRB.SetVar("Phase1PressPack", 0)
    if INDEX >= len(PLAN):
        GemRB.SetVar("Phase1MenuComplete", 1)
        return
    name, action, capture = PLAN[INDEX]
    GemRB.SetVar('Phase1MenuStep', INDEX + 1)
    try:
        action()
    except Exception as error:
        record(name, False, error=repr(error))
        capture = True
    if capture:
        CAPTURE += 1
        GemRB.SetVar("Phase1MenuCapture", CAPTURE)
    ROWS.append(dict(step=INDEX, action=name, capture=CAPTURE if capture else None))
    INDEX += 1
    GemRB.SetVar("Phase1FailedChecks", sum(row.get("passed") is False for row in ROWS))
    (OUTPUT / "menu-runtime.json").write_text(json.dumps(dict(schema="bg-redux-menu-runtime/1",
        nonce=NONCE, steps=INDEX, planned_steps=len(PLAN), checks=ROWS,
        context_required=["priest memorization/casting needs priest", "store/merchant", "container/bag/loot",
                          "dialogue/cutscene", "character generation", "world travel", "level-up/dual-class",
                          "sequencer/contingency", "rest confirmation", "export/customization submenus"],
        pointer_hit_testing=False, automatic_visual_acceptance=False), indent=2), encoding="utf8")
    GemRB.GamePause(1, 3)
