"""G8 texture/tree agreement (EV112, Guillermo 2026-10-17: dark forest-floor ground where trees should be).

Usage: python -I g8_agreement.py <records.json> <gate-rasters dir> <livonia-ev112-bands.json> <out.json>
         [--windows x0,z0;...] [--min-forest-ha 20]
Measured as livonia_bands.py measures enoch (5 m cells; the shipped forest-floor texture sampled every 12.5 m like
Livonia's enoch_surf; land = not visible water):
  free10        share of forest-floor land cells with no tree (conifer/broadleaf WRP position) within 10 m
  patch10_400   share of forest-floor land cells in 8-connected tree-free patches >= 400 m2
  far_trees_ha  trees per ha on land beyond the Livonia spill band (signed distance to the texture < -40 m, > 25 m
                from water, outside the bog and its 25 m margin)
Exempt: the Narva urban exclusion (terrain 'narva' cells + 6 m, cell centre within 6 m + half a cell diagonal):
no vegetation by product rule, it waits for buildings; its bare forest floor is reported apart (whole_map). And the
plan hulls of the streambed kit pieces and kit stones (cell centre inside the visual-bbox hull): the piece's mesh
covers that ground [inferred from the models' plan size, not checked in game]; the margin around them is judged. And
the bridge exclusion zone (6 m around a bridge plan hull or the v31_bridge_cut / fill cells): no tree by product rule
(G1); its bare forest-floor texture is a surface matter (repaint the earthwork in the bridge surface patch), reported
apart as bridge_forest_floor_km2 and listed by site, not judged here.
Local rule: no tree-free forest-floor patch (8-connected 5 m cells) larger than Livonia's largest on its whole map
(livonia-ev112-bands.json largest_patch_m2, 2000 m2): window shares dilute a single dark clearing.
Bands: Livonia [min, max] over its 1 km windows (free10, patch10_400: windows with >= 20 ha of forest floor;
far_trees_ha: >= 5 ha of that land). Rule (strict, per window, every window of the map with enough area): free10 <=
max, patch10_400 <= max, far_trees_ha <= max. The bog is not exempt from free10 / patch10_400: its forest-floor part
must carry trees like any forest floor. Prints PASS or FAIL last; exit 1 on FAIL.
Also reports the whole-map values next to Livonia's whole-map values (not judged)."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glib  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("records")
ap.add_argument("rasters")
ap.add_argument("bands")
ap.add_argument("out")
ap.add_argument("--windows")
ap.add_argument("--min-forest-ha", type=float, default=20.0)
ap.add_argument("--size", type=float, default=1000.0)
a = ap.parse_args()
MR = glib.MapRecords(a.records)
R = glib.Rasters(a.rasters)
LB = json.loads(Path(a.bands).read_text(encoding="utf-8"))["agreement"]
ff, free, cnt, far = glib.agreement_maps(R, MR)
wins = [tuple(float(v) for v in w.split(",")) for w in a.windows.split(";")] if a.windows else [(x, z) for z in glib.WIN_X0 for x in glib.WIN_X0]
rows, bad = [], []
for x0, z0 in wins:
    r = glib.agreement_window(ff, free, cnt, far, x0, z0, a.size)
    r["fails"] = []
    if r["forest_ha"] >= a.min_forest_ha:
        for k in ("free10", "patch10_400"):
            if r[k] > LB[k]["max"]:
                r["fails"].append(k)
    if r.get("max_patch_m2", 0.0) > LB["largest_patch_m2"]:
        r["fails"].append("max_patch_m2")
    if r["far_ha"] >= 5 and r.get("far_trees_ha", 0) > LB["far_trees_ha"]["max"]:
        r["fails"].append("far_trees_ha")
    rows.append(r)
    if r["fails"]:
        bad.append(r)
judged = [r for r in rows if r["forest_ha"] >= a.min_forest_ha]
import numpy as np  # noqa: E402
whole = {"free10": float(free.sum()) / max(1, int(ff.sum())), "forest_floor_km2": float(ff.sum() * 25 / 1e6),
         "far_trees_ha": float(cnt[far].sum()) / max(1e-9, float(far.sum() * 25 / 1e4)), "far_km2": float(far.sum() * 25 / 1e6),
         "narva_forest_floor_km2_exempt": float((R.tex_samp & ~R.water & R.narva).sum() * 25 / 1e6),
         "kit_hull_forest_floor_km2_exempt": float((R.tex_samp & ~R.water & R.kit).sum() * 25 / 1e6),
         "bridge_zone_forest_floor_km2_exempt": float((R.tex_samp & ~R.water & R.bridge & ~R.narva).sum() * 25 / 1e6)}
from scipy import ndimage as _nd  # noqa: E402
_bl, _bn = _nd.label(R.tex_samp & ~R.water & R.bridge, structure=np.ones((3, 3)))
whole["bridge_zone_sites_forest_floor_ge_500m2"] = sorted(
    ([round(float(_x.mean() * 5 + 2.5), 1), round(float(_y.mean() * 5 + 2.5), 1), int(len(_x) * 25)]
     for _y, _x in (np.nonzero(_bl == _k) for _k in range(1, _bn + 1)) if len(_x) * 25 >= 500), key=lambda t: -t[2])
summ = {"windows": len(rows), "judged_forest_windows": len(judged), "failed_windows": len(bad),
        "max_free10": max((r["free10"] for r in judged), default=None), "livonia_free10_max": LB["free10"]["max"],
        "max_patch10_400": max((r["patch10_400"] for r in judged), default=None), "livonia_patch10_400_max": LB["patch10_400"]["max"],
        "largest_patch_m2": max((r.get("max_patch_m2", 0.0) for r in rows), default=None), "livonia_largest_patch_m2": LB["largest_patch_m2"],
        "largest_patches": sorted(({"m2": r["max_patch_m2"], "xz": r.get("max_patch_xz")} for r in rows if r.get("max_patch_m2", 0) >= 1000), key=lambda t: -t["m2"])[:20],
        "p50_free10": float(np.median([r["free10"] for r in judged])) if judged else None, "livonia_free10_p50": LB["free10"]["p50"],
        "max_far_trees_ha": max((r.get("far_trees_ha", 0) for r in rows if r["far_ha"] >= 5), default=None),
        "livonia_far_trees_ha_max": LB["far_trees_ha"]["max"], "whole_map": whole, "livonia_whole_map": LB["whole_map"],
        "failures": [{k: r[k] for k in ("x0", "z0", "fails", "forest_ha", "free10", "patch10_400", "max_patch_m2", "max_patch_xz") if k in r} for r in bad[:40]]}
Path(a.out).write_text(json.dumps({"summary": summ, "windows": rows}, indent=1) + "\n", encoding="utf-8")
print(json.dumps(summ, indent=1))
ok = len(judged) > 0 and not bad
print(f"G8 {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
