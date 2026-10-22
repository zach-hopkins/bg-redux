// External Phase 0 host for the pinned, unmodified GemRB shared library.
// No normal main loop, script stepping, arbitrary eval, or rendering is claimed.
#include "Interface.h"
#include "InterfaceConfig.h"
#include "GUI/GameControl.h"
#include "Game.h"
#include "Map.h"
#include "PluginMgr.h"
#include "SaveGameIterator.h"
#include "Scriptable/Actor.h"
#include "Logging/Logging.h"
#include "Logging/Loggers/Stdio.h"
#include "Strings/StringConversion.h"

#include <clocale>
#include <cstdlib>
#include <fstream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

using namespace GemRB;
using Fields = std::vector<std::pair<std::string, std::string>>;

static std::string Q(const std::string& text)
{
    std::string out = "\"";
    const char* hex = "0123456789abcdef";
    for (unsigned char c : text) {
        if (c == '"' || c == '\\') { out += '\\'; out += char(c); }
        else if (c < 32) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
        else out += char(c);
    }
    return out + '"';
}

static std::string O(const Fields& fields)
{
    std::string out = "{";
    for (const auto& field : fields) {
        if (out.size() > 1) out += ',';
        out += Q(field.first) + ':' + field.second;
    }
    return out + '}';
}

static std::string A(const std::vector<std::string>& rows)
{
    std::string out = "[";
    for (const auto& row : rows) { if (out.size() > 1) out += ','; out += row; }
    return out + ']';
}

template<typename T> static std::string NumberJSON(T value) { return std::to_string(value); }
static std::string PointJSON(const Point& p) { return A({NumberJSON(p.x), NumberJSON(p.y)}); }

static std::string Variables(const ieVarsMap& vars)
{
    std::map<std::string, ieDword> ordered;
    for (const auto& pair : vars) ordered[pair.first.c_str()] = pair.second;
    Fields fields;
    for (const auto& pair : ordered) fields.emplace_back(pair.first, NumberJSON(pair.second));
    return O(fields);
}

static std::string Effects(const EffectQueue& queue)
{
    std::vector<std::string> rows;
    auto iterator = queue.GetFirstEffect();
    while (const Effect* fx = queue.GetNextEffect(iterator)) {
        rows.push_back(O({{"opcode",NumberJSON(fx->Opcode)}, {"target",NumberJSON(fx->Target)}, {"power",NumberJSON(fx->Power)},
            {"parameters",A({NumberJSON(fx->Parameter1),NumberJSON(fx->Parameter2),NumberJSON(fx->Parameter3),NumberJSON(fx->Parameter4),NumberJSON(fx->Parameter5),NumberJSON(fx->Parameter6)})},
            {"timing",NumberJSON(fx->TimingMode)}, {"duration",NumberJSON(fx->Duration)}, {"resistance",NumberJSON(fx->Resistance)},
            {"probability",A({NumberJSON(fx->ProbabilityRangeMin),NumberJSON(fx->ProbabilityRangeMax)})},
            {"resources",A({Q(fx->Resource.c_str()),Q(fx->Resource2.c_str()),Q(fx->Resource3.c_str()),Q(fx->Resource4.c_str())})},
            {"source_ref",Q(fx->SourceRef.c_str())}, {"source_type",NumberJSON(fx->SourceType)}, {"source_flags",NumberJSON(fx->SourceFlags)},
            {"inventory_slot",NumberJSON(fx->InventorySlot)}, {"caster_level",NumberJSON(fx->CasterLevel)}, {"caster_id",NumberJSON(fx->CasterID)},
            {"save_type",NumberJSON(fx->SavingThrowType)}, {"save_bonus",NumberJSON(fx->SavingThrowBonus)},
            {"dice",A({NumberJSON(fx->DiceThrown),NumberJSON(fx->DiceSides)})}, {"first_apply",NumberJSON(fx->FirstApply)},
            {"projectile",NumberJSON(fx->Projectile)}, {"position",PointJSON(fx->Pos)}, {"source_position",PointJSON(fx->Source)},
            {"primary_type",NumberJSON(fx->PrimaryType)}, {"secondary_type",NumberJSON(fx->SecondaryType)},
            {"secondary_delay",NumberJSON(fx->SecondaryDelay)}, {"special",NumberJSON(fx->IsVariable)},
            {"save_for_half",NumberJSON(fx->IsSaveForHalfDamage)}, {"random_value",NumberJSON(fx->RandomValue)}}));
    }
    return A(rows);
}

static std::string InventoryJSON(const Inventory& inv)
{
    std::vector<std::string> rows;
    for (int slot = 0; slot < inv.GetSlotCount(); ++slot) {
        const CREItem* item = inv.GetSlotItem(slot);
        if (!item) continue;
        rows.push_back(O({{"slot",NumberJSON(slot)}, {"resref",Q(item->ItemResRef.c_str())},
            {"flags",NumberJSON(item->Flags)}, {"expired",NumberJSON(item->Expired)},
            {"usages",A({NumberJSON(item->Usages[0]),NumberJSON(item->Usages[1]),NumberJSON(item->Usages[2])})}}));
    }
    return O({{"slot_count",NumberJSON(inv.GetSlotCount())}, {"fist_slot",NumberJSON(Inventory::GetFistSlot())}, {"equipped",NumberJSON(inv.GetEquipped())},
        {"equipped_header",NumberJSON(inv.GetEquippedHeader())}, {"items",A(rows)}});
}

static std::string SpellbookJSON(Spellbook& book)
{
    std::vector<std::string> pages;
    for (int type = 0; type < book.GetTypes(); ++type) {
        for (unsigned level = 0; level < book.GetSpellLevelCount(type); ++level) {
            auto* page = book.GetSpellMemorization(type, level);
            if (!page) continue;
            std::vector<std::string> known, memorized;
            for (const auto& spell : page->knownSpells) known.push_back(O({{"resref",Q(spell->SpellResRef.c_str())},
                {"level",NumberJSON(spell->Level)}, {"type",NumberJSON(spell->Type)}}));
            for (const auto& spell : page->memorizedSpells) memorized.push_back(O({{"resref",Q(spell->SpellResRef.c_str())},
                {"flags",NumberJSON(spell->Flags)}}));
            pages.push_back(O({{"type",NumberJSON(type)}, {"level",NumberJSON(level)}, {"slots",NumberJSON(page->SlotCount)},
                {"slots_with_bonus",NumberJSON(page->SlotCountWithBonus)}, {"known",A(known)}, {"memorized",A(memorized)}}));
        }
    }
    return A(pages);
}

static std::string ActorJSON(Actor* actor)
{
    if (!actor) return "null";
    std::vector<std::string> base, modified;
    for (auto value : actor->BaseStats) base.push_back(NumberJSON(value));
    for (auto value : actor->Modified) modified.push_back(NumberJSON(value));
    return O({{"script_name",Q(actor->GetScriptName().c_str())}, {"name",Q(MBStringFromString(actor->GetName()))},
        {"runtime_id",NumberJSON(actor->GetGlobalID())}, {"in_party",NumberJSON(actor->InParty)}, {"area",Q(actor->AreaName.c_str())},
        {"position",PointJSON(actor->Pos)}, {"orientation",NumberJSON(actor->GetOrientation())},
        {"portraits",A({Q(actor->SmallPortrait.c_str()),Q(actor->LargePortrait.c_str())})},
        {"base_stats",A(base)}, {"modified_stats",A(modified)}, {"locals",Variables(actor->locals)},
        {"inventory",InventoryJSON(actor->inventory)}, {"spellbook",SpellbookJSON(actor->spellbook)},
        {"effects",Effects(actor->fxqueue)}});
}

static std::string Snapshot(Game* game)
{
    std::vector<std::string> party, npcs, mapActors, journal;
    for (int i = 0; i < game->GetPartySize(false); ++i) party.push_back(ActorJSON(game->GetPC(i, false)));
    for (int i = 0; i < game->GetNPCCount(); ++i) npcs.push_back(ActorJSON(game->GetNPC(i)));
    Map* map = game->GetCurrentArea();
    if (map) for (int i = 0; i < map->GetActorCount(true); ++i) mapActors.push_back(ActorJSON(map->GetActor(i, true)));
    for (unsigned i=0; i<game->GetJournalCount(); ++i) {
        const auto* entry = game->GetJournalEntry(i);
        journal.push_back(O({{"text_ref",NumberJSON(static_cast<ieDword>(entry->Text))},
            {"time",NumberJSON(entry->GameTime)}, {"chapter",NumberJSON(entry->Chapter)},
            {"section",NumberJSON(entry->Section)}, {"group",NumberJSON(entry->Group)}}));
    }
    return O({{"schema",Q("bg-redux-state/1")}, {"game_time",NumberJSON(game->GameTime.load())},
        {"gold",NumberJSON(game->PartyGold)}, {"reputation",NumberJSON(game->Reputation)}, {"current_area",Q(game->CurrentArea.c_str())},
        {"campaign",Q(game->CurrentCampaign.c_str())}, {"expansion",NumberJSON(game->Expansion)},
        {"globals",Variables(game->locals)}, {"journal_count",NumberJSON(game->GetJournalCount())}, {"journal",A(journal)},
        {"party",A(party)}, {"stored_npcs",A(npcs)}, {"current_area_actors",A(mapActors)},
        {"area_locals",map ? Variables(map->locals) : "null"},
        {"selection",NumberJSON(game->GetSelectedPCSingle())}});
}

static void ValidateEffects(Actor* actor)
{
    if (!actor) return;
    auto iterator = actor->fxqueue.GetFirstEffect();
    while (const auto* effect = actor->fxqueue.GetNextEffect(iterator)) {
        if (effect->Opcode >= Globals::MAX_EFFECTS) {
            throw std::runtime_error("Unsupported effect payload opcode=" + NumberJSON(effect->Opcode)
                + "; refusing area/effect initialization (no effects stripped)");
        }
    }
}

static void Write(const std::string& path, const std::string& json)
{
    std::ofstream file(path, std::ios::binary);
    if (!file) throw std::runtime_error("Cannot write probe artifact");
    file << json << '\n';
}

static void StopLog() { ToggleLogging(false, true); }

#ifndef REDUX_GUI_HOST
int main(int argc, char** argv)
{
    std::map<std::string,std::string> args;
    for (int i=1; i+1<argc; i+=2) args[argv[i]] = argv[i+1];
    if (!args.count("--config") || !args.count("--output") || !args.count("--save-id")) return 64;
    std::setlocale(LC_ALL, ".UTF8");
    std::atexit(StopLog);
    std::unique_ptr<Interface> engine;
    int rc = 0;
    try {
        const char* engineArgs[] = {"redux-save-probe", "-c", args["--config"].c_str()};
        auto config = LoadFromArgs(3, const_cast<char**>(engineArgs));
        ToggleLogging(true);
        AddLogWriter(createStdioLogWriter());
        // Current core filter is msg.level >= LL; FATAL retains every severity.
        SetMainLogLevel(FATAL);
        engine = std::make_unique<Interface>(std::move(config));
        // One game per process: let the core DLL initialize its own lazy opcode
        // registry. Calling inline Globals::Get from this host creates another
        // module-local singleton and can clash with the DLL's first use.
        SetTokenAsString("SaveDir", u"save");
        auto* iterator = core->GetSaveGameIterator().get();
        Holder<SaveGame> selected;
        if (args.count("--save-dir")) {
            // Load an explicit GAM/SAV fixture independently of UI preview filtering.
            selected = MakeHolder<SaveGame>(args["--save-dir"], "HarnessInput", core->GameNameResRef,
                "HarnessInput", 0, std::stoi(args["--save-id"]));
        } else {
            for (const auto& save : iterator->GetSaveGames()) {
                if (save->GetSaveID() == std::stoi(args["--save-id"])) { selected=save; break; }
            }
        }
        if (!selected) throw std::runtime_error("Required save fixture not found; no skip permitted");
        core->LoadGame(selected, GAMVersion::GemRB);
        Game* game = core->GetGame();
        if (!game || !game->GetPartySize(false)) throw std::runtime_error("No imported party");
        Write(args["--output"] + ".imported.json", Snapshot(game));
        for (int i=0; i<game->GetPartySize(false); ++i) ValidateEffects(game->GetPC(i,false));
        for (int i=0; i<game->GetNPCCount(); ++i) ValidateEffects(game->GetNPC(i));
        game->ConsolidateParty();
        auto* control = core->StartGameControl();
        const auto* actor = core->GetFirstSelectedPC(true);
        if (!control || !actor) throw std::runtime_error("Missing game control/selected living actor");
        control->ChangeMap(actor, true);
        for (int i=0; i<game->GetPartySize(false); ++i) {
            auto* pc = game->GetPC(i,false);
            if (pc->GetCurrentArea() != game->GetCurrentArea()) game->GetCurrentArea()->AddActor(pc,true);
        }
        if (args.count("--select")) {
            if (!game->SelectPCSingle(std::stoi(args["--select"]))) throw std::runtime_error("Selection refused");
        }
        Write(args["--output"], Snapshot(game));
        if (args.count("--resave")) {
            SetTokenAsString("SaveDir", u"save");
            core->config.SavePath = args["--resave"];
            // Use the ordinary, non-forced save API; retain all CanSave guards.
            const int result = iterator->CreateSaveGame(Holder<SaveGame>(), StringView("Redux Harness"), nullptr, false);
            Write(args["--output"] + ".save-result.json", O({{"return_code",NumberJSON(result)},
                {"forced", "false"}, {"post_save_state",Snapshot(game)}}));
            if (result != GEM_OK) throw std::runtime_error("Ordinary save refused or failed; see save-result");
        }
    } catch (const std::exception& error) {
        Write(args["--output"] + ".error.json", O({{"error",Q(error.what())}}));
        rc = 1;
    }
    if (engine) {
        core->SetGame(nullptr);
        VideoDriver.reset();
        engine.reset();
        core=nullptr;
        PluginMgr::Get()->RunCleanup();
    }
    StopLog();
    return rc;
}
#endif
