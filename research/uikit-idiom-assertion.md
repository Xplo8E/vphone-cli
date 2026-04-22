# UIKit idiom assertion root cause

Smallest fix for the observed SpringBoard abort: override MobileGestalt `DeviceClassNumber` to an integer value that maps to `UIUserInterfaceIdiomPhone`. Use `DeviceClassNumber = 1` as the cleanest value. For this specific UIKitCore assertion path, `ProductType = iPhone17,3` is not required: `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` does not read `ProductType`, `HWModelStr`, `HWMachine`, or `DeviceClass`; it reads only `DeviceClassNumber`.

IDA evidence from `/tmp/uikit_extract/UIKitCore`:

```text
symbol: __UIDeviceNativeUserInterfaceIdiomIgnoringClassic
start:  0x185599978
key:    "DeviceClassNumber" at 0x186cff021
assert file: "UIDevice.m"
assert line: 852
assert reason: "Device type is not associated with user interface idiom."
```

The function loads the CFString `DeviceClassNumber`, calls an unresolved external answer-copy helper at `0x18C216740` with `x1 = 0`, sends `intValue` to the returned object, then validates the integer. In the extracted single-image IDA view, the exact external target is outside the loaded UIKitCore segment, but the call shape and key are consistent with a MobileGestalt answer lookup. The local MG auth stubs (`_MGCopyAnswer`, `_MGCopyAnswerWithError`, `_MGGetSInt32Answer`, `_MGIsDeviceOneOfType`) exist in UIKitCore, but this function does not branch to those stubs directly.

The assertion predicate is:

```text
v = [answer intValue]
i = v - 1
if i >= 7: assert
if ((0x6f >> i) & 1) == 0: assert
return qword_186C821C0[i]
```

Accepted raw `DeviceClassNumber` values are `1, 2, 3, 4, 6, 7`. The return table maps them as:

```text
1 -> 0  Phone
2 -> 0  Phone-compatible
3 -> 1  Pad
4 -> 2  TV
6 -> 4  Watch
7 -> 0  Phone-compatible
```

So for SpringBoard, set `DeviceClassNumber = 1` and retry. If a broader MobileGestalt compatibility profile is needed later, `ProductType` can still be overridden separately, but it is not the key tripping this UIKit assertion.

Implementation status: the deterministic plist edit remains in `scripts/patchers/cfw_patch_mobilegestalt.py`, but direct ramdisk editing is not the active path because Data-volume `mount_apfs` hangs from the SSH ramdisk. The active path is boot-time instead: install `/usr/bin/vphone_mgpatch` plus `/System/Library/LaunchDaemons/vphone_mgpatch.plist` into the System volume and inject it into `/System/Library/xpc/launchd.plist`. The binary waits for the MobileGestalt cache during normal boot, writes `CacheExtra["DeviceClassNumber"] = 1`, and leaves `/private/var/root/.vphone_mobilegestalt_patched` as a verifier.
