# Tiiny Owner SSH

Unofficial native Windows tooling for owner-managed SSH access to a Tiiny device using its existing SSH service. Not affiliated with or endorsed by Tiiny.

## Current status

Documentation checkpoint only. No supported backup-first installer or restore command has been committed yet. Do not treat this repository as ready to install root access.

Read PROJECT_STATE.md before continuing development or testing.

## Scope

The intended workflow reads the paired Windows app's local management token, uses authenticated management APIs to bootstrap an owner public key, and verifies root SSH on port 3588. Installation must first export and verify a durable pre-change backup on the Windows laptop. Restoration must restore the affected configuration and verify that the owner key no longer authenticates.

The goal is configuration rollback and removal of the access added by this tool, not erasing logs, guaranteeing factory equivalence, or establishing warranty approval.

## Security

Use only on devices you own or are authorized to administer. The supplied bootstrap approach uses HTTP management requests and a temporary container with host filesystem write access. Use a trusted network.

Never commit management tokens, private keys, app databases, backups, raw API responses, or device-specific state. Store runtime data outside the repository. Ignore rules are safeguards, not secret scanning or access controls.

## Provenance

Development began from a Bash/Python bootstrap supplied by the owner. Its origin and redistribution license have not been established. No project license is assigned at this checkpoint.
