# Successful hardware install and restore cycle

Updated: 2026-10-19. These owner-run results supersede the earlier installation/restoration readiness statements in docs/PAIRED_REHEARSAL_RESULTS.md and docs/VALIDATED_CHECKPOINT.md. Earlier documents remain historical checkpoints.

## Actual installation

The owner ran the paired preview's install command using the existing immutable baseline. The command completed and verified a fresh native SSH login as root, reporting uid=0(root) and gid=0(root). The owner supplied the local private-key passphrase interactively.

Temporary service absence, temporary report absence, and temporary connector absence were verified. Cleanup checks passed.

## Actual restoration after installation

The owner subsequently ran restore using the same baseline. This was a real reversal after a successful installation, not the earlier no-op rehearsal.

The command reported that managed state matched the original baseline. A fresh authentication probe offered the owner public key and received authentication rejection. Temporary service, report, and connector cleanup checks passed.

The last reported device state is restored. The owner SSH access added by this workflow is not currently enabled. Existing separately opened SSH sessions, if any, must be closed separately.

## What this establishes

The normal installation and configuration-restore path has been exercised successfully on the owner's current setup. The earlier backup, unit-file inspection, listener checks, and paired check/no-op restore results are recorded in the preceding checkpoint documents.

This is configuration rollback for the managed owner key, drop-in, and directory metadata, not a factory-image restoration, history erasure, or warranty determination.

## Not yet validated

- Automatic restoration after a real installation or final-login failure.
- Recovery after interruption, network loss, partial writes, conflicting changes, or failed rollback.
- Persistence across reboot.
- Behavior across firmware updates or on different devices/versions.

A final read-only check after the real restore is recommended to confirm baseline state true, installed state false, and root login policy no. Do not represent that additional check as completed until its output is supplied.

## Continued use and baseline handling

For continued owner SSH access, reinstall with the same verified baseline. Do not generate a replacement baseline from the installed state. Preserve the entire private state directory and a secure second copy. Restore before firmware changes where feasible; do not assume restoration across changed firmware/configuration will be accepted.

## Source preservation and privacy

The paired implementation is still a locally supplied preview; the actual tested tiiny_access.py and tiiny_access_host.py should be reviewed and imported in a separately approved source commit. This results document does not itself preserve those source files.

No device IP, username, key fingerprint, private key, management token, raw output, baseline data, or vendor-source excerpts are included here. Keep all runtime state out of the public repository.
