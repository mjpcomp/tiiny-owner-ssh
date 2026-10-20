# Current project state

Updated 2026-10-20. README.md, docs/USAGE.md and docs/VALIDATION.md are current guidance. Other checkpoint files retain historical stage descriptions.

The seven original engine modules are committed, matched the owner's working uploads by Git blob hash, compiled and had all local import targets present. cramjam was unavailable in the Linux build environment; the owner tested that dependency and the workflow on Windows AMD64.

The owner completed original-state backup, check, actual install with fresh root SSH login, actual restore with fresh owner-key rejection, and final baseline-state check; temporary-resource cleanup passed. On 2026-10-20, the new Windows shortcut's system-Python fallback, omitted-IP prompt, default state-directory reuse, dry-run and live check also passed. Launcher-driven install/restore, the Windows .venv branch and menu remain unvalidated on hardware. See docs/VALIDATION.md for precise scope.

32 mocked/synthetic Linux tests passed. They do not establish real failure/interruption recovery, reboot persistence, firmware-update compatibility or universal device support.

The owner confirms that the tested SearXNG helper image came from installing Odysseus through TiinyOS. The tool uses a new helper container from the cached image and a separate existing connector-report volume; it does not provision Odysseus or silently pull another image. Future package versions may not supply the pinned image.

Normal entry point: tiiny.cmd / tiiny.py. Advanced engines remain directly callable. tiiny_owner.py is still an internal dependency; removing its legacy CLI/shared-code coupling requires a separate tested refactor. No runtime changes are included in this documentation update.

Baseline and runtime state, tokens, private keys, raw output and vendor-source evidence stay private. Preserve the original baseline rather than regenerate it. Current per-device access state is not tracked publicly. Hardware observations and unverified capacities are documented separately in docs/HARDWARE.md.
