// External normal-loop menu observer. Reuse the established host's serializers,
// fonts and destruction order; do not alter or replace an application screen.
#define main ReduxLegacyGUIProbeMain
#include "../phase0/native/gui_probe.cpp"
#undef main
#include "GUI/Button.h"
#include "RNG.h"
#include <chrono>
#include <iostream>

// Same-process byte equality only. Never export object bytes or pointer values.
static std::string DisplayActorBytes()
{
    std::string value;
    for (int i=0; i<core->GetGame()->GetPartySize(false); ++i) {
        const auto* actor=core->GetGame()->GetPC(i, false);
        value.append(reinterpret_cast<const char*>(&actor->BaseStats),sizeof(actor->BaseStats));
        value.append(reinterpret_cast<const char*>(&actor->Modified),sizeof(actor->Modified));
        value.append(reinterpret_cast<const char*>(&actor->ToHit),sizeof(actor->ToHit));
        value.append(reinterpret_cast<const char*>(&actor->weaponInfo),sizeof(actor->weaponInfo));
    }
    return value;
}

struct Display3EControl {
    bool active;
    explicit Display3EControl(bool requested): active(requested)
    {
        if (active) {
            if (core->HasFeature(GFFlags::RULES_3ED)) throw std::runtime_error("3E diagnostic requires an initial 2E game");
            core->SetFeature(GFFlags::RULES_3ED);
        }
    }
    ~Display3EControl() { if (active) core->ClearFeature(GFFlags::RULES_3ED); }
};

static const std::vector<const char*> MenuPacks = {"GUIOPT", "GUIREC", "GUISAVE", "GUILOAD", "GUIMAP", "GUIWMAP", "GUIJRNL", "GUIMG", "GUIPR", "WIN_KEYS", "OPTWIN", "PORTWIN"};

static void PressRegisteredMenu(const char* pack, ScriptingId windowId, ScriptingId controlId)
{
    // Resolve the requested alias itself, rather than assuming its ID equals
    // the window's primary pack ID (WIN_KEYS/OPTWIN are ordinary aliases).
    const auto* ref = static_cast<const ViewScriptingRef*>(ScriptEngine::GetScriptingRef(ScriptingGroup_t(pack), windowId));
    auto* window = GetView<Window>(ref);
    auto* control = window ? GetControl(controlId, window) : nullptr;
    if (!control || control->IsDisabled() || !control->IsVisible() || !control->PerformAction())
        throw std::runtime_error("Registered menu callback unavailable/refused");
}

static std::string MenuUIJSON()
{
    std::vector<std::string> rows;
    auto packs = MenuPacks;
    for (auto pack : {"GUIINV", "WIN_TOP", "GAMEWIN", "SUB_WIN", "LOADWIN"}) packs.push_back(pack);
    for (const auto* pack : packs) {
        std::set<View*> seen;
        for (auto* view : GetViews(ScriptingGroup_t(pack))) {
            if (!seen.insert(view).second) continue;
            const auto* ref = view->GetScriptingRef();
            auto* window = view->GetWindow();
            const auto* wr = window ? window->GetScriptingRef() : nullptr;
            if (!ref || (window && !wr)) continue;
            auto* ctrl = dynamic_cast<Control*>(view);
            auto* button = dynamic_cast<Button*>(view);
            // Button::DragCursor returns Picture, unless the base debug cursor
            // is active. Fail closed on that fallback; never call this a resref.
            const bool pictureObservable = button && !button->Control::DragCursor();
            auto picture = pictureObservable ? button->DragCursor() : Holder<Sprite2D>();
            const auto r = view->Frame();
            rows.push_back(O({{"pack", Q(pack)}, {"id", NumberJSON(ctrl ? ctrl->ControlID : ref->Id)},
                {"window", wr ? NumberJSON(wr->Id) : "null"}, {"type", ctrl ? NumberJSON(ctrl->ControlType) : "null"},
                {"rect", A({NumberJSON(r.x),NumberJSON(r.y),NumberJSON(r.w),NumberJSON(r.h)})},
                {"visible", view->IsVisible() ? "true" : "false"}, {"disabled", view->IsDisabled() ? "true" : "false"},
                {"flags", NumberJSON(view->Flags())}, {"text", ctrl ? Q(MBStringFromString(ctrl->QueryText())) : "null"},
                {"value", ctrl ? NumberJSON(ctrl->GetValue()) : "null"},
                {"tooltip", Q(MBStringFromString(view->TooltipText()))},
                {"stored_tooltip", Q(MBStringFromString(view->View::TooltipText()))},
                {"picture_observable", pictureObservable ? "true" : "false"},
                {"picture_present", picture ? "true" : "false"},
                {"picture_size", picture ? A({NumberJSON(picture->Frame.w),NumberJSON(picture->Frame.h)}) : "null"}}));
        }
    }
    return O({{"schema", Q("bg-redux-menu-ui/1")}, {"controls", A(rows)}});
}

static std::string ObserverJSON()
{
    std::vector<std::string> actors;
    auto* game = core->GetGame();
    for (int i=0; i<game->GetPartySize(false); ++i) {
        auto* actor = game->GetPC(i, false);
        auto action = actor->GetCurrentAction();
        std::vector<std::string> weapons;
        for (int hand=0;hand<2;++hand) {
            const auto& wi=actor->weaponInfo[hand];
            auto* header=wi.extHeader;
            weapons.push_back(O({{"hand",NumberJSON(hand)}, {"slot",NumberJSON(wi.slot)},
                {"header_dice",header?NumberJSON(header->DiceThrown):"null"},
                {"header_sides",header?NumberJSON(header->DiceSides):"null"},
                {"header_bonus",header?NumberJSON(header->DamageBonus):"null"},
                {"cached_proficiency_bonus",NumberJSON(wi.profdmgbon)}, {"launcher_bonus",NumberJSON(wi.launcherDmgBonus)}}));
        }
        actors.push_back(O({{"party_index", NumberJSON(i+1)}, {"runtime_id", NumberJSON(actor->GetGlobalID())},
            {"cached_thac0", NumberJSON(actor->ToHit.GetTotal())}, {"cached_base_thac0", NumberJSON(actor->ToHit.GetBase())},
            {"cached_tohit_components", O({
                {"weapon", NumberJSON(actor->ToHit.GetWeaponBonus())}, {"armor", NumberJSON(actor->ToHit.GetArmorBonus())},
                {"shield", NumberJSON(actor->ToHit.GetShieldBonus())}, {"ability", NumberJSON(actor->ToHit.GetAbilityBonus())},
                {"proficiency", NumberJSON(actor->ToHit.GetProficiencyBonus())}, {"generic", NumberJSON(actor->ToHit.GetGenericBonus())},
                {"effects", NumberJSON(actor->ToHit.GetFxBonus())}})},
            {"used_left_hand", actor->usedLeftHand ? "true" : "false"},
            {"attack_count", NumberJSON(actor->attackcount)},
            {"attacks_per_round_stat", NumberJSON(actor->GetSafeStat(IE_NUMBEROFATTACKS))},
            {"private_attacks_per_round_cache_sampled", "false"},
            {"action_id", action ? NumberJSON(action->actionID) : "null"},
            {"action_target", NumberJSON(actor->CurrentActionTarget)}, {"action_state", NumberJSON(actor->CurrentActionState)},
            {"action_ticks", NumberJSON(actor->CurrentActionTicks)}, {"weapon_cache",A(weapons)}}));
    }
    return O({{"schema",Q("bg-redux-menu-observer/1")}, {"actors",A(actors)}, {"rng_sampled","false"}});
}

int main(int argc, char** argv)
{
    std::map<std::string,std::string> args;
    for (int i=1; i+1<argc; i+=2) args[argv[i]]=argv[i+1];
    for (auto required : {"--config", "--output", "--scripts"}) if (!args.count(required)) return 64;
    const auto out = args["--output"];
    const auto journey = args.count("--journey") ? args["--journey"] : "menus";
    if (journey != "menus" && journey != "stats" && journey != "display-query" && journey != "hotkeys-edit" && journey != "hotkeys-reload") return 64;
    if (!args.count("--nonce") || args["--nonce"].size()!=32 ||
        args["--nonce"].find_first_not_of("0123456789abcdef")!=std::string::npos) return 64;
    const auto runtime = journey == "menus" ? "MenuRuntime" : journey == "stats" ? "StatsRuntime" : journey == "display-query" ? "DisplayQueryRuntime" : "HotkeyRuntime";
    std::filesystem::create_directories(out);
    if (std::filesystem::exists(out+"/menu-host-result.json")) return 73;
    std::setlocale(LC_ALL,".UTF8");
    std::atexit(StopLog);
    std::unique_ptr<Interface> engine;
    int rc=0, stage=-1, waits=0, ticks=0, captures=0, callbacks=0, keys=0;
    bool completed=false;
    int queryObservations=0;
    try {
        const char* argvEngine[]={"redux-menu-probe","-c",args["--config"].c_str()};
        auto config=LoadFromArgs(3,const_cast<char**>(argvEngine));
        ToggleLogging(true); AddLogWriter(createStdioLogWriter()); SetMainLogLevel(FATAL);
        engine=std::make_unique<Interface>(std::move(config));
        auto script=core->GetGUIScriptEngine();
        const std::string configure = (journey == "menus" || journey == "stats" || journey == "display-query") ? Q(out)+","+Q(args["--nonce"]) : Q(out)+","+Q(journey)+","+Q(args["--nonce"]);
        if (!script->ExecString("import sys; sys.path.insert(0,"+Q(args["--scripts"])+"); import "+std::string(runtime)+"; "+runtime+".Configure("+configure+")"))
            throw std::runtime_error("Cannot initialize external menu plan");
        core->SetNextScript("MenuStart");
        core->SetTimer([&]() {
            try {
                if (++ticks>1200) throw std::runtime_error("Menu plan exceeded 300-second timer budget");
                if (stage==-1) {
                    if (!script->ExecString("import MenuStart; MenuStart.PopulateLoad()")) throw std::runtime_error("Load list not ready");
                    Press("GUILOAD",0,26); stage=0; return;
                }
                if (!core->GetGame() || !core->GetGameControl() || !GetViews(ScriptingGroup_t("LOADWIN")).empty()) {
                    if (++waits>80) throw std::runtime_error("Menu game/load boundary not ready");
                    return;
                }
                if (stage==0) {
                    core->SetPause(PauseState::On,3);
                    Write(out+"/fonts.json",FontsJSON());
                    Write(out+"/before.state.json",Snapshot(core->GetGame()));
                    Write(out+"/before.observer.json",ObserverJSON());
                    stage=1;
                }
                const bool queryMode=journey=="display-query";
                std::string actorBytes;
                std::mt19937_64 rngBefore, rngAfter;
                bool rngReadyBefore=false;
                if (queryMode) {
                    actorBytes=DisplayActorBytes();
                    rngReadyBefore=RNG::TrySnapshotState(rngBefore);
                }
                const bool controlled3E=queryMode && core->GetDictionary().Get("Phase1Display3EControl",0);
                const auto queryStart=std::chrono::steady_clock::now();
                {
                    Display3EControl control(controlled3E);
                    if (controlled3E) std::cout << "[DisplayQueryControl]: begin unsupported-3e rejection" << std::endl;
                    if (!script->ExecString(std::string(runtime)+".Step()")) throw std::runtime_error("Menu plan Python exception");
                    if (controlled3E) std::cout << "[DisplayQueryControl]: end unsupported-3e rejection" << std::endl;
                }
                const auto queryNanoseconds=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-queryStart).count();
                if (queryMode) {
                    if (controlled3E) core->GetDictionary().Set("Phase1Display3EControl",0);
                    const int kind=core->GetDictionary().Get("Phase1DisplayKind",0);
                    if (kind) {
                        const bool rngReadyAfter=RNG::TrySnapshotState(rngAfter);
                        Write(out+"/display-query-step-"+NumberJSON(++queryObservations)+".json",O({
                            {"nonce",Q(args["--nonce"])}, {"kind",NumberJSON(kind)},
                            {"runtime_step",NumberJSON(core->GetDictionary().Get("Phase1MenuStep",0))},
                            {"actor_stats_and_cache_bytes_unchanged",actorBytes==DisplayActorBytes()?"true":"false"},
                            {"calling_thread_rng_before_available",rngReadyBefore?"true":"false"},
                            {"calling_thread_rng_after_available",rngReadyAfter?"true":"false"},
                            {"calling_thread_rng_unchanged",rngReadyBefore&&rngReadyAfter&&rngBefore==rngAfter?"true":"false"},
                            {"controlled_3e_rejection",controlled3E?"true":"false"},
                            {"feature_flag_restored",!core->HasFeature(GFFlags::RULES_3ED)?"true":"false"},
                            {"python_step_nanoseconds",NumberJSON(queryNanoseconds)}}));
                    }
                }
                const int pack=core->GetDictionary().Get("Phase1PressPack",0);
                if (pack) {
                    if (pack<1 || pack>int(MenuPacks.size())) throw std::runtime_error("Invalid menu callback pack");
                    const auto name="callback-"+NumberJSON(callbacks+1);
                    Write(out+"/"+name+"-before.state.json",Snapshot(core->GetGame()));
                    Write(out+"/"+name+"-before.observer.json",ObserverJSON());
                    const int window=core->GetDictionary().Get("Phase1PressWindow",0);
                    const int control=core->GetDictionary().Get("Phase1PressControl",0);
                    PressRegisteredMenu(MenuPacks[pack-1],window,control);
                    Write(out+"/"+name+".json",O({{"schema",Q("bg-redux-callback-dispatch/1")}, {"nonce",Q(args["--nonce"])},
                        {"pack",Q(MenuPacks[pack-1])}, {"window",NumberJSON(window)}, {"control",NumberJSON(control)},
                        {"performed","true"}, {"sequence",NumberJSON(callbacks+1)}, {"timer_tick",NumberJSON(ticks)},
                        {"runtime_step",NumberJSON(core->GetDictionary().Get("Phase1MenuStep",0))}}));
                    Write(out+"/"+name+"-after.state.json",Snapshot(core->GetGame()));
                    Write(out+"/"+name+"-after.observer.json",ObserverJSON());
                    ++callbacks;
                    core->GetDictionary().Set("Phase1NativeCallbacks",callbacks);
                }
                const int key=core->GetDictionary().Get("Phase1DispatchKey",0);
                if (key) {
                    if (journey=="menus" || key < 'a' || key > 'z') throw std::runtime_error("Unsupported journey key event");
                    const auto name="key-"+NumberJSON(keys+1);
                    Write(out+"/"+name+"-before.ui.json",MenuUIJSON());
                    Write(out+"/"+name+"-before.state.json",Snapshot(core->GetGame()));
                    Write(out+"/"+name+"-before.observer.json",ObserverJSON());
                    EventMgr events;
                    events.DispatchEvent(EventMgr::CreateKeyEvent(static_cast<KeyboardKey>(key),true,0));
                    events.DispatchEvent(EventMgr::CreateKeyEvent(static_cast<KeyboardKey>(key),false,0));
                    Write(out+"/"+name+"-after.ui.json",MenuUIJSON());
                    Write(out+"/"+name+"-after.state.json",Snapshot(core->GetGame()));
                    Write(out+"/"+name+"-after.observer.json",ObserverJSON());
                    Write(out+"/"+name+".json",O({{"schema",Q("bg-redux-key-dispatch/1")}, {"nonce",Q(args["--nonce"])},
                        {"sequence",NumberJSON(keys+1)}, {"keycode",NumberJSON(key)}, {"modifiers","0"},
                        {"keydown_dispatched","true"}, {"keyup_dispatched","true"},
                        {"route",Q("EventMgr::DispatchEvent")}, {"timer_tick",NumberJSON(ticks)}, {"os_input_injected","false"}}));
                    ++keys;
                    core->GetDictionary().Set("Phase1NativeKeys",keys);
                }
                const int capture=core->GetDictionary().Get("Phase1MenuCapture",0);
                if (capture) {
                    const auto name="capture-"+NumberJSON(capture);
                    Write(out+"/"+name+".ui.json",MenuUIJSON());
                    Write(out+"/"+name+".state.json",Snapshot(core->GetGame()));
                    Write(out+"/"+name+".observer.json",ObserverJSON());
                    PluginHolder<ImageWriter> writer=MakePluginHolder<ImageWriter>(PLUGIN_IMAGE_WRITER_BMP);
                    FileStream file;
                    if (!writer || !file.Create(out,name,IE_BMP_CLASS_ID)) throw std::runtime_error("Cannot create menu screenshot");
                    writer->PutImage(&file,core->GetWindowManager()->GetScreenshot(nullptr));
                    ++captures;
                }
                core->SetPause(PauseState::On,3);
                if (core->GetDictionary().Get("Phase1MenuComplete",0)) {
                    Write(out+"/after.state.json",Snapshot(core->GetGame()));
                    Write(out+"/after.observer.json",ObserverJSON());
                    completed=true; core->QuitFlag=QF_KILL;
                }
            } catch (const std::exception& error) {
                Write(out+"/error.json",O({{"stage",NumberJSON(stage)},{"error",Q(error.what())}}));
                rc=1; core->QuitFlag=QF_KILL;
            }
        },250,-1);
        engine->Main();
        if (!completed) rc=1;
        if (core->GetDictionary().Get("Phase1FailedChecks",0)) rc=1;
    } catch (const std::exception& error) {
        Write(out+"/error.json",O({{"error",Q(error.what())}})); rc=1;
    }
    Write(out+"/menu-host-result.json",O({{"schema",Q("bg-redux-menu-host/1")}, {"completed",completed?"true":"false"},
        {"captures",NumberJSON(captures)},{"callbacks",NumberJSON(callbacks)}, {"timer_ticks",NumberJSON(ticks)},
        {"native_keys",NumberJSON(keys)}, {"journey",Q(journey)}, {"nonce",Q(args["--nonce"])},
        {"load_waits",NumberJSON(waits)},{"visual_acceptance","false"},{"pointer_hit_testing","false"}}));
    if (engine) { engine.reset(); core=nullptr; VideoDriver.reset(); PluginMgr::Get()->RunCleanup(); }
    StopLog(); return rc;
}
