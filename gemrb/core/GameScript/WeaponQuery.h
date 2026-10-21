// SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
//
// SPDX-License-Identifier: GPL-2.0-or-later

#ifndef GEMRB_WEAPONQUERY_H
#define GEMRB_WEAPONQUERY_H

namespace GemRB {
namespace WeaponQuery {

// HAND.IDS: 1 MAINHAND, 2 OFFHAND, 3 BOTH. Keep the combination
// policy separate: BOTH's any-hand interpretation awaits an original-engine
// mixed-hand oracle. Do not turn OFFHAND into a main-hand fallback.
template<class Predicate>
bool ForSelectedHand(int hand, Predicate&& predicate)
{
	if (hand < 1 || hand > 3) return false;
	return ((hand & 1) && predicate(false)) || ((hand & 2) && predicate(true));
}

// This query tests resistance, not rolled damage, skins, images or weapon
// immunity. In particular, protection from magical weapons must not make
// WeaponCanDamage false (measured BG2EE +1 sword fixture: 0 / 1).
inline bool ResistanceAllowsDamage(int resistance)
{
	return resistance < 100;
}

}
}

#endif
