#!/usr/bin/env python3
"""
Find patch offsets in firmware binaries using capstone disassembly.
Based on the writeup's patching strategy for vphone600ap virtual iPhone.

Targets:
1. AVPBooter - image4_validate_property_callback -> return 0
2. iBSS     - image4_validate_property_callback -> return 0
3. iBEC     - image4_validate_property_callback -> return 0, boot-args
4. LLB      - image4_validate_property_callback -> return 0, boot-args, SSV bypass
5. TXM      - trustcache bypass
6. kernel   - SSV bypass
"""

import struct
import sys
from capstone import *

RAW_DIR = "raw"

def load_binary(name):
    path = f"{RAW_DIR}/{name}"
    with open(path, "rb") as f:
        return bytearray(f.read())

def find_bytes(data, pattern):
    """Find all occurrences of a byte pattern."""
    results = []
    start = 0
    while True:
        idx = data.find(pattern, start)
        if idx == -1:
            break
        results.append(idx)
        start = idx + 1
    return results

def find_string(data, s):
    """Find string in binary."""
    return find_bytes(data, s.encode('utf-8') + b'\x00')

def disasm_at(data, offset, count=20, base=0):
    """Disassemble instructions at offset."""
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    code = bytes(data[offset:offset+count*4])
    insns = list(md.disasm(code, base + offset))
    return insns

def find_image4_validate_callback(data, name):
    """
    Find image4_validate_property_callback by searching for 0x4447 ("DG")
    immediate value, which is an IMG4 tag used in the validation function.
    The writeup says: search for "0x4447" in IDA, find the function,
    patch its epilogue to return 0.
    """
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True

    # Search for MOV/CMP with 0x4447 immediate
    # 0x4447 = 17479
    candidates = []
    code = bytes(data)

    for insn in md.disasm(code, 0):
        if insn.mnemonic in ('mov', 'movz', 'cmp') and len(insn.operands) >= 2:
            op = insn.operands[-1]
            if op.type == 2 and op.imm == 0x4447:  # CS_OP_IMM = 2
                candidates.append(insn.address)
        elif insn.mnemonic == 'movk' and len(insn.operands) >= 2:
            op = insn.operands[-1]
            if op.type == 2 and op.imm == 0x4447:
                candidates.append(insn.address)

    if not candidates:
        # Also try searching for the raw bytes of CMP Wn, #0x4447
        # CMP W0, #0x4447 would be encoded differently
        # Let's search for the 0x4447 pattern in different encodings
        # MOV W0, #0x4447 = 0x528088E0
        mov_patterns = [
            struct.pack('<I', 0x528088E0),  # mov w0, #0x4447
            struct.pack('<I', 0x528088E1),  # mov w1, #0x4447
            struct.pack('<I', 0x528088E2),  # mov w2, #0x4447
            struct.pack('<I', 0x528088E8),  # mov w8, #0x4447
            struct.pack('<I', 0x528088E9),  # mov w9, #0x4447
        ]
        # CMP Wn, #0x111, LSL#4  (0x4447 = 0x111 << 4 + 0x7... nope)
        # Actually: CMP Wn, #imm12 only supports 12-bit. 0x4447 > 0xFFF
        # So it must be loaded with MOV first, then CMP
        for pat in mov_patterns:
            offsets = find_bytes(data, pat)
            for o in offsets:
                candidates.append(o)

    print(f"\n{'='*60}")
    print(f"[{name}] Searching for image4_validate_property_callback")
    print(f"  Found {len(candidates)} references to 0x4447:")

    for addr in candidates:
        print(f"  0x{addr:X}")
        # Show context
        insns = disasm_at(data, max(0, addr - 8*4), 20)
        for i in insns:
            marker = " <<<" if i.address == addr else ""
            print(f"    0x{i.address:06X}: {i.mnemonic} {i.op_str}{marker}")

    return candidates

def find_boot_args_string(data, name):
    """Find boot-args related strings."""
    patterns = [b"serial=", b"debug=", b"boot-args", b"-v "]
    print(f"\n{'='*60}")
    print(f"[{name}] Searching for boot-args strings:")
    for pat in patterns:
        offsets = find_bytes(data, pat)
        for o in offsets:
            # Read surrounding string
            start = o
            while start > 0 and data[start-1] != 0:
                start -= 1
            end = o
            while end < len(data) and data[end] != 0:
                end += 1
            s = data[start:end].decode('ascii', errors='replace')
            print(f"  0x{o:X}: \"{s}\" (string start: 0x{start:X})")

def find_ssv_bypass_strings(data, name):
    """Find SSV-related panic strings for kernel/LLB patching."""
    patterns = [
        b"root snapshot",
        b"seal is broken",
        b"rootvp not authenticated",
        b"Failed to find the root snapshot",
        b"root volume seal",
    ]
    print(f"\n{'='*60}")
    print(f"[{name}] Searching for SSV bypass targets:")
    for pat in patterns:
        offsets = find_bytes(data, pat)
        for o in offsets:
            start = o
            while start > 0 and data[start-1] != 0:
                start -= 1
            end = o + len(pat) + 100
            while end < len(data) and data[end] != 0:
                end += 1
            s = data[start:min(end, start+120)].decode('ascii', errors='replace')
            print(f"  0x{o:X}: \"{s}\"")

def find_trustcache_bypass(data, name):
    """
    Find TXM trustcache bypass points.
    Writeup: "CodeSignature: selector: 24 | 0xA8 | 0x30 | 1"
    Patches at specific offsets relative to base 0xFFFFFFF017004000
    """
    print(f"\n{'='*60}")
    print(f"[{name}] TXM Analysis:")
    print(f"  Binary size: {len(data)} bytes (0x{len(data):X})")

    # Search for CodeSignature related strings
    patterns = [b"CodeSignature", b"selector:", b"trustcache"]
    for pat in patterns:
        offsets = find_bytes(data, pat)
        for o in offsets:
            start = o
            while start > 0 and data[start-1] >= 0x20:
                start -= 1
            end = o
            while end < len(data) and data[end] >= 0x20:
                end += 1
            s = data[start:end].decode('ascii', errors='replace')
            print(f"  0x{o:X}: \"{s}\"")

def analyze_all():
    print("=" * 60)
    print("Firmware Patch Offset Finder")
    print("=" * 60)

    # 1. AVPBooter
    try:
        avp = load_binary("AVPBooter.raw")
        find_image4_validate_callback(avp, "AVPBooter")
    except Exception as e:
        print(f"AVPBooter error: {e}")

    # 2. iBSS
    try:
        ibss = load_binary("iBSS.raw")
        find_image4_validate_callback(ibss, "iBSS")
    except Exception as e:
        print(f"iBSS error: {e}")

    # 3. iBEC
    try:
        ibec = load_binary("iBEC.raw")
        find_image4_validate_callback(ibec, "iBEC")
        find_boot_args_string(ibec, "iBEC")
    except Exception as e:
        print(f"iBEC error: {e}")

    # 4. LLB
    try:
        llb = load_binary("LLB.raw")
        find_image4_validate_callback(llb, "LLB")
        find_boot_args_string(llb, "LLB")
        find_ssv_bypass_strings(llb, "LLB")
    except Exception as e:
        print(f"LLB error: {e}")

    # 5. TXM
    try:
        txm = load_binary("txm.raw")
        find_trustcache_bypass(txm, "TXM")
    except Exception as e:
        print(f"TXM error: {e}")

    # 6. Kernel
    try:
        kern = load_binary("kcache.raw")
        find_ssv_bypass_strings(kern, "kernel")
    except Exception as e:
        print(f"kernel error: {e}")

if __name__ == "__main__":
    analyze_all()
