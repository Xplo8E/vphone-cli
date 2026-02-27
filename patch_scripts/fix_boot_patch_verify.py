#!/usr/bin/env python3
"""
Patch + verify fix_boot binaries exactly like original-research flow.

Defaults expect files in /tmp:
  /tmp/launchd_cache_loader
  /tmp/mobileactivationd
  /tmp/launchd

Usage:
  python3 patch_scripts/fix_boot_patch_verify.py --patch
  python3 patch_scripts/fix_boot_patch_verify.py --verify
  python3 patch_scripts/fix_boot_patch_verify.py --patch --verify
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


PATCHES = {
    "launchd_cache_loader": {
        "offset": 0xB58,
        "value": 0xD503201F,  # NOP
    },
    "mobileactivationd": {
        "offset": 0x2F5F84,
        "value": 0xD2800020,  # MOV X0, #1
    },
    "launchd": {
        "offset": 0xD73C,
        "value": 0x14000017,  # B #0x5C
    },
}


def u32le_at(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def patch_file(path: Path, off: int, value: int) -> None:
    b = bytearray(path.read_bytes())
    if off + 4 > len(b):
        raise ValueError(f"offset 0x{off:X} out of range for {path} (size={len(b)})")
    b[off : off + 4] = value.to_bytes(4, "little")
    path.write_bytes(b)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/tmp", help="Directory containing local binaries")
    ap.add_argument("--patch", action="store_true", help="Apply patches")
    ap.add_argument("--verify", action="store_true", help="Verify patch values")
    args = ap.parse_args()

    if not args.patch and not args.verify:
        args.verify = True

    root = Path(args.dir)
    print(f"Using directory: {root}")

    for name, spec in PATCHES.items():
        p = root / name
        off = spec["offset"]
        val = spec["value"]
        if not p.exists():
            print(f"[MISS] {p} not found")
            continue

        if args.patch:
            patch_file(p, off, val)
            print(f"[PATCH] {name}: 0x{off:X} <= 0x{val:08X}")

        if args.verify:
            cur = u32le_at(p.read_bytes(), off)
            status = "OK" if cur == val else "BAD"
            print(
                f"[{status}] {name}: off=0x{off:X} dec={off} "
                f"u32=0x{cur:08X} expect=0x{val:08X}"
            )

    print("\ndd checks (little-endian bytes expected):")
    for name, spec in PATCHES.items():
        off = spec["offset"]
        want_le = spec["value"].to_bytes(4, "little").hex()
        print(
            f"  dd if={root / name} bs=1 skip={off} count=4 2>/dev/null | xxd -p"
            f"   # expect {want_le}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
