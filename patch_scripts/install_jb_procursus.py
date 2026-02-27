#!/usr/bin/env python3
"""
install_jb_procursus.py

Stage-1 jailbreak setup from the original research flow:
1) mount /mnt5
2) copy Procursus bootstrap + Sileo deb into preboot hash dir
3) unpack into jb-vphone/procursus layout

This script is intended to run while SSH ramdisk is active
(boot_rd.sh + iproxy 2222 22).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
BIN_DIR = REPO_ROOT / "bin"


def find_tool(name: str, env_var: str | None = None) -> str:
    if env_var and os.environ.get(env_var):
        return os.environ[env_var]
    p = BIN_DIR / name
    if p.exists():
        return str(p)
    from_path = shutil.which(name)
    if from_path:
        return from_path
    return name


SSHPASS = find_tool("sshpass", "SSHPASS")
ZSTD = find_tool("zstd", "ZSTD")
SSH_HOST = "root@127.0.0.1"
SSH_PASS = "alpine"


def ssh_opts(timeout: int) -> str:
    return (
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        f"-o ConnectTimeout={timeout} "
        "-o ServerAliveInterval=5 "
        "-o ServerAliveCountMax=120"
    )


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"$ {cmd}")
    cp = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if cp.stdout.strip():
        print(cp.stdout.strip())
    if cp.returncode != 0 and check:
        if cp.stderr.strip():
            print(cp.stderr.strip())
        raise RuntimeError(f"command failed: {cmd}")
    return cp


def ssh(port: str, timeout: int, remote_cmd: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = (
        f'{SSHPASS} -p "{SSH_PASS}" ssh {ssh_opts(timeout)} '
        f'-p {port} {SSH_HOST} "{remote_cmd}"'
    )
    return run(cmd, check=check)


def scp_to(port: str, timeout: int, local_path: Path, remote_path: str) -> None:
    cmd = (
        f'{SSHPASS} -p "{SSH_PASS}" scp -q -O {ssh_opts(timeout)} '
        f'-P {port} "{local_path}" "{SSH_HOST}:{remote_path}"'
    )
    run(cmd)


def resolve_jb_dir(user_dir: str | None) -> Path:
    candidates = []
    if user_dir:
        candidates.append(Path(user_dir))
    candidates.extend(
        [
            REPO_ROOT / "jb",
            REPO_ROOT / "original-research" / "super-tart-vphone" / "CFW" / "jb",
        ]
    )
    required = ("bootstrap-iphoneos-arm64.tar.zst", "org.coolstar.sileo_2.5.1_iphoneos-arm64.deb")
    for c in candidates:
        if c.exists() and all((c / name).exists() for name in required):
            return c

    msg = ["Could not find a jb directory containing required files:"]
    msg.extend([f"  - {name}" for name in required])
    msg.append("Checked:")
    msg.extend([f"  - {p}" for p in candidates])
    raise FileNotFoundError("\n".join(msg))


def get_boot_manifest_hash(port: str, timeout: int, mnt5_path: str) -> str:
    out = ssh(port, timeout, f"/bin/ls {mnt5_path}").stdout
    for token in out.split():
        if re.fullmatch(r"[0-9A-Fa-f]{96}", token):
            return token
    raise RuntimeError(f"Could not find 96-char preboot hash under {mnt5_path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Install Procursus payload into preboot from SSH ramdisk.")
    ap.add_argument("--ssh-port", default="2222", help="SSH port (default: 2222)")
    ap.add_argument("--ssh-timeout", type=int, default=10, help="SSH timeout seconds")
    ap.add_argument("--jb-dir", default=None, help="Path to jb directory")
    ap.add_argument("--mnt5", default="/mnt5", help="Mount point for disk1s5 (default: /mnt5)")
    args = ap.parse_args()

    jb_dir = resolve_jb_dir(args.jb_dir)
    bootstrap_zst = jb_dir / "bootstrap-iphoneos-arm64.tar.zst"
    sileo_deb = jb_dir / "org.coolstar.sileo_2.5.1_iphoneos-arm64.deb"

    if not bootstrap_zst.exists():
        raise FileNotFoundError(f"Missing {bootstrap_zst}")
    if not sileo_deb.exists():
        raise FileNotFoundError(f"Missing {sileo_deb}")

    print(f"JB directory: {jb_dir}")
    print(f"Bootstrap:    {bootstrap_zst.name}")
    print(f"Sileo deb:    {sileo_deb.name}")

    ssh(args.ssh_port, args.ssh_timeout, "/usr/bin/id -u")
    ssh(args.ssh_port, args.ssh_timeout, f"/sbin/mount_apfs -o rw /dev/disk1s5 {args.mnt5}", check=False)
    boot_hash = get_boot_manifest_hash(args.ssh_port, args.ssh_timeout, args.mnt5)
    print(f"Preboot hash: {boot_hash}")

    with tempfile.TemporaryDirectory(prefix="jb_procursus_") as td:
        td_path = Path(td)
        bootstrap_tar = td_path / "bootstrap-iphoneos-arm64.tar"

        # Keep host repo clean; decompress into temp location.
        run(f'"{ZSTD}" -d -f "{bootstrap_zst}" -o "{bootstrap_tar}"')

        remote_dir = f"{args.mnt5}/{boot_hash}"
        print(f"Uploading to: {remote_dir}")
        scp_to(args.ssh_port, args.ssh_timeout, bootstrap_tar, f"{remote_dir}/")
        scp_to(args.ssh_port, args.ssh_timeout, sileo_deb, f"{remote_dir}/")

    ssh(args.ssh_port, args.ssh_timeout, f"/bin/mkdir -p {args.mnt5}/{boot_hash}/jb-vphone")
    ssh(args.ssh_port, args.ssh_timeout, f"/bin/chmod 0755 {args.mnt5}/{boot_hash}/jb-vphone")
    ssh(args.ssh_port, args.ssh_timeout, f"/usr/sbin/chown 0:0 {args.mnt5}/{boot_hash}/jb-vphone")

    ssh(
        args.ssh_port,
        args.ssh_timeout,
        f"/usr/bin/tar --preserve-permissions -xkf {args.mnt5}/{boot_hash}/bootstrap-iphoneos-arm64.tar "
        f"-C {args.mnt5}/{boot_hash}/jb-vphone/",
    )
    ssh(
        args.ssh_port,
        args.ssh_timeout,
        f"/bin/mv {args.mnt5}/{boot_hash}/jb-vphone/var {args.mnt5}/{boot_hash}/jb-vphone/procursus",
    )
    ssh(
        args.ssh_port,
        args.ssh_timeout,
        f"/bin/mv {args.mnt5}/{boot_hash}/jb-vphone/procursus/jb/* {args.mnt5}/{boot_hash}/jb-vphone/procursus",
        check=False,
    )
    ssh(
        args.ssh_port,
        args.ssh_timeout,
        f"/bin/rm -rf {args.mnt5}/{boot_hash}/jb-vphone/procursus/jb",
        check=False,
    )
    ssh(
        args.ssh_port,
        args.ssh_timeout,
        f"/bin/rm {args.mnt5}/{boot_hash}/bootstrap-iphoneos-arm64.tar",
        check=False,
    )

    print("\nDone: Procursus payload staged.")
    print("Next:")
    print("  1) halt ramdisk VM")
    print("  2) normal boot")
    print("  3) SSH into normal boot (usually dropbear port 22222)")
    print("  4) run GUIDE.md procursus bootstrap commands under /private/preboot/<hash>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
