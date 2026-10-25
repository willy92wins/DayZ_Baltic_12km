"""Relief V30, chosen option (Guillermo 2026-10-02): V29 hills in the high zones, option B plains elsewhere.

mix = h * A + (1 - h) * B, with V29 exact inside the envelope of engineered water, Narva and map edges.
  A  design_relief_v30a.py: V29 relief with the old area protections removed (no straight or elliptical walls).
  B  design_relief_v30.py: relief regenerated from the real topography, plains and gentle valleys.
  h  high-zone weight. Codex's factor only picks which upland is a high zone; the outline follows the real
     large-scale elevation, so the hill areas end along natural contours instead of round blobs.
"""
import json
import os
import sys

import numpy as np

A_DIR, B_DIR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
P = {"pick_factor": [6.0, 10.0], "outline_elevation": [3.5, 6.0]}
os.makedirs(OUT, exist_ok=True)


def ease(t):
    t = np.clip(t, 0, 1)
    return t * t * t * (10 + t * (-15 + 6 * t))


def main():
    a = np.load(os.path.join(A_DIR, "relief_v30.npz"))
    b = np.load(os.path.join(B_DIR, "relief_v30.npz"))
    v29, ha, hb = a["v29"].astype("float64"), a["new"].astype("float64"), b["new"].astype("float64")
    f_old, big, env = b["f_old"].astype("float64"), b["big"].astype("float64"), b["envelope"]
    h = ease((f_old - P["pick_factor"][0]) / (P["pick_factor"][1] - P["pick_factor"][0])) * \
        ease((big - P["outline_elevation"][0]) / (P["outline_elevation"][1] - P["outline_elevation"][0]))
    mix = h * ha + (1 - h) * hb
    mix[env] = v29[env]
    assert np.array_equal(mix[env], v29[env]) and np.isfinite(mix).all()

    def slope(x):
        gy, gx = np.gradient(x, 6.0)
        return np.degrees(np.arctan(np.hypot(gx, gy)))

    land = v29 > 1.0
    s29, sm = slope(v29), slope(mix)
    stats = {"params": P,
             "height_max": [round(float(v29.max()), 1), round(float(mix.max()), 1)],
             "height_land_mean": [round(float(v29[land].mean()), 2), round(float(mix[land].mean()), 2)],
             "flat_lt2deg_pct": [round(100 * float((s29[land] < 2).mean()), 1), round(100 * float((sm[land] < 2).mean()), 1)],
             "slope_pct_over": {f">{t}deg": [round(100 * float((s29[land] > t).mean()), 1), round(100 * float((sm[land] > t).mean()), 1)] for t in (10, 20, 25, 30, 35)},
             "envelope_exact": True,
             "changed_cells_pct": round(100 * float((np.abs(mix - v29) > 0.01).mean()), 1)}
    np.savez_compressed(os.path.join(OUT, "relief_v30.npz"), new=mix.astype("float32"), v29=a["v29"], high=h.astype("float32"), envelope=env)
    with open(os.path.join(OUT, "relief_v30_stats.json"), "wb") as f:
        f.write(json.dumps(stats, indent=1, ensure_ascii=False).encode("utf-8"))
    print(json.dumps({k: v for k, v in stats.items() if k != "params"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
