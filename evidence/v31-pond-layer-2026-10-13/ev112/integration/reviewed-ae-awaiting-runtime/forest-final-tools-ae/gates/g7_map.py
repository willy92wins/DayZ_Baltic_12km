"""Diagnostic map extension of the original r2 bog contract. All dry bog pixels,
including forest-floor texture, are judged. No wooded-bog exemption. All original
r2 density, clearings, transition and contrast bands remain unchanged.
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
import gcfg  # noqa: E402
import glib  # noqa: E402

BANDS = {"trees_per_ha": (20.0, 80.0), "pine_share_of_trees": (0.70, None), "broadleaf_share_of_trees": (None, 0.20),
         "treefree_patch_share": (0.30, None), "treefree_patch_share_full": (0.30, None), "bush_per_ha": (20.0, 150.0),
         "dead_per_ha": (1.0, 15.0), "pine_nn_p50_m": None, "tree_height_p50_m": (None, 8.0), "low_scale_share": (0.95, None),
         "contrast_trees_per_ha": (60.0, None), "t_out": (0.40, 1.20), "t_in": (0.0, 0.60), "t_out_minus_t_in": (0.20, None)}
RING_KEYS = ("contrast_trees_per_ha", "t_out", "t_in", "t_out_minus_t_in")
PAD, TRANS, MIN_CORE_HA, MIN_WOODED_HA, PATCH_M2 = 110, 25.0, 2.0, 2.0, 400.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("rasters")
    ap.add_argument("out")
    ap.add_argument("--livonia-bands", required=True)
    ap.add_argument("--free-m", type=float, default=10.0)
    ap.add_argument("--bbox")
    a = ap.parse_args()
    lp = json.loads(gcfg.PINES.read_text(encoding="utf-8"))["nn_pine_to_pine_m_p1_p5_p50_p90"]
    bands = dict(BANDS, pine_nn_p50_m=(lp[1], lp[3]))
    free_max = json.loads(Path(a.livonia_bands).read_text(encoding="utf-8"))["agreement"]["free10"]["max"]
    MR = glib.MapRecords(a.records)
    mods = MR.ref["models"]
    R = glib.Rasters(a.rasters)
    bog1 = R.big("bog1m")
    slot1 = R.big("slot1m")
    ws1 = R.big("wsea1m")
    scale = np.linalg.norm(MR.m[:, 0:3], axis=1)
    height = np.array([mods[nm]["height"] if nm in mods else 0.0 for nm in MR.names]) * scale
    q30 = np.array([float(np.interp(30, mods[nm]["scale_levels"], mods[nm]["scale_q"])) if nm in mods else 0.0 for nm in MR.names])
    bbox = [float(v) for v in a.bbox.split(",")] if a.bbox else None
    if bbox:
        i0, i1, j0, j1 = int(gcfg.MAP - bbox[3]), int(gcfg.MAP - bbox[1]), int(bbox[0]), int(bbox[2])
        sub = np.zeros(bog1.shape, bool)
        sub[i0:i1, j0:j1] = bog1[i0:i1, j0:j1]
        lab, n = ndimage.label(sub)
    else:
        lab, n = ndimage.label(np.asarray(bog1))
    objs = ndimage.find_objects(lab)
    out, judged_any, ok_all = [], False, True
    for k, sl in enumerate(objs):
        if sl is None:
            continue
        if (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start) < 20000:   # cannot hold a 2 ha core
            continue
        i0, i1 = sl[0].start - PAD, sl[0].stop + PAD
        j0, j1 = sl[1].start - PAD, sl[1].stop + PAD
        comp = glib_window(lab, i0, i1, j0, j1, 0) == k + 1
        land = glib_window(ws1, i0, i1, j0, j1, 3) == 0
        yy_, xx_ = np.mgrid[i0:i1, j0:j1]
        nv = R.narva[np.clip(((gcfg.MAP - yy_ - 0.5) // 5).astype(int), 0, glib.NB - 1), np.clip((xx_ // 5).astype(int), 0, glib.NB - 1)]
        land &= ~nv
        slot = glib_window(slot1, i0, i1, j0, j1, 255)
        bd = ndimage.distance_transform_edt(comp) - 0.5
        od = ndimage.distance_transform_edt(~comp) - 0.5
        openb = comp & land
        woodb = np.zeros(comp.shape, bool)
        core_o, core_w = openb & (bd >= TRANS), woodb & (bd >= TRANS)
        ha = lambda m_: float(m_.sum()) / 1e4  # noqa: E731
        if ha(core_o) < MIN_CORE_HA and ha(core_w) < MIN_WOODED_HA:
            continue
        X0, Z1 = j0, gcfg.MAP - i0
        ids = MR.select(X0, gcfg.MAP - i1, j1, Z1)
        px, pz = MR.x[ids], MR.z[ids]
        ii = np.clip(np.floor(Z1 - pz).astype(int), 0, i1 - i0 - 1)
        jj = np.clip(np.floor(px - X0).astype(int), 0, j1 - j0 - 1)
        fam, tree, pine = MR.fam[ids], MR.tree[ids], MR.pine[ids]
        kd = cKDTree(np.c_[px[tree], pz[tree]]) if tree.any() else None

        def at(mask_):
            return mask_[ii, jj]

        def treefree(m_):
            if kd is not None:
                yy, xx = np.nonzero(m_)
                dist = kd.query(np.c_[X0 + xx + 0.5, Z1 - yy - 0.5], distance_upper_bound=a.free_m + 1)[0]
                free = np.zeros(m_.shape, bool)
                free[yy, xx] = dist >= a.free_m
            else:
                free = m_.copy()
            lb, nn_ = ndimage.label(free, structure=np.ones((3, 3)))
            szs = ndimage.sum(np.ones(free.shape), lb, index=np.arange(1, nn_ + 1)) if nn_ else np.zeros(0)
            return float(szs[szs >= PATCH_M2].sum()) / max(int(m_.sum()), 1)
        ys, xs = np.nonzero(comp)
        rec = {"component": k + 1, "centre_xz": [round(float(X0 + xs.mean()), 1), round(float(Z1 - ys.mean()), 1)],
               "bog_ha": ha(comp & land), "open_ha": ha(openb), "wooded_ha": ha(woodb), "open_core_ha": ha(core_o), "wooded_core_ha": ha(core_w)}
        ring = land & ~comp & (od < TRANS)
        rec["ring_forest_share"] = float((slot[ring] == 1).mean()) if ring.any() else 0.0
        bog_ok = True
        if ha(core_o) >= MIN_CORE_HA:
            c = at(core_o)
            nt = int((c & tree).sum())
            v = {"trees_per_ha": nt / ha(core_o),
                 "pine_share_of_trees": float((c & tree & pine).sum()) / nt if nt else None,
                 "broadleaf_share_of_trees": float((c & (fam == 1)).sum()) / nt if nt else None,
                 "bush_per_ha": float((c & (fam == 2)).sum()) / ha(core_o), "dead_per_ha": float((c & (fam == 3)).sum()) / ha(core_o),
                 "tree_height_p50_m": float(np.median(height[ids][c & tree])) if nt else None,
                 "low_scale_share": float((scale[ids][c & pine] <= q30[ids][c & pine] + 1e-4).mean()) if (c & pine).sum() else None,
                 "treefree_patch_share": treefree(core_o), "treefree_patch_share_full": treefree(openb)}
            pc = c & pine
            if pc.sum() >= 20:
                allp = np.c_[px[pine], pz[pine]]
                v["pine_nn_p50_m"] = float(np.median(cKDTree(allp).query(np.c_[px[pc], pz[pc]], k=2)[0][:, 1]))
            else:
                v["pine_nn_p50_m"] = None
            rim_o, rim_i = comp & land & (bd < TRANS / 2), comp & land & (bd >= TRANS / 2) & (bd < TRANS)   # r2: rims of the whole bog
            dens = {nm_: float((at(m_) & tree).sum()) / max(ha(m_), 1e-9) for nm_, m_ in (("ring", ring), ("rim_out", rim_o), ("rim_in", rim_i))}
            con = dens["ring"] - v["trees_per_ha"]
            v["contrast_trees_per_ha"] = con
            v["t_out"] = (dens["rim_out"] - v["trees_per_ha"]) / con if con > 1e-9 else None
            v["t_in"] = (dens["rim_in"] - v["trees_per_ha"]) / con if con > 1e-9 else None
            v["t_out_minus_t_in"] = v["t_out"] - v["t_in"] if v["t_out"] is not None and v["t_in"] is not None else None
            rec["zones_trees_per_ha"] = dict(dens, core=v["trees_per_ha"])
            rims = comp & land & (bd < TRANS)
            rec["rim_open_share"] = float((slot[rims] != 1).mean()) if rims.any() else 0.0
            judge_ring = True
            res = {}
            for key, b in bands.items():
                if key in RING_KEYS and not judge_ring:
                    res[key] = [v[key], "NOT_JUDGED (ring not forest or rim wooded)"]
                    continue
                lo, hi = b
                val = v[key]
                good = val is not None and (lo is None or val >= lo) and (hi is None or val <= hi)
                bog_ok &= good
                res[key] = [val, "PASS" if good else "FAIL"]
            rec["open"] = res
        if ha(core_w) >= MIN_WOODED_HA:
            c = at(core_w)
            nt = int((c & tree).sum())
            yy, xx = np.nonzero(core_w)
            if kd is not None:
                dist = kd.query(np.c_[X0 + xx + 0.5, Z1 - yy - 0.5], distance_upper_bound=11)[0]
                f10 = float((dist > 10).mean())
            else:
                f10 = 1.0
            w = {"trees_per_ha": nt / ha(core_w), "pine_share_of_trees": float((c & tree & pine).sum()) / nt if nt else None,
                 "low_scale_share": float((scale[ids][c & pine] <= q30[ids][c & pine] + 1e-4).mean()) if (c & pine).sum() else None,
                 "free10": f10}
            wb = {"pine_share_of_trees": (0.70, None), "low_scale_share": (0.95, None), "free10": (None, free_max)}
            res = {}
            for key, (lo, hi) in wb.items():
                val = w[key]
                good = val is not None and (lo is None or val >= lo) and (hi is None or val <= hi)
                bog_ok &= good
                res[key] = [val, "PASS" if good else "FAIL"]
            res["trees_per_ha"] = [w["trees_per_ha"], "reported"]
            rec["wooded"] = res
        rec["ok"] = bool(bog_ok)
        judged_any = True
        ok_all &= bog_ok
        out.append(rec)
    ok_all &= judged_any
    fails = [r for r in out if not r["ok"]]
    summ = {"judged_bogs": len(out), "open_judged": sum(1 for r in out if "open" in r), "wooded_judged": sum(1 for r in out if "wooded" in r),
            "failed_bogs": len(fails), "failed_metrics": {}}
    for r in fails:
        for part in ("open", "wooded"):
            for key, (val, st) in r.get(part, {}).items():
                if st == "FAIL":
                    summ["failed_metrics"][f"{part}.{key}"] = summ["failed_metrics"].get(f"{part}.{key}", 0) + 1
    Path(a.out).write_text(json.dumps({"summary": summ, "free_m": a.free_m, "bands": {k: list(b) for k, b in bands.items()},
                                       "bogs": out}, indent=1, default=float) + "\n", encoding="utf-8")
    print(json.dumps(summ, indent=1))
    for r in fails[:20]:
        print("  FAIL bog", r["component"], r["centre_xz"], {p: {k_: (round(v_[0], 3) if isinstance(v_[0], float) else v_[0]) for k_, v_ in r[p].items() if v_[1] == "FAIL"}
                                                          for p in ("open", "wooded") if p in r})
    print(f"G7 {'PASS' if ok_all else 'FAIL'}")
    return 0 if ok_all else 1


def glib_window(arr, i0, i1, j0, j1, fill):
    o = np.full((i1 - i0, j1 - j0), fill, arr.dtype)
    a0, a1, b0, b1 = max(i0, 0), min(i1, gcfg.MAP), max(j0, 0), min(j1, gcfg.MAP)
    o[a0 - i0:a1 - i0, b0 - j0:b1 - j0] = arr[a0:a1, b0:b1]
    return o


if __name__ == "__main__":
    sys.exit(main())
