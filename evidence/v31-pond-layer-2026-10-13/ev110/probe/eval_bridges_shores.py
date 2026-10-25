"""EV110 server probe, bridges and shores families. Rows P;id;ground;sea;pond;surface;depth;roadY;objects (BalticBridgeProbeV2). The level check uses the engine pond surface field: ground + depth follows the waves.
bridges: per site, max |d roadY| / |d s| over consecutive 1 m road points (roadY = SurfaceRoadY3D from +30 m, the top roadway),
under points wet (depth > 0), water surface ground + depth vs the site level, sea flags. shores: wet pairs need depth > 0,
dry pairs depth <= 0 and no sea. Fails closed on non-finite values and on missing rows."""
import json, math, sys
W = "C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/"
def rows(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        a = line.strip().split(";")
        if a[0] == "P":
            v = dict(ground=float(a[2]), sea=a[3] == "true", pond=a[4] == "true", surface=float(a[5]), depth=float(a[6]), roadY=float(a[7]), objects=int(a[8]))
            assert all(math.isfinite(v[k]) for k in ("ground", "depth", "roadY")), a
            assert int(a[1]) not in out
            out[int(a[1])] = v
    return out
res = {"bridges": {}, "shores": {}}
B = json.load(open("bridges-points.json")); RB = rows("split/bridges-baltic_bridge_probe_v2.log"); assert len(RB) == len(B)
sites = {s["id"]: s for s in json.load(open(W + "evidence/v31-pond-layer-2026-10-13/bridges/ev110/sites-ev110.json"))}
old = json.load(open(W + "evidence/v31-pond-layer-2026-10-13/bridges/ev109/probe-ev109-summary.json"))["bridges"]
ok = True
for sid in sites:
    road = sorted([p for p in B if p["site"] == sid and p["kind"] == "road"], key=lambda p: p["s"])
    und = [p for p in B if p["site"] == sid and p["kind"] == "under"]
    steps = [abs(RB[b["id"]]["roadY"] - RB[a["id"]]["roadY"]) / abs(b["s"] - a["s"]) for a, b in zip(road, road[1:])]
    wet = [RB[p["id"]]["depth"] > 0 for p in und]
    lvl = sites[sid]["level"]
    err = max([abs(RB[p["id"]]["surface"] - lvl) for p in und if RB[p["id"]]["depth"] > 0] or [float("nan")])  # engine pond surface field; ground + depth carries the waves
    sea = sum(RB[p["id"]]["sea"] for p in und)
    r = dict(max_step_per_m=round(max(steps), 3), road_points=len(road), under_wet=f"{sum(wet)}/{len(wet)}", under_level_err=round(err, 3), sea_under=sea,
             ev109=old.get(sid))
    r["pass"] = r["max_step_per_m"] <= 0.35 and all(wet) and sea == 0 and err <= 0.05
    ok &= r["pass"]
    res["bridges"][sid] = r
S = json.load(open("shores-points.json")); RS = rows("split/shores-baltic_bridge_probe_v2.log"); assert len(RS) == len(S)
bad = []
for i, p in enumerate(S):
    v = RS[i]
    good = (v["depth"] > 0) if p["expect"] == "wet" else (v["depth"] <= 0 and not v["sea"])
    if not good:
        bad.append(dict(i=i, expect=p["expect"], stretch=p["stretch"], body=p["body"], x=round(p["x"], 1), z=round(p["z"], 1), depth=v["depth"], sea=v["sea"], ground=v["ground"], npz_ground=p["ground"]))
res["shores"] = dict(n=len(S), wet_ok=sum(1 for i, p in enumerate(S) if p["expect"] == "wet" and RS[i]["depth"] > 0), dry_ok=sum(1 for i, p in enumerate(S) if p["expect"] == "dry" and RS[i]["depth"] <= 0 and not RS[i]["sea"]),
                     islet_pairs_ok=sum(1 for i, p in enumerate(S) if p.get("islet") and ((RS[i]["depth"] > 0) if p["expect"] == "wet" else (RS[i]["depth"] <= 0))), islet_points=sum(1 for p in S if p.get("islet")),
                     ground_match_max=round(max(abs(RS[i]["ground"] - p["ground"]) for i, p in enumerate(S)), 3), failures=bad)
ok &= not bad
res["pass"] = bool(ok)
json.dump(res, open("eval-bridges-shores.json", "w", newline="\n"), indent=1)
for sid, r in res["bridges"].items():
    e = r["ev109"] or {}
    print(sid, "step", r["max_step_per_m"], "(ev109", e.get("max_step_per_m"), ") under", r["under_wet"], "(ev109", e.get("under_wet"), ") lvl_err", r["under_level_err"], "sea", r["sea_under"], "PASS" if r["pass"] else "FAIL")
sh = res["shores"]; print("shores wet", sh["wet_ok"], "/50 dry", sh["dry_ok"], "/50 islet", sh["islet_pairs_ok"], "/", sh["islet_points"], "ground_match_max", sh["ground_match_max"], "failures", len(sh["failures"]))
for f in sh["failures"][:10]: print("  ", f)
print("OVERALL", "PASS" if ok else "FAIL")
