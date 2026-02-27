#!/usr/bin/env python3
"""
Find image4_validate_property_callback in bootloaders.
The function compares property tags like 0x4447 ("DG"), 0x444D ("DM"), etc.
We search for the MOV instruction that loads 0x4447.

ARM64 encoding for MOV Wn, #0x4447:
  MOVZ Wn, #0x4447 = 0x5288_88E0 | Rd
  where 0x4447 << 5 = 0x88E0, opcode = 0x52800000
  So: 0x528088E0 for W0, 0x528088E1 for W1, etc.

Also check CMP: CMP can't encode 0x4447 directly (>12 bits),
so it's likely a MOV + CMP sequence.
"""

import struct
import os
from capstone import *

RAW_DIR = "raw"

def load_binary(name):
    with open(f"{RAW_DIR}/{name}", "rb") as f:
        return bytearray(f.read())

def find_all(data, pattern):
    results = []
    start = 0
    while True:
        idx = data.find(pattern, start)
        if idx == -1:
            break
        results.append(idx)
        start = idx + 1
    return results

def search_mov_0x4447(data, name):
    """Search for any MOV Wn/Xn, #0x4447 encoding."""
    print(f"\n{'='*60}")
    print(f"[{name}] Searching for MOV with 0x4447 immediate")

    # MOVZ Wn, #0x4447: 0x52800000 | (0x4447 << 5) | Rd = 0x528088E0 | Rd
    base_encoding = 0x528088E0

    for rd in range(31):
        enc = struct.pack('<I', base_encoding | rd)
        offsets = find_all(data, enc)
        for o in offsets:
            print(f"  0x{o:04X}: MOVZ W{rd}, #0x4447")
            show_context(data, o, name)

    # Also search for MOVZ Xn, #0x4447: 0xD2800000 | (0x4447 << 5) | Rd
    base_encoding_x = 0xD28088E0
    for rd in range(31):
        enc = struct.pack('<I', base_encoding_x | rd)
        offsets = find_all(data, enc)
        for o in offsets:
            print(f"  0x{o:04X}: MOVZ X{rd}, #0x4447")
            show_context(data, o, name)

    # Also search for raw bytes "DG" (0x44, 0x47) in string tables
    dg_offsets = find_all(data, b'DGST')
    if dg_offsets:
        print(f"  Found {len(dg_offsets)} 'DGST' string references")
        for o in dg_offsets[:3]:
            print(f"    0x{o:04X}")

    # Search for string "img4"
    img4_offsets = find_all(data, b'IMG4')
    if img4_offsets:
        print(f"  Found {len(img4_offsets)} 'IMG4' references")
        for o in img4_offsets[:5]:
            print(f"    0x{o:04X}")

def show_context(data, offset, name):
    """Show disassembly context around an offset."""
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True

    # Go back 10 instructions, forward 15
    start = max(0, offset - 40)
    # Align to 4 bytes
    start = start & ~3
    end = min(len(data), offset + 60)

    code = bytes(data[start:end])

    # Find function prologue (STP X29, X30) going backwards
    func_start = None
    for back in range(offset, max(0, offset - 0x200), -4):
        insn_bytes = struct.unpack('<I', data[back:back+4])[0]
        # STP X29, X30, [SP, #imm]! = 0xA9xx7BFD
        if (insn_bytes & 0xFFE07FFF) == 0xA9007BFD:
            func_start = back
            break

    if func_start:
        print(f"    Likely function start: 0x{func_start:04X}")

    # Find function epilogue (RET) going forward
    func_end = None
    for fwd in range(offset, min(len(data), offset + 0x200), 4):
        insn_bytes = struct.unpack('<I', data[fwd:fwd+4])[0]
        if insn_bytes == 0xD65F03C0:  # RET
            func_end = fwd
            break

    if func_end:
        print(f"    Likely function end (RET): 0x{func_end:04X}")

    print(f"    --- Disassembly around 0x{offset:04X} ---")
    for insn in md.disasm(code, start):
        marker = " <<<" if insn.address == offset else ""
        if insn.address == func_end:
            marker += " [RET]"
        print(f"      0x{insn.address:06X}: {insn.mnemonic:8s} {insn.op_str}{marker}")

def analyze_bootloader_epilogue(data, name, mov_offset):
    """
    Analyze the function containing the MOV 0x4447 instruction.
    Find where to patch: the function's return to always return 0.

    Pattern from writeup:
      NOP the instruction before MOV X0, #0
      Then MOV X0, #0
    Which makes the function return 0 (success).
    """
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)

    # Find the function boundary
    # Search backwards for STP x29, x30 (function prologue)
    func_start = None
    for back in range(mov_offset, max(0, mov_offset - 0x500), -4):
        insn_bytes = struct.unpack('<I', data[back:back+4])[0]
        if (insn_bytes & 0xFFE07FFF) == 0xA9007BFD:
            func_start = back
            break

    if not func_start:
        print(f"  Could not find function prologue for {name}")
        return None

    # Disassemble the whole function to find all RET paths
    func_code = bytes(data[func_start:func_start+0x800])

    # Find the first RET after our MOV instruction
    ret_offset = None
    for fwd in range(mov_offset, min(len(data), mov_offset + 0x200), 4):
        insn_bytes = struct.unpack('<I', data[fwd:fwd+4])[0]
        if insn_bytes == 0xD65F03C0:  # RET
            ret_offset = fwd
            break

    if ret_offset:
        # The patch should go just before RET:
        # We need the LDP instruction that restores x29, x30
        # Typical epilogue: LDP x29, x30, [sp], #imm ; RET
        ldp_offset = ret_offset - 4
        insn_bytes = struct.unpack('<I', data[ldp_offset:ldp_offset+4])[0]

        print(f"\n  [{name}] Function: 0x{func_start:04X} - 0x{ret_offset:04X}")
        print(f"  Suggested patch location (before RET epilogue):")

        # Show last few instructions before RET
        ctx_start = max(func_start, ret_offset - 24)
        ctx_code = bytes(data[ctx_start:ret_offset+4])
        for insn in md.disasm(ctx_code, ctx_start):
            print(f"    0x{insn.address:06X}: {insn.mnemonic:8s} {insn.op_str}")

        return func_start, ret_offset

    return None

# Main
for name in ["AVPBooter.raw", "iBSS.raw", "iBEC.raw", "LLB.raw"]:
    data = load_binary(name)
    search_mov_0x4447(data, name.replace('.raw', ''))
