#!/usr/bin/env python3
"""
Inject bash/dropbear/trollvnc launch daemons into a launchd plist.

Usage:
  python3 patch_scripts/inject_launchdaemons.py \
    --launchd /tmp/launchd.plist \
    --repo "$(pwd)"
"""

from __future__ import annotations

import argparse
import plistlib
from pathlib import Path


DAEMONS = ("bash", "dropbear", "trollvnc")


def load_plist(path: Path) -> dict:
    with path.open("rb") as f:
        return plistlib.load(f)


def save_plist(path: Path, data: dict) -> None:
    with path.open("wb") as f:
        plistlib.dump(data, f, sort_keys=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--launchd",
        required=True,
        type=Path,
        help="Path to local launchd.plist (downloaded from device).",
    )
    parser.add_argument(
        "--repo",
        required=True,
        type=Path,
        help="Repository root path.",
    )
    parser.add_argument(
        "--daemons-dir",
        type=Path,
        default=None,
        help=(
            "Optional override for daemon plist directory. "
            "Default: <repo>/jb/LaunchDaemons "
            "(fallback: <repo>/original-research/super-tart-vphone/CFW/jb/LaunchDaemons)"
        ),
    )
    args = parser.parse_args()

    launchd_path: Path = args.launchd
    repo: Path = args.repo
    if args.daemons_dir is not None:
        daemons_dir = args.daemons_dir
    else:
        primary = repo / "jb/LaunchDaemons"
        fallback = repo / "original-research/super-tart-vphone/CFW/jb/LaunchDaemons"
        daemons_dir = primary if primary.exists() else fallback

    if not launchd_path.exists():
        raise FileNotFoundError(f"launchd plist not found: {launchd_path}")
    if not daemons_dir.exists():
        raise FileNotFoundError(f"daemon plist directory not found: {daemons_dir}")

    launchd = load_plist(launchd_path)
    launchd.setdefault("LaunchDaemons", {})

    injected = []
    for daemon_name in DAEMONS:
        source_path = daemons_dir / f"{daemon_name}.plist"
        if not source_path.exists():
            raise FileNotFoundError(f"missing daemon plist: {source_path}")
        source_data = load_plist(source_path)
        key = f"/System/Library/LaunchDaemons/{daemon_name}.plist"
        launchd["LaunchDaemons"][key] = source_data
        injected.append(key)

    save_plist(launchd_path, launchd)

    print(f"Updated: {launchd_path}")
    print("Injected keys:")
    for key in injected:
        print(f"  - {key}")

    dropbear = launchd["LaunchDaemons"].get("/System/Library/LaunchDaemons/dropbear.plist", {})
    args_list = dropbear.get("ProgramArguments", [])
    if isinstance(args_list, list):
        if "22222" in args_list:
            print("Dropbear port in plist: 22222")
        elif "22" in args_list:
            print("Dropbear port in plist: 22")
        else:
            print("Dropbear port in plist: unknown (check ProgramArguments)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
