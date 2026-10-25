"""Re-survey the BALTIC-015 crossings of 2026-10-11 (EV97) on a v31 terrain: water type on each side (first water along
the water axis 4-36 m out) and a bridge plan.
Usage: crossings_resurvey_v31.py <crossings-ev97-v2.json> <terrain.npz> <footprint.npz> <out.json> <out.csv>"""
import csv, json, math, sys
import numpy as np
src, tpath, fpath, out_j, out_c = sys.argv[1:6]
H = np.load(tpath)["heights"].astype(float); plane = np.load(fpath)["plane"].astype(float)
ZTOP = 12282
def side(x, z):
    """Water type around (x, z): pond (footprint cell with a corner below its plane), sea (terrain < 0.75 m), dry."""
    r, c = int((ZTOP - z) / 6), int(x / 6)
    best = ("dry", None)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            corners = [H[rr, cc], H[rr, cc + 1], H[rr + 1, cc], H[rr + 1, cc + 1]]
            if np.isfinite(plane[rr, cc]) and min(corners) < plane[rr, cc]:
                return ("pond", round(float(plane[rr, cc]), 3))
            if min(corners) < 0.75 and not np.isfinite(plane[rr, cc]):
                best = ("sea", 0.75)
    return best
rows = []
for r in json.load(open(src, encoding="utf-8"))["rows"]:
    if r["kind"] != "CROSSING":
        continue
    wb = math.radians(r["water_bearing_deg"]); wd = (math.sin(wb), math.cos(wb))
    def first_wet(sign):
        """First water found along the water axis 4..36 m from the crossing (EV102 cones fill the first metres)."""
        for dist in range(4, 37, 2):
            k = side(r["x"] + sign * dist * wd[0], r["z"] + sign * dist * wd[1])
            if k[0] != "dry":
                return (k[0], k[1], dist)
        return ("dry", None, None)
    up, dn = first_wet(1), first_wet(-1)
    kinds = {up[0], dn[0]} - {"none"}
    if kinds == {"sea"}:
        water = "sea"
    elif kinds == {"pond"} and up[1] == dn[1]:
        water = "pond"
    elif kinds == {"pond"}:
        water = "pond-two-levels"
    elif "dry" in kinds and len(kinds) == 1:
        water = "dry"
    else:
        water = "mixed"
    level = 0.75 if water == "sea" else (up[1] if water == "pond" else None)
    fb = None if level is None else round(r["road_y"] - level, 2)
    W = float(r["design_width_m"] or 4.0)
    if r["navigable"]:
        plan = "navigable: decide (clearance for the boat)"
    elif water in ("mixed", "dry", "pond-two-levels"):
        plan = f"skip ({water})"
    elif r["design_class"] == "river":
        plan = "bridge_metal_25 x2" if fb is not None and fb >= 1.96 else "bridge_metal_25: underside clearance fails"
    else:
        plan = "bridge_wood_25" if W <= 6 else "bridge_wood_50"
    rows.append(dict(n=r["n"], site=r["site"], id=r["id"], name=r.get("name"), x=r["x"], z=r["z"], road_bearing=r["road_bearing_deg"],
                     water_bearing=r["water_bearing_deg"], angle=r["crossing_angle_deg"], design_class=r["design_class"], width=W,
                     road_y=r["road_y"], up=f"{up[0]}:{up[1]}@{up[2]}m", down=f"{dn[0]}:{dn[1]}@{dn[2]}m", water=water, level=level, road_minus_level=fb,
                     navigable=r["navigable"], plan=plan))
json.dump(rows, open(out_j, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
with open(out_c, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r["water"] for r in rows), Counter(r["plan"] for r in rows))
