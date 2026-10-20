# Hardware and platform observations

Observed on one owner-administered Tiiny system on 2026-10-19. Not universal specifications, a benchmark, a teardown or a warranty statement. Unique identifiers and raw output are omitted.

| Component | Observation |
| --- | --- |
| Board model / compatible | AiBox SIT Board V0.1.2 / cix,sky1 |
| CPU | 8 Cortex-A720 plus 4 Cortex-A520 logical CPUs |
| CPU policy maxima | A520 about 1.8 GHz; A720 groups about 2.2, 2.3, 2.5 and 2.6 GHz |
| Host RAM / swap | Approximately 32 GB installed, about 31 GiB Linux-visible; 16 GB-class NVMe swap |
| Accelerator | PCI 1f6b:0c00, driver houmo,xh2a, xh2a_drv v1.4.1 in the kernel's DKMS updates directory |
| Accelerator link | Current and maximum 16 GT/s x4: PCIe 4.0 x4, not measured throughput |
| SSD | Samsung MZAL81T0HFLB-00BL2, 1 TB-class NVMe, PM9C1a controller identification |
| Wireless | MediaTek MT7922 using mt7921e |
| Temperature snapshot | Roughly 49-53 C; not a thermal qualification |
| Host software | Debian 12, Linux 6.6.89-generic with lcfc-build package label, Python 3.11.2 |
| Docker | 27.3.1, overlay2, systemd cgroups, storage /data/docker |

Exact SoC SKU and Houmo card/module SKU are not independently certified. The build label does not establish a manufacturing relationship. Driver reference counts/device numbers are not utilization or memory measurements.

## Memory and accelerator tools

Vendor specifications describe 32 GB SoC-side plus 48 GB discrete-NPU-side memory. Only the host pool has been observed directly; accelerator capacity is unmeasured and is not ordinary CPU RAM. Specification: https://www.tiiny.ai/products/tiiny-pocket

Observed xh2a interfaces include control, IPU, system, DDR/SPM allocators, transfer, fast-memory, I2C, QSPI and RPMsg. Nodes were mode 0666; actual access may also depend on driver, device-cgroup and security checks. Do not dump/write character devices to investigate.

A vendor logger identifies /data/model/houmo_drv_xh2_v0.5.0/tools/hm_smi, querying -a and filtering DDR/Power. That wrapper creates/appends/rotates files in /data/log. Houmo also documents data/log output from the underlying query via XDG_DATA_HOME; it is not guaranteed zero-write. The directory version is not proof of SDK/firmware version. No SMI capacity/power output has been supplied. The wrapper source is not reproduced. Do not run download, update, reset or stress utilities for inventory.

## Boot and filesystems

RAUC identified AIBOX_HW_V1 and slot B as booted/selected; A and B were marked good. Recorded boot status is not independent integrity validation.

| Role | A | B, observed active |
| --- | --- | --- |
| Boot | nvme0n1p1 | nvme0n1p2 |
| Root | nvme0n1p3 | nvme0n1p4 |
| Root verification metadata | nvme0n1p7 | nvme0n1p8 |

Root was ext4 read-only on p4; /etc and /var were overlays. The large /data was ext4 read/write through userdata_crypt on the final large partition. Unlock policy and LUKS format are not established.

No active dm-verity mapping was reported. Hash partitions/read-only mounting do not establish active kernel verification, and no mapping does not rule out earlier boot verification.

RAUC data.0 referred to p10, not mounted /data. Its configured ext4 type differed from lsblk's vfat detection; unresolved, not a reason to format/repair. An inactive slot label does not authorize modifying it. cix_resume_prepare.service was failed with exit 255; cause/expected behavior remain unverified and it was not repaired.

## Software and containers

CIX GPU/media/firmware, ONNX Runtime, MNN and llama.cpp packages were installed; activity/functionality is unproven. Windows app version 1.0.1 and platform container name suffix 0.1.35 are separate observations, not a verified firmware version.

Core containers included compose-manager, tiiny_model, kb_service, tiiny-gateway, connectors, aibox, tiiny-backup and conversation-service. The application services API listed application stacks separately. connectors and compose-manager used host networking, explaining empty published-port listings. The original localhost deployment route returned 404 despite successful bridge execution.

connectors mounted /data/connectors plus a separate WhatsApp authentication volume. Do not publish its contents. tiiny_model and aibox were privileged; empty explicit device lists/no whole-/dev bind do not rule out hardware access, but do not prove active inference.

The SSH workflow keeps the capability-tested cached SearXNG image rather than silently changing to the later-discovered connector image.

## Unresolved

Accelerator model/capacity/firmware/utilization/power; active inference runtime; integrated CIX NPU/GPU usage; precise verification/update/overlay behavior; standalone slot-type mismatch; resume unit failure; reboot/update access persistence and failure recovery.

Do not publish serials, MACs, device addresses, owner names, fingerprints, raw history, secrets or vendor-source excerpts. No hardware settings were intentionally changed by these inventory queries.
