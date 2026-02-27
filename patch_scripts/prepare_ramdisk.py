#!/usr/bin/env python3
"""
prepare_ramdisk.py - Create IMG4-signed firmware and SSH ramdisk for DFU boot.

Takes patched firmware (from patch_fw.py) and creates IMG4-signed images
that can be loaded into the VM via irecovery in DFU mode.

Prerequisites:
  - patch_fw.py must have been run (patched IM4P files in firmware directory)
  - VM must be running in DFU mode (for SHSH fetch via idevicerestore)
  - Tools: idevicerestore, img4 (img4lib), trustcache, pyimg4, ldid
  - SSHRD_Script sshtars/ssh.tar must exist (SSH components for ramdisk)

Steps:
  1. Fetch SHSH blobs from DFU device via idevicerestore
  2. Extract IM4M (APTicket) from SHSH
  3. Sign patched firmware components to IMG4
  4. Build custom SSH ramdisk (enlarged, re-signed)
  5. Build ramdisk trustcache
  6. Sign ramdisk + trustcache to IMG4

Output:
  _work/Ramdisk/ directory with all .img4 files ready for boot_rd.sh

Usage:
  python3 prepare_ramdisk.py [--firmware-dir PATH] [--output-dir PATH]
  python3 prepare_ramdisk.py --skip-shsh --im4m PATH   # reuse existing IM4M
"""

import argparse
import glob
import gzip
import os
import shutil
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
SSHRD_DIR = REPO_ROOT / "oems" / "SSHRD_Script"

IMG4 = os.environ.get("IMG4", str(BIN_DIR / "img4"))
IMG4TOOL = os.environ.get("IMG4TOOL", str(BIN_DIR / "img4tool"))
IDEVICERESTORE = os.environ.get("IDEVICERESTORE", str(BIN_DIR / "idevicerestore"))
TRUSTCACHE = os.environ.get("TRUSTCACHE", str(BIN_DIR / "trustcache"))
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
LDID = os.environ.get("LDID", str(BIN_DIR / "ldid") if (BIN_DIR / "ldid").exists()
       else shutil.which("ldid") or str(SSHRD_DIR / "Darwin" / "ldid"))
GTAR = os.environ.get("GTAR", str(BIN_DIR / "gtar") if (BIN_DIR / "gtar").exists()
       else shutil.which("gtar") or str(SSHRD_DIR / "Darwin" / "gtar"))

# SSH tarball from SSHRD_Script
SSH_TAR = SSHRD_DIR / "sshtars" / "ssh.tar"
SSH_TAR_GZ = SSHRD_DIR / "sshtars" / "ssh.tar.gz"

# Default firmware directory (prefer _work layout).
DEFAULT_FW_DIR = (WORK_ROOT / "firmwares" / "firmware_patched"
                  / "iPhone17,3_26.1_23B85_Restore")


def detect_firmware_dir(explicit_fw_dir):
    """Resolve firmware directory from explicit arg or common repo layouts."""
    if explicit_fw_dir:
        return str(Path(explicit_fw_dir).expanduser().resolve())

    candidates = [
        DEFAULT_FW_DIR,
        REPO_ROOT / "firmwares" / "firmware_patched" / "iPhone17,3_26.1_23B85_Restore",
        Path.cwd() / "_work" / "firmwares" / "firmware_patched" / "iPhone17,3_26.1_23B85_Restore",
        Path.cwd() / "firmwares" / "firmware_patched" / "iPhone17,3_26.1_23B85_Restore",
        Path.cwd() / "iPhone17,3_26.1_23B85_Restore",
    ]
    for c in candidates:
        if (c / "BuildManifest.plist").exists():
            return str(c)
    return str(DEFAULT_FW_DIR)

# =============================================================================
# Firmware components to sign as IMG4
# =============================================================================
# Components that use img4 (img4lib) for signing
# tag=None means the tool auto-detects (DFU bootloaders)
FIRMWARE_COMPONENTS = [
    {
        "name": "iBSS",
        "im4p": "Firmware/dfu/iBSS.vresearch101.RELEASE.im4p",
        "img4": "iBSS.vresearch101.RELEASE.img4",
        "tool": "img4",
        "tag": None,
    },
    {
        "name": "iBEC",
        "im4p": "Firmware/dfu/iBEC.vresearch101.RELEASE.im4p",
        "img4": "iBEC.vresearch101.RELEASE.img4",
        "tool": "img4",
        "tag": None,
    },
    {
        "name": "SPTM",
        "im4p": "Firmware/sptm.vresearch1.release.im4p",
        "img4": "sptm.vresearch1.release.img4",
        "tool": "img4",
        "tag": "sptm",
    },
    {
        "name": "DeviceTree",
        "im4p": "Firmware/all_flash/DeviceTree.vphone600ap.im4p",
        "img4": "DeviceTree.vphone600ap.img4",
        "tool": "img4",
        "tag": "rdtr",
    },
    {
        "name": "SEP",
        "im4p": "Firmware/all_flash/sep-firmware.vresearch101.RELEASE.im4p",
        "img4": "sep-firmware.vresearch101.RELEASE.img4",
        "tool": "img4",
        "tag": "rsep",
    },
    {
        "name": "TXM",
        "im4p": "Firmware/txm.iphoneos.research.im4p",
        "img4": "txm.img4",
        "tool": "pyimg4",
    },
    {
        "name": "kernel",
        "im4p": "kernelcache.research.vphone600",
        "img4": "krnl.img4",
        "tool": "pyimg4",
    },
]

# Ramdisk source (IM4P container in IPSW)
RAMDISK_IM4P = "043-53775-129.dmg"
RAMDISK_TRUSTCACHE_IM4P = "Firmware/043-53775-129.dmg.trustcache"


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


def find_shsh(shsh_dir):
    """Find the SHSH file in the shsh/ directory."""
    pattern = os.path.join(shsh_dir, "*.shsh")
    matches = glob.glob(pattern)
    if not matches:
        # Try .shsh.gz (gzipped)
        gz_pattern = os.path.join(shsh_dir, "*.shsh.gz")
        gz_matches = glob.glob(gz_pattern)
        if gz_matches:
            # Pick newest gzipped blob if multiple exist.
            gz_path = max(gz_matches, key=lambda p: os.path.getmtime(p))
            shsh_path = gz_path.replace(".shsh.gz", ".shsh")
            print(f"  Decompressing {os.path.basename(gz_path)}...")
            with gzip.open(gz_path, 'rb') as f_in:
                with open(shsh_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return shsh_path
        return None
    # Pick newest SHSH if multiple files exist.
    return max(matches, key=lambda p: os.path.getmtime(p))


def _is_gzip_file(path):
    """Return True if file is gzip-compressed (by magic bytes)."""
    try:
        with open(path, "rb") as f:
            return f.read(2) == b"\x1f\x8b"
    except OSError:
        return False


def normalize_shsh_for_pyimg4(shsh_path, work_dir):
    """
    Ensure SHSH is in a format pyimg4 can read.
    Some idevicerestore builds save gzip-compressed SHSH with a .shsh extension.
    """
    if _is_gzip_file(shsh_path):
        decoded_path = os.path.join(work_dir, "vphone.shsh.dec")
        print(f"  Detected gzip-compressed SHSH: {os.path.basename(shsh_path)}")
        print(f"  Decompressing to: {decoded_path}")
        with gzip.open(shsh_path, "rb") as f_in:
            with open(decoded_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return decoded_path
    return shsh_path


def fetch_shsh(fw_dir, work_dir):
    """Fetch SHSH blobs from DFU device using idevicerestore."""
    print("\n" + "=" * 60)
    print("[Step 1] Fetching SHSH blobs")
    print("=" * 60)

    shsh_dir = os.path.join(work_dir, "shsh")
    os.makedirs(shsh_dir, exist_ok=True)

    # Remove stale SHSH artifacts so we always use a freshly fetched ticket.
    for pattern in ("*.shsh", "*.shsh.gz"):
        for path in glob.glob(os.path.join(shsh_dir, pattern)):
            try:
                os.remove(path)
            except OSError:
                pass

    # idevicerestore -e -y <restore_dir> -t fetches TSS ticket only
    # Run from work_dir so shsh/ is created there
    cmd = f'cd "{work_dir}" && "{IDEVICERESTORE}" -e -y "{fw_dir}" -t'
    run_cmd(cmd)

    shsh_path = find_shsh(shsh_dir)
    if not shsh_path:
        print("  ERROR: No SHSH file found after idevicerestore!")
        print(f"  Checked: {shsh_dir}")
        sys.exit(1)

    print(f"  SHSH: {shsh_path}")
    return shsh_path


def extract_im4m(shsh_path, im4m_path, work_dir):
    """Extract IM4M from SHSH blob."""
    print("\n" + "=" * 60)
    print("[Step 2] Extracting IM4M from SHSH")
    print("=" * 60)

    normalized_shsh = normalize_shsh_for_pyimg4(shsh_path, work_dir)
    run_cmd(f'{PYIMG4} im4m extract -i "{normalized_shsh}" -o "{im4m_path}"')
    size = os.path.getsize(im4m_path)
    print(f"  IM4M: {im4m_path} ({size} bytes)")
    return im4m_path


def preserve_payp_structure(source_im4p, target_im4p):
    """
    Append PAYP structure from source IM4P to target IM4P and fix DER length.
    Mirrors original-research CFW/get_rd.py behavior for TXM/kernel compatibility.
    """
    src = Path(source_im4p).read_bytes()
    payp_offset = src.rfind(b"PAYP")
    if payp_offset == -1:
        print(f"    WARNING: PAYP not found in {source_im4p}; skipping PAYP preservation")
        return False

    payp_blob = src[payp_offset - 10:]
    payp_sz = len(payp_blob)
    with open(target_im4p, "ab") as f:
        f.write(payp_blob)

    data = bytearray(Path(target_im4p).read_bytes())
    old_len = int.from_bytes(data[2:5], "big")
    data[2:5] = (old_len + payp_sz).to_bytes(3, "big")
    Path(target_im4p).write_bytes(bytes(data))
    return True


def sign_firmware_components(fw_dir, output_dir, im4m_path, work_dir):
    """Sign all firmware IM4P files to IMG4 using IM4M."""
    print("\n" + "=" * 60)
    print("[Step 3] Signing firmware components to IMG4")
    print("=" * 60)

    for comp in FIRMWARE_COMPONENTS:
        name = comp["name"]
        im4p_path = os.path.join(fw_dir, comp["im4p"])
        img4_path = os.path.join(output_dir, comp["img4"])
        tool = comp["tool"]

        print(f"\n  [{name}]")

        if not os.path.exists(im4p_path):
            print(f"    ERROR: {im4p_path} not found!")
            sys.exit(1)

        if tool == "img4":
            # img4 (img4lib): img4 -i <im4p> -o <img4> -M <im4m> [-T <tag>]
            tag_arg = f' -T {comp["tag"]}' if comp.get("tag") else ""
            run_cmd(f'"{IMG4}" -i "{im4p_path}" -o "{img4_path}" -M "{im4m_path}"{tag_arg}')
        elif tool == "pyimg4":
            if name == "kernel":
                # Original-research behavior: build recovery kernel IM4P as rkrn.
                # Then preserve PAYP from original kernel IM4P before IMG4 signing.
                raw_kernel = os.path.join(work_dir, "kcache.sign.raw")
                rkrn_im4p = os.path.join(work_dir, "krnl.rkrn.im4p")
                payp_source = im4p_path + ".bak" if os.path.exists(im4p_path + ".bak") else im4p_path

                run_cmd(f'{PYIMG4} im4p extract -i "{im4p_path}" -o "{raw_kernel}"')
                run_cmd(f'{PYIMG4} im4p create -i "{raw_kernel}" -o "{rkrn_im4p}" -f rkrn --lzfse')
                preserve_payp_structure(payp_source, rkrn_im4p)
                run_cmd(f'{PYIMG4} img4 create -p "{rkrn_im4p}" -o "{img4_path}" -m "{im4m_path}"')
                size = os.path.getsize(img4_path)
                print(f"    Output: {os.path.basename(img4_path)} ({size} bytes)")
                continue
            # pyimg4: pyimg4 img4 create -p <im4p> -o <img4> -m <im4m>
            run_cmd(f'{PYIMG4} img4 create -p "{im4p_path}" -o "{img4_path}" -m "{im4m_path}"')

        size = os.path.getsize(img4_path)
        print(f"    Output: {os.path.basename(img4_path)} ({size} bytes)")

    print("\n  All firmware components signed.")


def build_ramdisk(fw_dir, output_dir, im4m_path, work_dir):
    """Build custom SSH ramdisk with trustcache."""
    print("\n" + "=" * 60)
    print("[Step 4] Building SSH ramdisk")
    print("=" * 60)

    ramdisk_im4p = os.path.join(fw_dir, RAMDISK_IM4P)
    ramdisk_dmg = os.path.join(work_dir, "ramdisk.dmg")
    ramdisk_custom = os.path.join(work_dir, "ramdisk1.dmg")
    mountpoint = os.path.join(work_dir, "SSHRD")

    # Check SSH tarball
    ssh_tar = str(SSH_TAR)
    if not os.path.exists(ssh_tar):
        if os.path.exists(str(SSH_TAR_GZ)):
            print("  Decompressing ssh.tar.gz...")
            run_cmd(f'gzip -dk "{SSH_TAR_GZ}"')
            ssh_tar = str(SSH_TAR)
        else:
            print(f"  WARNING: SSH tarball not found at {SSH_TAR}")
            print("  The ramdisk will be built without SSH. Run:")
            print("    cd oems/SSHRD_Script && git submodule update --init --recursive")
            ssh_tar = None

    # 4a. Extract ramdisk DMG from IM4P
    print("\n  [4a] Extracting ramdisk DMG from IM4P...")
    if not os.path.exists(ramdisk_im4p):
        print(f"    ERROR: {ramdisk_im4p} not found!")
        sys.exit(1)
    run_cmd(f'{PYIMG4} im4p extract -i "{ramdisk_im4p}" -o "{ramdisk_dmg}"')

    # 4b. Create enlarged ramdisk (254MB)
    print("\n  [4b] Creating enlarged ramdisk (254MB)...")
    os.makedirs(mountpoint, exist_ok=True)

    # Clean stale artifact from a previous interrupted run.
    if os.path.exists(ramdisk_custom):
        print(f"    Removing stale file: {ramdisk_custom}")
        run_cmd(f'sudo rm -f "{ramdisk_custom}"')

    # Mount original
    run_cmd(f'sudo hdiutil attach -mountpoint "{mountpoint}" "{ramdisk_dmg}" -owners off')

    # Create larger copy
    run_cmd(f'sudo hdiutil create -size 254m'
            f' -imagekey diskimage-class=CRawDiskImage'
            f' -format UDZO -fs APFS -layout NONE'
            f' -srcfolder "{mountpoint}" -copyuid root'
            f' "{ramdisk_custom}"')

    # Detach original, mount enlarged
    run_cmd(f'sudo hdiutil detach -force "{mountpoint}"')
    run_cmd(f'sudo hdiutil attach -mountpoint "{mountpoint}" "{ramdisk_custom}" -owners off')

    # 4c. Remove unnecessary files to free space
    print("\n  [4c] Removing unnecessary files for space...")
    remove_patterns = [
        "usr/standalone",
        "usr/lib/libLLVM*",
        "usr/share/progressui",
        "usr/share/restore",
    ]
    for pattern in remove_patterns:
        full_pattern = os.path.join(mountpoint, pattern)
        for path in glob.glob(full_pattern):
            if os.path.exists(path):
                run_cmd(f'sudo rm -rf "{path}"', check=False)

    # 4d. Add SSH components if available
    if ssh_tar:
        print("\n  [4d] Adding SSH components from SSHRD_Script...")
        run_cmd(f'"{GTAR}" -x --no-overwrite-dir -f "{ssh_tar}" -C "{mountpoint}/"')

    # 4e. Re-sign all Mach-O binaries (preserving entitlements)
    print("\n  [4e] Re-signing all Mach-O binaries...")
    target_paths = [
        f"{mountpoint}/usr/local/bin/*",
        f"{mountpoint}/usr/local/lib/*",
        f"{mountpoint}/usr/bin/*",
        f"{mountpoint}/bin/*",
        f"{mountpoint}/usr/lib/*",
        f"{mountpoint}/sbin/*",
        f"{mountpoint}/usr/sbin/*",
        f"{mountpoint}/usr/libexec/*",
    ]
    sign_count = 0
    for pattern in target_paths:
        for path in glob.glob(pattern):
            if os.path.isfile(path) and not os.path.islink(path):
                file_type = subprocess.run(
                    f'file "{path}"', shell=True, capture_output=True, text=True
                ).stdout
                if "Mach-O" in file_type:
                    subprocess.run(
                        f'"{LDID}" -S -M -Cadhoc "{path}"',
                        shell=True, capture_output=True
                    )
                    sign_count += 1
    print(f"    Re-signed {sign_count} Mach-O binaries")

    # 4f. Build trustcache for ramdisk
    print("\n  [4f] Building ramdisk trustcache...")
    sshrd_tc = os.path.join(work_dir, "sshrd.tc")
    tc_im4p = os.path.join(work_dir, "trustcache.im4p")
    tc_img4 = os.path.join(output_dir, "trustcache.img4")

    run_cmd(f'"{TRUSTCACHE}" create "{sshrd_tc}" "{mountpoint}"')
    run_cmd(f'{PYIMG4} im4p create -i "{sshrd_tc}" -o "{tc_im4p}" -f rtsc')
    run_cmd(f'{PYIMG4} img4 create -p "{tc_im4p}" -o "{tc_img4}" -m "{im4m_path}"')

    tc_size = os.path.getsize(tc_img4)
    print(f"    Trustcache: {os.path.basename(tc_img4)} ({tc_size} bytes)")

    # 4g. Finalize ramdisk
    print("\n  [4g] Finalizing ramdisk...")
    run_cmd(f'sudo hdiutil detach -force "{mountpoint}"')
    resize_cmd = f'hdiutil resize -sectors min "{ramdisk_custom}"'
    resize_result = run_cmd(resize_cmd, check=False, capture=True)
    if resize_result.returncode != 0:
        stderr = (resize_result.stderr or "").strip()
        # ramdisk1.dmg can be root-owned because it is created with sudo above.
        if resize_result.returncode == 13 or "permission denied" in stderr.lower():
            print("    Non-sudo resize failed with permission denied; retrying with sudo...")
            run_cmd(f"sudo {resize_cmd}")
        else:
            if stderr:
                print(f"  STDERR: {stderr}")
            print(f"  ERROR: command failed with exit code {resize_result.returncode}")
            sys.exit(1)

    # Sign ramdisk to IMG4
    rd_im4p = os.path.join(work_dir, "ramdisk.im4p")
    rd_img4 = os.path.join(output_dir, "ramdisk.img4")

    run_cmd(f'{PYIMG4} im4p create -i "{ramdisk_custom}" -o "{rd_im4p}" -f rdsk')
    run_cmd(f'{PYIMG4} img4 create -p "{rd_im4p}" -o "{rd_img4}" -m "{im4m_path}"')

    rd_size = os.path.getsize(rd_img4)
    print(f"    Ramdisk: {os.path.basename(rd_img4)} ({rd_size} bytes)")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare IMG4-signed firmware and SSH ramdisk for DFU boot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output files (in output directory):
  iBSS.vresearch101.RELEASE.img4    - Patched iBSS bootloader
  iBEC.vresearch101.RELEASE.img4    - Patched iBEC bootloader
  sptm.vresearch1.release.img4      - SPTM firmware
  DeviceTree.vphone600ap.img4       - Device tree
  sep-firmware.vresearch101.RELEASE.img4 - SEP firmware
  txm.img4                          - Patched TXM (trustcache manager)
  krnl.img4                         - Patched kernel
  ramdisk.img4                      - Custom SSH ramdisk
  trustcache.img4                   - Ramdisk trustcache

Use boot_rd.sh to load these into the VM via irecovery.
""")
    parser.add_argument("--firmware-dir", "-d",
                        default=None,
                        help="Path to extracted IPSW restore directory (auto-detected if omitted)")
    parser.add_argument("--output-dir", "-o",
                        default=str(WORK_ROOT / "Ramdisk"),
                        help="Output directory for IMG4 files (default: _work/Ramdisk/)")
    parser.add_argument("--skip-shsh", action="store_true",
                        help="Skip SHSH fetch (use existing IM4M)")
    parser.add_argument("--im4m",
                        default=None,
                        help="Path to existing IM4M file (requires --skip-shsh)")
    parser.add_argument("--work-dir", "-w",
                        default=None,
                        help="Working directory for temp files")
    args = parser.parse_args()

    fw_dir = detect_firmware_dir(args.firmware_dir)
    output_dir = args.output_dir
    work_dir = args.work_dir or str(WORK_ROOT / "ramdisk_work")

    # Validate firmware directory
    if not os.path.isdir(fw_dir):
        print(f"ERROR: Firmware directory not found: {fw_dir}")
        sys.exit(1)

    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)

    print(f"Firmware directory: {fw_dir}")
    print(f"Output directory:   {output_dir}")
    print(f"Work directory:     {work_dir}")

    # Check tools
    tools = [
        ("img4", IMG4), ("pyimg4", PYIMG4), ("trustcache", TRUSTCACHE),
        ("ldid", LDID),
    ]
    if not args.skip_shsh:
        tools.append(("idevicerestore", IDEVICERESTORE))

    for name, path in tools:
        if not path or (not os.path.exists(path) and not shutil.which(path)):
            print(f"ERROR: {name} not found at {path}")
            sys.exit(1)
        print(f"  {name}: {path}")

    # Step 1-2: Get IM4M
    im4m_path = os.path.join(work_dir, "vphone.im4m")

    if args.skip_shsh:
        if args.im4m:
            if not os.path.exists(args.im4m):
                print(f"ERROR: IM4M file not found: {args.im4m}")
                sys.exit(1)
            shutil.copy2(args.im4m, im4m_path)
            print(f"\nUsing existing IM4M: {args.im4m}")
        elif os.path.exists(im4m_path):
            print(f"\nUsing cached IM4M: {im4m_path}")
        else:
            print("ERROR: --skip-shsh requires --im4m or existing IM4M in work dir")
            sys.exit(1)
    else:
        shsh_path = fetch_shsh(fw_dir, work_dir)
        extract_im4m(shsh_path, im4m_path, work_dir)

    # Step 3: Sign firmware components
    sign_firmware_components(fw_dir, output_dir, im4m_path, work_dir)

    # Step 4: Build ramdisk + trustcache
    build_ramdisk(fw_dir, output_dir, im4m_path, work_dir)

    # Summary
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    print(f"IMG4 files ready in: {output_dir}")
    print()
    for f in sorted(os.listdir(output_dir)):
        if f.endswith(".img4"):
            size = os.path.getsize(os.path.join(output_dir, f))
            print(f"  {f:50s} {size:>10,} bytes")
    print()
    print("Next: Run boot_rd.sh to load into DFU VM via irecovery")


if __name__ == "__main__":
    main()
