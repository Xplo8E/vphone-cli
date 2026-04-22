"""Patch UIKitCore idiom resolver in the SystemOS dyld shared cache.

For iOS 18.5 / 22F76, SpringBoard and AccessibilityUIServer abort inside
`_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` when the PCC VM reports an
unsupported device class. The MobileGestalt cache override is not authoritative
for this early UIKit path, so patch the resolver itself to return
`UIUserInterfaceIdiomPhone` (0).
"""

from __future__ import annotations

from pathlib import Path
import sys

# Resolved with: ipsw dyld a2o dyld_shared_cache_arm64e 0x185599978 --hex
#   sub_cache=dsc.03, aggregate-offset=0x5599978, file-offset=0x1a5978
SUBCACHE_NAME = "dyld_shared_cache_arm64e.03"
FUNC_OFFSET = 0x1A5978
EXPECTED = bytes.fromhex("7f2303d5 f44fbea9")  # pacibsp; stp x20,x19,[sp,#-0x20]!
PATCHED = bytes.fromhex("000080d2 c0035fd6")  # mov x0,#0; ret


def patch_uikit_idiom(sysos_mount: str | Path) -> bool:
    cache = Path(sysos_mount) / "System/Library/Caches/com.apple.dyld" / SUBCACHE_NAME
    if not cache.exists():
        raise FileNotFoundError(cache)

    with cache.open("r+b") as f:
        f.seek(FUNC_OFFSET)
        current = f.read(len(EXPECTED))
        if current == PATCHED:
            print(f"  [=] UIKit idiom patch already applied: {cache}:{FUNC_OFFSET:#x}")
            return True
        if current != EXPECTED:
            raise RuntimeError(
                f"unexpected bytes at {cache}:{FUNC_OFFSET:#x}: "
                f"got {current.hex()} expected {EXPECTED.hex()}"
            )
        f.seek(FUNC_OFFSET)
        f.write(PATCHED)
        f.flush()

    print(f"  [+] UIKit idiom patch applied: {cache}:{FUNC_OFFSET:#x}")
    print("      _UIDeviceNativeUserInterfaceIdiomIgnoringClassic -> mov x0,#0; ret")
    return True


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: cfw_patch_uikit_idiom.py <mounted SystemOS root>", file=sys.stderr)
        return 2
    patch_uikit_idiom(argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
