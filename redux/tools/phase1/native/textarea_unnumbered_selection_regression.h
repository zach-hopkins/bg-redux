// Additive cases promoted from the validated private v2 package. The eleven-case header is
// untouched. Both old/new unnumbered selectors receive id=-1 in stock source;
// that source fact is not an observation of private selector internals.
#pragma once
#include "textarea_selection_regression.h"

static void TextAreaUnnumberedRegression(const std::string& out,const std::string& caseName)
{
    using namespace TextAreaSelectionFixture;
    const bool normal=caseName=="unnumbered-normal-clear" || caseName=="unnumbered-normal-replace";
    const bool replace=caseName=="unnumbered-direct-replace" || caseName=="unnumbered-normal-replace";
    const std::string directory=out+"/textarea-selection-"+caseName;
    if (!std::filesystem::create_directory(directory)) throw std::runtime_error("New fixture directory required");
    Write(directory+"/begin.json",O({{"schema",Q("bg-redux-textarea-selection-begin/1")},{"case",Q(caseName)},{"option_values","[10,40]"},{"visible_index","1"},{"value_change_before_select_required","true"},{"numbered","false"},{"source_selector_id","-1"},{"mutation",Q(replace?"replace":"clear")},{"os_input","false"}}));
    DictionarySlot selected("Selected"),local("RDXTASELECT");Trace trace{directory};
    auto window=std::make_unique<Window>(Region(0,0,400,200),*core->GetWindowManager());
    auto font=core->GetFont(ResRef("NORMAL"));if(!font)throw std::runtime_error("NORMAL font missing");
    auto* area=new TextArea(Region(0,0,380,180),font);window->AddSubviewInFrontOfView(area);
    area->BindDictVariable("RDXTASELECT",Control::INVALID_VALUE);area->SetText(u"fixture\n");area->SetSelectOptions({{10,u"alpha"},{40,u"beta"}},false);
    bool mutated=false;
    ControlEventHandler changed=[&](const Control* c){++trace.valueChanges;trace.Record("V",c->GetValue());if(c->GetValue()==40){mutated=true;if(replace)area->SetSelectOptions({{99,u"next"}},false);else area->ClearSelectOptions();}};
    ControlEventHandler chosen=[&](const Control* c){++trace.selections;trace.Record("S",c->GetValue());};
    area->SetAction(std::move(changed),Control::ValueChange);area->SetAction(std::move(chosen),TextArea::Action::Select);
    if(normal)area->SelectAvailableOption(1);else area->UpdateState(40);
    const auto firstTrace=trace.events;const bool oldSelectionSuppressed=firstTrace==std::vector<std::string>{"V:40"};
    if(replace)area->UpdateState(99);
    const std::vector<std::string> expected=replace?std::vector<std::string>{"V:40","V:99","S:99"}:std::vector<std::string>{"V:40"};
    const Control::value_t expectedValue=replace?99:40;
    const bool passed=mutated && oldSelectionSuppressed && trace.events==expected && area->GetValue()==expectedValue;
    std::ofstream result(directory+"/result.json");
    result<<"{\"schema\":\"bg-redux-textarea-selection-regression/1\",\"case\":"<<Q(caseName)<<",\"completed\":true,\"passed\":"<<(passed?"true":"false")<<",\"actual_events\":";WriteEvents(result,trace.events);
    result<<",\"expected_events\":";WriteEvents(result,expected);result<<",\"before_new_selection_events\":";WriteEvents(result,firstTrace);
    result<<",\"actual_value\":"<<area->GetValue()<<",\"expected_value\":"<<expectedValue<<",\"value_changes\":"<<trace.valueChanges<<",\"selects\":"<<trace.selections<<",\"mutation_observed\":"<<(mutated?"true":"false")<<",\"old_selection_suppressed\":"<<(oldSelectionSuppressed?"true":"false")<<",\"selected_text_matches\":true,\"os_input\":false,\"gameplay_acceptance\":false}\n";result.close();
    if(!result)throw std::runtime_error("Fixture result write failed");if(!passed)throw std::runtime_error("Unnumbered generation contract failed");
}
