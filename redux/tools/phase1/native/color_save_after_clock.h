// External-only hook for the frozen normal-loop GUI host. No engine mutation API.
static void ColorSaveAfterClock(const std::string& out)
{
    Write(out+"/color-before-save.state.json", Snapshot(core->GetGame()));
    const int saved = core->GetSaveGameIterator()->CreateSaveGame(Holder<SaveGame>(),
        StringView("Redux Color Cycle"), core->GetWindowManager()->GetScreenshotPreview(), false);
    Write(out+"/color-after-save.state.json", Snapshot(core->GetGame()));
    std::vector<std::string> directories;
    for (const auto& save : core->GetSaveGameIterator()->GetSaveGames()) {
        if (save->GetName() == u"Redux Color Cycle") directories.push_back(Q(save->GetPath()));
    }
    Write(out+"/color-save-result.json", O({{"schema",Q("bg-redux-color-save-native/1")},
        {"save_return_code",NumberJSON(saved)}, {"forced","false"}, {"directories",A(directories)},
        {"boundary",Q("after paused-final clock samples; ordinary CreateSaveGame")}}));
    if (saved != GEM_OK || directories.size() != 1)
        throw std::runtime_error("Ordinary color save failed or output is ambiguous");
}
