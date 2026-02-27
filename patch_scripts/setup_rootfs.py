#!/usr/bin/env python3
"""
setup_rootfs.py - Modify virtual iPhone rootfs via SSH ramdisk.

After booting the SSH ramdisk (boot_rd.sh), this script connects over SSH
and sets up the rootfs for normal boot: installs Cryptex, patches system
binaries, installs launch daemons, and optionally adds GPU Metal support.

Prerequisites:
  - VM booted with SSH ramdisk (boot_rd.sh)
  - iproxy running: iproxy 2222 22 &
  - Tools: sshpass, ipsw, aea, ldid, plutil (on host)
  - Files:
    - patch_scripts/signcert.p12 (preferred code signing identity location)
    - jb/iosbinpack64.tar     (jailbreak binary pack)
    - jb/LaunchDaemons/       (bash.plist, dropbear.plist, trollvnc.plist)
  - IPSW firmware directory with Cryptex DMGs

Steps:
  1. Mount rootfs read-write, rename snapshot
  2. Decrypt and install Cryptex (SystemOS + AppOS)
  3. Create dyld cache symlinks
  4. Patch seputil (hardcode AA.gl gigalocker filename)
  5. Rename gigalocker to AA.gl
  6. Patch launchd_cache_loader (NOP secure cache check)
  7. Patch mobileactivationd (activation bypass, research flow)
  8. Patch launchd (jetsam panic mitigation used by original research)
  9. Install iosbinpack64
  10. Install launch daemons + modify launchd.plist
  11. Install AppleParavirtGPUMetalIOGPUFamily.bundle from PCC (optional)
  12. Install libAppleParavirtCompilerPluginIOGPUFamily.dylib (optional, for Metal)
  13. Halt device

Usage:
  python3 setup_rootfs.py [--firmware-dir PATH] [--pcc-gpu-bundle PATH] [--pcc-gpu-plugin PATH]
"""

import argparse
import glob
import os
import plistlib
import shlex
import struct
import subprocess
import shutil
import sys
import tempfile
from pathlib import Path

# =============================================================================
# Paths
# =============================================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
BIN_DIR = REPO_ROOT / "bin"

# Default firmware directories
DEFAULT_FW_DIR = (REPO_ROOT / "firmwares" / "firmware_patched"
                  / "iPhone17,3_26.1_23B85_Restore")
DEFAULT_PCC_DIR = (REPO_ROOT / "firmwares" / "firmware_patched" / "pcc_extracted")

# Tool paths (prefer bin/ then system)
def _find_tool(name, env_var, fallback=None):
    """Find a tool: env var > bin/ > PATH > fallback."""
    if env_var and os.environ.get(env_var):
        return os.environ[env_var]
    bin_path = str(BIN_DIR / name)
    if os.path.exists(bin_path):
        return bin_path
    found = shutil.which(name)
    if found:
        return found
    return fallback or name

SSHPASS = _find_tool("sshpass", "SSHPASS")
IPSW = _find_tool("ipsw", "IPSW")
LDID = _find_tool("ldid", "LDID")
PLUTIL = _find_tool("plutil", "PLUTIL", "/usr/bin/plutil")

# SSH connection settings
SSH_HOST = "root@127.0.0.1"
SSH_PORT = "2222"
SSH_PASS = "alpine"
SSH_CONNECT_TIMEOUT = int(os.environ.get("SSH_CONNECT_TIMEOUT", "10"))
SCP_RETRIES = int(os.environ.get("SCP_RETRIES", "3"))
SCP_TIMEOUT = int(os.environ.get("SCP_TIMEOUT", "900"))
SCP_RECURSIVE_TIMEOUT = int(os.environ.get("SCP_RECURSIVE_TIMEOUT", "1800"))


def set_ssh_port(port):
    """Update the SSH port used for all connections."""
    global SSH_PORT
    SSH_PORT = port


# Signing certificate (preferred to mirror original-research fix_boot.py behavior).
_default_signcert_candidates = [
    str(SCRIPT_DIR / "signcert.p12"),
    str(REPO_ROOT / "signcert.p12"),
    str(REPO_ROOT / "original-research" / "super-tart-vphone" / "CFW" / "signcert.p12"),
]
if os.environ.get("SIGNCERT"):
    _default_signcert_candidates.insert(0, os.environ["SIGNCERT"])
SIGNCERT = next((p for p in _default_signcert_candidates if os.path.exists(p)), None)

# Cryptex file names within the IPSW restore directory
CRYPTEX_SYSTEM_AEA = "043-54303-126.dmg.aea"
CRYPTEX_APP_DMG = "043-54062-129.dmg"

# Patch offsets
SEPUTIL_PATCH_OFFSET = 0x1B3F1    # "AA" string for gigalocker filename
LAUNCHD_CACHE_PATCH_OFFSET = 0xB58  # NOP the secure cache check
MOBILEACTIVATIOND_PATCH_OFFSET = 0x2F5F84  # mov x0,#1 (activation bypass)
LAUNCHD_JETSAM_PATCH_OFFSET = 0xD73C  # b #0x5c (original-research mitigation)

# TrollVNC plist from OEM
TROLLVNC_PLIST = REPO_ROOT / "oems" / "TrollVNC" / "layout" / "Library" / "LaunchDaemons" / "com.82flex.trollvnc.plist"


# =============================================================================
# SSH helpers
# =============================================================================
def ssh_opts():
    return (
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        f"-o ConnectTimeout={SSH_CONNECT_TIMEOUT} "
        "-o ServerAliveInterval=5 "
        "-o ServerAliveCountMax=120"
    )


def _scp_cmd(local_path, remote_path, recursive=False, from_device=False):
    direction_src = f'"{SSH_HOST}:{remote_path}"' if from_device else f'"{local_path}"'
    direction_dst = f'"{local_path}"' if from_device else f'"{SSH_HOST}:{remote_path}"'
    recursive_flag = "-r " if recursive else ""
    # Force legacy SCP protocol (-O) for better compatibility with SSHRD/dropbear.
    return (
        f'{SSHPASS} -p "{SSH_PASS}" scp -q -O {recursive_flag}{ssh_opts()} '
        f'-P {SSH_PORT} {direction_src} {direction_dst}'
    )


def _run_scp(cmd, label, timeout, retries=SCP_RETRIES):
    for attempt in range(1, retries + 1):
        print(f"      attempt {attempt}/{retries}")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            print(f"    ERROR: SCP timed out after {timeout}s ({label})")
            if attempt < retries:
                print("    Retrying SCP...")
                continue
            return False

        if result.returncode == 0:
            return True

        err = result.stderr.strip() or result.stdout.strip()
        print(f"    ERROR: SCP failed ({label}): {err}")
        if attempt < retries:
            print("    Retrying SCP...")
    return False


def remote_cmd(cmd, check=True):
    """Execute a command on the device via SSH."""
    full_cmd = (f'{SSHPASS} -p "{SSH_PASS}" ssh {ssh_opts()} '
                f'-p {SSH_PORT} {SSH_HOST} "{cmd}"')
    print(f"    [ssh] {cmd}")
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"           {result.stdout.strip()}")
    if check and result.returncode != 0:
        if result.stderr.strip():
            print(f"           STDERR: {result.stderr.strip()}")
        print(f"    ERROR: Remote command failed (exit {result.returncode})")
        return None
    return result.stdout.strip()


def scp_to_device(local_path, remote_path):
    """Copy a file to the device via SCP."""
    print(f"    [scp] {os.path.basename(local_path)} → {remote_path}")
    cmd = _scp_cmd(local_path=local_path, remote_path=remote_path, recursive=False, from_device=False)
    return _run_scp(cmd, label=f"upload {os.path.basename(local_path)}", timeout=SCP_TIMEOUT)


def scp_to_device_recursive(local_path, remote_path):
    """Copy a directory recursively to the device."""
    print(f"    [scp] {local_path} → {remote_path} (recursive)")
    cmd = _scp_cmd(local_path=local_path, remote_path=remote_path, recursive=True, from_device=False)
    return _run_scp(cmd, label=f"upload recursive {remote_path}", timeout=SCP_RECURSIVE_TIMEOUT)


def scp_from_device(remote_path, local_path):
    """Copy a file from the device via SCP."""
    print(f"    [scp] {remote_path} → {os.path.basename(local_path)}")
    cmd = _scp_cmd(local_path=local_path, remote_path=remote_path, recursive=False, from_device=True)
    return _run_scp(cmd, label=f"download {os.path.basename(remote_path)}", timeout=SCP_TIMEOUT)


def check_remote_file_exists(path):
    """Check if a file exists on the remote device."""
    cmd = (f'{SSHPASS} -p "{SSH_PASS}" ssh {ssh_opts()} '
           f'-p {SSH_PORT} {SSH_HOST} "test -e {shlex.quote(path)}"')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        err = result.stderr.strip() or result.stdout.strip()
        if err:
            print(f"    WARNING: path probe failed for {path}: {err}")
    return result.returncode == 0


def run_local(cmd, check=True):
    """Run a local shell command."""
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        sys.exit(1)
    return result


def ldid_sign(binary_path, identifier=None):
    """Sign a binary, preferring original-research signing flags/cert when available."""
    if SIGNCERT and os.path.exists(SIGNCERT):
        id_opt = f' -I{identifier}' if identifier else ""
        run_local(f'{LDID} -S -M -K"{SIGNCERT}"{id_opt} "{binary_path}"')
    else:
        print("  WARNING: signcert.p12 not found; falling back to ad-hoc ldid -S signing.")
        id_opt = f' -I{identifier}' if identifier else ""
        run_local(f'{LDID} -S{id_opt} "{binary_path}"')


def ensure_mnt1_rw():
    """Best-effort ensure /mnt1 is mounted read-write."""
    remote_cmd("/sbin/mount_apfs -o rw /dev/disk1s1 /mnt1", check=False)


# =============================================================================
# Patch helpers
# =============================================================================
def patch_binary_bytes(filepath, offset, data):
    """Patch bytes at a specific offset in a binary file."""
    file_size = os.path.getsize(filepath)
    if offset < 0 or (offset + len(data)) > file_size:
        raise ValueError(
            f"Patch offset out of bounds for {filepath}: "
            f"offset=0x{offset:X}, size={file_size}, patch_len={len(data)}"
        )
    with open(filepath, "r+b") as f:
        f.seek(offset)
        old = f.read(len(data))
        f.seek(offset)
        f.write(data)
    return old


def patch_binary_u32(filepath, offset, value):
    """Patch a 32-bit value at a specific offset."""
    return patch_binary_bytes(filepath, offset, struct.pack('<I', value))


# =============================================================================
# LaunchDaemon plist generators
# =============================================================================
def make_bash_plist():
    """Generate bash LaunchDaemon plist."""
    return {
        "Label": "com.vphone.bash",
        "ProgramArguments": ["/iosbinpack64/bin/bash"],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardErrorPath": "/tmp/bash-stderr.log",
        "StandardOutPath": "/tmp/bash-stdout.log",
    }


def make_dropbear_plist():
    """Generate dropbear SSH LaunchDaemon plist."""
    return {
        "Label": "com.vphone.dropbear",
        "ProgramArguments": [
            "/iosbinpack64/usr/local/bin/dropbear",
            "--shell", "/iosbinpack64/bin/bash",
            "-R", "-p", "22", "-F",
        ],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardErrorPath": "/tmp/dropbear-stderr.log",
        "StandardOutPath": "/tmp/dropbear-stdout.log",
    }


# =============================================================================
# Step implementations
# =============================================================================
def step_verify_ssh():
    """Verify SSH connection to the device."""
    print("\n" + "=" * 60)
    print("[Step 0] Verifying SSH connection")
    print("=" * 60)

    # Use exit status as the source of truth (stdout can vary across SSHRD builds).
    cmd = (f'{SSHPASS} -p "{SSH_PASS}" ssh {ssh_opts()} '
           f'-p {SSH_PORT} {SSH_HOST} "/usr/bin/id -u"')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("  ERROR: Cannot connect to device via SSH!")
        if result.stderr.strip():
            print(f"  SSH stderr: {result.stderr.strip()}")
        if result.stdout.strip():
            print(f"  SSH stdout: {result.stdout.strip()}")
        print("  Make sure:")
        print("    1. VM is booted with SSH ramdisk (boot_rd.sh)")
        print("    2. iproxy is running: iproxy 2222 22 &")
        print(f"    3. SSH is accessible at {SSH_HOST}:{SSH_PORT}")
        sys.exit(1)
    print("  SSH connection OK")


def step_mount_rootfs():
    """Mount rootfs read-write and rename snapshot."""
    print("\n" + "=" * 60)
    print("[Step 1] Mounting rootfs and renaming snapshot")
    print("=" * 60)

    remote_cmd("/sbin/mount_apfs -o rw /dev/disk1s1 /mnt1")

    # Get snapshot name
    snap_output = remote_cmd("/usr/bin/snaputil -l /mnt1")
    if not snap_output:
        print("  WARNING: Could not list snapshots. Rootfs may already be modified.")
        return

    # Find the com.apple.os.update snapshot
    snap_name = None
    for line in snap_output.splitlines():
        line = line.strip()
        if line.startswith("com.apple.os.update-"):
            snap_name = line
            break

    if snap_name:
        print(f"  Renaming snapshot: {snap_name} → orig-fs")
        remote_cmd(f'/usr/bin/snaputil -n "{snap_name}" orig-fs /mnt1')
    else:
        print("  No com.apple.os.update snapshot found (may already be renamed)")

    # Keep /mnt1 mounted for subsequent patch/install steps.
    print("  Keeping /mnt1 mounted for remaining steps")


def step_install_cryptex(fw_dir, work_dir):
    """Decrypt and install Cryptex partitions."""
    print("\n" + "=" * 60)
    print("[Step 2] Installing Cryptex (SystemOS + AppOS)")
    print("=" * 60)

    cryptex_sys_aea = os.path.join(fw_dir, CRYPTEX_SYSTEM_AEA)
    cryptex_app_dmg_src = os.path.join(fw_dir, CRYPTEX_APP_DMG)
    cryptex_sys_dmg = os.path.join(work_dir, "CryptexSystemOS.dmg")
    cryptex_app_dmg = os.path.join(work_dir, "CryptexAppOS.dmg")
    mount_sys = os.path.join(work_dir, "CryptexSystemOS")
    mount_app = os.path.join(work_dir, "CryptexAppOS")

    # 2a. Decrypt SystemOS AEA
    if not os.path.exists(cryptex_sys_dmg):
        print("\n  [2a] Decrypting CryptexSystemOS AEA...")
        if not os.path.exists(cryptex_sys_aea):
            print(f"    ERROR: {cryptex_sys_aea} not found!")
            sys.exit(1)

        key_result = run_local(f'{IPSW} fw aea --key "{cryptex_sys_aea}"', check=True)
        key = key_result.stdout.strip()
        print(f"    AEA key: {key[:32]}...")
        run_local(f'aea decrypt -i "{cryptex_sys_aea}" -o "{cryptex_sys_dmg}" -key-value \'{key}\'')
    else:
        print("  CryptexSystemOS.dmg already exists, skipping decrypt")

    # 2b. Copy AppOS DMG
    if not os.path.exists(cryptex_app_dmg):
        print("\n  [2b] Copying CryptexAppOS DMG...")
        shutil.copy2(cryptex_app_dmg_src, cryptex_app_dmg)
    else:
        print("  CryptexAppOS.dmg already exists")

    # 2c. Mount Cryptex DMGs
    print("\n  [2c] Mounting Cryptex DMGs...")
    os.makedirs(mount_sys, exist_ok=True)
    os.makedirs(mount_app, exist_ok=True)
    run_local(f'sudo hdiutil attach -mountpoint "{mount_sys}" "{cryptex_sys_dmg}" -owners off')
    run_local(f'sudo hdiutil attach -mountpoint "{mount_app}" "{cryptex_app_dmg}" -owners off')

    # 2d. Prepare device directories
    print("\n  [2d] Preparing device Cryptex directories...")
    # /mnt1 may already be mounted from Step 1; "Resource busy" is expected in that case.
    remote_cmd("/sbin/mount_apfs -o rw /dev/disk1s1 /mnt1", check=False)

    remote_cmd("/bin/rm -rf /mnt1/System/Cryptexes/App")
    remote_cmd("/bin/rm -rf /mnt1/System/Cryptexes/OS")
    remote_cmd("/bin/mkdir -p /mnt1/System/Cryptexes/App")
    remote_cmd("/bin/chmod 0755 /mnt1/System/Cryptexes/App")
    remote_cmd("/bin/mkdir -p /mnt1/System/Cryptexes/OS")
    remote_cmd("/bin/chmod 0755 /mnt1/System/Cryptexes/OS")

    # 2e. Copy Cryptex files to device
    print("\n  [2e] Copying Cryptex files to device (this will take several minutes)...")
    if not scp_to_device_recursive(f"{mount_sys}/.", "/mnt1/System/Cryptexes/OS"):
        print("  ERROR: Failed to upload Cryptex SystemOS files")
        sys.exit(1)
    if not scp_to_device_recursive(f"{mount_app}/.", "/mnt1/System/Cryptexes/App"):
        print("  ERROR: Failed to upload Cryptex AppOS files")
        sys.exit(1)

    # 2f. Create dyld cache symlinks
    print("\n  [2f] Creating dyld cache symlinks...")
    remote_cmd("/bin/ln -sf ../../../System/Cryptexes/OS/System/Library/Caches/com.apple.dyld "
               "/mnt1/System/Library/Caches/com.apple.dyld")
    remote_cmd("/bin/ln -sf ../../../../System/Cryptexes/OS/System/DriverKit/System/Library/dyld "
               "/mnt1/System/DriverKit/System/Library/dyld")

    # Cleanup mounts
    print("\n  Unmounting Cryptex DMGs...")
    run_local(f'sudo hdiutil detach -force "{mount_sys}"', check=False)
    run_local(f'sudo hdiutil detach -force "{mount_app}"', check=False)


def step_patch_seputil(work_dir):
    """Patch seputil to hardcode AA.gl gigalocker filename."""
    print("\n" + "=" * 60)
    print("[Step 3] Patching seputil (gigalocker → AA.gl)")
    print("=" * 60)

    ensure_mnt1_rw()

    local_seputil = os.path.join(work_dir, "seputil")

    # Backup on device if needed
    if not check_remote_file_exists("/mnt1/usr/libexec/seputil.bak"):
        print("  Creating backup...")
        remote_cmd("/bin/cp /mnt1/usr/libexec/seputil /mnt1/usr/libexec/seputil.bak")

    # Download from device (always from backup)
    scp_from_device("/mnt1/usr/libexec/seputil.bak", local_seputil)

    # Patch: write "AA" at the gigalocker lookup offset
    print(f"  Patching offset 0x{SEPUTIL_PATCH_OFFSET:X} with 'AA'...")
    patch_binary_bytes(local_seputil, SEPUTIL_PATCH_OFFSET, b"AA")

    # Re-sign (prefer original-research cert mode: -S -M -Ksigncert.p12)
    print("  Re-signing seputil...")
    ldid_sign(local_seputil, identifier="com.apple.seputil")

    # Upload patched binary
    scp_to_device(local_seputil, "/mnt1/usr/libexec/seputil")
    remote_cmd("/bin/chmod 0755 /mnt1/usr/libexec/seputil")

    # Rename gigalocker on device
    print("  Renaming gigalocker to AA.gl...")
    remote_cmd("/sbin/mount_apfs -o rw /dev/disk1s3 /mnt3", check=False)
    remote_cmd("/bin/mv /mnt3/*.gl /mnt3/AA.gl", check=False)

    os.remove(local_seputil)


def step_patch_launchd_cache_loader(work_dir):
    """Patch launchd_cache_loader to enable unsecure cache mode."""
    print("\n" + "=" * 60)
    print("[Step 4] Patching launchd_cache_loader")
    print("=" * 60)

    ensure_mnt1_rw()

    local_lcl = os.path.join(work_dir, "launchd_cache_loader")

    # Backup on device if needed
    if not check_remote_file_exists("/mnt1/usr/libexec/launchd_cache_loader.bak"):
        print("  Creating backup...")
        remote_cmd("/bin/cp /mnt1/usr/libexec/launchd_cache_loader "
                   "/mnt1/usr/libexec/launchd_cache_loader.bak")

    # Download from device (always from backup)
    scp_from_device("/mnt1/usr/libexec/launchd_cache_loader.bak", local_lcl)

    # Patch: NOP the secure cache check at offset 0xB58
    NOP = 0xD503201F
    print(f"  Patching offset 0x{LAUNCHD_CACHE_PATCH_OFFSET:X} with NOP...")
    patch_binary_u32(local_lcl, LAUNCHD_CACHE_PATCH_OFFSET, NOP)

    # Re-sign (adhoc is sufficient with TXM trustcache bypass)
    print("  Re-signing launchd_cache_loader...")
    ldid_sign(local_lcl, identifier="com.apple.launchd_cache_loader")

    # Upload patched binary
    scp_to_device(local_lcl, "/mnt1/usr/libexec/launchd_cache_loader")
    remote_cmd("/bin/chmod 0755 /mnt1/usr/libexec/launchd_cache_loader")

    os.remove(local_lcl)


def step_patch_mobileactivationd(work_dir):
    """Patch mobileactivationd for activation bypass used in original research flow."""
    print("\n" + "=" * 60)
    print("[Step 5] Patching mobileactivationd")
    print("=" * 60)

    ensure_mnt1_rw()

    local_mad = os.path.join(work_dir, "mobileactivationd")

    # Backup on device if needed
    if not check_remote_file_exists("/mnt1/usr/libexec/mobileactivationd.bak"):
        print("  Creating backup...")
        remote_cmd("/bin/cp /mnt1/usr/libexec/mobileactivationd "
                   "/mnt1/usr/libexec/mobileactivationd.bak")

    # Download from device (always from backup)
    scp_from_device("/mnt1/usr/libexec/mobileactivationd.bak", local_mad)

    # Patch: mov x0, #1
    MOV_X0_1 = 0xD2800020
    print(f"  Patching offset 0x{MOBILEACTIVATIOND_PATCH_OFFSET:X} with MOV X0,#1...")
    patch_binary_u32(local_mad, MOBILEACTIVATIOND_PATCH_OFFSET, MOV_X0_1)

    # Re-sign
    print("  Re-signing mobileactivationd...")
    ldid_sign(local_mad)

    # Upload patched binary
    scp_to_device(local_mad, "/mnt1/usr/libexec/mobileactivationd")
    remote_cmd("/bin/chmod 0755 /mnt1/usr/libexec/mobileactivationd")

    os.remove(local_mad)


def step_patch_launchd(work_dir):
    """Patch launchd to match original-research jetsam panic mitigation."""
    print("\n" + "=" * 60)
    print("[Step 6] Patching launchd")
    print("=" * 60)

    ensure_mnt1_rw()

    local_launchd = os.path.join(work_dir, "launchd")

    # Backup on device if needed
    if not check_remote_file_exists("/mnt1/sbin/launchd.bak"):
        print("  Creating backup...")
        remote_cmd("/bin/cp /mnt1/sbin/launchd /mnt1/sbin/launchd.bak")

    # Download from device (always from backup)
    scp_from_device("/mnt1/sbin/launchd.bak", local_launchd)

    # Patch: b #0x5c
    B_0X5C = 0x14000017
    print(f"  Patching offset 0x{LAUNCHD_JETSAM_PATCH_OFFSET:X} with branch...")
    patch_binary_u32(local_launchd, LAUNCHD_JETSAM_PATCH_OFFSET, B_0X5C)

    # Re-sign
    print("  Re-signing launchd...")
    ldid_sign(local_launchd)

    # Upload patched binary
    scp_to_device(local_launchd, "/mnt1/sbin/launchd")
    remote_cmd("/bin/chmod 0755 /mnt1/sbin/launchd")

    os.remove(local_launchd)


def step_install_iosbinpack(jb_dir):
    """Install iosbinpack64 jailbreak binaries."""
    print("\n" + "=" * 60)
    print("[Step 7] Installing iosbinpack64")
    print("=" * 60)

    ensure_mnt1_rw()

    tar_path = os.path.join(jb_dir, "iosbinpack64.tar")
    fallback_tar_path = os.path.join(
        str(REPO_ROOT), "original-research", "super-tart-vphone", "CFW", "jb", "iosbinpack64.tar"
    )
    if not os.path.exists(tar_path):
        if os.path.exists(fallback_tar_path):
            print(f"  {tar_path} not found, using fallback from original-research:")
            print(f"    {fallback_tar_path}")
            tar_path = fallback_tar_path
        else:
            print(f"  ERROR: {tar_path} not found!")
            print("  Download iosbinpack64 and place it at jb/iosbinpack64.tar")
            sys.exit(1)

    print("  Uploading iosbinpack64.tar to device...")
    if not scp_to_device(tar_path, "/mnt1/iosbinpack64.tar"):
        print("  ERROR: Failed to upload iosbinpack64.tar")
        sys.exit(1)

    print("  Extracting on device...")
    if remote_cmd("/usr/bin/tar --preserve-permissions --no-overwrite-dir "
                  "-xvf /mnt1/iosbinpack64.tar -C /mnt1") is None:
        print("  ERROR: Failed to extract iosbinpack64.tar on device")
        sys.exit(1)
    remote_cmd("/bin/rm /mnt1/iosbinpack64.tar", check=False)


def step_install_launch_daemons(jb_dir, work_dir):
    """Install launch daemons for bash, dropbear, and trollvnc."""
    print("\n" + "=" * 60)
    print("[Step 8] Installing launch daemons")
    print("=" * 60)

    ensure_mnt1_rw()

    ld_dir = os.path.join(jb_dir, "LaunchDaemons")
    os.makedirs(ld_dir, exist_ok=True)

    # Generate plists if they don't exist
    plists = {}

    # bash.plist
    bash_plist_path = os.path.join(ld_dir, "bash.plist")
    if not os.path.exists(bash_plist_path):
        print("  Generating bash.plist...")
        with open(bash_plist_path, 'wb') as f:
            plistlib.dump(make_bash_plist(), f, sort_keys=False)
    plists["bash.plist"] = bash_plist_path

    # dropbear.plist
    dropbear_plist_path = os.path.join(ld_dir, "dropbear.plist")
    if not os.path.exists(dropbear_plist_path):
        print("  Generating dropbear.plist...")
        with open(dropbear_plist_path, 'wb') as f:
            plistlib.dump(make_dropbear_plist(), f, sort_keys=False)
    plists["dropbear.plist"] = dropbear_plist_path

    # trollvnc.plist (from TrollVNC OEM)
    trollvnc_plist_path = os.path.join(ld_dir, "trollvnc.plist")
    if not os.path.exists(trollvnc_plist_path):
        if os.path.exists(str(TROLLVNC_PLIST)):
            print("  Copying trollvnc.plist from TrollVNC...")
            shutil.copy2(str(TROLLVNC_PLIST), trollvnc_plist_path)
        else:
            print(f"  WARNING: TrollVNC plist not found at {TROLLVNC_PLIST}")
            print("  Skipping trollvnc daemon installation")
    if os.path.exists(trollvnc_plist_path):
        plists["trollvnc.plist"] = trollvnc_plist_path

    # 6a. Upload plists to device
    print("\n  [6a] Uploading launch daemon plists...")
    daemon_dir_candidates = [
        "/mnt1/System/Library/LaunchDaemons",
        "/mnt1/System/Cryptexes/OS/System/Library/LaunchDaemons",
    ]
    daemon_remote_dir = None
    for candidate in daemon_dir_candidates:
        if check_remote_file_exists(candidate):
            daemon_remote_dir = candidate
            break
    if not daemon_remote_dir:
        # Directory doesn't exist yet — create the preferred location
        daemon_remote_dir = daemon_dir_candidates[0]
        print(f"  LaunchDaemons directory not found; creating {daemon_remote_dir}")
        remote_cmd(f"/bin/mkdir -p {daemon_remote_dir}")
        remote_cmd(f"/bin/chmod 0755 {daemon_remote_dir}")
    print(f"  Using LaunchDaemons directory: {daemon_remote_dir}")

    installed_plists = {}
    for name, path in plists.items():
        remote_target = f"{daemon_remote_dir}/{name}"
        if scp_to_device(path, remote_target):
            # Some layouts may not expose all targets; don't fail hard on chmod.
            remote_cmd(f"/bin/chmod 0644 {remote_target}", check=False)
            installed_plists[name] = path
        else:
            print(f"    WARNING: Failed to upload {name}; skipping its launchd injection.")

    if not installed_plists:
        print("  WARNING: No launch daemon plist was uploaded successfully. Skipping launchd.plist modification.")
        return

    # 6b. Modify launchd.plist to inject our daemons
    print("\n  [6b] Modifying launchd.plist...")
    local_launchd_plist = os.path.join(work_dir, "launchd.plist")
    launchd_candidates = [
        "/mnt1/System/Library/xpc/launchd.plist",
        "/mnt1/System/Cryptexes/OS/System/Library/xpc/launchd.plist",
    ]
    launchd_remote = None
    for candidate in launchd_candidates:
        if check_remote_file_exists(candidate):
            launchd_remote = candidate
            break

    if not launchd_remote:
        print("    WARNING: launchd.plist not found in expected locations:")
        for p in launchd_candidates:
            print(f"      - {p}")
        print("    Skipping launchd.plist injection step.")
        return

    launchd_backup = f"{launchd_remote}.bak"
    launchd_remote_dir = os.path.dirname(launchd_remote)
    print(f"    Using launchd.plist at: {launchd_remote}")

    # Backup on device if needed
    if not check_remote_file_exists(launchd_backup):
        print("    Creating backup...")
        remote_cmd(f'/bin/cp "{launchd_remote}" "{launchd_backup}"')

    # Download launchd.plist (always from backup)
    if not scp_from_device(launchd_backup, local_launchd_plist):
        print("    WARNING: Could not download launchd.plist backup; skipping launchd injection.")
        return

    # Convert to XML for editing
    run_local(f'{PLUTIL} -convert xml1 "{local_launchd_plist}"')

    # Load and inject each daemon
    with open(local_launchd_plist, 'rb') as f:
        launchd_data = plistlib.load(f)

    for name, path in installed_plists.items():
        insert_key = f"/System/Library/LaunchDaemons/{name}"
        print(f"    Injecting {insert_key}...")
        with open(path, 'rb') as f:
            daemon_data = plistlib.load(f)
        launchd_data.setdefault('LaunchDaemons', {})[insert_key] = daemon_data

    with open(local_launchd_plist, 'wb') as f:
        plistlib.dump(launchd_data, f, sort_keys=False)

    # Upload modified launchd.plist
    if not scp_to_device(local_launchd_plist, f"{launchd_remote_dir}/launchd.plist"):
        print("    WARNING: Failed to upload modified launchd.plist.")
        return
    remote_cmd(f"/bin/chmod 0644 {launchd_remote}", check=False)

    os.remove(local_launchd_plist)


def step_install_gpu_metal(gpu_bundle_path, gpu_plugin_path=None):
    """Install Metal GPU bundle and optional compiler plugin dylib."""
    print("\n" + "=" * 60)
    print("[Step 9] Installing GPU Metal support")
    print("=" * 60)

    if not gpu_bundle_path and not gpu_plugin_path:
        print("  Skipped (no --pcc-gpu-bundle or --pcc-gpu-plugin specified)")
        print("  To enable Metal GPU support, provide:")
        print("    1) --pcc-gpu-bundle  /path/.../AppleParavirtGPUMetalIOGPUFamily.bundle")
        print("    2) --pcc-gpu-plugin /path/.../libAppleParavirtCompilerPluginIOGPUFamily.dylib")
        print("  The plugin dylib is required for working Metal on vphone.")
        return

    ensure_mnt1_rw()

    bundle_remote = "/mnt1/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle"
    plugin_remote = f"{bundle_remote}/libAppleParavirtCompilerPluginIOGPUFamily.dylib"

    remote_cmd("/bin/mkdir -p /mnt1/System/Library/Extensions")

    if gpu_bundle_path:
        if not os.path.isdir(gpu_bundle_path):
            print(f"  ERROR: GPU bundle not found at {gpu_bundle_path}")
            return
        print(f"  Bundle source: {gpu_bundle_path}")
        print("  Uploading bundle to /mnt1/System/Library/Extensions/...")
        if not scp_to_device_recursive(gpu_bundle_path, bundle_remote):
            print("  ERROR: Failed to upload GPU bundle.")
            return
    else:
        print("  No --pcc-gpu-bundle specified; assuming bundle already exists on rootfs.")
        if not check_remote_file_exists(bundle_remote):
            print(f"  ERROR: Bundle not found on device: {bundle_remote}")
            print("         Provide --pcc-gpu-bundle or install the bundle first.")
            return

    if gpu_plugin_path:
        if not os.path.isfile(gpu_plugin_path):
            print(f"  ERROR: GPU plugin dylib not found at {gpu_plugin_path}")
            return
        print(f"  Plugin source: {gpu_plugin_path}")
        print("  Uploading compiler plugin dylib...")
        if not scp_to_device(gpu_plugin_path, plugin_remote):
            print("  ERROR: Failed to upload compiler plugin dylib.")
            return
    else:
        print("  WARNING: --pcc-gpu-plugin not provided.")
        print("           Metal may still fail (black setup / no MTL device).")

    # Best-effort ownership/mode normalization to mirror original-research flow.
    remote_cmd(f"/usr/sbin/chown -R 0:0 {bundle_remote}", check=False)
    remote_cmd(f"/bin/chmod 0755 {bundle_remote}", check=False)
    remote_cmd(f"/bin/chmod 0755 {bundle_remote}/AppleParavirtGPUMetalIOGPUFamily", check=False)
    remote_cmd(f"/bin/chmod 0755 {plugin_remote}", check=False)
    remote_cmd(f"/bin/chmod 0644 {bundle_remote}/Info.plist", check=False)
    remote_cmd(f"/bin/chmod 0644 {bundle_remote}/_CodeSignature/CodeResources", check=False)

    # If iosbinpack ldid exists, ad-hoc sign on device as well (best-effort).
    if gpu_plugin_path:
        remote_cmd(
            f"if [ -x /mnt1/iosbinpack64/usr/bin/ldid ]; then "
            f"/mnt1/iosbinpack64/usr/bin/ldid -S {plugin_remote}; "
            f"else echo WARNING:_ldid_not_found_on_device_skip_resign; fi",
            check=False,
        )

    print("  GPU Metal files installed.")
    print("  NOTE: normal boot + MetalTest/MTLCreateSystemDefaultDevice should now work.")


def step_halt():
    """Halt the device."""
    print("\n" + "=" * 60)
    print("[Step 10] Halting device")
    print("=" * 60)

    remote_cmd("/sbin/halt", check=False)
    print("  Device halting. Wait for it to shut down completely before rebooting.")


# =============================================================================
# Main
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Set up virtual iPhone rootfs via SSH ramdisk.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
After this script completes, the device will halt.
Reboot using boot_rd.sh (but with normal kernel, not ramdisk) or
use idevicerestore to restore normally, then boot with tart.

For GPU Metal support, pass both:
  --pcc-gpu-bundle /path/to/mounted/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle
  --pcc-gpu-plugin /path/to/libAppleParavirtCompilerPluginIOGPUFamily.dylib
""")
    parser.add_argument("--firmware-dir", "-d",
                        default=str(DEFAULT_FW_DIR),
                        help="Path to extracted IPSW restore directory")
    parser.add_argument("--jb-dir", "-j",
                        default=str(REPO_ROOT / "jb"),
                        help="Path to jailbreak files directory (default: jb/)")
    parser.add_argument("--work-dir", "-w",
                        default=None,
                        help="Working directory for temp files")
    parser.add_argument("--pcc-gpu-bundle",
                        default=None,
                        help="Path to AppleParavirtGPUMetalIOGPUFamily.bundle from PCC")
    parser.add_argument("--pcc-gpu-plugin",
                        default=None,
                        help="Path to libAppleParavirtCompilerPluginIOGPUFamily.dylib")
    parser.add_argument("--skip-cryptex", action="store_true",
                        help="Skip Cryptex installation")
    parser.add_argument("--skip-patches", action="store_true",
                        help="Skip seputil/launchd_cache_loader/mobileactivationd patching")
    parser.add_argument("--patch-launchd", action="store_true",
                        help="Also patch /sbin/launchd (disabled by default; may trigger AMFI launch constraints)")
    parser.add_argument("--skip-launchd-patch", action="store_true",
                        help="Deprecated alias (launchd patch is already skipped by default)")
    parser.add_argument("--skip-iosbinpack", action="store_true",
                        help="Skip iosbinpack64 installation")
    parser.add_argument("--skip-daemons", action="store_true",
                        help="Skip launch daemon installation")
    parser.add_argument("--no-halt", action="store_true",
                        help="Don't halt the device when done")
    parser.add_argument("--ssh-port", default=SSH_PORT,
                        help="SSH port (default: 2222)")
    args = parser.parse_args()

    set_ssh_port(args.ssh_port)

    fw_dir = args.firmware_dir
    jb_dir = args.jb_dir
    work_dir = args.work_dir or os.path.join(
        os.path.dirname(fw_dir), "rootfs_work")

    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(jb_dir, exist_ok=True)

    print(f"Firmware directory: {fw_dir}")
    print(f"JB directory:       {jb_dir}")
    print(f"Work directory:     {work_dir}")

    # Check tools
    for name, path in [("sshpass", SSHPASS), ("ldid", LDID), ("plutil", PLUTIL)]:
        if not shutil.which(path) and not os.path.exists(path):
            print(f"ERROR: {name} not found at {path}")
            sys.exit(1)

    if not args.skip_cryptex:
        if not shutil.which(IPSW) and not os.path.exists(IPSW):
            print(f"ERROR: ipsw not found at {IPSW}")
            sys.exit(1)

    # Step 0: Verify SSH
    step_verify_ssh()

    # Step 1: Mount rootfs
    step_mount_rootfs()

    # Step 2: Install Cryptex
    if not args.skip_cryptex:
        step_install_cryptex(fw_dir, work_dir)

    # Step 3: Patch seputil
    if not args.skip_patches:
        step_patch_seputil(work_dir)

    # Step 4: Patch launchd_cache_loader
    if not args.skip_patches:
        step_patch_launchd_cache_loader(work_dir)

    # Step 5: Patch mobileactivationd
    if not args.skip_patches:
        step_patch_mobileactivationd(work_dir)

    # Step 6: Patch launchd (opt-in only; README_old flow does not require this patch)
    if not args.skip_patches:
        if args.patch_launchd and not args.skip_launchd_patch:
            step_patch_launchd(work_dir)
        else:
            print("\n[Info] Skipping launchd patch (default behavior).")
            print("       Use --patch-launchd only if you explicitly need jetsam mitigation.")
    elif args.skip_launchd_patch:
        print("\n[Info] --skip-launchd-patch acknowledged (launchd patch skipped).")

    # Step 7: Install iosbinpack64
    if not args.skip_iosbinpack:
        step_install_iosbinpack(jb_dir)

    # Step 8: Install launch daemons
    if not args.skip_daemons:
        step_install_launch_daemons(jb_dir, work_dir)

    # Step 9: GPU Metal
    step_install_gpu_metal(args.pcc_gpu_bundle, args.pcc_gpu_plugin)

    # Step 10: Halt
    if not args.no_halt:
        step_halt()

    print("\n" + "=" * 60)
    print("DONE - Rootfs setup complete")
    print("=" * 60)
    print()
    if not args.no_halt:
        print("Device is halting. After shutdown, boot normally with tart.")
    print("First boot services: bash, dropbear (SSH), trollvnc")
    print()
    print("After normal boot, connect via:")
    print("  iproxy 2222 22 &")
    print("  ssh root@127.0.0.1 -p2222  (password: alpine)")


if __name__ == "__main__":
    main()
