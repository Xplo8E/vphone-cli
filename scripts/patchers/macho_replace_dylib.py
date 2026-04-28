#!/usr/bin/env python3
"""Replace an existing Mach-O dylib path string in-place."""
import argparse
import sys
from pathlib import Path


def replace(binary, old_path, new_path):
    old = old_path.encode() + b'\0'
    new = new_path.encode() + b'\0'
    if len(new) > len(old):
        raise SystemExit(f'replacement path too long: {new_path} > {old_path}')
    p = Path(binary)
    data = p.read_bytes()
    count = data.count(old)
    if count == 0:
        if new in data:
            print(f'  [=] {p}: already uses {new_path}')
            return
        raise SystemExit(f'{old_path} not found in {p}')
    if count != 1:
        raise SystemExit(f'expected one {old_path}, found {count}')
    padded = new + b'\0' * (len(old) - len(new))
    p.write_bytes(data.replace(old, padded, 1))
    print(f'  [+] {p}: {old_path} -> {new_path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('binary')
    ap.add_argument('old_path')
    ap.add_argument('new_path')
    args = ap.parse_args()
    replace(args.binary, args.old_path, args.new_path)
    return 0

if __name__ == '__main__':
    sys.exit(main())
