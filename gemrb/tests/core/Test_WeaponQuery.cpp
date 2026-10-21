// SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
//
// SPDX-License-Identifier: GPL-2.0-or-later

#include "../../core/GameScript/WeaponQuery.h"

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

}
