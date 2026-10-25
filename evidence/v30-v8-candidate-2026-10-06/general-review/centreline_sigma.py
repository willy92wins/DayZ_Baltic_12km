"""Corners per km and displacement of the design river/stream centre lines under Gaussian smoothing along the arc,
ends anchored (junctions and mouths stay), for several sigmas. Input: tests/water_v3/profiles.npz (6 m resampled OSM
courses: columns s, x, z, ground, level, bed)."""
import json

import numpy as np
from scipy.ndimage import gaussian_filter1d

P = np.load(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\tests\water_v3\profiles.npz')


def smooth(pts, sigma_m, step):
    k = sigma_m / step
    if k <= 0:
        return pts
    sm = gaussian_filter1d(pts, k, axis=0, mode='nearest')
    n = len(pts)
    i = np.arange(n)
    w = np.clip(np.minimum(i, n - 1 - i) / (2 * k), 0, 1)[:, None]
    return pts + (sm - pts) * w


def turns(pts):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    q = np.arange(0, s[-1], 12.0)
    pp = np.column_stack([np.interp(q, s, pts[:, 0]), np.interp(q, s, pts[:, 1])])
    ang = np.degrees(np.arctan2(*np.diff(pp, axis=0).T[::-1]))
    return np.abs((np.diff(ang) + 180) % 360 - 180), s[-1]


rows = {}
for sigma in (0, 6, 12, 18, 24, 36):
    km = 0.0; t45 = 0; t20 = 0; shifts = []
    for k in P.files:
        a = P[k]
        pts = a[:, 1:3].astype(float)
        if len(pts) < 9:
            continue
        step = float(np.median(np.diff(a[:, 0])))
        sp = smooth(pts, sigma, step)
        tt, L = turns(sp)
        km += L / 1000; t45 += int((tt > 45).sum()); t20 += int((tt > 20).sum())
        shifts.append(np.linalg.norm(sp - pts, axis=1))
    sh = np.concatenate(shifts)
    rows[sigma] = {'turns_over_45_per_km': round(t45 / km, 2), 'turns_over_20_per_km': round(t20 / km, 2),
                   'shift_p50_m': round(float(np.percentile(sh, 50)), 2), 'shift_p95_m': round(float(np.percentile(sh, 95)), 2),
                   'shift_max_m': round(float(sh.max()), 1), 'km': round(km, 1)}
print(json.dumps(rows, indent=1))
