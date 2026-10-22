// SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
//
// SPDX-License-Identifier: GPL-2.0-or-later

#include "../../core/RNG.h"

#include <gtest/gtest.h>
#include <thread>

namespace GemRB {

TEST(RNGSnapshotTest, AbsentObservationDoesNotInstantiateAndIsThreadScoped)
{
	// A fresh thread has no RNG even if other tests initialized their thread's RNG.
	std::thread worker([] {
		std::mt19937_64 state, copy;
		const auto untouched = state;
		EXPECT_FALSE(RNG::TrySnapshotState(state));
		EXPECT_FALSE(RNG::TrySnapshotState(state));
		EXPECT_EQ(untouched, state);
		RNG::getInstance(); // ordinary initialization, never done by observation
		ASSERT_TRUE(RNG::TrySnapshotState(state));
		std::thread other([] {
			std::mt19937_64 state;
			EXPECT_FALSE(RNG::TrySnapshotState(state));
		});
		other.join();
		ASSERT_TRUE(RNG::TrySnapshotState(copy));
		EXPECT_EQ(state, copy);
	});
	worker.join();
}

TEST(RNGSnapshotTest, RepeatedCopiesDoNotAdvanceButRealDrawMatchesCopiedEngine)
{
	std::thread worker([] {
		RNG& live = RNG::getInstance();
		std::mt19937_64 before, after, copy;
		ASSERT_TRUE(RNG::TrySnapshotState(before));
		for (int i = 0; i < 8; ++i) {
			ASSERT_TRUE(RNG::TrySnapshotState(copy));
			EXPECT_EQ(before, copy);
		}
		auto expected = before;
		std::uniform_int_distribution<int> distribution(0, 1000000);
		const int copiedDraw = distribution(expected);
		EXPECT_EQ(live.rand(0, 1000000), copiedDraw);
		ASSERT_TRUE(RNG::TrySnapshotState(after));
		EXPECT_NE(before, after);
		EXPECT_EQ(expected, after);
		ASSERT_TRUE(RNG::TrySnapshotState(copy));
		EXPECT_EQ(after, copy);
	});
	worker.join();
}

}
