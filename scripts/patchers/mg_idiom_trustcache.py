#!/usr/bin/env python3
"""
Append vphone_mg_idiom.dylib to the restore StaticTrustCache.

DYLD_INSERT_LIBRARIES is not enough for restricted/platform processes on
iOS 18.x. The inserted dylib also needs to be trusted by the boot-loaded
trustcache, otherwise dyld/AMFI strips or rejects the injection before the
interposer can run.
"""

import argparse
import hashlib
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(argv, **kwargs):
    return subprocess.run(argv, check=True, text=True, **kwargs)


def find_restore_dir(vm_dir: Path) -> Path:
    candidates = sorted(vm_dir.glob("*_Restore"))
    if not candidates:
        raise FileNotFoundError(f"no *_Restore directory under {vm_dir}")
    if len(candidates) > 1:
        names = ", ".join(str(p) for p in candidates)
        raise RuntimeError(f"multiple restore directories found: {names}")
    return candidates[0]


def static_trustcache_path(restore_dir: Path) -> Path:
    manifest_path = restore_dir / "BuildManifest.plist"
    with manifest_path.open("rb") as f:
        manifest = plistlib.load(f)

    identities = manifest.get("BuildIdentities", [])
    if not identities:
        raise RuntimeError(f"{manifest_path} has no BuildIdentities")

    identity_manifest = identities[0].get("Manifest", {})
    static_tc = identity_manifest.get("StaticTrustCache", {})
    rel_path = static_tc.get("Info", {}).get("Path")
    if not rel_path:
        raise RuntimeError("BuildManifest StaticTrustCache path not found")

    path = restore_dir / rel_path
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def update_manifest_digest(manifest_path: Path, component: str, payload_path: Path) -> bool:
    if not manifest_path.exists():
        return False

    with manifest_path.open("rb") as f:
        manifest = plistlib.load(f)

    identities = manifest.get("BuildIdentities", [])
    changed = False
    digest = hashlib.sha384(payload_path.read_bytes()).digest()

    for identity in identities:
        component_dict = identity.get("Manifest", {}).get(component)
        if not isinstance(component_dict, dict):
            continue
        info = component_dict.get("Info", {})
        rel_path = info.get("Path")
        if not rel_path:
            continue
        if (manifest_path.parent / rel_path).resolve() != payload_path.resolve():
            continue
        if component_dict.get("Digest") != digest:
            component_dict["Digest"] = digest
            changed = True

    if changed:
        with manifest_path.open("wb") as f:
            plistlib.dump(manifest, f, sort_keys=False)
    return changed


def update_all_manifest_digests(restore_dir: Path, payload_path: Path) -> None:
    changed = []
    for name in ("BuildManifest.plist", "iPhone-BuildManifest.plist"):
        manifest_path = restore_dir / name
        if update_manifest_digest(manifest_path, "StaticTrustCache", payload_path):
            changed.append(name)
    if changed:
        print(f"  [+] updated StaticTrustCache digest in {', '.join(changed)}")


def im4p_fourcc(pyimg4: str, im4p_path: Path) -> str:
    proc = subprocess.run(
        [pyimg4, "im4p", "info", "-i", str(im4p_path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("FourCC:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError(f"could not read IM4P FourCC from {im4p_path}")


def ensure_tool(path: str, name: str) -> str:
    resolved = shutil.which(path) if "/" not in path else path
    if not resolved or not Path(resolved).exists():
        raise FileNotFoundError(f"{name} not found: {path}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vm-dir", default="vm", help="VM directory")
    parser.add_argument(
        "--dylib",
        default="scripts/vphone_mg_idiom/vphone_mg_idiom.dylib",
        help="signed interposer dylib to trust",
    )
    parser.add_argument(
        "--pyimg4",
        default=".venv/bin/pyimg4",
        help="pyimg4 executable",
    )
    parser.add_argument(
        "--trustcache",
        default=".tools/bin/trustcache",
        help="trustcache executable",
    )
    args = parser.parse_args()

    vm_dir = Path(args.vm_dir).resolve()
    dylib = Path(args.dylib).resolve()
    pyimg4 = ensure_tool(args.pyimg4, "pyimg4")
    trustcache = ensure_tool(args.trustcache, "trustcache")

    if not dylib.exists():
        raise FileNotFoundError(dylib)

    restore_dir = find_restore_dir(vm_dir)
    tc_im4p = static_trustcache_path(restore_dir)
    fourcc = im4p_fourcc(pyimg4, tc_im4p)

    with tempfile.TemporaryDirectory(prefix="vphone-mg-tc-") as tmp:
        tmpdir = Path(tmp)
        raw = tmpdir / "static.tc"
        out = tmpdir / tc_im4p.name

        run([pyimg4, "im4p", "extract", "-i", str(tc_im4p), "-o", str(raw)])

        before = subprocess.run(
            [trustcache, "info", "-c", str(raw)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout

        cdhash = subprocess.run(
            ["ldid", "-h", str(dylib)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout
        cdhash_line = next(
            (line for line in cdhash.splitlines() if line.startswith("CDHash=")),
            "",
        )
        wanted = cdhash_line.split("=", 1)[1].strip() if cdhash_line else ""
        if not wanted:
            raise RuntimeError(f"could not read CDHash from {dylib}")

        if wanted in before:
            update_all_manifest_digests(restore_dir, tc_im4p)
            print(f"  [=] {tc_im4p}: already trusts {wanted}")
            return 0

        run([trustcache, "append", "-u", "0", str(raw), str(dylib)])

        after = subprocess.run(
            [trustcache, "info", "-c", str(raw)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout
        if wanted not in after:
            raise RuntimeError(f"trustcache append did not add {wanted}")

        run(
            [
                pyimg4,
                "im4p",
                "create",
                "-i",
                str(raw),
                "-o",
                str(out),
                "-f",
                fourcc,
                "-d",
                "1",
            ]
        )

        backup = tc_im4p.with_suffix(tc_im4p.suffix + ".bak")
        if not backup.exists():
            shutil.copy2(tc_im4p, backup)
        shutil.copy2(out, tc_im4p)

    update_all_manifest_digests(restore_dir, tc_im4p)
    print(f"  [+] {tc_im4p}: appended {wanted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
