# Continue BG Redux on the Lab VM

Read [BG_REDUX_COMPLETE_CONTEXT.md](BG_REDUX_COMPLETE_CONTEXT.md) completely. It includes the decision ledger and full charter/audit appendices. The hosted source is [zach-hopkins/bg-redux](https://github.com/zach-hopkins/bg-redux), branch `codex/phase0-audit`; Phase0 materials live in `redux/`.

Use the paste prompt near the end of the decision ledger to start a new chat bound to `C:\BGRedux` on Lab. The subsequent appendices preserve the detailed specifications. This host has not verified guest execution yet. Keep engine code unchanged.

Clone the fork into `C:\BGRedux\gemrb`. Copy its `redux/docs` and `redux/tools` to `C:\BGRedux\docs` and `C:\BGRedux\tools` to restore the existing harness layout. Additional design-context directories under `redux/` should be copied to the matching project-relative locations. A repository download alone does not contain the licensed game, private fixtures, compiled runtime or raw save evidence.

Transfer both private packages from the physical host:

- Base: `phase0-local/vm-transfer/20261021T183745Z`, runtime, source, game copy and required baseline fixtures. Verify against its original `transfer-manifest.json` before overlaying current docs.
- Companion: `phase0-local/context-transfer/20261021-complete-context`, current docs/tools/design references and every existing Phase0 result/log/config/screenshot, with `context-manifest.json`. Copy its `BGRedux` contents over the destination after base verification, then verify this manifest. It preserves historical provenance; it does not turn host runs into guest tests.

Keep both packages private. Do not put game resources, saves, binaries, credentials or the entire surrounding workspace into Git. Do not reset VMware encryption; its password is separate from the passwordless guest administrator account. Actual guest migration acceptance steps are in [VM_HOST_HANDOFF.md](../testing/VM_HOST_HANDOFF.md).
