"""Instance counts per family, per class of land and per km2, Baltic against Livonia with the same code. Counts only:
no performance claim (project rule 7). The densest km2 is flagged for an FPS check in game.

Usage: python -I counts_map.py <records.json> <gate-rasters dir> <out.json>
km2 cells: 1 km squares aligned to each map's origin (Baltic 12 x 12 full cells of its 12.288 km; Livonia 12 x 12 of
its 12.8 km, enoch veg.npz). Land share per cell from the water rasters (Baltic grasters water 5 m; Livonia ctx.npz).
Per family and all vegetation: totals, per km2 of land, and the p50 / p90 / p99 / max over the cells with >= 90 % land.
Livonia families from veg.npz (conifer, broadleaf, bush, dead, reed, herb; Baltic places no herb)."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402
import glib  # noqa: E402

FAMS = ["conifer", "broadleaf", "bush", "dead", "reed", "herb"]


def per_km2(x, z, fam, land5, nkm):
    land = land5[:nkm * 200, :nkm * 200].reshape(nkm, 200, nkm, 200).mean(axis=(1, 3))
    r = np.clip((z // 1000).astype(int), 0, nkm - 1)
    c = np.clip((x // 1000).astype(int), 0, nkm - 1)
    ok = (x >= 0) & (z >= 0) & (x < nkm * 1000) & (z < nkm * 1000)
    out = {"density_scope": "0<=X<12000 and 0<=Z<12000, same numerator and land-area denominator; total includes all placed instances", "land_km2": float(land.sum()), "cells_ge_90pct_land": int((land >= 0.9).sum())}
    grids = {}
    for name, sel in [(f, fam == i) for i, f in enumerate(FAMS)] + [("trees", fam <= 1), ("all", fam >= 0)]:
        g = np.zeros((nkm, nkm))
        np.add.at(g, (r[sel & ok], c[sel & ok]), 1)
        grids[name] = g
        v = g[land >= 0.9]
        out[name] = {"total": int(sel.sum()), "count_in_12km_square": int((sel & ok).sum()), "per_km2_land": float((sel & ok).sum()) / float(land.sum()),
                     "cell_p50_p90_p99_max": [float(np.percentile(v, q)) for q in (50, 90, 99)] + [float(v.max())] if v.size else None}
    k = np.unravel_index(np.argmax(grids["all"]), grids["all"].shape)
    kt = np.unravel_index(np.argmax(grids["trees"]), grids["trees"].shape)
    out["densest_km2_all"] = {"x0_z0": [int(k[1] * 1000), int(k[0] * 1000)], "all": int(grids["all"][k]), "trees": int(grids["trees"][k]),
                              "bush": int(grids["bush"][k]), "land_share": float(land[k])}
    out["densest_km2_trees"] = {"x0_z0": [int(kt[1] * 1000), int(kt[0] * 1000)], "trees": int(grids["trees"][kt]), "all": int(grids["all"][kt]),
                                "land_share": float(land[kt])}
    order = np.argsort(-grids["all"].ravel())[:5]
    out["top5_km2_all"] = [{"x0_z0": [int(i % nkm * 1000), int(i // nkm * 1000)], "all": int(grids["all"].ravel()[i]),
                            "trees": int(grids["trees"].ravel()[i])} for i in order]
    return out


MR = glib.MapRecords(sys.argv[1])
R = glib.Rasters(sys.argv[2])
fam = np.where(MR.fam <= 4, MR.fam, -1)
bal = per_km2(MR.x, MR.z, fam, ~R.water, 12)
v = np.load(gcfg.LIVONIA / "veg.npz")
c = np.load(gcfg.LIVONIA / "ctx.npz")
liv = per_km2(v["x"], v["z"], v["fam"].astype(int), ~c["water"], 12)
res = {"baltic": bal, "livonia": liv,
       "ratio_per_km2_land": {k: bal[k]["per_km2_land"] / liv[k]["per_km2_land"] if liv[k]["per_km2_land"] else None
                              for k in FAMS + ["trees", "all"]},
       "note": "instance counts only; no performance claim (project rule 7)"}
Path(sys.argv[3]).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1))
