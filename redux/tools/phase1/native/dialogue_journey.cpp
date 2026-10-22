// Separate external normal-loop stock Jaheira dialogue/control journey.
#define main UnusedProtectedGUIProbeMain
#include "gui_probe.cpp"
#undef main
#include "DialogHandler.h"
#include "TileMap.h"
#include "Scriptable/Door.h"

struct DialogueBranch { int state, strref, transition, local, response; };
static const DialogueBranch Branches[] = {
    {0,899,4,4,904},{47,20128,94,0,-1},{5,909,9,0,-1},
    {51,20142,98,0,-1},{8,912,12,0,-1},{49,20132,96,0,-1},
    {50,20136,97,0,-1},{9,921,14,1,923},{58,20176,105,0,-1},
    {59,20177,106,0,-1},{14,945,45,0,-1}
};

static Actor* DialogueTarget()
{
    auto* game=core->GetGame();auto* map=game->GetCurrentArea();Actor* found=nullptr;
    if (!map || map->GetScriptName()!="AR0602" || game->GetPartySize(false)!=2)
        throw std::runtime_error("Required stock area/two-member party absent");
    for (int i=0;i<map->GetActorCount(true);++i) {
        auto* actor=map->GetActor(i,true);
        if (actor->GetScriptName()!="jaheira") continue;
        if (found) throw std::runtime_error("Ambiguous Jaheira target");
        found=actor;
    }
    if (!found || found->InParty || found->GetDialog()!="JAHEIRA")
        throw std::runtime_error("Stock Jaheira identity/dialogue differs");
    return found;
}

static std::string DialogueScene()
{
    auto* game=core->GetGame();auto* target=DialogueTarget();auto* leader=game->GetPC(0,false);
    auto* door=game->GetCurrentArea()->TMap->GetDoor(ieVariable("Cell01"));
    if (!door || !leader) throw std::runtime_error("Cell01/leader absent");
    bool hasKey=false;std::vector<std::string> actions;
    for (int i=0;i<game->GetPartySize(false);++i) {
        auto* pc=game->GetPC(i,false);hasKey|=pc->inventory.CountItems(ResRef("MISC4B"),false)!=0;
        auto action=pc->GetCurrentAction();auto next=pc->GetNextAction();
        actions.push_back(O({{"runtime_id",NumberJSON(pc->GetGlobalID())},
            {"action_id",action?NumberJSON(action->actionID):"null"},{"next_action_id",next?NumberJSON(next->actionID):"null"},
            {"moving",pc->InMove()?"true":"false"},{"position",PointJSON(pc->Pos)}}));
    }
    auto targetAction=target->GetCurrentAction();auto targetNext=target->GetNextAction();
    auto* handler=core->GetGameControl()->dialoghandler.get();
    auto* actualTarget=handler?handler->GetTarget():nullptr;auto* actualSpeaker=handler?handler->GetSpeaker():nullptr;
    return O({{"schema",Q("bg-redux-dialogue-scene/1")},{"target_name",Q(target->GetScriptName().c_str())},
        {"target_id",NumberJSON(target->GetGlobalID())},{"target_position",PointJSON(target->Pos)},
        {"dialog",Q(target->GetDialog().c_str())},{"talk_count",NumberJSON(target->TalkCount)},
        {"leader_id",NumberJSON(leader->GetGlobalID())},{"party_count",NumberJSON(game->GetPartySize(false))},
        {"door_name",Q("Cell01")},{"door_flags",NumberJSON(door->Flags)},
        {"door_open",door->IsOpen()?"true":"false"},{"has_key",hasKey?"true":"false"},
        {"in_dialog",core->GetGameControl()->InDialog()?"true":"false"},
        {"target_action_id",targetAction?NumberJSON(targetAction->actionID):"null"},
        {"target_next_action_id",targetNext?NumberJSON(targetNext->actionID):"null"},
        {"target_moving",target->InMove()?"true":"false"},
        {"dialogue_target_id",actualTarget?NumberJSON(actualTarget->GetGlobalID()):"null"},
        {"dialogue_speaker_id",actualSpeaker?NumberJSON(actualSpeaker->GetGlobalID()):"null"},
        {"party_actions",A(actions)},{"game_time",NumberJSON(game->GameTime.load())}});
}

static bool DialogueIdle()
{
    auto* game=core->GetGame();auto* target=DialogueTarget();
    if (core->GetGameControl()->InDialog() || target->GetCurrentAction() || target->GetNextAction() || target->InMove()) return false;
    for (int i=0;i<game->GetPartySize(false);++i) {auto* pc=game->GetPC(i,false);
        if (pc->GetCurrentAction() || pc->GetNextAction() || pc->InMove()) return false;}
    return true;
}

static Window* DialogueButtonWindow()
{
    Window* found=nullptr;
    for (auto* pack : {"GUIW10","GUIW08","GUIW","GUIW13","GUIW14","GUIW15","GUIW16","GUIW17","GUIW18","GUIW19","GUIW20"}) {
        for (auto* view:GetViews(ScriptingGroup_t(pack))) {
            auto* win=dynamic_cast<Window*>(view);
            if (win && win->IsVisible() && win->GetScriptingRef() && win->GetScriptingRef()->Id==9) {
                if (found && found!=win) throw std::runtime_error("Ambiguous stock Continue/End window");
                found=win;
            }
        }
    }
    return found;
}

static std::vector<std::string> DialogueMessageTypes;
static String DialogueMessageText(TextArea* area)
{
    // QueryText reports the selected option while options exist. Read the
    // publicly reachable text containers instead; never dispatch mouse input.
    const auto size=area->Dimensions();
    if(size.w<=0 || size.h<=0 || size.w>4096 || size.h>4096)throw std::runtime_error("Message geometry outside observation bound");
    std::set<View*> containers;std::set<std::string> observedTypes;
    for(int y=0;y<size.h;y+=8)for(int x=0;x<size.w;x+=8){
        auto* view=area->SubviewAt(Point(x,y),true,true);
        if(!view)continue;
        const std::string type=typeid(*view).name();
        observedTypes.insert(type);
        // These concrete classes/methods are not exported from the Debug DLL.
        // Match the pinned GCC RTTI spelling, then use only public inline
        // Contents()/Text() accessors. No private offset or copied implementation.
        if(type=="N5GemRB13TextContainerE" || type=="N5GemRB8TextArea12SpanSelector7OptSpanE")containers.insert(view);
    }
    DialogueMessageTypes.clear();for(const auto& type:observedTypes)DialogueMessageTypes.push_back(Q(type));
    String result;for(auto* view:containers){
        auto* text=static_cast<TextContainer*>(view);
        for(auto* content:text->Contents()){
            if(std::string(typeid(*content).name())!="N5GemRB8TextSpanE")continue;
            result+=static_cast<const TextSpan*>(content)->Text();
        }
        result+=u"\n";
    }
    return result;
}

static size_t DialogueOccurrences(const String& text,const String& value)
{
    if(value.empty())return 0;
    size_t count=0,at=0;
    while((at=text.find(value,at))!=String::npos){++count;at+=value.size();}
    return count;
}

int main(int argc,char** argv)
{
    std::map<std::string,std::string> args;
    for(int i=1;i+1<argc;i+=2) { if(args.count(argv[i]))return 64;args[argv[i]]=argv[i+1]; }
    if(argc!=11 || args.size()!=5)return 64;
    for(auto key:{"--config","--output","--scripts","--journey","--nonce"})if(!args.count(key))return 64;
    const bool reload=args["--journey"]=="reload";
    if ((!reload && args["--journey"]!="talk") || args["--nonce"].size()!=32 ||
        args["--nonce"].find_first_not_of("0123456789abcdef")!=std::string::npos)return 64;
    const auto out=args["--output"];std::setlocale(LC_ALL,".UTF8");std::atexit(StopLog);
    std::unique_ptr<Interface> engine;std::vector<std::string> events,samples,saves;
    bool completed=false;int ticks=0,phase=-2,idle=0,branch=0,requests=0;unsigned startTime=0;
    std::string error;String previousMessage;
    try {
        const char* engineArgs[]={"redux-dialogue-journey","-c",args["--config"].c_str()};
        auto config=LoadFromArgs(3,const_cast<char**>(engineArgs));
        ToggleLogging(true);AddLogWriter(createStdioLogWriter());SetMainLogLevel(FATAL);
        engine=std::make_unique<Interface>(std::move(config));auto* script=core->GetGUIScriptEngine();
        if (!script->ExecString("import sys;sys.path.insert(0,"+Q(args["--scripts"])+");import DialogueStart"))throw std::runtime_error("Startup import failed");
        core->SetNextScript("DialogueStart");
        const auto run=[&](const char* function){if(!script->ExecString(std::string("DialogueStart.")+function+"()"))throw std::runtime_error("Stock startup/save selector failed");};
        const auto capture=[&](const std::string& name,bool image){
            if(std::filesystem::exists(out+"/"+name+".scene.json"))throw std::runtime_error("Refuse checkpoint overwrite");
            Write(out+"/"+name+".scene.json",DialogueScene());Write(out+"/"+name+".state.json",Snapshot(core->GetGame()));
            if(image){PluginHolder<ImageWriter> writer=MakePluginHolder<ImageWriter>(PLUGIN_IMAGE_WRITER_BMP);FileStream file;
                if(!writer || !file.Create(out,name,IE_BMP_CLASS_ID))throw std::runtime_error("Capture creation failed");
                writer->PutImage(&file,core->GetWindowManager()->GetScreenshot(nullptr));}
        };
        const auto event=[&](const std::string& kind,const std::string& extra){events.push_back(O({{"sequence",NumberJSON(events.size()+1)},
            {"tick",NumberJSON(ticks)},{"nonce",Q(args["--nonce"])},{"kind",Q(kind)},{"details",extra}}));};
        const auto button=[&](const char* pack,int window,int control){Press(pack,window,control);event("registered-button",O({{"pack",Q(pack)},{"window",NumberJSON(window)},{"control",NumberJSON(control)},{"performed","true"}}));};
        core->SetTimer([&](){try {
            if(++ticks>1000)throw std::runtime_error("Dialogue callback-count bound exceeded");
            if(phase==-2){run("PopulateLoad");button("GUILOAD",0,26);phase=-1;return;}
            if(!core->GetGame() || !core->GetGameControl() || !GetViews(ScriptingGroup_t("LOADWIN")).empty())return;
            auto* game=core->GetGame();auto* gc=core->GetGameControl();
            if(phase==-1){run("SelectLeader");capture("loaded",true);startTime=game->GameTime.load();core->SetPause(PauseState::Off,3);phase=0;return;}
            if(phase==0){
                const bool ready=DialogueIdle();idle=ready?idle+1:0;
                const auto name="startup-"+NumberJSON(samples.size());capture(name,false);
                samples.push_back(O({{"checkpoint",Q(name)},{"idle",ready?"true":"false"},{"consecutive_idle",NumberJSON(idle)},
                    {"tick",NumberJSON(ticks)},{"game_time",NumberJSON(game->GameTime.load())}}));
                if(idle<4 || game->GameTime.load()<startTime+2*core->Time.defaultTicksPerSec)return;
                capture("ready",true);
                if(reload){core->SetPause(PauseState::On,3);capture("final",true);completed=true;core->QuitFlag=QF_KILL;return;}
                auto* door=game->GetCurrentArea()->TMap->GetDoor(ieVariable("Cell01"));
                bool hasKey=false;for(int i=0;i<2;++i)hasKey|=game->GetPC(i,false)->inventory.CountItems(ResRef("MISC4B"),false)!=0;
                if(DialogueTarget()->TalkCount!=0 || DialogueTarget()->Pos!=Point(3898,2676) || !door || door->IsOpen() ||
                    door->Flags!=1634 || hasKey || game->GetJournalCount()!=2 || core->GetFirstSelectedPC(false)!=game->GetPC(0,false))
                    throw std::runtime_error("Initial stock dialogue preconditions changed before request");
                auto* messages=core->GetMessageTextArea();if(!messages)throw std::runtime_error("Message TextArea absent before request");
                previousMessage=DialogueMessageText(messages);
                Write(out+"/talk-request.message.json",O({{"observed_text",Q(MBStringFromString(previousMessage))},
                    {"observed_runtime_types",A(DialogueMessageTypes)}}));
                gc->TryToTalk(game->GetPC(0,false),DialogueTarget());++requests;
                event("ordinary-talk-request",O({{"route",Q("GameControl::TryToTalk/NIDSpecial1")},{"target_id",NumberJSON(DialogueTarget()->GetGlobalID())}}));phase=1;return;
            }
            if(phase==1){
                if(branch==11){if(gc->InDialog())return;core->SetPause(PauseState::On,3);capture("after-dialogue",true);run("OpenOptions");phase=2;return;}
                if(!gc->InDialog())return;
                if(!gc->dialoghandler->IsTarget(DialogueTarget()) || !gc->dialoghandler->IsSpeaker(game->GetPC(0,false)))throw std::runtime_error("Actual dialogue participants differ");
                auto* ta=core->GetMessageTextArea();if(!ta)throw std::runtime_error("Message TextArea absent");
                const auto& expected=Branches[branch];const auto text=DialogueMessageText(ta);const auto npc=core->GetString(ieStrRef(expected.strref));
                const auto beforeOccurrences=DialogueOccurrences(previousMessage,npc),afterOccurrences=DialogueOccurrences(text,npc);
                if(npc.empty() || afterOccurrences<=beforeOccurrences){
                    Write(out+"/message-wait-"+NumberJSON(ticks)+".json",O({{"expected_npc_strref",NumberJSON(expected.strref)},
                        {"observed_runtime_types",A(DialogueMessageTypes)},{"observed_text",Q(MBStringFromString(text))}}));return;
                }
                if(expected.response<0){auto* window=DialogueButtonWindow();auto* control=window?GetControl(0,window):nullptr;
                    if(!control || control->IsDisabled() || !control->IsVisible())return;}
                const auto prefix="branch-"+NumberJSON(branch);capture(prefix,true);
                Write(out+"/"+prefix+".text.json",O({{"message_text",Q(MBStringFromString(text))},
                    {"previous_text",Q(MBStringFromString(previousMessage))},{"npc_occurrences_before",NumberJSON(beforeOccurrences)},
                    {"npc_occurrences_after",NumberJSON(afterOccurrences)},
                    {"expected_npc_strref",NumberJSON(expected.strref)},{"expected_npc_text",Q(MBStringFromString(npc))},
                    {"observed_runtime_types",A(DialogueMessageTypes)},
                    {"identity_method",Q("Sequential expected NPC strref text present in actual transcript; private internal state index not sampled")}}));
                if(expected.response>=0){
                    const auto response=core->GetString(ieStrRef(expected.response));
                    if(response.empty() || text.find(response)==String::npos)throw std::runtime_error("Expected response is not displayed");
                    if(!ta->SupportsAction(ControlActionResponder::ActionKey(TextArea::Action::Select)))throw std::runtime_error("Registered dialogue response callback missing");
                    ta->UpdateState(expected.local);
                }else{
                    auto* window=DialogueButtonWindow();auto* control=window?GetControl(0,window):nullptr;
                    const auto label=core->GetString(ieStrRef(branch==10?9371:9372));
                    if(!control || control->IsDisabled() || !control->IsVisible())return;
                    if(control->QueryText()!=label || !control->PerformAction())throw std::runtime_error("Stock Continue/End callback absent/wrong label");
                }
                event(expected.response>=0?"registered-response":"registered-continue-end",O({{"state",NumberJSON(expected.state)},
                    {"npc_strref",NumberJSON(expected.strref)},{"transition",NumberJSON(expected.transition)},{"local_transition",NumberJSON(expected.local)},
                    {"response_strref",expected.response>=0?NumberJSON(expected.response):"null"},{"performed","true"}}));previousMessage=text;++branch;return;
            }
            core->SetPause(PauseState::On,3);
            if(phase==2){button("GUIOPT",2,6);phase=3;return;}
            if(phase==3){run("ChooseNewSave");button("GUISAVE",0,26);phase=4;return;}
            if(phase==4){auto* input=RequiredControl("GUISAVE",1,3);input->SetText(u"Redux Jaheira Dialogue");
                if(!input->PerformAction(ControlActionResponder::ActionKey(Control::ValueChange)))throw std::runtime_error("Save name ValueChange callback missing");
                event("registered-save-name",O({{"performed","true"},{"control","3"}}));phase=5;return;}
            if(phase==5){capture("before-save",true);button("GUISAVE",1,7);phase=6;return;}
            if(phase==6){for(const auto& save:core->GetSaveGameIterator()->GetSaveGames())if(save->GetName()==u"Redux Jaheira Dialogue")saves.push_back(Q(save->GetPath()));
                if(saves.size()!=1)throw std::runtime_error("Created GUI save absent/ambiguous");
                capture("final",true);completed=true;core->QuitFlag=QF_KILL;return;}
        }catch(const std::exception& failure){error=failure.what();core->QuitFlag=QF_KILL;}},250,-1);
        engine->Main();
    }catch(const std::exception& failure){error=failure.what();}
    Write(out+"/dialogue-result.json",O({{"schema",Q("bg-redux-jaheira-native/1")},{"nonce",Q(args["--nonce"])},
        {"journey",Q(args["--journey"])},{"completed",completed?"true":"false"},{"error",Q(error)},
        {"talk_requests",NumberJSON(requests)},{"branches_completed",NumberJSON(branch)},{"events",A(events)},
        {"ticks_per_second",engine?NumberJSON(core->Time.defaultTicksPerSec):"0"},
        {"startup_samples",A(samples)},{"saves",A(saves)},{"os_pointer_input","false"},{"forced_dialogue_state","false"}}));
    if(engine){engine.reset();core=nullptr;VideoDriver.reset();PluginMgr::Get()->RunCleanup();}StopLog();
    return completed && error.empty()?0:1;
}
