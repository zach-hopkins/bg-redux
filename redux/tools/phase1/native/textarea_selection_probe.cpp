// External synthetic control fixture after ordinary stock load. Unused helper
// main is renamed in generated gui_helpers.cpp, never with a preprocessor macro.
#include "gui_helpers.cpp"
#include "textarea_unnumbered_selection_regression.h"
#include <algorithm>

static std::string FullDictionary()
{
    Fields values;
    for (const auto& row : core->GetDictionary()) {
        const StringView key = row.first;
        values.emplace_back(key.MakeString(), NumberJSON(row.second));
    }
    std::sort(values.begin(), values.end());
    return O(values);
}

int main(int argc, char** argv)
{
    std::map<std::string,std::string> args;
    if (argc != 11) return 64;
    for (int i=1; i+1<argc; i+=2) if (!args.emplace(argv[i],argv[i+1]).second) return 64;
    for (const auto* key : {"--config","--output","--scripts","--case","--nonce"}) if (!args.count(key)) return 64;
    const std::set<std::string> allowed={"direct-replace","direct-remove","normal-replace","already-selected","new-context","invalid-visible-index","invalid-value-clear","value-clear","value-replace","select-reentry","invalid-unselected","unnumbered-direct-clear","unnumbered-direct-replace","unnumbered-normal-clear","unnumbered-normal-replace"};
    if (!allowed.count(args["--case"]) || args["--nonce"].size()!=32 ||
        args["--nonce"].find_first_not_of("0123456789abcdef")!=std::string::npos) return 64;
    const std::string out=args["--output"];
    std::setlocale(LC_ALL,".UTF8"); std::atexit(StopLog);
    std::unique_ptr<Interface> engine;
    int rc=1,ticks=0,phase=-1,calls=0;bool completed=false,worldSame=false,dictionarySame=false;
    std::string error;
    try {
        const char* engineArgs[]={"redux-textarea-selection","-c",args["--config"].c_str()};
        auto config=LoadFromArgs(3,const_cast<char**>(engineArgs));
        ToggleLogging(true);AddLogWriter(createStdioLogWriter());SetMainLogLevel(FATAL);
        engine=std::make_unique<Interface>(std::move(config));
        auto script=core->GetGUIScriptEngine();
        if (!script->ExecString("import sys; sys.path.insert(0,"+Q(args["--scripts"])+")")) throw std::runtime_error("External startup path failed");
        core->SetNextScript("ReduxStart");
        core->SetTimer([&](){try {
            if (++ticks>120) throw std::runtime_error("Normal load readiness exceeded 120 samples");
            if (phase==-1) {
                if (!script->ExecString("import ReduxStart; ReduxStart.PopulateLoad()")) throw std::runtime_error("Stock load population failed");
                Press("GUILOAD",0,26);phase=0;return;
            }
            if (!core->GetGame() || !core->GetGameControl() || !GetViews(ScriptingGroup_t("LOADWIN")).empty()) return;
            if (phase!=0 || calls) throw std::runtime_error("Duplicate fixture dispatch");
            if (!script->ExecString("ReduxStart.Ready()")) throw std::runtime_error("Paused loaded readiness failed");
            auto* game=core->GetGame();
            if (game->GetPartySize(false)!=2 || !game->GetCurrentArea() || game->GetCurrentArea()->GetScriptName()!="AR0602") throw std::runtime_error("Declared stock fixture not loaded");
            const std::string before=Snapshot(game),dictionaryBefore=FullDictionary();
            Write(out+"/before.state.json",before);Write(out+"/before.dictionary.json",dictionaryBefore);
            Write(out+"/dispatch.json",O({{"schema",Q("bg-redux-textarea-dispatch/1")},{"case",Q(args["--case"])},{"nonce",Q(args["--nonce"])},{"calls",NumberJSON(++calls)},{"normal_load", "true"},{"paused","true"},{"tick",NumberJSON(ticks)}}));
            try {
                if(args["--case"].find("unnumbered-")==0)TextAreaUnnumberedRegression(out,args["--case"]);
                else TextAreaSelectionRegression(out,args["--case"]);
                completed=true;
            }
            catch (const std::exception& failure) {error=failure.what();}
            const std::string after=Snapshot(game),dictionaryAfter=FullDictionary();
            Write(out+"/after.state.json",after);Write(out+"/after.dictionary.json",dictionaryAfter);
            worldSame=before==after;dictionarySame=dictionaryBefore==dictionaryAfter;
            if (!worldSame || !dictionarySame) error += " Collected world/dictionary changed";
            rc=completed && worldSame && dictionarySame ? 0 : 1;
            core->QuitFlag=QF_KILL;phase=1;
        } catch (const std::exception& failure) {error=failure.what();rc=1;core->QuitFlag=QF_KILL;}},250,-1);
        engine->Main();
    } catch (const std::exception& failure) {error=failure.what();rc=1;}
    Write(out+"/host-result.json",O({{"schema",Q("bg-redux-textarea-host/1")},{"case",Q(args["--case"])},{"nonce",Q(args["--nonce"])},{"completed",completed?"true":"false"},{"calls",NumberJSON(calls)},{"ticks",NumberJSON(ticks)},{"world_equal",worldSame?"true":"false"},{"dictionary_equal",dictionarySame?"true":"false"},{"error",Q(error)},{"os_input","false"},{"gameplay_acceptance","false"}}));
    if (engine) {engine.reset();core=nullptr;VideoDriver.reset();PluginMgr::Get()->RunCleanup();}
    StopLog();return rc;
}
