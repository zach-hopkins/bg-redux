// External Phase 1 six-hand query observer. No normal loop, ticks or saves.
// Serializer is an unchanged private-tool copy of the Phase 0 implementation.
#define REDUX_GUI_HOST
#include "phase0_save_probe_snapshot.cpp"
#include "Item.h"
#include "GameScript/GameScript.h"
#include "GameScript/Matching.h"
#include "GameScript/Targets.h"

static const char* Queries[] = {
    "WeaponEffectiveVs(Player2,MAINHAND)", "WeaponCanDamage(Player2,MAINHAND)",
    "WeaponEffectiveVs(Player2,OFFHAND)", "WeaponCanDamage(Player2,OFFHAND)",
    "WeaponEffectiveVs(Player2,BOTH)", "WeaponCanDamage(Player2,BOTH)"
};

static std::string Weapons(const Actor* actor)
{
    std::vector<std::string> hands;
    for (unsigned hand = 0; hand < 2; ++hand) {
        const auto& wi = actor->weaponInfo[hand];
        int headerIndex = -1;
        if (wi.item && wi.extHeader) {
            for (size_t i = 0; i < wi.item->extHeaders.size(); ++i) {
                if (&wi.item->extHeaders[i] == wi.extHeader) headerIndex = static_cast<int>(i);
            }
        }
        hands.push_back(O({{"hand",NumberJSON(hand+1)}, {"slot",NumberJSON(wi.slot)},
            {"item",wi.item ? Q(wi.item->Name.c_str()) : "null"},
            {"item_flags",wi.item ? NumberJSON(wi.item->Flags) : "null"},
            {"base_enchantment",wi.item ? NumberJSON(wi.item->Enchantment) : "null"},
            {"itemflags",NumberJSON(wi.itemflags)}, {"enchantment",NumberJSON(wi.enchantment)},
            {"wflags",NumberJSON(wi.wflags)}, {"header_index",NumberJSON(headerIndex)},
            {"header",wi.extHeader ? O({{"attack_type",NumberJSON(wi.extHeader->AttackType)},
                {"location",NumberJSON(wi.extHeader->Location)}, {"damage_type",NumberJSON(wi.extHeader->DamageType)},
                {"dice_sides",NumberJSON(wi.extHeader->DiceSides)}, {"dice_thrown",NumberJSON(wi.extHeader->DiceThrown)},
                {"damage_bonus",NumberJSON(wi.extHeader->DamageBonus)}, {"charges",NumberJSON(wi.extHeader->Charges)},
                {"recharge_flags",NumberJSON(wi.extHeader->RechargeFlags)}}) : "null"}}));
    }
    return O({{"schema",Q("bg-redux-phase1-weapon-cache/1")}, {"sender_runtime_id",NumberJSON(actor->GetGlobalID())},
        {"equipped_slot",NumberJSON(actor->inventory.GetEquippedSlot())},
        {"shield_slot",NumberJSON(actor->inventory.GetShieldSlot())}, {"hands",A(hands)}});
}

int main(int argc, char** argv)
{
    std::map<std::string, std::string> args;
    for (int i = 1; i+1 < argc; i += 2) {
        if (args.count(argv[i])) return 64;
        args[argv[i]] = argv[i+1];
    }
    const std::vector<std::string> required = {"--config", "--output", "--save-dir", "--case-id", "--repeats"};
    if (argc % 2 != 1 || args.size() != required.size()) return 64;
    for (const auto& key : required) if (!args.count(key)) return 64;
    const auto& output = args["--output"];
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
        const char* engineArgs[] = {"redux-phase1-weapon-query", "-c", args["--config"].c_str()};
        auto config = LoadFromArgs(3, const_cast<char**>(engineArgs));
        ToggleLogging(true); AddLogWriter(createStdioLogWriter()); SetMainLogLevel(FATAL);
        engine = std::make_unique<Interface>(std::move(config));
        SetTokenAsString("SaveDir", u"save");
        auto selected = MakeHolder<SaveGame>(args["--save-dir"], "HarnessInput", core->GameNameResRef, "HarnessInput", 0, 7);
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
        for (unsigned i = 0; i < 6; ++i) {
            auto trigger = GenerateTrigger(Queries[i]);
            if (!trigger || trigger->triggerID != (i % 2 ? 0xf2 : 0xec) || trigger->int0Parameter != static_cast<int>(i/2+1))
                throw std::runtime_error("Fixed query trigger/hand parse failed");
            std::unique_ptr<Targets> targets(GetAllObjects(game->GetCurrentArea(), sender, trigger.get(), 0));
            if (!targets || targets->Count() != 1 || targets->GetTarget(0, ST_ACTOR) != target)
                throw std::runtime_error("Parsed Player2 does not resolve to declared target");
            parsed.push_back(O({{"expression",Q(Queries[i])}, {"trigger_id",NumberJSON(trigger->triggerID)},
                {"hand",NumberJSON(trigger->int0Parameter)}, {"target_count",NumberJSON(targets->Count())},
                {"target_runtime_id",NumberJSON(targetID)}}));
        }
        Write(output+"/initialized.state.json", Snapshot(game));
        Write(output+"/initialized.weapons.json", Weapons(sender));
        unsigned call = 0;
        const auto evaluate = [&](const char* expression, int repetition) {
            ++call;
            const auto stem = "call-"+NumberJSON(call);
            const auto before = Snapshot(game), weaponsBefore = Weapons(sender);
            Write(output+"/"+stem+"-before.state.json", before);
            Write(output+"/"+stem+"-before.weapons.json", weaponsBefore);
            const int value = GameScript::EvaluateString(sender, expression);
            const auto after = Snapshot(game), weaponsAfter = Weapons(sender);
            Write(output+"/"+stem+"-after.state.json", after);
            Write(output+"/"+stem+"-after.weapons.json", weaponsAfter);
            observations.push_back(O({{"call",NumberJSON(call)}, {"expression",Q(expression)},
                {"repetition",NumberJSON(repetition)}, {"value",NumberJSON(value)},
                {"before",Q(stem+"-before.state.json")}, {"after",Q(stem+"-after.state.json")},
                {"weapons_before",Q(stem+"-before.weapons.json")}, {"weapons_after",Q(stem+"-after.weapons.json")},
                {"native_equal",before == after ? "true" : "false"},
                {"weapons_equal",weaponsBefore == weaponsAfter ? "true" : "false"}}));
            return value;
        };
        const int trueControl = evaluate("True()", 0), falseControl = evaluate("False()", 0);
        if (trueControl != 1 || falseControl != 0) throw std::runtime_error("Evaluator controls failed");
        for (int repetition = 1; repetition <= repeats; ++repetition)
            for (const auto* query : Queries) evaluate(query, repetition);
        Write(output+"/final.state.json", Snapshot(game));
        Write(output+"/final.weapons.json", Weapons(sender));
        completed = true;
    } catch (const std::exception& error) {
        failure = error.what();
    }
    Write(output+"/query-result.json", O({{"schema",Q("bg-redux-phase1-weapon-query-native/1")},
        {"case_id",Q(args["--case-id"])}, {"repeats",NumberJSON(repeats)}, {"completed",completed ? "true" : "false"},
        {"sender_runtime_id",NumberJSON(senderID)}, {"target_runtime_id",NumberJSON(targetID)},
        {"parsed_queries",A(parsed)}, {"observations",A(observations)}, {"error",Q(failure)},
        {"scope",Q("Collected state and selected weapon caches after library initialization; no loop/ticks/save. Hidden state and RNG internals unobserved.")}}));
    if (engine) {
        core->SetGame(nullptr); VideoDriver.reset(); engine.reset(); core = nullptr;
        PluginMgr::Get()->RunCleanup();
    }
    StopLog();
    return completed ? 0 : 1;
}
