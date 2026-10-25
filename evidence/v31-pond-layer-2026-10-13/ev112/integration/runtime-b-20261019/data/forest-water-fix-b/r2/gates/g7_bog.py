"""G7 bog: the OSM wetland of each pilot sector is a sparse, open pine bog with tree-free moss clearings, shrubs, a few
dead trees and a transition to the forest around it (EV111 decision of 2026-10-16, product-spec P13).

Usage: python -I g7_bog.py <records.json> [--json out.json] [--free-m D]
Inputs are the records and the shared layers (layers.npz osm_wetland, terrain, footprint, sectors, Livonia reference
for model family, genus, height and scale quantiles); nothing is read from the placer's report or instances.
Livonia has no raised bog: every band below is a design value [DESIGN] unless it says Livonia.
Areas (1 m pixels, sector polygon inset 50 m as G2/G3, land only: not visible water):
  bog   bilinear osm_wetland vertex fraction >= 0.5; bd = distance into the bog on a raster padded by 110 m.
  core  bd >= 25 m.   rim_out 0 <= bd < 12.5 m.   rim_in 12.5 <= bd < 25 m.   ring: outside the bog, 0-25 m from it.
A sector is judged when its core has >= 2 ha in the analysis area; a sector with less is reported, not judged, and G7
needs at least one judged sector.
Metrics and bands (core unless named):
  trees_per_ha           [20, 80]   [DESIGN] sparse: above Livonia open land (7.4/ha), below Livonia interior p10 (136)
  pine_share_of_trees    >= 0.70    [DESIGN, orchestrator brief]
  broadleaf_share        <= 0.20    [DESIGN, orchestrator brief]
  treefree_patch_share   >= 0.30    [DESIGN, orchestrator brief] share of the core in connected patches (8-neighbour)
                                    >= 400 m2 of pixels with no tree position within --free-m (10 m [DESIGN]: set on
                                    the dev pilot so that the control n26, the same core trees scattered uniformly,
                                    falls below 0.30 (0.22) while the designed clearings stay near 0.5; at 6 m both
                                    pass, 0.62 vs 0.73)
  bush_per_ha            [20, 150]  [DESIGN] shrubs present (Livonia open land median 67.8/ha inside the band)
  dead_per_ha            [1, 15]    [DESIGN] "a few dead trees" (Livonia open land median 4.66/ha inside the band)
  pine_nn_p50_m          [1.96, 9.13]  Livonia pine-to-pine nearest neighbour p5..p90 (livonia-pines.json)
  tree_height_p50_m      <= 8.0     [DESIGN] low pine: visual model height x scale, median over the core trees
  low_scale_share        >= 0.95    [DESIGN] core pines with scale <= the model's Livonia p30 (+1e-4)
  contrast_trees_per_ha  ring - core >= 60  [DESIGN] the bog reads as a different biome from the forest around it
  treefree_patch_share_full >= 0.30 [orchestrator brief: "30 % of the bog area"] the same measure over the whole bog
                         of the analysis area (core + rims), r2 after EV111 review 1: the brief asks it of the bog, not
                         only of its core (the rims are ~60 % of the bog). Over the whole bog the trees/ha, pine and
                         broadleaf shares and the height p50 are reported (key "full"), not judged.
  transition t_out, t_in (rim density - core) / (ring - core): t_out in [0.40, 1.20], t_in in [0.00, 0.60],
                         t_out - t_in >= 0.20  [DESIGN] a gradual drop into the bog, not a cut (placer: smoothstep over
                         25 m, expected t_out ~0.8, t_in ~0.2)
Prints one line per metric and PASS or FAIL last; exit 1 on FAIL.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate_common as GC  # noqa: E402

PAD, TRANS = 110, 25.0
PINES = GC.E / "ev111-wip/forest/bog/livonia-pines.json"
BANDS = {"trees_per_ha": (20.0, 80.0), "pine_share_of_trees": (0.70, None), "broadleaf_share_of_trees": (None, 0.20),
         "treefree_patch_share": (0.30, None), "treefree_patch_share_full": (0.30, None), "bush_per_ha": (20.0, 150.0), "dead_per_ha": (1.0, 15.0),
         "pine_nn_p50_m": None, "tree_height_p50_m": (None, 8.0), "low_scale_share": (0.95, None),
         "contrast_trees_per_ha": (60.0, None), "t_out": (0.40, 1.20), "t_in": (0.0, 0.60), "t_out_minus_t_in": (0.20, None)}
MIN_CORE_HA = 2.0
PATCH_M2 = 400.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("--json")
    ap.add_argument("--free-m", type=float, default=10.0)
    a = ap.parse_args()
    lp = json.loads(PINES.read_text(encoding="utf-8"))
    p5, _, _, p90 = lp["nn_pine_to_pine_m_p1_p5_p50_p90"][1], None, None, lp["nn_pine_to_pine_m_p1_p5_p50_p90"][3]
    bands = dict(BANDS, pine_nn_p50_m=(p5, p90))
    ref = json.loads(GC.REFERENCE.read_text(encoding="utf-8"))
    models = ref["models"]
    secs = json.loads(GC.SECTORS.read_text(encoding="utf-8"))["sectors"]
    t = np.load(GC.TERRAIN)
    H = t["heights"].astype(np.float64)
    plane = np.load(GC.FOOTPRINT)["plane"]
    recs = GC.load_records(a.records)
    if any(r["model"] not in models for r in recs):
        print("FAIL unknown models")
        print("G7 FAIL")
        return 1
    P = np.array([r["matrix"][9:12] for r in recs], float)
    Mx = np.array([r["matrix"][0:3] for r in recs], float)
    scale = np.linalg.norm(Mx, axis=1)
    names = [r["model"] for r in recs]
    fam = np.array([models[nm]["family"] for nm in names])
    genus = np.array([models[nm]["genus"] or "" for nm in names])
    height = np.array([models[nm]["height"] for nm in names]) * scale
    q30 = np.array([float(np.interp(30, models[nm]["scale_levels"], models[nm]["scale_q"])) for nm in names])
    tree = np.isin(fam, ["conifer", "broadleaf"])
    pine = genus == "pinussylvestris"
    ok_all, judged_any, dump = True, False, {}
    for sec in secs:
        poly = np.asarray(sec["polygon_xz"], float)
        x0, z0 = int(np.floor(poly[:, 0].min())), int(np.floor(poly[:, 1].min()))
        x1, z1 = int(np.ceil(poly[:, 0].max())), int(np.ceil(poly[:, 1].max()))
        Hh, Ww = z1 - z0, x1 - x0
        Xp, Zp = np.meshgrid(x0 - PAD + np.arange(Ww + 2 * PAD) + 0.5, z1 + PAD - np.arange(Hh + 2 * PAD) - 0.5)
        bog_p = GC.wetland_fraction(Xp, Zp) >= 0.5
        sl = (slice(PAD, PAD + Hh), slice(PAD, PAD + Ww))
        bog = bog_p[sl]
        bd = (ndimage.distance_transform_edt(bog_p) - 0.5)[sl]
        od = (ndimage.distance_transform_edt(~bog_p) - 0.5)[sl]
        X, Z = Xp[sl], Zp[sl]
        h = GC.h_planar(H, X, Z)
        rr = np.clip(np.floor((GC.ZTOP - Z) / 6).astype(int), 0, GC.N - 2)
        cc = np.clip(np.floor(X / 6).astype(int), 0, GC.N - 2)
        pl = plane[rr, cc]
        land = ~((np.isfinite(pl) & (h < np.nan_to_num(pl, nan=-1e9))) | (h < 0.75))
        area = GC.in_poly(X, Z, poly) & (GC.poly_edge_dist(X, Z, poly) >= GC.INSET) & land
        core = area & bog & (bd >= TRANS)
        rim_o = area & bog & (bd < TRANS / 2)
        rim_i = area & bog & (bd >= TRANS / 2) & (bd < TRANS)
        ring = area & ~bog & (od < TRANS)
        ha = lambda m: float(m.sum()) / 1e4  # noqa: E731
        sel = GC.in_poly(P[:, 0], P[:, 2], poly)
        ii = np.clip(np.floor(z1 - P[:, 2]).astype(int), 0, Hh - 1)
        jj = np.clip(np.floor(P[:, 0] - x0).astype(int), 0, Ww - 1)

        def at(mask):
            return sel & mask[ii, jj]
        res = {"bog_ha": ha(area & bog), "core_ha": ha(core), "rim_out_ha": ha(rim_o), "rim_in_ha": ha(rim_i), "ring_ha": ha(ring)}
        print(f"== {sec['name']}: bog {res['bog_ha']:.2f} ha in the analysis area, core {res['core_ha']:.2f}, "
              f"rim {res['rim_out_ha']:.2f} + {res['rim_in_ha']:.2f}, forest ring {res['ring_ha']:.2f} ha")
        if res["core_ha"] < MIN_CORE_HA:
            print(f"  not judged: core {res['core_ha']:.2f} ha < {MIN_CORE_HA} ha")
            dump[sec["name"]] = dict(res, judged=False)
            continue
        judged_any = True
        c = at(core)
        nt = int((c & tree).sum())
        v = {"trees_per_ha": nt / res["core_ha"],
             "pine_share_of_trees": float((c & tree & pine).sum()) / nt if nt else None,
             "broadleaf_share_of_trees": float((c & (fam == "broadleaf")).sum()) / nt if nt else None,
             "bush_per_ha": float((c & (fam == "bush")).sum()) / res["core_ha"],
             "dead_per_ha": float((c & (fam == "dead")).sum()) / res["core_ha"],
             "tree_height_p50_m": float(np.median(height[c & tree])) if nt else None,
             "low_scale_share": float((scale[c & pine] <= q30[c & pine] + 1e-4).mean()) if (c & pine).sum() else None}
        # tree-free moss patches: every tree of the sector counts as an obstacle
        tp = P[sel & tree][:, [0, 2]]
        kd = cKDTree(tp) if len(tp) else None

        def treefree(m):
            if kd is not None:
                dist = kd.query(np.c_[X[m], Z[m]], distance_upper_bound=a.free_m + 1)[0]
                free = np.zeros(m.shape, bool)
                free[m] = dist >= a.free_m
            else:
                free = m.copy()
            lab, n = ndimage.label(free, structure=np.ones((3, 3)))
            sizes = ndimage.sum(np.ones(free.shape), lab, index=np.arange(1, n + 1)) if n else np.zeros(0)
            return float(sizes[sizes >= PATCH_M2].sum()) / max(int(m.sum()), 1), int((sizes >= PATCH_M2).sum())
        v["treefree_patch_share"], res["treefree_patches_ge_400m2"] = treefree(core)
        full = area & bog
        v["treefree_patch_share_full"], res["treefree_patches_ge_400m2_full"] = treefree(full)
        cf = at(full)
        nf = int((cf & tree).sum())
        res["full"] = {"trees_per_ha": nf / max(res["bog_ha"], 1e-9),
                       "pine_share_of_trees": float((cf & tree & pine).sum()) / nf if nf else None,
                       "broadleaf_share_of_trees": float((cf & (fam == "broadleaf")).sum()) / nf if nf else None,
                       "tree_height_p50_m": float(np.median(height[cf & tree])) if nf else None,
                       "treefree_patch_share": v["treefree_patch_share_full"]}
        pc = c & pine
        if pc.sum() >= 20:
            allp = P[sel & pine][:, [0, 2]]
            d2 = cKDTree(allp).query(P[pc][:, [0, 2]], k=2)[0][:, 1]
            v["pine_nn_p50_m"] = float(np.median(d2))
        else:
            v["pine_nn_p50_m"] = None
        dens = {k: float((at(m) & tree).sum()) / max(ha(m), 1e-9) for k, m in (("ring", ring), ("rim_out", rim_o), ("rim_in", rim_i))}
        res["trees_per_ha_by_zone"] = dict(dens, core=v["trees_per_ha"])
        con = dens["ring"] - v["trees_per_ha"]
        v["contrast_trees_per_ha"] = con
        v["t_out"] = (dens["rim_out"] - v["trees_per_ha"]) / con if con > 1e-9 else None
        v["t_in"] = (dens["rim_in"] - v["trees_per_ha"]) / con if con > 1e-9 else None
        v["t_out_minus_t_in"] = v["t_out"] - v["t_in"] if v["t_out"] is not None else None
        ok = True
        for k, (lo, hi) in bands.items():
            val = v[k]
            good = val is not None and (lo is None or val >= lo) and (hi is None or val <= hi)
            ok &= good
            print(f"  {k:26s} {val if val is None else round(val, 4)!s:>10} [{lo}, {hi}] {'PASS' if good else 'FAIL'}")
        print(f"  zones trees/ha: {({k: round(x, 1) for k, x in res['trees_per_ha_by_zone'].items()})}; "
              f"tree-free patches >= 400 m2: core {res['treefree_patches_ge_400m2']}, whole bog {res['treefree_patches_ge_400m2_full']}")
        print(f"  whole bog (reported, not judged except the tree-free share): "
              f"{({k: (None if x is None else round(x, 4)) for k, x in res['full'].items()})}")
        print(f"  {sec['name']} G7: {'PASS' if ok else 'FAIL'}")
        ok_all &= ok
        dump[sec["name"]] = dict(res, judged=True, values=v, ok=bool(ok), bands={k: list(b) for k, b in bands.items()})
    if not judged_any:
        ok_all = False
        print("  FAIL no sector with a judged bog core")
    if a.json:
        Path(a.json).write_text(json.dumps({"free_m": a.free_m, "sectors": dump}, indent=1) + "\n", encoding="utf-8")
    print(f"G7 {'PASS' if ok_all else 'FAIL'}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
