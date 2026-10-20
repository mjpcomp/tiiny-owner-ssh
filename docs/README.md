# Documentation guide

## Current guidance

- [Start here](../README.md): what the tool does, why to use it, prerequisites and the correct path for new versus returning users.
- [Usage](USAGE.md): key setup, original-state backup, check/install/restore, arguments, SSH/PuTTY and recovery limits.
- [Hardware](HARDWARE.md): sanitized observations from the inspected system, separate from advertised specs and unresolved questions.
- [Validation](VALIDATION.md): exactly which Windows/device paths and synthetic tests were exercised.
- [Project state](../PROJECT_STATE.md): current source preservation, implementation scope and outstanding work.

The end-user entry point is tiiny.cmd or tiiny.py. Internal/advanced files are explained in the README; their presence is not an invitation to run every script.

## Historical development checkpoints

These preserve the sequence of work, not current setup instructions. Earlier statements such as code not yet imported or installation not yet tested are superseded by the current guidance above.

- [Initial verified backup](VALIDATED_CHECKPOINT.md)
- [No-op restore rehearsal](PAIRED_REHEARSAL_RESULTS.md)
- [First real install/restore cycle](INSTALL_RESTORE_VALIDATED.md)

Do not copy old diagnostic routes, recreate a baseline or repeat device-changing tests merely because an earlier checkpoint describes them. Never publish runtime state or raw vendor-source evidence with documentation.
