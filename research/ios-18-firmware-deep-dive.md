# iOS 18.5 Firmware Deep Dive - 22F76

Last updated: 2026-04-21

This is the narrative research log for iOS 18.5 support. The short version lives in [ios-18-preparations.md](ios-18-preparations.md). This file keeps the messy details: what was inspected, what failed, what IDA showed, and why the next implementation steps are shaped the way they are.

## Starting Point

The first instinct was to treat iOS 18.5 as a pattern-retargeting job. The existing project already knows how to build a hybrid restore using cloudOS boot firmware plus iPhone OS payloads. The previous flow used `vresearch101ap` for DFU compatibility and `vphone600ap` for runtime pieces because the vphone600 DeviceTree/kernel combination had the boot properties we wanted.

Then the 18.5 manifests killed that assumption. There is no `vphone600ap` in the cloudOS 18.5 IPSW we have. Not hidden, not an empty DeviceMap entry, just absent from the usable BuildManifest identities.

So this is not just a patch-offset migration. It is a profile migration.

## Firmware Inputs

Local firmware files:

```text
/Users/vinay/ipsw/iPhone17,3_18.5_22F76_Restore.ipsw
/Users/vinay/ipsw/cloudOS_18.5_22F76.ipsw
```

Temporary extraction/analysis paths used during this pass:

```text
/tmp/vphone-ios18-22F76
/tmp/vphone-ios18-22F76/raw
/tmp/vphone-ios18-vm-test
```

The `/tmp/vphone-ios18-vm-test` directory was a shim only. It renamed `vresearch101` runtime files to the old vphone600 filenames so the current hardcoded pipeline could be exercised. That tells us where patch locators work or fail, but it is not a valid final firmware layout.

## Manifest Reality Check

The iPhone IPSW is straightforward:

```text
ProductVersion: 18.5
ProductBuildVersion: 22F76
DeviceClass: d47ap
BuildIdentities: 5
```

The interesting iPhone identities are the research erase/upgrade identities. They carry:

```text
Firmware/dfu/iBSS.d47.RESEARCH_RELEASE.im4p
Firmware/dfu/iBEC.d47.RESEARCH_RELEASE.im4p
Firmware/all_flash/LLB.d47.RESEARCH_RELEASE.im4p
Firmware/all_flash/iBoot.d47.RESEARCH_RELEASE.im4p
Firmware/txm.iphoneos.research.im4p
kernelcache.research.iphone17
```

The cloudOS IPSW is where things changed:

```text
ProductVersion: 18.5
ProductBuildVersion: 22F76
BuildIdentities: 4
DeviceClasses: j236cap, j475dap, vresearch101ap
Restore DeviceMap: j236cap, j475dap, vresearch101ap
```

For `vresearch101ap`, cloudOS gives us both release and research identities:

```text
Firmware/dfu/iBSS.vresearch101.RELEASE.im4p
Firmware/dfu/iBSS.vresearch101.RESEARCH_RELEASE.im4p
Firmware/dfu/iBEC.vresearch101.RELEASE.im4p
Firmware/dfu/iBEC.vresearch101.RESEARCH_RELEASE.im4p
Firmware/all_flash/LLB.vresearch101.RELEASE.im4p
Firmware/all_flash/LLB.vresearch101.RESEARCH_RELEASE.im4p
Firmware/all_flash/iBoot.vresearch101.RELEASE.im4p
Firmware/all_flash/iBoot.vresearch101.RESEARCH_RELEASE.im4p
Firmware/all_flash/DeviceTree.vresearch101ap.im4p
Firmware/all_flash/sep-firmware.vresearch101.RELEASE.im4p
Firmware/sptm.vresearch1.release.im4p
Firmware/txm.iphoneos.release.im4p
Firmware/txm.iphoneos.research.im4p
kernelcache.release.vresearch101
kernelcache.research.vresearch101
```

What it does not give us:

```text
kernelcache.research.vphone600
kernelcache.release.vphone600
Firmware/all_flash/DeviceTree.vphone600ap.im4p
Firmware/all_flash/sep-firmware.vphone600.RELEASE.im4p
```

That is why the current manifest script fails:

```python
PROD, RES = find_cloudos(C, "vresearch101ap")
VP, VPR = find_cloudos(C, "vphone600ap")
```

`VP, VPR` cannot resolve on 18.5. The failure mode is clean:

```text
KeyError: 'No release identity for DeviceClass=vphone600ap'
```

Takeaway: the 18.5 path needs a runtime profile. For the firmware we currently have, that runtime profile is `vresearch101ap`, not `vphone600ap`.

## DeviceTree: What Changed

The decoded 18.5 cloud DeviceTree payload is:

```text
/tmp/vphone-ios18-22F76/raw/DeviceTree.vresearch101ap.raw
size: 57672 bytes
```

High-signal root properties:

```text
/device-tree/serial-number = "syscfg/SrNm/0x20,zeroes/0x20"
/device-tree/target-type = "VRESEARCH101"
/device-tree/target-sub-type = "VRESEARCH101AP"
/device-tree/compatible = "VRESEARCH101AP", "ComputeModule14,2", "AppleVirtualPlatformARM"
/device-tree/secure-root-prefix = "md"
/device-tree/device-tree-tag = "EmbeddedDeviceTrees-9747.122.4"
```

High-signal `chosen` properties:

```text
/device-tree/chosen/txm-secure-channel = 1
/device-tree/chosen/protected-data-access = 1
/device-tree/chosen/amfi-allows-trust-cache-load = 0
/device-tree/chosen/debug-enabled = 0
/device-tree/chosen/effective-security-mode-ap = 0
/device-tree/chosen/effective-production-status-ap = 0
/device-tree/chosen/effective-security-mode-sep = 0
/device-tree/chosen/effective-production-status-sep = 0
/device-tree/chosen/sepfw-load-at-boot = 1
```

High-signal `product` properties:

```text
/device-tree/product/has-virtualization = 1
/device-tree/product/product-description = "virtual machine for PCC Research Environment"
/device-tree/product/artwork-device-subtype = 0
/device-tree/product/has-exclaves = 0
/device-tree/product/partition-style = "iOS"
/device-tree/product/product-name = "Apple PCC Research Environment Virtual Machine 1"
```

Important absences:

```text
MKB: not found
mkb: not found
keybag: not found
home-button-type: not found
island-notch-location: not found
/buttons node: not found
```

Current `DeviceTreePatcher` expects old vphone600-style nodes/properties:

```text
/device-tree/serial-number
/device-tree/buttons/home-button-type
/device-tree/product/artwork-device-subtype
/device-tree/product/island-notch-location
```

On `DeviceTree.vresearch101ap`, it patches serial-number and then dies on `/device-tree/buttons`.

This is one of those places where adding a missing node blindly is the wrong move. The old home button/notch patches may be UI-shaping leftovers, while the real boot/security behavior may be in `chosen/*` and the filesystem/secure-root fields. We need profile-specific DeviceTree logic.

## TXM: IDA Notes

Input:

```text
/tmp/vphone-ios18-22F76/raw/txm.cloud.research.raw
```

Triage:

```text
Mach-O 64-bit executable arm64e
MH_MAGIC_64 ARM64 subtype E caps KER00 EXECUTE PIE
IDA function count: 1276
SHA-256: 67a64d43d516e417f9d485be9f9e6f25b060981d646b61a36cb7babfffed225f
```

Segments that matter for the current bug:

```text
__TEXT           vmaddr 0xfffffff017004000 fileoff 0      filesize 49152
__DATA_CONST     vmaddr 0xfffffff017010000 fileoff 49152  filesize 49152
__TEXT_EXEC      vmaddr 0xfffffff01701c000 fileoff 98304  filesize 262144
__TEXT_BOOT_EXEC vmaddr 0xfffffff01705c000 fileoff 360448 filesize 32768
__DATA           vmaddr 0xfffffff017064000 fileoff 393216 filesize 16384
```

That matters because current `TXMDevPatcher` does ADRP math in file-offset space. On this TXM, ADRP resolves VM addresses. IDA sees the xrefs; the Swift flat scanner does not.

### `get-task-allow`

IDA strings/xrefs:

```text
get-task-allow @ 0xfffffff0170065d3
  xrefs: 0xfffffff017010f08, 0xfffffff01701f5a8, 0xfffffff017031f98

com.apple.security.get-task-allow @ 0xfffffff017008161
  xrefs: 0xfffffff017031fb0
```

Relevant functions:

```text
sub_FFFFFFF01701F538 start 0xfffffff01701f538 size 224
sub_FFFFFFF017031F14 start 0xfffffff017031f14 size 300
```

`sub_FFFFFFF01701F538` is especially interesting. IDA decompilation shows it refuses the path unless `byte_FFFFFFF017064CD3 == 1`, then checks `get-task-allow`, and sets `*(a1 + 32) = 1` when the entitlement path passes.

That means the old dev-mode/get-task-allow relationship still exists in 18.5. The locator is what broke.

### Debugger Entitlement

IDA strings/xrefs:

```text
com.apple.private.cs.debugger @ 0xfffffff0170063fb
  xrefs: 0xfffffff017010f10
         0xfffffff017010f40
         0xfffffff01701ca24
         0xfffffff01701f37c
         0xfffffff01701f3f4
```

Relevant function:

```text
sub_FFFFFFF01701F328 start 0xfffffff01701f328 size 528
```

IDA decompilation shows the important behavior:

```c
v9 = sub_FFFFFFF01701E9E4(0, "com.apple.private.cs.debugger", 0);
if ((v9 & 1) == 0) {
    sub_FFFFFFF0170219FC("disallowed non-debugger initiated debug mapping");
    return 37;
}
```

So the debugger gate is still present and still patchable in concept. Again, the current Swift dev locator misses it because the string-reference model is wrong for Mach-O.

### Developer Mode State

IDA string/xref:

```text
"developer mode enabled due to system policy configuration" @ 0xfffffff0170066c8
  xref: 0xfffffff01701f9f8
```

Relevant function:

```text
sub_FFFFFFF01701F98C start 0xfffffff01701f98c size 268
```

IDA shows this function computes `v1` and eventually writes:

```c
byte_FFFFFFF017064CD3 = v1;
```

That same global is consumed by `sub_FFFFFFF01701F538` before get-task-allow is accepted. This is a strong sign the dev-mode bypass target still exists, but the old patch pattern needs to be re-derived against this exact function.

### Trust Cache Loading

IDA strings/xrefs:

```text
personalized.trust-cache @ 0xfffffff017006c5b
  xrefs: 0xfffffff0170101c0, 0xfffffff017010860

missing trust cache range from device tree @ 0xfffffff017006b9a
  xref: 0xfffffff017021f28
```

Relevant function:

```text
sub_FFFFFFF017021C18 start 0xfffffff017021c18 size 928
```

IDA decompilation shows this path calls a helper that reads a trust cache range from the DeviceTree, then logs:

```text
missing trust cache range from device tree
trust cache range is 0 length
failed to load external trust cache module: %u
loaded external trust cache modules: %u/%u
```

This connects TXM behavior back to the DeviceTree profile problem. The 18.5 `vresearch101ap` DeviceTree needs to be understood as a policy input, not just a cosmetic tree.

## TXM Patcher Dry-Run

Base TXM patching works:

```text
0x027E54: bl 0x26950 -> mov x0, #0
[trustcache bypass: legacy binary-search call -> mov x0, #0]
```

Dev TXM patching partially works in the shim run:

```text
base trustcache: found
selector24 force pass: found
get-task-allow refs: missing
debugger-gate function: missing
debugger refs: missing
developer-mode string ref: missing
```

The misses are false negatives from the locator, not proof the code paths disappeared. IDA proved the strings and functions are still there.

Fix direction: teach TXM dev patching to resolve ADRP/ADD in Mach-O VM address space, then re-validate each patch target from control flow.

## Kernel Patcher Dry-Run

Input:

```text
/tmp/vphone-ios18-22F76/cloud/kernelcache.research.vresearch101
```

Dry-run result: 24 patch records emitted.

What found cleanly:

```text
_apfs_vfsop_mount sealed volume check
_authapfs_seal_is_broken
_bsd_init rootvp auth gate
_proc_check_launch_constraints
_PE_i_can_has_debugger
postValidation CMP
_check_dyld_policy_internal
_apfs_graft
_apfs_vfsop_mount rw check
_apfs_mount_upgrade_checks
_handle_fsioc_graft
Sandbox MACF hook stubs
```

What missed:

```text
[8] post-validation NOP (txm-related)
    reason: TBNZ not found after TXM error string ref

[16] handle_get_dev_by_role: bypass entitlement gate
    reason: entitlement gate pattern not found
```

The kernel result is encouraging but not done. The old semantic anchors still cover most of the kernel, but two important validation/access-control patch sites changed enough to break the pattern.

Next move is IDA on `kernelcache.research.vresearch101`, not guessing. For `[8]`, start from `TXM [Error]: CodeSignature`. For `[16]`, start from `com.apple.apfs.get-dev-by-role` and walk the handler.

## Full Dev Pipeline Shim Run

The shim run was useful because it showed the whole pipeline failure order:

```text
AVPBooter: patched
 iBSS: patched
 iBEC: patched
 LLB: partially patched, old rootfs patterns missed
 TXM: partially patched, dev-only string ref locators missed
 Kernel: partially patched, misses [8] and [16]
 DeviceTree: failed on missing child node 'buttons'
```

This tells us the next engineering order:

1. Stop needing shim filenames by adding a firmware profile.
2. Fix TXM Mach-O xrefs.
3. Make DeviceTree patch sets profile-aware.
4. Retarget kernel misses with IDA.
5. Only then run the real dev firmware path.

## Phase 1 Implementation Log - Firmware Profiles

The first implementation slice is done: the project now has an explicit firmware profile layer instead of assuming every runtime component is named like vphone600.

The important design choice is that `legacy` remains the old hybrid:

```text
boot DeviceClass:    vresearch101ap
runtime DeviceClass: vphone600ap
kernel:              kernelcache.research.vphone600
DeviceTree:          Firmware/all_flash/DeviceTree.vphone600ap.im4p
```

The new `ios18-22F76` profile is intentionally narrower:

```text
boot DeviceClass:    vresearch101ap
runtime DeviceClass: vresearch101ap
kernel:              kernelcache.research.vresearch101
DeviceTree:          Firmware/all_flash/DeviceTree.vresearch101ap.im4p
RecoveryMode:        optional / absent
```

This is not saying `vresearch101ap` is semantically equivalent to vphone600. It only says the 18.5 firmware set we have does not contain vphone600, so all path and manifest plumbing must be able to target `vresearch101ap` before any deeper patch work can be tested honestly.

Files changed in this phase:

```text
sources/FirmwarePatcher/Pipeline/FirmwareProfile.swift
sources/FirmwarePatcher/Pipeline/FirmwarePipeline.swift
sources/FirmwarePatcher/Manifest/FirmwareManifest.swift
sources/vphone-cli/VPhoneCLI.swift
scripts/fw_manifest.py
scripts/fw_prepare.sh
scripts/ramdisk_build.py
scripts/pymobiledevice3_bridge.py
Makefile
tests/FirmwarePatcherTests/FirmwarePatcherTests.swift
Package.swift
sources/FirmwarePatcher/Binary/MachOHelpers.swift
```

`Package.swift` and `MachOHelpers.swift` changed because `MachOHelpers.swift` imported MachOKit but only used its own manual Mach-O parser. Swift 6.2 hit a MachOKit compile/importer crash during verification, so the unused dependency was removed from the package graph instead of patching vendor code.

The profile value now flows through the command surface:

```bash
make fw_prepare FIRMWARE_PROFILE=ios18-22F76
make fw_patch_dev FIRMWARE_PROFILE=ios18-22F76
make ramdisk_build FIRMWARE_PROFILE=ios18-22F76
make ramdisk_send FIRMWARE_PROFILE=ios18-22F76
```

The Swift CLI equivalent is:

```bash
.build/debug/vphone-cli patch-firmware \
  --vm-directory ./vm \
  --variant dev \
  --firmware-profile ios18-22F76
```

The manifest verifier was run against plist files extracted from:

```text
/Users/vinay/ipsw/iPhone17,3_18.5_22F76_Restore.ipsw
/Users/vinay/ipsw/cloudOS_18.5_22F76.ipsw
```

Verifier output:

```text
firmware profile: ios18-22F76
cloudOS vresearch101ap: release=#2, research=#3 [boot]
cloudOS vresearch101ap: release=#2, research=#3 [runtime]
iPhone  erase: #0
skipping RecoveryMode: not present for vresearch101ap
wrote BuildManifest.plist
wrote Restore.plist
assertions: ok
DeviceMap: ['d47ap', 'vresearch101ap']
```

The generated 18.5 manifest now selects:

```text
DeviceTree:        Firmware/all_flash/DeviceTree.vresearch101ap.im4p
RestoreDeviceTree: Firmware/all_flash/DeviceTree.vresearch101ap.im4p
KernelCache:       kernelcache.research.vresearch101
RestoreKernelCache: kernelcache.release.vresearch101
RecoveryMode:      absent
```

Other verification completed:

```text
python3 -m py_compile scripts/fw_manifest.py scripts/ramdisk_build.py scripts/pymobiledevice3_bridge.py
swift test --filter FirmwarePipelineTests/firmwareProfileControlsRuntimePaths
git diff --check
make -n fw_prepare FIRMWARE_PROFILE=ios18-22F76
make -n fw_patch FIRMWARE_PROFILE=ios18-22F76 VM=iphone_18_5
```

The targeted Swift test passed. A full Swift test run is not a useful signal right now because the local `ipsws/patch_refactor_input` test fixture directory is empty.

Phase 2 closes the TXM xref problem. The next blocker is the `vresearch101ap` DeviceTree profile.

## Phase 2 Implementation Log - TXM Mach-O Retargeting

The TXM fix had two parts.

First, `TXMDevPatcher` now resolves string references in the address model the payload actually uses:

```text
string file offset -> Mach-O VM address
instruction file offset -> Mach-O VM address
ADR target or ADRP page math -> VM address
resolved patch site -> file offset
```

The old scanner only understood ADRP+ADD in flat file-offset space. The 18.5 TXM image is a Mach-O, and the high-signal cstring references are mostly direct `ADR` instructions because `__TEXT_EXEC` and `__TEXT.__cstring` are close enough:

```asm
0xfffffff01701f5a8  adr x1, 0xfffffff0170065d3 ; "get-task-allow"
0xfffffff01701f3f4  adr x1, 0xfffffff0170063fb ; "com.apple.private.cs.debugger"
0xfffffff01701f9f8  adr x0, 0xfffffff0170066c8 ; developer-mode log
```

So the final resolver supports both:

```text
ADR direct refs
ADRP + ADD refs with VM-address page math
flat-binary fallback when no Mach-O segments exist
```

Second, the developer-mode patch shape changed. The old branch was adjacent to the force-enable assignment and could be NOPed. On 18.5, the function already has a force-enable block:

```asm
0xfffffff01701f9c0  ldrb w9, [x9, #0x3d]
0xfffffff01701f9c4  cbz  w9, 0xfffffff01701f9f4
...
0xfffffff01701f9f4  mov  w19, #1
0xfffffff01701f9f8  adr  x0, "developer mode enabled due to system policy configuration"
```

NOPing `cbz` would be wrong because it would fall through into the normal policy path. The new patch replaces the conditional branch with an unconditional branch to the force-enable block:

```text
0x01B9C4: cbz w9, 0x1b9f4 -> b 0x1b9f4
```

Direct raw payload verifier:

```bash
.build/debug/vphone-cli patch-component \
  --component txm-dev \
  --input /tmp/vphone-ios18-22F76/raw/txm.cloud.research.raw \
  --output /tmp/vphone-ios18-22F76/raw/txm.cloud.research.dev-patched.raw
```

IM4P verifier:

```bash
.build/debug/vphone-cli patch-component \
  --component txm-dev \
  --input /tmp/vphone-ios18-22F76/cloud/Firmware/txm.iphoneos.research.im4p \
  --output /tmp/vphone-ios18-22F76/raw/txm.cloud.research.dev-patched-from-im4p.raw
```

Both emitted the same 12 records:

```text
0x027E54  trustcache bypass
0x02CCE0  selector24 pass: mov w0, #0xa1
0x02CCE4  selector24 pass: branch epilogue
0x01B5B8  get-task-allow BL -> mov x0, #1
0x022EC8  selector42|29 branch to shellcode
0x0570A8  shellcode nop pad
0x0570AC  shellcode mov x0, #1
0x0570B0  shellcode strb w0, [x20, #0x30]
0x0570B4  shellcode mov x0, x20
0x0570B8  shellcode branch back
0x01B404  debugger entitlement BL -> mov w0, #1
0x01B9C4  developer-mode guard -> force-enable branch
```

A profile-aware full pipeline run was also tested without vphone600 shim names:

```bash
.build/debug/vphone-cli patch-firmware \
  --vm-directory /tmp/vphone-ios18-vm-profile-fresh \
  --variant dev \
  --firmware-profile ios18-22F76
```

Result:

```text
AVPBooter: patched
iBSS: patched
iBEC: patched
LLB: patched with known rootfs misses
TXM: 12 patches applied
kernelcache: 24 patches applied, known misses [8] and [16]
DeviceTree: failed on missing child node 'buttons'
```

That is the expected phase boundary. TXM is no longer blocking the real 18.5 path; DeviceTree is.

## Phase 3 Implementation Log - DeviceTree Profiles

The DeviceTree blocker is now removed from the patch pipeline.

The important call was to avoid inventing legacy nodes in the 18.5 tree. `DeviceTree.vresearch101ap` simply does not have:

```text
/device-tree/buttons
/device-tree/buttons/home-button-type
/device-tree/product/island-notch-location
```

Those look like legacy/cosmetic shaping fields from the old vphone600 profile. Adding them blindly would make the file look more like the old tree, but it would not prove the properties are consumed by the 18.5 boot stack.

The `ios18-22F76` DeviceTree patch set now only changes properties that exist in the 18.5 tree:

```text
/device-tree/serial-number = "vphone-1337"
/device-tree/product/artwork-device-subtype = 2556
```

It intentionally does not change the policy-looking `chosen` fields yet:

```text
/device-tree/chosen/amfi-allows-trust-cache-load = 0
/device-tree/chosen/debug-enabled = 0
```

Those may matter later, but they need boot/runtime evidence. For Phase 3, the objective was not "make the tree permissive"; it was "make profile-aware patching precise enough to complete without fake legacy nodes."

Direct verifier:

```bash
.build/debug/vphone-cli patch-component \
  --component device-tree \
  --firmware-profile ios18-22F76 \
  --input /tmp/vphone-ios18-22F76/cloud/Firmware/all_flash/DeviceTree.vresearch101ap.im4p \
  --output /tmp/vphone-ios18-22F76/raw/DeviceTree.vresearch101ap.ios18-patched.raw
```

Output:

```text
0x000128: serial-number -> vphone-1337
0x00A964: artwork-device-subtype -> 2556
[2 DeviceTree patch(es) applied]
```

Full profile-aware dev pipeline verifier:

```bash
.build/debug/vphone-cli patch-firmware \
  --vm-directory /tmp/vphone-ios18-vm-profile \
  --variant dev \
  --firmware-profile ios18-22F76
```

Result:

```text
All 9 components patched successfully
59 total patches
```

The kernel still reports known misses:

```text
[8] post-validation NOP: TBNZ not found after TXM error string ref
[16] handle_get_dev_by_role: entitlement gate pattern not found
```

Those are now the next slice, not a blocker to the patch pipeline itself.

## Phase 4 Implementation Log - Kernel Miss Retargeting

The kernel slice started with the two misses from the 18.5 `kernelcache.research.vresearch101` dry-run:

```text
[8] post-validation NOP
    old locator expected a nearby TBNZ after "TXM [Error]: CodeSignature"

[16] handle_get_dev_by_role entitlement gate
    old locator expected the legacy APFS entitlement-deny block shape
```

IDA MCP was attempted first, per the normal kernel workflow:

```text
open_idb /tmp/vphone-ios18-22F76/raw/kernelcache.research.vresearch101.raw
analysis_status
```

Both calls timed out on this kernel in the current environment. I did not treat that as IDA evidence. The retargeting below is based on deterministic extraction, Mach-O address mapping, and Capstone instruction decode.

The raw kernel used for analysis was decompressed from the cloudOS IM4P:

```bash
source .venv/bin/activate
python3 - <<'PY'
from pyimg4 import IM4P
from pathlib import Path

im = IM4P(Path('/tmp/vphone-ios18-22F76/cloud/kernelcache.research.vresearch101').read_bytes())
im.payload.decompress()
Path('/tmp/vphone-ios18-22F76/raw/kernelcache.research.vresearch101.raw').write_bytes(im.payload.data)
PY
```

Triage:

```text
/tmp/vphone-ios18-22F76/raw/kernelcache.research.vresearch101.raw
Mach-O 64-bit kernel arm64e
size: ~36 MB
```

### Patch `[8]`: Post-Validation NOP

The anchor string still exists:

```text
"TXM [Error]: CodeSignature" @ file offset 0x7F329
string ref sequence @ 0x0EACA98 / 0x0EACA9C
```

The old locator only accepted `tbnz` after that string reference. iOS 18.5 changed the branch shape:

```asm
0x0EACA98  adrp x0, #0x7f000
0x0EACA9C  add  x0, x0, #0x329
0x0EACAA0  bl   <log>
0x0EACAA4  mov  w0, #5
0x0EACAA8  ldrb w8, [x19, #6]
0x0EACAAC  cmp  w8, #1
0x0EACAB0  b.eq 0x0EACB98
```

The target block at `0x0EACB98` is the extra assertion/error path. The patch intent is still the same: after the TXM CodeSignature error log, avoid the extra validation branch and keep normal return behavior.

Implementation change:

```text
KernelPatchPostValidation.patchPostValidationNOP()
old accepted branch: tbnz only
new accepted branches: tbnz, tbz, cbz, cbnz, b.eq, b.ne
```

The locator is still semantic:

```text
find "TXM [Error]: CodeSignature"
find ADRP/ADD refs
scan a small forward window after the ref
NOP the first post-log conditional validation branch
```

It does not hardcode `0x0EACAB0`.

Verified patch:

```text
0x0EACAB0: b.eq 0xeacb98 -> nop
```

### Patch `[16]`: APFS `get-dev-by-role` Entitlement Gate

The APFS role lookup entitlement anchor also still exists:

```text
"com.apple.apfs.get-dev-by-role" @ file offset 0x581DAC
string ref sequence @ 0x1F9E540 / 0x1F9E544
```

The 18.5 handler shape is tighter than the legacy scan expected:

```asm
0x1F9E540  adrp x1, #0x581000
0x1F9E544  add  x1, x1, #0xdac ; "com.apple.apfs.get-dev-by-role"
0x1F9E548  bl   <entitlement_check>
0x1F9E54C  cbz  w0, 0x1F9E5B0
```

The branch target contains the entitlement-deny logging block. The observed 18.5 line ID in that block is:

```text
0x3EC2
```

Legacy kernels used different APFS line IDs:

```text
0x332D
0x333B
```

Implementation change:

```text
KernelPatchApfsMount.patchHandleGetDevByRole()
first preference: scan immediately after the entitlement string check for cbz/cbnz w0 into an entitlement-error block
fallback: preserve the legacy whole-function scan for older kernels
error-block line IDs: 0x332D, 0x333B, 0x3EC2
```

Again, the patch does not depend on the final 18.5 file offset. It depends on:

```text
string anchor -> nearby entitlement check -> branch on W0 -> recognized entitlement-deny block
```

Verified patch:

```text
0x1F9E54C: cbz w0, 0x1f9e5b0 -> nop
```

### Phase 4 Verification

Direct kernel verifier:

```bash
.build/debug/vphone-cli patch-component \
  --component kernel-base \
  --input /tmp/vphone-ios18-22F76/cloud/kernelcache.research.vresearch101 \
  --output /tmp/vphone-ios18-22F76/raw/kernelcache.research.vresearch101.basepatched.phase4.raw
```

Result:

```text
26 kernel patches emitted
[8]  0x0EACAB0: b.eq 0xeacb98 -> nop
[16] 0x1F9E54C: cbz w0, 0x1f9e5b0 -> nop
```

Full profile-aware dev pipeline verifier:

```bash
.build/debug/vphone-cli patch-firmware \
  --vm-directory /tmp/vphone-ios18-vm-profile \
  --variant dev \
  --firmware-profile ios18-22F76
```

Result:

```text
All 9 components patched successfully
61 total patch records
```

This is the first point where the Swift pipeline can produce a complete iOS 18.5 dev patch set without shim paths and without the known TXM/DeviceTree/kernel misses from the first dry-run.

## Phase 5 Progress Log - Real Workspace Build

Phase 5 moved from temp trees into the real repo `vm/` workspace.

The workspace was created with:

```bash
make vm_new VM_DIR=vm
```

Resulting workspace contents:

```text
vm/AVPBooter.vresearch1.bin
vm/AVPSEPBooter.vresearch1.bin
vm/Disk.img
vm/SEPStorage
vm/config.plist
```

Then firmware preparation was run against the local 18.5 IPSWs, not downloaded URLs:

```bash
make fw_prepare \
  VM_DIR=vm \
  FIRMWARE_PROFILE=ios18-22F76 \
  IPHONE_SOURCE=/Users/vinay/ipsw/iPhone17,3_18.5_22F76_Restore.ipsw \
  CLOUDOS_SOURCE=/Users/vinay/ipsw/cloudOS_18.5_22F76.ipsw
```

The prepare flow copied and extracted both IPSWs, imported cloudOS firmware components into the iPhone restore tree, and generated hybrid plists:

```text
firmware profile: ios18-22F76
cloudOS vresearch101ap: release=#2, research=#3 [boot]
cloudOS vresearch101ap: release=#2, research=#3 [runtime]
iPhone erase: #0
RecoveryMode: absent / skipped for vresearch101ap
Restore directory: vm/iPhone17,3_18.5_22F76_Restore
```

Generated real-workspace component paths:

```text
DeviceTree:         Firmware/all_flash/DeviceTree.vresearch101ap.im4p
RestoreDeviceTree:  Firmware/all_flash/DeviceTree.vresearch101ap.im4p
KernelCache:        kernelcache.research.vresearch101
RestoreKernelCache: kernelcache.release.vresearch101
iBSS:               Firmware/dfu/iBSS.vresearch101.RELEASE.im4p
iBEC:               Firmware/dfu/iBEC.vresearch101.RELEASE.im4p
LLB:                Firmware/all_flash/LLB.vresearch101.RELEASE.im4p
iBoot:              Firmware/all_flash/iBoot.vresearch101.RESEARCH_RELEASE.im4p
SEP:                Firmware/all_flash/sep-firmware.vresearch101.RELEASE.im4p
StaticTrustCache:   Firmware/044-89310-099.dmg.aea.trustcache
RestoreTrustCache:  Firmware/044-89333-100.dmg.trustcache
```

`BuildManifest.plist` does not carry a top-level `DeviceMap`; the generated `Restore.plist` does:

```text
d47ap
vresearch101ap
```

The real dev patch run was then applied directly to `vm/`:

```bash
make fw_patch_dev VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76
```

Result:

```text
All 9 components patched successfully
61 total patch records
```

Component counts:

```text
AVPBooter:   1
iBSS:        4
iBEC:        7
LLB:         9
TXM:         12
kernelcache: 26
DeviceTree:  2
```

The LLB patcher still reports that several old rootfs line-ID anchors are absent:

```text
mov w8, #0x3b7: absent
mov w8, #0x3c2: absent
mov w8, #0x110: absent
```

But it does emit the rootfs size-check and panic-bypass patches:

```text
0x027548: b.hs 0x276a4 -> nop
0x017DA4: cbnz w0, 0x17db8 -> nop
```

That keeps LLB as a boot-triage risk, not a pipeline blocker.

High-signal real-workspace offsets matched the clean temp verifier:

```text
TXM developer mode:       0x01B9C4  cbz w9, 0x1b9f4 -> b 0x1b9f4
kernel post-validation:   0x0EACAB0 b.eq 0xeacb98 -> nop
kernel APFS role gate:    0x1F9E54C cbz w0, 0x1f9e5b0 -> nop
DeviceTree serial:        0x000128
DeviceTree artwork:       0x00A964
```

The first ramdisk build attempt exposed a script bug before it reached firmware work:

```text
NameError: name 'shsh_dir' is not defined
```

That was in the missing-SHSH error path. The code now searches both supported SHSH locations:

```text
vm/*.shsh
vm/*.shsh2
vm/shsh/*.shsh
vm/shsh/*.shsh2
```

After the fix, `ramdisk_build` fails cleanly with the actual prerequisite:

```text
No SHSH blob found in /Users/vinay/vphone-cli/vm/ or /Users/vinay/vphone-cli/vm/shsh/
Run 'make restore_get_shsh' first, or place your .shsh/.shsh2 file in the VM directory.
```

Host preflight is not the blocker now. `make boot_host_preflight VM_DIR=vm` reports:

```text
model: MacBook Air
kern.hv_vmm_present: 0
SIP: disabled
allow-research-guests: enabled
current kern.bootargs: amfi_get_out_of_my_way=1 -v
signed release help: exit 0
```

So the next Phase 5 move is to boot DFU, read `vm/udid-prediction.txt`, fetch SHSH, then rerun ramdisk build.

DFU boot succeeded far enough to generate the deterministic identity file:

```text
vm/udid-prediction.txt
UDID=0000FE01-FD01E5DAE1ED866F
CPID=0x0000FE01
ECID=0xFD01E5DAE1ED866F
MACHINE_IDENTIFIER=config.plist
```

Recovery probing against that ECID succeeded, and SHSH fetch produced:

```text
vm/FD01E5DAE1ED866F.shsh
```

With SHSH present, ramdisk build reaches real artifact generation. Completed stages:

```text
iBSS.vresearch101.RELEASE.img4
iBEC.vresearch101.RELEASE.img4
sptm.vresearch1.release.img4
DeviceTree.vresearch101ap.img4
sep-firmware.vresearch101.RELEASE.img4
txm.img4
krnl.ramdisk.img4
krnl.img4
```

The builder derives `krnl.ramdisk.img4` from the pristine cached profile kernel:

```text
ipsws/045c5b04d14892c444162a975b69ba46438656e31ee6219173d4ceb3eb99acf6/kernelcache.research.vresearch101
```

Then it also builds `krnl.img4` from the patched restore kernel:

```text
vm/iPhone17,3_18.5_22F76_Restore/kernelcache.research.vresearch101
```

The remaining ramdisk blocker is not firmware pathing or signing. It is local privilege for mounting the restore ramdisk:

```text
sudo -n hdiutil attach \
  -mountpoint /Users/vinay/vphone-cli/vm/SSHRD \
  /Users/vinay/vphone-cli/vm/ramdisk_builder_temp/ramdisk.raw.dmg \
  -nobrowse \
  -owners off
```

Without cached sudo credentials, `sudo -n` returns:

```text
sudo: a password is required
```

`ramdisk_build.py` now preflights this condition before doing expensive signing work. The Makefile also refuses `sudo make ramdisk_build` before invoking SwiftPM. This matters because SwiftPM writes into `.build/`; running the target as root can leave root-owned Capstone/SwiftPM intermediates that later break normal builds with `Operation not permitted`.

Correct operator flow:

```bash
make patcher_build
sudo -v
make ramdisk_build VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76 RAMDISK_UDID=0000FE01-FD01E5DAE1ED866F

# or, for non-interactive automation:
VPHONE_SUDO_PASSWORD='<password>' make ramdisk_build VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76 RAMDISK_UDID=0000FE01-FD01E5DAE1ED866F
```

Do not run `sudo make ramdisk_build`. If that mistake already happened, remove or chown the root-owned `.build/` files and rebuild the patcher as the normal user before retrying.

After caching sudo with `sudo -v`, the normal-user ramdisk build completed:

```bash
make ramdisk_build VM_DIR=vm FIRMWARE_PROFILE=ios18-22F76 RAMDISK_UDID=0000FE01-FD01E5DAE1ED866F
```

Final `vm/Ramdisk/` artifacts:

```text
DeviceTree.vresearch101ap.img4                    63,385 bytes
iBEC.vresearch101.RELEASE.img4                   573,891 bytes
iBSS.vresearch101.RELEASE.img4                   573,891 bytes
krnl.img4                                     11,627,059 bytes
krnl.ramdisk.img4                             12,537,805 bytes
ramdisk.img4                                  266,344,013 bytes
sep-firmware.vresearch101.RELEASE.img4         3,069,568 bytes
sptm.vresearch1.release.img4                      98,846 bytes
trustcache.img4                                   16,177 bytes
txm.img4                                         154,205 bytes
```

Cleanup verifier:

```text
No /Users/vinay/vphone-cli/vm/SSHRD mount remains.
No ramdisk_builder_temp/ directory remains.
```

### Ramdisk Send Runtime Split

The first `ramdisk_send` attempt used the generated ramdisk-specific kernel:

```text
Ramdisk/krnl.ramdisk.img4
```

That send completed all iBoot transfer stages and issued `bootx`. Serial showed iBSS/iBEC, accepted ramdisk and DeviceTree, then stopped after iBoot handoff:

```text
loaded ramdisk at ...
loaded device tree at ...
======== End of iBoot serial output. ========
```

No Darwin kernel banner, `irecv`, or usbmux endpoint followed. The VM process stayed alive. Current state for that path: `candidate` early kernel handoff/hang for the derived `krnl.ramdisk.img4`.

The second attempt forced fallback to:

```text
Ramdisk/krnl.img4
```

That image is built from the restore-patched `kernelcache.research.vresearch101`, which had already proven it could boot far enough for disk-root/APFS validation. With `krnl.ramdisk.img4` moved aside, `ramdisk_send` selected `krnl.img4` and the SSH ramdisk booted:

```text
iBoot version: iBoot-11881.122.1
Darwin Image4 Extension Version 7.0.0
AMFI booted with research mode
AMFI: Enabling developer mode since we are restoring....
BSD root: md0, major 3, minor 0
container_rootmount:2603: boot from ramdisk /dev/md0
apfs_vfsop_mount: mount-complete volume ramdisk
libignition boot spec name: ramdisk
boot-args = serial=3 rd=md0 debug=0x2014e -v wdt=-1 rd=md0 -progress -restore
Starting ramdisk tool
USB init done
SSHRD_Script by Nathan (verygenericname)
Running server
```

Host-side verifier:

```text
usbmux-list -> 0000FE01-FD01E5DAE1ED866F
pymobiledevice3 usbmux forward --serial 0000FE01-FD01E5DAE1ED866F 2222 22
ssh root@127.0.0.1 -p 2222 -> ready
```

Implementation decision: for `ios18-22F76`, the profile now disables generated `krnl.ramdisk.img4` creation and `ramdisk_send` ignores stale `krnl.ramdisk.img4` if one exists. Legacy keeps the old preference because that behavior is documented for the existing vphone600 path.

The DFU VM was stopped after SHSH acquisition. No `vphone-cli --dfu` process remained after cleanup.

After SHSH acquisition, DFU was restarted and the real restore was executed:

```bash
make restore \
  VM_DIR=vm \
  RESTORE_UDID=0000FE01-FD01E5DAE1ED866F \
  RESTORE_ECID=0xFD01E5DAE1ED866F
```

The restore command exited 0. It transferred the large filesystem list:

```text
54272/54272
verify-restore: 100/100
```

The post-restore boot log is more useful than the restore command output. It shows the kernel getting much farther than the earlier patch-pipeline gates:

```text
Got boot device = ... AppleVirtIOStorageDevice ...
BSD root: disk0s1
apfs_vfsop_mountroot: apfs: mountroot called!
disk1s1 Rooting from snapshot with xid 61.
authenticate_root_hash: disk1s1:61 successfully validated on-disk root hash
mount-complete volume System
libignition boot spec name: local
```

That is a strong signal that the 18.5 profile, kernel patch set, DeviceTree selection, and restore manifest are coherent enough for disk boot and APFS root authentication.

The failure happens after that, at userspace start:

```text
libignition: cryptex1 sniff: ignition failed: 8
libignition: ignition boot failed: 8
Library not loaded: /usr/lib/libSystem.B.dylib
Reason: tried: '/usr/lib/libSystem.B.dylib' (no such file, no dyld cache)
panic: initproc failed to start
Panicked task: pid 1 launchd
```

Current interpretation: this was not evidence that the Phase 1-4 firmware patching failed. It was a pre-CFW userspace completeness failure: the restored disk could authenticate and mount the sealed system snapshot, but `launchd` could not find the dyld cache / `libSystem` path because the Cryptex payloads had not been installed yet.

The CFW install was then run from the SSH ramdisk:

```bash
make cfw_install_dev VM_DIR=vm SSH_PORT=2222
```

That completed. The high-signal stages were:

```text
SystemOS Cryptex -> /mnt1/System/Cryptexes/OS
AppOS Cryptex    -> /mnt1/System/Cryptexes/App
launchd jetsam guard:        0xD618 tbnz -> b
debugserver entitlements:    task_for_pid-allow added
APFS update snapshot:        renamed to orig-fs
launchd_cache_loader gate:   0xB58 cbz -> nop
mobileactivationd:           0x17320 mov x0, #1; ret
LaunchDaemons:               bash/dropbear/trollvnc/vphoned/rpcserver_ios injected
```

Transient `ssh`/`scp` disconnects happened during the copy/patch stages, but the script's retry loop recovered and the command reached the normal completion path:

```text
[+] CFW installation complete!
Reboot the device for changes to take effect.
After boot, SSH will be available on port 22222 (password: alpine)
```

The next verifier is now first normal boot after CFW. The specific regression test is the earlier `launchd` panic: if the boot still reports `Library not loaded: /usr/lib/libSystem.B.dylib`, `no dyld cache`, or `libignition ... cryptex1 ... failed`, then the CFW/Cryptex packaging path becomes the active confirmed blocker. If it passes that point, the next gates are activation, LaunchDaemon startup, and host-to-guest control over `vphoned`.

## Working Notes For Next Session

Do not start by changing offsets. Phase 1 profile plumbing, Phase 2 TXM retargeting, Phase 3 DeviceTree profile patching, and Phase 4 kernel miss retargeting are done. Phase 5 has created, prepared, dev-patched, DFU-booted, fetched SHSH, restored the real `vm/` workspace, built the SSH ramdisk, booted it using `krnl.img4`, and completed `cfw_install_dev`. Disk boot reached APFS root authentication before CFW but panicked because Cryptex/dyld content was not yet deployed. That exact panic must now be re-tested after CFW.

Concrete next commands/targets:

```bash
# first normal boot after CFW; Vinay runs this locally to watch the console
make boot VM_DIR=vm
```

Good signs:

```text
BSD root: disk0s1
authenticate_root_hash ... successfully validated
libignition boot spec name: local
```

Bad old failure signature:

```text
libignition: cryptex1 sniff: ignition failed
Library not loaded: /usr/lib/libSystem.B.dylib
Reason: ... no dyld cache
panic: initproc failed to start
```

When patch logic changes, update [0_binary_patch_comparison.md](0_binary_patch_comparison.md).
