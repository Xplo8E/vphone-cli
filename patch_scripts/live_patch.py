#!/usr/bin/env python3
"""
live_patch.py - Apply kernel + TXM patches via SSH ramdisk without re-restore.

Connects to a booted SSH ramdisk, grabs the APTicket from preboot,
patches kernel and TXM locally, signs with the APTicket, uploads the
patched IMG4 files back to preboot, and halts the device.

This avoids the full re-restore cycle (DETAILED_GUIDE Section 15) when
iterating on patch offsets. After halt, do a normal boot to pick up changes.

Prerequisites:
  - SSH ramdisk booted (boot_rd.sh)
  - iproxy running: iproxy 2222 22
  - Tools: pyimg4, sshpass
  - Patched firmware directory with .bak files (from patch_fw.py)

Usage:
  python3 live_patch.py [--firmware-dir PATH] [--dry-run]
  python3 live_patch.py --kernel-only    # skip TXM
  python3 live_patch.py --txm-only       # skip kernel
  python3 live_patch.py --no-halt        # don't halt after upload
"""

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

# =============================================================================
# Paths
# =============================================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
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
    for p in sorted(Path.home().glob("Library/Python/*/bin/pyimg4"), reverse=True):
        if p.exists():
            return str(p)
    return "pyimg4"

PYIMG4 = _find_pyimg4()
SSHPASS = os.environ.get("SSHPASS", str(BIN_DIR / "sshpass")
          if (BIN_DIR / "sshpass").exists() else shutil.which("sshpass") or "sshpass")

# SSH connection settings
SSH_HOST = "root@127.0.0.1"
SSH_PORT = os.environ.get("SSH_PORT", "2222")
SSH_PASS = os.environ.get("SSH_PASS", "alpine")

# Default firmware directory
DEFAULT_FW_DIR = (REPO_ROOT / "firmwares" / "firmware_patched"
                  / "iPhone17,3_26.1_23B85_Restore")

# =============================================================================
# Import patch lists from patch_fw.py
# =============================================================================
# We import the patch lists so live_patch always uses the same offsets as
# patch_fw.py. This avoids duplicating hundreds of patch tuples.
sys.path.insert(0, str(SCRIPT_DIR))
from patch_fw import (
    KERNEL_PATCHES_BASE,
    KERNEL_PATCHES_JB_EXTRA,
    TXM_PATCHES_BASE,
    TXM_PATCHES_JB_EXTRA,
)


# =============================================================================
# SSH helpers (mirrors setup_rootfs.py patterns)
# =============================================================================
def ssh_opts():
    return (
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        "-o ConnectTimeout=10 "
        "-o ServerAliveInterval=5 "
        "-o ServerAliveCountMax=60"
    )


def run_cmd(cmd, check=True, capture=False):
    """Run a shell command."""
    print(f"  $ {cmd}")
    if capture:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    else:
        result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        if capture:
            print(f"  STDERR: {result.stderr.strip()}")
        print(f"  ERROR: command failed with exit code {result.returncode}")
        sys.exit(1)
    return result


def remote_cmd(cmd, check=True):
    """Run a command on the device via SSH."""
    full_cmd = (
        f'{SSHPASS} -p "{SSH_PASS}" ssh {ssh_opts()} '
        f'-p {SSH_PORT} {SSH_HOST} "{cmd}"'
    )
    result = run_cmd(full_cmd, check=check, capture=True)
    if result.stdout:
        print(f"    {result.stdout.strip()}")
    return result


def scp_from_device(remote_path, local_path):
    """SCP a file from the device to the host."""
    cmd = (
        f'{SSHPASS} -p "{SSH_PASS}" scp -q -O {ssh_opts()} '
        f'-P {SSH_PORT} "{SSH_HOST}:{remote_path}" "{local_path}"'
    )
    run_cmd(cmd)


def scp_to_device(local_path, remote_path):
    """SCP a file from the host to the device."""
    cmd = (
        f'{SSHPASS} -p "{SSH_PASS}" scp -q -O {ssh_opts()} '
        f'-P {SSH_PORT} "{local_path}" "{SSH_HOST}:{remote_path}"'
    )
    run_cmd(cmd)


def check_remote_file(remote_path):
    """Check if a file exists on the device."""
    result = remote_cmd(f'/bin/test -f {remote_path}', check=False)
    return result.returncode == 0


# =============================================================================
# Patch application (reuses patch_fw.py logic)
# =============================================================================
def apply_patches(raw_data, patches, name):
    """Apply a list of (offset, value, description) patches to raw binary data."""
    data = bytearray(raw_data)
    for offset, value, desc in patches:
        if isinstance(value, int):
            patch_bytes = struct.pack('<I', value)
        elif isinstance(value, str):
            patch_bytes = value.encode()
        elif isinstance(value, bytes):
            patch_bytes = value
        else:
            raise ValueError(f"Unknown patch type for {desc}: {type(value)}")

        if offset + len(patch_bytes) > len(data):
            print(f"    SKIP: {desc} — offset 0x{offset:X} beyond binary ({len(data)} bytes)")
            continue

        data[offset:offset + len(patch_bytes)] = patch_bytes
    print(f"    Applied {len(patches)} patches to {name}")
    return bytes(data)


# =============================================================================
# PAYP preservation (mirrors prepare_ramdisk.py / patch_fw.py)
# =============================================================================
def preserve_payp(source_im4p, target_im4p):
    """Append PAYP structure from source IM4P and fix DER length."""
    src = Path(source_im4p).read_bytes()
    payp_offset = src.rfind(b"PAYP")
    if payp_offset == -1:
        print(f"    WARNING: PAYP not found in {source_im4p}")
        return False

    payp_blob = src[payp_offset - 10:]
    payp_sz = len(payp_blob)
    with open(target_im4p, "ab") as f:
        f.write(payp_blob)

    data = bytearray(Path(target_im4p).read_bytes())
    old_len = int.from_bytes(data[2:5], "big")
    data[2:5] = (old_len + payp_sz).to_bytes(3, "big")
    Path(target_im4p).write_bytes(bytes(data))
    print(f"    PAYP preserved: {payp_sz} bytes")
    return True


# =============================================================================
# Main workflow
# =============================================================================
def get_boot_manifest_hash():
    """Get the bootManifestHash directory name from preboot."""
    result = remote_cmd("/bin/ls /mnt5", check=True)
    entries = result.stdout.strip().split()
    # bootManifestHash is a 96-character hex string
    for entry in entries:
        if len(entry) == 96:
            return entry
    print("  ERROR: Could not find bootManifestHash in /mnt5")
    print(f"  Contents: {entries}")
    sys.exit(1)


def patch_and_sign_kernel(fw_dir, work_dir, apticket_path, kernel_jb_extra):
    """Patch kernel, repack as IMG4, sign with APTicket."""
    print("\n" + "=" * 60)
    print("[Kernel] Patching and signing")
    print("=" * 60)

    kernel_im4p = os.path.join(fw_dir, "kernelcache.research.vphone600")
    bak_path = kernel_im4p + ".bak"
    payp_source = bak_path if os.path.exists(bak_path) else kernel_im4p

    raw_path = os.path.join(work_dir, "kcache.raw")
    im4p_path = os.path.join(work_dir, "krnl.im4p")
    img4_path = os.path.join(work_dir, "kernelcache")

    # Extract raw from backup (unpatched original)
    print("  Extracting raw kernel from backup...")
    source = bak_path if os.path.exists(bak_path) else kernel_im4p
    run_cmd(f'{PYIMG4} im4p extract -i "{source}" -o "{raw_path}"')

    # Apply patches
    raw_data = Path(raw_path).read_bytes()
    patches = list(KERNEL_PATCHES_BASE)
    if kernel_jb_extra:
        patches += list(KERNEL_PATCHES_JB_EXTRA)
    print(f"  Applying {len(patches)} kernel patches...")
    patched_data = apply_patches(raw_data, patches, "kernel")
    Path(raw_path).write_bytes(patched_data)

    # Repack as krnl IM4P (NOT rkrn — preboot uses krnl fourcc)
    print("  Repacking as krnl IM4P...")
    run_cmd(f'{PYIMG4} im4p create -i "{raw_path}" -o "{im4p_path}" -f krnl --lzfse')

    # Preserve PAYP
    preserve_payp(payp_source, im4p_path)

    # Sign with APTicket
    print("  Signing with APTicket...")
    run_cmd(f'{PYIMG4} img4 create -p "{im4p_path}" -o "{img4_path}" -m "{apticket_path}"')

    size = os.path.getsize(img4_path)
    print(f"  Output: kernelcache ({size:,} bytes)")
    return img4_path


def patch_and_sign_txm(fw_dir, work_dir, apticket_path, txm_jb_extra):
    """Patch TXM, repack as IMG4, sign with APTicket."""
    print("\n" + "=" * 60)
    print("[TXM] Patching and signing")
    print("=" * 60)

    txm_im4p = os.path.join(fw_dir, "Firmware", "txm.iphoneos.research.im4p")
    bak_path = txm_im4p + ".bak"
    payp_source = bak_path if os.path.exists(bak_path) else txm_im4p

    raw_path = os.path.join(work_dir, "txm.raw")
    im4p_path = os.path.join(work_dir, "txm.im4p")
    img4_path = os.path.join(work_dir, "Ap,TrustedExecutionMonitor.img4")

    # Extract raw from backup
    print("  Extracting raw TXM from backup...")
    source = bak_path if os.path.exists(bak_path) else txm_im4p
    run_cmd(f'{PYIMG4} im4p extract -i "{source}" -o "{raw_path}"')

    # Apply patches
    raw_data = Path(raw_path).read_bytes()
    patches = list(TXM_PATCHES_BASE)
    if txm_jb_extra:
        patches += list(TXM_PATCHES_JB_EXTRA)
    print(f"  Applying {len(patches)} TXM patches...")
    patched_data = apply_patches(raw_data, patches, "TXM")
    Path(raw_path).write_bytes(patched_data)

    # Repack as trxm IM4P
    print("  Repacking as trxm IM4P...")
    run_cmd(f'{PYIMG4} im4p create -i "{raw_path}" -o "{im4p_path}" -f trxm --lzfse')

    # Preserve PAYP
    preserve_payp(payp_source, im4p_path)

    # Sign with APTicket
    print("  Signing with APTicket...")
    run_cmd(f'{PYIMG4} img4 create -p "{im4p_path}" -o "{img4_path}" -m "{apticket_path}"')

    size = os.path.getsize(img4_path)
    print(f"  Output: Ap,TrustedExecutionMonitor.img4 ({size:,} bytes)")
    return img4_path


def main():
    global SSH_PORT
    parser = argparse.ArgumentParser(
        description="Apply kernel + TXM patches via SSH ramdisk (no re-restore).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow:
  1. Boot SSH ramdisk (boot_rd.sh) and run iproxy 2222 22
  2. Run: python3 live_patch.py --kernel-jb-extra --txm-jb-extra
  3. Device halts automatically (--no-halt to skip)
  4. Normal boot picks up patched kernel + TXM

This replaces the full re-restore cycle (DETAILED_GUIDE Section 15)
for iterative patch development.
""")
    parser.add_argument("--firmware-dir", "-d",
                        default=str(DEFAULT_FW_DIR),
                        help="Path to extracted IPSW restore directory")
    parser.add_argument("--kernel-jb-extra", action="store_true",
                        help="Apply full kernel jailbreak patches (AMFI/sandbox/codesign/tfp0/kcall10)")
    parser.add_argument("--txm-jb-extra", action="store_true",
                        help="Apply TXM jailbreak patches (debugger/dev-mode/code-sign)")
    parser.add_argument("--kernel-only", action="store_true",
                        help="Only patch kernel (skip TXM)")
    parser.add_argument("--txm-only", action="store_true",
                        help="Only patch TXM (skip kernel)")
    parser.add_argument("--no-halt", action="store_true",
                        help="Don't halt device after upload")
    parser.add_argument("--dry-run", action="store_true",
                        help="Patch and sign locally but don't upload or halt")
    parser.add_argument("--ssh-port", default=None,
                        help=f"SSH port (default: {SSH_PORT})")
    args = parser.parse_args()

    if args.ssh_port is not None:
        SSH_PORT = args.ssh_port

    fw_dir = args.firmware_dir
    do_kernel = not args.txm_only
    do_txm = not args.kernel_only

    if not os.path.isdir(fw_dir):
        print(f"ERROR: Firmware directory not found: {fw_dir}")
        sys.exit(1)

    # Check tools
    for name, path in [("pyimg4", PYIMG4), ("sshpass", SSHPASS)]:
        if not path or (not os.path.exists(path) and not shutil.which(path)):
            print(f"ERROR: {name} not found at {path}")
            sys.exit(1)

    # Work directory for temporary files
    work_dir = tempfile.mkdtemp(prefix="live_patch_")
    print(f"Work directory: {work_dir}")

    try:
        # =====================================================================
        # Step 1: Mount preboot and get bootManifestHash
        # =====================================================================
        print("\n" + "=" * 60)
        print("[Step 1] Mounting preboot and getting bootManifestHash")
        print("=" * 60)

        remote_cmd("/sbin/mount_apfs -o rw /dev/disk1s5 /mnt5", check=False)
        boot_hash = get_boot_manifest_hash()
        print(f"  bootManifestHash: {boot_hash}")

        # =====================================================================
        # Step 2: Grab APTicket from preboot
        # =====================================================================
        print("\n" + "=" * 60)
        print("[Step 2] Grabbing APTicket from preboot")
        print("=" * 60)

        apticket_remote = f"/mnt5/{boot_hash}/System/Library/Caches/apticket.der"
        apticket_local = os.path.join(work_dir, "apticket.der")

        scp_from_device(apticket_remote, apticket_local)
        size = os.path.getsize(apticket_local)
        print(f"  APTicket: {size:,} bytes")

        # =====================================================================
        # Step 3: Patch and sign kernel
        # =====================================================================
        kernel_img4 = None
        if do_kernel:
            kernel_img4 = patch_and_sign_kernel(
                fw_dir, work_dir, apticket_local, args.kernel_jb_extra
            )

        # =====================================================================
        # Step 4: Patch and sign TXM
        # =====================================================================
        txm_img4 = None
        if do_txm:
            txm_img4 = patch_and_sign_txm(
                fw_dir, work_dir, apticket_local, args.txm_jb_extra
            )

        # =====================================================================
        # Step 5: Upload to preboot
        # =====================================================================
        if args.dry_run:
            print("\n" + "=" * 60)
            print("[DRY RUN] Skipping upload and halt")
            print("=" * 60)
            if kernel_img4:
                print(f"  Would upload: {kernel_img4}")
            if txm_img4:
                print(f"  Would upload: {txm_img4}")
            return

        print("\n" + "=" * 60)
        print("[Step 5] Uploading patched files to preboot")
        print("=" * 60)

        if kernel_img4:
            remote_kernel = f"/mnt5/{boot_hash}/System/Library/Caches/com.apple.kernelcaches/kernelcache"
            remote_kernel_bak = remote_kernel + ".bak"

            # Create backup on device if not exists
            if not check_remote_file(remote_kernel_bak):
                print("  Creating kernel backup on device...")
                remote_cmd(f"/bin/cp {remote_kernel} {remote_kernel_bak}")

            print("  Uploading patched kernel...")
            scp_to_device(kernel_img4, remote_kernel)
            remote_cmd(f"/bin/chmod 0644 {remote_kernel}")
            remote_cmd(f"/usr/sbin/chown 0:0 {remote_kernel}")
            print("  Kernel uploaded.")

        if txm_img4:
            remote_txm = f"/mnt5/{boot_hash}/usr/standalone/firmware/FUD/Ap,TrustedExecutionMonitor.img4"
            remote_txm_bak = remote_txm + ".bak"

            # Create backup on device if not exists
            if not check_remote_file(remote_txm_bak):
                print("  Creating TXM backup on device...")
                remote_cmd(f"/bin/cp {remote_txm} {remote_txm_bak}")

            print("  Uploading patched TXM...")
            scp_to_device(txm_img4, remote_txm)
            remote_cmd(f"/bin/chmod 0644 {remote_txm}")
            remote_cmd(f"/usr/sbin/chown 0:0 {remote_txm}")
            print("  TXM uploaded.")

        # =====================================================================
        # Step 6: Halt
        # =====================================================================
        if not args.no_halt:
            print("\n" + "=" * 60)
            print("[Step 6] Halting device")
            print("=" * 60)
            print("  Device will halt. Next normal boot will use patched kernel/TXM.")
            remote_cmd("/sbin/halt", check=False)
        else:
            print("\n  --no-halt: device still running. Halt manually when ready.")

        # Summary
        print("\n" + "=" * 60)
        print("DONE — Live patch applied")
        print("=" * 60)
        components = []
        if kernel_img4:
            n = len(KERNEL_PATCHES_BASE) + (len(KERNEL_PATCHES_JB_EXTRA) if args.kernel_jb_extra else 0)
            components.append(f"kernel ({n} patches)")
        if txm_img4:
            n = len(TXM_PATCHES_BASE) + (len(TXM_PATCHES_JB_EXTRA) if args.txm_jb_extra else 0)
            components.append(f"TXM ({n} patches)")
        print(f"  Patched: {', '.join(components)}")
        if not args.no_halt:
            print("  Device halted. Do a normal boot to test changes.")
        print()

    finally:
        # Cleanup work directory
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
