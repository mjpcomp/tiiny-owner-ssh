# Tiiny Owner SSH

Enable owner-managed, key-based root SSH on a Tiiny device from Windows, with an original-state backup and a matching restore command.

For authorized administration, troubleshooting and system inspection. Uses the existing SSH server on port 3588; does not flash firmware or install a replacement SSH server. Unofficial and experimental, not affiliated with Tiiny.

## Start here

### 1. Prepare the device and Windows

- Tested client: Windows 11 AMD64, Python 3.13.15, Windows OpenSSH client/ssh-keygen. WSL is not required.
- Pair the TiinyOS Windows app with the target once, note its IPv4 address, then exit the app completely, including the tray instance, before token reading.
- On the tested setup, installing Odysseus through the TiinyOS application supplied the cached SearXNG helper image. No separate SearXNG installation was needed. The tool creates a NEW temporary helper container, not a command inside your existing app container.
- This version requires registry.tiiny.cloud/wa-odysseus-searxng:v0.1 and the separate existing platform volume aibox_connectors_config. It does not provision an app or pull another image. Future Odysseus versions may differ; this is not a universal compatibility promise.

If Odysseus is already installed, do not reinstall it just for this procedure. Installing an app changes application/container state and is not undone by the SSH restore.

Download this repository using GitHub Code > Download ZIP and extract it, or clone with Git. Open PowerShell in the folder containing tiiny.cmd and requirements.txt:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
```

### 2. Choose your path

| Situation | What to do |
| --- | --- |
| First use, no key/baseline | [First-time setup](docs/USAGE.md#first-time-setup): key, original-state backup, check, then install |
| Existing owner key and baseline | Preserve them. Use check/install/restore; do not create another baseline |
| Remove the access added by this tool | [Restore](docs/USAGE.md#restore), using the SAME original baseline |
| Only interested in the device internals | Read [hardware findings](docs/HARDWARE.md); no installation needed to read the notes |

Start with a local preview:

```powershell
.\tiiny.cmd check --dry-run
```

It prompts for the IP and shows the invocation without contacting the device or creating state files. Dry-run does not validate actual device/dependency readiness.

### 3. Use the launcher

```powershell
.\tiiny.cmd
```

No arguments opens a menu; check is the default, never install. To check directly:

```powershell
.\tiiny.cmd check
```

The IP is prompted when omitted. The engine still asks for CHECK, BACKUP, INSTALL or RESTORE; no confirmation is bypassed. [Full usage guide](docs/USAGE.md) covers each operation, explicit arguments, key setup and PuTTY.

The default private state directory is %LOCALAPPDATA%\TiinyOwnerSSH\device-baseline. Keep the WHOLE directory and a secure second copy. Never overwrite, regenerate or hand-edit the original baseline after installation. Keep private keys/PPKs private.

## What changes, and what is undo?

Install adds your public key and an SSH drop-in, validates configuration, reloads the existing listener and verifies a fresh root login. It does not enable root password authentication. Existing default authorized-key files remain searched, so previously authorized root keys may also become usable.

Restore returns the managed files' recorded bytes, existence, ownership and permissions to the baseline and checks fresh rejection of your owner key. It does not terminate already-open sessions. It is not a factory image, log erasure, full metadata restore, firmware recovery or warranty guarantee. Unexpected state is refused rather than overwritten.

Management uses HTTP without TLS and temporary containers; install/restore require host write access and PID visibility. Use a trusted network. Recovery attempts can fail. Keep the token/API, cached helper image, report volume and baseline available. Read the [security and recovery limits](docs/USAGE.md#security-and-recovery-limits) before installation.

## Tested versus untested

| Scope | Status |
| --- | --- |
| Underlying backup/check/install/real restore/fresh login and rejection/cleanup | Passed on one setup |
| Windows shortcut with system Python, IP prompt, default state reuse, dry-run and live check | Passed 2026-10-20 |
| Mocked/synthetic Linux tests | 32 passed: 16 launcher, 16 host-state |
| Windows .venv branch, action menu, launcher-driven install/restore on hardware | Not yet validated |
| Real interruption recovery, reboot persistence, firmware updates, other versions | Not established |

[Validation details](docs/VALIDATION.md). Device observations: Debian 12/aarch64, Linux 6.6.89, Windows app 1.0.1 and platform container name suffix 0.1.35. That suffix is not a verified firmware version.

## Hardware we found

AiBox SIT Board V0.1.2 / CIX Sky1-family; 8 Cortex-A720 + 4 Cortex-A520; approximately 32 GB host RAM; Houmo/XH2A driver v1.4.1 over PCIe 4.0 x4; Samsung 1 TB-class NVMe; RAUC A/B, read-only root and configuration overlays.

These are observations on our inspected setup, not universal specifications. Accelerator-local memory capacity is still unmeasured. [Hardware findings, software architecture and open questions](docs/HARDWARE.md).

## Repository guide

- Run tiiny.cmd / tiiny.py for normal use.
- tiiny_backup_ready.py / tiiny_access.py are advanced engine entry points.
- The other Python files are required helpers; keep them together. Do not delete tiiny_owner.py or run its old CLI: it is still imported, while its unsupported discovery path is bypassed by the wrappers. Removing it requires a separate tested refactor.
- [Usage](docs/USAGE.md), [hardware](docs/HARDWARE.md), [validation](docs/VALIDATION.md), [documentation index](docs/README.md), and [current project state](PROJECT_STATE.md) are current guidance. Other checkpoint documents are historical.

Do not publish tokens, private keys, app databases, backups, runtime JSON, raw device output or vendor-source excerpts. No runtime code is changed by this documentation update. No project license is assigned; the original owner-supplied bootstrap's redistribution license remains unresolved.
