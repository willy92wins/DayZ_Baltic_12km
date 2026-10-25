"""Wiggle of the exact sea waterline in 60 m disks (review 1's local metric), before/after.
Usage: local_disks.py <before.npz> <before_fp.npz> <after.npz> <after_fp.npz> <tools_dir> <out.json>"""
import json, sys, os
import numpy as np
bt, bf, at, af, tools, outp = sys.argv[1:7]
sys.path.insert(0, os.path.join(tools, "water"))
import shore_ramp_v31 as sr
DISKS = {"stretch313": (7565, 10730), "c0_east_end_N": (7600, 10770), "c0_east_end_S": (7590, 10715),
         "c0_islet_end_N": (6960, 10668), "c0_islet_end_S": (7005, 10615), "c1_mainland_W": (6725, 10165),
         "c1_mainland_E": (6785, 10175), "c1_islet_W": (6815, 10545), "c1_islet_E": (6870, 10540),
         "c0_mid": (7286, 10693), "c1_mid": (6789, 10357)}
res = {}
for tag, tp, fpp in (("before", bt, bf), ("after", at, af)):
    H = np.load(tp)["heights"].astype(np.float64)
    f = np.load(fpp); pl = f["plane"].astype(np.float64)
    W, fp = sr.corner_water(pl, f["field"].astype(np.float64))
    for name, (x, z) in DISKS.items():
        r0, r1 = int((sr.ZTOP - (z + 80)) / 6), int((sr.ZTOP - (z - 80)) / 6) + 1
        c0, c1 = int((x - 80) / 6), int((x + 80) / 6) + 1
        seg = sr.extract_segments(H, W, fp, pl, r0 - 10, r1 + 10, c0 - 10, c1 + 10)
        seg = sr.subseg(seg, ~seg["pond"])
        vals = []
        for c in sr.chain(seg):
            q, v = sr.wiggle_profile(sr.canonical(c["pts"], c["closed"]), c["closed"], 12.0, 0.5)
            m = (np.hypot(q[:, 0] - x, q[:, 1] - z) <= 60) & np.isfinite(v)
            vals.append(v[m])
        v = np.concatenate(vals)
        res.setdefault(name, {"xz": [x, z]})[tag] = dict(samples=int(len(v)), p90=round(float(np.percentile(v, 90)), 4) if len(v) else None,
                                                       max=round(float(v.max()), 4) if len(v) else None)
json.dump(res, open(outp, "w", encoding="utf-8"), indent=1)
for k, e in res.items():
    print(f"{k:16s} {e['xz']}  p90 {e['before']['p90']} -> {e['after']['p90']}   max {e['before']['max']} -> {e['after']['max']}")
