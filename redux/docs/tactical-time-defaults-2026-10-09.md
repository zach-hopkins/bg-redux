# Tactical Time defaults — 2026-10-09

This decision supersedes metered Tactical Grace and the earlier 25% Slow / single Hard Pause cooldown. Historical test reports retain the speeds and recharge behavior actually measured at the time.

| Control | Default | Purpose |
| --- | --- | --- |
| Normal | 100% | Execute commands normally |
| Tactical Slow | 25% target, unlimited (26.7% at native rate30) | Routine tactical micro |
| Hard Pause in combat | 0%, two banked charges | Shared planning and emergencies |
| Outside combat | Ordinary native pause, unrestricted by MRDX | Exploration without artificial friction |

Slow replaces routine pausing; Hard Pause supplements it. There is no Slow meter or duration limit. Either peer's active Slow intent slows the whole world. Normal speed returns after the last requester releases it. Hard Pause clears all Slow intents, and Ready completion resumes Normal; Slow must be requested again.

## Initial bank policy

- One shared host-authoritative bank, initially full at two charges per logical session. Simultaneous requests for an already active Hard Pause do not spend another charge.
- Each accepted in-combat Hard Pause consumes one charge. A second charge can be used immediately after resuming. An empty bank rejects requests until a charge recharges.
- Current default: ten simulated seconds per charge (150 game ticks), configurable. The user increased this after the two-charge GUI test; the earlier five-second value remains in historical test evidence.
- Recharge starts when the first charge is spent, preserves partial progress when another charge is spent, and fills charges sequentially up to capacity. A full bank stores no surplus time.
- Recharge uses the native game clock: no credit while time is stopped; at the rounded default26.7% Slow, ten simulated seconds takes about37.5 real seconds. Active exploration time also recharges the bank. Combat boundaries do not instantly refill it.
- Native exploration pause remains unchanged and does not consume charges. The coordinated combat Hard Pause API remains combat-scoped; outside combat use ordinary native pause.
- Abort does not refund a spent charge. Disconnect cleanup and Ready participant removal retain their existing authority rules.
- Session/load resets currently initialize a full bank. Save-persistent recharge accounting is not implemented.

## Source changes

`ui/settings.lua`: Slow25% target, recharge ten seconds, capacity two. Local `slow_activation` accepts `toggle` or `hold`, default toggle. At the ordinary native rate30, the integer Slow setting rounds to8 (four game ticks per second,26.7% actual speed). The panel truthfully rounds that actual percentage to27%. The user chose this default after trying20% and30% in the paired GUI session.

`time/reducer.lua`: Time schema version 3 adds canonical `pause_charges`, `pause_capacity`, and `recharge_ticks`. `recharge_until` is the deadline for the next charge, zero when full. The host alone commits recharge observations. Slow remains unmetered.

`time/runtime.lua`: host checks the native clock and requests a recharge commit only when a deadline is due. Configuration passes capacity into the reducer.

`ui/model.lua` and `ui/presenter.lua`: expose charge counts and local Slow intent; toggle and hold press/release submit intent without optimistic canonical changes. Actual GUI bindings and selection of the configured activation style remain part of the GUI adapter work; no new installed menu is claimed.

## Verification and next gate

Regression cases are prepared for immediate use of both charges, empty-bank rejection, simulated deadlines, exploration recharge, no free refill at combat end, full-bank cap, host-only recharge, unlimited Slow with an empty bank, Ready/departure behavior, serialized charge state, and toggle/hold intent.

SSH access returned on 2026-10-09. The full Core/Interaction/Time/UI regression suite passed on Zach-PC, including the new bank and activation-intent cases. The rebuilt bundle passed LuaJIT parsing and isolated WeiDU installation/rollback with the TLK unchanged. Both closed disposable copies were installed and all seven overlay hashes verified. Native in-game and paired verification of these new defaults remains pending.

Next: exercise native rate 30→6→30 and banked recharge, then batch the paired gate for bank synchronization, no recharge while paused, aggregate Slow ownership, competing pause requests, Ready and departure/reload cleanup. Old solo timing cases still assert rate 8/single cooldown and must be updated before reuse.

## Installed candidate

- Package: `dist/mrdx-scene-wait-lab-533ef65d57.zip`.
- Runtime SHA256: `533ef65d571f6708dda9cded586719b7da9d693a0baed581ac0987501d0bbf10`.
- Local rollback backup: `scratch/bg2ee-local/MRDX-automation/backups/combined-lab-20261009-135615`.
- Laptop rollback backup: `C:\Users\Zach\Documents\Baldur's Gate II Enhanced Edition\MRDX-automation\backups\combined-lab-20261009-135617`.
- Solo autoboot disabled on both, multiplayer menus available. Existing saves preserved. Other running games were not changed or stopped.


## Paired gate completed and cooldown fix installed

The focused two-player default-policy checks passed after a native acknowledgement retry fix. Slow ownership, pause/Ready/Unready, two immediate charges, third-request rejection, simulated recharge at 20% speed, and ordinary exploration pause were observed. Recharge measured 76 game ticks / 25037 ms at rate 6. See [full gate report](tactical-time-paired-gate-2026-10-09.md) for the initial failure, running Lua patch, limitations, evidence and latest installed hash. The latest permanent package is `mrdx-scene-wait-lab-9baef2faae.zip`; it supersedes the initial installation listed above. Both games are closed, and fresh startup of this permanent bundle remains unobserved.
