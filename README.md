# Tiiny Owner SSH

Unofficial experimental Windows tooling for owner-managed root SSH, with an original-state backup and a paired restore procedure. Use only on authorized devices and a trusted network. Not affiliated with Tiiny.

## What works and what changed

The seven engine modules are the owner's hardware-tested snapshots: backup, check, real root SSH installation, real restoration, fresh owner-key rejection, and a final baseline-state check succeeded on one setup. Cleanup checks passed.

The new tiiny.py launcher adds an action menu, optional IP prompting, default state directory, argument validation and dry-run. It delegates to those engines in a separate process using the same Python interpreter. It does not change their device logic or bypass typed confirmations. The Windows tiiny.cmd shortcut prefers a local .venv, otherwise python on PATH.

The launcher has 16 mocked unit tests; the host-state engine has 16 synthetic POSIX regression tests. All 32 passed in the Linux build environment. The new launcher/batch shortcut have not yet been device-tested on Windows. Validate --dry-run first. The seven original modules were compared with the owner's attachments by Git blob hash and matched byte-for-byte.

## Setup

Prerequisites: Python 3.13 and Windows OpenSSH client/ssh-keygen. The tested client was Windows 11 AMD64 with Python 3.13.15. WSL is not required; Windows ARM64 is unvalidated.

Clone/download the repository, open PowerShell in its root, then:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
```

Pair the TiinyOS Windows app with the device, then exit the app completely before token reading. The tested app was 1.0.1; device platform container names included 0.1.35, which is not a verified firmware version.

The cached registry.tiiny.cloud/wa-odysseus-searxng:v0.1 image and existing aibox_connectors_config volume must already be available. The tool requests pull_policy: never; it does not install an app or fetch a replacement image. This prerequisite is not guaranteed on every Tiiny.

## Easier commands

```powershell
.\tiiny.cmd
.\tiiny.cmd check
.\tiiny.cmd install
.\tiiny.cmd restore
```

No arguments opens a menu. Omitted IP prompts for the device IPv4 address. Check is the menu default; install is never chosen automatically.

Alternatively use python tiiny.py, or the venv interpreter explicitly. The launcher supports a positional IP or --ip, --state-dir and --key. For example:

```powershell
python .\tiiny.py check --dry-run
```

Dry-run prompts as needed and displays the engine invocation; it does not launch the engine, contact the device, or create state files. It does not prove dependency/device readiness. Output may include local usernames, paths and target IPs: review before sharing.

The default Windows state directory remains %LOCALAPPDATA%\TiinyOwnerSSH\device-baseline, compatible with existing backups. No IP is silently saved or inferred. A command-line override is passed through explicitly.

## Key and backup first

Keep an existing owner key pair. Do not regenerate it or overwrite a baseline. For a new setup only:

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" -Force | Out-Null
ssh-keygen -t ed25519 -C tiiny-owner -f "$env:USERPROFILE\.ssh\tiiny_owner_ed25519"
```

Choose a passphrase. Then create the original-state backup:

```powershell
.\tiiny.cmd backup
```

The engine asks for BACKUP. This creates temporary resources with a read-only host mount; it does not intentionally edit SSH files or reload SSH. Preserve the entire state directory and a private second copy. It includes baseline.json, known_hosts, ssh_config and receipts. It is outside the checkout and must never be committed.

Backup refuses an existing baseline. Missing baselines block check/install/restore. Do not delete state to force a retry; diagnose failures. Open the default directory with:

```powershell
explorer.exe "$env:LOCALAPPDATA\TiinyOwnerSSH\device-baseline"
```

## Check, install, restore

Run each operation separately. The engine still requires CHECK, INSTALL or RESTORE. Before first install, check should report baseline state true, installed state false, enabled native service, verified listener, and clean resource removal.

Install adds the owner public key and drop-in, validates syntax/effective default policy/state, signals the verified native listener, and verifies a fresh root login. It does not enable/start/restart native SSH. Existing default authorized-key files remain searched; previously authorized root keys may also become usable while root key login is allowed.

Install/restore require a temporary read/write host mount and host PID namespace. On install or final-login failure, restoration is attempted, not guaranteed. The launcher waits for the engine during terminal interrupts rather than forcibly killing it; closing the terminal or repeated interruption can still disrupt recovery.

Restore uses management access and the saved public key; it does not require the private key. It restores the exact expected managed state and checks fresh key rejection. Conflicting external edits are refused. Existing SSH sessions are not terminated; close them yourself. After restore, check should report baseline state true, installed state false, and root login policy no.

## Direct engine entry points

These remain available for existing automation:

```text
python tiiny_backup_ready.py backup DEVICE_IP --state-dir DIRECTORY
python tiiny_access.py check DEVICE_IP --state-dir DIRECTORY
python tiiny_access.py install DEVICE_IP --state-dir DIRECTORY
python tiiny_access.py restore DEVICE_IP --state-dir DIRECTORY
```

Do not run tiiny_owner.py as a CLI. Despite its legacy name it remains a required internal module. Its original deployment-discovery route failed on the tested setup and is bypassed by the verified wrappers. Removing it now breaks imports. Extracting shared code/removing obsolete paths is a separate future refactor, not part of this launcher update. Keep all engine files together.

## SSH and PuTTY

After successful installation, use root and port 3588 with the existing key. OpenSSH example:

```powershell
$DeviceIP = Read-Host 'Tiiny IPv4 address'
$StateDir = Join-Path $env:LOCALAPPDATA 'TiinyOwnerSSH\device-baseline'
ssh -F "$StateDir\ssh_config" -i "$env:USERPROFILE\.ssh\tiiny_owner_ed25519" -p 3588 -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$StateDir\known_hosts" "root@$DeviceIP"
```

For PuTTY, import the same private key into PuTTYgen and save a protected PPK copy; do not generate a different pair. Compare PuTTY's Ed25519 host fingerprint with ssh-keygen -l -E sha256 -f on the saved known_hosts file. Never upload private keys or PPKs.

## Limits and privacy

Management HTTP carries the bearer token without TLS. Initial SSH host-key trust derives from that management channel. Restore depends on the baseline, paired token, API, cached image, report volume and valid listener/configuration. Do not prune/remove them and assume recovery remains available.

This is selected configuration rollback, not a factory reset, log erasure, warranty approval or complete metadata backup. ACLs, xattrs, timestamps and overlay internals are not comprehensively preserved. Firmware matching is limited; changes may be refused. Restore before firmware updates where feasible and never hand-edit the baseline to bypass checks.

Default sshd checks do not simulate every Match context. Actual login/rejection matters. Reboot persistence, firmware-update behavior and real interruption recovery remain unvalidated.

Do not commit tokens, databases, baseline/runtime JSON, raw logs, private keys, serials, MACs or vendor-source excerpts. Ignore rules are not a guarantee. See docs/HARDWARE.md and PROJECT_STATE.md. Earlier checkpoint documents are historical, not current instructions.

## Tests

```text
python -m unittest discover -s tests -v
```

Launcher tests use temporary placeholder files and mocked child processes. Host-state tests use POSIX temporary-file operations with mocked system/SSH checks and signaling; transaction ownership is mapped to the test user. The combined suite was run on Linux. Host-state tests are POSIX-only, but that does not make WSL a Windows runtime requirement. They are not end-to-end API, real reload, firmware or disaster-recovery tests. The Windows batch shortcut was reviewed but not executed in the build environment.

No project license is assigned. Development began from an owner-supplied bootstrap whose original redistribution license has not been established. No vendor-source evidence is reproduced.
