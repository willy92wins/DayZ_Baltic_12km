"""BALTIC-015 rollout probe points: per bridge, 'road' every 1 m along the road axis through the crossing, from 15 m before
to 15 m after the bridge ends (expect a continuous rolling surface: deck on the bridge, road terrain outside), and 'under'
on the water axis inside the deck footprint, every 1 m within +-W/2 + 2 m (expect water at the stream level, no sea).
Stacked sites (stack = true) and model swaps (bridge_wood_50_1, posed on wood_50's roadway) take the same points: the
upper roadway, its length and the water under it do not change (the lower copy lies under the upper deck); each point
carries the site's model and stack flag so a probe summary can tell them apart.
Usage: probe_points_bridges.py <sites.json> <bridge-report.json> <points.csv> <points.json>"""
import json, math, sys
sites_p, rep_p, csv_p, json_p = sys.argv[1:5]
rep = {r["site"]: r for r in json.load(open(rep_p))["sites"]}
HALF = {"bridge_wood_25": 16.641, "bridge_wood_50": 25.77, "bridge_wood_50_1": 25.77,     # roadway half length, from
        "bridge_metal_25": 12.5}                                                       # bridges_v31.model_info
pts = []
for s in json.load(open(sites_p)):
    if s["model"] not in HALF:
        raise SystemExit(f"probe_points_bridges: no roadway half length for {s['model']}")
    b = math.radians(s["bearing"]); d = (math.sin(b), math.cos(b))
    wb = math.radians(s["water_bearing"]); wd = (math.sin(wb), math.cos(wb))
    half = HALF[s["model"]] * s.get("spans", 1)
    tag = dict(model=s["model"], stack=bool(s.get("stack", False)))
    for k in range(-int(half) - 15, int(half) + 16):
        pts.append(dict(id=len(pts), site=s["id"], kind="road", s=k, x=s["x"] + k * d[0], z=s["z"] + k * d[1], **tag))
    for k in range(-int(s["width"] / 2) - 2, int(s["width"] / 2) + 3):
        pts.append(dict(id=len(pts), site=s["id"], kind="under", s=k, x=s["x"] + k * wd[0], z=s["z"] + k * wd[1],
                        level=rep[s["id"]]["level"], water=rep[s["id"]]["water"], **tag))
with open(csv_p, "w", newline="\n") as f:
    for p in pts:
        f.write(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n")
json.dump(pts, open(json_p, "w", newline="\n"), indent=1)
print(len(pts))
