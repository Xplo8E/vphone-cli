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

## Board Identity Model

There are two different identities in this project, and mixing them up causes wrong conclusions:

| Layer | Existing iOS 26 / legacy flow | iOS 18.5 `22F76` flow | Meaning |
| --- | --- | --- | --- |
| VM / PV hardware identity | `vresearch101` / `vresearch101ap` | `vresearch101` / `vresearch101ap` | What Virtualization.framework exposes. Hardware descriptor uses PV=3, `boardID=0x90`, `CPID=0xFE01`; iBoot logs this as `Local boot, Board 0x90 (vresearch101ap)`. |
| Boot-chain identity | `vresearch101ap` | `vresearch101ap` | LLB, iBSS, iBEC, and research iBoot are selected from cloudOS `vresearch101ap` because the VM identifies this way in DFU/TSS. |
| Runtime firmware identity | `vphone600ap` | `vresearch101ap` | KernelCache, DeviceTree, SEP, RestoreDeviceTree, RestoreKernelCache, and RecoveryMode source. This is the part that changed for iOS 18.5. |

So the old officially working path is not "pure vphone600". It is a hybrid: `vresearch101ap` boot chain with `vphone600ap` runtime components. The new iOS 18.5 path is `vresearch101ap` for both boot chain and runtime components because local cloudOS 18.5 only has `j236cap`, `j475dap`, and `vresearch101ap` build identities. Local cloudOS 26.3 still has both `vphone600ap` and `vresearch101ap`, which is why the legacy runtime selection was possible there.

Current 18.5 hybrid output confirms the profile selection:

| Component | 18.5 path |
| --- | --- |
| LLB | `Firmware/all_flash/LLB.vresearch101.RELEASE.im4p` |
| iBoot | `Firmware/all_flash/iBoot.vresearch101.RESEARCH_RELEASE.im4p` |
| KernelCache | `kernelcache.research.vresearch101` |
| DeviceTree | `Firmware/all_flash/DeviceTree.vresearch101ap.im4p` |
| SEP | `Firmware/all_flash/sep-firmware.vresearch101.RELEASE.im4p` |
| RecoveryMode | absent for `vresearch101ap` |

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
| superseded | First standalone normal boot after the original CFW attempt did not reach the kernel. | `make boot VM_DIR=vm` loaded local `LLB.vresearch101.RELEASE` from disk and repeatedly entered `MODE: Recovery` / `Entering recovery mode, starting command prompt` before any `BSD root`, `authenticate_root_hash`, or `libignition` output. `irecovery -q` saw ECID `0xfd01e5dae1ed866f`, `MODE: Recovery`. `setenv auto-boot true`, `saveenv`, `fsboot`, and `irecovery -n` only looped back to the same LLB recovery prompt. | Superseded by the iOS 18.5 LLB auth-blob bypass below. This row is kept as historical context for the recovery-loop symptom. |
| confirmed | Experimental iOS 18.5 LLB auth-blob bypass is implemented, restored, and gets normal boot past LLB. | `IBootPatcher` now receives `FirmwareProfile`; for `ios18-22F76` LLB it semantically finds the adjacent `system-volume-auth-blob` / `boot-path` string pair and NOPs the nearby `BL helper; TBNZ W0,#31,<recovery>` failure branch. Direct verifier emitted `0x001CE8: tbnz w0,#0x1f,0x1d90 -> nop`; full `make fw_patch_dev VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76` emitted the same line and increased the dev patch count to 62; `make restore` completed `verify-restore: 100/100`; next normal boot no longer stopped at `7ab90c923dae682:1819` and reached XNU/APFS/Preboot. | This was the missing piece for the normal-boot recovery loop. LLB recovery fallback is no longer the active blocker. |
| confirmed | Post-restore userspace is incomplete until CFW installs Cryptexes. | Normal boot after the patched restore reached `disk1s5 mount-complete volume Preboot`, then `libignition: cryptex1 sniff: ignition failed: 8`, `ignite() returned 8`, `ignition disabled`, and panicked in `launchd`: `Library not loaded: /usr/lib/libSystem.B.dylib`, `no such file, no dyld cache`, `initproc failed to start`. | This is expected before CFW on this workflow. Next phase is to boot the SSH ramdisk and rerun `cfw_install_dev`, which copies SystemOS/AppOS Cryptexes and patches `launchd_cache_loader`. |
| confirmed | Normal boot after CFW reaches root shell on iOS 18.5. | After rerunning ramdisk + `cfw_install_dev`, normal boot reached `bash-4.4#`; `id` returned `uid=0(root) gid=0(wheel)`, `/var` is readable, and the host window shows `VPHONE [connected]`, indicating `vphoned` connected. Serial still prints expected noisy first-boot messages such as vnode jetsam and `AppleSEPKeyStore` selector failures. | Core iOS 18.5 dev bring-up is alive. Remaining active blocker is the visual UI staying on the black progress screen after root shell/vphoned are already up. |
| confirmed | SpringBoard load-gate plist experiment is a dead end and must not be repeated casually. | Offline probe showed SpringBoard exists in both `/System/Library/LaunchDaemons/com.apple.SpringBoard.plist` and embedded `/System/Library/xpc/launchd.plist`, with `_LimitLoadFromClarityMode=true` and `LimitLoadFromHardware = { osenvironment = [diagnostics] }`. Removing those gates by Python `plistlib` reserialization caused `launchd` panic: `initproc exited -- exit reason namespace 7 subcode 0x1 description: No service cache`. Byte rollback restored gates but did not fix the panic; rebuilding the active CFW launchd cache removed the panic and returned to the previous stuck-progress state. | Do not round-trip `/System/Library/xpc/launchd.plist` with generic plist tooling. Future UI work should target lower-level environment/Clarity state or inject diagnostics through the existing CFW cache path. |
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
- 2026-04-22 08:58 - Retried the manual README flow from the patching boundary. `ramdisk_build` now emits only `krnl.img4` for `ios18-22F76`, ramdisk boots to `SSHRD_Script` / `Running server`, and CFW can be re-run when the usbmux forward is kept open. First standalone `make boot` after CFW still loops at LLB recovery:
  - `Local boot, Board 0x90 (vresearch101ap)`
  - `Entering recovery mode, starting command prompt`
  - `irecovery -q` reports `MODE: Recovery`
  - `setenv auto-boot true`, `saveenv`, `fsboot`, and `irecovery -n` do not continue into kernel boot.
  - README first-boot shell commands require `bash-4.4#`; we are not reaching that layer.
- 2026-04-22 09:35 - Ruled out host-side NVRAM-preservation hypothesis.
  - `sources/vphone-cli/VPhoneVirtualMachine.swift` was changed to open existing NVRAM via `VZMacAuxiliaryStorage(contentsOf:)` instead of `creatingStorageAt:.allowOverwrite`.
  - With a freshly-created NVRAM the VM stuck in SecureROM/DFU and never reached LLB (`MODE: DFU`, `SRTG: mBoot-18000.101.7`). Strict regression vs `.allowOverwrite`.
  - With the pre-existing `nvram.bin` preserved, LLB still emitted the same hash sequence (`7ab90c923dae682:1819`) then `Entering recovery mode`.
  - Code reverted. NVRAM is not the root cause; the recovery fallback is decided by state on disk or LLB's own internal validation before NVRAM boot-selection matters.
- 2026-04-22 09:45 - Captured full iBoot hash sequence from serial:
  ```
  3974bfd3d441da3:1557
  3974bfd3d441da3:1628
  f6ce2cad806de9b:184
  9905b4edc794469:939
  f6ce2cad806de9b:204
  7ab90c923dae682:1819   <- immediate pre-recovery emitter
  Entering recovery mode, starting command prompt
  337a834f05a86eb:373
  ea0f64a4253252:981     <- heartbeat, repeats
  ```
  Extracted raw LLB to `/tmp/llb.vresearch101.raw` (from `LLB.vresearch101.RELEASE.im4p`, 568168 bytes, uncompressed, unencrypted, AArch64). Next session: decode `7ab90c923dae682:1819` in Binary Ninja to name the failing condition.
- 2026-04-22 12:40 - Added the experimental iOS 18.5 LLB LocalPolicy boot-object bypass.
  - Code: `IBootPatcher(data:mode:firmwareProfile:)` keeps legacy behavior by default.
  - Profile scope: only `mode == .llb && firmwareProfile == .ios18_22F76`.
  - Semantic target: adjacent `system-volume-auth-blob` / `boot-path` string pair, then nearby `BL <auth blob helper>; TBNZ W0,#31,<recovery bail>`.
  - Direct verifier on the current 18.5 LLB emitted:
    ```text
    0x001CE8: tbnz w0, #0x1f, 0x1d90 -> nop
    ```
  - `make patcher_build` passed. `swift test --filter LLBComparisonTests` built but could not execute the comparison because `ipsws/patch_refactor_input/raw_payloads/llb.bin` is absent in this checkout.
- 2026-04-22 12:53 - Refreshed the real `vm/` disk with the experimental LLB patch installed.
  - `make fw_prepare VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76 ...` completed and regenerated the hybrid tree from local iPhone/cloudOS 18.5 IPSWs.
  - `make fw_patch_dev VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76` completed with 62 total dev patches. The LLB section emitted `0x001CE8: tbnz w0,#0x1f,0x1d90 -> nop` and reported `10 llb patches applied`.
  - `make restore_get_shsh ...` saved `FD01E5DAE1ED866F.shsh`.
  - `make restore ...` completed filesystem transfer and `verify-restore: 100/100`.
  - Next evidence gate is normal boot from the restored disk: confirm whether the old `7ab90c923dae682:1819` recovery fallback is gone.
- 2026-04-22 13:05 - Normal boot from the patched restore confirmed the LLB fix.
  - Boot no longer stops at `7ab90c923dae682:1819` / `Entering recovery mode`.
  - Kernel/APFS reached Preboot: `disk1s5 mount-complete volume Preboot`.
  - New active blocker is expected pre-CFW Cryptex/userspace failure: `libignition: cryptex1 sniff: ignition failed: 8`, `Library not loaded: /usr/lib/libSystem.B.dylib`, `no dyld cache`, `initproc failed to start`.
  - Next phase: boot SSH ramdisk and rerun `cfw_install_dev` on this freshly restored disk.
- 2026-04-22 13:15 - First `ramdisk_build` retry failed during the host `patcher_build` dependency with no real compiler diagnostic in the tee log. Isolated `make patcher_build` completed successfully afterward with only the known non-fatal Swift object verification warning for `VPhoneKeychainWindowController.swift.o`. Treat this as a transient parallel SwiftPM build failure; rerun `ramdisk_build` without cleaning.
- 2026-04-22 14:10 - Normal boot after rerunning CFW reached the expected dev direct console.
  - `bash-4.4# id` returned `uid=0(root) gid=0(wheel) groups=...`.
  - `/var` is accessible and populated.
  - Host window title shows `VPHONE [connected]`, so the guest `vphoned` control path is alive.
  - Screen remains black with a white progress bar after a long wait; treat this as separate UI/SpringBoard/first-boot state, not a boot-chain failure.
- 2026-04-22 14:25 - First-boot README commands were already run while the progress bar was around 75%, then the VM rebooted and loaded from 0% to full progress over roughly one hour. It still did not transition to visible UI. Active slice is now late userspace/UI: SpringBoard, backboardd, Setup/Buddy, activation, RunningBoard, or display services.
- 2026-04-22 14:35 - UI process probe while the progress bar reset/loaded again:
  - Alive: `/usr/libexec/runningboardd`, `/usr/libexec/backboardd`, `/usr/libexec/mobileactivationd`, `/usr/bin/vphoned`, Dropbear, TrollVNC, `rpcserver_ios`.
  - Missing from `ps`: `SpringBoard`, Setup/Buddy, FrontBoard-named process.
  - `launchctl print system/com.apple.SpringBoard`, `system/com.apple.backboardd`, `system/com.apple.runningboardd`, and `system/com.apple.mobileactivationd` all returned `Could not find service ... in domain for system`, even though several of those processes exist. Need enumerate actual launchd labels/domains instead of assuming macOS-style `system/<label>`.
  - Current hypothesis: UI is stuck because SpringBoard is not being launched or is immediately failing before it appears in `ps`.
- 2026-04-22 14:45 - SpringBoard files are present: `/System/Library/CoreServices/SpringBoard.app/SpringBoard` exists and is executable, `/System/Library/LaunchDaemons/com.apple.SpringBoard.plist` exists, and `/System/Library/xpc/launchd.plist` still contains the SpringBoard launch entry. This rules out missing SpringBoard payload. Active question is why launchd is not registering/starting the job.
- 2026-04-22 14:50 - Manual `launchctl bootstrap system /System/Library/LaunchDaemons/com.apple.SpringBoard.plist` returned `Service cannot load in requested session`. That is high-signal: SpringBoard is not loadable in the `system` domain on this iOS build. Next test should target the mobile GUI/user domain (`gui/501` or `user/501`) and inspect `LimitLoadToSessionType` / MachServices from the SpringBoard plist.
- 2026-04-22 14:58 - `launchctl help` from the guest confirms this iosbinpack64 launchctl explicitly says `user/<uid>` and `gui/<uid>` domains do not exist on iOS; legacy subcommands target the system domain. The serial console is now noisy enough to corrupt pasted commands (`launchctl load ...` appeared to execute as a stale `grep` pipeline), so continue UI launchd triage over SSH instead of the direct serial shell.
- 2026-04-22 15:05 - SSH triage blocker: host usbmux forward is listening on `127.0.0.1:2222`, but `ssh -p 2222 root@127.0.0.1` returns `Connection closed by 127.0.0.1`. This usually means Dropbear accepted the TCP connection and closed during handshake. Next checks: restart the usbmux forward after the reboot, verify `/var/dropbear/dropbear_*_host_key` exists in the guest, and restart the `Dropbear` launchd job.
- 2026-04-22 15:12 - Host forward verified correct: local `127.0.0.1:2222` is `pymobiledevice3 usbmux forward --serial 0000FE01-FD01E5DAE1ED866F 2222 22222`. Guest host keys exist and can be regenerated. Manual foreground Dropbear on `22222` fails with `Address already in use` because launchd immediately restarts the `Dropbear` job after `killall`. Next test should avoid launchd by running foreground Dropbear on alternate guest port `22223` and forwarding host `2223 -> 22223`.
- 2026-04-22 15:18 - Alternate host forward verified correct: local `127.0.0.1:2223` is `pymobiledevice3 usbmux forward --serial 0000FE01-FD01E5DAE1ED866F 2223 22223`. OpenSSH still closes pre-banner on `2223`, so if foreground Dropbear was actually running on guest `22223`, the next required evidence is its stderr/stdout. If there was no foreground Dropbear output, the guest listener may not have stayed up.
- 2026-04-22 15:25 - Decision: stop fighting noisy live serial/Dropbear for UI triage. Added `scripts/ios18_offline_ui_probe.sh` for DFU/SSH-ramdisk collection. It mounts the installed disk at `/mnt1`, collects SpringBoard/backboard/runningboard/mobileactivation/Buddy launch plists plus `xpc/launchd.plist` and `.bak`, converts them with host `plutil`, and writes diffs/strings into `vm/offline_ui_probe_*`.
- 2026-04-22 16:10 - Offline UI probe result:
  - SpringBoard is present in both `/System/Library/LaunchDaemons/com.apple.SpringBoard.plist` and embedded `/System/Library/xpc/launchd.plist`.
  - The SpringBoard dictionary in patched `launchd.plist` matches `launchd.plist.bak`; CFW daemon injection only added bash/dropbear/rpcserver/trollvnc/vphoned entries and did not alter SpringBoard.
  - SpringBoard load gates are `_LimitLoadFromClarityMode=true` and `LimitLoadFromHardware = { osenvironment = [diagnostics] }`.
  - Hypothesis: on the `vresearch101ap` iOS 18.5 path, launchd sees a Clarity/diagnostics-like hardware/session state and suppresses SpringBoard. Added `scripts/ios18_patch_springboard_load.sh` to remove those two gates from both the standalone SpringBoard plist and the embedded launchd database as a targeted experiment.
- 2026-04-22 16:17 - SpringBoard load-gate experiment failed and must be rolled back.
  - `scripts/ios18_patch_springboard_load.sh` successfully removed `_LimitLoadFromClarityMode` and `LimitLoadFromHardware` from the standalone SpringBoard plist and embedded launchd service cache copy.
  - Normal boot then panicked in `launchd`:
    - `launchd_cache_loader` printed `Using unsecure cache: /System/Library/xpc/launchd.plist` and `Cache sent to launchd successfully`.
    - Kernel panic was `initproc exited -- exit reason namespace 7 subcode 0x1 description: No service cache`.
  - Interpretation: directly round-tripping `/System/Library/xpc/launchd.plist` with Python `plistlib` is unsafe even when the result is still a valid binary plist. Apple launchd's service cache has constraints beyond generic plist parseability.
  - Action taken: added `scripts/ios18_restore_springboard_load_backup.sh` to copy the `.ios18-ui-bak` files back byte-for-byte from the SSH ramdisk, and guarded `scripts/ios18_patch_springboard_load.sh` behind `IOS18_ALLOW_UNSAFE_LAUNCHD_PLIST_PATCH=1`.
  - Next rule: do not edit `launchd.plist` via generic plist reserialization. Future UI experiments should either use the existing CFW patcher path that already preserves launchd semantics, patch lower-level hardware/environment state, or collect more launchd cache evidence first.
- 2026-04-22 16:25 - Byte rollback restored the SpringBoard load gates but normal boot still panicked with `No service cache`.
  - The rollback log verified `_LimitLoadFromClarityMode` and `LimitLoadFromHardware` are present again in both restored files.
  - The boot log still reaches `launchd_cache_loader` and panics after `Cache sent to launchd successfully`.
  - New recovery action: added `scripts/ios18_rebuild_cfw_launchd_cache.sh`, which performs only the final CFW LaunchDaemon phase: install our daemon plists, rebuild active `/System/Library/xpc/launchd.plist` from `/System/Library/xpc/launchd.plist.bak` using the existing CFW injector, and verify bash/dropbear/trollvnc/vphoned/rpcserver entries. If this still panics, rerun full `cfw_install_dev`.
- 2026-04-22 16:35 - Fast CFW launchd-cache rebuild recovered from the `No service cache` panic.
  - After `scripts/ios18_rebuild_cfw_launchd_cache.sh`, normal boot no longer panics.
  - The VM returns to the same state as before the SpringBoard gate experiment: root/userspace alive, but visual UI still stuck on the black progress screen.
  - Conclusion: the gate-removal experiment did not solve UI bring-up. The only useful outcome was learning that direct generic reserialization of `launchd.plist` can poison launchd's service cache. Current blocker remains SpringBoard/UI state, not boot-chain or CFW recovery.

## Documentation Rules For This Branch

Use these docs instead of a repo TODO file:

| Document | Purpose |
| --- | --- |
| `research/ios-18-preparations.md` | Current state, blockers, implementation plan, verifier gates |
| `research/ios-18-firmware-deep-dive.md` | Narrative technical log: what was inspected, what failed, what IDA showed |
| `research/0_binary_patch_comparison.md` | Must be updated when patch logic changes or new patch behavior is introduced |

Do not let important context live only in terminal scrollback. Every meaningful dry-run, IDA finding, patch miss, and boot result should land in one of the research docs before moving to the next slice.

## Current Active Blocker

The normal-boot recovery loop is fixed. The missing piece was the iOS 18.5 LLB `system-volume-auth-blob` failure branch:

```text
LLB.vresearch101.RELEASE
sub_1928:
  BL   sub_16E9C("system-volume-auth-blob", "boot-path", ...)
  TBNZ W0,#31,loc_1D90   ; negative lookup result -> 1819 recovery fallback
```

The profile-scoped patch NOPs that branch on `ios18-22F76` LLB only:

```text
0x001CE8: tbnz w0, #0x1f, 0x1d90 -> nop
```

Evidence chain:

1. Before the patch, normal boot stopped at `7ab90c923dae682:1819` and entered iBoot recovery before XNU.
2. After `fw_patch_dev` emitted the `0x001CE8` NOP and restore completed, normal boot passed LLB and reached XNU/APFS/Preboot.
3. After CFW reinstall, normal boot reaches root shell and `vphoned`.

Current blocker is late userspace/UI only:

```text
working:
  LLB -> XNU -> APFS -> Cryptex via CFW -> launchd -> root shell -> vphoned

not working:
  visible SpringBoard/home UI
```

The VM currently returns to the black progress screen state without the `No service cache` panic after rebuilding the CFW launchd cache.

Do not repeat the SpringBoard load-gate removal as-is. It caused a launchd service-cache panic and did not solve the UI:

```text
panic: initproc exited -- exit reason namespace 7 subcode 0x1 description: No service cache
```

Next useful UI work:

1. Collect live launchd evidence from the recovered stuck-progress state without editing `launchd.plist`: `launchctl print-cache`, `launchctl dumpstate`, process list, and SpringBoard/backboard logs if available.
2. Reverse where `LimitLoadFromHardware` gets its `osenvironment=diagnostics` decision, likely DeviceTree/chosen or launchd hardware-state plumbing.
3. If adding boot diagnostics, inject them through the CFW launchd-cache path, not by standalone `plistlib` edits to `/System/Library/xpc/launchd.plist`.

### 2026-04-22 serial-shell investigation on stuck 100% boot

The progress bar reaches 100% but SpringBoard never shows. Serial shell reached (`bash-4.4#` over PL011). Two *independent* failures were identified.

#### Failure A: SpringBoard crash loop (UIKit idiom assertion)

- `/var/mobile/Library/Logs/CrashReporter/SpringBoard-2026-04-22-023653.ips`
- `consecutiveCrashCount: 20`, `throttleTimeout: 1200` - SpringBoard has been crashing since boot.
- `exception: EXC_CRASH / SIGABRT`, `abort() called`, reason: `NSAssertionHandler` fired inside UIKit.
- Crashing thread stack (trimmed):
  ```
  -[NSAssertionHandler handleFailureInFunction:file:lineNumber:description:]
  _UIDeviceNativeUserInterfaceIdiomIgnoringClassic
  __24+[UIKeyboard inputUIOOP]_block_invoke
  +[SBInputUISceneController _shouldControlInputUIScene]
  +[SBSystemUIScenesCoordinator _sceneControllersConfigurations]
  -[UISApplicationSupportService initializeClientWithParameters:completion:]
  ```
- `modelCode: "ComputeModule14,2"` in the crash report. `ioreg -rc IOPlatformExpertDevice` confirms `model = "ComputeModule14,2"` from IOPlatformDevice.
- UIKitCore's `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` resolves the device UI idiom from MobileGestalt (`ProductType` / `DeviceClassNumber`) and asserts the answer is in a known enum set (Phone/Pad/TV/CarPlay/Watch/Vision/Mac/Realitykit/etc.). `ComputeModule14,2` is PCC vresearch virtualization - not in the whitelist for iOS 18.5. The idiom resolver returns an out-of-set value, NSAssertion fires, SpringBoard aborts. AccessibilityUIServer crashes for the same reason (separate `.ips` files for it).
- MobileGestalt cache exists on disk and is readable:
  - `/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist` (8866 bytes, `mobile:mobile` owner, parent dir is `d---------+` so only UID `mobile`/`nobody` can traverse via plist-lookup APIs; direct read from root works).

#### Failure B: com.apple.datamigrator hung for 10+ minutes

- `/var/mobile/Library/Logs/CrashReporter/stacks+com.apple.datamigrator-2026-04-22-040605.ips` (bug type 288 = PRECAUTIONARY stackshot, not crash).
- `reason: "PRECAUTIONARY stackshot - migration might be hung or deadlocked. Plugin: com.apple.locationd.migrator (CoreLocationMigrator.migrator) (10 minutes) (overall migration start 155134195) (erase)"`
- Thread 877 (main migration dispatch) blocked on thread 6361; 10 plugin threads blocked on thread 877.
- Both `com.apple.datamigrator` (pid 130, started 03:54) and `com.apple.migrationpluginwrapper` (pid 649, started 03:56) still running idle at time of capture.
- This is the "stuck at 100%" wall. Even once SpringBoard can start, the boot progress sequence will not hand off until datamigrator completes or is given up.
- Migration sentinel paths checked: `/var/db/`, `/var/mobile/Library/`, `/var/root/Library/Caches/` — no obvious `com.apple.datamigrator.done` or `migration-complete` file. Needs deeper search.

#### Other boot-state signals captured

- Mounts are healthy:
  ```
  /dev/disk1s1 on / (apfs, sealed, local, read-only, journaled, noatime)
  /dev/disk1s2 on /private/var (apfs, local, nodev, nosuid, journaled, noatime, protect)
  /dev/disk1s5 on /private/preboot ... /dev/disk1s3 on /private/xarts ... /dev/disk1s6 on /private/var/MobileSoftwareUpdate ... /dev/disk1s4 on /private/var/hardware
  df shows 12Gi used on rootfs, 964Mi on var, plenty free.
  ```
- NVRAM looks healthy: `auto-boot=true`, `boot-breadcrumbs` trail shows full boot chain (rkrn -> ibec -> sptm -> trxm -> rtsc -> rdsk -> rdtr), no `recovery-boot-mode` set.
- Launchd daemons mostly running (100+ processes from `ps`). Notably running: `backboardd`, `locationd`, `cfprefsd`, `lsd`, `cfprefsd`, `containermanagerd`, `analyticsd`, `apsd`, `lockdownd`, `runningboardd`. SpringBoard/AccessibilityUIServer only visible as corpse-release / respawn spam in `dmesg`.
- dmesg shows a respawn storm: `fairplayd.H2`, `spaceattributiond`, `webbookmarksd`, `chronod`, `kbd`, `healthd` repeatedly forked and reaped; vnode jetsam already hitting 1024 desired / 1947 numvnodes, killing idle services to reclaim. That is a downstream symptom of SpringBoard never coming up, not a separate problem.
- One repeated kernel log line: `"AppleSEPKeyStore":12667:559: operation failed (sel: 35 ret: e00002f0)` correlates with `AKS` sel 35 (likely key bag / passcode derivation). On a fresh PCC VM with no passcode set this is expected and harmless; noted so we do not chase it.

#### Current UI unblock state

The UIKit idiom hypothesis has moved from hypothesis to installed fix. IDA proved the crashing path reads only `DeviceClassNumber`, and normal boot now confirms the boot-time patcher wrote `CacheExtra["DeviceClassNumber"] = 1` into the MobileGestalt cache:

```text
/private/var/root/.vphone_mobilegestalt_patched
[vphone_mgpatch] patched /private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist
```

Next diagnostic split: if new SpringBoard crash reports no longer mention `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic`, the MobileGestalt fix worked and the remaining stuck progress bar is a different UI/userspace blocker. If the same assertion still appears, the cache override is not the authoritative answer source and the next durable lever is DeviceTree identity spoofing before MobileGestalt cache generation.

Secondary lever: bypass or unblock `com.apple.datamigrator`. Options in order of reversibility:
- Forcibly `kill -9` pids 130 and 649 and see if backboardd/SpringBoard progresses (SpringBoard is crash-looping for UIKit reasons, but backboardd migration-queue may unblock).
- `launchctl bootout system/com.apple.datamigrator` then `launchctl disable system/com.apple.datamigrator`.
- Discover the migration-done sentinel and touch it (needs more hunting inside `DataMigration.framework`).

#### Next actions

1. Collect newest SpringBoard / AccessibilityUIServer crash reports and verify whether `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` disappeared.
2. Dump `CacheExtra["DeviceClassNumber"]` from the live MobileGestalt cache to prove the on-disk state matches the patcher stamp.
3. If the UIKit idiom assertion is gone but UI is still stuck, focus on `com.apple.datamigrator` and migration sentinels.
4. If the same assertion remains, test DeviceTree identity spoofing (`ProductType`/compatible/target-type source path) before MobileGestalt cache generation.
5. Capture whatever new dmesg / crash reports appear after each step. Do NOT reboot until diagnostics are saved somewhere durable on `/private/var` (not under `/` which is sealed RO).

#### IDA confirmation of UIKit idiom resolver

Follow-up IDA analysis of `/tmp/uikit_extract/UIKitCore` confirms the cheap verification item above. See [uikit-idiom-assertion.md](uikit-idiom-assertion.md).

Key correction: `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` does **not** directly read `ProductType`, `HWModelStr`, `HWMachine`, or `DeviceClass` on this path. It reads only `DeviceClassNumber`, converts the returned object with `intValue`, and asserts if the number is not in UIKit's accepted raw device-class set.

Smallest SpringBoard-crash fix to test:

```text
MobileGestalt DeviceClassNumber = 1
```

That maps to return value `0` (`UIUserInterfaceIdiomPhone`) and should avoid the `UIDevice.m:852` assertion. `ProductType = iPhone17,3` can still be tested as a broader compatibility override, but it is not required for this specific `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` assertion.

Implementation:

- `scripts/patchers/cfw_patch_mobilegestalt.py` still contains the deterministic plist patch logic: `CacheExtra["DeviceClassNumber"] = 1`.
- Direct ramdisk editing of the Data-volume cache is kept only as a diagnostic helper because Data currently hangs under `mount_apfs` from the ramdisk.
- `scripts/cfw_install_dev.sh` now installs the boot-time patcher as phase `7/8`: `/usr/bin/vphone_mgpatch` plus `/System/Library/LaunchDaemons/vphone_mgpatch.plist`.
- `scripts/patchers/cfw_daemons.py` injects `vphone_mgpatch.plist` into `/System/Library/xpc/launchd.plist` together with the existing CFW daemons.

Fast test path after installing the boot-time patcher:

```bash
make boot VM_DIR=vm 2>&1 | tee vm/logs/ui_after_mobilegestalt_boot_patcher.log
```

Verifier after normal boot reaches shell:

```sh
cat /private/var/root/.vphone_mobilegestalt_patched
cat /private/var/log/vphone_mgpatch.log
```

### 2026-04-22 MobileGestalt ramdisk patch helper SSH stall

While testing the targeted UIKit idiom fix, `scripts/ios18_patch_mobilegestalt_cache.sh` could stall during the ramdisk SSH/mount phase. The observed output was repeated SSH connection-loss retries around `echo ready`, `/mnt2` creation, or mounting `/dev/disk1s2` as the installed Data volume. This is not a MobileGestalt plist parsing failure; it happens before the cache is copied back to the host. The likely states are either the ramdisk SSH service is still unstable after boot, the host port-forward is connected to a half-ready ramdisk, or the APFS mount command is wedging/resetting the remote shell.

The helper was hardened with short SSH connect timeouts, server-alive probes, a command-level timeout wrapper, and `IOS18_MOBILEGESTALT_PROBE_ONLY=1` mode. The probe prints current ramdisk mounts and `/dev/disk1*` devices before attempting to mount `/mnt2`. This lets us verify whether `/dev/disk1s2` exists and whether `/mnt2` is already mounted before doing the cache patch.

Follow-up: the helper no longer assumes `disk1s2`. It now scans candidate APFS volumes (`disk1s2`, `disk1s6`, `disk1s5`, `disk1s4`, `disk1s3`, `disk1s1`) and stops on the first mounted volume that contains `containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist`. This is safer for the 18.5 APFS layout because the visible BSD slice number is not strong evidence of APFS role.

### 2026-04-22 MobileGestalt fix pivot: boot-time patcher

Direct ramdisk patching of the Data-volume MobileGestalt cache was abandoned. Evidence: APFS role probing showed `/dev/disk1s2` is `Data` and `/dev/disk1s1` is `System`, but every `mount_apfs` attempt against Data hung until the command timeout fired (`rc=142`). System mounted cleanly. This points to a Data-volume mount/protection problem from the SSH ramdisk, not a wrong-slice issue.

The replacement is a boot-time patcher installed onto the mountable System volume. `scripts/ios18_mgpatch/vphone_mgpatch.m` is a tiny arm64 iOS Foundation binary. On normal boot it waits up to 180 seconds for `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist`, backs it up once as `.vphone_bak`, writes `CacheExtra["DeviceClassNumber"] = 1` as a binary plist, restores `501:501` ownership and `0644` mode, and writes `/private/var/root/.vphone_mobilegestalt_patched`.

Installed verification from the ramdisk:

```text
/mnt1/usr/bin/vphone_mgpatch
/mnt1/System/Library/LaunchDaemons/vphone_mgpatch.plist
/mnt1/System/Library/xpc/launchd.plist contains /System/Library/LaunchDaemons/vphone_mgpatch.plist
```

The launchd cache was also checked to still contain the existing CFW entries: `bash`, `dropbear`, `rpcserver_ios`, `trollvnc`, and `vphoned`. Future `cfw_install_dev` runs now install this boot-time patcher instead of trying to mount Data from the ramdisk.

### 2026-04-22 UIKitCore direct idiom patch

Latest SpringBoard and AccessibilityUIServer crash reports still hit `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` after the MobileGestalt boot-time patcher wrote `CacheExtra["DeviceClassNumber"] = 1`. That proves the cache edit is not authoritative for this UIKit path.

IDA/`ipsw` resolved the function to the iOS 18.5 SystemOS dyld shared cache:

```text
vaddr:    0x185599978
subcache: dyld_shared_cache_arm64e.03
offset:   0x1a5978
before:   pacibsp; stp x20, x19, [sp, #-0x20]!
after:    mov x0, #0; ret
```

The mounted Cryptex DMG is sealed/read-only, so the patch must be applied to the copied SystemOS Cryptex on the restored rootfs from the SSH ramdisk: `/mnt1/System/Cryptexes/OS/System/Library/Caches/com.apple.dyld/dyld_shared_cache_arm64e.03`. This is wired into `cfw_install_dev` and exposed as `scripts/ios18_patch_uikit_idiom_from_ramdisk.sh` for one-off testing.

Follow-up correction for the UIKitCore direct patch:

- `ipsw dyld a2o` printed aggregate cache offset `0x5599978`, but the writable target is the subcache file itself. Searching the expected prologue in `dyld_shared_cache_arm64e.03` resolved the actual file-local offset to `0x1a5978`.
- The first helper version tried to stage bytes through `/tmp` and `scp`, but Dropbear/SFTP could not see the temporary file. The helper now reads remote bytes over SSH stdout with `dd | xxd -p`.
- The next helper version used shell `printf '\x..'`; on the ramdisk shell that wrote literal ASCII bytes (`7830307830307838`, `x00x00x8`) instead of binary. This was repaired in place with `printf 000080d2c0035fd6 | xxd -r -p | dd ...`.
- Final verifier: `scripts/ios18_patch_uikit_idiom_from_ramdisk.sh` reports the copied SystemOS subcache is already patched at `/mnt1/System/Cryptexes/OS/System/Library/Caches/com.apple.dyld/dyld_shared_cache_arm64e.03+1726840`.

### 2026-04-22 Next active blocker: fairplayd.H2 crash-respawn loop

With the UIKitCore idiom patch landed, SpringBoard and AccessibilityUIServer no longer crash. Loading bar is visible full. No SpringBoard/AccessibilityUIServer crash reports are being emitted anymore. The new boot blocker is datamigrator → locationd → fairplayd.

Evidence chain from the newest datamigrator stackshot (`stacks+com.apple.datamigrator-2026-04-22-074133.ips`, 42 min hung, plugin `com.apple.locationd.migrator`):

```text
thread 1547: turnstile blocked on task pid 1, hops: 1, priority: 37
             (com.apple.fairplayd.versioned (service throttled by launchd))
thread  532: blocked on 1547
thread 1462: blocked on 1547
thread 1566: blocked on 1462 (com.apple.locationd.synchronous)
thread 2189: blocked on 1462 (com.apple.locationd.synchronous)
thread 2803: blocked on 1462 (com.apple.locationd.synchronous)
thread 2122: blocked on 1462
  → 36709 / 37809 / 37821: blocked on 2122
```

Translation: fairplayd.versioned is launchd-throttled (never stays alive long enough to answer Mach port lookups). Thread 1547 is inside `CLHarvestControllerSilo`'s fairplayd call site; locationd (1462) serializes on 1547; the CoreLocationMigrator plugin blocks on locationd; datamigrator blocks on the plugin; whole chain deadlocks at 100% progress.

dmesg confirms fairplayd respawn storm: `/usr/sbin/fairplayd.H2[782] ... ReportCrash[783] Corpse failure, too many 6` repeating every ~10s. Kernel corpse subsystem is at its 6-corpse cap, so fairplayd's own crash reports are being dropped — that's why `ls /var/mobile/Library/Logs/CrashReporter/ | grep -i fairplay` returns nothing.

Neither `launchctl print system/com.apple.fairplayd.H2` nor `.versioned` resolved — service label is in a different domain (possibly `user/…` or an XPC-registered subservice). fairplayd.H2 binary is at `/usr/sbin/fairplayd.H2` (21 MB, May 6 2025, stock — not touched by CFW).

Related kernel log that's probably upstream: `"AppleSEPKeyStore":12667:559: operation failed (sel: 35 ret: e00002f0)`. AKS selector 35 ~ key derivation; vresearch SEP likely has no usable key material for fairplayd's DRM identity.

Two remediation candidates:

1. **Disable the fairplayd LaunchDaemons at CFW install.** Rename `/System/Library/LaunchDaemons/com.apple.fairplayd*.plist` so launchd never tries to start them. Clients that call fairplayd get immediate `XPC_ERROR_CONNECTION_INVALID` or Mach port lookup failure instead of blocking. Minimum risk, matches existing CFW philosophy of disabling VM-incompatible services.
2. **No-op fairplayd.H2 binary.** Same pattern as `patch-mobileactivationd`: patch the Mach-O so it starts, registers its Mach services, and returns success on every XPC message without calling SEP. More invasive but yields better client compatibility.

Prefer (1) first — reversible by restoring the plist, and it isolates SEP-dependent code paths entirely from the VM. If (1) causes secondary failures (e.g., locationd crashes rather than hangs when the port lookup fails), fall back to (2).

Next actions:

1. Find the LaunchDaemon plist filenames and Labels: `find /System/Library/LaunchDaemons -name "*fairplay*"`.
2. Dump the plists, identify the exact Label strings used by launchd.
3. Confirm no other LaunchDaemon in `/System/Library/LaunchDaemons` lists a `MachService` matching `com.apple.fairplayd.versioned`.
4. Prototype by renaming the plist(s) on the live VM (`/System/Library/...` is RO sealed; do this from ramdisk), or at ramdisk time via `cfw_install_dev`.
5. After reboot, verify: datamigrator progresses past `com.apple.locationd.migrator`, locationd threads are no longer turnstile-blocked on fairplayd, home screen appears.

#### Implementation of fairplayd disable

Plists located: `/System/Library/LaunchDaemons/com.apple.fairplayd.H2.plist` (binary, Label `com.apple.fairplayd.H2`, UserName `mobile`, Program `/usr/sbin/fairplayd.H2`, MachServices registered via binary-plist dict) and `/System/Library/LaunchDaemons/com.apple.fairplaydeviceidentityd.plist` (XML, Label `com.apple.fairplaydeviceidentityd`, MachService `com.apple.fairplaydeviceidentityd`).

The turnstile error string `com.apple.fairplayd.versioned` is a MachService alias registered by `fairplayd.H2` (not a separate plist). Disabling `com.apple.fairplayd.H2.plist` removes that registration so clients fail port lookup fast instead of turnstile-blocking.

Implementation:

- `scripts/ios18_disable_fairplayd_from_ramdisk.sh` — standalone, idempotent ramdisk helper. Renames both plists to `*.plist.disabled` and keeps a one-time `*.plist.vphone_bak` so re-runs are safe and revert is just renaming back.
- `scripts/cfw_install_dev.sh` now runs `disable_remote_fairplayd` right after `patch_remote_uikit_idiom` during Cryptex install (both need `/mnt1` mounted rw; both disable VM-incompatible userspace services).

Test path: `make cfw_install_dev` picks up the new step. After it completes and normal boot reaches userspace, verify `ls /System/Library/LaunchDaemons/com.apple.fairplayd*` shows both as `.disabled`, no fairplayd respawn lines appear in `dmesg`, `ps auxww | grep -i springboard` shows SpringBoard running, and datamigrator either finishes or is skippable.

Revert path: rename `.plist.disabled` back to `.plist` (or use the `.vphone_bak` copy).

### 2026-04-22 CRITICAL: UIKitCore byte-patch violates codesign and kills all UIKit consumers

After fairplayd was disabled via `/var/db/com.apple.xpc.launchd/disabled.plist` (adding keys `com.apple.fairplayd.H2` / `.versioned` / `.chronod` / `.ndoagent` / `.WebBookmarks.webbookmarksd`), SSH over port 2222 became reachable and we captured real `ReportCrash` `.ips` files. They show:

```json
"exception": {"type":"EXC_CRASH","signal":"SIGKILL - CODESIGNING"}
"termination": {"namespace":"CODESIGNING","indicator":"Invalid Page"}
```

Every process that loads UIKit (SpringBoard, AccessibilityUIServer, ReportCrash, chronod, ndoagent, spaceattributiond, nanotimekitcompaniond, webbookmarksd) dies with this SIGKILL. This is not a UIKit idiom assertion, not fairplayd, not AKS - it is the kernel's AMFI walking the dyld shared cache code-directory hash tree, finding our patched page at `dyld_shared_cache_arm64e.03 + 0x1a5978` (`mov x0,#0 ; ret` replacing `pacibsp; stp x20, x19, [sp, #-0x20]!`) and killing the process with "Invalid Page".

The "Text page corruption detected in dying process" dmesg lines we chased earlier are a kernel post-mortem artifact of this same SIGKILL, not a separate cause.

The UIKit idiom byte-patch *does* bypass the NSAssertion on a single process load, but because the subcache page's CDHash no longer matches the signed value, every subsequent process that memory-maps that same page gets SIGKILLed by AMFI. The UI never comes up because SpringBoard dies to codesign before reaching its main, ReportCrash dies to codesign while trying to write crash reports, and the whole userspace cascades.

Options to unblock (ordered by risk):

1. **Add `amfi_get_out_of_my_way=1` to guest NVRAM boot-args.** The current guest boot-args are `serial=3 debug=0x104c04`. If the guest kernel honors `amfi_get_out_of_my_way` the same way the host does, AMFI will stop hash-verifying shared-cache pages and the patch can stand. Must be added in `sources/vphone-cli/VPhoneVirtualMachine.swift` where NVRAM `boot-args` are written.
2. **Revert the UIKitCore byte patch and find another way to make `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` return `UIUserInterfaceIdiomPhone`.** Options include a dyld-interposer dylib loaded via `DYLD_INSERT_LIBRARIES` in SpringBoard's launchd environment, or patching a different (non-shared-cache) binary that influences the answer.
3. **Rebuild the subcache code directory + shared-cache codesign blob** after the byte patch. This is the "correct" fix but requires understanding how `ipsw` signs / packages subcaches and how AMFI trust-cache entries need to be updated. Deeper work.

Option 1 is the cheapest test and matches what host macOS already uses (`amfi_get_out_of_my_way=1`). If it works the UIKit patch is durable; if it doesn't, we move to option 2 or 3.

### 2026-04-22 NVRAM boot-args investigation — Swift NVRAM not effective

Confirmed: `VZMacAuxiliaryStorage._setDataValue:forNVRAMVariableNamed:` writes to a different NVRAM namespace than what iBoot reads for kernel-boot-args substitution.

Evidence:
- Guest `kern.bootargs` shows `serial=3 -v debug=0x2014e ` (trailing space + empty after).
- iBoot's baked boot-args format is `serial=3 -v debug=0x2014e %s` (in patched iBEC).
- `%s` substitution yields empty even though host-side Swift sets a non-empty value on the aux-storage NVRAM and logs "NVRAM boot-args: ..." success.
- Guest runtime `nvram boot-args=...` sets the value but it does not survive a host-side reboot because Swift recreates aux storage with `.allowOverwrite` each launch, and iBoot reads from a source that the aux-storage writes do not populate.

Fix: bake the required boot-args directly into `IBootPatcher.bootArgs` so they live in the patched iBEC binary on disk. This edit is done. Applying it requires rebuilding iBEC via `make fw_patch_dev`, full restore via ramdisk, then `cfw_install_dev`. Documented here so next session does not re-investigate the Swift NVRAM path.

Current `IBootPatcher.bootArgs`:
```
serial=3 -v debug=0x2014e amfi_get_out_of_my_way=1 cs_enforcement_disable=1 %s
```

Swift `boot-args` in `VPhoneVirtualMachine.swift` is reverted to the original `serial=3 debug=0x104c04` since Swift's NVRAM layer does not feed iBoot anyway.

Dependency chain summary of today's work:
1. LLB `system-volume-auth-blob` gate → patched at 0x1ce8 (done, doc'd).
2. UIKitCore idiom assertion → byte-patched at dyld_shared_cache_arm64e.03+0x1a5978 (done, doc'd).
3. Patch (2) violates shared-cache code-directory hash → AMFI SIGKILLs every UIKit consumer (new finding).
4. Fix for (3): bake `amfi_get_out_of_my_way=1 cs_enforcement_disable=1` into iBoot's kernel boot-args (edit made, requires full restore cycle to apply).
5. fairplayd/chronod/ndoagent/webbookmarksd disabled via `/var/db/com.apple.xpc.launchd/disabled.plist` at runtime + the LaunchDaemon plist rename at CFW install time (both done, one documented and wired).

### 2026-04-22 Progress snapshot + strategy pivot: TXM/kernel codesign bypass in dev variant

Today's net progress:
- Before today: LLB went to recovery; boot never reached XNU.
- End of today: LLB passes, XNU boots, APFS Cryptex loads, launchd starts, first-boot shell runs, root shell over SSH on port 2222 works, backboardd runs, datamigrator tries to run.
- First remaining blocker: SpringBoard and many other UIKit consumers are SIGKILLed by AMFI with `CODESIGNING: Invalid Page` because the UIKitCore byte-patch at `dyld_shared_cache_arm64e.03 + 0x1a5978` invalidates the signed page hash.

`amfi_get_out_of_my_way=1 cs_enforcement_disable=1` via iBoot-baked boot-args is one possible fix, but these boot-args are blunt and will still leave AMFI partially enforcing on iOS 18.5 (Apple has hardened the kernel flags here over time). A cleaner and more surgical path is to use the kernel-side codesign bypass patches that already exist in this repo. The JB variant already ships the exact patch we need.

Existing kernel patches that matter for this problem:

| Patch | Layer | Applies to | Effect |
|---|---|---|---|
| `KernelPatchPostValidation` patch 8 | base | regular+dev+jb | NOP TBNZ after `TXM [Error]: CodeSignature` log — keeps process alive past TXM CodeSignature error. |
| `KernelPatchPostValidation` patch 9 | base | regular+dev+jb | Rewrites `cmp w0,#imm` → `cmp w0,w0` after `AMFI: code signature validation failed` string — forces AMFI postValidation path to look successful. |
| `KernelJBPatchAmfiTrustcache.patchAmfiCdhashInTrustcache` | JB | jb only | Rewrites `AMFIIsCDHashInTrustCache` to always return 1. |
| `KernelJBPatchAmfiExecve.patchKillPathExecve` (or similar) | JB | jb only | NOPs the AMFI-kills-on-execve path. |

The combination that should actually fix our shared-cache hash-mismatch SIGKILL:
- Base patches 8 + 9 are already applied in regular/dev, but they handle different code paths (TXM post-validation + generic AMFI CS validation failure). They do NOT override `AMFIIsCDHashInTrustCache`, which is what the kernel calls when memory-mapping a shared-cache page into a process. That function is the one returning "not trusted" for our patched page and driving the "Invalid Page" SIGKILL.
- `patchAmfiCdhashInTrustcache` is the precise override. It lives only in the JB patcher right now.

**Planned change for next session**: port `patchAmfiCdhashInTrustcache` (and optionally `patchAmfiExecve`) into the dev variant without pulling in the full JB patch set. These are the two Group-A JB patches that address AMFI runtime gates; the remaining JB patches handle user-r00t/tfp0-style escalation which we do not need.

Candidate wiring:

1. Extract the two methods' bodies from `sources/FirmwarePatcher/Kernel/JBPatches/KernelJBPatchAmfiTrustcache.swift` and `KernelJBPatchAmfiExecve.swift` into a shared module (or keep them in JB and have the dev variant construct a JB patcher with only those methods active).
2. Simpler, higher-parity alternative: in `sources/FirmwarePatcher/Pipeline/FirmwarePipeline.swift` around the `case .regular, .dev:` kernel branch, add a `KernelJBPatcher` that runs with a `devOnly` flag restricting it to `patchAmfiCdhashInTrustcache` + `patchAmfiExecve`. Do not expand to the Group B / Group C JB patches. Wire the buffer-merge logic similarly to how JB variant already layers base then JB patches sequentially.
3. Revert `IBootPatcher.bootArgs` back to `serial=3 -v debug=0x2014e %s`. The AMFI flags are no longer needed once `AMFIIsCDHashInTrustCache` always returns 1.
4. Keep the UIKitCore idiom byte-patch at its current offset. The kernel patches make the hash mismatch harmless.
5. Keep all other fixes (LLB, fairplayd disable, launchd plist rename, MobileGestalt cache override even if redundant).

Stability caveat: the two AMFI patches are the minimum surface. If later we find additional `CODESIGNING: Invalid Page` SIGKILLs survive these two patches, we can port more JB kernel patches incrementally.

State at end of session:
- Swift `VPhoneVirtualMachine.swift` `bootArgs` reverted to `serial=3 debug=0x104c04` — Swift NVRAM does not feed iBoot, so the kernel flags there are ineffective.
- `IBootPatcher.swift` `bootArgs` currently has the AMFI flags baked in. **Decision for next session**: revert this to the original `serial=3 -v debug=0x2014e %s` if we port the JB AMFI kernel patches; keep the AMFI flags if we want belt-and-suspenders.
- Disk state on VM: UIKitCore byte-patched, fairplayd plists renamed, `/var/db/com.apple.xpc.launchd/disabled.plist` has fairplayd/chronod/ndoagent/webbookmarksd disabled. VM boots to 100% progress bar, SpringBoard in crash loop.
