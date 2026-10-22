// SPDX-FileCopyrightText: 2009 Contributors to the GemRB project <https://gemrb.org>
//
// SPDX-License-Identifier: GPL-2.0-or-later

#ifndef KEYMAP_H
#define KEYMAP_H

#include "exports.h"
#include "ie_types.h"

#include "Strings/StringMap.h"
#include "System/VFS.h"

#include <map>

namespace GemRB {

class GEM_EXPORT KeyMap {
public:
	struct Function {
		ieVariable moduleName;
		ieVariable function;
		int group;
		int key;
	};

	bool InitializeKeyMap(const path_t& inifile, const ResRef& keyfile);
	bool ResolveKey(unsigned short key, int group) const;
	bool ResolveName(const StringView& name, int group) const;

	const Function* LookupFunction(const StringView& name);

	struct Binding {
		Function action;
		int defaultKey;
	};
	using BindingKeys = std::map<std::string, int>;
	const std::map<std::string, Binding>& GetBindings() const { return bindings; }
	// Empty means valid. No key/action changes happen unless the complete set
	// validates. Dry-run supports persistence-before-commit in the editor.
	std::string ApplyBindings(const BindingKeys& keys, bool dryRun = false);
	static bool IsEditableKey(int key);
	static std::string ValidateBindingKeys(const BindingKeys& keys);

private:
	StringMap<Function> keymap;
	std::map<std::string, Binding> bindings;
};

}

#endif
