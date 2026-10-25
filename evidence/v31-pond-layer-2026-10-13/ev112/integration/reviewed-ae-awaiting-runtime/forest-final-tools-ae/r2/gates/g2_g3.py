"""G2 (density, spacing, species mix per context) and G3 (forest edges) against the Livonia 1 km window envelope.

Usage: python -I g2_g3.py <records.json> <G2|G3> [--dense SECTOR ...] [--json out.json] [--keep-bog]
Rule (fixed before the first run, strict contract restored in v3): every metric of the sector (analysis area = polygon
inset 50 m minus the bog cells, canopy contexts recomputed from the records with forest_metrics.py) lies within
[min, max] of the 256 comparable Livonia windows (land >= 90 %, canopy >= 50 %); tvd.* only <= max; agreement.* only
>= min. A sector named with --dense must also have density.interior.trees >= the Livonia window p50 (P13: dense
reserve). Contexts below the minimum area are not judged. A sector passes with 0 failed metrics: no tolerance file.
G3 includes the texture-relative edge profile (tex_edge.*, tex_gradient.*: densities and ratios in bins of the signed
distance to the forest-floor texture, sampled as Livonia's surface), an edge reference independent of the generated
canopy.
v3 (EV111 bog): the OSM wetland is left out of the analysis area (gate_common.py docstring; G7 judges it); --keep-bog
measures it as v2 did, for the record only. r2: so is a 25 m margin around it (gate_common.BOG_MARGIN_M).
Prints one line per metric and PASS or FAIL last.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate_common as GC  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("records")
ap.add_argument("gate", choices=["G2", "G3"])
ap.add_argument("--dense", action="append", default=[])
ap.add_argument("--json")
ap.add_argument("--keep-bog", action="store_true")
a = ap.parse_args()
ref = json.loads(GC.REFERENCE.read_text(encoding="utf-8"))
secs = json.loads(GC.SECTORS.read_text(encoding="utf-8"))["sectors"]
t = np.load(GC.TERRAIN)
H = t["heights"].astype(np.float64)
plane = np.load(GC.FOOTPRINT)["plane"]
recs = GC.load_records(a.records)
tex = GC.texture_forest_fn() if a.gate == "G2" else None
mask = GC.texture_mask() if a.gate == "G3" else None
prefixes = GC.PREFIXES[a.gate]
ok_all, dump = True, {}
for sec in secs:
    m, _ = GC.sector_measure(recs, ref, sec, H, plane, tex, mask, exclude_bog=not a.keep_bog)
    vals = GC.metric_table(m, ref)
    _, rows = GC.judge(vals, ref, prefixes)
    failed = [r[0] for r in rows if r[4].startswith("FAIL")]
    ok = not failed
    print(f"== {sec['name']}: analysed {m['analysis_area_ha']:.1f} ha (bog left out {m['bog_excluded_ha']:.1f} ha), "
          f"{m['n_points_analysed']} instances, context ha {({k: round(v, 1) for k, v in m['area_ha'].items()})}")
    if m["unknown_models"]:
        ok = False
        print(f"  FAIL unknown models: {m['unknown_models']}")
    if m["n_points_analysed"] == 0:
        ok = False
        print("  FAIL no instances in the analysis area")
    for k, v, lo, hi, st in rows:
        print(f"  {k:42s} {v if v is None else round(v, 4)!s:>10} [{lo if lo is None else round(lo, 4)}, {hi if hi is None else round(hi, 4)}] {st}")
    if a.gate == "G2" and sec["name"] in a.dense:
        v, p50 = vals.get("density.interior.trees"), ref["bands"]["density.interior.trees"]["p50"]
        good = v is not None and v >= p50
        ok &= good
        print(f"  dense rule: density.interior.trees {v if v is None else round(v, 1)} >= Livonia p50 {p50}: {'PASS' if good else 'FAIL'}")
    judged = sum(1 for r in rows if r[4] != "NO_BAND")
    if judged == 0:
        ok = False
        print("  FAIL nothing judged")
    print(f"  {sec['name']} {a.gate}: {'PASS' if ok else 'FAIL'} ({judged} metrics judged, {len(failed)} failed, allowed 0; "
          f"{sum(1 for r in rows if 'outside p10' in r[4])} outside p10-p90)")
    ok_all &= ok
    dump[sec["name"]] = {"values": vals, "ok": bool(ok), "failed": failed, "allowed": 0,
                         "context_area_ha": m["area_ha"], "bog_excluded_ha": m["bog_excluded_ha"]}
if a.json:
    Path(a.json).write_text(json.dumps(dump, indent=1) + "\n", encoding="utf-8")
print(f"{a.gate} {'PASS' if ok_all else 'FAIL'}")
sys.exit(0 if ok_all else 1)
