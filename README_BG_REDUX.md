# BG Redux — Phase 1 development

A GemRB derivative for a modern, extensible Baldur's Gate runtime. Preserve the game, modernize the engine, refine the experience.

**Phase 1 implementation is authorized and in progress in an isolated checkout.** See [Phase 1 status](redux/docs/PHASE1_STATUS.md) for current source, builds, evidence and remaining gates. The accepted Phase 0 release and its unchanged engine baseline remain preserved. This development branch is not an accepted compatibility release.

- [Complete continuation context, accepted decisions and embedded charter/reports](redux/docs/handoff/BG_REDUX_COMPLETE_CONTEXT.md)
- [Phase 0 release and technical acceptance](redux/docs/PHASE0_RELEASE.md)
- [Current LAB status](redux/docs/CURRENT_STATUS.md)
- [Phase 0 audit and roadmap](redux/docs/BG_REDUX_PHASE0_AUDIT.md)
- [Start here for the dedicated Windows VM](redux/docs/handoff/START_HERE.md)
- [Architecture acceptance matrix](redux/docs/architecture/subsystem-acceptance-matrix.md)
- [AI-first harness specification](redux/docs/testing/ai-first-harness.md)
- [External harness sources](redux/tools/phase0)

The preserved Phase 0 branch is `codex/phase0-audit`; implementation work uses `codex/phase1-engine`. Original GemRB documentation and license notices remain intact. The current authorization covers the Phase 1 backlog; later gameplay enhancements retain their separate decision boundaries.

## Workspace layout

Historical tooling uses an outer project directory with `gemrb/` for the engine checkout, `docs/` and `tools/` for the audit/harness, and ignored `phase0-local/` for private runtimes and results. For example, clone this branch into `C:\BGRedux\gemrb`, then copy `gemrb\redux\docs`, `gemrb\redux\tools` and its other design-reference directories into matching paths under `C:\BGRedux`. Read the handoff before building. The published `redux/` directory is an additive distribution of those materials; it does not change upstream engine paths.

The licensed game, original saves, toolchain/build outputs, screenshots and raw runtime evidence are deliberately private. The user has separately manifested local transfer packages and preserved LAB results. Existing JSON summaries retain their historical provenance; the release record identifies fresh guest runs. Some linked raw upstream issue archives are private companion files; consult their original GitHub URLs in the issue roadmap. No GitHub CI, deterministic replay or full campaign acceptance is claimed.

The external harness sources added under `redux/tools/phase0` are distributed under GPL-2.0-or-later, consistent with the engine. This grants no rights to commercial game content. Preserve existing upstream and bundled-component notices.
