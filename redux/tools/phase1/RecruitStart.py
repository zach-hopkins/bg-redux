"""Private external startup/selectors; application load/save screens stay stock."""
import GemRB
import GUILOAD
import GUISAVE
import GUIOPT

def OnLoad():
    GemRB.SetToken('SaveDir', 'save')
    GemRB.SetVar('oldgame', 1)
    GemRB.SetVar('PlayMode', 0)
    GemRB.SetMasterScript('BALDUR', 'WORLDMAP')
    if len(GemRB.GetSaveGames()) != 1:
        raise RuntimeError('Exactly one immutable copied dialogue input required')
    GemRB.SetNextScript('GUILOAD')

def PopulateLoad():
    GUILOAD.ScrollBarUpdated(GUILOAD.ScrollBar)

def SelectLeader():
    from GUIDefines import SELECT_REPLACE
    GemRB.GameSelectPC(1, 1, SELECT_REPLACE)

def OpenOptions():
    GUIOPT.OpenOptionsWindow()

def ChooseNewSave():
    count = len(GUISAVE.Games)
    GUISAVE.ScrollBar.SetVarAssoc('TopIndex', count, 0, count)
    GUISAVE.ScrollBarPress()
