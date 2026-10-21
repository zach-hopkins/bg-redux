# Discovered temporary defenses: current-state policy

Accepted by the user on October 12, 2026.

Discovering a temporary defense permits accurate tracking of its continued
presence during the encounter. It does not reveal other defenses or hidden
timers. This is an intentional convenience after discovery, not a claim that
every expiration is otherwise observable in the base game.

## Player-facing behavior

| Evidence and state | Inspection behavior |
| --- | --- |
| Defense present but undiscovered | Show nothing. |
| Combat evidence establishes a defense | Show the earned category, or specific name when established, as active. |
| A reliable category-specific check establishes that the observed defense ended | Remove its active entry; optionally retain an ended entry in history. |
| A check fails or lacks coverage | Preserve last observation or mark current state unknown; never claim expiration. |
| Application witnessed and duration reliably established | An optional timer may track that observed duration. |
| Defense discovered partway through its duration | Show active status without exposing its hidden remaining timer. |
| An unseen new application follows expiration | Do not inherit disclosure permission from the earlier application. |

Combat evidence grants disclosure permission. Independent, read-only state
checks keep already-discovered defenses accurate. These checks must not create
new discoveries, disclose other defenses, queued spells, contingency contents,
or persistent innate traits. Persistent enemy knowledge remains a separate layer.

## Implementation requirements

- Attach discovery to the target incarnation and observed defense application,
  rather than globally granting access to every subsequent casting of a spell.
- Check the relevant defensive effects or effective state. A source spell may
  retain unrelated effects after its protective component ends.
- Establish completeness for each supported category before interpreting an
  absent effect as an ended defense. Multiple matching active instances must
  not be confused with disappearance of the observed instance.
- Revalidate object identity and effect lifetime on each bounded snapshot; do
  not retain borrowed engine pointers between checks.
- Keep verification read-only and preserve combat rules. Refresh on inspection
  or bounded invalidation rather than scanning every creature every frame.
- Respect current inspection visibility. Do not turn off-screen or hidden
  state changes into unsolicited public announcements.
- Resolve Shift-hover coexistence with EEex's optional effect menu without
  replacing or enabling that module silently.

The EEex effect menu provides an existing effect-enumeration and UI example,
not a complete defense verifier. The installed and upstream `B3EffMen.lua`
iterate the timed-effect list, group by source resource, filter certain
permanent/no-icon effects, and rebuild when the hovered target changes.
Its omission of an entry is not an authoritative absence test, and its spell
grouping does not establish which components of a spell remain active.

Reference: [EEex effect-menu source](https://github.com/Bubb13/EEex/blob/master/EEex/copy/EEex_scripts/B3EffMen.lua).

## Delivery order and feasibility gates

Continue causal logging and safe event publication first. Later, implement a
small defense verifier with active/ended presentation for established categories.
Optional observed-duration timers follow; a predicted/confirmed/uncertain
three-category UI is not required for the initial inspection feature.

Before promoting a defense category, demonstrate discovery, continued presence,
expiration, explicit removal, partial spell survival, overlapping applications,
hidden reapplication, failed reads, and target replacement. Validate installed
baseline and EET resources and SCS/Ascension variants as applicable. These are
future acceptance gates, not completed runtime coverage.
