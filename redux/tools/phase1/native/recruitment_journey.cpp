// External composed AR0602 checkpoint. Protected helper mains are never invoked.
#include "recruitment_dialogue_helpers.cpp"
#include "Scriptable/Container.h"
static Actor* RecruitTarget() {
    auto* g=core->GetGame();auto* map=g->GetCurrentArea();Actor* result=nullptr;
    if(!map || map->GetScriptName()!="AR0602" || (g->GetPartySize(false)!=2 && g->GetPartySize(false)!=3))throw std::runtime_error("Recruitment area/party guard");
    for(int i=0;i<map->GetActorCount(true);++i){auto* a=map->GetActor(i,true);if(a->GetScriptName()!="jaheira")continue;
        if(result)throw std::runtime_error("Duplicate Jaheira");result=a;}
    if(!result || (result->GetDialog()!="JAHEIRA" && result->GetDialog()!="JAHEIRAJ"))throw std::runtime_error("Jaheira identity/dialog differs");
    return result;
}
static Door* RecruitDoor() {
    auto* d=core->GetGame()->GetCurrentArea()->TMap->GetDoor(ieVariable("Cell01"));
    if(!d || d->OriginalName!="Cell01" || d->KeyResRef!="MISC4B" || d->LockDifficulty!=100 || d->Trapped)throw std::runtime_error("Cell01 input identity/key/trap guard");return d;
}
static Container* RecruitTable() {
    Container* result=nullptr;
    for(const auto& c:core->GetGame()->GetCurrentArea()->TMap->GetContainers())if(c->OriginalName=="Jailkeep Table"){
        if(result)throw std::runtime_error("Duplicate table");result=c.get();}
    if(!result || result->GetScriptName()!="jailkeeptable" || result->Pos!=Point(3109,2829) || result->containerType!=5 || result->Flags || result->Trapped)throw std::runtime_error("Stock table guard");return result;
}
static unsigned RecruitGlobal(const char* name) {
    for(const auto& pair:core->GetGame()->locals)if(pair.first==StringView(name))return pair.second;return 0;
}
static int RecruitKeys() {int n=0;auto* g=core->GetGame();for(int i=0;i<g->GetPartySize(false);++i)n+=g->GetPC(i,false)->inventory.CountItems(ResRef("MISC4B"),false);return n;}
static bool RecruitIdle() {
    auto* g=core->GetGame();auto* t=RecruitTarget();if(core->GetGameControl()->InDialog() || t->GetCurrentAction() || t->GetNextAction() || t->InMove())return false;
    for(int i=0;i<g->GetPartySize(false);++i){auto* a=g->GetPC(i,false);if(a->GetCurrentAction() || a->GetNextAction() || a->InMove())return false;}return true;
}
static std::string RecruitAction(const Holder<Action>& a) {
    if(!a)return "null";return O({{"id",NumberJSON(a->actionID)},{"int0",NumberJSON(a->int0Parameter)},{"resref",Q(a->resref0Parameter.c_str())}});
}
static std::string RecruitScene() {
    auto* g=core->GetGame();auto* t=RecruitTarget();auto* d=RecruitDoor();auto* table=RecruitTable();auto* leader=g->GetPC(0,false);auto* h=core->GetGameControl()->dialoghandler.get();std::vector<std::string> party;
    for(int i=0;i<g->GetPartySize(false);++i){auto* a=g->GetPC(i,false);party.push_back(O({{"id",NumberJSON(a->GetGlobalID())},{"position",PointJSON(a->Pos)},
        {"current",RecruitAction(a->GetCurrentAction())},{"next",RecruitAction(a->GetNextAction())},{"moving",a->InMove()?"true":"false"}}));}
    auto* c=core->GetCurrentContainer();auto* selected=core->GetFirstSelectedPC(false);
    return O({{"schema",Q("bg-redux-recruitment-scene/1")},{"game_time",NumberJSON(g->GameTime.load())},{"leader_id",NumberJSON(leader->GetGlobalID())},
        {"target_id",NumberJSON(t->GetGlobalID())},{"target_name",Q(t->GetScriptName().c_str())},{"target_in_party",NumberJSON(t->InParty)},{"target_dialog",Q(t->GetDialog().c_str())},
        {"talk_count",NumberJSON(t->TalkCount)},{"target_current",RecruitAction(t->GetCurrentAction())},{"target_next",RecruitAction(t->GetNextAction())},{"target_moving",t->InMove()?"true":"false"},
        {"party_count",NumberJSON(g->GetPartySize(false))},{"party_keys",NumberJSON(RecruitKeys())},{"table_keys",NumberJSON(table->inventory.CountItems(ResRef("MISC4B"),false))},
        {"table_id",NumberJSON(table->GetGlobalID())},{"table_inventory",InventoryJSON(table->inventory)},
        {"door_id",NumberJSON(d->GetGlobalID())},{"door_name",Q(d->OriginalName.c_str())},{"door_key",Q(d->KeyResRef.c_str())},{"door_flags",NumberJSON(d->Flags)},
        {"door_open",d->IsOpen()?"true":"false"},{"door_locked",d->IsLocked()?"true":"false"},
        {"released",NumberJSON(RecruitGlobal("JaheiraReleased"))},{"jerk",NumberJSON(RecruitGlobal("JaheiraJerk"))},{"hunt",NumberJSON(RecruitGlobal("JaheiraHunt"))},
        {"bd_defai",NumberJSON(RecruitGlobal("BD_DEFAI"))},{"leader_class_script",Q(leader->GetScript(SCR_CLASS,true).c_str())},
        {"selected_id",selected?NumberJSON(selected->GetGlobalID()):"null"},{"selected_count",NumberJSON(g->selected.size())},
        {"current_container",c?NumberJSON(c->GetGlobalID()):"null"},{"dialogue_flags",NumberJSON(core->GetGameControl()->GetDialogueFlags())},
        {"in_dialog",core->GetGameControl()->InDialog()?"true":"false"},{"speaker",h&&h->GetSpeaker()?NumberJSON(h->GetSpeaker()->GetGlobalID()):"null"},
        {"dialogue_target",h&&h->GetTarget()?NumberJSON(h->GetTarget()->GetGlobalID()):"null"},{"party_actions",A(party)}});
}
static Window* RecruitVisible(int id) {
    Window* result=nullptr;
    for(const char* pack:{"GUIW10","GUIW08","GUIW"})for(auto* v:GetViews(ScriptingGroup_t(pack))){auto* w=dynamic_cast<Window*>(v);
        if(w && w->GetScriptingRef() && w->GetScriptingRef()->Id==static_cast<ScriptingId>(id) && w->IsVisible()){
            if(result && result!=w)throw std::runtime_error("Ambiguous stock window");result=w;}}
    return result;
}
static void RecruitPress(Control* c) {
    if(!c || c->IsDisabled() || !c->IsVisible())throw std::runtime_error("Disabled/missing stock control");
    if(c->IsDictBound()){const auto variable=c->DictVariable();c->BindDictVariable(variable,c->GetValue(),c->GetValueRange());}
    if(!c->PerformAction())throw std::runtime_error("Registered stock callback missing");
}
static void RecruitResources(const std::string& out) {
    Fields rows;
    for(const auto& spec:std::vector<std::pair<std::string,SClass_ID>>{{"jaheira",IE_DLG_CLASS_ID},{"misc4b",IE_ITM_CLASS_ID},{"action",IE_IDS_CLASS_ID},{"pdialog",IE_2DA_CLASS_ID},{"jaheira-script",IE_BCS_CLASS_ID},{"trigger",IE_IDS_CLASS_ID},{"object",IE_IDS_CLASS_ID}}){
        std::unique_ptr<DataStream> stream(gamedata->GetResourceStream(StringView(spec.first=="jaheira-script"?"jaheira":spec.first),spec.second));
        if(!stream || stream->Size()<8 || stream->Size()>8*1024*1024)throw std::runtime_error("Runtime recruitment resource bounds");
        std::string raw(stream->Size(),'\0');if(stream->Read(&raw[0],raw.size())!=static_cast<strret_t>(raw.size()))throw std::runtime_error("Runtime resource short read");
        std::ofstream file(out+"/"+spec.first+".runtime",std::ios::binary);if(!file || !file.write(raw.data(),raw.size()))throw std::runtime_error("Runtime resource freeze failed");
        rows.emplace_back(spec.first,O({{"originalfile",Q(stream->originalfile.c_str())},{"bytes",NumberJSON(raw.size())}}));
    }
    Write(out+"/recruitment-providers.json",O({{"schema",Q("bg-redux-recruitment-providers/1")},{"resources",O(rows)}}));
}
int main(int argc,char** argv) {
    std::map<std::string,std::string> args;for(int i=1;i+1<argc;i+=2){if(args.count(argv[i]))return 64;args[argv[i]]=argv[i+1];}
    if(argc!=11 || args.size()!=5)return 64;for(const char* k:{"--config","--output","--scripts","--journey","--nonce"})if(!args.count(k))return 64;
    const bool reload=args["--journey"]=="reload";if((!reload && args["--journey"]!="recruit") || args["--nonce"].size()!=32 || args["--nonce"].find_first_not_of("0123456789abcdef")!=std::string::npos)return 64;
    const auto out=args["--output"];std::setlocale(LC_ALL,".UTF8");std::atexit(StopLog);std::unique_ptr<Interface> engine;
    std::vector<std::string> events,samples,saves;std::string error;bool completed=false,sawOpen=false;int autos=0;int phase=-2,ticks=0,phaseTick=0,idle=0,branch=0,opens=0,takes=0,closes=0,doors=0,talks=0;unsigned started=0;String previous;
    try {
        const char* ea[]={"redux-recruitment","-c",args["--config"].c_str()};auto config=LoadFromArgs(3,const_cast<char**>(ea));ToggleLogging(true);AddLogWriter(createStdioLogWriter());SetMainLogLevel(FATAL);
        engine=std::make_unique<Interface>(std::move(config));auto script=core->GetGUIScriptEngine();
        if(!script->ExecString("import sys;sys.path.insert(0,"+Q(args["--scripts"])+");import RecruitStart"))throw std::runtime_error("Private startup failed");core->SetNextScript("RecruitStart");
        const auto run=[&](const char* fn){if(!script->ExecString(std::string("RecruitStart.")+fn+"()"))throw std::runtime_error("Stock selector failed");};
        const auto capture=[&](const std::string& name,bool image){if(std::filesystem::exists(out+"/"+name+".scene.json"))throw std::runtime_error("Refuse evidence overwrite");
            Write(out+"/"+name+".scene.json",RecruitScene());Write(out+"/"+name+".state.json",Snapshot(core->GetGame()));
            if(image){PluginHolder<ImageWriter> w=MakePluginHolder<ImageWriter>(PLUGIN_IMAGE_WRITER_BMP);FileStream f;if(!w || !f.Create(out,name,IE_BMP_CLASS_ID))throw std::runtime_error("Image creation failed");w->PutImage(&f,core->GetWindowManager()->GetScreenshot(nullptr));}};
        const auto event=[&](const char* kind,const std::string& details){events.push_back(O({{"sequence",NumberJSON(events.size()+1)},{"tick",NumberJSON(ticks)},{"nonce",Q(args["--nonce"])},{"kind",Q(kind)},{"details",details}}));Write(out+"/recruitment-events.json",A(events));};
        const auto button=[&](const char* pack,int win,int id){Press(pack,win,id);event("registered-button",O({{"pack",Q(pack)},{"window",NumberJSON(win)},{"control",NumberJSON(id)}}));};
        const auto advance=[&](int next){phase=next;phaseTick=ticks;idle=0;};
        core->SetTimer([&](){try {
            if(++ticks>(reload?360:720) || ticks-phaseTick>200)throw std::runtime_error("Bounded recruitment timer/phase exhausted");
            if(phase==-2){run("PopulateLoad");button("GUILOAD",0,26);advance(-1);return;}
            if(!core->GetGame() || !core->GetGameControl() || !GetViews(ScriptingGroup_t("LOADWIN")).empty())return;
            auto* g=core->GetGame();auto* gc=core->GetGameControl();auto* leader=g->GetPC(0,false);auto* target=RecruitTarget();auto* door=RecruitDoor();auto* table=RecruitTable();
            if(phase==-1){RecruitResources(out);run("SelectLeader");capture("loaded",true);started=g->GameTime.load();core->SetPause(PauseState::Off,3);advance(0);return;}
            const auto tickName="sample-"+NumberJSON(ticks);capture(tickName,false);
            const bool natural=RecruitIdle() && core->GetFirstSelectedPC(false)==leader && g->selected.size()==1 && !core->GetCurrentContainer();
            samples.push_back(O({{"checkpoint",Q(tickName)},{"tick",NumberJSON(ticks)},{"phase",NumberJSON(phase)},{"idle",natural?"true":"false"},{"game_time",NumberJSON(g->GameTime.load())}}));Write(out+"/recruitment-samples.json",A(samples));
            if(phase==0){idle=natural?idle+1:0;if(idle<4 || g->GameTime.load()<started+2*core->Time.defaultTicksPerSec || RecruitGlobal("BD_DEFAI")!=1 || leader->GetScript(SCR_CLASS,true)!="BDDEFAI")return;
                capture("ready",true);if(reload){core->SetPause(PauseState::On,3);capture("final",true);completed=true;core->QuitFlag=QF_KILL;return;}
                if(g->GetPartySize(false)!=2 || target->TalkCount!=1 || target->InParty || door->Flags!=1634 || RecruitKeys()!=0 || table->inventory.CountItems(ResRef("MISC4B"),false)!=1 || RecruitGlobal("JaheiraReleased") || RecruitGlobal("JaheiraJerk") || RecruitGlobal("JaheiraHunt"))throw std::runtime_error("Measured parent checkpoint no longer applicable");
                capture("before-container-command",true);auto action=GenerateAction("UseContainer()");if(!action)throw std::runtime_error("UseContainer parse failed");
                ++opens;event("ordinary-container-command",O({{"action_id",NumberJSON(action->actionID)},{"target_id",NumberJSON(table->GetGlobalID())}}));core->SetCurrentContainer(leader,table);leader->CommandActor(std::move(action));capture("after-container-command",false);advance(1);return;}
            if(phase==1){auto* w=RecruitVisible(8);if(!w)return;if(core->GetCurrentContainer()!=table || core->GetFirstSelectedPC(false)!=leader)throw std::runtime_error("Actual table/selected actor differs");
                auto* scroll=GetControl(52,w);if(!scroll || !scroll->IsDictBound() || scroll->DictVariable()!=StringView("LeftTopIndex"))throw std::runtime_error("Actual table scrollbar missing");
                capture("before-scroll",true);scroll->SetValue(1);if(scroll->GetValue()!=1 || core->GetDictionary().Get("LeftTopIndex",0)!=1)throw std::runtime_error("Ordinary scrollbar value not observed");
                event("registered-scroll",O({{"control","52"},{"value","1"},{"dict_name",Q(scroll->DictVariable().c_str())}}));advance(2);return;}
            if(phase==2){auto* w=RecruitVisible(8);auto* c=w?GetControl(4,w):nullptr;const auto* item=table->inventory.GetSlotItem(7);
                if(!c || !c->IsDictBound() || c->DictVariable()!=StringView("LeftIndex") || c->GetValue()!=7 || !item || item->ItemResRef!="MISC4B")throw std::runtime_error("Actual visible key icon/slot binding differs");
                const ResRef takenRef=item->ItemResRef;capture("before-key-take",true);++takes;RecruitPress(c);event("registered-key-take",O({{"control","4"},{"dict_value","7"},{"dict_name",Q("LeftIndex")},{"resref",Q(takenRef.c_str())}}));
                // Do not use the borrowed item pointer after the transfer.
                capture("after-key-take",true);if(RecruitKeys()!=1 || table->inventory.CountItems(ResRef("MISC4B"),false)!=0)throw std::runtime_error("Key transfer outcome missing");
                ++closes;RecruitPress(GetControl(51,w));event("registered-container-close",O({{"control","51"}}));advance(3);return;}
            if(phase==3){idle=natural?idle+1:0;if(idle<4 || RecruitVisible(8))return;if(RecruitKeys()!=1 || door->Flags!=1634)throw std::runtime_error("Key/door changed before command");
                capture("before-door-command",true);auto* message=core->GetMessageTextArea();if(!message)throw std::runtime_error("Auto-dialogue baseline message absent");previous=DialogueMessageText(message);Write(out+"/auto-baseline.message.json",O({{"observed_text",Q(MBStringFromString(previous))}}));auto action=GenerateAction("NIDSpecial9()");if(!action)throw std::runtime_error("Normal toggle action parse failed");action->int0Parameter=door->GetGlobalID();
                // HandleDoor is private. Mirror its default non-cast/non-attack/non-pick dispatch, not mouse hit testing.
                core->SetEventFlag(EF_RESETTARGET);door->AddTrigger(TriggerEntry(trigger_clicked,leader->GetGlobalID()));++doors;
                event("ordinary-door-command",O({{"action_id",NumberJSON(action->actionID)},{"int0",NumberJSON(action->int0Parameter)},{"clicked_actor",NumberJSON(leader->GetGlobalID())},{"route",Q("Mirrored HandleDoor/NIDSpecial9")}}));leader->CommandActor(std::move(action));capture("after-door-command",false);advance(4);return;}
            if(phase==4){if(!door->IsOpen() || door->IsLocked() || door->Flags!=1633 || RecruitKeys()!=0)return;
                if(!sawOpen){capture("door-open",true);sawOpen=true;}
                // JAHEIRA.BCS naturally sets Released=1 and starts dialogue when
                // Cell01 opens and Player1 is visible. Never race it with a host request.
                if(!gc->InDialog())return;
                if(!gc->dialoghandler->IsTarget(target) || !gc->dialoghandler->IsSpeaker(leader) || target->TalkCount!=2 || target->InParty || RecruitGlobal("JaheiraReleased")!=1)throw std::runtime_error("Actual stock auto-dialogue boundary differs");
                ++autos;capture("auto-dialogue",true);event("stock-auto-dialogue-observed",O({{"target_id",NumberJSON(target->GetGlobalID())},{"speaker_id",NumberJSON(leader->GetGlobalID())},{"route",Q("Source-supported JAHEIRA.BCS/OpenState/StartDialogueNoSet; exact action may be between samples")}}));advance(5);return;}
            if(phase==5){if(branch==2){if(gc->InDialog())return;capture("dialogue-ended",true);advance(6);return;}if(!gc->InDialog())return;
                if(!gc->dialoghandler->IsTarget(target) || !gc->dialoghandler->IsSpeaker(leader))throw std::runtime_error("Dialogue participants differ");
                auto* ta=core->GetMessageTextArea();if(!ta)throw std::runtime_error("Message widget absent");const int ref=branch==0?1021:1026;const auto text=DialogueMessageText(ta),npc=core->GetString(ieStrRef(ref));
                if(npc.empty() || DialogueOccurrences(text,npc)<=DialogueOccurrences(previous,npc))return;
                if(branch==1){auto* w=DialogueButtonWindow();auto* c=w?GetControl(0,w):nullptr;if(!c || c->IsDisabled() || !c->IsVisible())return;}
                const auto name="branch-"+NumberJSON(branch);capture(name,true);Write(out+"/"+name+".text.json",O({{"expected_npc_strref",NumberJSON(ref)},{"expected_npc_text",Q(MBStringFromString(npc))},{"previous_text",Q(MBStringFromString(previous))},{"message_text",Q(MBStringFromString(text))},{"observed_runtime_types",A(DialogueMessageTypes)}}));
                if(branch==0){const auto response=core->GetString(ieStrRef(1022));if(text.find(u"1. - "+response)==String::npos || !ta->SupportsAction(ControlActionResponder::ActionKey(TextArea::Action::Select)))throw std::runtime_error("Actual numbered recruitment option missing");ta->SelectAvailableOption(0);event("registered-recruit-response",O({{"state","33"},{"npc_strref","1021"},{"transition","75"},{"response","1022"},{"visible_index","0"},{"entry",Q("TextArea::SelectAvailableOption")}}));}
                else{auto* w=DialogueButtonWindow();auto* c=w?GetControl(0,w):nullptr;if(!c || c->IsDisabled() || !c->IsVisible())return;const auto raw=core->GetString(ieStrRef(9371));auto label=raw;if(c->Flags()&IE_GUI_BUTTON_LOWERCASE)StringToLower(label);else if(c->Flags()&IE_GUI_BUTTON_CAPS)StringToUpper(label);
                    Write(out+"/branch-1.button.json",O({{"raw_label",Q(MBStringFromString(raw))},{"flags",NumberJSON(c->Flags())},{"expected_label",Q(MBStringFromString(label))},{"actual_label",Q(MBStringFromString(c->QueryText()))}}));if(c->QueryText()!=label || !c->PerformAction())throw std::runtime_error("Actual End label/callback differs");event("registered-recruit-end",O({{"state","34"},{"npc_strref","1026"},{"transition","79"},{"label_strref","9371"}}));}
                previous=text;++branch;return;}
            if(phase==6){if(g->GetPartySize(false)!=3 || !target->InParty || target->GetDialog()!="JAHEIRAJ" || target->TalkCount!=2 || RecruitGlobal("JaheiraReleased")!=1 || RecruitGlobal("JaheiraHunt") || RecruitGlobal("JaheiraJerk"))return;
                idle=natural?idle+1:0;if(idle<4)return;capture("recruited",true);core->SetPause(PauseState::On,3);run("OpenOptions");advance(7);return;}
            core->SetPause(PauseState::On,3);
            if(phase==7){button("GUIOPT",2,6);advance(8);return;}
            if(phase==8){run("ChooseNewSave");button("GUISAVE",0,26);advance(9);return;}
            if(phase==9){auto* c=RequiredControl("GUISAVE",1,3);c->SetText(u"Redux Cell Recruitment");if(!c->PerformAction(ControlActionResponder::ActionKey(Control::ValueChange)))throw std::runtime_error("Save name callback absent");event("registered-save-name",O({{"control","3"}}));advance(10);return;}
            if(phase==10){capture("before-save",true);button("GUISAVE",1,7);advance(11);return;}
            if(phase==11){for(const auto& s:core->GetSaveGameIterator()->GetSaveGames())if(s->GetName()==u"Redux Cell Recruitment")saves.push_back(Q(s->GetPath()));if(saves.size()!=1)throw std::runtime_error("Actual GUI save absent/duplicate");capture("final",true);completed=true;core->QuitFlag=QF_KILL;return;}
        }catch(const std::exception& e){error=e.what();core->QuitFlag=QF_KILL;}},250,-1);engine->Main();
    }catch(const std::exception& e){error=e.what();}
    Write(out+"/recruitment-result.json",O({{"schema",Q("bg-redux-recruitment-native/1")},{"nonce",Q(args["--nonce"])},{"journey",Q(args["--journey"])},{"completed",completed?"true":"false"},{"error",Q(error)},
        {"container_commands",NumberJSON(opens)},{"takes",NumberJSON(takes)},{"closes",NumberJSON(closes)},{"door_commands",NumberJSON(doors)},{"talk_requests",NumberJSON(talks)},{"auto_dialogues",NumberJSON(autos)},{"branches",NumberJSON(branch)},
        {"events",A(events)},{"samples",A(samples)},{"saves",A(saves)},{"os_pointer_input","false"},{"forced_outcomes","false"}}));
    if(engine){engine.reset();core=nullptr;VideoDriver.reset();PluginMgr::Get()->RunCleanup();}StopLog();return completed && error.empty()?0:1;
}
