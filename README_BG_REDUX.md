# BG Redux — Phase 0

A GemRB derivative for a modern, extensible Baldur's Gate runtime. Preserve the game, modernize the engine, refine the experience.

**Phase 0 research, baseline validation, architecture contracts and external test tooling now have fresh LAB evidence. Engine source is unchanged from `bcb5cfaa9f19ffbe8a51f25a3c014fa344173351`.** See the release record for technical acceptance and explicit compatibility limits. This is not a native-like compatibility release.

- [Complete continuation context, accepted decisions and embedded charter/reports](redux/docs/handoff/BG_REDUX_COMPLETE_CONTEXT.md)
- [Phase 0 release and technical acceptance](redux/docs/PHASE0_RELEASE.md)
- [Current LAB status](redux/docs/CURRENT_STATUS.md)
- [Phase 0 audit and roadmap](redux/docs/BG_REDUX_PHASE0_AUDIT.md)
- [Start here for the dedicated Windows VM](redux/docs/handoff/START_HERE.md)
- [Architecture acceptance matrix](redux/docs/architecture/subsystem-acceptance-matrix.md)
- [AI-first harness specification](redux/docs/testing/ai-first-harness.md)
- [External harness sources](redux/tools/phase0)

The default Phase 0 branch is `codex/phase0-audit`. Original GemRB documentation and license notices remain intact. Engine changes and gameplay enhancements need separate authorization. The modern UI and BG2EE-import/versioned-Redux-save directions are approved; neither is implemented by this publication.

## Workspace layout

Historical tooling uses an outer project directory with `gemrb/` for the engine checkout, `docs/` and `tools/` for the audit/harness, and ignored `phase0-local/` for private runtimes and results. For example, clone this branch into `C:\BGRedux\gemrb`, then copy `gemrb\redux\docs`, `gemrb\redux\tools` and its other design-reference directories into matching paths under `C:\BGRedux`. Read the handoff before building. The published `redux/` directory is an additive distribution of those materials; it does not change upstream engine paths.

The licensed game, original saves, toolchain/build outputs, screenshots and raw runtime evidence are deliberately private. The user has separately manifested local transfer packages and preserved LAB results. Existing JSON summaries retain their historical provenance; the release record identifies fresh guest runs. Some linked raw upstream issue archives are private companion files; consult their original GitHub URLs in the issue roadmap. No GitHub CI, deterministic replay or full campaign acceptance is claimed.

The external harness sources added under `redux/tools/phase0` are distributed under GPL-2.0-or-later, consistent with the engine. This grants no rights to commercial game content. Preserve existing upstream and bundled-component notices.
