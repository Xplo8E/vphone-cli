# iOS 18.5 Support Preparation - 22F76

Last updated: 2026-04-21

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
| confirmed | cloudOS 18.5 `22F76` has no `vphone600ap` build identity. | `BuildManifest.plist` contains `j236cap`, `j475dap`, and `vresearch101ap`; no `vphone600ap`. Running current `scripts/fw_manifest.py` against 18.5 manifests throws `KeyError: 'No release identity for DeviceClass=vphone600ap'`. | Current `fw_prepare` hybrid manifest generation cannot work unchanged on these 18.5 files. |
| confirmed | Existing pipeline hardcodes vphone600 runtime paths. | `sources/FirmwarePatcher/Pipeline/FirmwarePipeline.swift` searches `kernelcache.research.vphone600` and `Firmware/all_flash/DeviceTree.vphone600ap.im4p`. `scripts/ramdisk_build.py` has the same vphone600 assumptions. | We need variant-aware paths or an explicit firmware profile before real 18.5 patching. |
| confirmed | 18.5 cloud TXM is Mach-O arm64e, not the flat-offset model assumed by parts of `TXMDevPatcher`. | `file` reports Mach-O arm64e. `otool -hv` reports `MH_MAGIC_64 ARM64 subtype E caps KER00 EXECUTE PIE`. IDA sees strings/xrefs, but the Swift dev patcher reports string refs missing. | Base TXM patch works, but dev-only TXM patches need Mach-O VA/file-offset aware string reference resolution. |
| confirmed | 18.5 `DeviceTree.vresearch101ap` does not match the current vphone600 DeviceTree patch contract. | Decoded DeviceTree has no `buttons` node, no `home-button-type`, no `island-notch-location`, and no `MKB`/`mkb`/`keybag` literals. It does have `chosen/amfi-allows-trust-cache-load=0`, `chosen/debug-enabled=0`, and `product/has-virtualization=1`. | Current `DeviceTreePatcher` applies `serial-number`, then fails on missing `buttons`. Needs variant-aware behavior before pipeline success. |
| candidate | Kernel base patching mostly retargets to `kernelcache.research.vresearch101`. | Dry-run found 24 records. Misses were post-validation NOP `[8]` and `handle_get_dev_by_role` entitlement bypass `[16]`. | Enough survives to keep going, but the two misses need IDA/XNU validation before we trust boot behavior. |
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

Goal: stop encoding firmware identity assumptions directly in the patch pipeline.

Tasks:

1. Add a firmware profile model for boot board/runtime board/kernel/device tree paths.
2. Add an iOS 18.5 profile that uses `vresearch101ap` for both boot and runtime components.
3. Update `scripts/fw_manifest.py` to detect absent `vphone600ap` and either:
   - use explicit `--runtime-device-class vresearch101ap`, or
   - auto-fallback with a loud log line.
4. Update `FirmwarePipeline` to consume profile paths instead of hardcoded vphone600 runtime paths.
5. Update `scripts/ramdisk_build.py` to use the same profile path source.

Verifier:

- Run manifest generation against 18.5 extracted manifests without `KeyError`.
- Confirm generated BuildManifest uses `vresearch101ap` runtime entries for DeviceTree/SEP/kernel/SPTM.
- Confirm no shim renaming is required for `patch-firmware --variant dev` to find files.

### Phase 2 - TXM Mach-O Retargeting

Goal: preserve current dev patch intent but make locators work on Mach-O TXM.

Tasks:

1. Add Mach-O segment parsing or reuse an existing parser for TXM.
2. Convert between file offset and VM address for ADRP/ADD resolution.
3. Replace `findRefsToOffset` with an address-aware resolver:
   - string file offset -> string VM address
   - instruction file offset -> instruction VM address
   - ADRP page math in VM address space
   - ADD page offset check
4. Retarget each dev patch independently:
   - `get-task-allow` entitlement force true
   - debugger entitlement force true
   - selector42/29 shellcode path
   - developer-mode guard bypass
5. Keep the existing flat fallback for older TXM images if needed.

Verifier:

- `patch-firmware --variant dev` emits expected TXM dev records on 18.5 TXM.
- IDA xrefs for `get-task-allow`, `com.apple.private.cs.debugger`, and developer-mode strings line up with emitted file offsets.
- Do not patch a branch just because a string exists. Each patch needs a nearby control-flow pattern that matches the intended consumer.

### Phase 3 - DeviceTree Profile Retargeting

Goal: make DeviceTree patching explicit per runtime profile instead of failing on legacy vphone600-only nodes.

Tasks:

1. Split DeviceTree patches into profile-specific sets.
2. For `vresearch101ap`, classify properties into:
   - required boot policy knobs
   - trustcache/developer-mode knobs
   - cosmetic host-device shaping
   - legacy vphone600-only fields
3. Decide whether to patch `chosen/amfi-allows-trust-cache-load` and `chosen/debug-enabled`, but only after TXM/kernel behavior is understood.
4. Make missing legacy cosmetic nodes a skipped patch, not a pipeline failure, when running the `ios18-22F76` profile.

Verifier:

- Patcher can rebuild `DeviceTree.vresearch101ap.im4p` without crashing.
- Rebuilt tree still parses cleanly.
- Every changed property is logged with before/after bytes.

### Phase 4 - Kernel Miss Retargeting

Goal: investigate the two missed kernel patches and decide whether they moved, changed shape, or are no longer needed.

Tasks:

1. Open `kernelcache.research.vresearch101` in IDA.
2. For post-validation NOP `[8]`:
   - locate `TXM [Error]: CodeSignature`
   - inspect all xrefs
   - identify the validation branch that replaced the old nearby `tbnz`, if any
3. For `handle_get_dev_by_role` `[16]`:
   - locate `com.apple.apfs.get-dev-by-role`
   - inspect the full handler
   - compare against XNU APFS role/dev handling if matching source is available
4. Update patchers only after a semantic target is clear.

Verifier:

- New locator is source-backed or IDA-backed, not hardcoded offset-backed.
- Dry-run emits the missing records on 18.5 or documents why the patch is obsolete.
- `research/0_binary_patch_comparison.md` is updated if patch logic changes.

### Phase 5 - First Real Dev Variant Build

Goal: produce an 18.5 dev variant package without shim paths.

Tasks:

1. Run setup/prepare flow against the 18.5 IPSWs.
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

## Documentation Rules For This Branch

Use these docs instead of a repo TODO file:

| Document | Purpose |
| --- | --- |
| `research/ios-18-preparations.md` | Current state, blockers, implementation plan, verifier gates |
| `research/ios-18-firmware-deep-dive.md` | Narrative technical log: what was inspected, what failed, what IDA showed |
| `research/0_binary_patch_comparison.md` | Must be updated when patch logic changes or new patch behavior is introduced |

Do not let important context live only in terminal scrollback. Every meaningful dry-run, IDA finding, patch miss, and boot result should land in one of the research docs before moving to the next slice.

## Next Immediate Work

1. Implement firmware profile/path selection for `ios18-22F76` without touching patch semantics.
2. Retarget `TXMDevPatcher` string xref resolution for Mach-O TXM and re-run dev TXM patching.
3. Make `DeviceTreePatcher` profile-aware so `vresearch101ap` missing legacy nodes do not kill the pipeline.
4. Open `kernelcache.research.vresearch101` in IDA and retarget or retire kernel misses `[8]` and `[16]` with evidence.
