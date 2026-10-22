// Separate versioned active main/ammo/launcher mutation journey.
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

static std::string ExpandedWeapons(const Actor* actor)
{
    std::vector<std::string> derived;
    for (unsigned hand=0;hand<2;++hand) {
        const auto& wi=actor->weaponInfo[hand];
        derived.push_back(O({{"hand",NumberJSON(hand+1)}, {"range",NumberJSON(wi.range)},
            {"itemtype",NumberJSON(wi.itemtype)}, {"proficiency",NumberJSON(wi.prof)},
            {"selected_header_range",wi.extHeader ? NumberJSON(wi.extHeader->Range):"null"},
            {"selected_header_thac0_bonus",wi.extHeader ? NumberJSON(wi.extHeader->THAC0Bonus):"null"},
            {"launcher_damage_bonus",NumberJSON(wi.launcherDmgBonus)},
            {"launcher_thac0_bonus",NumberJSON(wi.launcherTHAC0Bonus)}}));
    }
    auto original=Weapons(actor); original.pop_back();
    return original+",\"derived_hands\":"+A(derived)+"}";
}

static std::string ResourceMetadata(const RetainedItems& retained)
{
    std::vector<std::string> resources;
    for (const auto& entry : retained) {
        const auto* item=entry.second; const auto* header=item->GetExtHeader(0);
        if (!header) throw std::runtime_error("Expected retained resource header0 missing");
        resources.push_back(O({{"resref",Q(entry.first.c_str())}, {"flags",NumberJSON(item->Flags)},
            {"enchantment",NumberJSON(item->Enchantment)}, {"itemtype",NumberJSON(item->ItemType)},
            {"proficiency",NumberJSON(item->WeaProf)}, {"header_index","0"},
            {"attack_type",NumberJSON(header->AttackType)}, {"damage_type",NumberJSON(header->DamageType)},
            {"location",NumberJSON(header->Location)}, {"range",NumberJSON(header->Range)},
            {"dice_sides",NumberJSON(header->DiceSides)}, {"dice_thrown",NumberJSON(header->DiceThrown)},
            {"damage_bonus",NumberJSON(header->DamageBonus)}, {"thac0_bonus",NumberJSON(header->THAC0Bonus)},
            {"charges",NumberJSON(header->Charges)}, {"recharge_flags",NumberJSON(header->RechargeFlags)}}));
    }
    return A(resources);
}

int main(int argc, char** argv)
{
    std::map<std::string, std::string> args;
    for (int i = 1; i+1 < argc; i += 2) {
        if (args.count(argv[i])) return 64;
        args[argv[i]] = argv[i+1];
    }
    const std::vector<std::string> required = {"--config", "--output", "--save-dir", "--case-id", "--repeats", "--scenario", "--nonce"};
    if (argc % 2 != 1 || args.size() != required.size()) return 64;
    for (const auto& key : required) if (!args.count(key)) return 64;
    const auto output = args["--output"];
    const bool ranged=args["--scenario"]=="ranged";
    if ((!ranged && args["--scenario"]!="main") || args["--nonce"].size()!=32
        || args["--nonce"].find_first_not_of("0123456789abcdef")!=std::string::npos
        || args["--case-id"]!=(ranged ? "ammo-plus-pfmw":"02-plus-normal-pfmw")) return 64;
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
        const auto* ammo=inventory.GetSlotItem(11);
        if (offSlot!=9 || inventory.GetEquippedHeader()!=0 || !main
            || (!ranged && (inventory.GetEquipped()!=0 || main->ItemResRef!=ResRef("sw1h02") || !off || off->ItemResRef!=ResRef("sw1h01")))
            || (ranged && (inventory.GetEquipped()!=-24 || main->ItemResRef!=ResRef("bow01") || off
                           || !ammo || ammo->ItemResRef!=ResRef("arow02") || ammo->Usages[0]!=40)))
            throw std::runtime_error("Exact prepared main/ranged equipment selection required");
        for (const char* ref : {"sw1h01", "sw1h02", "bow01", "bow02", "arow01", "arow02"}) {
            const Item* item = gamedata->GetItem(ResRef(ref), true);
            if (!item) throw std::runtime_error("Required retained item missing");
            retained.emplace_back(ResRef(ref), item);
        }
        for (unsigned pair=0;pair<6;pair+=2)
            if (retained[pair].second->Enchantment!=0 || retained[pair+1].second->Enchantment!=1)
                throw std::runtime_error("Stock normal/plus resource control missing");
        Write(output+"/resources.json",ResourceMetadata(retained));
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
        const auto ordinary = [&](int slot, const char* ref, int count) {
            if (!inventory.UnEquipItem(slot, false)) throw std::runtime_error("Ordinary unequip refused");
            std::unique_ptr<CREItem> removed(inventory.RemoveItem(slot,0));
            if (!removed || inventory.GetSlotItem(slot)) throw std::runtime_error("Ordinary removal failed");
            auto item = std::make_unique<CREItem>();
            if (!CreateItemCore(item.get(), ResRef(ref), count, 0, 0)) throw std::runtime_error("Ordinary item creation failed");
            if (inventory.AddSlotItem(item.get(), slot) != ASI_SUCCESS) throw std::runtime_error("Ordinary active-slot add refused");
            item.release(); inventory.EquipItem(slot); sender->ReinitQuickSlots();
        };
        const auto createItemAPI = [&](int slot, const char* ref, int count) {
            // Exact mutation calls used by GemRB_CreateItem's explicit-slot path.
            inventory.SetSlotItemRes(ResRef(ref), slot, count, 0, 0);
            inventory.EquipItem(slot); sender->ReinitQuickSlots();
        };
        const auto transform = [&](const std::string& folder, const char* oldRef, const char* newRef, int expectedSlot) {
            const auto expression="TransformItem(\""+std::string(oldRef)+"\",\""+newRef+"\")";
            auto action=GenerateAction(expression.c_str());
            if (!action) throw std::runtime_error("TransformItem parse failed");
            std::unique_ptr<Targets> targets(GetAllObjects(game->GetCurrentArea(),sender,action,0));
            const auto* resolved=targets && targets->Count() ? targets->GetTarget(0,ST_ANY):nullptr;
            const bool hasObjects=action->objects[0] || action->objects[1] || action->objects[2];
            int matches=0,matchedSlot=-1;
            for (unsigned slot=0;slot<inventory.GetSlotCount();++slot) {
                const auto* item=inventory.GetSlotItem(slot);
                if (item && item->ItemResRef==ResRef(oldRef)) { ++matches;matchedSlot=slot; }
            }
            Write(folder+"/transform-action.json",O({{"parsed","true"},{"expression",Q(expression)},
                {"action_id",NumberJSON(action->actionID)},{"flags",NumberJSON(action->flags)},
                {"has_objects",hasObjects ? "true":"false"},{"old_item",Q(action->resref0Parameter.c_str())},
                {"new_item",Q(action->resref1Parameter.c_str())},{"matching_inventory_items",NumberJSON(matches)},
                {"matching_slot",NumberJSON(matchedSlot)},{"target_count",NumberJSON(targets ? targets->Count():0)},
                {"resolved_runtime_id",resolved ? NumberJSON(resolved->GetGlobalID()):"null"},
                {"charges",A({NumberJSON(action->int0Parameter),NumberJSON(action->int1Parameter),NumberJSON(action->int2Parameter)})}}));
            if (action->actionID!=356 || hasObjects || action->flags&ACF_MISSING_OBJECT || resolved!=sender
                || !targets || targets->Count()<1 || matches!=1 || matchedSlot!=expectedSlot
                || action->resref0Parameter!=ResRef(oldRef) || action->resref1Parameter!=ResRef(newRef)
                || action->int0Parameter || action->int1Parameter || action->int2Parameter)
                throw std::runtime_error("Actual TransformItem implicit sender/unique physical slot differs");
            GameScript::TransformItem(sender,std::move(action));
        };
        const auto observe = [&](const char* id, const char* route, const char* expectedMain,
                                 const char* expectedAmmo, const std::function<void(const std::string&)>& mutate) {
            const auto folder=output+"/"+id, queries=folder+"/queries";
            if (!std::filesystem::create_directory(folder) || !std::filesystem::create_directory(queries))
                throw std::runtime_error("Refuse existing step directory");
            const auto safe=[&]() {
                if (!SafeCache(sender,retained)) {
                    Write(folder+"/unsafe-cache.json",UnsafeCacheAddresses(sender));
                    throw std::runtime_error("Unknown cache pointer; dereference/query refused");
                }
            };
            safe(); Write(folder+"/before-mutation.state.json",Snapshot(game));
            Write(folder+"/before-mutation.weapons.json",ExpandedWeapons(sender));
            Write(folder+"/before-mutation.rng.json",QueryRNGState());
            mutate(folder); safe();
            Write(queries+"/initialized.state.json",Snapshot(game));
            Write(queries+"/initialized.weapons.json",ExpandedWeapons(sender));
            Write(queries+"/initialized.rng.json",QueryRNGState());
            std::vector<std::string> observations;
            unsigned call=0;
            const auto evaluate=[&](const char* expression,int repetition) {
                safe(); ++call;const auto stem="call-"+NumberJSON(call);
                const auto before=Snapshot(game), cacheBefore=ExpandedWeapons(sender), rngBefore=QueryRNGState();
                Write(queries+"/"+stem+"-before.state.json",before);
                Write(queries+"/"+stem+"-before.weapons.json",cacheBefore);
                Write(queries+"/"+stem+"-before.rng.json",rngBefore);
                const int value=GameScript::EvaluateString(sender,expression);safe();
                const auto after=Snapshot(game), cacheAfter=ExpandedWeapons(sender), rngAfter=QueryRNGState();
                Write(queries+"/"+stem+"-after.state.json",after);
                Write(queries+"/"+stem+"-after.weapons.json",cacheAfter);
                Write(queries+"/"+stem+"-after.rng.json",rngAfter);
                observations.push_back(O({{"call",NumberJSON(call)},{"expression",Q(expression)},
                    {"repetition",NumberJSON(repetition)},{"value",NumberJSON(value)},
                    {"before",Q(stem+"-before.state.json")},{"after",Q(stem+"-after.state.json")},
                    {"weapons_before",Q(stem+"-before.weapons.json")},{"weapons_after",Q(stem+"-after.weapons.json")},
                    {"rng_before",Q(stem+"-before.rng.json")},{"rng_after",Q(stem+"-after.rng.json")},
                    {"native_equal",before==after ? "true":"false"},{"weapons_equal",cacheBefore==cacheAfter ? "true":"false"},
                    {"rng_equal",RNGEqual(rngBefore,rngAfter)}}));
                return value;
            };
            if (evaluate("True()",0)!=1 || evaluate("False()",0)!=0) throw std::runtime_error("Evaluator controls failed");
            for (int repetition=1;repetition<=repeats;++repetition) for (const auto* query:Queries) evaluate(query,repetition);
            safe();Write(queries+"/final.state.json",Snapshot(game));Write(queries+"/final.weapons.json",ExpandedWeapons(sender));
            Write(queries+"/final.rng.json",QueryRNGState());
            const auto queryCase=args["--case-id"]+":"+id;
            Write(queries+"/query-result.json",O({{"schema",Q("bg-redux-phase1-weapon-query-native/1")},
                {"case_id",Q(queryCase)},{"repeats",NumberJSON(repeats)},{"completed","true"},{"error",Q("")},
                {"sender_runtime_id",NumberJSON(senderID)},{"target_runtime_id",NumberJSON(targetID)},
                {"parsed_queries",A(parsed)},{"observations",A(observations)},{"rng_control_draw_call","null"}}));
            const auto step=O({{"id",Q(id)},{"route",Q(route)},{"expected_main",Q(expectedMain)},
                {"expected_ammo",expectedAmmo ? Q(expectedAmmo):"null"},{"completed","true"}});
            Write(folder+"/step.json",step);steps.push_back(step);
        };
        if (!ranged) {
            observe("00-initial","none","sw1h02",nullptr,[](const auto&){});
            observe("01-create-main-normal","CreateItem explicit-slot","sw1h01",nullptr,[&](const auto&){createItemAPI(35,"sw1h01",0);});
            observe("02-ordinary-main-plus","ordinary remove/add/select","sw1h02",nullptr,[&](const auto&){ordinary(35,"sw1h02",0);});
            observe("03-transform-main-normal","parsed TransformItem","sw1h01",nullptr,[&](const auto& f){transform(f,"sw1h02","sw1h01",35);});
            observe("04-create-main-plus","CreateItem explicit-slot","sw1h02",nullptr,[&](const auto&){createItemAPI(35,"sw1h02",0);});
        } else {
            observe("00-initial","none","bow01","arow02",[](const auto&){});
            observe("01-create-ammo-normal","CreateItem explicit-slot","bow01","arow01",[&](const auto&){createItemAPI(11,"arow01",40);});
            observe("02-transform-launcher-plus","parsed TransformItem","bow02","arow01",[&](const auto& f){transform(f,"bow01","bow02",35);});
            observe("03-ordinary-ammo-plus","ordinary remove/add/select","bow02","arow02",[&](const auto&){ordinary(11,"arow02",40);});
            observe("04-transform-launcher-normal","parsed TransformItem","bow01","arow02",[&](const auto& f){transform(f,"bow02","bow01",35);});
            observe("05-create-ammo-normal","CreateItem explicit-slot","bow01","arow01",[&](const auto&){createItemAPI(11,"arow01",40);});
            observe("06-create-launcher-plus","CreateItem explicit-slot","bow02","arow01",[&](const auto&){createItemAPI(35,"bow02",0);});
            observe("07-ordinary-launcher-normal","ordinary remove/add/select","bow01","arow01",[&](const auto&){ordinary(35,"bow01",0);});
            observe("08-create-ammo-plus","CreateItem explicit-slot","bow01","arow02",[&](const auto&){createItemAPI(11,"arow02",40);});
        }
        completed = true;
    } catch (const std::exception& error) { failure = error.what(); }
    Write(output+"/journey.json", O({{"schema",Q("bg-redux-phase1-active-slot-journey-native/1")},
        {"scenario",Q(args["--scenario"])}, {"nonce",Q(args["--nonce"])},
        {"case_id",Q(args["--case-id"])}, {"repeats",NumberJSON(repeats)}, {"completed",completed ? "true" : "false"},
        {"sender_runtime_id",NumberJSON(senderID)}, {"target_runtime_id",NumberJSON(targetID)},
        {"parsed_queries",A(parsed)}, {"steps",A(steps)}, {"error",Q(failure)},
        {"safety",Q("Item resources retained across mutations; cached item/header pointers matched retained resources before dereference/query. Unknown pointers abort. No repair or recache by observer.")}}));
    if (engine) core->SetGame(nullptr); // Keep retained resources alive through actor destruction.
    for (const auto& resource : retained) gamedata->FreeItem(resource.second, resource.first, false);
    if (engine) { VideoDriver.reset(); engine.reset(); core = nullptr; PluginMgr::Get()->RunCleanup(); }
    StopLog(); return completed ? 0 : 1;
}
