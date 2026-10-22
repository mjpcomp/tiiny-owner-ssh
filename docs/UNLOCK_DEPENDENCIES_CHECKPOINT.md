# Recovery callbacks and unlock dependencies checkpoint

Recorded 2026-10-22 on one owner-administered setup. Continues [recovery initialization review](RECOVERY_INITIALIZATION_CHECKPOINT.md), [boot follow-up](BOOT_RECOVERY_FOLLOWUP.md), and [storage observations](STORAGE_USB_RECOVERY.md). These are sanitized inspection findings, not a supported unlock procedure or validated backup/restore workflow.

## Recovery daemon: stronger evidence, unresolved gates

- The inspected recovery daemon is an AArch64 ELF executable retaining symbols and debug information. Static call-target summaries show recovery-server construction, HTTP-handler registration and HTTP serving.
- The operation handler references authentication, request decoding, recovery-operation state transitions and goroutine creation. Constructor-associated callback bodies reference password verification, factory readiness checking and factory coordination. Their existence does not prove callback wiring, failure handling or authorization on every mutation path.
- The inspected Compose-version helper has filename/string/integer parsing references; no subprocess execution was demonstrated in that helper.
- No direct factory-format operation was demonstrated in the inspected entry-point summaries. This is not proof of harmless startup: inlining, callbacks, package initialization, conditional paths and unexamined delegates remain limitations.
- The line-flash initializer's completion record is separate from the daemon's operation machinery. It is not a global prohibition on future factory operations.

## Normal-system startup and unlock dependencies

- Normal authd runs directly as a Type=simple service. A running service is not an application-readiness notification or independent proof of successful data unlock.
- The configured data-unlocked target is ordered after authd. Docker requires and follows that target; the first-unlock Compose service requires and follows Docker. This records declared relationships, not a complete runtime trace.
- Docker's inspected pre-start helper immediately succeeds when the target is active. Otherwise it tests whether /data is a mountpoint, attempts to start the target, tolerates that start failing, and returns success. It does not validate the mounted device or encryption health. Do not execute this helper as a passive diagnostic: it can change service state.
- Normal authd contains both LUKS-related and direct dm-crypt helpers. The normal unlock function directly references a blob loader, mapping creation, mounting and data-availability signaling. Other callers use the same mapping helper for vault operations, so helper presence alone does not identify the live data path.
- The blob loader references a filesystem read and a byte-loader helper. The byte loader references a keyctl-named helper and integer parsing. That helper references external-command construction and execution. The exact command, arguments, key type, blob contents and backend selection were not established by these summaries.
- A package name suggesting TEE use does not prove direct userspace TEE communication, a particular kernel trusted-key backend, hardware binding or key portability. Conversely, a kernel-keyring interface does not rule out a TEE-backed implementation.
- Mapping-status and on-device LUKS-recognition checks did not establish a complete encryption format or recovery unlock method. Unit-specific current state, command output, identifiers and encryption parameters remain private. Do not infer a damaged header, plain dm-crypt, or detached-header location from these checks alone.

## Inspection boundary

Selected scripts were read as text. File classification, symbol inventories, filtered direct-call summaries and a targeted direct-caller scan read binaries without invoking them. Some inspection steps made private temporary copies on /run tmpfs and removed them on normal exit; tmpfs may be swapped. This was not forensic zero-change handling.

No loader, keyctl command, mapping helper, authentication endpoint or factory operation was deliberately invoked by these inspection commands. No experimental recovery boot, service restart, key export, slot change or firmware modification was performed as part of this review. The normal running system continued operating.

Call-name inspection stops here. Such lists omit arguments, data flow, conditional branches, inlined effects and indirect-call targets. More names alone cannot certify a safe recovery boot or a portable image. Vendor implementation, executable/disassembly dumps, raw logs, current per-device state, credentials and keys must remain outside public GitHub.

## Next work: preservation and supported restoration

1. Determine the actual blob/configuration preservation locations and their persistent filesystem backing without reading or exporting payloads. Include any trusted-application, firmware or secure-storage dependencies only when established.
2. Establish the key type and trust-source configuration through narrowly scoped metadata or authoritative vendor information, not key extraction or guessed loader commands.
3. Obtain or verify a supported offline imaging and restore/unlock procedure, distinguishing restoration on the original device from replacement hardware. A ciphertext image alone does not establish unlockability.
4. Verify a sufficiently large external destination's current identity and free bytes, then plan consistent imaging and integrity checks. The earlier small USB write/read-back test is not a whole-system backup.
5. Preserve the original SSH baseline privately. No whole-system image, bare-metal restore, portable-key recovery or approved recovery-boot route has been validated.

Do not repair, format, regenerate blobs, reset accounts, rebind the device, change keyrings, close the working data mapping, invoke boot/status getters with known side effects, or overwrite the only working system for discovery. Keep backups and evidence encrypted/private and off the source NVMe and public repository.
