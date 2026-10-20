# Usage guide

[Start page](../README.md) | [Documentation index](README.md) | [Hardware](HARDWARE.md)

This guide is for the current snapshot on an authorized device, not a universal Tiiny compatibility promise. Use the README's Windows/Python setup first. Keep all runtime files together and TiinyOS closed while its stored token is read. Odysseus supplied the tested cached SearXNG helper image on the inspected setup; the platform report volume is a separate prerequisite. Installing Odysseus is ordinary application deployment, not part of the SSH file rollback.

## First-time setup

### Create or preserve the owner key

The default key is %USERPROFILE%\.ssh\tiiny_owner_ed25519 with its .pub file. If you already used the tool, preserve that pair and the original baseline. Do not overwrite the key or generate a different pair to work around an error.

For a new setup only:

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" -Force | Out-Null
ssh-keygen -t ed25519 -C tiiny-owner -f "$env:USERPROFILE\.ssh\tiiny_owner_ed25519"
```

Use a passphrase. If ssh-keygen asks to overwrite an existing file, cancel and inspect it. The installer accepts an interactive LOCAL key-passphrase prompt; it does not require a root device password.

### Preview locally

```powershell
.\tiiny.cmd check --dry-run
```

Enter the device IPv4 address when prompted. Dry-run displays the invocation without executing the engine. Local paths/IPs may appear; sanitize screenshots or output before sharing.

### Back up the original state

```powershell
.\tiiny.cmd backup
```

Enter the IP, then type BACKUP. The tool creates temporary management resources and a container with a read-only host mount. It does not intentionally change SSH files or reload SSH. It records the selected files' existence, bytes, uid/gid and permissions, verifies local read-back/integrity, and checks that the owner key is rejected before installation.

The baseline directory defaults to %LOCALAPPDATA%\TiinyOwnerSSH\device-baseline. It contains baseline.json, known_hosts, ssh_config and receipts/diagnostics. Open it with:

```powershell
explorer.exe "$env:LOCALAPPDATA\TiinyOwnerSSH\device-baseline"
```

Preserve ALL of it and a private second copy. Do not post its contents or copy it into the repository. Backup refuses an existing baseline and may refuse leftover trust files from a failed attempt. Diagnose a failure; do not delete state blindly to force another backup. Never back up the installed state as a replacement original baseline.

### Inspect the state

```powershell
.\tiiny.cmd check
```

Type CHECK. Before first installation, expect baseline state true, installed state false, native service enabled, listener verified and cleanup passed.

| Result | Meaning |
| --- | --- |
| Baseline true; installed false | Managed state matches the recorded original |
| Baseline false; installed true | Managed state matches the expected installed configuration; not a corrupt backup |
| Baseline integrity error, unexpected state, or cleanup warning | Stop and inspect the output/state; do not force installation |

Check does not grant access. It uses temporary resources and a read-only host mount, so it is not a zero-trace forensic operation.

### Install only when ready

```powershell
.\tiiny.cmd install
```

Type INSTALL. Installation mounts the host read/write and shares its PID namespace. It adds the owner key/drop-in, validates syntax/effective default policy/state, signals the verified listener and verifies a fresh root SSH login. It does not enable/start/restart the native SSH service.

The intended root policy is prohibit-password (also displayed by OpenSSH as without-password). Existing default authorized-key files remain searched. Root password/keyboard-interactive authentication is not enabled, but other already-authorized root keys may also become usable.

If installation or the final login fails, restoration through management is attempted. That attempt can fail or be interrupted. Never assume a failed run made no changes. Keep the baseline and all receipts, review cleanup, and stop before further changes if the outcome is unclear.

## Returning users

Use the same original key, target and state directory. You can run check, install or restore without repeating backup. The tool refuses changed target identity/configuration and has no force-overwrite option. Current per-device access state is private; use check rather than a public project status document.

## Restore

When you intend to remove the access added by this tool:

```powershell
.\tiiny.cmd restore
```

Type RESTORE. Restore uses management access and the saved public key, not the new root session/private key. It checks expected state, restores recorded file bytes/metadata or removes newly created files, validates root policy, reloads when necessary and verifies a fresh owner-key rejection.

It refuses unrelated edits and does not recursively delete unrelated directory contents. A valid native listener/configuration and working management path are still required. Close separately opened SSH sessions yourself; already-established sessions are not terminated.

After restoration, run check again. Expect baseline state true, installed state false, root login policy no and successful cleanup. A no-op restore before installation is not proof of reversing changes. A real install/restore cycle and final check were completed on the inspected device.

## Arguments and menu

```powershell
.\tiiny.cmd
.\tiiny.cmd check
```

No action opens a menu whose default is check. An omitted IP prompts; the tool does not scan for devices or silently remember an address. To supply an address explicitly:

```powershell
$DeviceIP = Read-Host 'Tiiny IPv4 address'
.\tiiny.cmd check --ip $DeviceIP
```

A positional address is also supported after the action. Override --state-dir or --key only intentionally; the engine validates the saved baseline/key. Use --dry-run to inspect invocation. The shortcut prefers .venv\Scripts\python.exe if present, otherwise python on PATH. You may call the selected interpreter with tiiny.py directly.

The engine still requests CHECK/BACKUP/INSTALL/RESTORE; the launcher does not bypass confirmations. On Ctrl+C the launcher waits for engine interrupt handling rather than killing it. Repeated interrupts or closing the terminal can still disrupt cleanup/recovery.

Advanced direct entry points remain:

```text
python tiiny_backup_ready.py backup DEVICE_IP --state-dir DIRECTORY
python tiiny_access.py check DEVICE_IP --state-dir DIRECTORY
python tiiny_access.py install DEVICE_IP --state-dir DIRECTORY
python tiiny_access.py restore DEVICE_IP --state-dir DIRECTORY
```

Do not run tiiny_owner.py directly. Its required shared functions remain, but the original discovery route is unsupported on the tested setup. Do not delete/move imported helpers for cosmetic cleanup.

## Connecting after installation

```powershell
$DeviceIP = Read-Host 'Tiiny IPv4 address'
$StateDir = Join-Path $env:LOCALAPPDATA 'TiinyOwnerSSH\device-baseline'
ssh -F "$StateDir\ssh_config" -i "$env:USERPROFILE\.ssh\tiiny_owner_ed25519" -p 3588 -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$StateDir\known_hosts" "root@$DeviceIP"
```

For PuTTY: import the existing private key (not its .pub) using PuTTYgen's Conversions > Import key, retain passphrase protection and save a PPK copy. Do not generate a new pair. Configure root, port 3588, the device IP and that PPK under SSH authentication credentials. Compare the Ed25519 HOST-key fingerprint before accepting it:

```powershell
ssh-keygen -l -E sha256 -f "$StateDir\known_hosts"
```

The host key is not your owner login key. Keep the original OpenSSH key and the PPK private. Both clients use the same underlying owner key; restore revokes the added device access for both.

## Security and recovery limits

Management uses HTTP without TLS, including the bearer token and bridge code. Use a trusted network. Initial SSH host-key trust derives from the same management channel. Temporary resources can have host write access and PID visibility; cleanup checks are not a guarantee through every failure.

Restore depends on the baseline, paired token/API, cached helper image, report volume and healthy listener/configuration. Removing them may prevent tool-based recovery. Address/identity/firmware changes may be refused; do not edit a baseline to bypass guards. Restore before firmware updates where feasible.

This restores selected configuration, not a factory image, logs/history, full metadata, firmware recovery or warranty status. ACLs, xattrs, timestamps and overlay internals are not comprehensively backed up. Default sshd checks do not simulate every Match context; actual login/rejection tests matter. Reboot persistence, firmware updates and real interrupted-failure recovery remain unvalidated.

Never publish tokens, keys, PPKs, app databases, runtime JSON, backup contents, raw logs, identifiers or vendor-source excerpts. Ignore rules cannot prevent all disclosure. Do not run reset/update/stress commands just for inventory.
