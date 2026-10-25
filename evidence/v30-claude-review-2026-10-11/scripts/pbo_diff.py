import sys, struct, hashlib, collections


def read_pbo(path):
    f = open(path, "rb")
    ents = []
    props = []

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
            while True:
                k = cstr()
                if k == "":
                    break
                props.append((k, cstr()))
            continue
        if name == "":
            break
        ents.append((name.replace(chr(92), "/"), mt, orig, size))
    data_start = f.tell()
    out = {}
    off = data_start
    for name, mt, orig, size in ents:
        f.seek(off)
        blob = f.read(size)
        out[name] = (mt, orig, size, hashlib.sha256(blob).hexdigest())
        off += size
    return props, ents, out


pa, ea, a = read_pbo(sys.argv[1])
pb, eb, b = read_pbo(sys.argv[2])
print("props A", pa)
print("props B", pb)
print("entries A", len(a), "B", len(b))
onlya = sorted(set(a) - set(b))
onlyb = sorted(set(b) - set(a))
print("only in A", len(onlya), onlya[:20])
print("only in B", len(onlyb), onlyb[:20])
changed = sorted(n for n in set(a) & set(b) if a[n][3] != b[n][3])
kinds = collections.Counter(n.rsplit(".", 1)[-1] for n in changed)
print("changed", len(changed), kinds)
for n in changed:
    if not n.endswith(".paa"):
        print("  ", n, a[n][:3], b[n][:3])
packed = [n for n in a if a[n][0] != 0]
print("A entries with nonzero packing method", len(packed), packed[:5])
packed = [n for n in b if b[n][0] != 0]
print("B entries with nonzero packing method", len(packed), packed[:5])
order_a = [e[0].replace(chr(92), "/") for e in ea]
print("A first entries", order_a[:8])

sz_diff = [n for n in changed if n.endswith(".paa") and a[n][2] != b[n][2]]
print("changed PAA with different byte size", len(sz_diff), sz_diff[:3])
for n in sz_diff[:3]:
    print("   ", n, "A", a[n][2], "B", b[n][2])
print("texHeaders same hash:", a.get("texheaders.bin", a.get("texHeaders.bin")) == b.get("texheaders.bin", b.get("texHeaders.bin")))
print([n for n in a if "texheader" in n.lower()])
