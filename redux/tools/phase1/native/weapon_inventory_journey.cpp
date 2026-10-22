// External mutation journey. Includes the observer helpers, not its entrypoint.
// Deliberate inventory writes are separated from per-query invariance captures.
#define main UnusedSixQueryObserverMain
#include "weapon_query_probe.cpp"
#undef main
#include "GameData.h"
#include "GameScript/GSUtils.h"

#include <cstdint>
#include <filesystem>
#include <functional>

using RetainedItems = std::vector<std::pair<ResRef, const Item*>>;

static bool SafeCache(const Actor* actor, const RetainedItems& retained)
{
    for (const auto& wi : actor->weaponInfo) {
        if (!wi.item) { if (wi.extHeader) return false; continue; }
        bool found = false;
        for (const auto& resource : retained) {
            if (wi.item != resource.second) continue;
            found = !wi.extHeader;
            for (const auto& header : resource.second->extHeaders)
                if (&header == wi.extHeader) found = true;
        }
        if (!found) return false;
    }
    return true;
}

static std::string UnsafeCacheAddresses(const Actor* actor)
{
    std::vector<std::string> hands;
    for (const auto& wi : actor->weaponInfo) hands.push_back(O({
        {"item_address",Q(NumberJSON(reinterpret_cast<std::uintptr_t>(wi.item)))},
        {"header_address",Q(NumberJSON(reinterpret_cast<std::uintptr_t>(wi.extHeader)))}}));
    return O({{"safe_to_dereference","false"}, {"hands",A(hands)}});
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
    const auto output = args["--output"];
    std::setlocale(LC_ALL, ".UTF8"); std::atexit(StopLog);
    std::unique_ptr<Interface> engine;
    RetainedItems retained;
    std::vector<std::string> steps, parsed;
    bool completed = false;
    std::string failure;
    int repeats = 0;
    ieDword senderID = 0, targetID = 0;
    try {
        repeats = std::stoi(args["--repeats"]);
        if (repeats < 1 || repeats > 8) throw std::runtime_error("Repeats must be in [1,8]");
        const char* engineArgs[] = {"redux-inventory-journey", "-c", args["--config"].c_str()};
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
        auto* control = core->StartGameControl(); const auto* first = core->GetFirstSelectedPC(true);
        if (!control || !first) throw std::runtime_error("Missing game control/selection");
        control->ChangeMap(first, true);
        for (int i = 0; i < game->GetPartySize(false); ++i) {
            auto* pc = game->GetPC(i, false);
            if (pc->GetCurrentArea() != game->GetCurrentArea()) game->GetCurrentArea()->AddActor(pc, true);
        }
        if (!game->SelectPCSingle(1)) throw std::runtime_error("Sender selection refused");
        Actor* sender = game->GetPC(0, false); Actor* target = game->GetPC(1, false);
        senderID = sender->GetGlobalID(); targetID = target->GetGlobalID();
        auto& inventory = sender->inventory; const int offSlot = inventory.GetShieldSlot();
        const auto* main = inventory.GetSlotItem(35); const auto* off = inventory.GetSlotItem(offSlot);
        if (offSlot != 9 || inventory.GetEquipped() != 0 || inventory.GetEquippedHeader() != 0
            || !main || main->ItemResRef != ResRef("sw1h02") || !off || off->ItemResRef != ResRef("sw1h01"))
            throw std::runtime_error("Requires prepared case02 main+1/offnormal selection");
        for (const char* ref : {"sw1h01", "sw1h02", "shld01"}) {
            const Item* item = gamedata->GetItem(ResRef(ref), true);
            if (!item) throw std::runtime_error("Required retained item missing");
            retained.emplace_back(ResRef(ref), item);
        }
        if (retained[0].second->AnimationType != retained[1].second->AnimationType
            || retained[0].second->Enchantment != 0 || retained[1].second->Enchantment != 1)
            throw std::runtime_error("Same-animation/0-to-1 enchantment control missing");
        for (unsigned i = 0; i < 6; ++i) {
            auto trigger = GenerateTrigger(Queries[i]);
            if (!trigger || trigger->triggerID != (i % 2 ? 0xf2 : 0xec) || trigger->int0Parameter != static_cast<int>(i/2+1))
                throw std::runtime_error("Fixed query parser mismatch");
            std::unique_ptr<Targets> targets(GetAllObjects(game->GetCurrentArea(), sender, trigger.get(), 0));
            if (!targets || targets->Count() != 1 || targets->GetTarget(0, ST_ACTOR) != target)
                throw std::runtime_error("Player2 target mismatch");
            parsed.push_back(O({{"expression",Q(Queries[i])}, {"trigger_id",NumberJSON(trigger->triggerID)},
                {"hand",NumberJSON(trigger->int0Parameter)}, {"target_count",NumberJSON(targets->Count())},
                {"target_runtime_id",NumberJSON(targetID)}}));
        }
        const auto removeOff = [&]() {
            if (!inventory.GetSlotItem(offSlot)) return;
            if (!inventory.UnEquipItem(offSlot, false)) throw std::runtime_error("Ordinary unequip refused");
            std::unique_ptr<CREItem> removed(inventory.RemoveItem(offSlot, 0));
            if (!removed || inventory.GetSlotItem(offSlot)) throw std::runtime_error("Ordinary removal failed");
        };
        const auto ordinary = [&](const char* ref) {
            removeOff();
            auto item = std::make_unique<CREItem>();
            if (!CreateItemCore(item.get(), ResRef(ref), 0, 0, 0)) throw std::runtime_error("Ordinary item creation failed");
            if (inventory.AddSlotItem(item.get(), offSlot) != ASI_SUCCESS) throw std::runtime_error("Ordinary off-hand add refused");
            item.release(); sender->ReinitQuickSlots();
        };
        const auto createItemAPI = [&](const char* ref) {
            // Exact mutation calls used by GemRB_CreateItem's explicit-slot path.
            inventory.SetSlotItemRes(ResRef(ref), offSlot, 0, 0, 0);
            inventory.EquipItem(offSlot); sender->ReinitQuickSlots();
        };
        const auto observe = [&](const char* id, const char* route, const char* expectedOff, const std::function<void()>& mutate) {
            const auto folder = output+"/"+id;
            if (!std::filesystem::create_directory(folder)) throw std::runtime_error("Refuse existing journey step directory");
            Write(folder+"/before-mutation.state.json", Snapshot(game));
            if (!SafeCache(sender, retained)) { Write(folder+"/unsafe-cache.json", UnsafeCacheAddresses(sender)); throw std::runtime_error("Unknown cache pointer before mutation"); }
            Write(folder+"/before-mutation.weapons.json", Weapons(sender));
            mutate();
            Write(folder+"/initialized.state.json", Snapshot(game));
            if (!SafeCache(sender, retained)) { Write(folder+"/unsafe-cache.json", UnsafeCacheAddresses(sender)); throw std::runtime_error("Unknown cache pointer after mutation; queries refused"); }
            Write(folder+"/initialized.weapons.json", Weapons(sender));
            std::vector<std::string> observations;
            unsigned call = 0;
            const auto evaluate = [&](const char* expression, int repetition) {
                if (!SafeCache(sender, retained)) throw std::runtime_error("Unsafe cache; query refused");
                ++call; const auto stem = "call-"+NumberJSON(call);
                const auto before = Snapshot(game), cacheBefore = Weapons(sender);
                Write(folder+"/"+stem+"-before.state.json", before); Write(folder+"/"+stem+"-before.weapons.json", cacheBefore);
                const int value = GameScript::EvaluateString(sender, expression);
                if (!SafeCache(sender, retained)) throw std::runtime_error("Query produced unsafe cache pointer");
                const auto after = Snapshot(game), cacheAfter = Weapons(sender);
                Write(folder+"/"+stem+"-after.state.json", after); Write(folder+"/"+stem+"-after.weapons.json", cacheAfter);
                observations.push_back(O({{"call",NumberJSON(call)}, {"expression",Q(expression)}, {"repetition",NumberJSON(repetition)}, {"value",NumberJSON(value)},
                    {"before",Q(stem+"-before.state.json")}, {"after",Q(stem+"-after.state.json")},
                    {"weapons_before",Q(stem+"-before.weapons.json")}, {"weapons_after",Q(stem+"-after.weapons.json")},
                    {"native_equal",before == after ? "true" : "false"}, {"weapons_equal",cacheBefore == cacheAfter ? "true" : "false"}}));
                return value;
            };
            const int trueValue = evaluate("True()", 0), falseValue = evaluate("False()", 0);
            if (trueValue != 1 || falseValue != 0) throw std::runtime_error("Evaluator controls failed");
            for (int repetition = 1; repetition <= repeats; ++repetition)
                for (const auto* query : Queries) evaluate(query, repetition);
            Write(folder+"/final.state.json", Snapshot(game)); Write(folder+"/final.weapons.json", Weapons(sender));
            const auto step = O({{"id",Q(id)}, {"route",Q(route)}, {"expected_off",expectedOff ? Q(expectedOff) : "null"},
                {"observations",A(observations)}, {"completed","true"}});
            Write(folder+"/step.json", step); steps.push_back(step);
        };
        observe("00-initial", "none", "sw1h01", [](){});
        observe("01-remove", "UnEquipItem+RemoveItem", nullptr, removeOff);
        observe("02-restore", "CreateItemCore+AddSlotItem", "sw1h01", [&](){ ordinary("sw1h01"); });
        observe("03-shield", "ordinary remove+AddSlotItem shield", "shld01", [&](){ ordinary("shld01"); });
        observe("04-create-normal", "GemRB_CreateItem explicit-slot calls", "sw1h01", [&](){ createItemAPI("sw1h01"); });
        observe("05-create-plus", "GemRB_CreateItem same-animation explicit-slot calls", "sw1h02", [&](){ createItemAPI("sw1h02"); });
        observe("06-reset-normal", "ordinary remove+AddSlotItem", "sw1h01", [&](){ ordinary("sw1h01"); });
        observe("07-transform-plus", "GameScript::TransformItem actual dispatch", "sw1h02", [&](){
            auto action = GenerateAction("TransformItem(\"sw1h01\",\"sw1h02\")");
            if (!action) {
                Write(output+"/07-transform-plus/transform-action.json", O({{"parsed","false"}}));
                throw std::runtime_error("TransformItem action parse failed");
            }
            std::unique_ptr<Targets> targets(GetAllObjects(game->GetCurrentArea(), sender, action, 0));
            const Scriptable* resolved = targets && targets->Count() ? targets->GetTarget(0, ST_ANY) : nullptr;
            const bool hasObjects = action->objects[0] || action->objects[1] || action->objects[2];
            Write(output+"/07-transform-plus/transform-action.json", O({{"parsed","true"},
                {"expression",Q("TransformItem(\"sw1h01\",\"sw1h02\")")}, {"action_id",NumberJSON(action->actionID)},
                {"flags",NumberJSON(action->flags)}, {"has_objects",hasObjects ? "true" : "false"},
                {"old_item",Q(action->resref0Parameter.c_str())}, {"new_item",Q(action->resref1Parameter.c_str())},
                {"target_count",NumberJSON(targets ? targets->Count() : 0)},
                {"resolved_runtime_id",resolved ? NumberJSON(resolved->GetGlobalID()) : "null"},
                {"resolution",Q("No-object action: GetAllActors puts sender first; handler selects first ST_ANY target")}}));
            // Shipped ACTION.IDS has only two strings, no object parameter.
            // Matching.cpp returns all actors, sender first, for this case;
            // TransformItem's handler chooses the first target, not a singleton.
            if (action->actionID != 356 || hasObjects || action->flags & ACF_MISSING_OBJECT
                || action->resref0Parameter != ResRef("sw1h01") || action->resref1Parameter != ResRef("sw1h02")
                || !targets || targets->Count() < 1 || resolved != sender)
                throw std::runtime_error("TransformItem action parse/target failed");
            GameScript::TransformItem(sender, std::move(action));
        });
        observe("08-reset-plus", "ordinary remove+AddSlotItem", "sw1h02", [&](){ ordinary("sw1h02"); });
        observe("09-create-normal", "GemRB_CreateItem same-animation reverse explicit-slot calls", "sw1h01", [&](){ createItemAPI("sw1h01"); });
        completed = true;
    } catch (const std::exception& error) { failure = error.what(); }
    Write(output+"/journey.json", O({{"schema",Q("bg-redux-phase1-inventory-journey-native/1")},
        {"case_id",Q(args["--case-id"])}, {"repeats",NumberJSON(repeats)}, {"completed",completed ? "true" : "false"},
        {"sender_runtime_id",NumberJSON(senderID)}, {"target_runtime_id",NumberJSON(targetID)},
        {"parsed_queries",A(parsed)}, {"steps",A(steps)}, {"error",Q(failure)},
        {"safety",Q("Item resources retained across mutations; cached item/header pointers matched retained resources before dereference/query. Unknown pointers abort. No repair or recache by observer.")}}));
    for (const auto& resource : retained) gamedata->FreeItem(resource.second, resource.first, false);
    if (engine) { core->SetGame(nullptr); VideoDriver.reset(); engine.reset(); core = nullptr; PluginMgr::Get()->RunCleanup(); }
    StopLog(); return completed ? 0 : 1;
}
