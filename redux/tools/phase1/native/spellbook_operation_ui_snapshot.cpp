// External normal-loop menu observer. Reuse the established host's serializers,
// fonts and destruction order; do not alter or replace an application screen.
#include "spellbook_gui_helpers.cpp"
#include "GUI/Button.h"

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
            const auto screen = view->ConvertPointToScreen(Point(0,0));
            rows.push_back(O({{"pack", Q(pack)}, {"id", NumberJSON(ctrl ? ctrl->ControlID : ref->Id)},
                {"window", wr ? NumberJSON(wr->Id) : "null"}, {"type", ctrl ? NumberJSON(ctrl->ControlType) : "null"},
                {"rect", A({NumberJSON(r.x),NumberJSON(r.y),NumberJSON(r.w),NumberJSON(r.h)})},
                {"screen_rect", A({NumberJSON(screen.x),NumberJSON(screen.y),NumberJSON(r.w),NumberJSON(r.h)})},
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
