"""Dump model-space bounding boxes of every water piece in the deployed water PBO to an npz table."""
import struct, sys, time
import numpy as np

sys.path.insert(0, r"C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts")
from odol_reader import ODOL  # noqa: E402

WATER = r"P:/Mods/@DayZ_Baltic_EV95_WideBankPreviewV1/Addons/baltic_water_v30.pbo"
OUT = r"E:/DayZ-Baltic-Build/v30-water-two-colour-fix-20261011/water-piece-bbox.npz"


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
        ents.append((name, size))
    off = f.tell()
    for n, s in ents:
        f.seek(off)
        yield n, f.read(s)
        off += s


names, mins, maxs = [], [], []
t = time.time()
for name, data in read_pbo(WATER):
    if not name.lower().endswith(".p3d"):
        continue
    mi = ODOL.from_bytes(data).model_info
    names.append(("baltic_water_v30\\" + name.replace("/", "\\")).lower())
    mins.append((mi.bbox_min.x, mi.bbox_min.y, mi.bbox_min.z))
    maxs.append((mi.bbox_max.x, mi.bbox_max.y, mi.bbox_max.z))
np.savez(OUT, names=np.array(names), bbox_min=np.array(mins, np.float64), bbox_max=np.array(maxs, np.float64))
print(len(names), "models in %.1fs" % (time.time() - t))
sz = np.array(maxs) - np.array(mins)
print("size x/z quantiles", np.round(np.quantile(sz[:, 0], [0, .5, 1]), 2), np.round(np.quantile(sz[:, 2], [0, .5, 1]), 2), "y span max", round(float(sz[:, 1].max()), 3))
