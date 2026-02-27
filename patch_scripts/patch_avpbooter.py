#!/usr/bin/env python3
"""
Patch AVPBooter.vresearch1.bin -> AVPBooter.vmapple2.bin

Patches image4_validate_property_callback epilogue to always return 0,
bypassing IMG4 signature verification during iBSS/iBEC restore.

Patch 1: 0x02ADC  -> NOP          (skip stack-cookie abort branch)
Patch 2: 0x02AE0  -> MOV X0, #0   (force return 0 = success)
"""

import struct, sys, os

SRC = "/System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPBooter.vresearch1.bin"
DST = os.path.normpath(os.path.join(os.path.dirname(__file__), "../.tart/vms/vphone/AVPBooter.vmapple2.bin"))

PATCHES = [
    (0x02ADC, 0xD503201F, "NOP (skip stack-cookie abort)"),
    (0x02AE0, 0xD2800000, "MOV X0, #0 (force return 0)"),
]

data = bytearray(open(SRC, "rb").read())

print("Current values at patch offsets:")
for off, new_val, desc in PATCHES:
    current = struct.unpack("<I", data[off:off+4])[0]
    print(f"  0x{off:05X}: 0x{current:08X}  ->  0x{new_val:08X}  ({desc})")
    struct.pack_into("<I", data, off, new_val)

open(DST, "wb").write(data)
print(f"\nWritten to {DST}")

# Show all diffs from original
orig = open(SRC, "rb").read()
diffs = [(i, struct.unpack("<I", orig[i:i+4])[0], struct.unpack("<I", bytes(data)[i:i+4])[0])
         for i in range(0, len(orig)-3, 4) if orig[i:i+4] != bytes(data)[i:i+4]]
print(f"Total diffs from original: {len(diffs)}")
for off, ov, pv in diffs:
    print(f"  0x{off:05X}: 0x{ov:08X} -> 0x{pv:08X}")
