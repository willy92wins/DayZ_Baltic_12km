"""Census of a PBO's terrain layer data: entries by folder and extension, and the PAA header (type, size, mipmap count)
of a sample of satellite (s_*) and mask (m_*) tiles. Read-only.
Usage: pbo_layers_census.py FILE.pbo [--sample 4] [--grep layers]"""
import argparse
import collections
import re
import struct
import sys

PAA_TYPES = {0xFF01: 'DXT1', 0xFF02: 'DXT2', 0xFF03: 'DXT3', 0xFF04: 'DXT4', 0xFF05: 'DXT5', 0x4444: 'ARGB4444',
             0x1555: 'ARGB1555', 0x8888: 'ARGB8888', 0x8080: 'AI88'}


def read_cstr(f):
    b = bytearray()
    while True:
        c = f.read(1)
        if not c or c == b'\0':
            return b.decode('latin-1')
        b += c


def entries(path):
    out = []
    with open(path, 'rb') as f:
        while True:
            name = read_cstr(f)
            method, orig, _res, _ts, size = struct.unpack('<5I', f.read(20))
            if not name:
                if method == 0x56657273:          # 'Vers' header extension: key/value strings until an empty key
                    while read_cstr(f):
                        read_cstr(f)
                    continue
                break
            out.append([name, method, orig, size])
        pos = f.tell()
    for e in out:
        e.append(pos)
        pos += e[3]
    return out


def paa_header(path, offset, size):
    with open(path, 'rb') as f:
        f.seek(offset)
        blob = f.read(min(size, 1 << 16))
    typ = struct.unpack_from('<H', blob, 0)[0]
    p, tags = 2, {}
    while blob[p:p + 4] == b'GGAT':
        name = blob[p + 4:p + 8][::-1].decode('latin-1')
        ln = struct.unpack_from('<I', blob, p + 8)[0]
        tags[name] = blob[p + 12:p + 12 + ln]
        p += 12 + ln
    npal = struct.unpack_from('<H', blob, p)[0]
    p += 2 + 3 * npal
    w, h = struct.unpack_from('<HH', blob, p)
    lzo = bool(w & 0x8000)
    offs = tags.get('OFFS')
    mips = sum(1 for k in range(0, len(offs), 4) if struct.unpack_from('<I', offs, k)[0]) if offs else None
    return {'type': PAA_TYPES.get(typ, hex(typ)), 'w': w & 0x7FFF, 'h': h, 'lzo_top': lzo, 'mips': mips,
            'tags': sorted(tags)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pbo')
    ap.add_argument('--sample', type=int, default=4)
    ap.add_argument('--grep', default='')
    a = ap.parse_args()
    es = entries(a.pbo)
    by = collections.defaultdict(lambda: [0, 0])
    for name, method, orig, size, off in es:
        if a.grep and a.grep.lower() not in name.lower():
            continue
        folder = '\\'.join(name.split('\\')[:-1])
        ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
        by[(folder, ext)][0] += 1
        by[(folder, ext)][1] += size
    print(f'{a.pbo}: {len(es)} entries, {sum(e[3] for e in es) / 2**20:.1f} MiB')
    for (folder, ext), (n, s) in sorted(by.items(), key=lambda kv: -kv[1][1])[:25]:
        print(f'  {n:6d} x .{ext:6s} {s / 2**20:9.1f} MiB  {folder}')
    for pat in (r'(^|\\)s_\d+_\d+_lco\.paa$', r'(^|\\)m_\d+_\d+_lca\.paa$'):
        hits = [e for e in es if re.search(pat, e[0], re.I)]
        if not hits:
            print(f'  no {pat}')
            continue
        sizes = sorted(e[3] for e in hits)
        print(f'  {pat}: {len(hits)} tiles, size min/median/max {sizes[0] / 1024:.0f}/{sizes[len(sizes) // 2] / 1024:.0f}/'
              f'{sizes[-1] / 1024:.0f} KiB')
        step = max(1, len(hits) // a.sample)
        for e in hits[::step][:a.sample]:
            print(f'    {e[0]}: {paa_header(a.pbo, e[4], e[3])}')
    rv = [e for e in es if e[0].lower().endswith('.rvmat') and re.search(r'(^|\\)p_\d+-\d+', e[0], re.I)]
    print(f'  tile rvmats: {len(rv)}')
    if rv:
        with open(a.pbo, 'rb') as f:
            f.seek(rv[0][4])
            txt = f.read(rv[0][3])
        print(f'    first: {rv[0][0]} ({rv[0][3]} bytes, {"binarized" if txt[:4] == b"\0raP" else "text"})')
        if txt[:4] != b'\0raP':
            print('    ' + txt.decode('latin-1')[:1500].replace('\n', '\n    '))


if __name__ == '__main__':
    sys.exit(main())
