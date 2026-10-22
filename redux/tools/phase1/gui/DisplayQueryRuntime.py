"""Fixed API diagnostic: display mode, legacy controls, rejection and RNG control."""
import GemRB
import MenuRuntime as menu

PURE_MINSC = None


def Signals():
    return dict(eq14=GemRB.EvaluateString('CheckStat(Player4,14,7)', True),
                eq12=GemRB.EvaluateString('CheckStat(Player4,12,7)', True),
                gt13=GemRB.EvaluateString('CheckStatGT(Player4,13,7)', True),
                missing=GemRB.EvaluateString('CheckStatGT(Player6,13,7)', True),
                control=GemRB.EvaluateString('CheckStat(Player1,14,7)', True))


def Boundary():
    menu.record('display-query.boundary', True)


def Pure():
    global PURE_MINSC
    GemRB.SetVar('Phase1DisplayKind', 1)
    if GemRB.GetPartySize() != 4 or GemRB.GetPlayerName(4, 0) != 'Minsc':
        raise RuntimeError('Display query requires the bound four-party Minsc fixture')
    before = Signals()
    rows = []
    for pc in range(1, 5):
        for hand in (0, 1):
            raw_before = GemRB.GetPlayerStat(pc, 7)
            details = GemRB.GetCombatDetails(pc, hand, True)
            repeated = GemRB.GetCombatDetails(pc, hand, True)
            rows.append(dict(actor=pc, hand=hand, actor_name=GemRB.GetPlayerName(pc, 0),
                before=raw_before, after=GemRB.GetPlayerStat(pc, 7), details=details,
                repeat_equal=details == repeated))
            if pc == 4 and hand == 0:
                PURE_MINSC = details
    loop_equal = all(GemRB.GetCombatDetails(4, 0, True) == PURE_MINSC for _ in range(128))
    after = Signals()
    expected = dict(eq14=True, eq12=False, gt13=True, missing=False, control=True)
    menu.record('display-query.pure', before == after == expected and loop_equal
        and all(row['before'] == row['after'] and row['repeat_equal'] and row['details'] for row in rows)
        and PURE_MINSC['ToHitStats']['Total'] == 12 and PURE_MINSC['ToHitStats']['Base'] == 14,
        samples=rows, before_signals=before, after_signals=after, repeated_calls=128,
        all_repeats_equal=loop_equal, total_api_calls=144)


def Legacy(explicit):
    GemRB.SetVar('Phase1DisplayKind', 3 if explicit else 2)
    before = GemRB.GetPlayerStat(4, 7)
    details = GemRB.GetCombatDetails(4, 0, False) if explicit else GemRB.GetCombatDetails(4, 0)
    after = GemRB.GetPlayerStat(4, 7)
    menu.record('display-query.legacy-false' if explicit else 'display-query.legacy-default',
        before == (12 if explicit else 14) and after == 12 and details == PURE_MINSC,
        before=before, after=after, details=details, equals_display_result=details == PURE_MINSC)


def Arm3E():
    GemRB.SetVar('Phase1Display3EControl', 1)


def Reject3E():
    GemRB.SetVar('Phase1DisplayKind', 4)
    caught = False
    message = ''
    try:
        GemRB.GetCombatDetails(4, 0, True)
    except RuntimeError as error:
        message = str(error)
        caught = message == 'Display-only combat details require 2E rules'
    menu.record('display-query.reject-3e', caught, error_message=message)


def RNGControl():
    GemRB.SetVar('Phase1DisplayKind', 5)
    result = GemRB.Roll(1, 20, 0)
    menu.record('display-query.rng-control', 1 <= result <= 20, result=result)


def Configure(output, nonce):
    global PURE_MINSC
    PURE_MINSC = None
    menu.Configure(output, nonce)
    GemRB.SetVar('Phase1Display3EControl', 0)
    menu.PLAN = [('display.before', Boundary, True), ('display.rng-control', RNGControl, False),
        ('display.pure', Pure, False), ('display.after-pure', Boundary, True), ('display.legacy-default', lambda: Legacy(False), False),
        ('display.legacy-false', lambda: Legacy(True), False), ('display.arm-3e', Arm3E, False),
        ('display.reject-3e', Reject3E, False),
        ('display.final', Boundary, True)]


def Step():
    GemRB.SetVar('Phase1DisplayKind', 0)
    menu.Step()
