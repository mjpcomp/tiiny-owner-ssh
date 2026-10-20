# Validation scope

Updated 2026-10-20. These are observations on one setup, not general compatibility claims.

## Device workflow, completed 2026-10-19

On Windows 11 AMD64/Python 3.13.15 with TiinyOS Windows client 1.0.1 and a Debian 12/aarch64 target: token/API checks; temporary connector/service/report lifecycle; immutable original-state backup and read-back; owner-key rejection; offline SSH service/listener preflight; real installation and fresh root SSH login; real restoration and fresh owner-key rejection; final baseline-state check. Cleanup checks passed. Later root access was used for inventory; public docs do not track the device's current access state.

## Launcher, completed on Windows 2026-10-20

The owner ran tiiny.cmd check --dry-run and tiiny.cmd check from a newly downloaded repository folder. System-Python fallback selected the installed Python 3.13; omitted IP prompted correctly; the existing default AppData state directory was reused. Dry-run did not invoke the engine. Live check preserved typed confirmation, passed baseline integrity, reported the expected installed state and verified service/listener; cleanup passed.

This does NOT validate the Windows .venv-selection branch, no-argument action menu, explicit-IP path or install/restore through the launcher on hardware. The underlying install/restore engines were tested directly.

## Build-environment checks

All seven original engine modules were compared to owner-supplied working files by Git blob hash and matched byte-for-byte; they compiled and local import targets were present. cramjam was absent in that build environment, so this was not a full real-dependency runtime import test. The owner had tested it on Windows.

32 Linux tests passed: 16 launcher unit tests with mocked child processes and 16 POSIX host-state regressions using temporary files and mocked system/SSH checks/signals. Ownership in transactions is mapped to the test user. They do not contact devices or prove real failure recovery.

## Not established

Reboot persistence, firmware-update compatibility, recovery through real interruption/failure, every Match context, other client/device versions, factory equivalence, complete metadata restoration, warranty neutrality and accelerator-local memory capacity. See HARDWARE.md for observed facts versus advertised specifications.
