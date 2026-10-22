// SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
// SPDX-License-Identifier: GPL-2.0-or-later
#include "../../core/KeyMap.h"
#include <gtest/gtest.h>
#include <vector>

namespace GemRB {
TEST(KeyMapBindings, DistinctKeysAndMultipleClears)
{
	EXPECT_TRUE(KeyMap::ValidateBindingKeys({ { "inventory", 'b' }, { "map", 'm' }, { "journal", 0 }, { "options", 0 } }).empty());
}
TEST(KeyMapBindings, DuplicateAndFixedKeysRejected)
{
	EXPECT_FALSE(KeyMap::ValidateBindingKeys({ { "inventory", 'b' }, { "map", 'b' } }).empty());
	for (int key : std::vector<int> { '0', '1', '7', '-', '=', ' ', '\t', 0x90, -1, 300 }) {
		EXPECT_FALSE(KeyMap::IsEditableKey(key));
		EXPECT_FALSE(KeyMap::ValidateBindingKeys({ { "inventory", key } }).empty());
	}
}
TEST(KeyMapBindings, PlainKeysOnlyAndNoUnknownActionMutation)
{
	for (int key : std::vector<int> { 'a', 'z', ',', '.', '/', ';', '\'', '[', ']', '\\', 0 }) EXPECT_TRUE(KeyMap::IsEditableKey(key));
	KeyMap map;
	EXPECT_FALSE(map.ApplyBindings({ { "unknown", 'b' } }).empty());
	EXPECT_TRUE(map.GetBindings().empty());
	EXPECT_EQ(map.LookupFunction("unknown"), nullptr);
}
}
