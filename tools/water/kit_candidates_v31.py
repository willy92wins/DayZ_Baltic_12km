"""Inventory of thin streams for the streambed kit (EV108 pilot): every narrow river/stream reach of the pond layer, measured
and classified, so extending the kit is one decision.

Narrow reach: wet pond-piece vertices (below their piece plane) of cls 5/6 whose 7 x 7 neighbourhood has no wet vertex farther
than 1.5 vertices from dry ground (v_streams_v31.py v4 rule), connected through native triangle edges, >= 6 vertices.
Per reach: length (longest geodesic path, m), thalweg depth (plane - terrain) p50, visible width p50/p90 (medial axis of the
native-triangle waterline, v_streams_v31.visible_width), drop (plane range), road vertices within 6 m of the reach (crossings or
roads alongside: the kit ends there or needs a culvert/bridge), wide water or sea touching it.
Class: 'irregular' when the thalweg depth p50 > 0.5 m (kit-118: 1.17 m; the smooth 5-9 m reaches measure 0.10-0.39 m, and
their width p90 overlaps the irregular ones, so width does not separate them), else 'smooth'. 'kit-ready' = irregular and
>= 60 m long; road vertices near the reach are reported (the kit tool trims ends at roads; a road crossing the middle of a
reach needs a crossing decision first).
Usage: kit_candidates_v31.py <terrain.npz> <footprint.npz> <out.json> <out.csv> <out.png>
"""
import csv, json, os, runpy, sys
from collections import deque
import numpy as np
from scipy.ndimage import label, distance_transform_edt, maximum_filter, binary_dilation

HERE = os.path.dirname(os.path.abspath(__file__))
vs = runpy.run_path(os.path.join(HERE, "v_streams_v31.py"), run_name="lib")
NATIVE = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1))


def geodesic_len(mask_rc):
    pts = set(map(tuple, mask_rc))
    def bfs(src):
        dist = {src: 0.0}; q = deque([src]); far = src
        while q:
            a = q.popleft()
            for dr, dc in NATIVE:
                b = (a[0] + dr, a[1] + dc)
                if b in pts and b not in dist:
                    dist[b] = dist[a] + (8.485 if dr and dc else 6.0); q.append(b)
                    if dist[b] > dist[far]:
                        far = b
        return far, dist[far]
    a, _ = bfs(next(iter(pts)))
    return bfs(a)[1]


def main():
    tpath, fpath, out_j, out_c, out_png = sys.argv[1:6]
    z = np.load(tpath); H = z["heights"].astype(np.float64); cls = z["cls"]
    road = z["reserve"] | z["platform"] | z["narva"]
    pl = np.load(fpath)["plane"].astype(np.float64)
    vp = np.full(H.shape, -np.inf); cp = np.where(np.isfinite(pl), pl, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            vp[dr:dr + 2047, dc:dc + 2047] = np.maximum(vp[dr:dr + 2047, dc:dc + 2047], cp)
    wet = np.isfinite(vp) & (H < vp)
    edt = distance_transform_edt(wet)
    narrow = wet & (maximum_filter(edt, size=7) <= 1.5) & np.isin(cls, (5, 6))
    kern = np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]])
    lab, n = label(narrow, kern)
    size = np.bincount(lab.ravel(), minlength=n + 1)
    wide = wet & ~narrow
    sea = (~np.isfinite(vp)) & (H < 0.75)
    vc = np.where(np.isfinite(pl), pl, np.nan)
    road6 = binary_dilation(road, np.ones((3, 3), bool))               # road vertex within one vertex (6 m)
    rows = []
    for i in range(1, n + 1):
        if size[i] < 6:
            continue
        rr, cc = np.nonzero(lab == i)
        r0, r1, c0, c1 = max(rr.min() - 3, 0), min(rr.max() + 3, 2047), max(cc.min() - 3, 0), min(cc.max() + 3, 2047)
        m = lab[r0:r1 + 1, c0:c1 + 1] == i
        wv = vs["visible_width"](H, vc, r0, r1, c0, c1)[m]
        depth = (vp - H)[rr, cc]
        ring = binary_dilation(m, np.ones((3, 3), bool), iterations=2) & ~m
        touch_wide = bool((wide[r0:r1 + 1, c0:c1 + 1] & ring).any())
        touch_sea = bool((sea[r0:r1 + 1, c0:c1 + 1] & ring).any())
        roads = int((road6[r0:r1 + 1, c0:c1 + 1] & binary_dilation(m, np.ones((3, 3), bool))).sum())
        length = geodesic_len(np.c_[rr, cc])
        irregular = bool(np.median(depth) > 0.5)
        rows.append(dict(reach=int(i), x=round(float(6 * cc.mean()), 1), z=round(float(6 * (2047 - rr.mean())), 1), vertices=int(size[i]),
                         length_m=round(length, 1), depth_p50=round(float(np.median(depth)), 2), width_p50=round(float(np.median(wv)), 1),
                         width_p90=round(float(np.percentile(wv, 90)), 1), plane_min=round(float(vp[rr, cc].min()), 3),
                         plane_max=round(float(vp[rr, cc].max()), 3), road_vertices_near=roads, touches_wide_water=touch_wide,
                         touches_sea=touch_sea, cls="irregular" if irregular else "smooth",
                         kit_ready=bool(irregular and length >= 60)))
    rows.sort(key=lambda r: (-r["kit_ready"], r["cls"] != "irregular", -r["length_m"]))
    summ = dict(reaches=len(rows), irregular=sum(r["cls"] == "irregular" for r in rows), smooth=sum(r["cls"] == "smooth" for r in rows),
                kit_ready=sum(r["kit_ready"] for r in rows), kit_ready_km=round(sum(r["length_m"] for r in rows if r["kit_ready"]) / 1000, 2),
                irregular_with_roads=sum(r["cls"] == "irregular" and r["road_vertices_near"] > 0 for r in rows),
                irregular_km=round(sum(r["length_m"] for r in rows if r["cls"] == "irregular") / 1000, 2),
                smooth_km=round(sum(r["length_m"] for r in rows if r["cls"] == "smooth") / 1000, 2))
    json.dump(dict(schema="kit-candidates-v31.v1", terrain=tpath, footprint=fpath, summary=summ, reaches=rows), open(out_j, "w", newline="\n"), indent=1)
    with open(out_c, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(rows)
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(np.where(np.isfinite(vp), 0.85, 1.0), cmap="Blues_r", extent=(0, 12288, 0, 12288), vmin=0, vmax=1.2)
    for r in rows:
        col = "red" if r["kit_ready"] else ("orange" if r["cls"] == "irregular" else "green")
        ax.plot(r["x"], r["z"], "o", ms=3 + r["length_m"] / 150, color=col, alpha=0.8)
    for x, zz, t in ((8245, 9070, "kit-118"), (8700, 11650, "kit-7")):
        ax.annotate(t, (x, zz), fontsize=8)
    ax.set_title("Thin reaches: red = kit-ready, orange = irregular with roads / short, green = smooth")
    plt.tight_layout(); plt.savefig(out_png, dpi=90)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
