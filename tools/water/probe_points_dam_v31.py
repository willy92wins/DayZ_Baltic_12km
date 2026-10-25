"""Engine probe points for dam_v31 sites (CSV 'id;x 0 z' for missions/BalticBridgeProbeV2, JSON with one classification
per point, judged by eval_dam_probe_v31.py). Per site, along the chain every 4 m from the first to the last piece end
(inset 2 m):
  crest   on the axis: expect_roadway_y = highest roadway triangle of the staged records (dam_stone_40 roadway LOD read
          from its ODOL, placed with each record matrix) under the point, so the ramps into the 6.8 m spillway notch are
          exact (the two-height approximation of round 2 was 0.059-0.078 m off at 4 points);
  up      3, 6 and 12 m upstream of the axis;
  shelf   4 and 9 m downstream (old bed left dry by the cut);
  sea     first point downstream with terrain < 0.5 m outside the footprint, then +2, +10 and +20 m;
  ends    2 m beyond each free end on the axis.
Every point carries the same two classes, computed from the final terrain and footprint (never from its kind):
  pond_class  'wet'  footprint cell present and plane - terrain >= POND_BAND (pond water at the plane expected);
              'none' no footprint cell, or plane - terrain <= -POND_BAND (no pond water);   'edge' otherwise (unjudged);
  tide_class  'always_sea' terrain < TIDE_LOW - TIDE_BAND (sea at every modelled tide), 'never_sea' terrain > TIDE_HIGH +
              TIDE_BAND, else 'tidal'; the evaluator resolves 'tidal' against the sea level the probe itself measures.
A pond-wet point on terrain below TIDE_HIGH is refused here: pond water over the engine sea (two colours; the 11-10 rule
keeps pond beds >= 1.0 m, the highest modelled tide).
Usage: probe_points_dam_v31.py <dam-report.json> <records.json> <terrain.npz> <footprint.npz> <points.csv> <points.json>"""
import json, os, sys
from collections import Counter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dam_v31 as D
from odol_reader import ODOL          # dam_v31 put the skill's scripts folder on sys.path

POND_BAND, TIDE_LOW, TIDE_HIGH, TIDE_BAND = 0.10, 0.5, 1.0, 0.05


def roadway_triangles(recs):
    od = ODOL.from_file(D.P3D)
    rw = [l for l in od.lods if l is not None and abs(l.resolution - 3e15) <= 3e15 * 1e-6]
    if len(rw) != 1 or od.lod_errors:
        raise SystemExit("probe_points_dam_v31: refused: dam_stone_40 needs exactly one roadway LOD and no LOD error")
    V = np.array([(p.x, p.y, p.z) for p in rw[0].vertices])
    tri = np.array([V[[f.vertex_indices[0], f.vertex_indices[i], f.vertex_indices[i + 1]]]
                    for f in rw[0].faces for i in range(1, len(f.vertex_indices) - 1)])
    out = []
    for r in recs:
        m = np.array(r["matrix"])
        out.append(tri @ m[:9].reshape(3, 3) + m[9:12])
    return np.concatenate(out)


def road_at(T, x, z):
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    d = (b[:, 2] - c[:, 2]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 2] - c[:, 2])
    ok = np.abs(d) > 1e-9
    d = np.where(ok, d, 1.0)
    w0 = ((b[:, 2] - c[:, 2]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (z - c[:, 2])) / d
    w1 = ((c[:, 2] - a[:, 2]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (z - c[:, 2])) / d
    w2 = 1.0 - w0 - w1
    inside = ok & (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
    if not inside.any():
        return None
    y = w0 * a[:, 1] + w1 * b[:, 1] + w2 * c[:, 1]
    return float(y[inside].max())


def main():
    rep_p, rec_p, tp, fpp, csv_p, json_p = sys.argv[1:7]
    rep = json.load(open(rep_p)); H = np.load(tp)["heights"].astype(np.float64)
    plane = np.load(fpp)["plane"].astype(np.float64)
    recs = [r for r in json.load(open(rec_p)) if r["model"] == D.MODEL]
    pts = []

    def cell_plane(x, z):
        v = plane[int((D.ZTOP - z) // 6), int(x // 6)]
        return None if not np.isfinite(v) else float(v)

    def add(site, kind, x, z, tris, **kw):
        t = float(D.height(H, x, z)); p = cell_plane(x, z)
        pond = "none" if p is None or p - t <= -POND_BAND else ("wet" if p - t >= POND_BAND else "edge")
        tide = "always_sea" if t < TIDE_LOW - TIDE_BAND else ("never_sea" if t > TIDE_HIGH + TIDE_BAND else "tidal")
        if pond == "wet" and t < TIDE_HIGH - 1e-3:
            raise SystemExit(f"probe_points_dam_v31: refused: pond water over possible sea at ({x:.2f}, {z:.2f}): terrain {t:.3f}")
        if kind == "sea" and pond != "none":
            raise SystemExit(f"probe_points_dam_v31: refused: sea point in the pond footprint at ({x:.2f}, {z:.2f})")
        ry = road_at(tris, x, z) if kind == "crest" else None
        if kind == "crest" and ry is None:
            raise SystemExit(f"probe_points_dam_v31: refused: crest point ({x:.2f}, {z:.2f}) has no roadway triangle")
        pts.append(dict(id=len(pts), site=site, kind=kind, x=round(float(x), 3), z=round(float(z), 3),
                        terrain_y=round(t, 4), plane=None if p is None else round(p, 4), pond_class=pond, tide_class=tide,
                        cell_in_footprint=p is not None, expect_roadway_y=None if ry is None else round(ry, 4), **kw))

    for s in rep["sites"]:
        srecs = [r for r in recs if r["site"] == s["id"]]
        if not srecs:
            raise SystemExit(f"probe_points_dam_v31: refused: no records for {s['id']}")
        tris = roadway_triangles(srecs)
        ax, _, az = D.axes(s["bearing"])
        u = np.array([ax[0], ax[2]]); n = np.array([az[0], az[2]]) * s["downstream"]
        ctr = np.mean(np.array(s["pieces"]), axis=0)
        a0, a1 = s["chain_along"]
        for a in np.arange(a0 + 2.0, a1 - 1.99, 4.0):
            q = ctr + a * u
            add(s["id"], "crest", *q, tris, along=round(float(a), 2))
            for d in (3.0, 6.0, 12.0):
                add(s["id"], "up", *(q - d * n), tris, along=round(float(a), 2), offset=-d)
            for d in (4.0, 9.0):
                add(s["id"], "shelf", *(q + d * n), tris, along=round(float(a), 2), offset=d)
            for d in np.arange(2.0, 60.0, 0.5):
                p = q + d * n
                if D.height(H, *p) < TIDE_LOW and cell_plane(*p) is None:
                    for e in (0.0, 2.0, 10.0, 20.0):
                        add(s["id"], "sea", *(q + (d + e) * n), tris, along=round(float(a), 2), offset=round(float(d + e), 2))
                    break
        for a in (a0 - 2.0, a1 + 2.0):
            add(s["id"], "ends", *(ctr + a * u), tris, along=round(float(a), 2))
    with open(csv_p, "w", newline="\n") as f:
        for p in pts:
            f.write(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n")
    with open(json_p, "w", newline="\n") as f:
        json.dump(dict(schema="dam-probe-points.v2", bands=dict(POND_BAND=POND_BAND, TIDE_LOW=TIDE_LOW, TIDE_HIGH=TIDE_HIGH,
                                                                   TIDE_BAND=TIDE_BAND),
                       inputs=dict(report=rep_p, records=rec_p, terrain=tp, footprint=fpp), points=pts), f, indent=1)
    print(len(pts), dict(Counter(p["kind"] for p in pts)), dict(Counter((p["pond_class"], p["tide_class"]) for p in pts)))


if __name__ == "__main__":
    main()
