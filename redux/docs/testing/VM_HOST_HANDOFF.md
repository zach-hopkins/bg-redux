# Complete the BG Redux Lab host setup

October 21 LAB update: Phase 0 technical evidence is consolidated in [the release record](../PHASE0_RELEASE.md). Base/context transfer and native validation are complete; engine source/binaries are unchanged. Host input isolation is user-confirmed. VM snapshots are optional and excluded from gates by explicit user instruction. Earlier pending-transfer/snapshot statements below are historical. Phase 1 engine implementation remains separately authorized work.

## Historical host-side record

October 21 guest continuation: this project now executes on LAB. See
[guest bring-up results](lab-guest-bringup.md) for independently verified system,
source and game hashes, partial harness failures and the remaining private
transfer gate. The physical-host execution statements below are historical.

Current execution is still on the physical host. The connected device is named Lab (`remote-control:env_e_6ad921094914832d8d5bda6f49aa37e4`), but no Lab project was returned by list_projects on October21,2026. The running chat cannot hand itself to another host with the available tool. The user must open/move this chat onto a saved project on Lab before its shell and Computer Use can be verified there. Do not claim remote execution from a connection label alone.

The user reports Windows installed/booted, Codex remote access paired, and Steam BG2EE installed inside Lab at:

`C:\Program Files (x86)\Steam\steamapps\common\Baldur's Gate II Enhanced Edition`

The physical host's VMware CLI confirms one running VM, BG Redux Lab. Guest-tools/IP commands stop at VMware's encryption-password requirement, before any Windows credential check. The VM encryption password is distinct from the user's passwordless Windows administrator account. Do not reset encryption, extract stored credentials, or request the password as a workaround for the Codex project binding.

## Transfer source and destination

Host package: `C:\Users\zach\Documents\ChatGPT\BG Multiplayer Redux\phase0-local\vm-transfer\20261021T183745Z`.

Its BGRedux subdirectory is the intended `C:\BGRedux` guest project. It contains6,488,245,518 manifested bytes across43,358 files, including the pinned engine checkout, historical build/runtime,2,324 original manifested game files, vanilla input, and two historical oracle runs required by the71 unit tests. Historical execution paths remain original-host records. The package predates the last VM status updates; use the host's latest audit/handoff files as follow-up documentation, not as new game-test evidence.

Copy through a narrowly scoped shared folder or another user-approved transfer method. Do not copy host credentials or unrelated Redux projects. Verify transfer-manifest.json using the supplied vm-guest-check.ps1 before modifying copied files. Keep the newly installed Steam game as a separate original source. Hash/version-check it before treating it as the previous reference dataset; do not overwrite original fixtures to hide differences.

## Required work after the chat executes on Lab

1. Record actual hostname, OS, VMware guest model, user context,6vCPU/12GiB configuration, free disk and renderer. Confirm a screenshot is of the guest and shell paths are guest paths. Verify VMware Tools/guest display driver; no screenshot or guest shell has yet been verified by this chat.
2. Verify Baldur.exe version and hash, chitin.key, dialog.tlk and game resources against the host baseline manifest. Record differences if the new Steam installation is a different version/content set.
3. Verify the copied engine checkout is clean at bcb5cfaa9f19ffbe8a51f25a3c014fa344173351 and four engine/test binaries plus45 plugins match baseline hashes. Keep engine code/binaries unchanged.
4. Use the copied UCRT64 Python/runtime; install Git for Windows if absent. Run71 harness tests. Two actual historical oracle runs are needed; the earlier copied-runtime attempt correctly failed when they were absent.
5. Rebuild only tools/phase0/native test hosts with build-save-probe.py and build-gui-probe.py. Their output directories are initially empty, so new receipts bind guest paths and copied engine hashes. The copied CMake cache contains physical-host paths: do not rebuild the engine in that directory.
6. Run capabilities, vanilla import/query/reload, normal GUI save/reload and presentation capture. Use fresh guest result directories and record process, assertion, persistence and presentation outcomes separately. Expected compatibility differences must remain visible.
7. Verify Computer Use and the AI harness operate inside the VM while the physical host remains usable. Keep the guest session available for graphical tasks. Take clean/validated snapshots after successful bring-up; verify snapshot creation through VMware before declaring recovery ready.
8. Update VM creation status, migration report and main Phase0 audit with actual guest outcomes. Mark active-host migration complete only when the project, game, native test hosts, guest test results and input isolation are verified. Engine changes remain deferred.

## Current confirmation boundary

Confirmed: paired Lab host identifier is exposed to handoff tooling; physical VM is running; private transfer package is staged; copied runtime passed71 tests on the physical host.

User-reported, not independently verified in Lab: Windows desktop ready, Codex paired and Steam game installed.

Remaining: project binding, file transfer, guest game/source/dependency verification, native host builds, guest tests, renderer/input isolation and snapshots. No setup-complete claim is justified yet.
