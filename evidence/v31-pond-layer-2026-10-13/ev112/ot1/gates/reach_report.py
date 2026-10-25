"""Per-reach report of the EV112 kit run: one row per site of the sites file, from kit-report.json and the gate outputs
(gate-g2/g3/g4/g10/g11.json, written by run_gates.py) plus the worklist (kit_worklist_v31.py output). Writes
<run>/reach-report.json and <run>/reach-report.csv. Usage: reach_report.py <run_dir> <worklist.json>"""
import csv, json, os, sys
from collections import Counter
run, wl = sys.argv[1:3]
rep = json.load(open(run + "/kit-report.json"))
g = {k: (json.load(open(f"{run}/gate-{k}.json")) if os.path.exists(f"{run}/gate-{k}.json") else {}) for k in ("g2", "g3", "g4", "g7", "g10", "g11")}
wlj = json.load(open(wl))
census = {x["reach"]: x for x in wlj["in_stems"]}
junc = {}
for j in g["g11"].get("junctions", []):
    junc.setdefault(j["site"], []).append(f"{j['end']}:{j['type']}:{j['distance_m']}")
road = g["g11"].get("road_pixels_by_site", {})
probe = Counter(p.get("site") for p in (json.load(open(run + "/probe/points.json")) if os.path.exists(run + "/probe/points.json") else [])
                if p.get("kind", "").startswith("kit_") or p.get("kind") == "old_bed")
rows = []
for s in rep["sites"]:
    sid = s["site"]; reach = sid.rsplit("-", 1)[0] if s.get("mode") == "reach" else None
    c = census.get(reach, {})
    row = dict(site=sid, mode=s.get("mode"), census_reach=reach, census_length_m=c.get("length_m"), census_wiggle=c.get("wiggle"),
               census_worst_segment_wiggle=c.get("worst_segment_wiggle"), census_width_p50=c.get("width_p50"), selected_by=c.get("reason"),
               skipped=s.get("skipped"))
    if "skipped" not in s:
        g2, g3, g4, g10 = g["g2"].get(sid, {}), g["g3"].get(sid, {}), g["g4"].get(sid, {}), g["g10"].get("per_site", {}).get(sid, {})
        row.update(ends=json.dumps(s.get("ends")), lattice_m=s["lattice_m"], wet_span_m=round(s["wet_span"][1] - s["wet_span"][0], 1),
                   pieces=s["pieces"], kinds=json.dumps(s["kinds"]), corners=len(s["corners"]), joint_overlap_min_m=s["joint_overlap_min_m"],
                   dev_lattice_thalweg_p90=s["dev_lattice_to_thalweg_p50_p90_max"][1],
                   g2_width_p10_50_90=json.dumps(g2.get("width_p10_50_90")), g2_std=g2.get("width_std"), g2_out_band=g2.get("edge_outside_band_share"),
                   g2_centre_dry=g2.get("centre_dry"), g2_pass=g2.get("passed"),
                   g3_axis_dry=g3.get("axis_dry_samples"), g3_regions=g3.get("wet_regions_total"), g3_pass=g3.get("passed"),
                   g4_samples=g4.get("samples"), g4_margin_min=g4.get("margin_min"), g4_water_ext_share=g4.get("water_ext_only_share_ge_0p10"), g4_pass=g4.get("passed"),
                   g10_stones=g10.get("stones"), g10_target=g10.get("target"), g10_per_km=g10.get("per_km"),
                   road_pixels=road.get(sid, 0), sills=s.get("sills"), sill_frozen=s.get("sill_frozen"),
                   ring_conflicts=s.get("frozen_or_protected_in_ring"), cover_cells_removed=s["cover_cells_removed"],
                   envelope_cells_removed=s["envelope_cells_removed"], pits_filled=s["pits_filled"], axis_moved_ring0=s["axis_moved_ring0"],
                   trimmed=json.dumps(s.get("trimmed_by")), junctions=" ".join(junc.get(sid, [])), probe_points=probe.get(sid, 0),
                   final_axis_below_min=s["final_axis_below_min"])
    rows.append(row)
keys = []
for r in rows:
    for k in r:
        if k not in keys:
            keys.append(k)
with open(run + "/reach-report.csv", "w", newline="\n", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n"); w.writeheader(); w.writerows(rows)
json.dump(dict(counts=rep["counts"], mounds=rep["mounds"], rows=rows, left_out=dict(stems=wlj["out_stems"], short_runs=wlj["short_runs_left_as_pond"],
                                                                                 thin_left_as_pond=wlj["thin_left_as_pond"])),
          open(run + "/reach-report.json", "w", newline="\n"), indent=1)
print(len(rows), "rows;", sum(1 for r in rows if r["skipped"]), "skipped")
