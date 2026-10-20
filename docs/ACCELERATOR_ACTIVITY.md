# Accelerator allocation and activity observations

Recorded 2026-10-20 from owner-supplied observations on one authorized Tiiny setup. This follows the inventory in [HARDWARE.md](HARDWARE.md) and supersedes its earlier unresolved utilization/power observations only to the extent stated here. It is not a throughput, energy-efficiency, thermal-qualification or memory-integrity benchmark. Raw output, process IDs, unique identifiers, credentials and conversation content are omitted.

## Scope and method

The previously verified LQ50-48GB used driver/firmware/HMSW V1.4.1 and HM_SMI V1.0.0. SMI used the existing package-root HOUMO_SDK_PATH, hal/lib on process-local LD_LIBRARY_PATH, and XDG_DATA_HOME under /dev/shm. No driver reload, SDK installation, device permission change, governor change, clock setting or power-limit setting was used.

The owner loaded models through the Tiiny application. A process-metadata scan checked for the Houmo HAL mapping and open xh2a/houmo-named device handles without printing command lines or environments. A bounded repeated SMI query then captured activity; it was stopped with Ctrl+C before all 30 planned samples completed. Running models/requests is a real workload and may change allocations, application history and logs. These observations are not zero-write inventory.

## Loaded-model state

Before model loading, SMI reported total/free DDR of 49024.0/49024.0 MB. After loading, total remained 49024.0 MB and free fell to 12970.01 MB: 36053.99 MB allocated by total-minus-free, approximately 73.5% of the usable pool. This is not a weights-only or per-model measurement.

Both cores initially reported 0% utilization, current/reported locked IPU rate 1300 MHz, voltage 750 mV and performance governor. Board power was 6.11 W in the first loaded snapshot. Core temperatures were 42.3/43.5 C; DDR sensor readings ranged 42.3-47.4 C. These are snapshots, not sustained-load temperatures or limits. Sensor labels do not establish physical package count.

The scan found:

| Process name as reported | Evidence |
| --- | --- |
| llama-server | Open Houmo control, IPU, DDR/SPM allocator, transfer and system devices |
| mirage-image-se | Houmo HAL mapped and the same device-interface classes open |
| mirage-speech-s | Houmo HAL mapped and the same device-interface classes open |

Names alone do not establish exact models or container ownership. Not finding an exact HAL mapping for llama-server does not negate its observed device handles. Process scans had unreadable/exited entries and may miss short-lived users, inaccessible descriptors or other naming schemes.

## Monitored activity

| Phase | Samples | Reported IPU load | Free DDR (MB) | Board power (W) |
| --- | --- | --- | --- | --- |
| Loaded, waiting | 1-13 | 0% | 12970.01 | 6.12-6.13 |
| Active work | 14-20 | 53.94-100%; both cores reached 100% | 12892.65 | Initially 6.13, then up to 14.86 |
| Further activity/allocation | 21 | 98.38% | 12172.22 | 14.66 |
| Zero reported utilization again | 22-27 | 0% | 12172.22 | Declined from 6.79 to 6.21 |

Clock/governor/voltage readings remained 1300 MHz, performance and 750 mV. Eight consecutive samples (14-21) reported nonzero activity. Sampled board power reached 14.86 W; this is not whole-device wall power or a guaranteed hardware maximum. Power rose later than utilization in the displayed samples; polling does not establish exact sensor synchronization or response latency.

Final allocated DDR was 36851.78 MB, 797.79 MB above the initial loaded state. The additional allocation persisted after reported utilization returned to zero. Its ownership was not identified; this is not proof of a memory leak or a particular cache/buffer implementation. Preserve the tool's MB labels; exact binary/decimal unit convention remains unverified.

This establishes software-reported active work on the Houmo accelerator, beyond model residency and open device handles. Attribution to a particular chat/model requires request timing and native-model state; several services were loaded. No tokens/second, TOPS, energy/token, effective bandwidth or sustained thermal result was established. Temperature was not included in this repeated monitor.

## Interrupted query

At sample 26, Ctrl+C was followed by Interrupted system call and RPMSG receive failed: -4. This was consistent with signal interruption, not by itself evidence of a spontaneous accelerator fault. Sample 27 returned another complete reading before the final interrupt. The run was not treated as a completed 30-sample test. Let finite monitoring finish when practical; do not reset the card solely because of this interrupted receive.

## Native API follow-up, not yet tested on this device

Source review of https://github.com/CooperativePenguinToby/tiiny-web identified these GET requests in src/app/api/device/route.ts and src/app/api/models/route.ts:

- /api/v1/npu/status: device utilization, accelerator memory and readiness/status.
- /api/v1/models/npu/status: model-management NPU allocation/availability, distinct from utilization.
- /api/v1/models/running: native running/pending instances, NPU share and active requests.
- /api/v1/models/?including_downloading=false: native model inventory/status.

The overview polls every five seconds. Its telemetry mapping selects devices[0], substitutes zero for missing first-device metrics and converts memory MB with 1024*1024. These are implementation choices, not independent verification of device units or complete multi-device coverage. Its polling hook retains previous data with a stale-values warning after errors.

The source client sends a bearer auth key. Do not publish the key or assume these endpoints work on every device version. The separate Open WebUI Ollama endpoint returned an empty loaded-model list during earlier checks; that did not describe the native Tiiny model service. No tiiny-web deployment or end-to-end tests were run; that project's tests and UI include device-changing operations.

Next useful step: a bounded, authenticated GET-only native status/model query compared with SMI. Do not install a dashboard, load more models, alter permissions or repeat a heavier workload solely to reconfirm activity. Review/sanitize API output before sharing because inventories may identify private models or device details.
