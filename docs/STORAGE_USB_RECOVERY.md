# Storage, USB and recovery observations

Recorded 2026-10-20 on one owner-administered Tiiny setup. Complements [hardware inventory](HARDWARE.md) and [accelerator activity](ACCELERATOR_ACTIVITY.md). This is sanitized evidence and a recovery-planning note, not a validated whole-system backup/restore procedure. No firmware change, slot switch, partition repair or reboot was requested during these inspections. Vendor source, raw EFI payloads, binary dumps, credentials and unit-specific identifiers are omitted.

## Storage layout

The internal NVMe reported 1024209543168 bytes. Root was ext4 mounted read-only from /dev/nvme0n1p4. /data was ext4 mounted read/write through /dev/mapper/userdata_crypt, backed by p12. The mapping establishes an encrypted block layer, not the encryption format, key origin or recovery unlock method.

| Partition | Observed size | Observed filesystem / configured role |
| --- | --- | --- |
| p1 | 512 MiB | FAT; RAUC boot slot A |
| p2 | 512 MiB | FAT; RAUC boot slot B |
| p3 | 16 GiB | ext4; RAUC root slot A |
| p4 | 16 GiB | ext4; RAUC root slot B, mounted / |
| p5 | 4 MiB | No filesystem identified; boot-control metadata candidate, not confirmed |
| p6 | 16 GiB | Active swap |
| p7 | 512 MiB | DM_verity_hash signature; RAUC rootfs_vbmeta A |
| p8 | 512 MiB | DM_verity_hash signature; RAUC rootfs_vbmeta B |
| p9 | 20 GiB | ext4; configured RAUC overlay slot |
| p10 | 2 GiB | FAT detected, but RAUC data.0 declares ext4; unresolved mismatch |
| p11 | 10 GiB | ext4; purpose unresolved |
| p12 | 936157453824 bytes | Backing partition for userdata_crypt and /data |

Partition signatures and names do not prove active dm-verity/AVB enforcement or filesystem integrity. Do not format p10 to reconcile the configuration mismatch. The earlier root/overlay observations do not by themselves establish the precise persistent backing of every configuration directory.

## USB-C external storage: tested successfully

The owner left the existing power connection unchanged and attached an existing NTFS USB stick to the unused connector. Before connection, only the internal Bluetooth device was shown in the USB tree. After connection:

- A USB disk appeared as /dev/sda with an NTFS partition /dev/sda1; these are session-specific names, not permanent destination identities.
- Disk size was 30765219840 bytes and partition size 30763122688 bytes.
- The mass-storage interface bound to usb-storage and negotiated 5000M (5 Gbit/s).
- Its root hub was displayed at 10000M; this does not establish the tested drive's throughput or a universal per-port maximum.
- Logical Type-C port1 changed from device/sink to host/source, correlating the tested physical connector with port1 on this setup.
- port0 remained device/sink and port2 remained host/sink. Logical numbering is not a physical label or a universal port mapping. The separate To PC connector's data-copy/boot capabilities were not established.

These observations confirm USB mass-storage enumeration. They do not establish USB boot, firmware recovery, internal-disk gadget export, every port's capability, or sustained drive power/transfer reliability.

### Filesystem write/read-back test

The running system exposed ntfs, ntfs3 and fuseblk support; NTFS-3G helpers were also installed. The test used ntfs3, not a newly installed driver.

After rechecking the USB transport, exact device sizes, filesystem type and absence of an existing mount, the existing NTFS partition was mounted read/write at a unique temporary /run directory with nosuid,nodev,noexec,noatime. The mount point was on tmpfs. The drive showed approximately 14 GiB available at the test snapshot; free space is not a permanent specification.

A uniquely named temporary file received 1 MiB of random data, was flushed with fsync, and was read back with matching SHA-256. Only that test file was deleted, and the temporary USB mount was cleanly unmounted. No formatting, filesystem repair or raw block-device output was used. Existing file contents were not targeted; mounting/writing can update filesystem metadata and system logs.

This validates a small Linux-to-USB filesystem write/read-back path. Immediate read-back may use caches. It is not independent media verification, a power-loss test, a speed benchmark or a long-duration backup qualification. The stick is far too small for an uncompressed image of the full NVMe. A future destination must have enough actual free space for the source's exact byte size plus overhead; matching advertised capacities are insufficient assurance. Do not assume encrypted sectors compress well.

## EFI observations

The EFI interface was present and efivarfs was mounted read/write. Directory entries included BootCurrent, BootOrder, Boot####, PlatformRecovery####, SecureBoot, SetupMode, security databases and vendor variables. Presence alone does not establish Secure Boot being enabled, a usable recovery image, a valid boot path or independent integrity verification. Standard entries were not decoded in this inspection.

A targeted read of AioPlatformVar reported:

| Metadata | Observation |
| --- | --- |
| Total efivarfs file size | 260 bytes |
| EFI attributes | 0x00000007 |
| Payload length | 256 bytes |
| Payload byte 2 | 0x00; the inspected vendor script labels it BootNextFlash |
| Payload byte-sum modulo 256 | 0x00; consistent with that script's stated checksum convention |

The attribute header is four bytes; 0x7 denotes nonvolatile, boot-service and runtime access. This payload check is not authentication or proof of valid firmware state. A zero byte at this offset does not rule out other update mechanisms.

A script named boot_next_flash was inspected as text, not executed. It sets the vendor flash-request field, writes EFI state and reboots; it is not a backup or safe inspection command. Do not invoke it to discover recovery behavior. Do not remove EFI immutability, replay arbitrary variables or change RecoveryFlag/boot selections merely to test recovery. Private preservation of selected metadata is not a tested EFI restoration procedure.

## RAUC custom backend: getters have side effects

The inspected configuration used bootloader=custom with /usr/bin/aibox-bootloader as its custom backend. Static review established:

- Every invocation performs directory setup and log rotation checks before dispatch; logs may be written/rotated and old log files deleted.
- get-primary prefers /var/rauc/settings/primary_slot, otherwise calls boot_control_avb and defaults to A unless it recognizes the B response.
- get-state returns a saved state, or good when its file is absent. A good result is not a bootability/integrity test.
- get-current calls boot_control_avb markBootSuccessful, queries the slot, writes a slot-state file as good, and defaults to A on unrecognized query output.

Thus get-current is not read-only, and other getters are not zero-write. RAUC status calls must not be described as guaranteed observation-only on this setup: depending on version/call path, they may invoke the configured backend. Earlier status output does not establish which calls occurred or whether an already-successful state changed. Do not attempt an uninformed reversal.

Direct file reads, bypassing the handler, reported primary_slot B, slot_A_state good and slot_B_state good. The saved B preference agreed with root mounted from p4, but the files do not independently validate either slot or the firmware's selected next boot.

## Lower-level boot metadata lead

/usr/bin/boot_control_avb was an ARM64 dynamically linked ELF with debug information and retained symbols. It was inspected as a file, not executed. Selected printable references included /proc/cmdline, boot.slot_suffix, boot-success/slot-control operation names and /dev/nvme0n1p5, alongside AVB-related symbols/messages.

The p5 reference makes that partition a credible boot-control metadata candidate. It does not prove the exact access path, format, offsets, write semantics or exclusivity of storage. AVB symbols do not prove active enforcement or that this device runs Android. Do not call initAvbMetaData, markBootSuccessful, slot-changing operations or guessed getters during inventory. Do not initialize or modify p5 to investigate it.

## Whole-system backup: still a planning task

The SSH baseline restores selected SSH state, not the system. No whole-NVMe image, EFI backup, encryption-header backup or bare-metal restore was performed here.

A recovery plan must account for:

1. Application data and persistent configuration, with an application-consistent export method.
2. Partition table and all relevant NVMe contents, not only the active root and /data.
3. Saved RAUC state and the lower-level boot-control metadata, once their locations/semantics are established.
4. Relevant firmware/EFI state that may exist outside the NVMe.
5. Encryption format, unlock dependencies and any device-bound recovery constraints, without exposing keys.
6. A supported offline/rescue environment, verified backup destination, integrity checks and a deliberate restoration plan.

A successful USB file test does not resolve live-system image consistency, firmware recovery, decryption after replacement, or bootability after restore. Do not take a live raw copy and call it a proven recovery image, do not write backups onto the source NVMe, and do not test restoration by overwriting the only working system.

Keep images, keys, EFI dumps, headers, raw evidence and application backups encrypted/private and off GitHub. Publish only sanitized observations and explicitly tested procedures. Outstanding questions include p5/p11 roles, detailed boot-control storage, EFI boot/recovery entry interpretation, Secure Boot state, data unlock mechanism, offline imaging access and tested restoration.
