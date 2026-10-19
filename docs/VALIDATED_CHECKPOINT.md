# Verified backup checkpoint

Updated: 2026-10-19. This document supersedes older validation-status statements in PROJECT_STATE.md where they conflict. It does not claim that installation or restoration is ready.

## Confirmed by owner-run tests

- Native Windows token parsing and authenticated connector-list access work.
- MCP connector creation requires a nonempty description on the tested API.
- Temporary connector creation, Python tool execution, deletion, and absence verification work.
- The original device-local deployment route on port 5555 returns HTTP 404 in the tested connector environment and must not be assumed available.
- The installed Windows client reports application version 1.0.1. Reviewed client evidence identifies agent-services.api.tiiny with /api/services as the application service-management URL.
- Authenticated GET /api/services through that virtual hostname returns Compose YAML definitions. These identify application stacks, not the platform connector image.
- An isolated test of registry.tiiny.cloud/wa-odysseus-searxng:v0.1 ran Python 3.14, found a chroot executable, and wrote a report through the existing aibox_connectors_config volume that the connector could read. The test requested pull_policy: never.
- Temporary service creation and startup through the services virtual host succeeded. The tested startup route is POST /api/services/{id}/start/stream.
- A corrected backup-only runner used that image, a read-only host mount, a read-only container root, no container network, and no host PID namespace.
- The backup completed, saved the original managed state locally, and verified it by reading it back.
- The owner public key was offered in a fresh SSH authentication probe and rejected before installation.
- Temporary service absence, temporary report absence, and temporary connector absence were verified after the successful backup.
- No owner SSH key or configuration changes have been installed by this workflow.

## Important service-state finding

Chrooted systemctl is-enabled checks for ssh.service, sshd.service, ssh.socket, and sshd.socket all returned exit status 1 with a bus-unavailable diagnostic. This does not establish that those units are disabled. The backup path was changed to record diagnostics rather than require enablement. The install/restore enablement guard has not been validated in this environment.

The next read-only preflight should use the host systemctl with --root=/ inside the host chroot to inspect unit-file enablement offline, and verify the relevant native SSH process and reload assumptions. Do not enable, start, or restart a unit just to satisfy the original script.

## Code preservation status

The public repository contains the original reviewed token/authentication checkers and documentation. The successful backup used additional locally generated and patched preview files that have not yet been imported. The owner should supply the current tiiny_owner.py, tiiny_host_state.py, and tiiny_backup_ready.py for review and consolidation. This document is not a backup of those source files.

## Remaining gates before installation

1. Preserve and review the exact working source.
2. Keep the immutable baseline and a private second copy outside the repository.
3. Resolve offline service enablement and native SSH reload assumptions without changing service state.
4. Adapt both install and restore to the tested services API and image.
5. Retain pre-change identity/content/metadata comparisons, baseline integrity checking, conflict refusal, SSH configuration validation, and temporary-resource cleanup.
6. Review the restore implementation before installing. End-to-end removal of added owner access remains untested.
7. After an eventual restore, test that the owner public key is rejected on a fresh connection. Existing separately opened SSH sessions must be closed separately.

## Scope and privacy

Restore targets the original managed file contents, existence, numeric ownership, and permissions. It is not a factory image, log erasure, a complete filesystem-metadata backup, or a warranty guarantee. Firmware matching remains limited. Never publish baseline files, runtime JSON, raw API responses, management tokens, private keys, application databases, or vendor-source excerpts.
