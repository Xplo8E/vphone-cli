#!/usr/bin/env python3
"""Add LC_REEXPORT_DYLIB to a thin arm64/arm64e Mach-O with header padding."""
import argparse
import struct
import sys
from pathlib import Path

MH_MAGIC_64 = 0xFEEDFACF
LC_REEXPORT_DYLIB = 0x8000001F


def align(value, n):
    return (value + n - 1) & ~(n - 1)


def first_non_header_fileoff(data, ncmds, sizeofcmds):
    off = 32
    first = len(data)
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from('<II', data, off)
        if cmd in (0x19, 0x1):  # LC_SEGMENT_64 / LC_SEGMENT
            if cmd == 0x19:
                fileoff, filesize = struct.unpack_from('<QQ', data, off + 40)
            else:
                fileoff, filesize = struct.unpack_from('<II', data, off + 32)
            if filesize and fileoff:
                first = min(first, fileoff)
        off += cmdsize
    return first


def add_reexport(path, dylib_path):
    p = Path(path)
    data = bytearray(p.read_bytes())
    magic = struct.unpack_from('<I', data, 0)[0]
    if magic != MH_MAGIC_64:
        raise SystemExit(f'{p}: only thin 64-bit Mach-O is supported')

    ncmds, sizeofcmds = struct.unpack_from('<II', data, 16)
    header_end = 32 + sizeofcmds
    first_fileoff = first_non_header_fileoff(data, ncmds, sizeofcmds)

    encoded = dylib_path.encode() + b'\0'
    cmdsize = align(24 + len(encoded), 8)
    new_end = header_end + cmdsize
    if new_end > first_fileoff:
        raise SystemExit(
            f'{p}: not enough header padding for LC_REEXPORT_DYLIB: '
            f'need {cmdsize}, have {first_fileoff - header_end}'
        )

    # Idempotent: existing string in load commands means already added/replaced.
    load_blob = bytes(data[32:header_end])
    if encoded in load_blob:
        print(f'  [=] {p}: already references {dylib_path}')
        return

    cmd = bytearray(cmdsize)
    struct.pack_into('<II', cmd, 0, LC_REEXPORT_DYLIB, cmdsize)
    struct.pack_into('<IIII', cmd, 8, 24, 0, 0, 0)  # name offset, timestamp, current, compat
    cmd[24:24 + len(encoded)] = encoded

    data[header_end:new_end] = cmd
    struct.pack_into('<II', data, 16, ncmds + 1, sizeofcmds + cmdsize)
    p.write_bytes(data)
    print(f'  [+] {p}: added LC_REEXPORT_DYLIB {dylib_path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('binary')
    ap.add_argument('dylib_path')
    args = ap.parse_args()
    add_reexport(args.binary, args.dylib_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
