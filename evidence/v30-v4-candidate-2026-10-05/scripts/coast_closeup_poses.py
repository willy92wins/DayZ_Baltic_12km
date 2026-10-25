"""Oblique close-up poses along the sea waterline (0.75 m contour) near the tide-view sites, on a given terrain."""
import json
import sys

import contourpy
import numpy as np

sys.path.insert(0, r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
                   r'\codex-handoff-review-74f290\tools\terrain')
from v30_common import N, tri_sample  # noqa: E402

terrain, out = sys.argv[1], sys.argv[2]
h = np.load(terrain)['heights'].astype(float)
SEEDS = {'COAST_FLAT1': (5141.4, 10341.3), 'COAST_FLAT2': (6828.0, 11646.0), 'COAST_FLAT3': (4122.0, 9300.0),
         'COAST_FLAT4': (4744.2, 11950.2), 'COAST_EDGE1': (2091.0, 7371.0)}
poses = []
for name, (sx, sz) in SEEDS.items():
    c0, c1 = int((sx - 180) / 6), int((sx + 180) / 6) + 1
    r0, r1 = int((12282 - sz - 180) / 6), int((12282 - sz + 180) / 6) + 1
    X = np.arange(c0, c1) * 6.0
    Z = 12282.0 - np.arange(r0, r1) * 6.0
    gen = contourpy.contour_generator(x=X, y=Z, z=h[r0:r1, c0:c1] - 0.75, line_type=contourpy.LineType.Separate)
    lines = [ln for ln in gen.lines(0.0) if len(ln) >= 20]
    best = None
    for ln in lines:
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ln, axis=0), axis=1))]
        q = np.arange(0, s[-1], 2.0)
        p = np.column_stack([np.interp(q, s, ln[:, 0]), np.interp(q, s, ln[:, 1])])
        d = np.hypot(p[:, 0] - sx, p[:, 1] - sz)
        k = int(np.argmin(d))
        if (best is None or d[k] < best[0]) and 15 <= k < len(p) - 15:
            best = (float(d[k]), p, k)
    assert best is not None, name
    dist, p, k = best
    p0 = p[k]
    t = p[k + 10] - p[k - 10]
    t /= np.linalg.norm(t)
    n = np.array([-t[1], t[0]])
    if tri_sample(h, *(p0 + 10 * n)) < tri_sample(h, *(p0 - 10 * n)):
        n = -n                                   # n points to land
    cam = p0 + 14 * n - 22 * t
    look = p0 + 18 * t
    gy = float(tri_sample(h, cam[0], cam[1]))
    poses.append({'name': name, 'cam_pos': [round(float(cam[0]), 1), round(gy + 7.0, 2), round(float(cam[1]), 1)],
                  'look_at': [round(float(look[0]), 1), 0.75, round(float(look[1]), 1)],
                  'note': f'waterline point {p0[0]:.1f},{p0[1]:.1f} at {dist:.0f} m from the seed; camera ground {gy:.2f} m'})
json.dump(poses, open(out, 'w', encoding='utf-8'), indent=1)
for p in poses:
    print(json.dumps(p))
