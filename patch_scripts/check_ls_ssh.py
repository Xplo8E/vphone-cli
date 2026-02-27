import struct
import pathlib

script_dir = pathlib.Path(__file__).resolve().parent
repo_root = script_dir.parent
candidates = [
    repo_root / "_work" / "rootfs_work" / "verify_lc",
    repo_root / "firmwares" / "firmware_patched" / "rootfs_work" / "verify_lc",
]
v = next((p for p in candidates if p.exists()), candidates[0])

for n in ("launchd","launchd.bak"):
    b = (v/n).read_bytes()
    print(n, "u32@0xD73C =", hex(struct.unpack_from("<I", b, 0xD73C)[0]))
