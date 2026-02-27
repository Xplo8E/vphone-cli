import struct, pathlib
v = pathlib.Path("../firmwares/firmware_patched/rootfs_work/verify")
def u32(f,o): 
    return struct.unpack_from("<I",(v/f).read_bytes(),o)[0]

print("launchd_cache_loader@0xB58 =", hex(u32("launchd_cache_loader",0xB58)), "expect 0xd503201f")
print("mobileactivationd@0x2F5F84 =", hex(u32("mobileactivationd",0x2F5F84)), "expect 0xd2800020")
print("launchd@0xD73C =", hex(u32("launchd",0xD73C)), "expect 0x14000017")
print("seputil@0x1B3F1 =", (v/"seputil").read_bytes()[0x1B3F1:0x1B3F3], "expect b'AA'")