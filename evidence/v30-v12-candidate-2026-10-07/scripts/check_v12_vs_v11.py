"""Check the v12 inland terrain against the v11's: classes and levels identical, heights changed only on navigable
(class 3) vertices and only upwards; reports the changed vertices and, per class, the inland water vertices whose bed is
under 0.85 m (the top of the engine sea band) in both. Exits non-zero on any violation.
Usage: check_v12_vs_v11.py V11.npz V12.npz OUT.json"""
import json
import sys

import numpy as np

a, b = np.load(sys.argv[1]), np.load(sys.argv[2])
cls = a['cls']
ok = np.array_equal(cls, b['cls'])
la, lb = a['level'], b['level']
ok &= np.array_equal(np.isnan(la), np.isnan(lb)) and np.array_equal(la[~np.isnan(la)], lb[~np.isnan(lb)])
ha, hb = a['heights'].astype(np.float64), b['heights'].astype(np.float64)
d = hb - ha
ch = d != 0
inland = np.nan_to_num(la, nan=-1.0) > 0.80
res = {'classes_and_levels_identical': bool(ok),
       'changed_vertices': int(ch.sum()),
       'changed_by_class': {int(k): int((ch & (cls == k)).sum()) for k in np.unique(cls[ch])},
       'raised_max_m': round(float(d.max()), 3), 'lowered_max_m': round(float(max(0.0, -d.min())), 3),
       'bed_under_0p85_inland_by_class': {int(k): {'v11': int(((cls == k) & inland & (ha < 0.85)).sum()),
                                                   'v12': int(((cls == k) & inland & (hb < 0.85)).sum())}
                                          for k in (2, 3, 5, 6, 7)}}
res['status'] = 'PASS' if (ok and set(res['changed_by_class']) <= {3} and res['lowered_max_m'] == 0) else 'FAIL'
with open(sys.argv[3], 'w', encoding='utf-8', newline='\n') as f:
    f.write(json.dumps(res, indent=1) + '\n')
print(json.dumps(res, indent=1))
sys.exit(0 if res['status'] == 'PASS' else 1)
