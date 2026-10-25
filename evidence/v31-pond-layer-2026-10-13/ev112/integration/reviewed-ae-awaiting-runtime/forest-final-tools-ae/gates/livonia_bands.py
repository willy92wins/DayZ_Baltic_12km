"""Livonia bands for the EV112 map-wide gates (written once, before any Baltic map output is judged).

Usage: python -I livonia_bands.py <out.json>
1 Texture/tree agreement (G8), measured on enoch exactly as g8_agreement.py measures Baltic:
  forest floor = Livonia forest surface (ctx.npz 'forest': enoch_surf ids 6/7 sampled every 12.5 m, nearest sample per
  5 m cell) on land; a forest-floor cell is tree-free when no tree (conifer/broadleaf WRP position) lies within 10 m
  of its centre.
    free10        share of forest-floor cells that are tree-free
    patch10_400   share of forest-floor cells in 8-connected tree-free patches of >= 16 cells (400 m2)
    largest_patch_m2  the largest such patch on the whole map (a local bound: one dark clearing on forest floor)
    far_trees_ha  trees per ha on land beyond the spill band: signed distance to the forest surface < -40 m, more than
                  25 m from water (Livonia's spill reaches 20-40 m beyond its surface)
  per 1 km window (step 500 m, 576 windows); free10 and patch10_400 over windows with >= 20 ha of forest floor,
  far_trees_ha over windows with >= 5 ha of that land. Band = [min, max] (one-sided: Baltic <= max).
2 G2/G3 leave-one-out: for every comparable Livonia window (land >= 0.9, canopy >= 0.5, 256) and every judged metric,
  the envelope of the other 255 windows; per metric the number of windows outside it and their largest excess in band
  widths; per gate the share of windows with >= 1 failed metric (the rate at which a Livonia-like window fails the
  strict contract). The map verdict of g2g3_map.py uses these per metric, never one metric's excess for another
  (Codex review 2 of EV111: the global 1.82 came from tvd.riparian.broadleaf)."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402

sys.path.insert(0, str(gcfg.R2_GATES))
sys.path.insert(0, str(gcfg.R2_GATES.parent))
import forest_metrics as FMx  # noqa: E402
import gate_common as GC  # noqa: E402

out_path = Path(sys.argv[1])
v = np.load(gcfg.LIVONIA / "veg.npz")
c = np.load(gcfg.LIVONIA / "ctx.npz")
x, z, fam = v["x"], v["z"], v["fam"]
NL = 2560
water = c["water"]
land = ~water
fs = c["forest"] & land
tree = (fam == 0) | (fam == 1)
tsd = FMx.surface_sd(c["forest"])
dw = ndimage.distance_transform_edt(~water) * 5.0
rr, cc = np.nonzero(fs)
d = cKDTree(np.c_[x[tree], z[tree]]).query(np.c_[(cc + 0.5) * 5, (rr + 0.5) * 5], distance_upper_bound=11.0)[0]
free = np.zeros((NL, NL), bool)
free[rr, cc] = d > 10.0
lab, n = ndimage.label(free, structure=np.ones((3, 3)))
sz = ndimage.sum(np.ones(free.shape), lab, index=np.arange(1, n + 1))
inpatch = np.zeros(n + 1, bool)
inpatch[1:] = sz >= 16
patch = inpatch[lab]
far = land & (tsd < -40) & (dw > 25)
r_pt = np.clip(np.floor(z / 5).astype(int), 0, NL - 1)
c_pt = np.clip(np.floor(x / 5).astype(int), 0, NL - 1)
tcount = np.zeros((NL, NL))
np.add.at(tcount, (r_pt[tree], c_pt[tree]), 1)
wins = []
for wr in range(0, NL - 200 + 1, 100):
    for wc in range(0, NL - 200 + 1, 100):
        sl = (slice(wr, wr + 200), slice(wc, wc + 200))
        nf, nfar = int(fs[sl].sum()), int(far[sl].sum())
        w = {"x0": wc * 5, "z0": wr * 5, "forest_ha": nf * 25 / 1e4, "far_ha": nfar * 25 / 1e4}
        if nf:
            w["free10"] = float(free[sl].sum()) / nf
            w["patch10_400"] = float(patch[sl].sum()) / nf
        if nfar:
            w["far_trees_ha"] = float(tcount[sl][far[sl]].sum()) / (nfar * 25 / 1e4)
        wins.append(w)


def band(vals):
    a = np.array(vals, float)
    return {"n": int(a.size), "min": float(a.min()), "p10": float(np.percentile(a, 10)), "p50": float(np.median(a)),
            "p90": float(np.percentile(a, 90)), "max": float(a.max())}


res = {"source": {"veg_npz_sha256": GC.sha256(gcfg.LIVONIA / "veg.npz"), "ctx_npz_sha256": GC.sha256(gcfg.LIVONIA / "ctx.npz"),
                  "script_sha256": GC.sha256(Path(__file__))},
       "agreement": {"definition": __doc__.split("2 G2/G3")[0].strip(),
                     "free10": band([w["free10"] for w in wins if w["forest_ha"] >= 20]),
                     "patch10_400": band([w["patch10_400"] for w in wins if w["forest_ha"] >= 20]),
                     "far_trees_ha": band([w["far_trees_ha"] for w in wins if w["far_ha"] >= 5]),
                     "largest_patch_m2": float(sz.max()) * 25.0, "largest_patches_m2": sorted((float(v) * 25.0 for v in sz), reverse=True)[:10],
                     "whole_map": {"free10": float(free.sum()) / int(fs.sum()), "patch10_400": float(patch.sum()) / int(fs.sum()),
                                   "far_trees_ha": float(tcount[far].sum()) / float(far.sum() * 25 / 1e4)},
                     "windows_forest_ge_20ha": sum(1 for w in wins if w["forest_ha"] >= 20)}}
# ---- G2/G3 leave-one-out per metric
ref = json.loads(gcfg.REFERENCE.read_text(encoding="utf-8"))
lw = json.loads((gcfg.F111 / "ref-v2/livonia-windows.json").read_text(encoding="utf-8"))
comp = [w for w in lw if w["land_frac"] >= 0.9 and (w["canopy_frac"] or 0) >= 0.5]
tabs = [GC.metric_table(w, ref) for w in comp]
res["loo"] = {"windows": len(comp), "reference_sha256": GC.sha256(gcfg.REFERENCE),
              "livonia_windows_sha256": GC.sha256(gcfg.F111 / "ref-v2/livonia-windows.json")}
for gate, pref in GC.PREFIXES.items():
    keys = sorted({k for t in tabs for k in t if k.startswith(pref)})
    vals = {k: np.array([np.nan if t.get(k) is None else t[k] for t in tabs], float) for k in keys}
    per, nfail = {}, np.zeros(len(tabs), int)
    for k in keys:
        if ref["bands"].get(k, {}).get("n", 0) < 10:
            continue
        ex = []
        for i in range(len(tabs)):
            vv = vals[k][i]
            if not np.isfinite(vv):
                continue
            o = np.delete(vals[k], i)
            o = o[np.isfinite(o)]
            lo, hi = (-np.inf if k.startswith("tvd.") else o.min()), (np.inf if k.startswith("agreement.") else o.max())
            if not (lo <= vv <= hi):
                nfail[i] += 1
                ex.append(GC.excess(vv, lo, hi, o.max() - o.min()))
        per[k] = {"n_windows": int(np.isfinite(vals[k]).sum()), "loo_fail": len(ex), "loo_max_excess": round(float(max(ex)), 6) if ex else 0.0}
    res["loo"][gate] = {"fail_share": float(np.mean(nfail > 0)), "failed_metrics_p50_p90_max": [float(a) for a in np.percentile(nfail, [50, 90, 100])],
                        "metrics": per}
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps({"agreement": {k: v_ for k, v_ in res["agreement"].items() if k != "definition"},
                  "loo": {g: {"fail_share": res["loo"][g]["fail_share"]} for g in GC.PREFIXES}}, indent=1))
