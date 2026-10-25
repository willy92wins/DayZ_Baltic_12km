"""List the mipmap chain of PAA entries inside a PBO (width, height, LZO flag, stored bytes), and decode each mip's
mean colour when it is DXT1 (LZO1X decompressed in pure Python). Read-only.
Usage: paa_mips.py FILE.pbo REGEX [--max 2]"""
import argparse
import os
import re
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from pbo_layers_census import entries  # noqa: E402


def lzo1x_decompress(src, out_len):
    """Minimal LZO1X decompressor (as used by PAA mipmaps), a direct translation of the reference lzo1x_d.ch."""
    dst = bytearray()
    ip = 0
    t = 0
    if src[0] > 17:
        t = src[0] - 17
        ip = 1
        dst += src[ip:ip + t]
        ip += t
        state = 'match_next_read' if t < 4 else 'first_literal_run'
    else:
        state = 'loop_top'
    while True:
        if state == 'loop_top':
            t = src[ip]
            ip += 1
            if t >= 16:
                state = 'match'
                continue
            if t == 0:
                while src[ip] == 0:
                    t += 255
                    ip += 1
                t += 15 + src[ip]
                ip += 1
            t += 3
            dst += src[ip:ip + t]
            ip += t
            state = 'first_literal_run'
            continue
        if state == 'first_literal_run':
            t = src[ip]
            ip += 1
            if t >= 16:
                state = 'match'
                continue
            m_pos = len(dst) - (1 + 0x0800) - (t >> 2) - (src[ip] << 2)
            ip += 1
            for _ in range(3):
                dst.append(dst[m_pos])
                m_pos += 1
            state = 'match_done'
            continue
        if state == 'match_next_read':
            t = src[ip]
            ip += 1
            state = 'match'
            continue
        if state == 'match':
            if t >= 64:
                m_pos = len(dst) - 1 - ((t >> 2) & 7) - (src[ip] << 3)
                ip += 1
                n = (t >> 5) - 1 + 2
            elif t >= 32:
                t &= 31
                if t == 0:
                    while src[ip] == 0:
                        t += 255
                        ip += 1
                    t += 31 + src[ip]
                    ip += 1
                n = t + 2
                d = src[ip] | (src[ip + 1] << 8)
                ip += 2
                m_pos = len(dst) - 1 - (d >> 2)
                t = d
            elif t >= 16:
                m_pos = len(dst) - ((t & 8) << 11)
                t &= 7
                if t == 0:
                    while src[ip] == 0:
                        t += 255
                        ip += 1
                    t += 7 + src[ip]
                    ip += 1
                n = t + 2
                d = src[ip] | (src[ip + 1] << 8)
                ip += 2
                m_pos -= d >> 2
                if m_pos == len(dst):
                    return bytes(dst), ip       # end of stream
                m_pos -= 0x4000
                t = d
            else:
                m_pos = len(dst) - 1 - (t >> 2) - (src[ip] << 2)
                ip += 1
                n = 2
            for _ in range(n):
                dst.append(dst[m_pos])
                m_pos += 1
            state = 'match_done'
        if state == 'match_done':
            t = src[ip - 2] & 3
            if t == 0:
                state = 'loop_top'
                continue
            dst += src[ip:ip + t]
            ip += t
            state = 'match_next_read'


def dxt1_mean(data, w, h):
    blocks = np.frombuffer(data[:(max(w, 4) // 4) * (max(h, 4) // 4) * 8], dtype=np.uint8).reshape(-1, 8)
    c0 = blocks[:, 0].astype(np.uint32) | (blocks[:, 1].astype(np.uint32) << 8)
    c1 = blocks[:, 2].astype(np.uint32) | (blocks[:, 3].astype(np.uint32) << 8)

    def rgb(c):
        return np.stack([((c >> 11) & 31) * 255 / 31, ((c >> 5) & 63) * 255 / 63, (c & 31) * 255 / 31], axis=1)
    return ((rgb(c0) + rgb(c1)) / 2).mean(axis=0).round(1).tolist()


def mips(path, off, size):
    with open(path, 'rb') as f:
        f.seek(off)
        blob = f.read(size)
    typ = struct.unpack_from('<H', blob, 0)[0]
    p = 2
    while blob[p:p + 4] == b'GGAT':
        p += 12 + struct.unpack_from('<I', blob, p + 8)[0]
    p += 2 + 3 * struct.unpack_from('<H', blob, p)[0]
    out = []
    while p + 4 <= len(blob):
        w, h = struct.unpack_from('<HH', blob, p)
        if w == 0 and h == 0:
            break
        n = blob[p + 4] | (blob[p + 5] << 8) | (blob[p + 6] << 16)
        data = blob[p + 7:p + 7 + n]
        lzo = bool(w & 0x8000)
        w &= 0x7FFF
        row = {'w': w, 'h': h, 'lzo': lzo, 'bytes': n}
        if typ == 0xFF01:
            raw_len = max(w, 4) * max(h, 4) // 2
            try:
                raw = lzo1x_decompress(data, raw_len)[0] if lzo else data
                row['raw_ok'] = len(raw) == raw_len
                row['mean_rgb'] = dxt1_mean(raw, w, h)
            except Exception as e:                     # noqa: BLE001
                row['decode_error'] = repr(e)[:60]
        out.append(row)
        p += 7 + n
    return typ, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pbo')
    ap.add_argument('regex')
    ap.add_argument('--max', type=int, default=2)
    a = ap.parse_args()
    rx = re.compile(a.regex, re.I)
    for name, method, orig, size, off in [e for e in entries(a.pbo) if rx.search(e[0])][:a.max]:
        typ, ms = mips(a.pbo, off, size)
        print(f'{name} type={typ:#06x}')
        for m in ms:
            print(f'   {m}')


if __name__ == '__main__':
    main()
