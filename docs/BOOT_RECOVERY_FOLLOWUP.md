# EFI boot and A/B comparison follow-up

Recorded 2026-10-20 on one authorized Tiiny setup. Read after [storage, USB and recovery observations](STORAGE_USB_RECOVERY.md). This qualifies that earlier note's then-undecoded EFI state. It is not a factory-reflash procedure or a tested recovery backup. Serial-bearing descriptions, partition GUIDs, optional EFI arguments, raw variables and vendor source are omitted.

## Observed firmware state

- SecureBoot reported 1; SetupMode reported 0. This is firmware-reported Secure Boot state, not independent attestation of every boot component or proof of Linux root/AVB verification.
- BootCurrent was Boot0001, labelled Linux S1 Loader.
- BootOrder was Boot0000, Boot0001, Boot0003. No BootNext value was reported.
- Boot0000 was labelled UiApp. Both Boot0000 and Boot0001 used media device-path nodes 04/07 and 04/06, corresponding to firmware-volume and firmware-file references, not an ordinary disk pathname.
- Boot0003 described the NVMe device; its full serial-bearing description is deliberately not reproduced.

BootOrder is a configured preference, not a trace of attempted entries. An active load-option bit does not identify the currently executing entry. Firmware-volume references do not locate the underlying physical firmware storage or establish what the S1 loader subsequently loads. An NVMe-only image must not be assumed to include all firmware and its state.

PlatformRecovery0000 was labelled Default PlatformRecovery and contained the file path \\EFI\\BOOT\\BOOTAA64.EFI. PlatformRecovery0001 was labelled Debian boot and contained \\EFI\\DEBIAN\\GRUBAA64.EFI. No hard-drive partition reference was decoded for these recovery entries, so the paths alone do not assign them to an internal partition or USB device.

BOOTAA64.EFI is the conventional AArch64 fallback-loader filename, not evidence of a Tiiny-specific flashing application. Recovery-entry presence does not prove the target exists on searched media, is trusted, can boot, or restores the device. No entry was selected or executed. Do not disable Secure Boot or set recovery/flash flags merely to test a hypothesis.

## Root-slot identity comparison

Read-only debugfs requests for /usr/lib/os-release on root A (p3) and root B (p4) both returned Debian GNU/Linux 12 (bookworm). This establishes matching base OS identity only. It does not compare kernels, platform releases, package sets, shared overlays, boot policy or all filesystem contents. Neither slot was established as a development/programming environment.

## Read-only FAT inspection

mdir was unavailable; no package was installed. Known FAT partitions p1, p2 and p10 were temporarily mounted with ro,nosuid,nodev,noexec,noatime at a unique /run location. Read-only options were checked, targeted files were inspected and each partition was unmounted. Mount-table changes and system logging mean this was not a forensic zero-change operation, but no partition writes or loader execution were requested.

| Partition | Direct observations |
| --- | --- |
| p1, configured boot A | Top-level EFI and GRUB directories; EFI/BOOT/BOOTAA64.EFI present, 1300568 bytes |
| p2, configured boot B | Top-level EFI and GRUB directories; EFI/BOOT/BOOTAA64.EFI present, 1300568 bytes |
| p10 | No top-level directories shown; neither searched EFI loader path present |

EFI/DEBIAN/GRUBAA64.EFI was absent from all three inspected partitions. This does not establish that its recovery entry is invalid or that the file cannot exist on other media. No top-level directories on p10 does not mean no root-level files or an empty partition; its purpose and RAUC filesystem-type mismatch remain unresolved.

### Loader digests

SHA-256 of EFI/BOOT/BOOTAA64.EFI:

```text
p1: f924c3840f66663b2e5ba5959cc8b748e58dac4c318d1fc279b4da01e4d00709
p2: 9ca2c149188b806396abcab341332a34727b8b0bdf09fd831afb15a4ca1dbdb6
```

The files have equal size but different contents. Therefore these boot partitions are not exact duplicate copies at this file-content level. The reason is unestablished: a digest is not a version identifier, signature verification or integrity assessment. The binaries were not yet identified as GRUB, shim, a custom loader or another implementation. Embedded GRUB configuration is a possible mechanism in that software family, not a finding about these files.

Preserve both boot partitions and their associated root/verification partitions in recovery planning. Do not replace one loader with the other, deduplicate partitions or test bootability by switching slots. A/B layout is consistent with paired update slots, not a backup against shared-disk failure or a verified emergency fallback.

## Next-work checklist: planned, not completed

1. Identify both EFI binaries with existing static file-inspection tools; list boot-file names/sizes and find configuration files under EFI/GRUB. Do not run binaries or source configurations.
2. Compare selected configuration references, kernel identifiers and platform release/package metadata across the paired slots. Hash chosen corresponding files before considering large whole-partition reads. Treat identifiers and boot arguments as private until reviewed.
3. Identify the encryption format and unlock dependencies for userdata_crypt without printing keys; establish p11 and lower-level boot-control metadata roles. The p5 binary reference remains a lead, not permission to initialize metadata.
4. Verify a larger USB destination's actual free bytes, identity,filesystem and write/read-back. Source NVMe size is 1024209543168 bytes; the small test stick cannot hold its uncompressed image.
5. Establish a supported offline/rescue and restore route, including ARM64 hardware support and the current Secure Boot trust constraints. A normal live raw copy is not automatically application-consistent or a tested recovery image.
6. Plan private application/configuration exports and preservation of relevant boot/EFI/encryption metadata. No whole-disk, EFI or encryption-header backup has been completed, and no bare-metal restore has been demonstrated.

Carry forward the custom-backend warning: aibox-bootloader get-current marks boot success and updates saved state. Saved good files are not integrity validation. Do not invoke RAUC/boot getters as guaranteed read-only, set boot/recovery variables, call initialization or slot-changing utilities, flash firmware, reboot for experiments, or overwrite the only working system.

Publish sanitized findings only. Keep firmware payloads, vendor implementation, raw EFI dumps, images, credentials, identifiers and private application data out of GitHub.
