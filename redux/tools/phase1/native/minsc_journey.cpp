// External stock Minsc journey. Included frozen helper mains are never called.
#include "minsc_dialogue_helpers.cpp"
#include "Scriptable/Container.h"
struct MBranch { const char* dlg;int state,ref,local,transition,response;std::vector<int> prefix; };
static const MBranch MPath[]={
 {"MINSCA",0,2306,0,0,2356,{2356}},{"MINSCA",1,2364,2,6,2395,{2393,2394,2395}},
 {"MINSCA",8,2524,0,22,-1,{}},{"MINSCA",20,19993,1,40,-1,{}},{"IMOENJ",7,38539,0,9,-1,{}},
 {"MINSCA",43,38542,0,75,-1,{}},{"MINSCA",32,25066,0,54,25067,{25067}},
 {"MINSCA",34,25071,1,59,25091,{25090,25091}},{"MINSCA",38,25101,0,66,25102,{25102}},
 {"MINSCA",39,25105,0,69,-1,{}},{"MINSCA",26,20008,0,46,-1,{}},
 {"MINSCA",40,25106,0,70,-1,{}},{"MINSCA",41,25107,0,71,-1,{}},
 {"MINSCA",42,25108,1,73,25110,{25109,25110}},{"MINSCA",22,20001,0,42,-1,{}},
 {"MINSCA",23,20002,0,43,-1,{}},{"MINSCA",10,2530,0,25,2548,{2548}},
 {"MINSCA",29,20018,1,50,-1,{}},{"IMOENJ",8,38543,0,10,-1,{}},
 {"MINSCA",13,2547,1,31,2557,{2555,2557}},{"MINSCA",15,2564,0,34,-1,{}}
};
static Actor* MNPC(const char* name) {
 auto* g=core->GetGame();auto* map=g->GetCurrentArea();Actor* found=nullptr;
 if(!map||map->GetScriptName()!="AR0602"||(g->GetPartySize(false)!=3&&g->GetPartySize(false)!=4))throw std::runtime_error("Minsc area/party guard");
 for(int i=0;i<map->GetActorCount(true);++i){auto* a=map->GetActor(i,true);if(a->GetScriptName()!=StringView(name))continue;if(found)throw std::runtime_error("Duplicate named actor");found=a;}
 if(!found)throw std::runtime_error("Required actor absent");return found;
}
static Door* MDoor(const char* name) {auto* d=core->GetGame()->GetCurrentArea()->TMap->GetDoor(ieVariable(name));if(!d||d->OriginalName!=StringView(name))throw std::runtime_error("Door identity missing");return d;}
static unsigned MGlobal(const char* name){for(const auto& r:core->GetGame()->locals)if(r.first==StringView(name))return r.second;return 0;}
static std::string MAction(const Holder<Action>& a){if(!a)return "null";return O({{"id",NumberJSON(a->actionID)},{"point",PointJSON(a->pointParameter)},{"int0",NumberJSON(a->int0Parameter)},{"resref",Q(a->resref0Parameter.c_str())}});}
static bool MIdle(){auto* g=core->GetGame();auto* t=MNPC("Minsc");if(core->GetGameControl()->InDialog()||t->GetCurrentAction()||t->GetNextAction()||t->InMove())return false;for(int i=0;i<g->GetPartySize(false);++i){auto* a=g->GetPC(i,false);if(a->GetCurrentAction()||a->GetNextAction()||a->InMove())return false;}return true;}
static std::string MScene(){
 auto* g=core->GetGame();auto* t=MNPC("Minsc");auto* imoen=MNPC("Imoen");auto* d=MDoor("Cell02");auto* leader=g->GetPC(0,false);auto* gc=core->GetGameControl();auto* h=gc->dialoghandler.get();auto* selected=core->GetFirstSelectedPC(false);std::vector<std::string> actions;
 for(int i=0;i<g->GetPartySize(false);++i){auto* a=g->GetPC(i,false);actions.push_back(O({{"id",NumberJSON(a->GetGlobalID())},{"position",PointJSON(a->Pos)},{"current",MAction(a->GetCurrentAction())},{"next",MAction(a->GetNextAction())},{"moving",a->InMove()?"true":"false"}}));}
 return O({{"schema",Q("bg-redux-minsc-scene/1")},{"game_time",NumberJSON(g->GameTime.load())},{"leader_id",NumberJSON(leader->GetGlobalID())},{"target_id",NumberJSON(t->GetGlobalID())},{"imoen_id",NumberJSON(imoen->GetGlobalID())},
 {"target_name",Q(t->GetScriptName().c_str())},{"target_dialog",Q(t->GetDialog().c_str())},{"target_in_party",NumberJSON(t->InParty)},{"talk_count",NumberJSON(t->TalkCount)},{"target_current",MAction(t->GetCurrentAction())},{"target_next",MAction(t->GetNextAction())},{"target_moving",t->InMove()?"true":"false"},{"target_position",PointJSON(t->Pos)},
 {"party_count",NumberJSON(g->GetPartySize(false))},{"door_id",NumberJSON(d->GetGlobalID())},{"door_name",Q(d->OriginalName.c_str())},{"door_flags",NumberJSON(d->Flags)},{"door_key",Q(d->KeyResRef.c_str())},{"door_open",d->IsOpen()?"true":"false"},{"door_locked",d->IsLocked()?"true":"false"},{"cell01_flags",NumberJSON(MDoor("Cell01")->Flags)},
 {"released",NumberJSON(MGlobal("JaheiraReleased"))},{"bd_defai",NumberJSON(MGlobal("BD_DEFAI"))},{"leader_class_script",Q(leader->GetScript(SCR_CLASS,true).c_str())},{"selected_id",selected?NumberJSON(selected->GetGlobalID()):"null"},{"selected_count",NumberJSON(g->selected.size())},{"current_container",core->GetCurrentContainer()?NumberJSON(core->GetCurrentContainer()->GetGlobalID()):"null"},
 {"in_dialog",gc->InDialog()?"true":"false"},{"dialogue_flags",NumberJSON(gc->GetDialogueFlags())},{"speaker",h&&h->GetSpeaker()?NumberJSON(h->GetSpeaker()->GetGlobalID()):"null"},{"dialogue_target",h&&h->GetTarget()?NumberJSON(h->GetTarget()->GetGlobalID()):"null"},{"party_actions",A(actions)}});
}
static void MResources(const std::string& out){Fields rows;
 for(const auto& spec:std::vector<std::pair<std::string,SClass_ID>>{{"minsca",IE_DLG_CLASS_ID},{"imoenj",IE_DLG_CLASS_ID},{"minscj",IE_DLG_CLASS_ID},{"minsc-script",IE_BCS_CLASS_ID},{"minscx-script",IE_BCS_CLASS_ID},{"action",IE_IDS_CLASS_ID},{"trigger",IE_IDS_CLASS_ID},{"object",IE_IDS_CLASS_ID},{"pdialog",IE_2DA_CLASS_ID},{"gender",IE_2DA_CLASS_ID}}){
  const auto dash=spec.first.find('-');const auto ref=spec.first.substr(0,dash);std::unique_ptr<DataStream> stream(gamedata->GetResourceStream(StringView(ref),spec.second));
  if(!stream||stream->Size()<8||stream->Size()>8*1024*1024)throw std::runtime_error("Minsc runtime provider bounds");std::string raw(stream->Size(),'\0');if(stream->Read(&raw[0],raw.size())!=static_cast<strret_t>(raw.size()))throw std::runtime_error("Resource short read");
  std::ofstream f(out+"/"+spec.first+".runtime",std::ios::binary);if(!f||!f.write(raw.data(),raw.size()))throw std::runtime_error("Provider freeze failed");rows.emplace_back(spec.first,O({{"originalfile",Q(stream->originalfile.c_str())},{"bytes",NumberJSON(raw.size())}}));
 }Write(out+"/minsc-providers.json",O({{"schema",Q("bg-redux-minsc-providers/1")},{"resources",O(rows)}}));
}
int main(int argc,char**argv){
 std::map<std::string,std::string> args;for(int i=1;i+1<argc;i+=2){if(args.count(argv[i]))return 64;args[argv[i]]=argv[i+1];}if(argc!=11||args.size()!=5)return 64;for(const char* k:{"--config","--output","--scripts","--journey","--nonce"})if(!args.count(k))return 64;
 const bool reload=args["--journey"]=="reload";if((!reload&&args["--journey"]!="recruit")||args["--nonce"].size()!=32||args["--nonce"].find_first_not_of("0123456789abcdef")!=std::string::npos)return 64;
 const auto out=args["--output"];std::setlocale(LC_ALL,".UTF8");std::atexit(StopLog);std::unique_ptr<Interface> engine;std::string error;bool completed=false,sawOpen=false;int phase=-2,ticks=0,phaseTick=0,idle=0,index=0,visited=0,moves=0,autos=0;unsigned started=0;String previous;std::vector<std::string> events,samples,saves;
 try{const char* ea[]={"redux-minsc","-c",args["--config"].c_str()};auto cfg=LoadFromArgs(3,const_cast<char**>(ea));ToggleLogging(true);AddLogWriter(createStdioLogWriter());SetMainLogLevel(FATAL);engine=std::make_unique<Interface>(std::move(cfg));auto script=core->GetGUIScriptEngine();
  if(!script->ExecString("import sys;sys.path.insert(0,"+Q(args["--scripts"])+");import MinscStart"))throw std::runtime_error("Private startup failed");core->SetNextScript("MinscStart");
  const auto run=[&](const char* name){if(!script->ExecString(std::string("MinscStart.")+name+"()"))throw std::runtime_error("Stock selector failed");};
  const auto capture=[&](const std::string& name,bool image){if(std::filesystem::exists(out+"/"+name+".scene.json"))throw std::runtime_error("Evidence overwrite");Write(out+"/"+name+".scene.json",MScene());Write(out+"/"+name+".state.json",Snapshot(core->GetGame()));if(image){PluginHolder<ImageWriter>w=MakePluginHolder<ImageWriter>(PLUGIN_IMAGE_WRITER_BMP);FileStream f;if(!w||!f.Create(out,name,IE_BMP_CLASS_ID))throw std::runtime_error("Image creation failed");w->PutImage(&f,core->GetWindowManager()->GetScreenshot(nullptr));}};
  const auto event=[&](const char* kind,const std::string& details){events.push_back(O({{"sequence",NumberJSON(events.size()+1)},{"tick",NumberJSON(ticks)},{"nonce",Q(args["--nonce"])},{"kind",Q(kind)},{"details",details}}));Write(out+"/minsc-events.json",A(events));};
  const auto button=[&](const char*pack,int win,int id){Press(pack,win,id);event("registered-button",O({{"pack",Q(pack)},{"window",NumberJSON(win)},{"control",NumberJSON(id)}}));};
  const auto advance=[&](int next){phase=next;phaseTick=ticks;idle=0;};
  core->SetTimer([&](){try{
   if(++ticks>(reload?360:720)||ticks-phaseTick>240)throw std::runtime_error("Minsc bounded timer/phase exhausted");
   if(phase==-2){run("PopulateLoad");button("GUILOAD",0,26);advance(-1);return;}
   if(!core->GetGame()||!core->GetGameControl()||!GetViews(ScriptingGroup_t("LOADWIN")).empty())return;
   auto*g=core->GetGame();auto*gc=core->GetGameControl();auto*leader=g->GetPC(0,false);auto*t=MNPC("Minsc");auto*d=MDoor("Cell02");
   if(phase==-1){MResources(out);run("SelectLeader");capture("loaded",true);started=g->GameTime.load();core->SetPause(PauseState::Off,3);advance(0);return;}
   const auto name="sample-"+NumberJSON(ticks);capture(name,false);const bool natural=MIdle()&&core->GetFirstSelectedPC(false)==leader&&g->selected.size()==1&&!core->GetCurrentContainer();samples.push_back(O({{"checkpoint",Q(name)},{"tick",NumberJSON(ticks)},{"phase",NumberJSON(phase)},{"idle",natural?"true":"false"},{"game_time",NumberJSON(g->GameTime.load())}}));Write(out+"/minsc-samples.json",A(samples));
   if(phase==0){idle=natural?idle+1:0;if(idle<4||g->GameTime.load()<started+2*core->Time.defaultTicksPerSec||MGlobal("BD_DEFAI")!=1||leader->GetScript(SCR_CLASS,true)!="BDDEFAI")return;
    capture("ready",true);if(reload){core->SetPause(PauseState::On,3);capture("final",true);completed=true;core->QuitFlag=QF_KILL;return;}
    if(g->GetPartySize(false)!=3||t->InParty||t->TalkCount||t->GetDialog()!="MINSCA"||d->Flags!=610||!d->KeyResRef.IsEmpty()||d->LockDifficulty!=100||MGlobal("JaheiraReleased")!=1)throw std::runtime_error("Exact parent checkpoint differs");
    auto*ta=core->GetMessageTextArea();if(!ta)throw std::runtime_error("Initial message absent");previous=DialogueMessageText(ta);Write(out+"/baseline.message.json",O({{"observed_text",Q(MBStringFromString(previous))}}));capture("before-move",true);
    auto action=GenerateAction("MoveToPoint([3909.2753])");if(!action||action->pointParameter!=Point(3909,2753))throw std::runtime_error("Ordinary approach parse differs");++moves;event("ordinary-approach-command",O({{"action_id",NumberJSON(action->actionID)},{"point",PointJSON(action->pointParameter)},{"actor_id",NumberJSON(leader->GetGlobalID())},{"route",Q("Mirrored GameControl::CreateMovement/MoveToPoint; no pointer hit test")}}));leader->CommandActor(std::move(action));leader->Destination=Point(3909,2753);capture("after-move-command",false);advance(1);return;}
   if(phase==1){if(!gc->InDialog())return;if(!gc->dialoghandler->IsTarget(t)||!gc->dialoghandler->IsSpeaker(leader)||t->TalkCount!=1)throw std::runtime_error("Initial stock auto participants differ");++autos;capture("auto-dialogue",true);event("stock-auto-dialogue-observed",O({{"target_id",NumberJSON(t->GetGlobalID())},{"speaker_id",NumberJSON(leader->GetGlobalID())}}));advance(2);return;}
   if(phase==2){
    if(index==21){if(gc->InDialog())return;capture("dialogue-ended",true);advance(3);return;}
    if(index==11&&d->Flags==609&&!sawOpen){capture("door-open",true);sawOpen=true;}
    if(!gc->InDialog())return;const auto&b=MPath[index];auto*participant=MNPC(b.dlg==std::string("IMOENJ")?"Imoen":"Minsc");
    if(!gc->dialoghandler->IsTarget(participant)||!gc->dialoghandler->IsSpeaker(leader))return;
    auto*ta=core->GetMessageTextArea();if(!ta)throw std::runtime_error("Message absent");const auto text=DialogueMessageText(ta),npc=core->GetString(ieStrRef(b.ref));if(npc.empty()||DialogueOccurrences(text,npc)<=DialogueOccurrences(previous,npc))return;
    if(t->TalkCount!=(index>=11?2:1)|| (index>=11&&d->Flags!=609))throw std::runtime_error("Restart counter/door boundary differs");
    bool eligible=true;int local=b.local,transition=b.transition;if(index==3||index==17){eligible=GameScript::EvaluateString(t,"IsValidForPartyDialog(\"Imoen\")")!=0;if(!eligible){local=0;transition=index==3?39:49;}}
    if(b.response<0){auto*w=DialogueButtonWindow();auto*c=w?GetControl(0,w):nullptr;if(!c||c->IsDisabled()||!c->IsVisible())return;}
    if(index==11){capture("restarted-dialogue",true);++autos;event("stock-restarted-dialogue-observed",O({{"target_id",NumberJSON(t->GetGlobalID())},{"speaker_id",NumberJSON(leader->GetGlobalID())}}));}
    const auto prefix="branch-"+NumberJSON(index);capture(prefix,true);std::vector<std::string> choices;
    for(size_t i=0;i<b.prefix.size();++i){auto value=core->GetString(ieStrRef(b.prefix[i]));String visible=String(1,static_cast<char16_t>(u'1'+i))+u". - "+value;if(value.empty()||text.find(visible)==String::npos)throw std::runtime_error("Required visible response prefix absent");choices.push_back(O({{"visible_index",NumberJSON(i)},{"value",NumberJSON(i)},{"strref",NumberJSON(b.prefix[i])},{"text",Q(MBStringFromString(value))}}));}
    Write(out+"/"+prefix+".text.json",O({{"index",NumberJSON(index)},{"dialog",Q(b.dlg)},{"state",NumberJSON(b.state)},{"npc_strref",NumberJSON(b.ref)},{"npc_text",Q(MBStringFromString(npc))},{"previous_text",Q(MBStringFromString(previous))},{"message_text",Q(MBStringFromString(text))},{"choices",A(choices)},{"imoen_eligible",eligible?"true":"false"},{"local",NumberJSON(local)},{"transition",NumberJSON(transition)}}));
    if(index==20)capture("before-join",true);
    if(b.response>=0){if(!ta->SupportsAction(ControlActionResponder::ActionKey(TextArea::Action::Select)))throw std::runtime_error("Normal Select responder absent");ta->SelectAvailableOption(b.local);}
    else{auto*w=DialogueButtonWindow();auto*c=w?GetControl(0,w):nullptr;if(!c||c->IsDisabled()||!c->IsVisible())return;const int labelRef=(index==10||index==20)?9371:9372;auto raw=core->GetString(ieStrRef(labelRef)),label=raw;if(c->Flags()&IE_GUI_BUTTON_LOWERCASE)StringToLower(label);else if(c->Flags()&IE_GUI_BUTTON_CAPS)StringToUpper(label);Write(out+"/"+prefix+".button.json",O({{"strref",NumberJSON(labelRef)},{"flags",NumberJSON(c->Flags())},{"raw",Q(MBStringFromString(raw))},{"actual",Q(MBStringFromString(c->QueryText()))}}));if(c->QueryText()!=label||!c->PerformAction())throw std::runtime_error("Actual Continue/End label/callback differs");}
    event("registered-branch",O({{"index",NumberJSON(index)},{"dialog",Q(b.dlg)},{"state",NumberJSON(b.state)},{"npc_strref",NumberJSON(b.ref)},{"local",NumberJSON(local)},{"transition",NumberJSON(transition)},{"imoen_eligible",eligible?"true":"false"},{"entry",Q(b.response>=0?"TextArea::SelectAvailableOption":"Control::PerformAction")}}));previous=text;++visited;if(index==3&&!eligible)index=6;else if(index==17&&!eligible)index=19;else ++index;phaseTick=ticks;return;}
   if(phase==3){if(g->GetPartySize(false)!=4||t->InParty!=4||t->GetDialog()!="MINSCJ"||t->TalkCount!=2||d->Flags!=609)return;idle=natural?idle+1:0;if(idle<4)return;capture("recruited",true);core->SetPause(PauseState::On,3);run("OpenOptions");advance(4);return;}
   core->SetPause(PauseState::On,3);
   if(phase==4){button("GUIOPT",2,6);advance(5);return;}
   if(phase==5){run("ChooseNewSave");button("GUISAVE",0,26);advance(6);return;}
   if(phase==6){auto*c=RequiredControl("GUISAVE",1,3);c->SetText(u"Redux Minsc Recruitment");if(!c->PerformAction(ControlActionResponder::ActionKey(Control::ValueChange)))throw std::runtime_error("Save name callback missing");event("registered-save-name",O({{"control","3"}}));advance(7);return;}
   if(phase==7){capture("before-save",true);button("GUISAVE",1,7);advance(8);return;}
   if(phase==8){for(const auto&s:core->GetSaveGameIterator()->GetSaveGames())if(s->GetName()==u"Redux Minsc Recruitment")saves.push_back(Q(s->GetPath()));if(saves.size()!=1)throw std::runtime_error("Unique ordinary GUI save absent");capture("final",true);completed=true;core->QuitFlag=QF_KILL;return;}
  }catch(const std::exception&e){error=e.what();core->QuitFlag=QF_KILL;}},250,-1);engine->Main();
 }catch(const std::exception&e){error=e.what();}
 Write(out+"/minsc-result.json",O({{"schema",Q("bg-redux-minsc-native/1")},{"nonce",Q(args["--nonce"])},{"journey",Q(args["--journey"])},{"completed",completed?"true":"false"},{"error",Q(error)},{"movement_commands",NumberJSON(moves)},{"talk_requests","0"},{"door_commands","0"},{"restart_requests","0"},{"auto_dialogues",NumberJSON(autos)},{"branches",NumberJSON(visited)},{"events",A(events)},{"samples",A(samples)},{"saves",A(saves)},{"os_pointer_input","false"},{"forced_outcomes","false"}}));
 if(engine){engine.reset();core=nullptr;VideoDriver.reset();PluginMgr::Get()->RunCleanup();}StopLog();return completed&&error.empty()?0:1;
}
