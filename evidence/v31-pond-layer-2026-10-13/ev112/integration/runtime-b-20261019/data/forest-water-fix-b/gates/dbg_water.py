import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402
import glib  # noqa: E402
import geom  # noqa: E402

T = gcfg.tool()
MR = glib.MapRecords(sys.argv[1])
mods = MR.ref["models"]
t = np.load(gcfg.TERRAIN)
H = t["heights"].astype(float)
fp = np.load(gcfg.FOOTPRINT)
plane, env = fp["plane"], fp["env_plane"]
for i in [int(v) for v in sys.argv[2:]]:
    nm = MR.names[i]
    m = MR.m[i]
    M = m[:9].reshape(3, 3).T
    bc = np.array(mods[nm]["bc"])
    org = m[9:12] - M @ bc
    s = np.linalg.norm(M[:, 0])
    fam = mods[nm]["family"]
    R = 0.25 if fam == "reed" else mods[nm]["base_radius_plan"] * s + 0.25
    pond = geom.disc_min(H, org[[0]], org[[2]], np.array([R]), lambda r, c: plane[r, c])
    mwp = (0.25 if fam == "reed" else mods[nm]["base_radius_plan"] * mods[nm]["scale_q"][-1] + 0.25) + 0.05
    dense = T.disc_wet_dense(H, plane, env, org[[0]], org[[2]], np.array([mwp]))
    g = np.linspace(-R, R, 401)
    X, Z = np.meshgrid(org[0] + g, org[2] + g)
    ins = np.hypot(X - org[0], Z - org[2]) <= R
    h, _, r0, c0 = T.tri_eval(H, X[ins], Z[ins])
    r0, c0 = np.minimum(r0, 2046), np.minimum(c0, 2046)
    pl = plane[r0, c0]
    dd = h - np.nan_to_num(pl, nan=1e9)
    k = int(np.argmin(dd))
    w, s2 = T.wet_at(H, plane, env, X[ins][[k]], Z[ins][[k]])
    print(nm.split(chr(92))[-1], "origin", np.round(org, 2), "R", round(R, 3), "mw", round(mwp, 3), "gate pond", pond,
          "dense hit", dense, "grid min h-plane", round(float(dd[k]), 3), "at", round(float(X[ins][k]), 2), round(float(Z[ins][k]), 2),
          "cell", int(r0[k]), int(c0[k]), "plane", pl[k], "h", round(float(h[k]), 3), "wet_at", w, s2)
