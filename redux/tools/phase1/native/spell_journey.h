// External callback adapter. Never grants spells or writes game globals/stats.
#include "GUI/Button.h"
static bool SpellReload=false, SpellCompleted=false, SpellOpened=false;
static int SpellStreak=0, SpellPresses=0, SpellCommand=-1, SpellOpenSample=-1, SpellRelease=-1, SpellActionID=-1;
static std::vector<std::string> SpellRows;
static Actor* SpellPC() {
    auto* g=core->GetGame();auto* a=g->GetPC(1,false);
    if (g->GetPartySize(false)!=2 || !a || a->GetScriptName()!="imoen" || a->GetCurrentArea()!=g->GetCurrentArea() || g->CurrentArea!="AR0602")
        throw std::runtime_error("Declared Imoen/party/area absent");
    return a;
}
static Window* SpellWindow(const char* alias) {
    Window* result=nullptr;
    for (auto* v:GetViews(ScriptingGroup_t(alias))) if (auto* w=dynamic_cast<Window*>(v)) {
        if (result && result!=w) throw std::runtime_error("Ambiguous GUI alias");result=w;
    }
    if (!result || !result->IsVisible() || result->IsDisabled()) throw std::runtime_error(std::string("GUI alias unavailable: ")+alias);
    return result;
}
static void SpellExec(const std::string& code) {
    auto script=core->GetGUIScriptEngine();
    if (!script->ExecString(code)) throw std::runtime_error("Stock spell GUI script failed");
}
static void SpellShot(const std::string& out,const std::string& name) {
    PluginHolder<ImageWriter> writer=MakePluginHolder<ImageWriter>(PLUGIN_IMAGE_WRITER_BMP);
    FileStream file;
    if (!writer || !file.Create(out,name,IE_BMP_CLASS_ID)) throw std::runtime_error("Spell screenshot unavailable");
    writer->PutImage(&file,core->GetWindowManager()->GetScreenshot(nullptr));
}
static Control* SpellControl(Window* w,int id) {
    auto* b=GetControl(id,w);
    if (!b || b->IsDisabled() || !b->IsVisible()) throw std::runtime_error("Declared callback control unavailable/disabled");
    return b;
}
static void SpellPress(Control* b) {
    // Native PerformAction invokes the real callback but does not update the bound
    // GUI dictionary itself. Rebind the identical existing UI value first; no
    // game global, selected spell index, or constructor outcome is fabricated.
    if (b->IsDictBound()) { const auto variable=b->DictVariable();b->BindDictVariable(variable,b->GetValue(),b->GetValueRange()); }
    if (!b->PerformAction()) throw std::runtime_error("Stock callback refused");
}
static std::string SpellAction(const Holder<Action>& a) {
    if (!a) return "null";
    auto target=a->objects[1];
    return O({{"id",NumberJSON(a->actionID)},{"resref",Q(a->resref0Parameter.c_str())},
        {"target_mode",target?NumberJSON(target->objectFields[0]):"null"},
        {"target_id",target?NumberJSON(target->objectFields[1]):"null"}});
}
static std::string SpellGlobal(const char* name) {
    for (const auto& row:core->GetGame()->locals) if (row.first==StringView(name)) return NumberJSON(row.second);
    return "null";
}
static bool SpellEligible() {
    auto* a=SpellPC();auto* g=core->GetGame();auto* leader=g->GetPC(0,false);
    return SpellGlobal("bd_defai")=="1" && leader->GetScript(SCR_CLASS,true)=="BDDEFAI" &&
        !a->GetCurrentAction() && !a->GetNextAction() && !a->InMove() &&
        g->selected.size()==1 && core->GetFirstSelectedPC(false)==a;
}
static std::string SpellContext() {
    auto* a=SpellPC();auto* g=core->GetGame();auto* selected=core->GetFirstSelectedPC(false);
    return O({{"actor",ActorJSON(a)},{"game_time",NumberJSON(g->GameTime.load())},
        {"selected_id",selected?NumberJSON(selected->GetGlobalID()):"null"},{"selected_count",NumberJSON(g->selected.size())},
        {"bd_defai",SpellGlobal("bd_defai")},{"leader_class_script",Q(g->GetPC(0,false)->GetScript(SCR_CLASS,true).c_str())},
        {"current",SpellAction(a->GetCurrentAction())},{"next",SpellAction(a->GetNextAction())},
        {"in_move",a->InMove()?"true":"false"},{"current_action_target",NumberJSON(a->CurrentActionTarget)},
        {"last_spell_target",NumberJSON(a->objects.LastSpellTarget)},{"casting_resref",Q(a->SpellResRef.c_str())},
        {"action_state",NumberJSON(a->CurrentActionState)},{"action_ticks",NumberJSON(a->CurrentActionTicks)}});
}
static int SpellReady() {
    auto* a=SpellPC();int n=0;
    for (unsigned i=0;i<a->spellbook.GetMemorizedSpellsCount(1,0,false);++i) {
        const auto* s=a->spellbook.GetMemorizedSpell(1,0,i);
        if (s && s->SpellResRef=="SPWI102" && s->Flags) ++n;
    }
    return n;
}
static bool SpellEffects() {
    auto* a=SpellPC();bool ac=false,icon=false;auto it=a->fxqueue.GetFirstEffect();
    while (const auto* fx=a->fxqueue.GetNextEffect(it)) {
        if (fx->SourceRef!="SPWI102" || (!SpellReload && fx->CasterID!=a->GetGlobalID()) || fx->Duration<=core->GetGame()->GameTime.load()) continue;
        if (fx->Opcode==0 && fx->Parameter1==6 && fx->Parameter2==16) ac=true;
        if (fx->Opcode==142 && fx->Parameter2==12) icon=true;
    }
    return ac && icon;
}
static void SpellStart(const std::string& out,bool reload) {
    SpellReload=reload;auto* a=SpellPC();
    auto* p=SpellControl(SpellWindow("PORTWIN"),1);
    if (!p->IsDictBound() || p->DictVariable()!=StringView("portrait") || p->GetValue()!=2) throw std::runtime_error("Actual Imoen portrait binding differs");
    Write(out+"/spell-portrait-before.state.json",Snapshot(core->GetGame()));SpellShot(out,"spell-before-portrait");
    SpellPress(p);
    if (core->GetGame()->selected.size()!=1 || core->GetFirstSelectedPC(false)!=a) throw std::runtime_error("Portrait callback did not select only Imoen");
    Write(out+"/spell-before.state.json",Snapshot(core->GetGame()));SpellShot(out,"spell-before");
    if (SpellReady()!=(reload?0:1) || SpellEffects()!=reload) throw std::runtime_error("Loaded ready/effect preconditions differ");
    auto action=GenerateActionDirect("NIDSpecial6()",a);
    if (!action || !action->objects[1] || action->objects[1]->objectFields[0]!=-1 || action->objects[1]->objectFields[1]!=static_cast<int>(a->GetGlobalID())) throw std::runtime_error("Shipped self spell action parse failed");
    SpellActionID=action->actionID; // parse only; this diagnostic action is never queued.
    SpellRows.push_back(O({{"sample","0"},{"running","false"},{"eligible",SpellEligible()?"true":"false"},{"streak","0"},{"press_count","0"},{"opened","false"},{"issued","false"},{"before",SpellContext()},{"after",SpellContext()}}));
}
static void SpellTick(const std::string& out,int sample,int endRunning) {
    const bool running=sample>4 && sample<=endRunning, eligible=SpellEligible();const auto before=SpellContext();bool issued=false,opened=false;
    if (!SpellReload && !SpellOpened) SpellStreak=running && eligible?SpellStreak+1:0;
    if (!SpellReload && !SpellOpened && SpellStreak==4) {
        if (SpellReady()!=1 || SpellEffects()) throw std::runtime_error("Natural initialization altered spell preconditions");
        Write(out+"/spell-cast-before.state.json",Snapshot(core->GetGame()));SpellShot(out,"spell-cast-before");
        ActionButtonRow row;SpellPC()->GetActionButtonRow(row);int cast=-1;
        for (int i=0;i<GUIBT_COUNT;++i) if (row[i]==2) {if(cast!=-1) throw std::runtime_error("Ambiguous stock Cast button");cast=i;}
        if(cast<0) throw std::runtime_error("Stock Cast action absent");
        auto* castButton=SpellControl(SpellWindow("ACTWIN"),cast);SpellOpened=true;SpellOpenSample=sample;opened=true;SpellPress(castButton);
        Write(out+"/spell-cast-button.json",O({{"control",NumberJSON(cast)},{"action","2"},{"visible","true"},{"disabled","false"}}));
    } else if (!SpellReload && SpellOpened && !SpellPresses && running) {
        if (!eligible || sample!=SpellOpenSample+1) throw std::runtime_error("Cast icon readiness lost; no retry");
        Write(out+"/spell-command-before.state.json",Snapshot(core->GetGame()));SpellShot(out,"spell-command-before");
        auto* window=SpellWindow("ACTWIN");Control* found=nullptr;SpellExtHeader chosen{};int control=-1;
        for(int i=0;i<GUIBT_COUNT;++i) {
            auto* b=GetControl(i,window);if(!b || !b->IsDictBound() || b->DictVariable()!=StringView("Spell")) continue;
            const auto value=b->GetValue();SpellExtHeader info{};
            if(value>=0 && SpellPC()->spellbook.GetSpellInfo(info,value/1000,value%1000) && info.spellName=="SPWI102") {
                if(found) throw std::runtime_error("Ambiguous resref-bound spell icon");found=b;chosen=info;control=i;
            }
        }
        if(!found || found->IsDisabled() || !found->IsVisible() || chosen.Target!=5 || chosen.type!=1 || chosen.level!=0) throw std::runtime_error("Enabled self SPWI102 icon absent");
        Write(out+"/spell-button.json",O({{"spell_control",NumberJSON(control)},
            {"resref",Q(chosen.spellName.c_str())},{"target",NumberJSON(chosen.Target)},{"type",NumberJSON(chosen.type)},
            {"level",NumberJSON(chosen.level)},{"slot",NumberJSON(chosen.slot)},{"ready_count",NumberJSON(chosen.count)},
            {"header_index",NumberJSON(chosen.headerindex)},{"casting_time",NumberJSON(chosen.CastingTime)},
            {"dict_name",Q(found->DictVariable().c_str())},{"dict_value",NumberJSON(found->GetValue())},{"visible","true"},{"disabled","false"}}));
        SpellShot(out,"spell-icons");
        // Count before dispatch so a callback failure cannot trigger a retry.
        ++SpellPresses;SpellCommand=sample;issued=true;SpellPress(found);
        Write(out+"/spell-command-after.state.json",Snapshot(core->GetGame()));SpellShot(out,"spell-command-after");
    }
    if (!SpellReload && SpellPresses==1 && SpellRelease<0 && sample>SpellCommand && SpellReady()==0 && SpellEffects() &&
        !SpellPC()->GetCurrentAction() && !SpellPC()->GetNextAction()) {
        SpellRelease=sample;SpellCompleted=true;Write(out+"/spell-released.state.json",Snapshot(core->GetGame()));SpellShot(out,"spell-released");
    }
    SpellRows.push_back(O({{"sample",NumberJSON(sample)},{"running",running?"true":"false"},{"eligible",eligible?"true":"false"},
        {"streak",NumberJSON(SpellStreak)},{"press_count",NumberJSON(SpellPresses)},{"opened",opened?"true":"false"},{"issued",issued?"true":"false"},{"before",before},{"after",SpellContext()}}));
    Write(out+"/spell-diagnostics.json",O({{"schema",Q("bg-redux-spell-diagnostics/1")},{"samples",A(SpellRows)}}));
}
static void SpellFinish(const std::string& out) {
    if ((!SpellReload && (!SpellCompleted || SpellPresses!=1 || SpellRelease<=SpellCommand)) || SpellReady()!=0 || !SpellEffects()) throw std::runtime_error("Bounded ordinary cast incomplete");
    Write(out+"/spell-before-save.state.json",Snapshot(core->GetGame()));SpellShot(out,"spell-before-save");
    // Follow the same shipped GUI save route as the established normal-loop host.
    SpellExec("import GUIOPT; GUIOPT.OpenOptionsWindow()");
    auto press=[](const char* pack,int win,int id) {auto* w=GetWindow(win,ScriptingGroup_t(pack));if(!w) throw std::runtime_error("GUI save window missing");SpellPress(SpellControl(w,id));};
    press("GUIOPT",2,6);SpellExec("import ReduxStart; ReduxStart.ChooseNewRow()");press("GUISAVE",0,26);
    auto* confirm=GetWindow(1,ScriptingGroup_t("GUISAVE"));if(!confirm) throw std::runtime_error("GUI save confirm missing");
    auto* edit=SpellControl(confirm,3);edit->SetText(u"Redux Spell Journey");
    if(!edit->PerformAction(ControlActionResponder::ActionKey(Control::ValueChange))) throw std::runtime_error("Save name callback unavailable");
    SpellShot(out,"spell-save-confirm");press("GUISAVE",1,7);
    Write(out+"/spell-after-save.state.json",Snapshot(core->GetGame()));SpellShot(out,"spell-after-save");
    std::vector<std::string> dirs;
    for(const auto& s:core->GetSaveGameIterator()->GetSaveGames()) if(s->GetName()==u"Redux Spell Journey") dirs.push_back(Q(s->GetPath()));
    Write(out+"/spell-result.json",O({{"schema",Q("bg-redux-spell-native/1")},{"reload",SpellReload?"true":"false"},
        {"press_count",NumberJSON(SpellPresses)},{"command_sample",NumberJSON(SpellCommand)},{"open_sample",NumberJSON(SpellOpenSample)},{"release_sample",NumberJSON(SpellRelease)},
        {"action_id",NumberJSON(SpellActionID)},{"portrait_callback",Q("GUICommonWindows.PortraitButtonOnPress")},
        {"cast_callback",Q(SpellReload?"none":"ActionsWindow.ActionCastPressed")},{"spell_callback",Q(SpellReload?"none":"ActionsWindow.SpellPressed")},
        {"gui_save_callback",Q("GUISAVE.ConfirmedSaveGame")},{"save_return_code_observed","false"},{"forced","false"},{"os_pointer_input","false"},{"directories",A(dirs)}}));
    if(dirs.size()!=1 || SpellReady()!=0 || !SpellEffects()) throw std::runtime_error("GUI save absent/ambiguous or spell lost");
}
