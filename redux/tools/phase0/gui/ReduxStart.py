"""External test startup and bounded selectors; all application screens are stock."""
import GemRB
import GUISAVE
import GUILOAD

def OnLoad():
    GemRB.SetToken('SaveDir', 'save')
    GemRB.SetVar('oldgame', 1)
    GemRB.SetVar('PlayMode', 0)
    GemRB.SetMasterScript('BALDUR', 'WORLDMAP')
    saves = GemRB.GetSaveGames()
    if len(saves) != 1:
        raise RuntimeError('Exactly one copied baseline fixture is required')
    GemRB.SetNextScript('GUILOAD')

def PopulateLoad():
    GUILOAD.ScrollBarUpdated(GUILOAD.ScrollBar)

def Ready():
    GemRB.GamePause(1, 3)
    GemRB.GameSelectPCSingle(1)

def ChooseNewRow():
    # Semantic scroll; the row and confirmation are dispatched through controls.
    count = len(GUISAVE.Games)
    GUISAVE.ScrollBar.SetVarAssoc('TopIndex', count, 0, count)
    GUISAVE.ScrollBarPress()

def ChooseExistingRow():
    matches = [i for i,s in enumerate(GUISAVE.Games) if s.GetName() == 'Redux GUI Baseline']
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one GUI-created save in the picker')
    pos = matches[0]
    GUISAVE.ScrollBar.SetVarAssoc('TopIndex', pos, 0, len(GUISAVE.Games))
    GUISAVE.ScrollBarPress()

def VerifyCreated():
    saves = [s for s in GemRB.GetSaveGames() if s.GetName() == 'Redux GUI Baseline']
    if len(saves) != 1 or saves[0].GetPreview() is None:
        raise RuntimeError('GUI save is absent, duplicated or missing its preview')
