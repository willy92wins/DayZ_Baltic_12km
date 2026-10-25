"""Road sections that run on a causeway: water (any class) within REACH metres on both sides of the centre line.
Samples each graded road chain (verify_roads_v30.road_chains) every 2 m and groups consecutive causeway samples."""
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

REPO = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees'
            r'\codex-handoff-review-74f290')
sys.path.insert(0, str(REPO / 'tools' / 'terrain'))
from v30_common import tri_sample  # noqa: E402
from verify_roads_v30 import road_chains  # noqa: E402

REACH, MIN_LEN, GAP = 30.0, 60.0, 20.0
t = np.load('E:/DayZ-Baltic-Build/v30-v5/coast/terrain_coast.npz')
h, cls = t['heights'].astype(np.float64), t['cls']
water = cls > 0


def wet(p):
    rr = np.clip(np.rint((12282 - p[:, 1]) / 6).astype(int), 0, 2047)
    cc = np.clip(np.rint(p[:, 0] / 6).astype(int), 0, 2047)
    return water[rr, cc], cls[rr, cc]


sections = []
for n, p in enumerate(road_chains()):
    if len(p) < 2:
        continue
    st = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    s = np.arange(0, st[-1], 2.0)
    if len(s) < 3:
        continue
    q = np.column_stack([np.interp(s, st, p[:, d]) for d in (0, 1)])
    tg = np.gradient(q, axis=0)
    nrm = np.column_stack([-tg[:, 1], tg[:, 0]]) / np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
    left = np.zeros(len(q), bool)
    right = np.zeros(len(q), bool)
    wcls = np.zeros(len(q), int)
    for off in np.arange(6.0, REACH + 0.1, 3.0):
        wl, cl = wet(q + nrm * off)
        wr, cr = wet(q - nrm * off)
        left |= wl
        right |= wr
        wcls = np.where(wl & (wcls == 0), cl, wcls)
    on = left & right
    # close gaps shorter than GAP, then keep runs of at least MIN_LEN
    idx = np.flatnonzero(on)
    if idx.size == 0:
        continue
    runs, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if (i - prev) * 2.0 > GAP:
            runs.append((start, prev))
            start = i
        prev = i
    runs.append((start, prev))
    for a, b in runs:
        length = (b - a) * 2.0
        if length < MIN_LEN:
            continue
        zc = tri_sample(h, q[a:b + 1, 0], q[a:b + 1, 1])
        sections.append(dict(chain=n, s0=float(s[a]), s1=float(s[b]), length=length,
                             x0=round(float(q[a, 0])), z0=round(float(q[a, 1])), x1=round(float(q[b, 0])),
                             z1=round(float(q[b, 1])), crest_p5=round(float(np.percentile(zc, 5)), 2),
                             crest_p95=round(float(np.percentile(zc, 95)), 2),
                             water_class=int(np.bincount(wcls[a:b + 1][wcls[a:b + 1] > 0]).argmax())
                             if (wcls[a:b + 1] > 0).any() else 0))
sections.sort(key=lambda d: -d['length'])
print('causeway sections', len(sections), 'total m', round(sum(d['length'] for d in sections)))
for d in sections:
    print(d)
