"""Print the type, tags and mipmap chain (width x height, stored size, LZO flag) of PAA files."""
import struct
import sys


def mips(path):
    with open(path, 'rb') as f:
        data = f.read()
    kind = struct.unpack_from('<H', data, 0)[0]
    p, tags = 2, []
    while data[p:p + 4] == b'GGAT':
        name = data[p + 4:p + 8][::-1].decode('latin-1')
        size = struct.unpack_from('<I', data, p + 8)[0]
        tags.append(name)
        p += 12 + size
    pal = struct.unpack_from('<H', data, p)[0]
    p += 2 + 3 * pal
    out = []
    while p + 7 <= len(data):
        w, h = struct.unpack_from('<HH', data, p)
        if w == 0 and h == 0:
            break
        size = data[p + 4] | data[p + 5] << 8 | data[p + 6] << 16
        out.append((w & 0x7FFF, h, size, bool(w & 0x8000)))
        p += 7 + size
    return hex(kind), tags, out


for path in sys.argv[1:]:
    k, tags, m = mips(path)
    print(path.split('/')[-1], k, tags, len(m), 'mips:', ' '.join(f'{w}x{h}{"z" if z else ""}:{s}' for w, h, s, z in m))
