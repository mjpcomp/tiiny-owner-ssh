# Paired implementation rehearsal results

Updated: 2026-10-19. These owner-run results extend docs/VALIDATED_CHECKPOINT.md.

## Read-only pre-install inspection

- Saved baseline integrity passed and current managed state/recorded identity matched.
- Offline unit-file inspection reported ssh.service enabled, sshd.service as an alias, and ssh.socket enabled.
- The default SSH configuration parsed successfully and reported port 3588, PermitRootLogin no, public-key authentication enabled, and /run/sshd.pid as the PID file.
- The expected PID file existed and its process was sshd.
- The process inspection detected no custom configuration, -o override, or port override flags.
- The main configuration directly included the standard SSH drop-in glob.
- Default configuration inspection does not simulate every possible Match context.

## Paired check command

The owner ran the new paired implementation's check command successfully. It reported baseline state true, installed state false, native ssh.service enabled offline, and a verified listener. Temporary service, report, and connector cleanup checks passed.

## Restore rehearsal before installation

The owner ran the paired restore command while the device was still in its original baseline state. It completed successfully, verified that managed state matched the baseline, and offered the owner public key on a fresh connection, where authentication was rejected. Temporary service, report, and connector cleanup checks passed.

This is a NO-OP restore rehearsal. The target files already matched the baseline, so it does not demonstrate restoration of installed changes or exercise the actual SSH reload branch. The temporary execution service requested a read/write host mount and host PID namespace, but the host-side state operation found no managed file changes necessary.

## Still unverified

- Actual installation of the owner public key/drop-in and successful fresh root SSH login.
- Real restoration after installation, including file replacement/removal and native daemon reload.
- Automatic restoration after a real installation or final-login failure.
- Persistence across reboot or firmware updates.

## Next hardware validation

Run installation with the existing immutable baseline. If fresh root SSH verification succeeds, run restore and verify public-key rejection, then run check and confirm baseline state true and installed state false. Stop on unexpected outcomes and preserve local state. Reinstallation for ongoing access should follow only after reviewing the full-cycle results.

The installer is designed to attempt restoration on installation/login-test failure; this remains a recovery attempt, not a guarantee. Conflicting external changes, interruption, API failure, or failed rollback can require manual recovery.

## Source and privacy status

The paired implementation was supplied as a local preview with sixteen passing synthetic transaction tests. Those tests are not hardware end-to-end validation. Its source has not yet been committed to this repository. No device-specific state or raw logs are included in this document. Keep baseline files, runtime receipts, management tokens, private keys, and vendor-source evidence out of the public repository.
