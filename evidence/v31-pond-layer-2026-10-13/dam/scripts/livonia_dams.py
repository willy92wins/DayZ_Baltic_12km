"""How Livonia seats dam_stone_40: per placement, terrain under/around the dam in model axes, roadway/top/bottom heights,
and the water on each side (W-category water pieces whose roadway LOD covers points 8-30 m upstream/downstream)."""
import json, sys, os
import numpy as np
sys.path.insert(0, r"E:/DayZ-Baltic-Build/vanilla-tricks-20261013/scripts")
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from terrain import Terrain, objects, matrix
from odol_reader import ODOL

T = Terrain("enoch")
objs = objects("enoch")
dams = [o for o in objs if "dam_stone_40" in o["shape"]]
water = [o for o in objs if o["cat"] == "W"]
_rw = {}


def roadway(shape):
    """Roadway (3e15) triangles of a water piece, model coords; read from P:/ (shape path relative to P:)."""
    if shape not in _rw:
        p = "P:/" + shape.replace("\\", "/")
        tris = []
        try:
            od = ODOL.from_file(p)
            for l in od.lods:
                if abs(l.resolution - 3e15) < 1e10:
                    V = np.array([(q.x, q.y, q.z) for q in l.vertices])
                    for f in l.faces:
                        ids = list(f.vertex_indices)
                        for i in range(1, len(ids) - 1):
                            tris.append(V[[ids[0], ids[i], ids[i + 1]]])
        except Exception as e:  # noqa
            tris = []
        _rw[shape] = np.array(tris)
    return _rw[shape]


def water_at(x, z):
    """Highest water roadway surface over (x, z) among W pieces, or None; also the model name."""
    best = None
    for o in water:
        if abs(o["x"] - x) > 80 or abs(o["z"] - z) > 80:
            continue
        A, t = matrix(o)
        tris = roadway(o["shape"])
        if not len(tris):
            continue
        W = tris @ A.T + t
        for a, b, c in W:
            # barycentric in xz
            d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(d) < 1e-9:
                continue
            l1 = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / d
            l2 = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / d
            l3 = 1 - l1 - l2
            if min(l1, l2, l3) >= -1e-6:
                y = l1 * a[1] + l2 * b[1] + l3 * c[1]
                if best is None or y > best[0]:
                    best = (round(float(y), 3), os.path.basename(o["shape"]))
    return best


out = []
for k, o in enumerate(dams):
    A, t = matrix(o)
    ax, ay, az = A[:, 0], A[:, 1], A[:, 2]
    rec = dict(i=k, x=round(o["x"], 2), z=round(o["z"], 2), y=round(o["y"], 3),
               bearing_len_deg=round(float(np.degrees(np.arctan2(ax[0], ax[2]))) % 180, 1), tilt=[round(float(v), 5) for v in ay])
    xs = np.arange(-20, 20.01, 2.0)
    prof = {}
    for zl in (-2.04, 0.0, 2.04):
        P = np.array([t + xl * ax + zl * az for xl in xs])
        prof[str(zl)] = (T.y(P[:, 0], P[:, 2]) - o["y"]).round(2).tolist()   # terrain - dam origin y
    rec["terrain_minus_origin_along_x_at_z"] = prof
    # ends: terrain at the two ends vs roadway top (origin + 4.077)
    top = o["y"] + 4.077
    rec["roadway_top_y"] = round(top, 3); rec["bottom_y"] = round(o["y"] - 4.077, 3)
    for side, zl in (("minus_z", -1), ("plus_z", 1)):
        rs = []
        for dz in (6, 10, 16, 24, 32):
            P = t + zl * dz * az
            w = water_at(P[0], P[2])
            rs.append(dict(d=dz, terrain=round(float(T.y(P[0], P[2])) - o["y"], 2), water=None if w is None else round(w[0] - o["y"], 3), model=None if w is None else w[1]))
        rec[side] = rs
    # does water reach under the dam footprint?
    under = []
    for xl in (-15, -5, 0, 5, 15):
        P = t + xl * ax
        w = water_at(P[0], P[2])
        under.append(None if w is None else round(w[0] - o["y"], 3))
    rec["water_under_axis_minus_origin"] = under
    out.append(rec)
    print(json.dumps(rec))
json.dump(out, open(sys.argv[1], "w"), indent=1)
