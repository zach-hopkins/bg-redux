// SPDX-FileCopyrightText: 2009 Contributors to the GemRB project <https://gemrb.org>
//
// SPDX-License-Identifier: GPL-2.0-or-later

#include "KeyMap.h"

#include "Interface.h"
#include "ScriptEngine.h"
#include "TableMgr.h"

#include "Logging/Logging.h"
#include "Streams/FileStream.h"

#include <unordered_set>
#include <utility>

namespace GemRB {

bool KeyMap::InitializeKeyMap(const path_t& inifile, const ResRef& tablefile)
{
	AutoTable kmtable = gamedata->LoadTable(tablefile);

	if (!kmtable) {
		return false;
	}

	path_t tINIkeymap = PathJoin(core->config.GamePath, inifile);
	DataStream* config = FileStream::OpenFile(tINIkeymap);
	if (!config) {
		config = gamedata->GetResourceStream(inifile.substr(0, inifile.size() - 4), IE_INI_CLASS_ID);
	}
	if (!config) {
		Log(WARNING, "KeyMap", "There is no '{}' file...", inifile);
		return false;
	}

	std::unordered_set<std::string> reservedKeyNames { "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "tab", "space" };
	const ieVariable defaultModuleName = kmtable->QueryField("Default", "MODULE");
	const ieVariable defaultFunction = kmtable->QueryField("Default", "FUNCTION");
	int defaultGroup = kmtable->QueryFieldSigned<int>("Default", "GROUP");
	std::string line;
	while (config->ReadLine(line) != DataStream::Error) {
		if (line.length() == 0 ||
		    (line[0] == '#') ||
		    (line[0] == '[') ||
		    (line[0] == '\r') ||
		    (line[0] == '\n') ||
		    (line[0] == ';')) {
			continue;
		}

		StringToLower(line);
		auto parts = Explode<std::string, std::string>(line, '=', 1);
		if (parts.size() < 2) {
			parts.emplace_back();
		}

		auto& key = parts[0];
		RTrim(key);
		if (key.substr(0, 10) == "unmappable") {
			continue;
		}

		auto& val = parts[1];
		if (val.length() == 0) continue;
		LTrim(val);

		if (reservedKeyNames.count(val) > 0) continue;
		if (val.length() > 1 || keymap.Get(val) != nullptr) { // "win1", "win2", "menu"
			Log(WARNING, "KeyMap", "Ignoring key {}", val);
			continue;
		}

		//change internal spaces to underscore
		std::replace(key.begin(), key.end(), ' ', '_');

		Function func;
		func.key = val[0];

		if (kmtable->GetRowIndex(key) != TableMgr::npos) {
			func.moduleName = kmtable->QueryField(key, "MODULE");
			func.function = kmtable->QueryField(key, "FUNCTION");
			func.group = kmtable->QueryFieldSigned<int>(key, "GROUP");
		} else {
			func.moduleName = defaultModuleName;
			func.function = defaultFunction;
			func.group = defaultGroup;
		}

		// lookup by either key or name
		keymap.Set(val, func);
		keymap.Set(key, func);
		if (func.group == 0 && IsEditableKey(func.key) &&
		    kmtable->GetRowIndex(key) != TableMgr::npos && func.function != "*") {
			bindings.emplace(key, Binding { func, func.key });
		}
	}
	delete config;

	// Profile overrides never modify the game's keymap.ini. Invalid/stale files
	// keep the complete original mapping rather than partially applying rows.
	std::unique_ptr<DataStream> profile(core->config.SavePath.empty() ? nullptr :
		FileStream::OpenFile(PathJoin(core->config.SavePath, "gemrb-keymap.ini")));
	if (profile) {
		BindingKeys keys;
		for (const auto& binding : bindings) keys.emplace(binding.first, binding.second.action.key);
		std::unordered_set<std::string> seen;
		bool valid = true;
		while (profile->ReadLine(line) != DataStream::Error) {
			LTrim(line); RTrim(line);
			if (line.empty() || line[0] == '#' || line[0] == ';' || line[0] == '[') continue;
			StringToLower(line);
			auto parts = Explode<std::string, std::string>(line, '=', 1);
			if (parts.size() != 2) { valid = false; break; }
			auto name = parts[0]; auto value = parts[1];
			LTrim(name); RTrim(name); LTrim(value); RTrim(value);
			if (bindings.count(name) == 0 || !seen.insert(name).second || value.size() > 1) { valid = false; break; }
			keys[name] = value.empty() ? 0 : static_cast<unsigned char>(value[0]);
		}
		const auto error = valid ? ApplyBindings(keys) : "Malformed or stale profile keymap";
		if (!error.empty()) Log(WARNING, "KeyMap", "Profile bindings ignored: {}", error);
	}
	return true;
}

bool KeyMap::IsEditableKey(int key)
{
	// Fixed party selection, pause, console, arrows/function keys and modified
	// debug/script routes keep their existing dispatch. Only plain ASCII keys.
	if (key < 0 || key > 127) return false;
	return key == 0 || (key >= 'a' && key <= 'z') ||
	       std::string(",./;'[]\\").find(static_cast<char>(key)) != std::string::npos;
}

std::string KeyMap::ValidateBindingKeys(const BindingKeys& keys)
{
	std::map<int, std::string> used;
	for (const auto& entry : keys) {
		if (entry.second < 0 || entry.second > 127 || !IsEditableKey(entry.second)) return "Unsupported or fixed key: " + entry.first;
		if (entry.second && !used.emplace(entry.second, entry.first).second) return "Duplicate key: " + entry.first;
	}
	return {};
}

std::string KeyMap::ApplyBindings(const BindingKeys& keys, bool dryRun)
{
	if (keys.size() != bindings.size()) return "Complete binding set required";
	const auto error = ValidateBindingKeys(keys);
	if (!error.empty()) return error;
	std::unordered_set<int> editableKeys;
	for (const auto& binding : bindings) editableKeys.insert(binding.second.action.key);
	for (const auto& entry : keys) {
		if (bindings.count(entry.first) == 0) return "Unknown action: " + entry.first;
		if (entry.second && editableKeys.count(entry.second) == 0) {
			char character[2] = { static_cast<char>(entry.second), 0 };
			if (keymap.Contains(character)) return "Key belongs to a non-editable action: " + entry.first;
		}
	}
	if (dryRun) return {};
	auto candidate = keymap;
	auto updated = bindings;
	// Remove every old alias before installing any new alias: swaps are safe.
	for (auto& binding : updated) {
		if (binding.second.action.key) {
			char character[2] = { static_cast<char>(binding.second.action.key), 0 };
			candidate.Erase(character);
		}
	}
	for (auto& binding : updated) {
		binding.second.action.key = keys.at(binding.first);
		candidate.Set(binding.first, binding.second.action);
		if (binding.second.action.key) {
			char character[2] = { static_cast<char>(binding.second.action.key), 0 };
			candidate.Set(character, binding.second.action);
		}
	}
	keymap = std::move(candidate);
	bindings = std::move(updated);
	return {};
}

//group can be:
//main gamecontrol
bool KeyMap::ResolveKey(unsigned short key, int group) const
{
	// FIXME: key is 2 bytes, but we ignore one. Some non english keyboards won't like this.
	char keystr[2] = { (char) key, 0 };
	if (key < 128) {
		Log(MESSAGE, "KeyMap", "Looking up key: {} ({}) ", key, keystr);
	} else {
		// We'd have to convert the codepoint into UTF-8 for non-ASCII numbers
		Log(MESSAGE, "KeyMap", "Looking up key: {}", key);
	}

	return ResolveName(keystr, group);
}

bool KeyMap::ResolveName(const StringView& name, int group) const
{
	auto lookup = keymap.Get(name);
	if (lookup == nullptr) {
		return false;
	}

	if (lookup->group != group) {
		return false;
	}

	Log(MESSAGE, "KeyMap", "RunFunction({}::{})", lookup->moduleName, lookup->function);
	core->GetGUIScriptEngine()->RunFunction(lookup->moduleName.c_str(), lookup->function.c_str());
	return true;
}

const KeyMap::Function* KeyMap::LookupFunction(const StringView& key)
{
	return keymap.Get(key);
}

}
