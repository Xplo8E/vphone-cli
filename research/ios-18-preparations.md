# iOS 18.5 Support Preparation - 22F76

Last updated: 2026-04-22

This is the control document for the iOS 18 support branch. Keep this file focused on state, blockers, decisions, and the execution plan. The deeper narrative notes live in [ios-18-firmware-deep-dive.md](ios-18-firmware-deep-dive.md).

## Scope

We are targeting iOS 18.5 / cloudOS 18.5 build `22F76` first, with the developer variant as the initial bring-up target.

Firmware inputs are local:

| Input | Path | Role |
| --- | --- | --- |
| iPhone IPSW | `/Users/vinay/ipsw/iPhone17,3_18.5_22F76_Restore.ipsw` | iPhone OS image, system volume, static trust cache, iPhone restore metadata |
| cloudOS IPSW | `/Users/vinay/ipsw/cloudOS_18.5_22F76.ipsw` | VM boot chain, cloud kernel, TXM/SPTM, DeviceTree, SEP |

The working assumption before testing was simple: reuse the existing vphone600 flow, swap in 18.5 firmware, and retarget patches only where patterns moved. That assumption is already partially wrong. The 18.5 cloudOS IPSW does not contain `vphone600ap` identities or `kernelcache.research.vphone600`, so the manifest/runtime merge has to move to `vresearch101ap`/`vresearch101` unless we find a separate vphone600 firmware source.

## Current Finding States

| State | Finding | Evidence | Impact |
| --- | --- | --- | --- |
| confirmed | Phase 1 firmware profile layer is implemented for `ios18-22F76`. | `FIRMWARE_PROFILE=ios18-22F76` now flows through `make fw_prepare`, `fw_patch*`, `ramdisk_build`, and `ramdisk_send`. `FirmwarePipeline` consumes `FirmwareProfile` paths. `scripts/fw_manifest.py --profile ios18-22F76` generates a manifest with `DeviceTree.vresearch101ap`, `kernelcache.research.vresearch101`, no `RecoveryMode`, and DeviceMap `['d47ap', 'vresearch101ap']`. | The iOS 18.5 path no longer needs shim-renamed vphone600 runtime files for manifest generation or component discovery. Patch semantics are unchanged. |
| confirmed | Phase 2 TXM dev retargeting works on 18.5 Mach-O TXM. | `patch-component --component txm-dev` emits 12 TXM dev records on both the raw 18.5 Mach-O payload and the IM4P container. A profile-aware `patch-firmware --variant dev --firmware-profile ios18-22F76` run reaches TXM with real `vresearch101` filenames and emits all 12 TXM records before stopping at the known DeviceTree blocker. | TXM is no longer the active bring-up blocker. `TXMDevPatcher` now handles Mach-O VM-address refs, direct `ADR` cstring refs, and the 18.5 developer-mode branch shape. |
| confirmed | Phase 3 DeviceTree profile retargeting works for `vresearch101ap`. | `DeviceTreePatcherTests` prove legacy still requires legacy nodes while `ios18-22F76` skips missing `buttons`/notch nodes. `patch-component --component device-tree --firmware-profile ios18-22F76` patches the real 18.5 DeviceTree with 2 records. Full `patch-firmware --variant dev --firmware-profile ios18-22F76` completes successfully with 59 total records. | DeviceTree is no longer a pipeline blocker. Policy knobs such as `chosen/debug-enabled` and `chosen/amfi-allows-trust-cache-load` remain intentionally unchanged pending boot evidence. |
| confirmed | Phase 4 kernel misses `[8]` and `[16]` are retargeted for `kernelcache.research.vresearch101`. | IDA MCP was attempted on the decompressed kernel but timed out, so the final evidence is deterministic Mach-O/Capstone analysis. Patch `[8]` now finds the 18.5 `TXM [Error]: CodeSignature` post-log `b.eq` at file offset `0x0EACAB0` and NOPs it. Patch `[16]` now finds the `com.apple.apfs.get-dev-by-role` entitlement-deny `cbz w0` at `0x1F9E54C` and NOPs it. A direct kernel-base component run emits 26 kernel records, and a full profile-aware dev patch run completes all 9 components with 61 total records. | The Swift patch pipeline now has no known Phase 1-4 blocker for producing a profile-aware iOS 18.5 dev firmware tree. Boot/runtime validation is still pending. |
| confirmed | Phase 5 restore reaches disk boot and APFS root authentication on the real `vm/` workspace. | `make restore` exited 0 for UDID `0000FE01-FD01E5DAE1ED866F` / ECID `0xFD01E5DAE1ED866F`. Post-restore boot logs show `BSD root: disk0s1`, `disk1s1 Rooting from snapshot with xid 61`, and `authenticate_root_hash ... successfully validated on-disk root hash`. | The generated 18.5 manifest, boot chain, DeviceTree profile, and kernel patches are coherent enough for restore and disk-root handoff. |
| confirmed | Phase 5 SSH ramdisk builds and boots with the restore-patched kernel for the real 18.5 profile. | `make ramdisk_build VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76 RAMDISK_UDID=0000FE01-FD01E5DAE1ED866F` completed after `sudo -v`. The first `ramdisk_send` using derived `krnl.ramdisk.img4` hung after `bootx` with no kernel serial. Retrying with `krnl.img4` booted the SSH ramdisk: serial reached `BSD root: md0`, `SSHRD_Script`, `Running server`; usbmux exposed `0000FE01-FD01E5DAE1ED866F`; SSH answered `ready` on `127.0.0.1:2222`. | The iOS 18.5 profile now disables generated `krnl.ramdisk.img4` preference and uses `krnl.img4` for ramdisk boot. |
| confirmed | Phase 5 dev CFW install completed over the SSH ramdisk. | `make cfw_install_dev VM_DIR=vm SSH_PORT=2222` completed. It installed SystemOS/AppOS Cryptexes, patched `launchd` jetsam guard, patched debugserver entitlements, renamed the APFS update snapshot to `orig-fs`, patched `seputil`, installed GPU bundle and iosbinpack64, patched `launchd_cache_loader`, patched `mobileactivationd`, installed `vphoned` plus dev LaunchDaemons, patched `launchd.plist`, unmounted device filesystems, and halted the ramdisk. Transient SSH/SCP drops recovered through the existing retry loop. | The next runtime gate is first normal boot after CFW. This is where the previous dyld/libSystem panic must be re-tested. |
| candidate | Post-restore userspace was incomplete before CFW install. | The pre-CFW post-restore boot panicked in `launchd`: `Library not loaded: /usr/lib/libSystem.B.dylib`, `no dyld cache`, `initproc failed to start`. | This must now be re-tested after CFW install. If it persists, it becomes a confirmed iOS 18.5 userspace packaging blocker. |
| confirmed | cloudOS 18.5 `22F76` has no `vphone600ap` build identity. | `BuildManifest.plist` contains `j236cap`, `j475dap`, and `vresearch101ap`; no `vphone600ap`. Running current `scripts/fw_manifest.py` against 18.5 manifests throws `KeyError: 'No release identity for DeviceClass=vphone600ap'`. | Current `fw_prepare` hybrid manifest generation cannot work unchanged on these 18.5 files. |
| confirmed | Existing pipeline hardcodes vphone600 runtime paths. | `sources/FirmwarePatcher/Pipeline/FirmwarePipeline.swift` searches `kernelcache.research.vphone600` and `Firmware/all_flash/DeviceTree.vphone600ap.im4p`. `scripts/ramdisk_build.py` has the same vphone600 assumptions. | We need variant-aware paths or an explicit firmware profile before real 18.5 patching. |
| confirmed | 18.5 cloud TXM is Mach-O arm64e, not the flat-offset model assumed by parts of `TXMDevPatcher`. | `file` reports Mach-O arm64e. `otool -hv` reports `MH_MAGIC_64 ARM64 subtype E caps KER00 EXECUTE PIE`. IDA sees strings/xrefs, but the Swift dev patcher reports string refs missing. | Base TXM patch works, but dev-only TXM patches need Mach-O VA/file-offset aware string reference resolution. |
| confirmed | 18.5 `DeviceTree.vresearch101ap` does not match the current vphone600 DeviceTree patch contract. | Decoded DeviceTree has no `buttons` node, no `home-button-type`, no `island-notch-location`, and no `MKB`/`mkb`/`keybag` literals. It does have `chosen/amfi-allows-trust-cache-load=0`, `chosen/debug-enabled=0`, and `product/has-virtualization=1`. | Current `DeviceTreePatcher` applies `serial-number`, then fails on missing `buttons`. Needs variant-aware behavior before pipeline success. |
| candidate | Existing iBoot/LLB patchers mostly still find usable patterns on 18.5 `vresearch101` release boot stages. | Shim dry-run patched AVPBooter, iBSS, iBEC, and LLB. LLB had several old rootfs pattern misses but still emitted 9 patches. | Boot-chain patching is not the first blocker, but LLB misses need review before signing/boot testing. |

## Firmware Inventory

### iPhone IPSW

`iPhone17,3_18.5_22F76_Restore.ipsw`

| Field | Value |
| --- | --- |
| ProductVersion | `18.5` |
| ProductBuildVersion | `22F76` |
| DeviceClass | `d47ap` |
| Build identities | 5 |
| Relevant variants | Customer Erase, Customer Upgrade, Research Customer Erase, Research Customer Upgrade, Recovery Customer |

Important iPhone paths:

| Component | Release path | Research path |
| --- | --- | --- |
| iBSS | `Firmware/dfu/iBSS.d47.RELEASE.im4p` | `Firmware/dfu/iBSS.d47.RESEARCH_RELEASE.im4p` |
| iBEC | `Firmware/dfu/iBEC.d47.RELEASE.im4p` | `Firmware/dfu/iBEC.d47.RESEARCH_RELEASE.im4p` |
| LLB | `Firmware/all_flash/LLB.d47.RELEASE.im4p` | `Firmware/all_flash/LLB.d47.RESEARCH_RELEASE.im4p` |
| iBoot | `Firmware/all_flash/iBoot.d47.RELEASE.im4p` | `Firmware/all_flash/iBoot.d47.RESEARCH_RELEASE.im4p` |
| TXM | `Firmware/txm.iphoneos.release.im4p` | `Firmware/txm.iphoneos.research.im4p` |
| Kernel | `kernelcache.release.iphone17` | `kernelcache.research.iphone17` |
| SPTM | `Firmware/sptm.t8140.release.im4p` | same release SPTM in the research identity |
| DeviceTree | `Firmware/all_flash/DeviceTree.d47ap.im4p` | same |
| SEP | `Firmware/all_flash/sep-firmware.d47.RELEASE.im4p` | same |

### cloudOS IPSW

`cloudOS_18.5_22F76.ipsw`

| Field | Value |
| --- | --- |
| ProductVersion | `18.5` |
| ProductBuildVersion | `22F76` |
| Build identities | 4 |
| DeviceClasses | `j236cap`, `j475dap`, `vresearch101ap` |
| Restore DeviceMap | `j236cap`, `j475dap`, `vresearch101ap` |
| vphone600 availability | absent |

Important `vresearch101ap` paths:

| Component | Release path | Research path |
| --- | --- | --- |
| iBSS | `Firmware/dfu/iBSS.vresearch101.RELEASE.im4p` | `Firmware/dfu/iBSS.vresearch101.RESEARCH_RELEASE.im4p` |
| iBEC | `Firmware/dfu/iBEC.vresearch101.RELEASE.im4p` | `Firmware/dfu/iBEC.vresearch101.RESEARCH_RELEASE.im4p` |
| LLB | `Firmware/all_flash/LLB.vresearch101.RELEASE.im4p` | `Firmware/all_flash/LLB.vresearch101.RESEARCH_RELEASE.im4p` |
| iBoot | `Firmware/all_flash/iBoot.vresearch101.RELEASE.im4p` | `Firmware/all_flash/iBoot.vresearch101.RESEARCH_RELEASE.im4p` |
| TXM | `Firmware/txm.iphoneos.release.im4p` | `Firmware/txm.iphoneos.research.im4p` |
| SPTM | `Firmware/sptm.vresearch1.release.im4p` | same release SPTM in the research identity |
| Kernel | `kernelcache.release.vresearch101` | `kernelcache.research.vresearch101` |
| DeviceTree | `Firmware/all_flash/DeviceTree.vresearch101ap.im4p` | same |
| SEP | `Firmware/all_flash/sep-firmware.vresearch101.RELEASE.im4p` | same |

The important delta is the missing vphone600 runtime set:

- missing `kernelcache.research.vphone600`
- missing `kernelcache.release.vphone600`
- missing `Firmware/all_flash/DeviceTree.vphone600ap.im4p`
- missing `Firmware/all_flash/sep-firmware.vphone600.RELEASE.im4p`

## Existing Patch Surface

The Swift firmware pipeline is ordered like this:

1. `AVPBooter` - host AVPBooter digest bypass.
2. `iBSS` - iBoot patcher, plus JB nonce extension for JB variant.
3. `iBEC` - iBoot patcher.
4. `LLB` - iBoot patcher.
5. `TXM` - base `TXMPatcher` for regular, `TXMDevPatcher` for dev/JB.
6. `kernelcache` - `KernelPatcher`, plus `KernelJBPatcher` for JB.
7. `DeviceTree` - fixed property patcher.
8. `Filesystem` - only for `.less`.
9. `Manifest` - only for `.less`.

For iOS 18.5 dev bring-up, the meaningful patch surfaces are `TXMDevPatcher`, `KernelPatcher`, `DeviceTreePatcher`, and the manifest/path selection code. AVPBooter and iBoot are still relevant, but they are not the first structural blockers.

## Current Structural Blockers

### 1. Manifest Merge Still Expects vphone600 Runtime

Current `scripts/fw_manifest.py` discovers:

```python
PROD, RES = find_cloudos(C, "vresearch101ap")
VP, VPR = find_cloudos(C, "vphone600ap")
```

That worked for the previous firmware set because `vresearch101ap` supplied DFU identity compatibility while `vphone600ap` supplied runtime pieces like DeviceTree/kernel/SEP. On 18.5, `vphone600ap` is gone from the cloudOS manifest. The script fails before it can generate the hybrid BuildManifest.

Decision needed after more reversing: either treat `vresearch101ap` as both boot and runtime profile for 18.5, or locate a separate vphone600 18.x source. Based on the local firmware we have right now, `vresearch101ap` is the only viable 18.5 cloud VM profile.

### 2. FirmwarePipeline Paths Are Not Profile-Aware

Current hardcoded paths include:

```swift
"Firmware/dfu/iBSS.vresearch101.RELEASE.im4p"
"Firmware/dfu/iBEC.vresearch101.RELEASE.im4p"
"Firmware/all_flash/LLB.vresearch101.RELEASE.im4p"
"Firmware/txm.iphoneos.research.im4p"
"kernelcache.research.vphone600"
"Firmware/all_flash/DeviceTree.vphone600ap.im4p"
```

The first four still exist in cloudOS 18.5. The last two do not. A quick shim can rename `kernelcache.research.vresearch101` and `DeviceTree.vresearch101ap.im4p` to the old vphone600 names, but that is only useful for patcher dry-runs. It is not a clean implementation path.

The proper fix is a firmware profile layer:

| Profile | Boot board | Runtime board | Kernel | DeviceTree |
| --- | --- | --- | --- | --- |
| legacy | `vresearch101ap` | `vphone600ap` | `kernelcache.research.vphone600` | `DeviceTree.vphone600ap.im4p` |
| ios18-22F76 candidate | `vresearch101ap` | `vresearch101ap` | `kernelcache.research.vresearch101` | `DeviceTree.vresearch101ap.im4p` |

### 3. TXM Dev Patches Need Mach-O Awareness

`TXMPatcher.patchTrustcacheBypass()` still finds the legacy trustcache site in 18.5 TXM:

```text
0x027E54: bl 0x26950 -> mov x0, #0
```

`TXMDevPatcher` then fails most dev-only patches because its string xref helper assumes a flat binary:

```swift
let pcPage = UInt64(off) & ~UInt64(0xFFF)
let resolved = Int(adrpPage) + Int(addImm12)
if resolved == targetOff { ... }
```

On 18.5, TXM is a Mach-O with high virtual addresses. Strings live at addresses like `0xfffffff0170065d3`, while the Swift helper compares against raw file offsets. IDA confirms the strings and xrefs exist, so this is not a missing-payload problem. It is an address model bug.

Verified IDA anchors in `/tmp/vphone-ios18-22F76/raw/txm.cloud.research.raw`:

| Anchor | String address | Xrefs | Function(s) |
| --- | ---: | --- | --- |
| `get-task-allow` | `0xfffffff0170065d3` | `0xfffffff017010f08`, `0xfffffff01701f5a8`, `0xfffffff017031f98` | `sub_FFFFFFF01701F538`, `sub_FFFFFFF017031F14` |
| `com.apple.security.get-task-allow` | `0xfffffff017008161` | `0xfffffff017031fb0` | `sub_FFFFFFF017031F14` |
| `com.apple.private.cs.debugger` | `0xfffffff0170063fb` | `0xfffffff017010f10`, `0xfffffff017010f40`, `0xfffffff01701ca24`, `0xfffffff01701f37c`, `0xfffffff01701f3f4` | `sub_FFFFFFF01701F328` among others |
| developer mode policy log | `0xfffffff0170066c8` | `0xfffffff01701f9f8` | `sub_FFFFFFF01701F98C` |
| `personalized.trust-cache` | `0xfffffff017006c5b` | `0xfffffff0170101c0`, `0xfffffff017010860` | trustcache setup path |
| missing trust cache range log | `0xfffffff017006b9a` | `0xfffffff017021f28` | `sub_FFFFFFF017021C18` |

IDA confirms the old concepts still exist:

- `sub_FFFFFFF01701F538` gates a get-task-allow style path behind `byte_FFFFFFF017064CD3 == 1` and sets `*(a1 + 32) = 1` when `get-task-allow` is accepted.
- `sub_FFFFFFF01701F328` checks `com.apple.private.cs.debugger`, logs `disallowed non-debugger initiated debug mapping`, and returns `37` on failure.
- `sub_FFFFFFF01701F98C` computes developer mode state and writes `byte_FFFFFFF017064CD3 = v1`.
- `sub_FFFFFFF017021C18` loads external trust cache modules and errors if the trust cache range is missing or length zero.

This means the dev patch intent still maps to 18.5, but the locator needs retargeting before patching.

### 4. DeviceTree Patcher Is Too Rigid for `vresearch101ap`

Current fixed DeviceTree patches are:

| Patch ID | Node | Property | New value |
| --- | --- | --- | --- |
| `devicetree.serial_number` | `/device-tree` | `serial-number` | `vphone-1337` |
| `devicetree.home_button_type` | `/device-tree/buttons` | `home-button-type` | `2` |
| `devicetree.artwork_device_subtype` | `/device-tree/product` | `artwork-device-subtype` | `2556` |
| `devicetree.island_notch_location` | `/device-tree/product` | `island-notch-location` | `144` |

18.5 `DeviceTree.vresearch101ap` differs:

| Path/property | Value |
| --- | --- |
| `/device-tree/target-type` | `VRESEARCH101` |
| `/device-tree/target-sub-type` | `VRESEARCH101AP` |
| `/device-tree/compatible` | `VRESEARCH101AP`, `ComputeModule14,2`, `AppleVirtualPlatformARM` |
| `/device-tree/chosen/txm-secure-channel` | `1` |
| `/device-tree/chosen/protected-data-access` | `1` |
| `/device-tree/chosen/amfi-allows-trust-cache-load` | `0` |
| `/device-tree/chosen/debug-enabled` | `0` |
| `/device-tree/chosen/effective-security-mode-ap` | `0` |
| `/device-tree/chosen/effective-production-status-ap` | `0` |
| `/device-tree/product/has-virtualization` | `1` |
| `/device-tree/product/artwork-device-subtype` | `0` |
| `/device-tree/product/has-exclaves` | `0` |
| `/device-tree/product/partition-style` | `iOS` |
| `/device-tree/product/product-name` | `Apple PCC Research Environment Virtual Machine 1` |

Missing properties/nodes:

- no `/device-tree/buttons`
- no `home-button-type`
- no `island-notch-location`
- no literal `MKB`, `mkb`, or `keybag`

This needs design, not blind adding. The old `vphone600ap` DeviceTree allegedly carried MKB/keybag-less boot behavior. The `vresearch101ap` tree uses different policy knobs. We need to understand which properties are semantically required for boot and which are just cosmetic/device-shaping.

## Dry-Run Patch Results

These dry-runs used extracted 18.5 components under `/tmp/vphone-ios18-22F76` and a shim VM tree under `/tmp/vphone-ios18-vm-test`. The shim renamed `vresearch101` runtime files to old vphone600 paths only to exercise existing patchers. That is evidence for locator behavior, not a valid final firmware layout.

### `patch-component --component txm`

Input: cloudOS 18.5 `Firmware/txm.iphoneos.research.im4p`

| Result | Detail |
| --- | --- |
| success | `txm.trustcache_bypass` emitted at file offset `0x027E54` |
| patch | `bl 0x26950 -> mov x0, #0` |
| limitation | This invokes base `TXMPatcher`, not dev-only `TXMDevPatcher`. |

### `patch-component --component kernel-base`

Input: cloudOS 18.5 `kernelcache.research.vresearch101`

| Patch area | Result |
| --- | --- |
| APFS root snapshot | found |
| APFS seal broken | found |
| `bsd_init` rootvp auth gate | found |
| launch constraints | found |
| debugger | found |
| post-validation NOP | missed - `TBNZ not found after TXM error string ref` |
| post-validation CMP | found |
| dyld policy | found |
| APFS graft | found |
| APFS mount/graft paths | mostly found |
| `handle_get_dev_by_role` entitlement gate | missed - pattern not found |
| Sandbox MACF hooks | found 5 hooks, emitted 10 records |

Total emitted records in dry-run: 24.

The two misses are not automatically fatal, but they are not safe to ignore. Both touch post-restore validation / APFS role access behavior, so they need IDA-backed retargeting before first real boot test.

### Full `patch-firmware --variant dev` Shim Run

| Component | Result |
| --- | --- |
| AVPBooter | success, digest bypass emitted |
| iBSS | success, 4 records |
| iBEC | success, 7 records |
| LLB | partial, 9 records, several old rootfs patterns missing |
| TXM dev | partial, base trustcache and selector24 emitted; get-task-allow/debugger/developer-mode locators missed |
| Kernel | partial, 24 records; misses `[8]` and `[16]` |
| DeviceTree | failed on missing child node `buttons` after serial-number patch |

So the current blocker order is clear: manifest/profile first, TXM address model second, DeviceTree profile behavior third, kernel misses fourth.

## Implementation Plan

### Phase 1 - Firmware Profile Layer

Status: complete for profile/path selection. No patch behavior was changed.

Goal: stop encoding firmware identity assumptions directly in the patch pipeline.

Tasks:

1. Done - added `FirmwareProfile` with `legacy` and `ios18-22F76`.
2. Done - `ios18-22F76` uses `vresearch101ap` as both boot and runtime DeviceClass.
3. Done - `scripts/fw_manifest.py` accepts `--profile` and optional `--runtime-device-class`; `RecoveryMode` is optional for `ios18-22F76`.
4. Done - `FirmwarePipeline` consumes profile paths instead of hardcoded vphone600 runtime paths.
5. Done - `scripts/ramdisk_build.py` and `scripts/pymobiledevice3_bridge.py` use the same profile-selected kernel/DeviceTree names.
6. Done - removed the unused MachOKit dependency from the Swift package; `MachOHelpers.swift` already uses a local parser and did not call MachOKit. This avoids a Swift 6.2/MachOKit compile crash during verification.

Verifier:

- Passed - `swift test --filter FirmwarePipelineTests/firmwareProfileControlsRuntimePaths`.
- Passed - `python3 -m py_compile scripts/fw_manifest.py scripts/ramdisk_build.py scripts/pymobiledevice3_bridge.py`.
- Passed - `git diff --check`.
- Passed - `scripts/fw_manifest.py --profile ios18-22F76` against the 18.5 manifests.
- Verified manifest paths:
  - `DeviceTree` and `RestoreDeviceTree`: `Firmware/all_flash/DeviceTree.vresearch101ap.im4p`
  - `KernelCache`: `kernelcache.research.vresearch101`
  - `RestoreKernelCache`: `kernelcache.release.vresearch101`
  - `RecoveryMode`: absent, intentionally skipped for `vresearch101ap`
  - `DeviceMap`: `d47ap`, `vresearch101ap`
- Passed - `make -n fw_prepare FIRMWARE_PROFILE=ios18-22F76`.
- Passed - `make -n fw_patch FIRMWARE_PROFILE=ios18-22F76 VM=iphone_18_5`.
- Passed - CLI parse check: `patch-firmware --firmware-profile ios18-22F76` is accepted and reaches the expected missing-restore-dir error on an empty VM directory.

Residual risk:

- This phase only proves profile/path plumbing. The real `patch-firmware --variant dev` run is still blocked by TXM dev locator misses and DeviceTree profile behavior.
- Full `swift test` is not currently a clean verifier because `ipsws/patch_refactor_input` fixtures are absent locally; the targeted profile test is the relevant Swift verifier for this phase.

### Phase 2 - TXM Mach-O Retargeting

Status: complete for 18.5 TXM dev patch discovery and direct component verification.

Goal: preserve current dev patch intent but make locators work on Mach-O TXM.

Tasks:

1. Done - reused the local `MachOParser` segment parser for TXM.
2. Done - converted between patch file offsets and Mach-O VM addresses for reference resolution.
3. Done - replaced `findRefsToOffset` with an address-aware resolver:
   - string file offset -> string VM address
   - instruction file offset -> instruction VM address
   - ADRP page math in VM address space
   - ADD page offset check
   - direct `ADR` cstring refs, which 18.5 uses for nearby `__TEXT` strings
4. Done - retargeted each dev patch independently:
   - `get-task-allow` entitlement force true
   - debugger entitlement force true
   - selector42/29 shellcode path
   - developer-mode guard bypass
5. Done - kept the flat fallback when Mach-O segment parsing returns no segments.
6. Done - added `patch-component --component txm-dev` for direct TXM dev verification.

Verifier:

- Passed - `swift test --filter FirmwarePipelineTests/firmwareProfileControlsRuntimePaths`.
- Passed - `git diff --check`.
- Passed - raw payload check:
  - `.build/debug/vphone-cli patch-component --component txm-dev --input /tmp/vphone-ios18-22F76/raw/txm.cloud.research.raw --output /tmp/vphone-ios18-22F76/raw/txm.cloud.research.dev-patched.raw`
  - emitted 12 TXM patches.
- Passed - IM4P container check:
  - `.build/debug/vphone-cli patch-component --component txm-dev --input /tmp/vphone-ios18-22F76/cloud/Firmware/txm.iphoneos.research.im4p --output /tmp/vphone-ios18-22F76/raw/txm.cloud.research.dev-patched-from-im4p.raw`
  - emitted the same 12 TXM patches.
- Passed - profile-aware full pipeline check:
  - `.build/debug/vphone-cli patch-firmware --vm-directory /tmp/vphone-ios18-vm-profile --variant dev --firmware-profile ios18-22F76`
  - used real `kernelcache.research.vresearch101` and `DeviceTree.vresearch101ap.im4p` names, emitted all 12 TXM patches, then stopped at the expected DeviceTree `buttons` miss.
- IDA/capstone alignment:
  - `get-task-allow` ref at VA `0xfffffff01701f5a8` / file offset `0x01B5A8`; patched BL at `0x01B5B8`.
  - `com.apple.private.cs.debugger` ref at VA `0xfffffff01701f3f4` / file offset `0x01B3F4`; patched BL at `0x01B404`.
  - developer-mode log ref at VA `0xfffffff01701f9f8` / file offset `0x01B9F8`; patched guard at `0x01B9C4` from `cbz w9, 0x1b9f4` to `b 0x1b9f4`.

Residual risk:

- The 18.5 developer-mode patch is semantically clear from local control flow, but first boot has not validated runtime effect yet.
- Full dev firmware build still cannot complete because `DeviceTreePatcher` is not profile-aware.

### Phase 3 - DeviceTree Profile Retargeting

Status: complete for profile-aware patch selection and full pipeline patching.

Goal: make DeviceTree patching explicit per runtime profile instead of failing on legacy vphone600-only nodes.

Tasks:

1. Done - split DeviceTree patches into profile-specific sets.
2. Done - classified `vresearch101ap` patch behavior:
   - retained: `/device-tree/serial-number`
   - retained: `/device-tree/product/artwork-device-subtype`
   - skipped as legacy-only: `/device-tree/buttons/home-button-type`
   - skipped as legacy-only: `/device-tree/product/island-notch-location`
   - deferred: `/device-tree/chosen/amfi-allows-trust-cache-load`
   - deferred: `/device-tree/chosen/debug-enabled`
3. Done - left `chosen/amfi-allows-trust-cache-load` and `chosen/debug-enabled` unchanged until boot evidence says they are needed.
4. Done - missing legacy cosmetic nodes no longer fail the `ios18-22F76` profile.
5. Done - added `patch-component --component device-tree --firmware-profile ...` for direct DeviceTree verification.

Verifier:

- Passed - `swift test --filter DeviceTreePatcherTests`.
- Passed - direct real-payload check:
  - `.build/debug/vphone-cli patch-component --component device-tree --firmware-profile ios18-22F76 --input /tmp/vphone-ios18-22F76/cloud/Firmware/all_flash/DeviceTree.vresearch101ap.im4p --output /tmp/vphone-ios18-22F76/raw/DeviceTree.vresearch101ap.ios18-patched.raw`
  - emitted 2 patches:
    - `0x000128` serial-number -> `vphone-1337`
    - `0x00A964` artwork-device-subtype -> `2556`
- Passed - full profile-aware dev patch run:
  - `.build/debug/vphone-cli patch-firmware --vm-directory /tmp/vphone-ios18-vm-profile --variant dev --firmware-profile ios18-22F76`
  - completed all 9 components successfully.
  - total patch records: 59.

Residual risk:

- We have not boot-tested whether `chosen/amfi-allows-trust-cache-load=0` or `chosen/debug-enabled=0` blocks later runtime behavior. They remain unmodified by design.
- Kernel misses `[8]` and `[16]` still need IDA-backed resolution or retirement.

### Phase 4 - Kernel Miss Retargeting

Status: complete for the two known iOS 18.5 kernel misses.

Goal: investigate the two missed kernel patches and decide whether they moved, changed shape, or are no longer needed.

Tasks:

1. Done - attempted to open `kernelcache.research.vresearch101` in IDA MCP. `open_idb` and `analysis_status` timed out on the decompressed kernel, so Phase 4 used a deterministic Mach-O/Capstone pass instead of pretending IDA evidence existed.
2. For post-validation NOP `[8]`:
   - Done - located `TXM [Error]: CodeSignature` at file offset `0x7F329`.
   - Done - found the string reference at `0x0EACA98/0x0EACA9C`.
   - Done - identified the 18.5 replacement shape: log call, `mov w0,#5`, `ldrb`, `cmp w8,#1`, then `b.eq 0xeacb98`.
   - Done - generalized the patch from old `tbnz` only to a nearby post-log conditional branch set: `tbnz`, `tbz`, `cbz`, `cbnz`, `b.eq`, `b.ne`.
3. For `handle_get_dev_by_role` `[16]`:
   - Done - located `com.apple.apfs.get-dev-by-role` at file offset `0x581DAC`.
   - Done - found the entitlement-check reference at `0x1F9E540/0x1F9E544`.
   - Done - identified the deny gate: `bl entitlement_check; cbz w0, 0x1f9e5b0`.
   - Done - added the observed 18.5 entitlement-deny line ID `0x3EC2` to the semantic error-block recognizer while preserving legacy IDs `0x332D` and `0x333B`.
4. Done - updated patchers only after the semantic targets were clear; no file offsets were hardcoded in patch logic.

Verifier:

- Passed - new locators are decode/semantic backed, not offset backed.
- Passed - direct kernel component check:
  - `.build/debug/vphone-cli patch-component --component kernel-base --input /tmp/vphone-ios18-22F76/cloud/kernelcache.research.vresearch101 --output /tmp/vphone-ios18-22F76/raw/kernelcache.research.vresearch101.basepatched.phase4.raw`
  - emitted 26 kernel records.
  - `[8] 0x0EACAB0: b.eq 0xeacb98 -> nop`
  - `[16] 0x1F9E54C: cbz w0, 0x1f9e5b0 -> nop`
- Passed - full profile-aware dev patch run:
  - `.build/debug/vphone-cli patch-firmware --vm-directory /tmp/vphone-ios18-vm-profile-fresh --variant dev --firmware-profile ios18-22F76`
  - completed all 9 components successfully.
  - total patch records: 61.
- Done - `research/0_binary_patch_comparison.md` updated for the Phase 4 patch logic changes.

Residual risk:

- This phase proves static patch discovery and patch emission. It does not prove boot behavior.
- LLB still reports old rootfs-pattern misses. They were not the current pipeline blocker, but they remain a boot-triage item if the VM fails before kernel handoff.

### Phase 5 - First Real Dev Variant Build

Status: in progress.

Goal: produce an 18.5 dev variant package without shim paths.

Tasks:

1. In progress - real workspace created with `make vm_new VM_DIR=vm`.
2. Run `make fw_patch_dev` or equivalent profile-aware target.
3. Build ramdisk using the same profile.
4. Boot once and collect logs.
5. If boot fails, triage in this order:
   - manifest/TSS mismatch
   - boot-chain component mismatch
   - TXM trustcache/developer mode rejection
   - kernel mount/rootfs/auth failure
   - DeviceTree policy mismatch

Verifier:

- Save patch logs.
- Save generated manifest component paths.
- Save boot logs or failure logs.
- Update this doc and the deep-dive log immediately after each run.

Progress log:

- 2026-04-21 23:37 - Created real `vm/` workspace with `AVPBooter.vresearch1.bin`, `AVPSEPBooter.vresearch1.bin`, sparse `Disk.img`, `SEPStorage`, and `config.plist`.
- 2026-04-21 23:39 - `make fw_prepare VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76 IPHONE_SOURCE=/Users/vinay/ipsw/iPhone17,3_18.5_22F76_Restore.ipsw CLOUDOS_SOURCE=/Users/vinay/ipsw/cloudOS_18.5_22F76.ipsw` completed.
- 2026-04-21 23:39 - Generated real workspace manifest paths:
  - `DeviceTree`: `Firmware/all_flash/DeviceTree.vresearch101ap.im4p`
  - `KernelCache`: `kernelcache.research.vresearch101`
  - `RestoreKernelCache`: `kernelcache.release.vresearch101`
  - `iBSS`: `Firmware/dfu/iBSS.vresearch101.RELEASE.im4p`
  - `iBEC`: `Firmware/dfu/iBEC.vresearch101.RELEASE.im4p`
  - `LLB`: `Firmware/all_flash/LLB.vresearch101.RELEASE.im4p`
  - `SEP`: `Firmware/all_flash/sep-firmware.vresearch101.RELEASE.im4p`
  - `RecoveryMode`: absent as expected for `ios18-22F76`
  - `Restore.plist DeviceMap`: `d47ap`, `vresearch101ap`
- 2026-04-21 23:41 - `make fw_patch_dev VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76` completed on the real workspace.
- 2026-04-21 23:41 - Real dev patch counts:
  - `AVPBooter`: 1
  - `iBSS`: 4
  - `iBEC`: 7
  - `LLB`: 9, with old rootfs line-ID patterns still absent but rootfs size and panic bypass emitted
  - `TXM`: 12
  - `kernelcache`: 26
  - `DeviceTree`: 2
  - total: 61
- 2026-04-21 23:41 - High-signal real patch offsets match the fresh verifier:
  - TXM developer mode: `0x01B9C4 cbz w9, 0x1b9f4 -> b 0x1b9f4`
  - kernel post-validation: `0x0EACAB0 b.eq 0xeacb98 -> nop`
  - kernel APFS role entitlement: `0x1F9E54C cbz w0, 0x1f9e5b0 -> nop`
  - DeviceTree serial/artwork: `0x000128`, `0x00A964`
- 2026-04-21 23:42 - `make ramdisk_build VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76` initially hit `NameError: shsh_dir is not defined` in the missing-SHSH error path. Fixed `scripts/ramdisk_build.py` to search `vm/*.shsh[2]` and `vm/shsh/*.shsh[2]`, then reran syntax check.
- 2026-04-21 23:42 - Re-running `ramdisk_build` now fails cleanly because no SHSH blob exists yet in `vm/` or `vm/shsh/`. This is the real Phase 5 blocker before ramdisk signing.
- 2026-04-21 23:45 - `make boot_host_preflight VM_DIR=vm` passed the host-side launch prerequisites: `kern.hv_vmm_present=0`, SIP disabled, `allow-research-guests` enabled, current boot-args `amfi_get_out_of_my_way=1 -v`, and signed release `vphone-cli --help` exits 0.
- 2026-04-21 23:47 - Started `make boot_dfu VM_DIR=vm`; it generated `vm/udid-prediction.txt` with UDID `0000FE01-FD01E5DAE1ED866F` and ECID `0xFD01E5DAE1ED866F`.
- 2026-04-21 23:48 - Recovery probe succeeded for ECID `0xFD01E5DAE1ED866F`; `make restore_get_shsh VM_DIR=vm RESTORE_UDID=0000FE01-FD01E5DAE1ED866F RESTORE_ECID=0xFD01E5DAE1ED866F` saved `vm/FD01E5DAE1ED866F.shsh`.
- 2026-04-21 23:52 - `ramdisk_build` with SHSH now signs stages 1-7 successfully and writes partial `vm/Ramdisk/` artifacts:
  - `iBSS.vresearch101.RELEASE.img4`
  - `iBEC.vresearch101.RELEASE.img4`
  - `sptm.vresearch1.release.img4`
  - `DeviceTree.vresearch101ap.img4`
  - `sep-firmware.vresearch101.RELEASE.img4`
  - `txm.img4`
  - `krnl.ramdisk.img4`
  - `krnl.img4`
- 2026-04-21 23:52 - Ramdisk stage 8 is blocked at `sudo -n hdiutil attach ... ramdisk.raw.dmg`; the final missing artifacts are `ramdisk.img4` and `trustcache.img4`.
- 2026-04-21 23:52 - Hardened `scripts/ramdisk_build.py` so non-interactive runs fail early unless sudo credentials are already cached, the command runs from an interactive terminal, or `VPHONE_SUDO_PASSWORD` is set.
- 2026-04-21 23:53 - Stopped the DFU VM process after SHSH acquisition. No `vphone-cli --dfu` process remains.
- 2026-04-22 00:02 - Restarted DFU and ran `make restore VM_DIR=vm RESTORE_UDID=0000FE01-FD01E5DAE1ED866F RESTORE_ECID=0xFD01E5DAE1ED866F`. Restore exited 0 after transferring `54272` filesystem items and completing `verify-restore`.
- 2026-04-22 00:02 - Post-restore boot reached the restored disk:
  - `BSD root: disk0s1`
  - `apfs_vfsop_mountroot: apfs: mountroot called`
  - `disk1s1 Rooting from snapshot with xid 61`
  - `authenticate_root_hash: disk1s1:61 successfully validated on-disk root hash`
  - `libignition` boot spec `local`
- 2026-04-22 00:02 - Post-restore boot then panicked in `launchd` because userspace was incomplete: `Library not loaded: /usr/lib/libSystem.B.dylib`, `no dyld cache`, `initproc failed to start`. Treat this as a runtime blocker to validate after ramdisk/CFW install, not a firmware patch pipeline failure yet.
- 2026-04-22 07:35 - Corrected the operator flow after a `sudo make ramdisk_build ...` attempt forced SwiftPM to rebuild `.build/` as root and left root-owned Capstone object files. Removed the stale root-owned build outputs, rebuilt `vphone-cli` as the normal user, and added a Makefile/script guard: run plain `make ramdisk_build`; let `ramdisk_build.py` sudo only the `hdiutil` mount/detach steps.
- 2026-04-22 07:36 - `make ramdisk_build VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76 RAMDISK_UDID=0000FE01-FD01E5DAE1ED866F` completed successfully after sudo credentials were cached with `sudo -v`. Verified the outputs from that run were present and non-empty:
  - `iBSS.vresearch101.RELEASE.img4`
  - `iBEC.vresearch101.RELEASE.img4`
  - `sptm.vresearch1.release.img4`
  - `DeviceTree.vresearch101ap.img4`
  - `sep-firmware.vresearch101.RELEASE.img4`
  - `txm.img4`
  - `krnl.ramdisk.img4`
  - `krnl.img4`
  - `trustcache.img4`
  - `ramdisk.img4`
- 2026-04-22 07:36 - Mount cleanup verified: no `/Users/vinay/vphone-cli/vm/SSHRD` mount remains after ramdisk build.
- 2026-04-22 07:51 - Runtime ramdisk send split:
  - Attempt 1 used generated `krnl.ramdisk.img4`; `ramdisk_send` completed all 8 iBoot stages and issued `bootx`, but no kernel serial, `irecv`, or usbmux endpoint appeared. VM stayed alive, so this is a candidate early kernel handoff/hang for the derived ramdisk kernel.
  - Attempt 2 forced fallback to `krnl.img4` by moving `krnl.ramdisk.img4` aside. This booted successfully: serial showed `BSD root: md0`, `mount-complete volume ramdisk`, `boot spec name: ramdisk`, `Starting ramdisk tool`, `USB init done`, `SSHRD_Script`, and `Running server`.
  - usbmux listed `0000FE01-FD01E5DAE1ED866F`, `pymobiledevice3 usbmux forward --serial 0000FE01-FD01E5DAE1ED866F 2222 22` worked in foreground, and SSH returned `ready` with password `alpine`.
- 2026-04-22 07:51 - Updated the iOS 18 profile behavior so future `ramdisk_build` does not generate `krnl.ramdisk.img4` and `ramdisk_send` does not prefer a stale `krnl.ramdisk.img4` when `FIRMWARE_PROFILE=ios18-22F76`.
- 2026-04-22 07:51 - CFW install is now blocked only by host sudo cache: `sudo -n true` returns `sudo: a password is required`. Do not start `cfw_install_dev` non-interactively until sudo is refreshed.
- 2026-04-22 08:10 - `make cfw_install_dev VM_DIR=vm SSH_PORT=2222` completed over the SSH ramdisk. High-signal stages:
  - SystemOS Cryptex copied to `/mnt1/System/Cryptexes/OS`; dyld cache chunks are present under `/System/Library/Caches/com.apple.dyld`.
  - AppOS Cryptex copied to `/mnt1/System/Cryptexes/App`.
  - `launchd` jetsam guard patched at file offset `0xD618` (`tbnz` -> `b`).
  - `debugserver` entitlements patched with `task_for_pid-allow`.
  - APFS update snapshot renamed to `orig-fs`.
  - `launchd_cache_loader` patched at file offset `0xB58` (`cbz` -> `nop`).
  - `mobileactivationd` patched at file offset `0x17320` (`mov x0, #1; ret`).
  - `vphoned`, `bash`, `dropbear`, `trollvnc`, and `rpcserver_ios` LaunchDaemons injected.
  - Device filesystems unmounted and ramdisk halted.

## Documentation Rules For This Branch

Use these docs instead of a repo TODO file:

| Document | Purpose |
| --- | --- |
| `research/ios-18-preparations.md` | Current state, blockers, implementation plan, verifier gates |
| `research/ios-18-firmware-deep-dive.md` | Narrative technical log: what was inspected, what failed, what IDA showed |
| `research/0_binary_patch_comparison.md` | Must be updated when patch logic changes or new patch behavior is introduced |

Do not let important context live only in terminal scrollback. Every meaningful dry-run, IDA finding, patch miss, and boot result should land in one of the research docs before moving to the next slice.

## Next Immediate Work

1. Run first normal boot after CFW: `make boot VM_DIR=vm`.
2. Capture whether the old pre-CFW dyld failure is gone: `libignition ... cryptex1 ... failed`, `Library not loaded: /usr/lib/libSystem.B.dylib`, `no dyld cache`, or `panic: initproc failed to start`.
3. If boot reaches userspace, verify post-CFW services: SSH on port `22222`, `dropbear`, `vphoned`, `rpcserver_ios`, and whether activation state is usable.
4. If boot panics before userspace, paste the last 150-250 serial lines into this doc and triage the failing layer before changing offsets.
