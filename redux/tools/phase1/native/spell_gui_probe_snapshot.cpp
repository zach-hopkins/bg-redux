// External full-loop host. Reuse the established snapshot serialization only.
// The pinned engine DLL and stock GUIScripts are not edited.
#define REDUX_GUI_HOST
#include "save_probe.cpp"
#include "GUI/WindowManager.h"
#include "GUI/GUIScriptInterface.h"
#include "GUI/TextSystem/Font.h"
#include "GUI/TextArea.h"
#include "GameData.h"
#include "GameScript/GameScript.h"
#include "ie_stats.h"
#include "ImageWriter.h"
#include "Streams/FileStream.h"
#include <set>
#include <typeinfo>
#include <filesystem>

static Window* WindowIn(const char* pack, ScriptingId id)
{
    for (auto* view : GetViews(ScriptingGroup_t(pack))) {
        auto* win = dynamic_cast<Window*>(view);
        if (win && win->GetScriptingRef() && win->GetScriptingRef()->Id == id) return win;
    }
    throw std::runtime_error(std::string("Required window missing: ") + pack + "/" + NumberJSON(id));
}

static Control* RequiredControl(const char* pack, ScriptingId win, ScriptingId id)
{
    auto* ctrl = GetControl(id, WindowIn(pack, win));
    if (!ctrl) throw std::runtime_error("Required control missing: " + NumberJSON(id));
    return ctrl;
}

static void Press(const char* pack, ScriptingId win, ScriptingId id)
{
    auto* ctrl = RequiredControl(pack, win, id);
    if (ctrl->IsDisabled() || !ctrl->IsVisible() || !ctrl->PerformAction())
        throw std::runtime_error("Control refused default callback: " + NumberJSON(id));
}

static std::string UIJSON()
{
    std::vector<std::string> controls;
    for (const auto* pack : {"GUILOAD", "GUIINV", "GUIREC", "GUIOPT", "GUISAVE", "WIN_TOP", "GAMEWIN"}) {
        std::set<View*> seen;
        for (auto* view : GetViews(ScriptingGroup_t(pack))) {
            if (!seen.insert(view).second) continue;
            auto* ctrl = dynamic_cast<Control*>(view);
            auto* win = view->GetWindow();
            // Closed windows can remain alive while their primary scripting
            // reference has been removed. Never dereference that absent ref.
            const auto* ref = view->GetScriptingRef();
            const auto* winref = win ? win->GetScriptingRef() : nullptr;
            if (!ref || (win && !winref)) continue;
            auto frame = view->Frame();
            controls.push_back(O({{"pack",Q(pack)}, {"id",NumberJSON(ctrl ? ctrl->ControlID : view->GetScriptingRef()->Id)},
                {"window", winref ? NumberJSON(winref->Id) : "null"},
                {"type",ctrl ? NumberJSON(ctrl->ControlType) : "null"},
                {"rect",A({NumberJSON(frame.x),NumberJSON(frame.y),NumberJSON(frame.w),NumberJSON(frame.h)})},
                {"visible",view->IsVisible()?"true":"false"}, {"disabled",view->IsDisabled()?"true":"false"},
                {"flags",NumberJSON(view->Flags())}, {"text",ctrl ? Q(MBStringFromString(ctrl->QueryText())) : "null"}}));
        }
    }
    return O({{"schema",Q("bg-redux-ui/1")}, {"controls",A(controls)},
        {"dialogue_flags",core->GetGameControl() ? NumberJSON(core->GetGameControl()->GetDialogueFlags()) : "null"}});
}

static void CheckpointSave(const std::string& destination)
{
    for (const auto& save : core->GetSaveGameIterator()->GetSaveGames()) {
        if (save->GetName()==u"Redux GUI Baseline") {
            std::filesystem::copy(save->GetPath(),destination,std::filesystem::copy_options::recursive);
            return;
        }
    }
    throw std::runtime_error("Expected GUI save missing at checkpoint");
}

static std::string FontsJSON()
{
    std::vector<std::string> rows;
    for (const auto* name : {"NORMAL","FLOATTXT","NUMBER","INITIALS","NUMBER2","NUMBER3","REALMS","STONEBIG","STONESML","TOOLFONT","TOOLTIP","STONSML","STATES","STATES2"}) {
        auto font = core->GetFont(ResRef(name));
        if (!font) { rows.push_back(O({{"name",Q(name)}, {"loaded","false"}})); continue; }
        std::vector<std::string> glyphs;
        for (char c : std::string("Aa0gW")) {
            const auto& glyph = font->GetGlyph(c);
            glyphs.push_back(O({{"char",Q(std::string(1,c))}, {"size",A({NumberJSON(glyph.size.w),NumberJSON(glyph.size.h)})},
                {"position",PointJSON(glyph.pos)}}));
        }
        rows.push_back(O({{"name",Q(name)}, {"loaded","true"}, {"runtime_type",Q(typeid(*font).name())},
            {"line_height",NumberJSON(font->LineHeight)}, {"baseline",NumberJSON(font->Baseline)},
            {"sample_width",NumberJSON(font->StringSize(u"Strength Armor Class 123").w)}, {"glyphs",A(glyphs)}}));
    }
    return O({{"schema",Q("bg-redux-fonts/1")}, {"fonts",A(rows)}});
}

// Deliberate laboratory effect applications, not player commands or a spell test.
static void StringProtectionChallenge(Actor* target, const std::string& out)
{
    auto* messages=core->GetMessageTextArea();
    if (!messages) throw std::runtime_error("Required message TextArea absent");
    EffectRef protection={"Protection:String",-1},display={"DisplayString",-1};
    std::vector<std::string> observations;
    auto challenge=[&](const char* phase,int strref,bool expectedSuppressed) {
        auto expected=core->GetString(ieStrRef(strref));
        if (expected.empty()) throw std::runtime_error("Required challenge string empty");
        auto before=messages->QueryText();
        auto effect=EffectQueue::CreateEffect(display,strref,0,FX_DURATION_INSTANT_PERMANENT);
        if (!effect) throw std::runtime_error("DisplayString effect unavailable");
        const int result=core->ApplyEffect(std::move(effect),target,target);
        auto after=messages->QueryText();
        const bool suppressed=before==after;
        const bool contains=after.find(expected)!=String::npos;
        observations.push_back(O({{"phase",Q(phase)},{"strref",NumberJSON(strref)},
            {"expected_suppressed",expectedSuppressed?"true":"false"},
            {"message_unchanged",suppressed?"true":"false"},{"expected_text_present",contains?"true":"false"},
            {"before_chars",NumberJSON(before.size())},{"after_chars",NumberJSON(after.size())},
            {"before_text",Q(MBStringFromString(before))},{"after_text",Q(MBStringFromString(after))},
            {"expected_text",Q(MBStringFromString(expected))},
            {"apply_return_code",NumberJSON(result)},
            {"passed",suppressed==expectedSuppressed && (suppressed || contains)?"true":"false"}}));
    };
    Write(out+"/challenge-before.state.json",Snapshot(core->GetGame()));
    for (int strref : {14665,41616,40979,40969,41495}) challenge("loaded-protection",strref,true);
    // Explicit causal removal: only this disposable target's opcode267 effects.
    target->fxqueue.RemoveAllEffects(protection);
    target->RefreshEffects();
    Write(out+"/challenge-removed.state.json",Snapshot(core->GetGame()));
    for (int strref : {14665,41616,40979,40969,41495}) challenge("removed-protection",strref,false);
    auto restored=EffectQueue::CreateEffect(protection,14665,134,FX_DURATION_INSTANT_PERMANENT);
    if (!restored) throw std::runtime_error("Protection:String effect unavailable");
    core->ApplyEffect(std::move(restored),target,target);
    auto* normalized=target->fxqueue.HasEffectWithParamPair(protection,14665,0);
    challenge("reapplied-protection",14665,true);
    Write(out+"/challenge-restored.state.json",Snapshot(core->GetGame()));
    Write(out+"/string-challenge.json",O({{"schema",Q("bg-redux-string-challenge/1")},
        {"laboratory_mutation","true"},{"reapplied_parameter2_normalized",normalized?"true":"false"},
        {"observations",A(observations)}}));
}

int main(int argc, char** argv)
{
    std::map<std::string,std::string> args;
    for (int i=1;i+1<argc;i+=2) args[argv[i]]=argv[i+1];
    if (!args.count("--config") || !args.count("--output") || !args.count("--scripts")) return 64;
    if (args.count("--mode") && args["--mode"]!="inspect" && args["--mode"]!="effect-cycle" &&
        args["--mode"]!="string-challenge" && args["--mode"]!="live-clock" && args["--mode"]!="save") return 64;
    const int runningSamples=args.count("--clock-running-samples")?std::stoi(args["--clock-running-samples"]):8;
    if (runningSamples<8 || runningSamples>320) return 64;
    std::setlocale(LC_ALL,".UTF8");
    std::atexit(StopLog);
    std::unique_ptr<Interface> engine;
    const auto out = args["--output"];
    int rc = 0, step = -1;
    bool completed = false;
    std::vector<std::string> events;
    std::vector<std::string> clockSamples;
    tick_t clockStart=0;
    int loadWaits=0;
    auto sampleClock=[&](int index,const char* phase) {
        std::vector<std::string> actionTrace;
        if (args.count("--trace-actions") && core->GetGame()->GetCurrentArea()) {
            auto* map=core->GetGame()->GetCurrentArea();
            for (int i=0;i<map->GetActorCount(true);++i) {
                auto* actor=map->GetActor(i,true);
                if (actor!=core->GetGame()->GetPC(0,false) && actor->GetScriptName()!="RDXFOE") continue;
                auto current=actor->GetCurrentAction();
                actionTrace.push_back(O({{"name",Q(actor->GetScriptName().c_str())},
                    {"runtime_id",NumberJSON(actor->GetGlobalID())},{"action_id",current?NumberJSON(current->actionID):"null"},
                    {"current_action_target",NumberJSON(actor->CurrentActionTarget)},
                    {"action_state",NumberJSON(actor->CurrentActionState)},
                    {"action_ticks",NumberJSON(actor->CurrentActionTicks)},
                    {"hp",NumberJSON(actor->GetStat(IE_HITPOINTS))},{"position",PointJSON(actor->Pos)}}));
            }
        }
        clockSamples.push_back(O({{"sample",NumberJSON(index)},{"phase",Q(phase)},
            {"elapsed_ms",NumberJSON(GetMilliseconds()-clockStart)},
            {"game_time",NumberJSON(core->GetGame()->GameTime.load())},
            {"real_time",NumberJSON(core->GetGame()->RealTime)},
            {"dialogue_flags",NumberJSON(core->GetGameControl()->GetDialogueFlags())},{"action_trace",A(actionTrace)}}));
        Write(out+"/clock-samples.json",O({{"schema",Q("bg-redux-live-clock/1")},
            {"ticks_per_second",NumberJSON(core->Time.ticksPerSec)},
            {"load_window_waits",NumberJSON(loadWaits)},{"samples",A(clockSamples)}}));
    };
    auto event = [&](const std::string& name) { events.push_back(Q(name)); Write(out+"/events.json",A(events)); };
    auto capture = [&](const std::string& name) {
        Write(out+"/"+name+".ui.json",UIJSON());
        if (core->GetGame()) Write(out+"/"+name+".state.json",Snapshot(core->GetGame()));
        PluginHolder<ImageWriter> writer=MakePluginHolder<ImageWriter>(PLUGIN_IMAGE_WRITER_BMP);
        if (!writer) throw std::runtime_error("No BMP writer");
        FileStream file;
        if (!file.Create(out,name,IE_BMP_CLASS_ID)) throw std::runtime_error("Cannot create screenshot");
        writer->PutImage(&file,core->GetWindowManager()->GetScreenshot(nullptr));
        event("captured:"+name);
    };
    try {
        const char* engineArgs[]={"redux-gui-probe","-c",args["--config"].c_str()};
        auto config=LoadFromArgs(3,const_cast<char**>(engineArgs));
        ToggleLogging(true); AddLogWriter(createStdioLogWriter()); SetMainLogLevel(FATAL);
        engine=std::make_unique<Interface>(std::move(config));
        auto script=core->GetGUIScriptEngine();
        // A dedicated startup module selects only this run's copied fixture.
        // All subsequent Game, inventory, record, options, load and save code is stock.
        if (!script->ExecString("import sys; sys.path.insert(0,"+Q(args["--scripts"])+")"))
            throw std::runtime_error("Cannot add external harness startup path");
        core->SetNextScript("ReduxStart");
        auto run=[&](const char* mod,const char* fn) {
            // ExecString reports Python exceptions and discards return values
            // (stock window loaders return GWindow, not a native Parameter).
            const std::string call=std::string(mod)+"."+fn;
            if (!script->ExecString(std::string("import ")+mod+"; "+call+"()"))
                throw std::runtime_error("Stock GUI call failed: "+call);
            event(call);
        };
        core->SetTimer([&]() {
            try {
                if (step==0 && (!core->GetGame() || !core->GetGameControl())) return;
                if (step==0 && args["--mode"]=="live-clock" && !GetViews(ScriptingGroup_t("LOADWIN")).empty()) {
                    ++loadWaits;
                    if (loadWaits>40) throw std::runtime_error("Load window readiness timed out");
                    return;
                }
                if (args["--mode"]=="live-clock" && step>0) {
                    const int index=step++;
                    const int endRunning=4+runningSamples;
                    sampleClock(index,index<=4?"paused-initial":(index<=endRunning?"running":"paused-final"));
                    if (index==4) { core->SetPause(PauseState::Off,3); event("clock:resume"); }
                    if (index==endRunning) { core->SetPause(PauseState::On,3); event("clock:pause"); }
                    if (index==endRunning+4) {
                        Write(out+"/clock-after.state.json",Snapshot(core->GetGame()));
                        completed=true; core->QuitFlag=QF_KILL;
                    }
                    return;
                }
                switch(step++) {
                case -1:
                    run("ReduxStart","PopulateLoad");
                    if (args["--mode"]!="effect-cycle" && args["--mode"]!="string-challenge" && args["--mode"]!="live-clock") capture("load-list");
                    Press("GUILOAD",0,26); event("press:load.baseline-row"); break;
                case 0:
                    run("ReduxStart","Ready");
                    if (args["--mode"]=="live-clock") {
                        clockStart=GetMilliseconds();sampleClock(0,"paused-initial");
                        Write(out+"/clock-before.state.json",Snapshot(core->GetGame()));
                        break;
                    }
                    if (args["--mode"]=="effect-cycle" || args["--mode"]=="string-challenge") {
                        Actor* target=nullptr;
                        auto* map=core->GetGame()->GetCurrentArea();
                        for (int i=0;i<map->GetActorCount(true);++i) {
                            auto* candidate=map->GetActor(i,true);
                            if (candidate->Pos==Point(2573,2461)) {
                                if (target) throw std::runtime_error("Ambiguous effect probe target");
                                target=candidate;
                            }
                        }
                        if (!target || !target->inventory.GetSlotItem(0) || target->inventory.GetSlotItem(0)->ItemResRef!="IMMCLOUD")
                            throw std::runtime_error("Required Mephit/IMMCLOUD fixture absent");
                        if (args["--mode"]=="string-challenge") {
                            StringProtectionChallenge(target,out);
                            completed=true; core->QuitFlag=QF_KILL; break;
                        }
                        Write(out+"/entry.state.json",Snapshot(core->GetGame()));
                        auto checks=[&]() {
                            EffectRef opcodeRef={"Protection:Opcode",-1},stringRef={"Protection:String",-1};
                            Fields status;
                            for (int opcode : {134,216}) status.emplace_back("opcode_"+NumberJSON(opcode),
                                target->fxqueue.HasEffectWithParam(opcodeRef,opcode)?"true":"false");
                            for (int strref : {14665,41616,40979,40969,41495}) status.emplace_back("string_"+NumberJSON(strref),
                                target->fxqueue.HasEffectWithParamPair(stringRef,strref,0)?"true":"false");
                            return O(status);
                        };
                        auto beforeChecks=checks();
                        target->RefreshEffects();
                        Write(out+"/refresh1.state.json",Snapshot(core->GetGame()));
                        target->RefreshEffects();
                        Write(out+"/refresh2.state.json",Snapshot(core->GetGame()));
                        auto afterChecks=checks();
                        const int saved=core->GetSaveGameIterator()->CreateSaveGame(Holder<SaveGame>(),StringView("Redux Effect Cycle"),
                            core->GetWindowManager()->GetScreenshotPreview(),false);
                        Write(out+"/persisted.state.json",Snapshot(core->GetGame()));
                        Write(out+"/effect-result.json",O({{"save_return_code",NumberJSON(saved)},
                            {"forced","false"},{"protection_queries_before",beforeChecks},{"protection_queries_after",afterChecks}}));
                        if (saved!=GEM_OK) throw std::runtime_error("Ordinary effect-cycle save failed");
                        completed=true; core->QuitFlag=QF_KILL; break;
                    }
                    Write(out+"/fonts.json",FontsJSON()); capture("00-game");
                    break;
                case 1: run("GUIINV","OpenInventoryWindow"); break;
                case 2: capture("01-inventory"); run("GUICommonWindows","CloseTopWindow"); break;
                case 3: run("GUIREC","OpenRecordsWindow"); break;
                case 4:
                    capture("02-record"); run("GUICommonWindows","CloseTopWindow");
                    if (args["--mode"]=="inspect") { completed=true; core->QuitFlag=QF_KILL; }
                    break;
                case 5: run("GUIOPT","OpenOptionsWindow"); break;
                case 6: capture("03-options"); Press("GUIOPT",2,6); event("press:options.save"); break;
                case 7: capture("04-save-list"); run("ReduxStart","ChooseNewRow"); break;
                case 8: Press("GUISAVE",0,26); event("press:save.new-row"); break;
                case 9:
                    capture("05-empty-confirm");
                    if (!RequiredControl("GUISAVE",1,7)->IsDisabled()) throw std::runtime_error("Empty name was not disabled");
                    if (RequiredControl("GUISAVE",1,7)->PerformAction()) throw std::runtime_error("Disabled empty-name save ran");
                    event("guard:empty-name-refused");
                    RequiredControl("GUISAVE",1,3)->SetText(u"Redux GUI Baseline");
                    if (!RequiredControl("GUISAVE",1,3)->PerformAction(ControlActionResponder::ActionKey(Control::ValueChange)))
                        throw std::runtime_error("Name edit ValueChange callback missing");
                    break;
                case 10:
                    capture("06-named-confirm"); Press("GUISAVE",1,7); event("press:save.create-confirm");
                    CheckpointSave(out+"/checkpoint-create"); break;
                case 11:
                    capture("07-after-create"); run("ReduxStart","VerifyCreated");
                    run("GUIOPT","OpenOptionsWindow"); break;
                case 12: Press("GUIOPT",2,6); break;
                case 13: run("ReduxStart","ChooseExistingRow"); Press("GUISAVE",0,26); break;
                case 14: capture("08-overwrite-confirm"); Press("GUISAVE",1,8); event("press:overwrite.cancel"); break;
                case 15:
                    capture("09-after-cancel"); CheckpointSave(out+"/checkpoint-cancel");
                    Press("GUISAVE",0,26); break;
                case 16:
                    capture("10-before-overwrite"); Press("GUISAVE",1,7); event("press:overwrite.confirm");
                    Write(out+"/overwrite-persisted.state.json",Snapshot(core->GetGame())); break;
                case 17: capture("11-after-overwrite"); run("ReduxStart","VerifyCreated"); completed=true; core->QuitFlag=QF_KILL; break;
                default: throw std::runtime_error("Invalid GUI test step");
                }
                // A paused observation scenario; GUI close callbacks restore
                // their own pause state. Reassert pause before the next tick.
                // Unpaused timing/playthrough behavior is a separate test.
                if (core->GetGameControl()) core->SetPause(PauseState::On,3);
            } catch (const std::exception& error) {
                Write(out+"/error.json",O({{"step",NumberJSON(step)}, {"error",Q(error.what())}}));
                rc=1; core->QuitFlag=QF_KILL;
            }
        },250,-1);
        engine->Main();
        if (!completed) rc=1;
        Write(out+"/gui-result.json",O({{"completed",completed?"true":"false"}, {"steps",NumberJSON(step)}, {"events",A(events)}}));
    } catch (const std::exception& error) {
        Write(out+"/error.json",O({{"error",Q(error.what())}})); rc=1;
    }
    // Match GemRB.cpp: GUI sprites/windows must die while VideoDriver exists.
    if (engine) { engine.reset(); core=nullptr; VideoDriver.reset(); PluginMgr::Get()->RunCleanup(); }
    StopLog(); return rc;
}
