"""Extract PBO entries whose name matches a regex into a folder (uncompressed entries only). Read-only on the PBO.
Usage: pbo_extract.py FILE.pbo REGEX OUTDIR [--max 10]"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pbo_layers_census import entries  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pbo')
    ap.add_argument('regex')
    ap.add_argument('outdir')
    ap.add_argument('--max', type=int, default=10)
    a = ap.parse_args()
    rx = re.compile(a.regex, re.I)
    hits = [e for e in entries(a.pbo) if rx.search(e[0])][:a.max]
    os.makedirs(a.outdir, exist_ok=True)
    with open(a.pbo, 'rb') as f:
        for name, method, orig, size, off in hits:
            if method not in (0, 0x43707273) or (orig and orig != size):
                print(f'skip packed {name} method={method:#x} orig={orig} size={size}')
                continue
            f.seek(off)
            dst = os.path.join(a.outdir, name.replace('\\', '__'))
            with open(dst, 'wb') as o:
                o.write(f.read(size))
            print(f'{name} -> {dst} ({size} bytes)')


if __name__ == '__main__':
    main()
