"""Per-tile comparison of the v9 and v10 surface layers: PAA sizes of the satellite (s_) and mask (m_) files, the
number of distinct mask colours per tile, and the tiles whose files changed most. Usage: compare_surface_tiles.py"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

A = Path('E:/DayZ-Baltic-Build/v30-redesign/surface/layers')
B = Path('E:/DayZ-Baltic-Build/v30-v10/surface/layers')


def colours(p):
    a = np.asarray(Image.open(p).convert('RGB')).reshape(-1, 3)
    u, n = np.unique(a, axis=0, return_counts=True)
    return int((n > 0.0005 * len(a)).sum())


rows = []
for pa in sorted(A.glob('*_lc?.paa')):
    pb = B / pa.name
    sa, sb = pa.stat().st_size, pb.stat().st_size
    rows.append((pa.name, sa, sb))
size = {k: [(n, a, b) for n, a, b in rows if n.startswith(k)] for k in ('s_', 'm_')}
out = {}
for k, v in size.items():
    a = np.array([r[1] for r in v], float)
    b = np.array([r[2] for r in v], float)
    rel = (b - a) / a
    order = np.argsort(-np.abs(rel))[:8]
    out[k] = {'tiles': len(v), 'v9_total': int(a.sum()), 'v10_total': int(b.sum()),
              'v9_min_max': [int(a.min()), int(a.max())], 'v10_min_max': [int(b.min()), int(b.max())],
              'rel_change_p50_p99_max': [round(float(np.percentile(np.abs(rel), q)), 4) for q in (50, 99, 100)],
              'top': [{'tile': v[i][0], 'v9': v[i][1], 'v10': v[i][2], 'rel': round(float(rel[i]), 3)} for i in order]}
ca, cb = [], []
for pa in sorted(A.glob('m_*_lca.png'))[::8]:
    ca.append(colours(pa))
    cb.append(colours(B / pa.name))
out['mask_colours_sampled_every_8th'] = {'tiles': len(ca), 'v9_hist': np.bincount(ca).tolist(),
                                         'v10_hist': np.bincount(cb).tolist()}
print(json.dumps(out, indent=1))
