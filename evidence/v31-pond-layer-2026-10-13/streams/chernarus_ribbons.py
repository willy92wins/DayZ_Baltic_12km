"""Terrain against the ribbon level across Chernarus stream/river pieces (Astra's survey.log, 2026-10-03).
Channel order mirrors IsChannelShape of BalticVanillaWaterSurveyV1 (init.c:59-65): stream_, river_, streambed."""
import json, sys
import numpy as np
from collections import defaultdict
F = "E:/DayZ-Baltic-Build/vanilla-water-survey-v1/survey.log"
chan, W = [], defaultdict(dict)
for line in open(F, encoding="utf-8", errors="replace"):
    f = line.rstrip("\n").split(";")
    if f[0] == "O":
        s = f[2].lower()
        if "stream_" in s or "river_" in s or "streambed" in s:
            chan.append(s)
    elif f[0] == "W":
        W[int(f[1])][(f[2], float(f[3]))] = dict(y=float(f[5]), ground=float(f[7]), pond=f[9] == "true", depth=float(f[11]))
print("channel objects", len(chan), "sampled", len(W))
out = {}
for fam in ("stream_14", "river_24"):
    ids = [i for i in W if fam in chan[i]]
    rows = {k: [] for k in ("centre", "in6", "out12")}
    for i in ids:
        w = W[i]
        rows["centre"].append(w[("x", 0.0)]["ground"] - w[("x", 0.0)]["y"])
        for o in (-6.0, 6.0):
            rows["in6"].append(w[("x", o)]["ground"] - w[("x", o)]["y"])
        for o in (-12.0, 12.0):
            rows["out12"].append(w[("x", o)]["ground"] - w[("x", o)]["y"])
    res = {"pieces": len(ids)}
    for k, a in rows.items():
        a = np.array(a)
        res[k] = dict(q10_25_50_75_90=[round(float(v), 2) for v in np.quantile(a, [.1, .25, .5, .75, .9])],
                      frac_below=round(float((a < 0).mean()), 3))
    out[fam] = res
print(json.dumps(out, indent=1))
