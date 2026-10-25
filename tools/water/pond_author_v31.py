"""Pond layer v31, step S5: author one MLOD per (48 m tile, 25 mm band) from footprint.npz.

Each footprint cell gives its two native triangles, A = (NW, NE, SE) and B = (NW, SE, SW), on the exact 6 m grid
(no 1 cm overhang). LODs follow water_mesh.py:38-63: LOD 1 visual at y = F - L (pond material, lodnoshadow, normal
(0,-1,0)); 1e13 class=pond damage=no without faces; 1e15 four points at the piece bounds; 3e15 roadway, the same
triangles at y = 0 with water_ext.paa. Winding as water_mesh.py:33-37, UV local/16 (:60), origin at the tile centre
(build_water_pieces_v30.py:64) at the band level L. Name p31_<sha256(geometry)[:16]>; identical geometry shares a model.
Usage: pond_author_v31.py <footprint.npz> <out_dir> [--window x0 x1 z0 z1]   (tile-aligned window; out_dir new)
"""
import argparse, hashlib, io, json, os, sys
from collections import defaultdict
import numpy as np
sys.path.insert(0, r"C:\Users\guill\DayZ-Modding-Knowledge-Pack\tools\py3d")
import py3d
assert py3d.IS_DAYZ_FORK

PREFIX, BAND, TILE, ZTOP = "baltic_water_v30", 0.025, 48, 12282
VIS_TEX, VIS_MAT = r"dz\data\data\normalmap1_dxt5.paa", r"dz\water\ponds\data\pond_moss_1.rvmat"
ROAD_TEX = r"dz\surfaces\data\roadway\water_ext.paa"
CONFIG = ("class CfgPatches { class Baltic_Water_V30 { units[]={}; weapons[]={}; requiredVersion=0.1; "
          "requiredAddons[]={\"DZ_Water\"}; }; };\n")            # build_water_pieces_v30.py:94-95


def triangles(cells, field, origin):
    """World-native triangles of the cells, local to origin: list of 3 x (x, y_visual, z)."""
    ox, oy, oz = origin
    tris = []
    for r, c in cells:
        x0, x1, zn, zs = 6 * c, 6 * c + 6, ZTOP - 6 * r, ZTOP - 6 * r - 6
        f = field[r, c]                                       # NW, NE, SW, SE
        nw, ne, sw, se = (x0, f[0], zn), (x1, f[1], zn), (x0, f[2], zs), (x1, f[3], zs)
        for tri in ((nw, ne, se), (nw, se, sw)):
            p = [(x - ox, y - oy, z - oz) for x, y, z in tri]
            cross = (p[1][0] - p[0][0]) * (p[2][2] - p[0][2]) - (p[1][2] - p[0][2]) * (p[2][0] - p[0][0])
            if cross < 0:
                p = p[::-1]
            tris.append(p)
    return tris


def build_model(tris, bounds):
    model = py3d.P3D()
    for res in (1, 1e13, 1e15, 3e15):
        lod = py3d.LOD(); lod.resolution = res
        if res == 1e13:
            lod.properties.update({"damage": "no", "class": "pond"})
        elif res == 1e15:
            x0, z0, x1, z1 = bounds
            for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
                pt = py3d.Point(); pt.coords = (x, 0, z); lod.points.append(pt)
        else:
            visual = res == 1
            lod.facenormals.append((0, -1, 0) if visual else (0, 1, 0))
            if visual:
                lod.properties["lodnoshadow"] = "1"
            index = {}
            for tri in tris:
                face = py3d.Face(lod.points, lod.facenormals)
                face.texture = VIS_TEX if visual else ROAD_TEX
                face.material = VIS_MAT if visual else ""
                for x, y, z in tri:
                    key = (round(x, 6), round(y, 6) if visual else 0.0, round(z, 6))
                    if key not in index:
                        index[key] = len(lod.points)
                        pt = py3d.Point(); pt.coords = key; lod.points.append(pt)
                    v = py3d.Vertex(lod.points, lod.facenormals)
                    v.point_index = index[key]; v.normal_index = 0
                    v.uv = (key[0] / 16, key[2] / 16)
                    face.vertices.append(v)
                lod.faces.append(face)
        model.lods.append(lod)
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("footprint"); ap.add_argument("out")
    ap.add_argument("--window", nargs=4, type=float)
    a = ap.parse_args()
    assert not os.path.exists(a.out), "fresh output required"
    src = os.path.join(a.out, "source", PREFIX); os.makedirs(src)
    fp = np.load(a.footprint)
    plane, field = fp["plane"].astype(np.float64), fp["field"]
    cells = np.argwhere(np.isfinite(plane))
    groups = defaultdict(list)
    for r, c in cells:
        x, z = 6 * c + 3, ZTOP - 6 * r - 3
        tx, tz = int(x // TILE), int(z // TILE)
        if a.window:
            wx0, wx1, wz0, wz1 = a.window
            if not (wx0 <= tx * TILE and (tx + 1) * TILE <= wx1 and wz0 <= tz * TILE and (tz + 1) * TILE <= wz1):
                continue
        band = int(round(float(plane[r, c]) / BAND))
        assert abs(band * BAND - plane[r, c]) < 1e-4, (r, c, plane[r, c])
        groups[(tx, tz, band)].append((int(r), int(c)))
    models, instances = {}, []
    for (tx, tz, band), cl in sorted(groups.items()):
        origin = (tx * TILE + 24.0, band * BAND, tz * TILE + 24.0)
        tris = triangles(cl, field, origin)
        xs = [p[0] for t in tris for p in t]; zs = [p[2] for t in tris for p in t]
        bounds = (min(xs), min(zs), max(xs), max(zs))
        assert -24 <= bounds[0] and bounds[2] <= 24 and -24 <= bounds[1] and bounds[3] <= 24
        canon = json.dumps(sorted([[[round(v, 6) for v in p] for p in t] for t in tris]))
        name = "p31_" + hashlib.sha256(canon.encode()).hexdigest()[:16]
        if name not in models:
            path = os.path.join(src, name + ".p3d")
            build_model(tris, bounds).save(path)
            got = py3d.P3D(io.BytesIO(open(path, "rb").read()))
            assert [len(l.faces) for l in got.lods] == [len(tris), 0, 0, len(tris)], name
            vis = np.array([p.coords for p in got.lods[0].points]); road = np.array([p.coords for p in got.lods[3].points])
            assert np.allclose(np.mod(vis[:, [0, 2]], 6), 0) and (np.abs(road[:, 1]) == 0).all(), name
            models[name] = dict(name=name, triangles=len(tris), bounds_rel=list(bounds),
                                visual_y_range=[float(vis[:, 1].min()), float(vis[:, 1].max())],
                                sha256=hashlib.sha256(open(path, "rb").read()).hexdigest())
        instances.append(dict(model=f"{PREFIX}\\{name}.p3d", tile=[tx, tz], band=band, origin=list(origin), cells=len(cl),
                              ramp=bool(models[name]["visual_y_range"] != [0.0, 0.0])))
    with open(os.path.join(src, "$PBOPREFIX$"), "w", encoding="ascii", newline="\n") as f:
        f.write(PREFIX)
    with open(os.path.join(src, "config.cpp"), "w", encoding="ascii", newline="\n") as f:
        f.write(CONFIG)
    rep = dict(schema="pond-author-v31.v1", footprint_sha256=hashlib.sha256(open(a.footprint, "rb").read()).hexdigest(),
               window=a.window, instances=len(instances), models=len(models), ramp_instances=sum(i["ramp"] for i in instances),
               cells=sum(i["cells"] for i in instances), triangles=sum(m["triangles"] for m in models.values()),
               instance_list=instances, model_list=list(models.values()))
    with open(os.path.join(a.out, "pieces.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if not k.endswith("_list")}, indent=1))


if __name__ == "__main__":
    main()
