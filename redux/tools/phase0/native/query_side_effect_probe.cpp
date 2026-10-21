// External library-mode query observer for the frozen engine DLL.
// No normal game loop, save operation, arbitrary expression or tick stepping.
#define REDUX_GUI_HOST
#include "save_probe.cpp"
#include "GameScript/GameScript.h"
#include "GameScript/Matching.h"
#include "GameScript/Targets.h"

#include <filesystem>

static std::string Artifact(const std::string& output, unsigned call, const char* suffix)
{
    return output + "/call-" + NumberJSON(call) + "-" + suffix + ".state.json";
}

int main(int argc, char** argv)
{
    std::map<std::string, std::string> args;
    for (int i = 1; i + 1 < argc; i += 2) args[argv[i]] = argv[i + 1];
    if (argc % 2 != 1 || !args.count("--config") || !args.count("--output")
        || !args.count("--save-dir") || !args.count("--case-id") || !args.count("--repeats")) return 64;
    const std::string output = args["--output"];
    std::setlocale(LC_ALL, ".UTF8");
    std::atexit(StopLog);
    std::unique_ptr<Interface> engine;
    std::vector<std::string> observations, parsed;
    bool completed = false;
    std::string failure;
    int repeats = 0;
    ieDword senderID = 0, targetID = 0;
    try {
        repeats = std::stoi(args["--repeats"]);
        if (repeats < 1 || repeats > 32) throw std::runtime_error("Repeats must be in [1,32]");
        const char* engineArgs[] = {"redux-query-side-effects", "-c", args["--config"].c_str()};
        auto config = LoadFromArgs(3, const_cast<char**>(engineArgs));
        ToggleLogging(true);
        AddLogWriter(createStdioLogWriter());
        SetMainLogLevel(FATAL);
        engine = std::make_unique<Interface>(std::move(config));
        SetTokenAsString("SaveDir", u"save");
        auto selected = MakeHolder<SaveGame>(args["--save-dir"], "HarnessInput", core->GameNameResRef,
                                             "HarnessInput", 0, 7);
        core->LoadGame(selected, GAMVersion::GemRB);
        Game* game = core->GetGame();
        if (!game || game->GetPartySize(false) != 2) throw std::runtime_error("Requires exactly two party actors");
        for (int i = 0; i < game->GetPartySize(false); ++i) ValidateEffects(game->GetPC(i, false));
        for (int i = 0; i < game->GetNPCCount(); ++i) ValidateEffects(game->GetNPC(i));
        game->ConsolidateParty();
        auto* control = core->StartGameControl();
        const auto* first = core->GetFirstSelectedPC(true);
        if (!control || !first) throw std::runtime_error("Missing game control/selected living actor");
        control->ChangeMap(first, true);
        for (int i = 0; i < game->GetPartySize(false); ++i) {
            auto* pc = game->GetPC(i, false);
            if (pc->GetCurrentArea() != game->GetCurrentArea()) game->GetCurrentArea()->AddActor(pc, true);
        }
        if (!game->SelectPCSingle(1)) throw std::runtime_error("Sender selection refused");
        Actor* sender = game->GetPC(0, false);
        Actor* target = game->GetPC(1, false);
        if (!sender || !target || sender == target) throw std::runtime_error("Distinct sender/target missing");
        senderID = sender->GetGlobalID(); targetID = target->GetGlobalID();
        const char* queries[] = {"WeaponEffectiveVs(Player2,MAINHAND)", "WeaponCanDamage(Player2,MAINHAND)"};
        const unsigned expectedIDs[] = {0xec, 0xf2};
        for (unsigned i = 0; i < 2; ++i) {
            auto trigger = GenerateTrigger(queries[i]);
            if (!trigger || trigger->triggerID != expectedIDs[i] || trigger->int0Parameter != 1)
                throw std::runtime_error("Fixed query did not parse as expected EE trigger/MAINHAND");
            std::unique_ptr<Targets> targets(GetAllObjects(game->GetCurrentArea(), sender, trigger.get(), 0));
            if (!targets || targets->Count() != 1 || targets->GetTarget(0, ST_ACTOR) != target)
                throw std::runtime_error("Parsed Player2 does not resolve to the declared target");
            parsed.push_back(O({{"expression",Q(queries[i])}, {"trigger_id",NumberJSON(trigger->triggerID)},
                                 {"hand",NumberJSON(trigger->int0Parameter)}, {"target_count",NumberJSON(targets->Count())},
                                 {"target_runtime_id",NumberJSON(targetID)}}));
        }
        Write(output + "/initialized.state.json", Snapshot(game));
        unsigned call = 0;
        const auto evaluate = [&](const char* expression, int repetition) {
            ++call;
            const auto before = Snapshot(game);
            Write(Artifact(output, call, "before"), before);
            const int value = GameScript::EvaluateString(sender, expression);
            const auto after = Snapshot(game);
            Write(Artifact(output, call, "after"), after);
            observations.push_back(O({{"call",NumberJSON(call)}, {"expression",Q(expression)},
                {"repetition",NumberJSON(repetition)}, {"value",NumberJSON(value)},
                {"before",Q("call-"+NumberJSON(call)+"-before.state.json")},
                {"after",Q("call-"+NumberJSON(call)+"-after.state.json")},
                {"native_equal",before == after ? "true" : "false"}}));
            return value;
        };
        if (evaluate("True()", 0) != 1 || evaluate("False()", 0) != 0)
            throw std::runtime_error("Positive/negative evaluator control failed");
        for (int repetition = 1; repetition <= repeats; ++repetition) {
            evaluate(queries[0], repetition);
            evaluate(queries[1], repetition);
        }
        Write(output + "/final.state.json", Snapshot(game));
        completed = true;
    } catch (const std::exception& error) {
        failure = error.what();
    }
    Write(output + "/query-result.json", O({{"schema",Q("bg-redux-query-side-effects-native/1")},
        {"case_id",Q(args["--case-id"])}, {"repeats",NumberJSON(repeats)}, {"completed",completed ? "true" : "false"},
        {"sender_runtime_id",NumberJSON(senderID)}, {"target_runtime_id",NumberJSON(targetID)},
        {"parsed_queries",A(parsed)}, {"observations",A(observations)}, {"error",Q(failure)},
        {"scope",Q("Same-process collected state around fixed query calls after library-mode initialization; no game loop/ticks/save. Hidden state and RNG internals are not observed.")}}));
    if (engine) {
        core->SetGame(nullptr);
        VideoDriver.reset();
        engine.reset();
        core = nullptr;
        PluginMgr::Get()->RunCleanup();
    }
    StopLog();
    return completed ? 0 : 1;
}
