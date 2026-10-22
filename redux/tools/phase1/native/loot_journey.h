// External adapter only. Ordinary actor action and shipped Container callbacks.
#include "TileMap.h"
#include "Scriptable/Container.h"

static bool LootReload=false, LootTaken=false;
static int LootActionID=-1;
static int LootCommands=0, LootReadyStreak=0, LootCommandSample=-1, LootTakeSample=-1;
static std::vector<std::string> LootDiagnostics;

static Container* LootContainer()
{
    auto* map=core->GetGame()->GetCurrentArea();
    if (!map || map->GetScriptName()!="AR0602") throw std::runtime_error("Required AR0602 absent");
    Container* found=nullptr;
    for (const auto& holder : map->TMap->GetContainers()) {
        auto* c=holder.get();
        // Scriptable::SetScriptName removes internal spaces; AREImporter
        // retains the exact stored container name separately in OriginalName.
        if (c->OriginalName!="Jailkeep Table") continue;
        if (found) throw std::runtime_error("Ambiguous Jailkeep Table");
        found=c;
    }
    if (!found) throw std::runtime_error("Stock table absent");
    if (found->GetScriptName()!="jailkeeptable" || found->Pos!=Point(3109,2829) || found->containerType!=5 || found->Flags!=0 || found->Trapped)
        throw std::runtime_error("Stock table guard differs: "+O({{"position",PointJSON(found->Pos)},
            {"type",NumberJSON(found->containerType)},{"flags",NumberJSON(found->Flags)},{"trapped",NumberJSON(found->Trapped)}}));
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
    return O({{"schema",Q("bg-redux-container-loot-state/1")},{"container",Q(c->OriginalName.c_str())},
        {"container_script_name",Q(c->GetScriptName().c_str())},{"container_runtime_id",NumberJSON(c->GetGlobalID())},
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

static std::string LootGlobal(const char* name)
{
    for (const auto& pair : core->GetGame()->locals)
        if (pair.first==StringView(name)) return NumberJSON(pair.second);
    return "null";
}

static bool LootEligible()
{
    auto* actor=LootPC();
    return LootGlobal("bd_defai")=="1" && actor->GetScript(SCR_CLASS,true)=="BDDEFAI" &&
        !actor->GetCurrentAction() && !actor->GetNextAction() && !actor->InMove() &&
        core->GetFirstSelectedPC(false)==actor && !core->GetCurrentContainer();
}

static std::string LootContext()
{
    auto* actor=LootPC();auto* selected=core->GetFirstSelectedPC(false);
    auto* current=core->GetCurrentContainer();auto action=actor->GetCurrentAction();auto next=actor->GetNextAction();
    std::vector<std::string> scripts,windows;
    for (int slot=0;slot<MAX_SCRIPTS;++slot) scripts.push_back(Q(actor->GetScript(slot,true).c_str()));
    for (const auto* pack : {"GUIW10","GUIW08","GUIW"}) {
        for (auto* view : GetViews(ScriptingGroup_t(pack))) {
            auto* win=dynamic_cast<Window*>(view);const auto* ref=win?win->GetScriptingRef():nullptr;
            if (ref && ref->Id==8) windows.push_back(O({{"pack",Q(pack)},{"id",NumberJSON(ref->Id)},
                {"visible",win->IsVisible()?"true":"false"},{"disabled",win->IsDisabled()?"true":"false"}}));
        }
    }
    return O({{"pc_runtime_id",NumberJSON(actor->GetGlobalID())},{"position",PointJSON(actor->Pos)},
        {"target_container_runtime_id",NumberJSON(LootContainer()->GetGlobalID())},
        {"selected_runtime_id",selected?NumberJSON(selected->GetGlobalID()):"null"},
        {"current_container_runtime_id",current?NumberJSON(current->GetGlobalID()):"null"},
        {"dialogue_flags",NumberJSON(core->GetGameControl()->GetDialogueFlags())},
        {"control_status",NumberJSON(core->GetGame()->ControlStatus)},
        {"party_ai_enabled",(core->GetGame()->ControlStatus&CS_PARTY_AI)?"true":"false"},
        {"game_time",NumberJSON(core->GetGame()->GameTime.load())},
        {"bd_defai",LootGlobal("bd_defai")},{"bdai_reset_timers",LootGlobal("bdai_reset_timers")},
        {"scripts",A(scripts)},{"current_action_id",action?NumberJSON(action->actionID):"null"},
        {"next_action_id",next?NumberJSON(next->actionID):"null"},{"in_move",actor->InMove()?"true":"false"},
        {"windows",A(windows)}});
}

static void LootDiagnostic(const std::string& out, int sample, bool running, bool eligible,
    int commandsBefore, bool issued, const std::string& before, bool complete)
{
    auto row=O({{"sample",NumberJSON(sample)},{"running",running?"true":"false"},
        {"eligible",eligible?"true":"false"},{"readiness_streak",NumberJSON(LootReadyStreak)},
        {"command_count_before",NumberJSON(commandsBefore)},{"command_count_after",NumberJSON(LootCommands)},
        {"command_issued",issued?"true":"false"},{"complete",complete?"true":"false"},
        {"before",before},{"after",complete?LootContext():"null"}});
    if (LootDiagnostics.size()==static_cast<size_t>(sample)) LootDiagnostics.push_back(row);
    else if (LootDiagnostics.size()==static_cast<size_t>(sample+1)) LootDiagnostics.back()=row;
    else throw std::runtime_error("Loot diagnostic sample continuity differs");
    Write(out+"/loot-diagnostics.json",O({{"schema",Q("bg-redux-loot-diagnostics/1")},{"samples",A(LootDiagnostics)}}));
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
    LootDiagnostic(out,0,false,LootEligible(),0,false,LootContext(),true);
    if (reload) { LootTaken=true;return; }
    auto* first=c->inventory.GetSlotItem(0);
    if (!first || first->ItemResRef!="SW1H04") throw std::runtime_error("First stock container item differs");
    // Do not issue a command while the stock area startup ActionOverride is pending.
    // The initial clock-before remains a separate observation from command-before.
}

static void LootTick(const std::string& out, int sample, int endRunning)
{
    const bool running=sample>4 && sample<=endRunning;
    const bool eligible=LootEligible();const auto before=LootContext();const int commandsBefore=LootCommands;
    bool issued=false;
    if (!LootReload && !LootCommands) LootReadyStreak=running && eligible ? LootReadyStreak+1 : 0;
    LootDiagnostic(out,sample,running,eligible,commandsBefore,false,before,false);
    if (!LootReload && !LootCommands && running && LootReadyStreak==4) {
        auto* actor=LootPC();auto* c=LootContainer();
        auto* first=c->inventory.GetSlotItem(0);
        if (actor->inventory.CountItems(ResRef("SW1H04"),false)!=0 || c->inventory.CountItems(ResRef("SW1H04"),false)!=1)
            throw std::runtime_error("Natural startup changed declared item ownership");
        if (!first || first->ItemResRef!="SW1H04") throw std::runtime_error("Command-before first item differs");
        Write(out+"/loot-command-before.json",LootState());Write(out+"/loot-command-before.state.json",Snapshot(core->GetGame()));
        auto action=GenerateAction("UseContainer()");
        if (!action) throw std::runtime_error("Shipped UseContainer action parse failed");
        LootActionID=action->actionID;LootCommandSample=sample;++LootCommands;issued=true;
        // One ordinary command only; never reissue after interruption.
        core->SetCurrentContainer(actor,c);actor->CommandActor(std::move(action));
    } else if (!LootReload && LootCommands==1 && !LootTaken && running) {
        auto* c=LootContainer();
        auto* window=LootWindow();
        if (window) {
            if (core->GetFirstSelectedPC(false)!=LootPC()) throw std::runtime_error("Selected loot destination changed");
            if (core->GetCurrentContainer()!=LootContainer()) throw std::runtime_error("Opened container differs");
            Write(out+"/loot-open.json",LootState());
            if (!core->GetGUIScriptEngine()->ExecString("import GemRB; GemRB.SetVar('LeftIndex', 0)"))
                throw std::runtime_error("Container UI selection failed");
            LootPress(window,0);
            Write(out+"/loot-after-take.json",LootState());
            if (LootPC()->inventory.CountItems(ResRef("SW1H04"),false)!=1 || c->inventory.CountItems(ResRef("SW1H04"),false)!=0)
                throw std::runtime_error("Stock callback did not transfer the declared item");
            LootPress(window,51);LootTaken=true;LootTakeSample=sample;
        }
    }
    LootDiagnostic(out,sample,running,eligible,commandsBefore,issued,before,true);
}

static void LootFinish(const std::string& out)
{
    if (!LootTaken || (!LootReload && (LootActionID<0 || LootCommands!=1 || LootCommandSample<5 || LootReadyStreak!=4))) throw std::runtime_error("Bounded loot journey incomplete");
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
        {"command_count",NumberJSON(LootCommands)},{"command_sample",NumberJSON(LootCommandSample)},
        {"callback_sample",NumberJSON(LootTakeSample)},
        {"action_id",NumberJSON(LootActionID)},{"callback",Q(LootReload?"none":"Container.TakeItemContainer")},
        {"close_callback",Q(LootReload?"none":"Container.LeaveContainer")},{"ui_left_index",LootReload?"null":"0"},
        {"os_pointer_input","false"},{"save_return_code",NumberJSON(saved)},{"forced","false"},{"directories",A(dirs)}}));
    if (saved!=GEM_OK || dirs.size()!=1) throw std::runtime_error("Ordinary loot save failed/ambiguous");
}
