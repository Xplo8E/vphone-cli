import struct, pathlib
v = pathlib.Path("../firmwares/firmware_patched/rootfs_work/verify_lc")
for n in ("launchd","launchd.bak"):
    b = (v/n).read_bytes()
    print(n, "u32@0xD73C =", hex(struct.unpack_from("<I", b, 0xD73C)[0]))