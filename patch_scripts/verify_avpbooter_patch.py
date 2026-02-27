#!/usr/bin/env python3
"""
Verify AVPBooter patch state for one or more files.

Reports:
  - size
  - sha256
  - values at 0x02ADC and 0x02AE0
  - classification:
      system_unpatched / system_patched / unknown_variant
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path


OFFSET_1 = 0x02ADC
OFFSET_2 = 0x02AE0

SYSTEM_UNPATCHED = (0x540005E1, 0xAA1403E0)
SYSTEM_PATCHED = (0xD503201F, 0xD2800000)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def classify(v1: int, v2: int) -> str:
    pair = (v1, v2)
    if pair == SYSTEM_UNPATCHED:
        return "system_unpatched"
    if pair == SYSTEM_PATCHED:
        return "system_patched"
    return "unknown_variant"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify AVPBooter patch bytes")
    parser.add_argument("files", nargs="+", help="AVPBooter file paths")
    args = parser.parse_args()

    rc = 0
    for raw in args.files:
        p = Path(raw).expanduser().resolve()
        print(f"\n== {p} ==")
        if not p.exists():
            print("  ERROR: file not found")
            rc = 1
            continue

        data = p.read_bytes()
        if len(data) < OFFSET_2 + 4:
            print(f"  ERROR: file too small ({len(data)} bytes)")
            rc = 1
            continue

        v1 = read_u32(data, OFFSET_1)
        v2 = read_u32(data, OFFSET_2)
        mode = classify(v1, v2)

        print(f"  size   : {len(data)}")
        print(f"  sha256 : {sha256(p)}")
        print(f"  0x{OFFSET_1:05X}: 0x{v1:08X}")
        print(f"  0x{OFFSET_2:05X}: 0x{v2:08X}")
        print(f"  classify: {mode}")

    return rc


if __name__ == "__main__":
    sys.exit(main())

