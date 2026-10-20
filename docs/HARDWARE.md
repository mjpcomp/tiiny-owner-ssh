# Hardware and platform observations

Observed on one owner-administered Tiiny system on 2026-10-19, with accelerator queries added 2026-10-20. Not universal specifications, a benchmark, a teardown or a warranty statement. Unique identifiers and raw output are omitted.

| Component | Observation |
| --- | --- |
| Board model / compatible | AiBox SIT Board V0.1.2 / cix,sky1 |
| CPU | 8 Cortex-A720 plus 4 Cortex-A520 logical CPUs |
| CPU policy maxima | A520 about 1.8 GHz; A720 groups about 2.2, 2.3, 2.5 and 2.6 GHz |
| Host RAM / swap | Approximately 32 GB installed, about 31 GiB Linux-visible; 16 GB-class NVMe swap |
| Accelerator | SMI model LQ50-48GB, PN 101C3011; PCI 1f6b:0c00, driver houmo,xh2a / xh2a_drv |
| Accelerator memory | SMI reports three 16 GB DDR chips and 49024.0 MB usable DDR; separate from host RAM |
| Accelerator link | Current and maximum 16 GT/s x4: PCIe 4.0 x4, not measured throughput |
| SSD | Samsung MZAL81T0HFLB-00BL2, 1 TB-class NVMe, PM9C1a controller identification |
| Wireless | MediaTek MT7922 using mt7921e |
| Temperature snapshot | Earlier system sensors roughly 49-53 C; not identified as accelerator temperature or thermal qualification |
| Host software | Debian 12, Linux 6.6.89-generic with lcfc-build package label, Python 3.11.2 |
| Docker | 27.3.1, overlay2, systemd cgroups, storage /data/docker |

Exact SoC SKU remains unresolved. The accelerator model is software-reported, not independently certified by teardown. The build label does not establish a manufacturing relationship. Driver reference counts/device numbers are not utilization or memory measurements.

## Memory and accelerator tools

Vendor specifications describe 32 GB SoC-side plus 48 GB discrete-NPU-side memory. Host inspection and the later SMI queries support these as separate memory pools, not ordinary unified CPU RAM. Specification: https://www.tiiny.ai/products/tiiny-pocket

### Successful SMI inventory, 2026-10-20

| Field | Reported result |
| --- | --- |
| Model / product part number | LQ50-48GB / 101C3011 |
| Driver / accelerator firmware | V1.4.1 / V1.4.1 |
| HMSW / HM_SMI | V1.4.1 / V1.0.0 |
| SDK build timestamp | 2026-08-07 17:45:18 |
| DDR_Memory_Total | 49024.0 MB |
| DDR_Memory_Free | 49024.0 MB at that snapshot |
| DDR_Chip_Num / DDR_Chip_Cap | 3 / 16GB, totaling 48 GB as reported |
| Chip_Revision | 1; installed help maps 0x1 to version2 |
| Avail_Core_Id | 0x11; installed help defines this as both cores available |

These are management-tool readings, not memory-cell testing or physical inspection. Total DDR is documented as usable capacity after reservations. Preserve the tool's exact MB label: binary-unit interpretation is plausible, but the exact unit convention and reservation size have not been independently verified. Free equaling total means no usage was reported for this pool at that instant, not proof of no accelerator activity. Available cores are not utilization or a measured performance result. Memory type/rate, effective bandwidth, error behavior and sustained performance remain unmeasured.

### Installed tool and library discovery

A vendor logger referenced /data/model/houmo_drv_xh2_v0.5.0/tools/hm_smi, but that path did not exist on this host. The logger creates/appends/rotates files in /data/log; it was not used for these snapshots and its source is not reproduced.

The executable actually found and successfully run was:

```text
/data/houmo-drv-xh2_v1.4.1/tools/hm_smi/hm_smi
```

The existing library was:

```text
/data/houmo-drv-xh2_v1.4.1/hal/lib/libhal_xh2a.so
```

Initial hardware queries failed with errorcode 12, HM Shared Library Not Found. This SMI build appends /hal/lib to HOUMO_SDK_PATH, so that variable must point to the package root, not the library directory. Successful queries used the root plus a process-local LD_LIBRARY_PATH pointing to hal/lib. No library copies, symlink changes, ldconfig, driver reload, app restart or SDK installation were used to resolve this failure. Directory names alone were not treated as proof of firmware version; the successful query reported it separately.

### Repeating the verified inventory

Run only on the authorized host with the same inspected package layout. Do not download a replacement SDK merely to make this command work.

```bash
(
    SDK_ROOT=/data/houmo-drv-xh2_v1.4.1
    SMI="$SDK_ROOT/tools/hm_smi/hm_smi"
    HAL_DIR="$SDK_ROOT/hal/lib"

    if [ ! -x "$SMI" ] || [ ! -r "$HAL_DIR/libhal_xh2a.so" ]; then
        printf 'Executable or HAL library unavailable; stopping.\n'
        exit 1
    fi

    if [ "$(findmnt -T /dev/shm -n -o FSTYPE)" != "tmpfs" ]; then
        printf '/dev/shm is not confirmed as tmpfs; stopping.\n'
        exit 1
    fi

    SMI_WORK=$(mktemp -d /dev/shm/tiiny-smi.XXXXXX) || exit 1

    XDG_DATA_HOME="$SMI_WORK" \
    HOUMO_SDK_PATH="$SDK_ROOT" \
    LD_LIBRARY_PATH="$HAL_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
        "$SMI" -a -f \
        Model PN Driver_Version Firmware_Version \
        DDR_Memory_Total DDR_Memory_Free

    XDG_DATA_HOME="$SMI_WORK" \
    HOUMO_SDK_PATH="$SDK_ROOT" \
    LD_LIBRARY_PATH="$HAL_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
        "$SMI" -a -vvv -f \
        DDR_Chip_Num DDR_Chip_Cap Chip_Revision Avail_Core_Id
)
```

The extended query confirmed a resolved log path under /dev/shm/tiiny-smi.*/hm_smi/logs/hm_smi.log. This confirms the intended log redirection for that run, not a forensic zero-write guarantee; tmpfs may be swapped. Temporary directories remain until removed or the tmpfs is cleared. Review output for SN, UUID, owner-specific paths and build-user information before sharing. A build-user field is SDK metadata, not necessarily the device owner. Do not publish raw dumps.

Observed xh2a interfaces include control, IPU, system, DDR/SPM allocators, transfer, fast-memory, I2C, QSPI and RPMsg. Nodes were mode 0666; actual access may also depend on driver, device-cgroup and security checks. Do not dump/write character devices to investigate. Do not run download, update, reset, governor/frequency/power-setting or stress utilities for inventory.

Reference for SMI fields and controls: https://developer.houmoai.com/hmdoc/m50/software-manual/latest/system-installation-device-management/device-monitoring-and-management/smi_tool_user_guide/commands/index.html

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

Accelerator utilization, power, temperature, current clocks/governor, measured bandwidth and memory integrity; active inference runtime; integrated CIX NPU/GPU usage; exact SoC SKU; precise verification/update/overlay behavior; standalone slot-type mismatch; resume unit failure; reboot/update access persistence and failure recovery.

Do not publish serials, MACs, device addresses, owner names, fingerprints, raw history, secrets or vendor-source excerpts. No hardware settings were intentionally changed by these inventory queries.
