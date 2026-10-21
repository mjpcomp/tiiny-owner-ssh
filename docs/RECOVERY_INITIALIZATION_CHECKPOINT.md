# Recovery initialization review checkpoint

Recorded 2026-10-20 from static inspection on one owner-administered setup. Read after [storage and USB observations](STORAGE_USB_RECOVERY.md) and [boot/recovery follow-up](BOOT_RECOVERY_FOLLOWUP.md). This note qualifies earlier unresolved recovery-storage observations; it is not a tested boot, backup or restore procedure.

## Findings and limits

- The inspected FAT recovery partition p10 contains filesystem.squashfs. Selected recovery scripts were read from the image as text, not executed. Do not format this partition to reconcile the earlier RAUC filesystem-type mismatch.
- The inspected initialization code uses p11/recovery-data for persistent recovery scripts, output, logs and operation state. The shared overlay is also involved. This clarifies configured roles, not every stored file or all recovery behavior.
- The recovery launcher prepares persistent directories, starts a USB-network helper, selects a normal root using recognized kernel slot-suffix text, and defaults to root A otherwise. It requests ro,noload for a new root mount, verifies its source, and links a Compose plugin from that root. Its existing-mount check does not independently verify read-only options. The active-root name is not independent proof of the normal system's active slot.
- The launcher executes a separate recovery daemon in recovery-factory mode. That daemon's automatic actions, interfaces, authentication and safeguards remain unverified. Intended USB networking does not establish a physical port mapping, a usable PC connection, USB boot or disk-gadget export.
- The separate line-flash initializer has an automatic call sequence, not an interactive approval step. When not skipped and after obtaining its operation lock, it records running state, prepares the overlay and device-bind TEE storage service, runs an authentication/data-initialization wrapper, attempts wired networking/DHCP, runs a production-reporting wrapper, and calls the data-initialization script with expand. Completion is recorded only after those stages return success.
- Recognized completed state skips later initialization stages; recognized legacy success is rewritten as completed. Missing or recognized retry states can proceed toward initialization; invalid state fails. State is checked before and after lock acquisition. The operation lock coordinates cooperating actors; it is not a dry-run or a user-confirmation gate.
- Directory/log writes occur before the completion skip. A completed initialization record does not make recovery non-mutating, establish backup consistency, or clear the separate daemon.
- Device-bind TEE storage references are a preservation dependency to investigate. They do not establish the userdata encryption format, unlock mechanism, key portability or replacement-hardware recovery. Wrapper behavior, reporting destinations/payloads and the precise effects of expand remain unverified.

Unit-specific saved-state values, raw output, vendor implementation, firmware payloads, identifiers, credentials and keys are deliberately not published. Do not edit completion state, remove locks, set override variables or invoke initialization to test the guards.

## End-of-session boundary

The recovery image inspection mounts were reported unmounted. The saved-state inspection used debugfs without write mode and did not mount the recovery-data filesystem. The reviewed scripts were not run as part of these inspections. No experimental recovery boot, slot change, firmware write or initialization is authorized by these findings.

The earlier small USB filesystem write/read-back test is not a whole-system backup. No whole-NVMe image, encryption-header backup, bare-metal restore or validated offline-imaging route has been established. Preserve the original SSH baseline privately; it is not a full-system backup.

## Resume priorities

1. Read this note and its linked predecessors; check GitHub for intervening changes. Retain private current-state observations outside this public repository.
2. Continue static, non-executing inspection of the recovery daemon's startup configuration and safeguards, then targeted wrapper/data-expansion behavior as needed. Do not invoke unknown binaries merely with --help and assume they are harmless.
3. Establish the userdata encryption format and unlock/preservation dependencies without printing keys.
4. Establish a supported offline/rescue and restore route compatible with this ARM64 platform and its firmware trust constraints. Built-in recovery remains unapproved for backup imaging pending that review.
5. Verify a sufficiently large external destination by current identity, actual free bytes and a controlled filesystem test before planning an image. Do not overwrite the only working system to validate restoration.

Carry forward the custom RAUC-backend warning: boot/status getters can have side effects, including marking boot success. Do not invoke guessed getters, select recovery, change boot/EFI state, reinitialize metadata or switch slots for discovery. Publish sanitized summaries only; keep evidence and backups private.
