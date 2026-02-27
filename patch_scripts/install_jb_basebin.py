#!/usr/bin/env python3
"""
install_jb_basebin.py

Stage-2 jailbreak setup from original research flow:
1) patch /sbin/launchd (inject launchdhook + jetsam mitigation)
2) build BaseBin hooks (systemhook, launchdhook)
3) upload hooks + libellekit into /mnt1/cores

Run this while SSH ramdisk is active (boot_rd.sh + iproxy 2222 22).
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
BIN_DIR = REPO_ROOT / "bin"

SSH_HOST = "root@127.0.0.1"
SSH_PASS = "alpine"
LAUNCHD_PATCH_OFFSET = 0xD73C
LAUNCHD_PATCH_VALUE = 0x14000017  # b #0x5c
LAUNCHD_DIRECT_RUN_STDOUT_CHECK_OFFSET = 0x17738
LAUNCHD_DIRECT_RUN_STDOUT_CHECK_EXPECT = 0x360026A8  # tbz w8,#0,<panic path>
NOP = 0xD503201F


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
LDID = find_tool("ldid", "LDID")

SIGNCERT_CANDIDATES = [
    SCRIPT_DIR / "signcert.p12",
    REPO_ROOT / "signcert.p12",
    REPO_ROOT / "original-research" / "super-tart-vphone" / "CFW" / "signcert.p12",
]
if os.environ.get("SIGNCERT"):
    SIGNCERT_CANDIDATES.insert(0, Path(os.environ["SIGNCERT"]))


def ssh_opts(timeout: int) -> str:
    return (
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        f"-o ConnectTimeout={timeout} "
        "-o ServerAliveInterval=5 "
        "-o ServerAliveCountMax=120"
    )


def run(cmd: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    print(f"$ {cmd}")
    cp = subprocess.run(cmd, shell=True, text=True, capture_output=True, cwd=str(cwd) if cwd else None)
    if cp.stdout.strip():
        print(cp.stdout.strip())
    if cp.returncode != 0 and check:
        if cp.stderr.strip():
            print(cp.stderr.strip())
        raise RuntimeError(f"command failed: {cmd}")
    return cp


def ssh(port: str, timeout: int, remote_cmd: str, check: bool = True) -> None:
    cmd = (
        f'{SSHPASS} -p "{SSH_PASS}" ssh {ssh_opts(timeout)} '
        f'-p {port} {SSH_HOST} "{remote_cmd}"'
    )
    run(cmd, check=check)


def scp_from(port: str, timeout: int, remote_path: str, local_path: Path) -> None:
    cmd = (
        f'{SSHPASS} -p "{SSH_PASS}" scp -q -O {ssh_opts(timeout)} '
        f'-P {port} "{SSH_HOST}:{remote_path}" "{local_path}"'
    )
    run(cmd)


def scp_to(port: str, timeout: int, local_path: Path, remote_path: str) -> None:
    cmd = (
        f'{SSHPASS} -p "{SSH_PASS}" scp -q -O {ssh_opts(timeout)} '
        f'-P {port} "{local_path}" "{SSH_HOST}:{remote_path}"'
    )
    run(cmd)


def patch_u32(path: Path, offset: int, value: int) -> None:
    b = bytearray(path.read_bytes())
    if offset + 4 > len(b):
        raise ValueError(f"offset out of range: 0x{offset:X}")
    b[offset : offset + 4] = struct.pack("<I", value)
    path.write_bytes(b)


def read_u32(path: Path, offset: int) -> int:
    b = path.read_bytes()
    if offset + 4 > len(b):
        raise ValueError(f"offset out of range: 0x{offset:X}")
    return struct.unpack("<I", b[offset : offset + 4])[0]


def sign_binary(path: Path, identifier: str | None = None) -> None:
    signcert = next((p for p in SIGNCERT_CANDIDATES if p.exists()), None)
    id_opt = f" -I{identifier}" if identifier else ""
    if signcert is not None:
        run(f'"{LDID}" -S -M -K"{signcert}"{id_opt} "{path}"')
    else:
        # fallback ad-hoc
        run(f'"{LDID}" -S -M -Cadhoc{ id_opt } "{path}"')


def resolve_paths(user_jb_dir: str | None) -> tuple[Path, Path, Path]:
    # returns (jb_dir, custom_26_1_dir, optool_path)
    candidates = []
    if user_jb_dir:
        candidates.append(Path(user_jb_dir))
    candidates.extend(
        [
            REPO_ROOT / "jb",
            REPO_ROOT / "original-research" / "super-tart-vphone" / "CFW" / "jb",
        ]
    )
    jb_dir = next(
        (
            c
            for c in candidates
            if c.exists() and (c / "BaseBin" / "systemhook").exists() and (c / "BaseBin" / "launchdhook").exists()
        ),
        None,
    )
    if jb_dir is None:
        raise FileNotFoundError("Could not find jb directory with BaseBin/systemhook and BaseBin/launchdhook")

    custom_candidates = [
        REPO_ROOT / "custom_26.1",
        REPO_ROOT / "original-research" / "super-tart-vphone" / "CFW" / "custom_26.1",
    ]
    custom_dir = next((c for c in custom_candidates if c.exists()), None)
    if custom_dir is None:
        raise FileNotFoundError("Could not find custom_26.1 directory (need libellekit.dylib)")

    optool_candidates = [
        REPO_ROOT / "tools" / "optool",
        REPO_ROOT / "original-research" / "super-tart-vphone" / "CFW" / "tools" / "optool",
        BIN_DIR / "optool",
    ]
    optool = next((p for p in optool_candidates if p.exists()), None)
    if optool is None:
        raise FileNotFoundError("Could not find optool binary")

    return jb_dir, custom_dir, optool


def main() -> int:
    ap = argparse.ArgumentParser(description="Install basebin hooks from SSH ramdisk.")
    ap.add_argument("--ssh-port", default="2222", help="SSH port (default: 2222)")
    ap.add_argument("--ssh-timeout", type=int, default=10, help="SSH timeout seconds")
    ap.add_argument("--jb-dir", default=None, help="Path to jb directory")
    ap.add_argument(
        "--jetsam-patch",
        action="store_true",
        help="Apply legacy launchd jetsam patch at 0xD73C (disabled by default)",
    )
    ap.add_argument(
        "--no-direct-run-bypass",
        action="store_true",
        help="Do not patch launchd stdout direct-run check (debug option)",
    )
    ap.add_argument("--no-halt", action="store_true", help="Do not halt device at end")
    args = ap.parse_args()

    jb_dir, custom_dir, optool = resolve_paths(args.jb_dir)
    libellekit = custom_dir / "libellekit.dylib"
    if not libellekit.exists():
        raise FileNotFoundError(f"Missing {libellekit}")

    basebin_dir = jb_dir / "BaseBin"
    if not (basebin_dir / "systemhook").exists() or not (basebin_dir / "launchdhook").exists():
        raise FileNotFoundError(f"Missing BaseBin dirs under {basebin_dir}")

    ssh(args.ssh_port, args.ssh_timeout, "/usr/bin/id -u")
    ssh(args.ssh_port, args.ssh_timeout, "/sbin/mount_apfs -o rw /dev/disk1s1 /mnt1", check=False)
    ssh(args.ssh_port, args.ssh_timeout, "/bin/mkdir -p /mnt1/cores")

    with tempfile.TemporaryDirectory(prefix="jb_basebin_") as td:
        td_path = Path(td)
        launchd_local = td_path / "launchd"

        # Backup once, always patch from backup.
        ssh(
            args.ssh_port,
            args.ssh_timeout,
            '/bin/test -f /mnt1/sbin/launchd.bak || /bin/cp /mnt1/sbin/launchd /mnt1/sbin/launchd.bak',
        )
        scp_from(args.ssh_port, args.ssh_timeout, "/mnt1/sbin/launchd.bak", launchd_local)

        run(f'"{optool}" install -c load -p /cores/launchdhook.dylib -t "{launchd_local}"')
        if not args.no_direct_run_bypass:
            cur = read_u32(launchd_local, LAUNCHD_DIRECT_RUN_STDOUT_CHECK_OFFSET)
            if cur != LAUNCHD_DIRECT_RUN_STDOUT_CHECK_EXPECT:
                raise RuntimeError(
                    f"Unexpected opcode at launchd direct-run check offset 0x{LAUNCHD_DIRECT_RUN_STDOUT_CHECK_OFFSET:X}: "
                    f"got 0x{cur:08X}, expected 0x{LAUNCHD_DIRECT_RUN_STDOUT_CHECK_EXPECT:08X}. "
                    "Refusing to patch unknown binary."
                )
            patch_u32(launchd_local, LAUNCHD_DIRECT_RUN_STDOUT_CHECK_OFFSET, NOP)
            print(
                "Applied launchd direct-run stdout bypass: "
                f"0x{LAUNCHD_DIRECT_RUN_STDOUT_CHECK_OFFSET:X} -> NOP"
            )
        else:
            print("Skipping launchd direct-run stdout bypass (--no-direct-run-bypass).")

        if args.jetsam_patch:
            patch_u32(launchd_local, LAUNCHD_PATCH_OFFSET, LAUNCHD_PATCH_VALUE)
            print(f"Applied jetsam patch: launchd@0x{LAUNCHD_PATCH_OFFSET:X} -> 0x{LAUNCHD_PATCH_VALUE:08X}")
        else:
            print("Skipping legacy jetsam patch (recommended default).")
        # Prefer signcert-based signing here; ad-hoc launchd can trigger early init failures.
        sign_binary(launchd_local)

        scp_to(args.ssh_port, args.ssh_timeout, launchd_local, "/mnt1/sbin/launchd")
        ssh(args.ssh_port, args.ssh_timeout, "/bin/chmod 0755 /mnt1/sbin/launchd")

    # Build hooks using BaseBin top-level orchestration.
    # This prepares .include/.build and dependency libs (required for clean builds).
    run("make .include .build", cwd=basebin_dir)
    run("make systemhook launchdhook", cwd=basebin_dir)

    systemhook_dylib = basebin_dir / "systemhook" / "systemhook.dylib"
    launchdhook_dylib = basebin_dir / "launchdhook" / "launchdhook.dylib"
    if not systemhook_dylib.exists():
        raise FileNotFoundError(f"Build output missing: {systemhook_dylib}")
    if not launchdhook_dylib.exists():
        raise FileNotFoundError(f"Build output missing: {launchdhook_dylib}")

    # Sign payloads before upload (required for launchd to load launchdhook on normal boot).
    with tempfile.TemporaryDirectory(prefix="jb_basebin_payloads_") as ptd:
        ptd_path = Path(ptd)
        systemhook_signed = ptd_path / "systemhook.dylib"
        launchdhook_signed = ptd_path / "launchdhook.dylib"
        libellekit_signed = ptd_path / "libellekit.dylib"

        shutil.copy2(systemhook_dylib, systemhook_signed)
        shutil.copy2(launchdhook_dylib, launchdhook_signed)
        shutil.copy2(libellekit, libellekit_signed)

        sign_binary(systemhook_signed)
        sign_binary(launchdhook_signed)
        sign_binary(libellekit_signed)

        scp_to(args.ssh_port, args.ssh_timeout, systemhook_signed, "/mnt1/cores/systemhook.dylib")
        scp_to(args.ssh_port, args.ssh_timeout, launchdhook_signed, "/mnt1/cores/launchdhook.dylib")
        scp_to(args.ssh_port, args.ssh_timeout, libellekit_signed, "/mnt1/cores/libellekit.dylib")
    ssh(args.ssh_port, args.ssh_timeout, "/bin/chmod 0755 /mnt1/cores/systemhook.dylib", check=False)
    ssh(args.ssh_port, args.ssh_timeout, "/bin/chmod 0755 /mnt1/cores/launchdhook.dylib", check=False)
    ssh(args.ssh_port, args.ssh_timeout, "/bin/chmod 0755 /mnt1/cores/libellekit.dylib", check=False)

    if not args.no_halt:
        ssh(args.ssh_port, args.ssh_timeout, "/sbin/halt", check=False)
        print("Device halt requested.")
    else:
        print("Skipped halt (--no-halt).")

    print("\nDone: basebin stage installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
