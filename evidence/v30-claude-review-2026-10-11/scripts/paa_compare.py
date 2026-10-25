"""Compare PAA headers (type, taggs, mip chain) between two world PBOs for the changed layer textures."""
import sys, struct, collections
sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])


def read_pbo(path):
    f = open(path, "rb")
    ents = []

    def cstr():
        b = bytearray()
        while True:
            c = f.read(1)
            if c in (b"\0", b""):
                return b.decode("latin1")
            b += c

    while True:
        name = cstr()
        mt, orig, res, ts, size = struct.unpack("<5I", f.read(20))
        if name == "" and mt == 0x56657273:
            while cstr() != "":
                pass
            continue
        if name == "":
            break
        ents.append((name.replace(chr(92), "/").lower(), size))
    off = f.tell()
    out = {}
    for n, s in ents:
        f.seek(off)
        out[n] = f.read(s)
        off += s
    return out


def paa_info(blob):
    typ = struct.unpack_from("<H", blob, 0)[0]
    p = 2
    tags = []
    while blob[p:p + 4] == b"GGAT":
        name = blob[p + 4:p + 8].decode("latin1")
        ln = struct.unpack_from("<I", blob, p + 8)[0]
        tags.append((name, ln, blob[p + 12:p + 12 + ln] if name in ("SFFO", "GALF", "ZIWS") else None))
        p += 12 + ln
    pal = struct.unpack_from("<H", blob, p)[0]
    p += 2 + pal * 3
    mips = []
    while p + 4 <= len(blob):
        w, h = struct.unpack_from("<HH", blob, p)
        if w == 0 and h == 0:
            break
        size = blob[p + 4] | (blob[p + 5] << 8) | (blob[p + 6] << 16)
        mips.append((w, h, size, p))
        p += 7 + size
    offs = None
    for name, ln, data in tags:
        if name == "SFFO":
            offs = [o for o in struct.unpack("<%dI" % (ln // 4), data) if o]
    return dict(type=hex(typ), tags=[t[0] for t in tags], mips=[(m[0], m[1]) for m in mips],
                mip_offsets=[m[3] for m in mips], sffo=offs, tail=len(blob) - p)


A = read_pbo(sys.argv[1])
B = read_pbo(sys.argv[2])
changed = [n for n in A if n.endswith(".paa") and A[n] != B.get(n)]
print("changed paa", len(changed))
summary = collections.Counter()
shown = 0
for n in changed:
    ia, ib = paa_info(A[n]), paa_info(B[n])
    key = []
    if ia["type"] != ib["type"]:
        key.append("type")
    if ia["mips"] != ib["mips"]:
        key.append("mipdims")
    if ia["tags"] != ib["tags"]:
        key.append("tags")
    if ia["sffo"] != ia["mip_offsets"][: len(ia["sffo"] or [])]:
        key.append("A_SFFO_mismatch")
    if ib["sffo"] != ib["mip_offsets"][: len(ib["sffo"] or [])]:
        key.append("B_SFFO_mismatch")
    summary[tuple(key)] += 1
    if key and shown < 4:
        shown += 1
        print(n, key)
        print("  A", ia)
        print("  B", ib)
print(summary)
