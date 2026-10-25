"""List the data/layers entries of a PBO header: counts and sizes by kind, to compare two packages."""
import collections
import struct
import sys


def entries(path):
    with open(path, 'rb') as f:
        out = []
        while True:
            name = b''
            while True:
                c = f.read(1)
                if c == b'\0' or not c:
                    break
                name += c
            meta = f.read(20)
            method, orig, _res, _ts, size = struct.unpack('<5I', meta)
            if not name:
                if method == 0x56657273:  # 'Vers' header extension
                    while True:  # key/value strings until an empty key
                        k = b''
                        while (c := f.read(1)) not in (b'\0', b''):
                            k += c
                        if not k:
                            break
                        while (c := f.read(1)) not in (b'\0', b''):
                            pass
                    continue
                break
            out.append((name.decode('latin-1'), method, orig, size))
        return out


for path in sys.argv[1:]:
    e = entries(path)
    lay = [x for x in e if '\\layers\\' in x[0].lower() or x[0].lower().startswith('data\\layers')]
    kinds = collections.Counter()
    sizes = collections.Counter()
    for n, m, o, s in lay:
        low = n.lower()
        k = ('rvmat' if low.endswith('.rvmat') else low[-8:])
        kinds[k] += 1
        sizes[k] += s
    print(path, 'entries', len(e), 'layers', len(lay))
    for k in sorted(kinds):
        print('  ', k, kinds[k], sizes[k])
    for n, m, o, s in lay:
        if 'm_008_020' in n.lower() or 's_008_020' in n.lower() or 'p_008-020' in n.lower():
            print('   ', n, m, o, s)
