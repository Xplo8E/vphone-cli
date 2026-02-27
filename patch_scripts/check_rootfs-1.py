import struct
import pathlib

script_dir = pathlib.Path(__file__).resolve().parent
repo_root = script_dir.parent
candidates = [
    repo_root / "_work" / "rootfs_work" / "verify",
    repo_root / "firmwares" / "firmware_patched" / "rootfs_work" / "verify",
]
v = next((p for p in candidates if p.exists()), candidates[0])

def u32(f,o): 
    return struct.unpack_from("<I",(v/f).read_bytes(),o)[0]

print("launchd_cache_loader@0xB58 =", hex(u32("launchd_cache_loader",0xB58)), "expect 0xd503201f")
print("mobileactivationd@0x2F5F84 =", hex(u32("mobileactivationd",0x2F5F84)), "expect 0xd2800020")
print("launchd@0xD73C =", hex(u32("launchd",0xD73C)), "expect 0x14000017")
print("seputil@0x1B3F1 =", (v/"seputil").read_bytes()[0x1B3F1:0x1B3F3], "expect b'AA'")
