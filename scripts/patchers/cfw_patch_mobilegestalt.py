"""
cfw_patch_mobilegestalt.py — Patch MobileGestalt cache for UIKit idiom.

Problem: On iOS 18.5, `UIKitCore` asserts inside
`_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` when MobileGestalt reports
`DeviceClassNumber` outside UIKit's known raw device-class set. SpringBoard
and AccessibilityUIServer crash-loop, UI never appears.

Fix: rewrite `CacheExtra["DeviceClassNumber"] = 1`, which makes UIKit map the
device to `UIUserInterfaceIdiomPhone` (0). IDA confirmed this exact UIKitCore
function only reads `DeviceClassNumber`; it does not read ProductType,
HWModelStr, HWMachine, or DeviceClass on this assertion path. `CacheExtra` is
merged into query results *after* the signed `CacheData`, so overriding it does
not break the cache signature.

The cache file on device lives at:
    /var/containers/Shared/SystemGroup/\
    systemgroup.com.apple.mobilegestaltcache/Library/Caches/\
    com.apple.MobileGestalt.plist

The file is an NSKeyedArchiver-free binary plist at the top level (dict with
`CacheData` / `CacheExtra` entries). We only touch `CacheExtra`.
"""

import plistlib
import shutil
import sys


# Minimal override confirmed by IDA in
# research/uikit-idiom-assertion.md. Raw DeviceClassNumber 1 maps through
# UIKitCore's qword_186C821C0 table to UIUserInterfaceIdiomPhone (0).
IPHONE_IDIOM_OVERRIDES = {
    "DeviceClassNumber": 1,
}


# Broader identity spoofing is kept explicit for later compatibility testing.
# It is not required for _UIDeviceNativeUserInterfaceIdiomIgnoringClassic.
IPHONE_IDENTITY_OVERRIDES = {
    **IPHONE_IDIOM_OVERRIDES,
    "ProductType": "iPhone17,3",              # iPhone 16 Pro Max product type
    "DeviceClass": "iPhone",
    "HWModelStr": "D94AP",                    # iPhone 16 Pro Max board id
    "ProductName": "iPhone OS",
    "HWMachine": "iPhone17,3",
    "ArtworkDeviceProductDescription": "iPhone",
    "ArtworkDeviceSubType": 2796,             # screen height bucket used by UIKit artwork
    "main-display-rotation": 0,
    "MobileSubscriberCountryCode": "us",
    "MobileSubscriberNetworkCode": "00",
}


def _load_bplist(path):
    """Load the cache as a plist dict; raise if the format is unexpected."""
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(b"bplist"):
        raise RuntimeError(
            f"{path}: not a bplist (first 8 bytes: {data[:8]!r}). "
            "The cache may be in a signed/wrapped format; patcher would need updating."
        )
    pl = plistlib.loads(data)
    if not isinstance(pl, dict):
        raise RuntimeError(f"{path}: root is {type(pl).__name__}, expected dict")
    return pl


def _save_bplist(path, plist_obj):
    with open(path, "wb") as f:
        plistlib.dump(plist_obj, f, fmt=plistlib.FMT_BINARY)


def patch_mobilegestalt(cache_path, out_path=None, overrides=None, verbose=True):
    """Patch MobileGestalt cache at `cache_path`. In-place if `out_path` is None."""
    overrides = overrides or IPHONE_IDIOM_OVERRIDES
    pl = _load_bplist(cache_path)

    # Make sure CacheExtra exists; MG tolerates its absence on untouched caches.
    cache_extra = pl.get("CacheExtra")
    if not isinstance(cache_extra, dict):
        cache_extra = {}
        pl["CacheExtra"] = cache_extra

    if verbose:
        print(f"[*] MobileGestalt cache: {cache_path}")
        print(f"    top-level keys: {sorted(pl.keys())}")
        print(f"    CacheExtra entries before: {len(cache_extra)}")

    changed = 0
    for key, value in overrides.items():
        prev = cache_extra.get(key)
        if prev != value:
            if verbose:
                print(f"    [+] CacheExtra[{key!r}] = {value!r}  (was {prev!r})")
            cache_extra[key] = value
            changed += 1

    target = out_path or cache_path
    if out_path is None and changed == 0:
        if verbose:
            print("    [=] no changes needed")
        return True

    _save_bplist(target, pl)
    if verbose:
        print(f"    [+] wrote patched cache ({changed} overrides) → {target}")
    return True


def main(argv):
    if len(argv) < 2 or len(argv) > 4:
        print("Usage: cfw_patch_mobilegestalt.py <cache.plist> [<out.plist>] [--full-identity]", file=sys.stderr)
        return 2
    src = argv[1]
    args = argv[2:]
    full_identity = False
    if "--full-identity" in args:
        full_identity = True
        args.remove("--full-identity")
    if len(args) > 1:
        print("Usage: cfw_patch_mobilegestalt.py <cache.plist> [<out.plist>] [--full-identity]", file=sys.stderr)
        return 2
    dst = args[0] if args else None
    if dst and dst != src:
        shutil.copy2(src, dst)
        src = dst
        dst = None
    overrides = IPHONE_IDENTITY_OVERRIDES if full_identity else IPHONE_IDIOM_OVERRIDES
    return 0 if patch_mobilegestalt(src, dst, overrides=overrides) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
