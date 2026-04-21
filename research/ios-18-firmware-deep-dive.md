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

## Working Notes For Next Session

Do not start by changing offsets. Start with profiles.

Concrete next commands/targets:

```bash
# manifest/profile failure reproduction
python3 scripts/fw_manifest.py /tmp/vphone-ios18-manifest-test/iphone /tmp/vphone-ios18-manifest-test/cloud

# TXM IDA target already decoded
/tmp/vphone-ios18-22F76/raw/txm.cloud.research.raw

# kernel IDA target for next slice
/tmp/vphone-ios18-22F76/cloud/kernelcache.research.vresearch101
```

When patch logic changes, update [0_binary_patch_comparison.md](0_binary_patch_comparison.md). For this pass, only research docs changed.
