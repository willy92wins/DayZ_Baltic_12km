"""List terrain tile materials inside a PBO: count tile RVMATs and the surface textures each one references."""
import collections
import re
import struct
import sys


def entries(path):
    with open(path, "rb") as f:
        out = []
        while True:
            name = b""
            while (c := f.read(1)) != b"\0":
                name += c
            method, original, reserved, stamp, size = struct.unpack("<5I", f.read(20))
            if not name:
                if method == 0x56657273:  # 'sreV' header extension: key/value pairs until an empty key
                    while True:
                        key = b""
                        while (c := f.read(1)) != b"\0":
                            key += c
                        if not key:
                            break
                        while f.read(1) != b"\0":
                            pass
                    continue
                break
            out.append((name.decode("latin-1"), method, size))
        offset = f.tell()
    return out, offset


def main():
    path = sys.argv[1]
    items, offset = entries(path)
    tiles = []
    pos = offset
    for name, method, size in items:
        if re.search(r"layers\\p_[^\\]+\.rvmat$", name, re.I):
            tiles.append((name, pos, size, method))
        pos += size
    print("entries", len(items), "tile rvmats", len(tiles))
    per_tile = collections.Counter()
    surfaces = collections.Counter()
    with open(path, "rb") as f:
        for name, start, size, method in tiles:
            f.seek(start)
            data = f.read(size)
            found = sorted({m.lower() for m in re.findall(rb"dz\\surfaces\\data\\terrain\\([a-z0-9_]+?)_(?:ca|nopx|nohq|co)\.paa", data, re.I)})
            per_tile[len(found)] += 1
            for s in found:
                surfaces[s.decode()] += 1
    print("surfaces per tile:", dict(sorted(per_tile.items())))
    print("tiles using each surface:", surfaces.most_common())


if __name__ == "__main__":
    main()
