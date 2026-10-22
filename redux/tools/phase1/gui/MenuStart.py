"""Private-profile startup; actual load uses the ordinary GUILOAD callback."""
import GemRB
import GUILOAD


def OnLoad():
    GemRB.SetToken("SaveDir", "save")
    GemRB.SetVar("oldgame", 1)
    GemRB.SetVar("PlayMode", 0)
    GemRB.SetMasterScript("BALDUR", "WORLDMAP")
    if len(GemRB.GetSaveGames()) != 1:
        raise RuntimeError("Exactly one copied fixture is required")
    GemRB.SetNextScript("GUILOAD")


def PopulateLoad():
    GUILOAD.ScrollBarUpdated(GUILOAD.ScrollBar)
