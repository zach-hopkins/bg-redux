// SPDX-License-Identifier: GPL-2.0-or-later
// External native regression fixture: one named case per owned process.
#pragma once
#include "Interface.h"
#include "GUI/Control.h"
#include "GUI/TextArea.h"
#include "GUI/Window.h"
#include "GUI/WindowManager.h"
#include "Strings/StringMap.h"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace TextAreaSelectionFixture {
using namespace GemRB;

struct DictionarySlot {
    std::string key;
    std::optional<Control::value_t> previous;
    explicit DictionarySlot(const char* name) : key(name)
    {
        if (const auto* value = core->GetDictionary().Get(StringView(key))) previous = *value;
    }
    ~DictionarySlot()
    {
        if (previous) core->GetDictionary().Set(StringView(key), *previous);
        else core->GetDictionary().Erase(StringView(key));
    }
};

struct Trace {
    std::string directory;
    std::vector<std::string> events;
    unsigned valueChanges = 0, selections = 0;
    void Record(const char* kind, Control::value_t value)
    {
        events.push_back(std::string(kind) + ":" + std::to_string(value));
        std::ofstream stream(directory + "/events.jsonl", std::ios::app);
        stream << "{\"sequence\":" << events.size() << ",\"kind\":\"" << kind << "\",\"value\":" << value << "}\n";
        stream.flush();
        if (!stream) throw std::runtime_error("Cannot retain selection callback trace");
    }
};

static void WriteEvents(std::ostream& stream, const std::vector<std::string>& values)
{
    stream << '[';
    for (size_t i = 0; i < values.size(); ++i) { if (i) stream << ','; stream << '"' << values[i] << '"'; }
    stream << ']';
}
}

static void TextAreaSelectionRegression(const std::string& out, const std::string& caseName)
{
    using namespace TextAreaSelectionFixture;
    const std::vector<std::string> allowed = {"direct-replace", "direct-remove", "normal-replace", "already-selected",
        "new-context", "invalid-visible-index", "invalid-value-clear", "value-clear", "value-replace", "select-reentry", "invalid-unselected"};
    if (std::find(allowed.begin(), allowed.end(), caseName) == allowed.end()) throw std::runtime_error("Unknown TextArea fixture case");
    if (!core || !core->GetGame() || !core->GetWindowManager()) throw std::runtime_error("Normal loaded engine required");
    const std::string directory = out + "/textarea-selection-" + caseName;
    if (!std::filesystem::create_directory(directory)) throw std::runtime_error("Selection fixture output must be new");
    std::ofstream begin(directory + "/begin.json");
    begin << "{\"schema\":\"bg-redux-textarea-selection-begin/1\",\"case\":\"" << caseName
        << "\",\"option_values\":[10,40],\"visible_index\":1,\"value_change_before_select_required\":true,"
        "\"scope\":\"unmanaged-native-control\",\"os_input\":false}\n";
    begin.close();
    if (!begin) throw std::runtime_error("Cannot retain selection fixture entry receipt");
    // TextArea's constructor binds Selected. Preserve that exact key as well
    // as our private dictionary-redraw key, including prior absence.
    DictionarySlot selected("Selected"), local("RDXTASELECT");
    Trace trace{directory};
    auto window = std::make_unique<Window>(Region(0, 0, 400, 200), *core->GetWindowManager());
    auto font = core->GetFont(ResRef("NORMAL"));
    if (!font) throw std::runtime_error("Existing NORMAL font unavailable");
    auto* area = new TextArea(Region(0, 0, 380, 180), font);
    window->AddSubviewInFrontOfView(area);
    area->BindDictVariable("RDXTASELECT", Control::INVALID_VALUE);
    area->SetText(u"fixture\n");
    const std::vector<SelectOption> initial = {{10, u"alpha"}, {40, u"beta"}};
    area->SetSelectOptions(initial, true);
    ControlEventHandler changed = [&](const Control* c) {
        ++trace.valueChanges;
        trace.Record("V", c->GetValue());
        if ((caseName == "value-clear" && c->GetValue() == 40) ||
            (caseName == "invalid-value-clear" && c->GetValue() == Control::INVALID_VALUE)) area->ClearSelectOptions();
        if (caseName == "value-replace" && c->GetValue() == 40) area->SetSelectOptions({{99, u"next"}}, true);
    };
    ControlEventHandler chosen = [&](const Control* c) {
        ++trace.selections;
        trace.Record("S", c->GetValue());
        if (trace.selections == 1 && (caseName == "direct-replace" || caseName == "normal-replace")) area->SetSelectOptions({{99, u"next"}}, true);
        if (trace.selections == 1 && caseName == "direct-remove") area->ClearSelectOptions();
        if (caseName == "select-reentry") area->UpdateState(c->GetValue());
    };
    area->SetAction(std::move(changed), Control::ValueChange);
    area->SetAction(std::move(chosen), TextArea::Action::Select);
    std::vector<std::string> expected = {"V:40", "S:40"};
    Control::value_t expectedValue = 40;
    bool selectedTextRequired = false;
    if (caseName == "invalid-unselected") {
        area->UpdateState(999);
        area->SelectAvailableOption(999);
        expected.clear(); expectedValue = Control::INVALID_VALUE;
    } else if (caseName == "normal-replace") {
        area->SelectAvailableOption(1);
    } else if (caseName == "invalid-visible-index" || caseName == "invalid-value-clear") {
        area->SelectAvailableOption(1);
        if (caseName == "invalid-visible-index") area->SelectAvailableOption(999);
        else area->UpdateState(999);
        expected.push_back("V:4294967295"); expectedValue = Control::INVALID_VALUE;
    } else {
        // This direct public entry is intentional: the prior native assertion
        // must be fixed rather than avoided by substituting the normal route.
        area->UpdateState(40);
        if (caseName == "already-selected") { area->UpdateState(40); area->SelectAvailableOption(1); selectedTextRequired = true; }
        if (caseName == "new-context") { area->SetSelectOptions(initial, true); area->UpdateState(40); expected.push_back("S:40"); }
        if (caseName == "value-clear") expected = {"V:40"};
        if (caseName == "value-replace") {
            area->UpdateState(99); expected = {"V:40", "V:99", "S:99"}; expectedValue = 99;
        }
    }
    const bool valueMatches = area->GetValue() == expectedValue;
    const bool textMatches = !selectedTextRequired || area->QueryText() == u"2. - beta";
    const bool passed = trace.events == expected && valueMatches && textMatches;
    std::ofstream result(directory + "/result.json");
    result << "{\"schema\":\"bg-redux-textarea-selection-regression/1\",\"case\":\"" << caseName
        << "\",\"completed\":true,\"passed\":" << (passed ? "true" : "false")
        << ",\"actual_events\":"; WriteEvents(result, trace.events);
    result << ",\"expected_events\":"; WriteEvents(result, expected);
    result << ",\"value_changes\":" << trace.valueChanges << ",\"selects\":" << trace.selections
        << ",\"actual_value\":" << area->GetValue() << ",\"expected_value\":" << expectedValue
        << ",\"selected_text_matches\":" << (textMatches ? "true" : "false")
        << ",\"dictionary_restore_guard_installed\":true,\"os_input\":false,\"gameplay_acceptance\":false}\n";
    result.close();
    if (!result) throw std::runtime_error("Cannot retain selection fixture result");
    if (!passed) throw std::runtime_error("TextArea selection trace/value contract failed");
}
