// External adapter only. Ordinary actor action and shipped Container callbacks.
#include "TileMap.h"
#include "Scriptable/Container.h"

static bool LootReload=false, LootTaken=false;
static int LootActionID=-1;

static Container* LootContainer()
{
    auto* map=core->GetGame()->GetCurrentArea();
    if (!map || map->GetScriptName()!="AR0602") throw std::runtime_error("Required AR0602 absent");
    Container* found=nullptr;
    for (const auto& holder : map->TMap->GetContainers()) {
        auto* c=holder.get();
        if (c->GetScriptName()!="Jailkeep Table") continue;
        if (found) throw std::runtime_error("Ambiguous Jailkeep Table");
        found=c;
    }
    if (!found || found->Pos!=Point(3109,2829) || found->containerType!=5 || found->Flags!=0 || found->Trapped)
        throw std::runtime_error("Stock table identity/position/type/lock/trap guard differs");
    return found;
}

static Actor* LootPC()
{
    auto* actor=core->GetGame()->GetPC(0,false);
    if (!actor || actor->GetCurrentArea()!=core->GetGame()->GetCurrentArea())
        throw std::runtime_error("Required party leader absent from current area");
    return actor;
}

static std::string LootState()
{
    auto* c=LootContainer();auto* actor=LootPC();
    return O({{"schema",Q("bg-redux-container-loot-state/1")},{"container",Q(c->GetScriptName().c_str())},{"container_runtime_id",NumberJSON(c->GetGlobalID())},
        {"position",PointJSON(c->Pos)},{"type",NumberJSON(c->containerType)},{"flags",NumberJSON(c->Flags)},
        {"trapped",NumberJSON(c->Trapped)},{"container_inventory",InventoryJSON(c->inventory)},
        {"pc_runtime_id",NumberJSON(actor->GetGlobalID())},{"pc_position",PointJSON(actor->Pos)},{"pc_inventory",InventoryJSON(actor->inventory)},
        {"game_time",NumberJSON(core->GetGame()->GameTime.load())}});
}

static Window* LootWindow()
{
    for (const auto* pack : {"GUIW10","GUIW08","GUIW"}) {
        for (auto* view : GetViews(ScriptingGroup_t(pack))) {
            auto* win=dynamic_cast<Window*>(view);
            if (win && win->GetScriptingRef() && win->GetScriptingRef()->Id==8 && win->IsVisible()) return win;
        }
    }
    return nullptr;
}

static void LootPress(Window* window, ScriptingId id)
{
    auto* control=GetControl(id,window);
    if (!control || control->IsDisabled() || !control->IsVisible() || !control->PerformAction())
        throw std::runtime_error("Stock container callback refused dispatch");
}

static void LootStart(const std::string& out, bool reload)
{
    LootReload=reload;auto* c=LootContainer();auto* actor=LootPC();
    if (!core->GetGUIScriptEngine()->ExecString("import GemRB; from GUIDefines import SELECT_REPLACE; GemRB.GameSelectPC(1, 1, SELECT_REPLACE)"))
        throw std::runtime_error("Party leader selection failed");
    if (core->GetFirstSelectedPC(false)!=actor) throw std::runtime_error("Loot destination selection differs");
    Write(out+"/loot-before.json",LootState());Write(out+"/loot-before.state.json",Snapshot(core->GetGame()));
    const int wanted=reload?1:0;
    if (actor->inventory.CountItems(ResRef("SW1H04"),false)!=wanted ||
        c->inventory.CountItems(ResRef("SW1H04"),false)!=(reload?0:1))
        throw std::runtime_error("Declared source/destination item preconditions differ");
    if (reload) { LootTaken=true;return; }
    auto* first=c->inventory.GetSlotItem(0);
    if (!first || first->ItemResRef!="SW1H04") throw std::runtime_error("First stock container item differs");
    auto action=GenerateAction("UseContainer()");
    if (!action) throw std::runtime_error("Shipped UseContainer action parse failed");
    LootActionID=action->actionID;
    // Same operation pair as GameControl::HandleContainer normal target mode.
    // This bypasses hit testing/OS pointer input, not the actor's ordinary action.
    core->SetCurrentContainer(actor,c);actor->CommandActor(std::move(action));
}

static void LootTick(const std::string& out, int sample)
{
    if (LootReload || LootTaken || sample<=4) return;
    auto* window=LootWindow();if (!window) return;
    if (core->GetFirstSelectedPC(false)!=LootPC()) throw std::runtime_error("Selected loot destination changed");
    if (core->GetCurrentContainer()!=LootContainer()) throw std::runtime_error("Opened container differs");
    Write(out+"/loot-open.json",LootState());
    // UI selection parameter only; never an outcome/global/quest marker.
    if (!core->GetGUIScriptEngine()->ExecString("import GemRB; GemRB.SetVar('LeftIndex', 0)"))
        throw std::runtime_error("Container UI selection failed");
    LootPress(window,0); // stock Container.TakeItemContainer -> ChangeContainerItem
    Write(out+"/loot-after-take.json",LootState());
    if (LootPC()->inventory.CountItems(ResRef("SW1H04"),false)!=1 ||
        LootContainer()->inventory.CountItems(ResRef("SW1H04"),false)!=0)
        throw std::runtime_error("Stock callback did not transfer the declared item");
    LootPress(window,51); // stock LeaveContainer
    LootTaken=true;
}

static void LootFinish(const std::string& out)
{
    if (!LootTaken || (!LootReload && LootActionID<0)) throw std::runtime_error("Bounded loot journey incomplete");
    if (LootWindow()) throw std::runtime_error("Container window did not close");
    Write(out+"/loot-after.json",LootState());Write(out+"/loot-before-save.state.json",Snapshot(core->GetGame()));
    const int saved=core->GetSaveGameIterator()->CreateSaveGame(Holder<SaveGame>(),StringView("Redux Loot Journey"),
        core->GetWindowManager()->GetScreenshotPreview(),false);
    Write(out+"/loot-after-save.state.json",Snapshot(core->GetGame()));
    std::vector<std::string> dirs;
    for (const auto& save : core->GetSaveGameIterator()->GetSaveGames())
        if (save->GetName()==u"Redux Loot Journey") dirs.push_back(Q(save->GetPath()));
    Write(out+"/loot-result.json",O({{"schema",Q("bg-redux-container-loot-native/1")},
        {"reload",LootReload?"true":"false"},{"completed",LootTaken?"true":"false"},
        {"action_id",NumberJSON(LootActionID)},{"callback",Q(LootReload?"none":"Container.TakeItemContainer")},
        {"close_callback",Q(LootReload?"none":"Container.LeaveContainer")},{"ui_left_index",LootReload?"null":"0"},
        {"os_pointer_input","false"},{"save_return_code",NumberJSON(saved)},{"forced","false"},{"directories",A(dirs)}}));
    if (saved!=GEM_OK || dirs.size()!=1) throw std::runtime_error("Ordinary loot save failed/ambiguous");
}
