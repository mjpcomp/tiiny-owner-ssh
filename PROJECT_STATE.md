# Project checkpoint

Updated: 2026-10-19.

## Validated on the owner's Windows laptop

- Windows 11 Pro with Python 3.13.15, AMD64, 64-bit.
- Windows OpenSSH client and ssh-keygen are available.
- cramjam 2.14.0 installed successfully from a Windows binary wheel.
- TiinyOS app database exists at %APPDATA%\TiinyOS\Local Storage\leveldb.
- Local token checker found and decoded a nonempty tiiny_auth_key candidate without displaying or saving it.
- Authenticated GET /v1/mcp/servers with Host: connector.api.tiiny returned HTTP 200 and a JSON list containing one item. Write permission is not established.
- Device TCP ports 80 and 3588 are reachable.
- A local Ed25519 owner key pair was generated at %USERPROFILE%\.ssh\tiiny_owner_ed25519. Whether a passphrase was set is not recorded.

## Not done

- The device-changing bootstrap has NOT been run in this workflow.
- No owner public key or owner SSH drop-in has been installed by this workflow.
- Backup-first installation, restore, and post-restore access rejection are NOT implemented or tested.
- Earlier chat-generated scripts exist on the owner's laptop, but their source has not been imported into this repository. Repository documentation is not a backup of those scripts.
- The earlier bootstrap lacks a durable pre-change backup and must not be used for the agreed reversible workflow.

## Known source approach

The supplied bootstrap creates a temporary stdio MCP connector, discovers the existing connector image through device-local port 5555, and creates a temporary Compose service through device-local port 8880. The service mounts the host filesystem read/write and shares the host PID namespace. It checks overlay-backed /etc and an enabled ssh service, adds an owner public key and sshd drop-in, validates sshd configuration, reloads the daemon, and tests root SSH on port 3588. Temporary resource cleanup is best-effort.

## Required pre-change backup

Capture original existence, exact bytes, numeric ownership, and permissions for:

- /etc/ssh/owner_authorized_keys/root
- /etc/ssh/sshd_config.d/00-owner-access.conf
- /etc/ssh/owner_authorized_keys (directory existence and metadata)

Inspect path types and reject unexpected symlinks or unsupported layouts before writing. Record device identity, firmware version when available, baseline key-authentication result, and created resource identifiers without storing tokens. Export the backup to the laptop and verify its integrity before changing SSH files. Never overwrite an existing baseline during a rerun.

## Installation and restore requirements

1. Validate inputs and confirm the owner key does not already authenticate; distinguish authentication rejection from transport failure.
2. Capture and verify the durable local backup before any SSH file changes.
3. Add only the intended public key and configuration. Validate before reloading.
4. Allow interactive local private-key passphrase entry during SSH verification.
5. Track and verify temporary connector/service cleanup, including partial-failure cases.
6. Restore original files and metadata, deleting files that originally did not exist. Remove a newly created directory only if empty.
7. Detect post-install file changes and stop for review instead of overwriting unrelated changes.
8. Validate restored configuration, reload SSH, close tool-owned sessions, and test a fresh connection using only the owner key. Success means authentication rejection, not a timeout.
9. Refuse blind restoration across firmware or device-identity mismatches. Restore before updating firmware where possible.

## Limits

Removing the added key does not disable vendor-managed SSH access. Log erasure and trace-free factory restoration are out of scope. Warranty policy, updater checks, recovery behavior, and persistence across firmware updates remain unverified. Baseline host inspection may itself require temporary management resources.

## Next implementation step

Import and review the existing checker source, add parser and failure-path tests, then implement a backup-only preflight before enabling install or restore. Do not claim end-to-end reversibility until it has been tested on the device.
