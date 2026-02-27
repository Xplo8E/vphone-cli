# vrevm / Virtualization.framework Analysis — macOS 26 beta 3

**Date:** 2026-02-26
**macOS:** Version 26.3 (Build 25D125)
**Binary:** `/System/Library/SecurityResearch/usr/bin/vrevm` (1693 functions, arm64e)

---

## Summary

On macOS 26 beta 3, Apple **removed platformVersion=3 (vresearch101) support** from Virtualization.framework. The vrevm binary itself is unchanged from the open-source security-pcc code, but the framework now rejects the hardware model configuration that vrevm and super-tart use for vphone VMs.

## Platform Version Support Matrix

Tested by creating `_VZMacHardwareModelDescriptor` objects and calling `VZMacHardwareModel._hardwareModelWithDescriptor:` then checking `isSupported`:

| PV | ISA 0-4 | Default boardID | minOS | state+0x24 (validity) | Notes |
|----|---------|-----------------|-------|-----------------------|-------|
| 0 | all false | 0xFFFFFFFF | — | — | Unknown/invalid PV |
| 1 | all false | 0xF8 (248) | 12.0.0 | 0 | Old Mac default — **dropped** |
| **2** | **all SUPPORTED** | **0x20 (32)** | **12.0.0** | **1** | **Only supported PV** |
| 3 | all false | 0x90 (144) | 15.0.0 | **0** | vresearch101 — **dropped** |
| 4 | all false | 0xFFFFFFFF | — | — | Unknown/invalid PV |
| 5 | all false | 0xFFFFFFFF | — | — | Unknown/invalid PV |

**Key observation:** PV=3 is *recognized* by the framework (state pointer exists, boardID=0x90 returned correctly, minOS=15.0.0) but the **validity byte at state+0x24 is set to 0**, meaning Apple deliberately disabled it.

## isSupported Implementation (Virtualization.framework)

Disassembled from `Virtualization`-[VZMacHardwareModel isSupported]` at `0x23510d20c`:

```asm
isSupported:
  ldr    x8, [x0, #0x38]           ; Load internal state pointer
  cbz    x8, return_false           ; If NULL → return false
  ldrb   w8, [x8, #0x24]           ; Load validity byte
  cmp    w8, #0x1                   ; Must equal 1
  b.ne   return_false               ; If != 1 → return false
  ; Then check host OS version:
  ldr    q0, [x0, #0x10]           ; Load minOSVersion.major + .minor
  ldr    x8, [x0, #0x20]           ; Load minOSVersion.patch
  ; Call [NSProcessInfo.processInfo isOperatingSystemAtLeastVersion:]
  ; Return that result
return_false:
  mov    w0, #0x0
  ret
```

Three-stage check:
1. State pointer at `self+0x38` must not be NULL
2. Byte at `state+0x24` must equal 1 (validity flag)
3. Host macOS version >= `minimumSupportedHostOSVersion` stored in the model

For PV=3: stage 2 fails (validity=0). For PV=2: all stages pass.

## VZMacHardwareModel Object Layout

| Offset | Size | Field | PV=2 ISA=2 | PV=3 ISA=2 |
|--------|------|-------|------------|------------|
| +0x08 | 8 | ISA | 2 | 2 |
| +0x10 | 8 | minOSVersion.major | 12 | 15 |
| +0x18 | 8 | minOSVersion.minor | 0 | 0 |
| +0x20 | 8 | minOSVersion.patch | 0 | 0 |
| +0x28 | 4 | boardID | 0x20 | 0x90 |
| +0x30 | 8 | variantID | 0 | 0 |
| +0x38 | 8 | state_ptr | valid | valid |
| state+0x24 | 1 | validity | **1** | **0** |

## Data Representation (bplist)

PV=2 ISA=2:
```
DataRepresentationVersion = 1
PlatformVersion = 2
ISA = 2
MinimumSupportedOS = (12, 0, 0)
```

PV=3 ISA=2 (unsupported):
```
DataRepresentationVersion = 1
PlatformVersion = 3
ISA = 2
MinimumSupportedOS = (15, 0, 0)
```

## boardID Sweep

PV=3 + any boardID (0x00–0xFE): all return `isSupported=false`
PV=2 + any boardID (0x00–0xFE): all return `isSupported=true`

The boardID from setBoardID is passed through to the model but does NOT affect isSupported. Only the platformVersion determines validity.

## Impact on vphone

- **vrevm** uses PV=3 + ISA=2 → **fails** on macOS 26.3 with "VM hardware config not supported (model.isSupported = false)"
- **super-tart** was patched to use PV=2 + ISA=2 → passes `isSupported` check
- **BUT** PV=2 gives boardID=0x20 (default Mac VM), not 0x90 (VPHONE600AP)
- The vphone firmware (iBSS/iBEC/LLB/kernel) may check boardID and refuse to boot with boardID=0x20
- Setting boardID=0x90 explicitly with PV=2 makes `isSupported` still return true, but whether the firmware accepts this combination is untested

## Workaround: ObjC Runtime Swizzle of isSupported

Patching the framework binary is impractical (dyld shared cache). Instead, use ObjC runtime `method_setImplementation` to hook `-[VZMacHardwareModel isSupported]` before creating the hardware model:

```swift
import ObjectiveC

let cls: AnyClass = VZMacHardwareModel.self
let sel = NSSelectorFromString("isSupported")
let method = class_getInstanceMethod(cls, sel)!
let alwaysTrue: @convention(block) (AnyObject) -> Bool = { _ in true }
method_setImplementation(method, imp_implementationWithBlock(alwaysTrue))
```

Then use the real vresearch101 config: `setPlatformVersion(3)`, `setBoardID(0x90)`, `setISA(2)`.

### Swizzle Test Results

| Config | isSupported | validate() | VZVirtualMachine init | start() | Notes |
|--------|-------------|------------|----------------------|---------|-------|
| PV=3 + boardID=0x90 (no swizzle) | **false** | — | — | — | Apple disabled PV=3 |
| PV=3 + boardID=0x90 + swizzle | **true** | **PASS** | **PASS** | see below | Swizzle works |
| PV=2 + boardID=0x90 (no swizzle) | **true** | **PASS** | **PASS** | see below | PV=2 natively supported |

### VM Start Results (with SEP coprocessor)

| Config | SEP Config | start() Result |
|--------|-----------|----------------|
| PV=3 + swizzle + SEP full (ROM+debug) | `_VZSEPCoprocessorConfiguration` + `romBinaryURL` + `debugStub` | **FAIL**: "The coprocessor configuration is invalid." |
| PV=3 + swizzle + SEP minimal (storage only) | `_VZSEPCoprocessorConfiguration` (no ROM, no debug) | **FAIL**: same error |
| PV=2 + SEP full | same as above | **FAIL**: same error |
| PV=3 + swizzle + **no SEP** (`SKIP_SEP=1`) | no `_setCoprocessors` call | **PASS** — VM starts and enters DFU |
| PV=2 + **no SEP** | no `_setCoprocessors` call | **PASS** — VM starts and enters DFU |

**Key finding:** The SEP coprocessor configuration is rejected by the hypervisor at `virtualMachine.start(options:)` regardless of platform version. This is a **separate** restriction from the `isSupported` validity byte — Apple also blocked `_VZSEPCoprocessorConfiguration` at the hypervisor/XPC level in macOS 26.3.

The error occurs in the `start()` call path (after `validate()` passes and `VZVirtualMachine` init succeeds), meaning the rejection happens inside the hypervisor daemon (`com.apple.Virtualization.VirtualMachine` XPC service), not in the framework's ObjC layer.

### Confirmed Boot Sequence (without SEP)

```
[swizzle] OK: -[VZMacHardwareModel isSupported] now always returns true
[vzHardwareModel] setPlatformVersion=3, setBoardID=0x90, setISA=2
[vzHardwareModel] plist: {
    DataRepresentationVersion = 1;
    ISA = 2;
    MinimumSupportedOS = (15, 0, 0);
    PlatformVersion = 3;
}
[vzHardwareModel] isSupported = true (after swizzle)
[craftConfig] ECID: 0x1de1518ecffe2725
[craftConfig] serialNumber: AAAAAA1337
[craftConfig] productionMode: true
[craftConfig] ========== CONFIGURATION VALID ==========
[VM.init] VZVirtualMachine created successfully
[VM.start] calling virtualMachine.start(options:)...
→ VM enters DFU mode, ready for irecovery firmware load
```

## Remaining Blockers

1. **SEP coprocessor rejected at hypervisor level** — `_VZSEPCoprocessorConfiguration` fails during `start()` for both PV=2 and PV=3. Without SEP, the vphone firmware bootchain will fail at stages that require SEP (e.g., secure boot, data protection). Need to investigate whether the hypervisor XPC service has its own `isSupported`-like check that can be bypassed, or whether this requires a different approach entirely.

2. **`_setPanicAction:` and `_setFatalErrorAction:` missing** — These `VZMacOSVirtualMachineStartOptions` methods are not recognized on macOS 26.3 (warnings in output). The APIs may have been renamed or removed.

## Possible Next Steps

1. **Boot without SEP** — Load the patched firmware via irecovery into the DFU VM to see how far the bootchain gets without SEP. iBSS/iBEC may still load; the kernel will likely panic when SEP is unavailable.

2. **Investigate hypervisor SEP validation** — The XPC service at `/System/Library/Frameworks/Virtualization.framework/Versions/A/XPCServices/com.apple.Virtualization.VirtualMachine.xpc` likely has additional checks. May need to reverse-engineer the XPC protocol or find a way to hook the daemon.

3. **Use macOS 26 beta 2** — Downgrade to a version where both PV=3 and SEP coprocessor are supported.

4. **Try `_coprocessorStorageFileDescriptor`** — `VZVirtualMachineConfiguration` has a `_coprocessorStorageFileDescriptor` property that may be an alternative way to configure SEP storage without the full `_VZSEPCoprocessorConfiguration`.

---

## vrevm Decompiled Functions

### sub_100055D28 — vzHardwareModel(platformType:)

```c
id sub_100055D28(char a1) {
  if ((a1 & 1) != 0) {
    // platformType == vresearch101
    v1 = [_VZMacHardwareModelDescriptor alloc] init];
    [v1 setPlatformVersion:3];
    [v1 setISA:2];
    v2 = [VZMacHardwareModel _hardwareModelWithDescriptor:v1];
    [v1 release];
    if (![v2 isSupported]) {
      // Throws VMError("VM hardware config not supported (model.isSupported = false)")
      throw VMError(0xD00000000000003C, 0x8000000100065CF0);
    }
  } else {
    // Unsupported platform type — throws error
    throw VMError(...);
  }
  return v2;
}
```

### sub_100054C28 — vzMachineConfig(bundle:platformType:platformFusing:machineIDBlob:avpsepbooter:)

Creates the full VM configuration:
1. Creates `VZVirtualMachineConfiguration` + `VZMacPlatformConfiguration`
2. Calls `vzHardwareModel(platformType:)` → sets hardware model
3. Sets machine identifier from blob
4. Creates SEP coprocessor:
   - `_VZSEPCoprocessorConfiguration(storageURL: bundle/SEPStorage)`
   - Optionally sets `romBinaryURL:` (AVPSEPBooter)
   - Creates `_VZGDBDebugStubConfiguration` for SEP debugging
   - Calls `_setCoprocessors:` with SEP config array
5. Sets production mode: compares fusing "dev" vs "prod", defaults to production
6. Display: `VZMacGraphicsDisplayConfiguration(1290, 2796, 460)` (iPhone 16 Pro Max)
7. Creates `VZMacAuxiliaryStorage` from bundle path

### sub_10005595C — vzVirtMeshDevice(path:rank:)

Creates `_VZCustomVirtioDeviceConfiguration`:
- PCI Vendor: 0x106B (Apple)
- PCI Device: 0x1A0E (kVirtMeshVirtioDevice)
- PCI Class: 0xFF
- 3 virtio queues
- Plugin: `com.apple.AppleVirtMeshPlugin.Virtio`
- `_supportsSaveRestore = true`
- `setOptionalFeatures:atIndex:` for VirtMesh node rank

### sub_1000047DC — VM.open() / run flow

The main VM open function:
1. Checks `VZVirtualMachine.isSupported`
2. Reads bundle config.plist
3. Creates VM configuration via `vzMachineConfig`
4. Creates `VZVirtualMachine(configuration:queue:)`
5. Sets up console I/O pipes
6. Runs the VM

---

## Private _VZ Classes in Virtualization.framework (macOS 26.3)

110+ private classes. Key ones used by vrevm:

- `_VZMacHardwareModelDescriptor` — Hardware model configuration
- `_VZSEPCoprocessorConfiguration` — SEP setup (storage, ROM, debug stub)
- `_VZSEPCoprocessor` — SEP runtime
- `_VZGDBDebugStubConfiguration` — GDB debug stub for SEP
- `_VZCustomVirtioDeviceConfiguration` — Custom virtio (VirtMesh)
- `_VZHostOnlyNetworkDeviceAttachment` — Host-only networking
- `_VZPL011SerialPortConfiguration` — PL011 UART serial port
- `_VZCoprocessorConfiguration` — Base coprocessor config
- `_VZDebugStubConfiguration` — Base debug stub config

New/interesting classes (not used by vrevm):
- `_VZMacTouchIDDeviceConfiguration` — TouchID passthrough
- `_VZAppleTouchScreenConfiguration` — Apple touch screen (vphone touch?)
- `_VZMacNeuralEngineDeviceConfiguration` — ANE passthrough
- `_VZMacScalerAcceleratorDeviceConfiguration` — M2 scaler
- `_VZMacVideoToolboxDeviceConfiguration` — VideoToolbox passthrough
- `_VZPCIPassthroughDeviceConfiguration` — PCI device passthrough
- `_VZMacBatteryPowerSourceDeviceConfiguration` — Battery simulation
- `_VZMacWallPowerSourceDeviceConfiguration` — Wall power simulation
- `_VZCPUEmulatorConfiguration` / `_VZCustomCPUEmulatorConfiguration` — CPU emulation
- `_VZMacBifrostDeviceConfiguration` — Bifrost (Apple's inter-VM comms)
- `_VZBiometricDeviceConfiguration` — Biometric device
- `_VZVNCServer` — Built-in VNC server
- `_VZLinearFramebufferGraphicsDeviceConfiguration` — Linear framebuffer
- `_VZMacRemoteServiceDiscoveryConfiguration` — RemoteServiceDiscovery config
- `_VZMemory` — Direct memory access (physicalAddress, mutableBytes)
- `_VZGuestTraceEvent` / `_VZMacOSBootLoaderGuestTraceEvent` — Guest tracing
