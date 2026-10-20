# Current project state

Updated: 2026-10-19. This file and README.md supersede historical checkpoint-stage descriptions.

The seven engine modules are committed and match the owner's uploaded working snapshots by Git blob hash. They compiled and all local import targets were present. The build environment lacked cramjam, so a full real-dependency import test was not performed there; the owner tested it and the workflow on Windows AMD64.

Owner-run hardware tests passed: token/API access; temporary connector/service/report lifecycle; immutable backup/read-back; key rejection before install; offline service/listener preflight; actual install with fresh root login; actual restore with fresh key rejection; final baseline-state check and cleanup.

The new tiiny.py/tiiny.cmd front end prompts for missing action/IP, defaults to the existing private state directory, validates inputs and delegates to unchanged engines without bypassing confirmations. It does not remove tiiny_owner.py: that remains a required internal dependency pending a separate refactor.

32 tests passed in the Linux build environment: 16 launcher tests with mocked child processes and 16 POSIX host-state regressions with mocked system checks/signals. This is not Windows batch or new hardware end-to-end validation. Validate the new launcher with --dry-run before device use; Windows shortcut execution remains untested here.

The paired backup/access engines remain directly callable. Unsupported legacy tiiny_owner.py CLI discovery is not a supported entry point. Existing baseline files must not be regenerated or edited.

The README includes setup, key, backup/check/install/restore, PuTTY and recovery limits. docs/HARDWARE.md separates observations from advertised capacities and unresolved questions.

Real failure/interruption recovery, reboot persistence, firmware updates, other client/device versions, complete metadata restoration and warranty neutrality remain unverified. Current per-device access state is intentionally not tracked publicly. All baseline/runtime data, tokens, private keys and raw evidence stay out of the repository.
