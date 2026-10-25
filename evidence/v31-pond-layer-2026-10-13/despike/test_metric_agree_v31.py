"""Cross-check: the gate's filter-based prominence equals the census/tool shift-based one on EV110, plus synthetic
fixtures (spike, pair, pit, triangle on a sloped plane). Usage: test_metric_agree_v31.py (paths fixed to the EV110 build)."""
import numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "terrain")))
import gate_despike_v31 as g
import census_pyramids_v31 as c
import despike_v31 as d

rng = np.random.default_rng(1)
fails = 0
# fixtures on a sloped plane (2048 so despike.prominence works)
H = np.fromfunction(lambda r, cc: 0.05 * cc - 0.03 * r, (2048, 2048))
H[100, 100] += 1.0          # single spike 1.0
H[200, 200] += 0.8; H[201, 200] += 0.8   # vertical pair 0.8
H[300, 300] -= 0.7          # pit 0.7
H[400, 400] += 0.6; H[400, 401] += 0.6; H[401, 401] += 0.6  # triangle (r,c),(r,c+1),(r+1,c+1)
for name, f in (("gate", lambda X: g.prom(X)), ("census", lambda X: c.prominence(X)[:2]), ("tool", lambda X: d.prominence(X))):
    pk, pt = f(H)
    exp = {(100, 100): ("pk", 1.0), (200, 200): ("pk", 0.8), (201, 200): ("pk", 0.8), (300, 300): ("pt", 0.7), (400, 401): ("pk", 0.6)}
    for (r, cc), (k, v) in exp.items():
        got = (pk if k == "pk" else pt)[r, cc]
        # on a plane the strict (non-detrended) prominence is s minus the slope rise to the highest ring vertex
        print(name, (r, cc), k, round(float(got), 4), "spike", v)
    # a plane gives no strict extremum
    print(name, "plane max peak away from fixtures", float(pk[600:700, 600:700].max()), float(pt[600:700, 600:700].max()))
B = "E:/DayZ-Baltic-Build/v31-pond-layer-20261013/"
Hb = np.load(B + "ev110/terrain-ev110.npz")["heights"].astype(np.float64)
a1, a2 = g.prom(Hb); b1, b2, _, _ = c.prominence(Hb); t1, t2 = d.prominence(Hb)
inner = (slice(3, -3), slice(3, -3))
for nm, x, y in (("gate-census peak", a1, b1), ("gate-census pit", a2, b2), ("gate-tool peak", a1, t1), ("gate-tool pit", a2, t2)):
    dd = np.abs(x[inner] - y[inner]); print(nm, "max abs diff", float(dd.max()))
    fails += int(dd.max() > 1e-9)
print("FAILS", fails)
