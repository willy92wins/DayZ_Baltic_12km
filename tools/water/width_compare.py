"""Visible width (medial axis on the native-triangle waterline) of the thin-V vertices, before vs after.
Usage: width_compare.py <terrainA> <fpA> <terrainB> <fpB> <mask_terrain_with_v31_v_stream>"""
import sys, runpy
import numpy as np
from scipy.ndimage import label
vs = runpy.run_path(sys.argv[0].replace("width_compare.py", "v_streams_v31.py"), run_name="lib")
tA, fA, tB, fB, mpath = sys.argv[1:6]
m = np.load(mpath); mask = m["v31_v_thalweg"] if "v31_v_thalweg" in m.files else m["v31_v_stream"]
lab, n = label(mask, np.ones((3, 3)))
res = {}
for tag, tp, fp in (("A", tA, fA), ("B", tB, fB)):
    H = np.load(tp)["heights"].astype(float); pl = np.load(fp)["plane"].astype(float)
    vc = np.where(np.isfinite(pl), pl, np.nan)
    ws = []
    for i in range(1, n + 1):
        rr, cc = np.nonzero(lab == i)
        r0, r1 = max(rr.min() - 3, 0), min(rr.max() + 3, 2047); c0, c1 = max(cc.min() - 3, 0), min(cc.max() + 3, 2047)
        wv = vs["visible_width"](H, vc, r0, r1, c0, c1)
        ws.append(wv[(lab[r0:r1 + 1, c0:c1 + 1] == i)])
    w = np.concatenate(ws)
    res[tag] = [round(float(x), 2) for x in np.percentile(w, [10, 50, 90])] + [round(float((w == 0).mean()), 3)]
print("width p10/p50/p90 m, share of vertices with no water ridge nearby:", res)
