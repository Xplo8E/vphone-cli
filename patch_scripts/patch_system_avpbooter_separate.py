#!/usr/bin/env python3
"""
Copy + patch the *system* AVPBooter into a separate directory.

This script intentionally does NOT modify:
  - ~/.tart
  - ~/Desktop

It reads:
  /System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPBooter.vresearch1.bin

And writes:
  <out-dir>/AVPBooter.vresearch1.system.original.bin
  <out-dir>/AVPBooter.vresearch1.system.patched.bin
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import struct
import sys
from pathlib import Path


DEFAULT_SRC = Path(
    "/System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPBooter.vresearch1.bin"
)
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "avpbooter_system_artifacts"

# original-research/super-tart-vphone/CFW/patch_avpbooter.py values
PATCHES = [
    (0x02ADC, 0x540005E1, 0xD503201F, "B.NE -> NOP"),
    (0x02AE0, 0xAA1403E0, 0xD2800000, "MOV X0,X20 -> MOV X0,#0"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def u32_le(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch system AVPBooter into a separate directory")
    parser.add_argument("--src", default=str(DEFAULT_SRC), help="Source AVPBooter path")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory")
    args = parser.parse_args()

    src = Path(args.src).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    orig_out = out_dir / "AVPBooter.vresearch1.system.original.bin"
    patched_out = out_dir / "AVPBooter.vresearch1.system.patched.bin"

    if not src.exists():
        print(f"ERROR: source not found: {src}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    # copyfile avoids preserving source flags/metadata that can fail on system files.
    shutil.copyfile(src, orig_out)

    data = bytearray(orig_out.read_bytes())
    print("Applying patches:")
    for off, expected, patched, desc in PATCHES:
        current = u32_le(data, off)
        if current == expected:
            struct.pack_into("<I", data, off, patched)
            print(f"  0x{off:05X}: 0x{current:08X} -> 0x{patched:08X}  ({desc})")
        elif current == patched:
            print(f"  0x{off:05X}: already patched 0x{current:08X} ({desc})")
        else:
            print(
                f"ERROR: unexpected value at 0x{off:05X}: 0x{current:08X} "
                f"(expected 0x{expected:08X} or 0x{patched:08X})"
            )
            return 1

    patched_out.write_bytes(data)

    print("\nOutput:")
    print(f"  source : {src}")
    print(f"  original copy: {orig_out} ({orig_out.stat().st_size} bytes)")
    print(f"  patched copy : {patched_out} ({patched_out.stat().st_size} bytes)")
    print(f"  sha256(original copy): {sha256(orig_out)}")
    print(f"  sha256(patched copy) : {sha256(patched_out)}")

    verify = patched_out.read_bytes()
    print("\nPatched values:")
    for off, _expected, patched, desc in PATCHES:
        current = u32_le(verify, off)
        status = "OK" if current == patched else "BAD"
        print(f"  [{status}] 0x{off:05X} = 0x{current:08X} ({desc})")

    print("\nNote: ~/.tart and ~/Desktop were not modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
