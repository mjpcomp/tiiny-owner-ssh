# Documentation guide

## Current guidance

- [Start here](../README.md): what the tool does, why to use it, prerequisites and the correct path for new versus returning users.
- [Usage](USAGE.md): key setup, original-state backup, check/install/restore, arguments, SSH/PuTTY and recovery limits.
- [Hardware](HARDWARE.md): sanitized inventory from the inspected system, separate from advertised specs and unresolved questions.
- [Accelerator activity follow-up](ACCELERATOR_ACTIVITY.md): later model allocations, observed runtime access, both cores reaching 100%, sampled board power up to 14.86 W, limitations and untested native API follow-up. This supersedes the earlier inventory's unresolved utilization/power notes only as explicitly described, not its unmeasured performance or thermal limits.
- [Validation](VALIDATION.md): Windows/device paths and synthetic tests exercised through the inventory stage; read the activity follow-up for subsequent workload observations.
- [Project state](../PROJECT_STATE.md): source preservation, implementation scope and outstanding work.

The end-user entry point is tiiny.cmd or tiiny.py. Internal/advanced files are explained in the README; their presence is not an invitation to run every script. Later workload observations do not change the SSH engines or establish broader restore/firmware compatibility.

## Historical development checkpoints

These preserve the sequence of work, not current setup instructions. Earlier statements such as code not yet imported or installation not yet tested are superseded by the current guidance above.

- [Initial verified backup](VALIDATED_CHECKPOINT.md)
- [No-op restore rehearsal](PAIRED_REHEARSAL_RESULTS.md)
- [First real install/restore cycle](INSTALL_RESTORE_VALIDATED.md)

Do not copy old diagnostic routes, recreate a baseline or repeat device-changing tests merely because an earlier checkpoint describes them. Never publish runtime state or raw vendor-source evidence with documentation.
