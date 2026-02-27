# VZ Coprocessor Configuration Investigation

## Environment
- Host: macOS 26.3 (25D125), Apple Silicon
- Firmware: cloudOS 23B85 / iOS 26.1 (iPhone17,3) mixed
- Binary: super-tart with VPHONE_MODE=1

## Error
```
Error Domain=VZErrorDomain Code=2 "The coprocessor configuration is invalid."
UserInfo={NSLocalizedFailure=Invalid virtual machine configuration.,
NSLocalizedFailureReason=The coprocessor configuration is invalid.}
```

Also warns:
```
WARNING: Trying to access an unrecognized member: VZMacOSVirtualMachineStartOptions._setPanicAction:
WARNING: Trying to access an unrecognized member: VZMacOSVirtualMachineStartOptions._setFatalErrorAction:
```

## Root Cause: Missing `romBinaryURL` on SEP config

### Current code (VM.swift:361-366) — BROKEN
```swift
let sepstorageURL = vmRoot.appendingPathComponent("SEPStorage")
let sepConfig = Dynamic._VZSEPCoprocessorConfiguration(storageURL: sepstorageURL)
sepConfig.debugStub = Dynamic._VZGDBDebugStubConfiguration(port: 8001)
Dynamic(configuration)._setCoprocessors([sepConfig.asObject])
```

### Old working code (docs/README_old.md:106-111)
```swift
let sep_config = Dynamic._VZSEPCoprocessorConfiguration(storageURL: sepstorageURL)
if let sepromURL { // default AVPSEPBooter.vresearch1.bin from VZ framework
    sep_config.romBinaryURL = sepromURL
}
sep_config.debugStub = Dynamic._VZGDBDebugStubConfiguration(port: 8001)
configuration._setCoprocessors([sep_config.asObject])
```

### Diff: `romBinaryURL` is not set in current code

The SEP ROM binary exists on disk:
```
/System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPSEPBooter.vresearch1.bin
```

Without it, `_VZSEPCoprocessorConfiguration` has no SEPROM → validation fails.

### Also: platformVersion changed
| | Old (working) | Current (broken) |
|---|---|---|
| platformVersion | 3 (.appleInternal4) | 2 |
| boardID | 0x90 | not set |
| ISA | 2 | 2 |
| OS version hints | not set | set (required on 26+) |

## _VZSEPCoprocessorConfiguration class methods (macOS 26.3)

Instance methods:
```
- initWithStorageURL:
- storage
- romBinaryURL
- setRomBinaryURL:
- debugStub
- setDebugStub:
- _coprocessor
- makeCoprocessorForVirtualMachine:coprocessorIndex:
- encodeWithEncoder:
- copyWithZone:
- initWithStorage:
- .cxx_destruct
- .cxx_construct
```

## VZVirtualMachineConfiguration coprocessor methods (macOS 26.3)
```
- _coprocessors
- _setCoprocessors:
- _coprocessorStorageFileDescriptor
- _setCoprocessorStorageFileDescriptor:
```

## _VZMacHardwareModelDescriptor methods (macOS 26.3)
```
- init
- setPlatformVersion:
- setBoardID:
- setISA:
- setInitialGuestMacOSVersion:
- setMinimumSupportedHostOSVersion:
- setVariantID:variantName:          ← NEW on 26.3
```

## VZMacHardwareModel class methods
```
+ _defaultBoardIDForPlatformVersion:
+ _defaultHardwareModel
+ _hardwareModelWithDescriptor:
```

## SEP firmware files in mixed firmware
```
firmwares/firmware_patched/.../Firmware/all_flash/sep-firmware.vphone600.RELEASE.im4p
firmwares/firmware_patched/.../Firmware/all_flash/sep-firmware.vresearch101.RELEASE.im4p
firmwares/firmware_patched/.../Firmware/all_flash/sep-firmware.vphone600.RELEASE.im4p.plist
firmwares/firmware_patched/.../Firmware/all_flash/sep-firmware.vresearch101.RELEASE.im4p.plist
```

## AVPBooter/SEPBooter files on host (macOS 26.3)
```
/System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/
  AVPBooter.vmapple2.bin      (234176 bytes)
  AVPBooter.vresearch1.bin    (251856 bytes)  ← used as ROM
  AVPSEPBooter.vresearch1.bin (167936 bytes)  ← needed for romBinaryURL
```

## VM directory (.tart/vms/vphone/)
```
AVPBooter.vmapple2.bin   (251856 bytes — note: this is actually vresearch1 size)
SEPStorage/              (EMPTY — framework manages this)
config.json
disk.img                 (1 GB)
nvram.bin                (33 MB)
```

## IDA Target for `setVariantID:variantName:`

Binary is in dyld shared cache:
```
/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
```
Open in IDA → select `Virtualization` module → search for `setVariantID:variantName:` in ObjC methods.

This is a new selector on macOS 26.3 on `_VZMacHardwareModelDescriptor`. May distinguish vresearch vs vphone platform variants.

## Next Steps

1. **Immediate fix**: Add `romBinaryURL` back — point to `AVPSEPBooter.vresearch1.bin`
2. **Investigate in IDA**: What does `setVariantID:variantName:` do? Does it affect hardware model validation for vphone?
3. **Investigate**: Should platformVersion be 3 (old) or 2 (current)? The old code with pv=3 + boardID=0x90 worked, current pv=2 may need OS version hints to compensate
4. **Check**: Does `_setCoprocessorStorageFileDescriptor:` offer an alternative init path?
