// SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
//
// SPDX-License-Identifier: GPL-2.0-or-later

#include "../../core/GameScript/WeaponQuery.h"
#include "../../core/Item.h"
#include "../../core/Scriptable/Actor.h"

#include <gtest/gtest.h>

namespace GemRB {

TEST(WeaponQueryTest, InvalidHandDoesNotInspectEitherWeapon)
{
	for (int hand : { -1, 0, 4, 255 }) {
		int calls = 0;
		EXPECT_FALSE(WeaponQuery::ForSelectedHand(hand, [&calls](bool) { ++calls; return true; }));
		EXPECT_EQ(calls, 0);
	}
}

TEST(WeaponQueryTest, ExplicitHandDoesNotFallBackOrInspectOtherHand)
{
	int calls = 0;
	EXPECT_FALSE(WeaponQuery::ForSelectedHand(2, [&calls](bool offHand) {
		++calls;
		EXPECT_TRUE(offHand);
		return !offHand; // empty/off-hand cannot borrow the effective main hand
	}));
	EXPECT_EQ(calls, 1);
	EXPECT_TRUE(WeaponQuery::ForSelectedHand(1, [](bool offHand) {
		EXPECT_FALSE(offHand);
		return true;
	}));
}

// Implementation policy test only. Mixed-hand BOTH parity is explicitly
// pending an original-engine oracle, not established by this unit test.
TEST(WeaponQueryTest, PendingOracleBothPolicyAcceptsEitherAvailableHand)
{
	for (bool main : { false, true }) {
		for (bool off : { false, true }) {
			EXPECT_EQ(WeaponQuery::ForSelectedHand(3, [main, off](bool left) { return left ? off : main; }), main || off);
		}
	}
}

TEST(WeaponQueryTest, PercentageResistanceBoundaryAndSusceptibility)
{
	for (int resistance : { -100, -1, 0, 50, 99 }) {
		EXPECT_TRUE(WeaponQuery::ResistanceAllowsDamage(resistance));
	}
	for (int resistance : { 100, 101, 200 }) {
		EXPECT_FALSE(WeaponQuery::ResistanceAllowsDamage(resistance));
	}
}

TEST(WeaponQueryTest, SelectedAmmunitionOwnEnchantmentAndFlagsPreserveCombatCache)
{
	// Both measured launcher/ammo pairs have cached combat enchantment1.
	// Only the selected ammunition determines the query's starting enchantment
	// and magical flag: normal ammo/+1 bow differs from +1 ammo/normal bow.
	for (ieDword ammoEnchantment : { 0U, 1U }) {
		Item ammunition;
		ammunition.Enchantment = ammoEnchantment;
		ammunition.Flags = 44U | (ammoEnchantment ? IE_ITEM_MAGICAL : 0U);
		ITMExtHeader header;
		header.AttackType = ITEM_AT_PROJECTILE;
		header.Location = ITEM_LOC_WEAPON;
		header.DamageType = 4;
		WeaponInfo combat;
		combat.item = &ammunition;
		combat.extHeader = &header;
		combat.slot = 11;
		combat.enchantment = 1;
		combat.itemflags = (ammunition.Flags << 8) | IE_INV_ITEM_IDENTIFIED | IE_INV_ITEM_EQUIPPED;
		combat.wflags = WEAPON_RANGED;
		combat.launcherDmgBonus = 3;

		const auto query = WeaponQuery::ForImmunity(combat);
		EXPECT_EQ(query.enchantment, ammoEnchantment);
		EXPECT_EQ(query.itemflags, combat.itemflags);
		EXPECT_EQ(bool(query.itemflags & IE_INV_ITEM_MAGICAL), bool(ammoEnchantment));
		EXPECT_EQ(query.item, &ammunition);
		EXPECT_EQ(query.extHeader, &header);
		EXPECT_EQ(query.slot, 11);
		EXPECT_EQ(query.wflags, WEAPON_RANGED);
		EXPECT_EQ(query.launcherDmgBonus, 3);
		EXPECT_EQ(combat.enchantment, 1U);
		EXPECT_EQ(ammunition.Enchantment, ammoEnchantment);
	}
}

}
