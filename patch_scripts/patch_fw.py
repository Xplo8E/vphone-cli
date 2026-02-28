#!/usr/bin/env python3
"""
patch_fw.py - Patch vphone600ap firmware binaries for virtual iPhone boot.

Patches applied:
  1. iBSS      - image4_validate_property_callback → return 0 (bypass signature verification)
  2. iBEC      - image4_validate_property_callback → return 0 + boot-args override
  3. LLB       - image4_validate_property_callback → return 0 + boot-args + SSV/rootfs bypass
  4. TXM       - trustcache bypass (default) + optional jailbreak/dev-mode helper patches
  5. kernel    - SSV (Signed System Volume) bypass (prevent boot panics)
  6. AVPBooter - image4_validate_property_callback → return 0 (VM bootrom sig bypass)

Based on cloudOS 23B85 (PCC) + iOS 26.1 23B85 (iPhone17,3) mixed firmware.
Offsets verified against image4_validate_property_callback found at:
  iBSS VA 0x70075D10 (file 0x9D10), LLB VA 0x700760D8 (file 0xA0D8)

AVPBooter is a raw binary (no IM4P container) copied from the system
Virtualization.framework and patched to bin/AVPBooter.vresearch1.bin.

NOTE: SIP/AMFI must be disabled on the host Mac because super-tart uses
  private Virtualization.framework APIs (_VZMacHardwareModelDescriptor,
  _setROMURL, _VZSEPCoprocessorConfiguration, _VZUSBTouchScreenConfiguration,
  etc.) which require the restricted com.apple.private.virtualization entitlement.

Usage:
  python3 patch_fw.py [--firmware-dir PATH] [--dry-run] [--verify-only]
"""

import argparse
import hashlib
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

# =============================================================================
# Paths
# =============================================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
WORK_ROOT = REPO_ROOT / "_work"
BIN_DIR = REPO_ROOT / "bin"

def _find_pyimg4():
    """Locate pyimg4: $PYIMG4 > PATH > .venv/bin > ~/Library/Python/*/bin."""
    if os.environ.get("PYIMG4"):
        return os.environ["PYIMG4"]
    found = shutil.which("pyimg4")
    if found:
        return found
    venv_path = str(REPO_ROOT / ".venv" / "bin" / "pyimg4")
    if os.path.exists(venv_path):
        return venv_path
    # Legacy fallback
    for p in sorted(Path.home().glob("Library/Python/*/bin/pyimg4"), reverse=True):
        if p.exists():
            return str(p)
    return "pyimg4"  # hope it's on PATH at runtime

PYIMG4 = _find_pyimg4()
IMG4TOOL = os.environ.get("IMG4TOOL", str(BIN_DIR / "img4tool"))

# AVPBooter system source path
AVPBOOTER_SRC = Path("/System/Library/Frameworks/Virtualization.framework"
                     "/Resources/AVPBooter.vresearch1.bin")

# =============================================================================
# ARM64 instruction encodings
# =============================================================================
NOP        = 0xD503201F  # NOP
MOV_X0_0   = 0xD2800000  # MOV X0, #0

# =============================================================================
# Patch definitions
# =============================================================================
# Each patch is: (offset, value, description)
# value is either an int (4-byte ARM64 instruction) or bytes/str (string patch)

IBSS_PATCHES = [
    # image4_validate_property_callback epilogue: B.NE → NOP, MOV X0, X22 → MOV X0, #0
    (0x9D10, NOP,      "image4_validate_property_callback: NOP B.NE (was 0x540009E1)"),
    (0x9D14, MOV_X0_0, "image4_validate_property_callback: MOV X0, #0 (was MOV X0, X22)"),
    # Preserve APNonce across stage transitions (matches original research flow).
    (0x1B544, 0x1400000E, "nonce: skip generate_nonce path to keep APNonce stable"),
    # Serial console logging: identify boot stage on serial output
    (0x84349, b"Loaded iBSS", "serial log: stage identifier string 1"),
    (0x843F4, b"Loaded iBSS", "serial log: stage identifier string 2"),
]

IBEC_PATCHES = [
    # image4_validate_property_callback
    (0x9D10, NOP,      "image4_validate_property_callback: NOP B.NE (was 0x540009E1)"),
    (0x9D14, MOV_X0_0, "image4_validate_property_callback: MOV X0, #0 (was MOV X0, X22)"),
    # boot-args: redirect ADRP+ADD to point to custom string at 0x24070
    (0x122D4, 0xD0000082, "boot-args: ADRP X2, #0x12000 → page of 0x24070"),
    (0x122D8, 0x9101C042, "boot-args: ADD X2, X2, #0x70 → offset to 0x24070"),
    (0x24070, b"serial=3 -v debug=0x2014e %s\x00", "boot-args: custom string"),
    # Serial console logging: identify boot stage on serial output
    (0x84349, b"Loaded iBEC", "serial log: stage identifier string 1"),
    (0x843F4, b"Loaded iBEC", "serial log: stage identifier string 2"),
]

LLB_PATCHES = [
    # image4_validate_property_callback
    (0xA0D8, NOP,      "image4_validate_property_callback: NOP B.NE (was 0x54000A61)"),
    (0xA0DC, MOV_X0_0, "image4_validate_property_callback: MOV X0, #0 (was MOV X0, X22)"),
    # boot-args: redirect ADRP+ADD to custom string at 0x24990
    (0x12888, 0xD0000082, "boot-args: ADRP X2, #0x12000 → page of 0x24990"),
    (0x1288C, 0x91264042, "boot-args: ADD X2, X2, #0x990 → offset to 0x24990"),
    (0x24990, b"serial=3 -v debug=0x2014e %s\x00", "boot-args: custom string"),
    # Serial console logging: identify boot stage on serial output
    (0x86809, b"Loaded LLB", "serial log: stage identifier string 1"),
    (0x868B4, b"Loaded LLB", "serial log: stage identifier string 2"),
    # SSV / rootfs bypass - allow loading edited rootfs (needed for snaputil -n)
    (0x2BFE8, 0x1400000B, "SSV: unconditional branch (was CBZ W0)"),
    (0x2BCA0, NOP,        "SSV: NOP conditional branch (was B.CC)"),
    (0x2C03C, 0x17FFFF6A, "SSV: unconditional branch (was CBZ W0)"),
    (0x2FCEC, NOP,        "SSV: NOP conditional branch (was CBZ X8)"),
    (0x2FEE8, 0x14000009, "SSV: unconditional branch (was CBZ W0)"),
    # bypass panic in unknown check
    (0x1AEE4, NOP,        "NOP panic branch (was CBNZ W0)"),
]

TXM_PATCHES_BASE = [
    # Trustcache bypass: replace BL to validation functions with MOV X0, #0
    # Allows running binaries not registered in trustcache
    # Trace: sub_FFFFFFF01702B018 → sub_FFFFFFF0170306E4 → ... → sub_FFFFFFF01702EC70
    (0x2C1F8, MOV_X0_0, "trustcache: MOV X0, #0 (was BL sub_FFFFFFF01702EC70)"),
    (0x2BEF4, MOV_X0_0, "trustcache: MOV X0, #0 (was BL validation func)"),
    (0x2C060, MOV_X0_0, "trustcache: MOV X0, #0 (was BL validation func)"),
    # Policy-bit relaxations.
    (0x20004, 0xD2800008, "policy: mov x8, #0 (device_type=0 -> txm_cs_disable=1)"),
    (0x20340, 0x92800000, "policy: mov x0, #-1 (enable all bits)"),
    (0x20348, 0x7904B280, "policy: set skipTrustEvaluation_allowAnySignature"),
    (0x20350, 0x39096A80, "policy: set allowUnrestrictedLocalSigning"),
    (0x2035C, 0x39097A80, "policy: set relaxProfileTrust"),
    (0x20360, 0x79058A80, "policy: set allowModifiedCodeAndUnrestrictDebug"),
]

TXM_PATCHES_JB_EXTRA = [
    # Jailbreak helper patches from original research flow:
    # TXM [Error]: CodeSignature: selector: 24 | 0xA1 | 0x30 | 1
    # Without these, boot loops with repeated TXM CodeSignature errors
    (0x313EC, NOP, "codesig: NOP selector 24|0xA1 check (prevents boot loop)"),
    (0x313F4, NOP, "codesig: NOP selector 24|0xA1 check (prevents boot loop)"),
    # Always make true for get-task-allow / make possible lldb debugging
    # TXM [Error]: selector: 41 | 29
    (0x1F5D4, 0xD2800020, "jailbreak: mov x0, #1 (selector 41|29)"),
    # TXM [Error]: selector: 42 | 29
    (0x2717C, 0x1400D88E, "jailbreak: branch to helper shellcode path (selector 42|29)"),
    # 0x5D3B8 shellcode block (FFFFFFF0170613B8)
    (0x5D3B4, NOP,        "jailbreak shellcode stub: NOP"),
    (0x5D3B8, 0xD2800020, "jailbreak shellcode: mov x0, #1"),
    (0x5D3BC, 0x3900C280, "jailbreak shellcode: strb w0, [x20, #0x30]"),
    (0x5D3C0, 0xAA1403E0, "jailbreak shellcode: mov x0, x20"),
    (0x5D3C4, 0x17FF276F, "jailbreak shellcode: b #-0x36244"),
    # always make true for com.apple.private.cs.debugger
    # TXM [Error]: selector: 42 | 37
    (0x1F3B8, 0x52800020, "jailbreak: mov w0, #1 (com.apple.private.cs.debugger)"),
    # always enable developer mode
    (0x1FA58, NOP,        "jailbreak: always enable developer mode"),
]

# Default TXM mode is minimal for stability.
TXM_PATCHES = TXM_PATCHES_BASE

KERNEL_PATCHES_BASE = [
    # SSV (Signed System Volume) bypass - NOP branches that lead to panics
    (0x2476964, NOP, "_apfs_vfsop_mount: NOP (prevent 'Failed to find root snapshot' panic)"),
    (0x23CFDE4, NOP, "_authapfs_seal_is_broken: NOP (prevent 'root volume seal broken' panic)"),
    (0x0F6D960, NOP, "_bsd_init: NOP (prevent 'rootvp not authenticated' panic)"),
    # Launch constraint compatibility for normal boot:
    # __Z30_proc_check_launch_constraintsP4prociiPvmP22launch_constraint_dataPPcPm
    (0x163863C, 0x52800000, "_proc_check_launch_constraints: MOV W0, #0"),
    (0x1638640, 0xD65F03C0, "_proc_check_launch_constraints: RET"),
]

# Jailbreak kernel patches from original research flow.
# Enable with --kernel-jb-extra. These provide AMFI/sandbox/codesign bypass,
# tfp0, kcall10 syscall primitive, MACF hook table overrides, and shellcode caves.
# All offsets for cloudOS/iOS 23B85 kernelcache.research.vphone600.
KERNEL_PATCHES_JB_EXTRA = [
    # === AMFI Trustcache bypass ===
    # AMFIIsCDHashInTrustCache: always return true
    (0x1633880, 0xD2800020, "AMFIIsCDHashInTrustCache: MOV X0, #1"),
    (0x1633884, 0xB4000042, "AMFIIsCDHashInTrustCache: CBZ X2, #8"),
    (0x1633888, 0xF9000040, "AMFIIsCDHashInTrustCache: STR X0, [X2]"),
    (0x163388C, 0xD65F03C0, "AMFIIsCDHashInTrustCache: RET"),

    # === _cred_label_update_execve shellcode at 0xAB1720 ===
    # Sets CS_PLATFORM_BINARY | CS_VALID | CS_ADHOC | CS_GET_TASK_ALLOW | CS_INSTALLER,
    # clears CS_HARD | CS_KILL | CS_CHECK_EXPIRATION etc.
    (0xAB1720,    0xF94007E0, "cred_label_execve shellcode: LDR X0, [SP,#8]"),
    (0xAB1724,    0xB9400001, "cred_label_execve shellcode: LDR W1, [X0]"),
    (0xAB1728,    0x32060021, "cred_label_execve shellcode: ORR W1, W1, #0x4000000 (CS_PLATFORM_BINARY)"),
    (0xAB172C,    0x32000C21, "cred_label_execve shellcode: ORR W1, W1, #0xF (CS_VALID|ADHOC|GET_TASK_ALLOW|INSTALLER)"),
    (0xAB1730,    0x12126421, "cred_label_execve shellcode: AND W1, W1, #0xFFFFC0FF (clear CS_HARD etc)"),
    (0xAB1734,    0xB9000001, "cred_label_execve shellcode: STR W1, [X0]"),
    (0xAB1738,    0xAA1F03E0, "cred_label_execve shellcode: MOV X0, XZR"),
    (0xAB173C,    0xD65F0FFF, "cred_label_execve shellcode: RETAB"),
    # Trampoline: redirect _cred_label_update_execve to shellcode
    (0x163C11C,   0x17D1D581, "_cred_label_update_execve trampoline: B #-0xB8A9FC (-> 0xAB1720)"),

    # === postValidation bypass ===
    (0x16405AC,   0x6B00001F, "postValidation: CMP W0, W0 (force zero flag)"),

    # === Dyld policy bypass ===
    (0x16410BC,   0x52800020, "_check_dyld_policy_internal: MOV W0, #1"),
    (0x16410C8,   0x52800020, "_check_dyld_policy_internal: MOV W0, #1 (second)"),

    # === APFS graft / mount / upgrade ===
    (0x242011C,   0x52800000, "_apfs_graft: MOV W0, #0"),
    (0x2475044,   0xEB00001F, "_apfs_vfsop_mount: CMP X0, X0 (force equal)"),
    (0x2476C00,   0x52800000, "_apfs_mount_upgrade_checks: MOV W0, #0"),
    (0x248C800,   0x52800000, "_handle_fsioc_graft: MOV W0, #0"),

    # === _syscallmask_apply_to_proc shellcode at 0xAB1740 ===
    # Bitmask data (10 words of 0xFFFFFFFF = allow all syscalls)
    (0xAB1740,    0xFFFFFFFF, "syscallmask bitmask [0]"),
    (0xAB1744,    0xFFFFFFFF, "syscallmask bitmask [1]"),
    (0xAB1748,    0xFFFFFFFF, "syscallmask bitmask [2]"),
    (0xAB174C,    0xFFFFFFFF, "syscallmask bitmask [3]"),
    (0xAB1750,    0xFFFFFFFF, "syscallmask bitmask [4]"),
    (0xAB1754,    0xFFFFFFFF, "syscallmask bitmask [5]"),
    (0xAB1758,    0xFFFFFFFF, "syscallmask bitmask [6]"),
    (0xAB175C,    0xFFFFFFFF, "syscallmask bitmask [7]"),
    (0xAB1760,    0xFFFFFFFF, "syscallmask bitmask [8]"),
    (0xAB1764,    0xFFFFFFFF, "syscallmask bitmask [9]"),
    # Shellcode
    (0xAB1768,    0xB4000362, "syscallmask shellcode: CBZ X2, #0x6C"),
    (0xAB176C,    0xD10103FF, "syscallmask shellcode: SUB SP, SP, #0x40"),
    (0xAB1770,    0xA90153F3, "syscallmask shellcode: STP X19, X20, [SP,#0x10]"),
    (0xAB1774,    0xA9025BF5, "syscallmask shellcode: STP X21, X22, [SP,#0x20]"),
    (0xAB1778,    0xA9037BFD, "syscallmask shellcode: STP X29, X30, [SP,#0x30]"),
    (0xAB177C,    0xAA0003F3, "syscallmask shellcode: MOV X19, X0"),
    (0xAB1780,    0xAA0103F4, "syscallmask shellcode: MOV X20, X1"),
    (0xAB1784,    0xAA0203F5, "syscallmask shellcode: MOV X21, X2"),
    (0xAB1788,    0xAA0303F6, "syscallmask shellcode: MOV X22, X3"),
    (0xAB178C,    0xD2800108, "syscallmask shellcode: MOV X8, #8"),
    (0xAB1790,    0xAA1103E0, "syscallmask shellcode: MOV X0, X17"),
    (0xAB1794,    0xAA1503E1, "syscallmask shellcode: MOV X1, X21"),
    (0xAB1798,    0xD2800002, "syscallmask shellcode: MOV X2, #0"),
    (0xAB179C,    0x10FFFD23, "syscallmask shellcode: ADR X3, #-0x5C (-> bitmask at 0xAB1740)"),
    (0xAB17A0,    0x9AC80AC4, "syscallmask shellcode: UDIV X4, X22, X8"),
    (0xAB17A4,    0x9B08D88A, "syscallmask shellcode: MSUB X10, X4, X8, X22"),
    (0xAB17A8,    0xB400004A, "syscallmask shellcode: CBZ X10, #8"),
    (0xAB17AC,    0x91000484, "syscallmask shellcode: ADD X4, X4, #1"),
    (0xAB17B0,    0x940302AA, "syscallmask shellcode: BL #0xC0AA8 (_zalloc_ro_mut)"),
    (0xAB17B4,    0xAA1303E0, "syscallmask shellcode: MOV X0, X19"),
    (0xAB17B8,    0xAA1403E1, "syscallmask shellcode: MOV X1, X20"),
    (0xAB17BC,    0xAA1503E2, "syscallmask shellcode: MOV X2, X21"),
    (0xAB17C0,    0xAA1603E3, "syscallmask shellcode: MOV X3, X22"),
    (0xAB17C4,    0xA94153F3, "syscallmask shellcode: LDP X19, X20, [SP,#0x10]"),
    (0xAB17C8,    0xA9425BF5, "syscallmask shellcode: LDP X21, X22, [SP,#0x20]"),
    (0xAB17CC,    0xA9437BFD, "syscallmask shellcode: LDP X29, X30, [SP,#0x30]"),
    (0xAB17D0,    0x910103FF, "syscallmask shellcode: ADD SP, SP, #0x40"),
    (0xAB17D4,    0x14144693, "syscallmask shellcode: B #0x511A4C (_proc_set_syscall_filter_mask)"),
    # Trampolines
    (0x2395530,   0xAA0003F1, "syscallmask trampoline: MOV X17, X0 (save zone)"),
    (0x2395584,   0x179C7079, "syscallmask trampoline: B #-0x18E3E1C (-> 0xAB1740 shellcode)"),

    # === _hook_cred_label_update_execve shellcode at 0xAB17D8 ===
    # Looks up vnode uid/gid and sets CS_INSTALLER flag
    (0xAB17D8,    0xD503201F, "hook_cred_label shellcode: NOP"),
    (0xAB17DC,    0xB4000543, "hook_cred_label shellcode: CBZ X3, #0xA8"),
    (0xAB17E0,    0xD11003FF, "hook_cred_label shellcode: SUB SP, SP, #0x400"),
    (0xAB17E4,    0xA9007BFD, "hook_cred_label shellcode: STP X29, X30, [SP]"),
    (0xAB17E8,    0xA90107E0, "hook_cred_label shellcode: STP X0, X1, [SP,#16]"),
    (0xAB17EC,    0xA9020FE2, "hook_cred_label shellcode: STP X2, X3, [SP,#32]"),
    (0xAB17F0,    0xA90317E4, "hook_cred_label shellcode: STP X4, X5, [SP,#48]"),
    (0xAB17F4,    0xA9041FE6, "hook_cred_label shellcode: STP X6, X7, [SP,#64]"),
    (0xAB17F8,    0xD503201F, "hook_cred_label shellcode: NOP"),
    (0xAB17FC,    0x940851AC, "hook_cred_label shellcode: BL #0x2146B0 (_vfs_context_current)"),
    (0xAB1800,    0xAA0003E2, "hook_cred_label shellcode: MOV X2, X0"),
    (0xAB1804,    0xF94017E0, "hook_cred_label shellcode: LDR X0, [SP,#0x28]"),
    (0xAB1808,    0x910203E1, "hook_cred_label shellcode: ADD X1, SP, #0x80"),
    (0xAB180C,    0x52807008, "hook_cred_label shellcode: MOV W8, #0x380"),
    (0xAB1810,    0xA900203F, "hook_cred_label shellcode: STP XZR, X8, [X1]"),
    (0xAB1814,    0xA9017C3F, "hook_cred_label shellcode: STP XZR, XZR, [X1,#0x10]"),
    (0xAB1818,    0xD503201F, "hook_cred_label shellcode: NOP"),
    (0xAB181C,    0x94085E69, "hook_cred_label shellcode: BL #0x2179A4 (_vnode_getattr)"),
    (0xAB1820,    0xB5000260, "hook_cred_label shellcode: CBNZ X0, +skip"),
    (0xAB1824,    0x52800002, "hook_cred_label shellcode: MOV W2, #0"),
    (0xAB1828,    0xB940CFE8, "hook_cred_label shellcode: LDR W8, [SP,#0xCC]"),
    (0xAB182C,    0x365800A8, "hook_cred_label shellcode: TBZ W8, #0xB, +skip"),
    (0xAB1830,    0xB940C7E8, "hook_cred_label shellcode: LDR W8, [SP,#0xC4]"),
    (0xAB1834,    0xF9400FE0, "hook_cred_label shellcode: LDR X0, [SP,#0x18]"),
    (0xAB1838,    0xB9001808, "hook_cred_label shellcode: STR W8, [X0,#0x18] (cr_uid)"),
    (0xAB183C,    0x52800022, "hook_cred_label shellcode: MOV W2, #1"),
    (0xAB1840,    0xB940CFE8, "hook_cred_label shellcode: LDR W8, [SP,#0xCC]"),
    (0xAB1844,    0x365000A8, "hook_cred_label shellcode: TBZ W8, #0xA, +skip"),
    (0xAB1848,    0x52800022, "hook_cred_label shellcode: MOV W2, #1"),
    (0xAB184C,    0xB940CBE8, "hook_cred_label shellcode: LDR W8, [SP,#0xC8]"),
    (0xAB1850,    0xF9400FE0, "hook_cred_label shellcode: LDR X0, [SP,#0x18]"),
    (0xAB1854,    0xB9002808, "hook_cred_label shellcode: STR W8, [X0,#0x28] (cr_gid)"),
    (0xAB1858,    0x340000A2, "hook_cred_label shellcode: CBZ W2, +skip"),
    (0xAB185C,    0xF94013E0, "hook_cred_label shellcode: LDR X0, [SP,#0x20]"),
    (0xAB1860,    0xB9445408, "hook_cred_label shellcode: LDR W8, [X0,#0x454] (p_csflags)"),
    (0xAB1864,    0x32180108, "hook_cred_label shellcode: ORR W8, W8, #0x100 (CS_INSTALLER)"),
    (0xAB1868,    0xB9045408, "hook_cred_label shellcode: STR W8, [X0,#0x454]"),
    (0xAB186C,    0xA94107E0, "hook_cred_label shellcode: LDP X0, X1, [SP,#0x10]"),
    (0xAB1870,    0xA9420FE2, "hook_cred_label shellcode: LDP X2, X3, [SP,#0x20]"),
    (0xAB1874,    0xA94317E4, "hook_cred_label shellcode: LDP X4, X5, [SP,#0x30]"),
    (0xAB1878,    0xA9441FE6, "hook_cred_label shellcode: LDP X6, X7, [SP,#0x40]"),
    (0xAB187C,    0xA9407BFD, "hook_cred_label shellcode: LDP X29, X30, [SP]"),
    (0xAB1880,    0x911003FF, "hook_cred_label shellcode: ADD SP, SP, #0x400"),
    (0xAB1884,    0xD503201F, "hook_cred_label shellcode: NOP"),
    (0xAB1888,    0x146420B7, "hook_cred_label shellcode: B #0x19082DC (_hook_cred_label_update_execve)"),
    (0xAB188C,    0xD503201F, "hook_cred_label shellcode: NOP (padding)"),
    # Hook table pointer: _hook_cred_label_update_execve entry -> shellcode
    (0xA54518,    0x00AB17D8, "MACF hook table: _hook_cred_label_update_execve -> shellcode"),

    # === MACF hook table overrides ===
    # All point to 0x23B73BC which is a MOV X0, #0; RET gadget in kernel
    (0xA545A8,    0x023B73BC, "MACF: _hook_file_check_mmap -> ret0"),
    (0xA54740,    0x023B73BC, "MACF: _hook_mount_check_mount -> ret0"),
    (0xA54748,    0x023B73BC, "MACF: _hook_mount_check_remount -> ret0"),
    (0xA54760,    0x023B73BC, "MACF: _hook_mount_check_umount -> ret0"),
    (0xA54848,    0x023B73BC, "MACF: _hook_vnode_check_rename -> ret0"),
    (0xA54C30,    0x023B73BC, "MACF: _hook_vnode_check_getattr -> ret0"),
    (0xA54C50,    0x023B73BC, "MACF: _hook_proc_check_get_cs_info -> ret0"),
    (0xA54C58,    0x023B73BC, "MACF: _hook_proc_check_set_cs_info -> ret0"),
    (0xA54C68,    0x023B73BC, "MACF: _hook_proc_check_set_cs_info (2) -> ret0"),
    (0xA54C78,    0x023B73BC, "MACF: _hook_vnode_check_chroot -> ret0"),
    (0xA54C80,    0x023B73BC, "MACF: _hook_vnode_check_create -> ret0"),
    (0xA54C88,    0x023B73BC, "MACF: _hook_vnode_check_deleteextattr -> ret0"),
    (0xA54C90,    0x023B73BC, "MACF: _hook_vnode_check_exchangedata -> ret0"),
    (0xA54C98,    0x023B73BC, "MACF: _hook_vnode_check_exec -> ret0"),
    (0xA54CA0,    0x023B73BC, "MACF: _hook_vnode_check_getattrlist -> ret0"),
    (0xA54CA8,    0x023B73BC, "MACF: _hook_vnode_check_getextattr -> ret0"),
    (0xA54CB0,    0x023B73BC, "MACF: _hook_vnode_check_ioctl -> ret0"),
    (0xA54CC8,    0x023B73BC, "MACF: _hook_vnode_check_link -> ret0"),
    (0xA54CD0,    0x023B73BC, "MACF: _hook_vnode_check_listextattr -> ret0"),
    (0xA54CE0,    0x023B73BC, "MACF: _hook_vnode_check_open -> ret0"),
    (0xA54CF8,    0x023B73BC, "MACF: _hook_vnode_check_readlink -> ret0"),
    (0xA54D20,    0x023B73BC, "MACF: _hook_vnode_check_setattrlist -> ret0"),
    (0xA54D28,    0x023B73BC, "MACF: _hook_vnode_check_setextattr -> ret0"),
    (0xA54D30,    0x023B73BC, "MACF: _hook_vnode_check_setflags -> ret0"),
    (0xA54D38,    0x023B73BC, "MACF: _hook_vnode_check_setmode -> ret0"),
    (0xA54D40,    0x023B73BC, "MACF: _hook_vnode_check_setowner -> ret0"),
    (0xA54D48,    0x023B73BC, "MACF: _hook_vnode_check_setutimes -> ret0"),
    (0xA54D50,    0x023B73BC, "MACF: _hook_vnode_check_stat -> ret0"),
    (0xA54D58,    0x023B73BC, "MACF: _hook_vnode_check_truncate -> ret0"),
    (0xA54D60,    0x023B73BC, "MACF: _hook_vnode_check_unlink -> ret0"),
    (0xA54E68,    0x023B73BC, "MACF: _hook_vnode_check_fsgetpath -> ret0"),

    # === Task / process security ===
    (0xB01194,    0xEB1F03FF, "_task_conversion_eval_internal: CMP XZR, XZR (always equal)"),
    (0x1063148,   0xD2800000, "_proc_security_policy: MOV X0, #0"),
    (0x106314C,   0xD65F03C0, "_proc_security_policy: RET"),
    (0x1060A90,   0xD503201F, "_proc_pidinfo: NOP pid 0 check"),
    (0x1060A98,   0xD503201F, "_proc_pidinfo: NOP pid 0 check (2)"),

    # === VM / memory ===
    (0xB02E94,    0x14000015, "_convert_port_to_map_with_flavor: B #0x54 (skip kernel map panic)"),
    (0xBA9E1C,    0xD503201F, "_vm_fault_enter_prepare: NOP"),
    (0xBC024C,    0x1400000A, "_vm_map_protect: B #0x28 (skip protection check)"),

    # === Mount / unmount MAC bypasses ===
    (0xCA5D54,    0xD503201F, "___mac_mount: NOP MAC check"),
    (0xCA5D88,    0xAA1F03E8, "___mac_mount: MOV X8, XZR (clear error)"),
    (0xCA8134,    0xD503201F, "_dounmount: NOP"),

    # === BSD init additional ===
    (0xF6D95C,    0xD2800000, "_bsd_init: MOV X0, #0 (additional rootvp panic prevent)"),

    # === Persona / task-for-pid ===
    (0xFA7024,    0xD503201F, "_spawn_validate_persona: NOP"),
    (0xFA702C,    0xD503201F, "_spawn_validate_persona: NOP (2)"),
    (0xFC383C,    0xD503201F, "_task_for_pid: NOP check"),

    # === Dylinker / shared region / NVRAM ===
    (0x1052A28,   0x14000011, "_load_dylinker: B #0x44 (skip check)"),
    (0x10729CC,   0xEB00001F, "_shared_region_map_and_slide_setup: CMP X0, X0 (force equal)"),
    (0x1234034,   0xD503201F, "verifyPermission(IONVRAMOperation): NOP"),

    # === IOSecureBSDRoot ===
    (0x128B598,   0x14000009, "_IOSecureBSDRoot: B #0x24 (skip check)"),

    # === kcall10 syscall primitive (replaces SYS_kas_info 439) ===
    # Sysent table entries
    (0x73E180,    0x00AB1890, "sysent[439].sy_call -> kcall10 shellcode"),
    (0x73E188,    0x00C66D28, "sysent[439].sy_arg_munge32 -> _munge_wwwwwwww"),
    (0x73E190,    0x00000007, "sysent[439].sy_return_type = SYSCALL_RET_UINT64_T"),
    (0x73E194,    0x00200008, "sysent[439].sy_narg=8, sy_arg_bytes=0x20"),
    # kcall10 shellcode at 0xAB1890
    (0xAB1890,    0xF94023EA, "kcall10: LDR X10, [SP, #0x40]"),
    (0xAB1894,    0xA9400540, "kcall10: LDP X0, X1, [X10, #0]"),
    (0xAB1898,    0xA9410D42, "kcall10: LDP X2, X3, [X10, #0x10]"),
    (0xAB189C,    0xA9421544, "kcall10: LDP X4, X5, [X10, #0x20]"),
    (0xAB18A0,    0xA9431D46, "kcall10: LDP X6, X7, [X10, #0x30]"),
    (0xAB18A4,    0xA9442548, "kcall10: LDP X8, X9, [X10, #0x40]"),
    (0xAB18A8,    0xF940294A, "kcall10: LDR X10, [X10, #0x50]"),
    (0xAB18AC,    0xAA0003F0, "kcall10: MOV X16, X0 (target fn)"),
    (0xAB18B0,    0xAA0103E0, "kcall10: MOV X0, X1"),
    (0xAB18B4,    0xAA0203E1, "kcall10: MOV X1, X2"),
    (0xAB18B8,    0xAA0303E2, "kcall10: MOV X2, X3"),
    (0xAB18BC,    0xAA0403E3, "kcall10: MOV X3, X4"),
    (0xAB18C0,    0xAA0503E4, "kcall10: MOV X4, X5"),
    (0xAB18C4,    0xAA0603E5, "kcall10: MOV X5, X6"),
    (0xAB18C8,    0xAA0703E6, "kcall10: MOV X6, X7"),
    (0xAB18CC,    0xAA0803E7, "kcall10: MOV X7, X8"),
    (0xAB18D0,    0xAA0903E8, "kcall10: MOV X8, X9"),
    (0xAB18D4,    0xAA0A03E9, "kcall10: MOV X9, X10"),
    (0xAB18D8,    0xA9BF7BFD, "kcall10: STP X29, X30, [SP, #-0x10]!"),
    (0xAB18DC,    0xD63F0200, "kcall10: BLR X16 (call target)"),
    (0xAB18E0,    0xA8C17BFD, "kcall10: LDP X29, X30, [SP], #0x10"),
    (0xAB18E4,    0xF94023EB, "kcall10: LDR X11, [SP, #0x40]"),
    (0xAB18E8,    0xD503201F, "kcall10: NOP"),
    (0xAB18EC,    0xA9000560, "kcall10: STP X0, X1, [X11, #0]"),
    (0xAB18F0,    0xA9010D62, "kcall10: STP X2, X3, [X11, #0x10]"),
    (0xAB18F4,    0xA9021564, "kcall10: STP X4, X5, [X11, #0x20]"),
    (0xAB18F8,    0xA9031D66, "kcall10: STP X6, X7, [X11, #0x30]"),
    (0xAB18FC,    0xA9042568, "kcall10: STP X8, X9, [X11, #0x40]"),
    (0xAB1900,    0xF900296A, "kcall10: STR X10, [X11, #0x50]"),
    (0xAB1904,    0xD2800000, "kcall10: MOV X0, #0 (return success)"),
    (0xAB1908,    0xD65F03C0, "kcall10: RET"),
    (0xAB190C,    0xD503201F, "kcall10: NOP (padding)"),

    # === Thread crash prevention ===
    # Prevents EXC_GUARD crashes (GUARD_TYPE_MACH_PORT)
    (0x67EB50,    0x00000000, "_thid_should_crash: set to 0"),
]

# Default kernel mode is minimal for stability.
KERNEL_PATCHES = KERNEL_PATCHES_BASE

# AVPBooter system variant (233,368 bytes) from Virtualization.framework.
# Two patches to image4_validate_property_callback:
#   0x2ADC: NOP the stack-cookie abort branch (B.NE → NOP)
#   0x2AE0: Force return 0 (MOV X0, X20 → MOV X0, #0)
#
# NOTE: A larger Desktop/VM variant (251,856 bytes) exists with offsets 0x2C1C/0x2C20.
# This repo uses the system variant only.
AVPBOOTER_PATCHES = [
    (0x2ADC, NOP,      "image4_validate_property_callback: NOP (skip stack-cookie abort)"),
    (0x2AE0, MOV_X0_0, "image4_validate_property_callback: MOV X0, #0 (was MOV X0, X20)"),
]

# =============================================================================
# Firmware file paths (relative to firmware restore directory)
# =============================================================================
FIRMWARE_FILES = {
    "iBSS": {
        "im4p": "Firmware/dfu/iBSS.vresearch101.RELEASE.im4p",
        "fourcc": "ibss",
        "patches": IBSS_PATCHES,
        "tool": "img4tool",  # bootloaders use img4tool for repack
    },
    "iBEC": {
        "im4p": "Firmware/dfu/iBEC.vresearch101.RELEASE.im4p",
        "fourcc": "ibec",
        "patches": IBEC_PATCHES,
        "tool": "img4tool",
    },
    "LLB": {
        "im4p": "Firmware/all_flash/LLB.vresearch101.RESEARCH_RELEASE.im4p",
        "fourcc": "illb",
        "patches": LLB_PATCHES,
        "tool": "img4tool",
    },
    "TXM": {
        "im4p": "Firmware/txm.iphoneos.research.im4p",
        "fourcc": "trxm",
        "patches": TXM_PATCHES,
        "tool": "pyimg4",  # TXM uses pyimg4 + PAYP preservation
        "lzfse": True,
        "preserve_payp": True,
    },
    "kernel": {
        "im4p": "kernelcache.research.vphone600",
        "fourcc": "krnl",
        "patches": KERNEL_PATCHES_BASE,  # overridden in main() if --kernel-jb-extra
        "tool": "pyimg4",  # kernel uses pyimg4 + PAYP preservation
        "lzfse": True,
        "preserve_payp": True,
    },
    "AVPBooter": {
        "source": str(AVPBOOTER_SRC),
        "output": str(BIN_DIR / "AVPBooter.vresearch1.bin"),
        "patches": AVPBOOTER_PATCHES,
        "raw": True,  # no IM4P container — patch raw binary directly
    },
}

# =============================================================================
# Expected original values at patch offsets (for verification)
# =============================================================================
EXPECTED_ORIGINALS = {
    "iBSS": {
        0x9D10: 0x540009E1,  # B.NE
        0x9D14: 0xAA1603E0,  # MOV X0, X22
        0x1B544: 0x370801C8,  # TBNZ W8, #1, ...
    },
    "iBEC": {
        0x9D10: 0x540009E1,
        0x9D14: 0xAA1603E0,
        0x122D4: 0xF0000382,  # ADRP X2, ...
        0x122D8: 0x9121A842,  # ADD X2, X2, #0x86A
    },
    "LLB": {
        0xA0D8: 0x54000A61,  # B.NE
        0xA0DC: 0xAA1603E0,  # MOV X0, X22
        0x12888: 0xB00003A2,  # ADRP X2
        0x1288C: 0x913ED442,  # ADD X2, X2, ...
        0x2BFE8: 0x34000160,  # CBZ W0
        0x2BCA0: 0x54000AE2,  # B.CC
        0x2C03C: 0x34FFED40,  # CBZ W0
        0x2FCEC: 0xB4000348,  # CBZ X8
        0x2FEE8: 0x34000120,  # CBZ W0
        0x1AEE4: 0x350004C0,  # CBNZ W0
    },
    "TXM": {
        0x2C1F8: 0x97FFFA9E,  # BL
        0x2BEF4: 0x97FFFB5F,  # BL
        0x2C060: 0x97FFFB04,  # BL
    },
    "kernel": {
        0x2476964: 0x37281048,  # TBNZ
        0x23CFDE4: 0x37700160,  # TBNZ
        0x0F6D960: 0x35001340,  # CBNZ
        # NOTE: expected originals for 0x163863C/0x1638640 vary across builds.
        # Kept out of strict expected checks, but patched unconditionally.
    },
    "AVPBooter": {
        0x2ADC: 0x540005E1,  # B.NE (stack-cookie abort branch)
        0x2AE0: 0xAA1403E0,  # MOV X0, X20
    },
}


def read_u32(data, offset):
    """Read a little-endian 32-bit value."""
    return struct.unpack('<I', data[offset:offset+4])[0]


def write_u32(data, offset, value):
    """Write a little-endian 32-bit value."""
    struct.pack_into('<I', data, offset, value)


def sha256(data):
    """Compute SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def run_cmd(cmd, check=True):
    """Run a shell command and return output."""
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        sys.exit(1)
    return result


def verify_offsets(data, name):
    """Verify that original values at patch offsets match expectations."""
    expected = EXPECTED_ORIGINALS.get(name, {})
    ok = True
    for offset, expected_val in expected.items():
        actual = read_u32(data, offset)
        if actual == expected_val:
            print(f"    0x{offset:X}: 0x{actual:08X} (expected) OK")
        elif actual in (NOP, MOV_X0_0):
            print(f"    0x{offset:X}: 0x{actual:08X} (already patched)")
        else:
            print(f"    0x{offset:X}: 0x{actual:08X} != expected 0x{expected_val:08X} MISMATCH")
            ok = False
    return ok


def apply_patches(data, patches, name):
    """Apply patches to raw binary data. Returns patched bytearray."""
    data = bytearray(data)
    count = 0
    for offset, value, desc in patches:
        if isinstance(value, int):
            # 4-byte instruction patch
            old = read_u32(data, offset)
            write_u32(data, offset, value)
            new = read_u32(data, offset)
            print(f"    0x{offset:X}: 0x{old:08X} → 0x{new:08X}  ({desc})")
        elif isinstance(value, (bytes, str)):
            # String/data patch
            if isinstance(value, str):
                value = value.encode('utf-8') + b'\x00'
            old_bytes = bytes(data[offset:offset+len(value)])
            data[offset:offset+len(value)] = value
            print(f"    0x{offset:X}: {len(value)} bytes  ({desc})")
        count += 1
    print(f"  Applied {count} patches to {name}")
    return bytes(data)


def extract_raw(im4p_path, raw_path):
    """Extract raw binary from IM4P container."""
    run_cmd(f'{PYIMG4} im4p extract -i "{im4p_path}" -o "{raw_path}"')


def repack_img4tool(raw_path, im4p_path, fourcc):
    """Repack raw binary to IM4P using img4tool (for bootloaders)."""
    run_cmd(f'{IMG4TOOL} -c "{im4p_path}" -t {fourcc} "{raw_path}"')


def repack_pyimg4(raw_path, im4p_path, fourcc, lzfse=False):
    """Repack raw binary to IM4P using pyimg4 (for kernel/TXM)."""
    compress = " --lzfse" if lzfse else ""
    run_cmd(f'{PYIMG4} im4p create -i "{raw_path}" -o "{im4p_path}" -f {fourcc}{compress}')


def preserve_payp(original_im4p_path, new_im4p_path):
    """
    Preserve PAYP structure from original IM4P.
    The PAYP (payload properties) section must be appended to the new IM4P
    and the DER length field updated accordingly.
    """
    original_data = Path(original_im4p_path).read_bytes()
    payp_offset = original_data.rfind(b'PAYP')
    if payp_offset == -1:
        print("  WARNING: Could not find PAYP structure in original IM4P!")
        return False

    # PAYP data starts 10 bytes before the 'PAYP' tag (DER header)
    payp_data = original_data[payp_offset - 10:]
    payp_sz = len(payp_data)
    print(f"  PAYP structure: {payp_sz} bytes (offset {payp_offset - 10} in original)")

    # Append PAYP to new IM4P
    with open(new_im4p_path, 'ab') as f:
        f.write(payp_data)

    # Update DER sequence length (bytes 2-5 of the IM4P file)
    im4p_data = bytearray(Path(new_im4p_path).read_bytes())
    old_len = int.from_bytes(im4p_data[2:5], 'big')
    new_len = old_len + payp_sz
    im4p_data[2:5] = new_len.to_bytes(3, 'big')
    Path(new_im4p_path).write_bytes(bytes(im4p_data))

    print(f"  Updated DER length: {old_len} → {new_len} (+{payp_sz})")
    return True


def process_raw_component(name, config, dry_run=False, verify_only=False):
    """Process a raw binary component (no IM4P container). Used for AVPBooter."""
    print(f"\n{'='*60}")
    print(f"[{name}]")
    print(f"{'='*60}")

    src_path = config["source"]
    out_path = config["output"]
    patches = config["patches"]

    # Check source exists
    if not os.path.exists(src_path):
        print(f"  ERROR: {src_path} not found!")
        return False

    # Read source binary
    raw_data = Path(src_path).read_bytes()
    print(f"  Source: {src_path}")
    print(f"  Binary: {len(raw_data)} bytes, SHA256: {sha256(raw_data)[:16]}...")

    # Verify original values
    print(f"  Verifying original instruction values:")
    if not verify_offsets(raw_data, name):
        print(f"  WARNING: Some offsets don't match expected values!")
        print(f"  This binary may be a different build. Proceed with caution.")

    if verify_only:
        return True

    # Apply patches
    print(f"  Applying patches:")
    patched_data = apply_patches(raw_data, patches, name)
    print(f"  Patched SHA256: {sha256(patched_data)[:16]}...")

    if dry_run:
        print(f"  DRY RUN: would write patched binary to {out_path}")
        return True

    # Write patched binary
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    Path(out_path).write_bytes(patched_data)
    print(f"  Output: {out_path} ({len(patched_data)} bytes)")
    print(f"  [{name}] DONE")
    return True


def process_component(name, config, fw_dir, tmp_dir, dry_run=False, verify_only=False):
    """Process a single firmware component: extract, verify, patch, repack."""
    print(f"\n{'='*60}")
    print(f"[{name}]")
    print(f"{'='*60}")

    im4p_rel = config["im4p"]
    im4p_path = os.path.join(fw_dir, im4p_rel)
    bak_path = im4p_path + ".bak"
    raw_path = os.path.join(tmp_dir, f"{name}.raw")
    fourcc = config["fourcc"]
    patches = config["patches"]

    # Check IM4P exists
    if not os.path.exists(im4p_path):
        print(f"  ERROR: {im4p_path} not found!")
        return False

    # Create backup
    if not os.path.exists(bak_path):
        print(f"  Creating backup: {os.path.basename(bak_path)}")
        if not dry_run:
            shutil.copy2(im4p_path, bak_path)
    else:
        print(f"  Backup already exists: {os.path.basename(bak_path)}")

    # Extract raw from backup (always from original)
    print(f"  Extracting raw binary from backup...")
    if not dry_run:
        extract_raw(bak_path, raw_path)

    # Read raw data
    if dry_run:
        if os.path.exists(raw_path):
            raw_data = Path(raw_path).read_bytes()
        else:
            print(f"  DRY RUN: would extract and patch {name}")
            return True
    else:
        raw_data = Path(raw_path).read_bytes()

    print(f"  Raw binary: {len(raw_data)} bytes, SHA256: {sha256(raw_data)[:16]}...")

    # Verify original values
    print(f"  Verifying original instruction values:")
    if not verify_offsets(raw_data, name):
        print(f"  WARNING: Some offsets don't match expected values!")
        print(f"  This firmware may be a different build. Proceed with caution.")

    if verify_only:
        return True

    # Apply patches
    print(f"  Applying patches:")
    patched_data = apply_patches(raw_data, patches, name)
    print(f"  Patched SHA256: {sha256(patched_data)[:16]}...")

    if dry_run:
        print(f"  DRY RUN: would write patched binary and repack")
        return True

    # Write patched raw
    Path(raw_path).write_bytes(patched_data)

    # Repack to IM4P
    print(f"  Repacking to IM4P (fourcc={fourcc})...")
    tool = config.get("tool", "img4tool")

    if tool == "img4tool":
        repack_img4tool(raw_path, im4p_path, fourcc)
    elif tool == "pyimg4":
        lzfse = config.get("lzfse", False)
        repack_pyimg4(raw_path, im4p_path, fourcc, lzfse=lzfse)

    # Preserve PAYP if needed
    if config.get("preserve_payp", False):
        print(f"  Preserving PAYP structure...")
        if not preserve_payp(bak_path, im4p_path):
            print(f"  ERROR: PAYP preservation failed!")
            return False

    # Verify output
    output_size = os.path.getsize(im4p_path)
    backup_size = os.path.getsize(bak_path)
    print(f"  Output: {output_size} bytes (backup: {backup_size} bytes)")
    print(f"  [{name}] DONE")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Patch vphone600ap firmware binaries for virtual iPhone boot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Components patched:
  iBSS      - Signature verification bypass (image4_validate_property_callback → return 0)
  iBEC      - Signature bypass + boot-args (serial=3 -v debug=0x2014e)
  LLB       - Signature bypass + boot-args + SSV/rootfs bypass
  TXM       - Trustcache bypass (default); add --txm-jb-extra for original-research extras
  kernel    - SSV bypass (default); add --kernel-jb-extra for full jailbreak patches
  AVPBooter - VM bootrom signature bypass (raw binary, no IM4P)

All offsets are for cloudOS/iOS 23B85 build.
""")
    parser.add_argument("--firmware-dir", "-d",
                        default=None,
                        help="Path to firmware restore directory (default: auto-detect)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Show what would be done without modifying files")
    parser.add_argument("--verify-only", "-v", action="store_true",
                        help="Only verify offsets match expected values, don't patch")
    parser.add_argument("--component", "-c", nargs="+",
                        choices=list(FIRMWARE_FILES.keys()) + ["all"],
                        default=["all"],
                        help="Components to patch (default: all)")
    parser.add_argument("--txm-jb-extra", action="store_true",
                        help="Enable extra TXM jailbreak/dev-mode patches from original-research (experimental)")
    parser.add_argument("--kernel-jb-extra", action="store_true",
                        help="Enable full kernel jailbreak patches (AMFI/sandbox/codesign/tfp0/kcall10/MACF hooks)")
    args = parser.parse_args()

    # Configure TXM patch mode.
    if args.txm_jb_extra:
        FIRMWARE_FILES["TXM"]["patches"] = TXM_PATCHES_BASE + TXM_PATCHES_JB_EXTRA
        EXPECTED_ORIGINALS["TXM"].update({
            0x1F5D4: 0x97FFFD17,  # BL
            0x2717C: 0xAA1403E0,  # MOV X0, X20
            0x1F3B8: 0x97FFFD9E,  # BL
            0x1FA58: 0x370000A9,  # TBNZ
        })
        print("TXM mode: jb-extra enabled (experimental)")
    else:
        FIRMWARE_FILES["TXM"]["patches"] = TXM_PATCHES_BASE
        print("TXM mode: minimal (trustcache-only)")

    # Configure kernel patch mode.
    if args.kernel_jb_extra:
        FIRMWARE_FILES["kernel"]["patches"] = KERNEL_PATCHES_BASE + KERNEL_PATCHES_JB_EXTRA
        print(f"Kernel mode: jb-extra enabled ({len(KERNEL_PATCHES_JB_EXTRA)} additional patches)")
    else:
        FIRMWARE_FILES["kernel"]["patches"] = KERNEL_PATCHES_BASE
        print(f"Kernel mode: minimal ({len(KERNEL_PATCHES_BASE)} patches, SSV + launch constraints only)")

    # Determine which components to patch
    components = list(FIRMWARE_FILES.keys()) if "all" in args.component else args.component

    # Separate raw components (AVPBooter) from IM4P components
    raw_components = [c for c in components if FIRMWARE_FILES[c].get("raw")]
    im4p_components = [c for c in components if not FIRMWARE_FILES[c].get("raw")]

    # Find firmware directory (only needed for IM4P components)
    fw_dir = None
    tmp_dir = None
    if im4p_components:
        if args.firmware_dir:
            fw_dir = args.firmware_dir
        else:
            # Auto-detect relative to script location
            candidates = [
                WORK_ROOT / "firmwares" / "firmware_patched" / "iPhone17,3_26.1_23B85_Restore",
                REPO_ROOT / "firmwares" / "firmware_patched" / "iPhone17,3_26.1_23B85_Restore",
                REPO_ROOT / "_work" / "iPhone17,3_26.1_23B85_Restore",
                Path.cwd() / "_work" / "firmwares" / "firmware_patched" / "iPhone17,3_26.1_23B85_Restore",
                Path.cwd() / "firmwares" / "firmware_patched" / "iPhone17,3_26.1_23B85_Restore",
                Path.cwd() / "iPhone17,3_26.1_23B85_Restore",
            ]
            for c in candidates:
                if c.exists():
                    fw_dir = str(c)
                    break
            if not fw_dir:
                print("ERROR: Could not find firmware directory. Use --firmware-dir to specify.")
                sys.exit(1)

        print(f"Firmware directory: {fw_dir}")

        # Check tools
        for tool_name, tool_path in [("pyimg4", PYIMG4), ("img4tool", IMG4TOOL)]:
            if not tool_path or not os.path.exists(tool_path):
                print(f"ERROR: {tool_name} not found at {tool_path}")
                print(f"Set {tool_name.upper()} environment variable or install it.")
                sys.exit(1)
            print(f"  {tool_name}: {tool_path}")

        # Create temp directory for raw binaries
        tmp_dir = os.path.join(os.path.dirname(fw_dir), "patch_tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        print(f"  Temp dir: {tmp_dir}")

    if args.dry_run:
        print("\n*** DRY RUN - no files will be modified ***")
    if args.verify_only:
        print("\n*** VERIFY ONLY - checking offsets ***")

    # Process each component
    results = {}
    for name in im4p_components:
        config = FIRMWARE_FILES[name]
        ok = process_component(name, config, fw_dir, tmp_dir,
                               dry_run=args.dry_run,
                               verify_only=args.verify_only)
        results[name] = ok

    for name in raw_components:
        config = FIRMWARE_FILES[name]
        ok = process_raw_component(name, config,
                                   dry_run=args.dry_run,
                                   verify_only=args.verify_only)
        results[name] = ok

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for name, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {name:10s}: {status}")

    if all(results.values()):
        print("\nAll components processed successfully.")
        if not args.dry_run and not args.verify_only:
            if fw_dir:
                print(f"Patched firmware is in: {fw_dir}")
                print(f"Backups saved with .bak extension.")
            for name in raw_components:
                print(f"  {name}: {FIRMWARE_FILES[name]['output']}")
    else:
        print("\nSome components failed. Check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
