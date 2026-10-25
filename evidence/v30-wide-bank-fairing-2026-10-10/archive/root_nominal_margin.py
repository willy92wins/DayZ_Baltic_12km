"""Independent nominal-margin diagnostic; no wave bound or acceptance claim."""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
PLANE = ROOT.parent / 'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
paths = [BASE, ROOT / 'candidate-terrain.npz', PLANE]
B, H = (np.load(p)['heights'].astype(np.float64) for p in paths[:2])
P = np.load(PLANE).astype(np.float64)
points = []
for r, c in np.argwhere(B != H):
    levels = P[max(0, r-1):min(r+1, len(P)), max(0, c-1):min(c+1, P.shape[1])]
    finite = levels[np.isfinite(levels)]
    level = float(finite.max()) if finite.size else None
    points.append({'row': int(r), 'col': int(c), 'B': float(B[r,c]), 'H': float(H[r,c]),
                   'delta': float(H[r,c]-B[r,c]), 'incident_P_max': level,
                   'B_clearance': None if level is None else float(B[r,c]-level),
                   'H_clearance': None if level is None else float(H[r,c]-level)})
water = [p for p in points if p['incident_P_max'] is not None]
lowered = [p for p in water if p['delta'] < 0]
summary = {'changed': len(points), 'touch_incident_P': len(water),
           'lowered_touch_incident_P': len(lowered),
           'minimum_H_clearance_incident_P': min((p['H_clearance'] for p in water), default=None),
           'lowered_H_clearance_below_observed_EV87_19325mm': sum(p['H_clearance'] < .19325 for p in lowered)}
result = {'status': 'NOMINAL_DIAGNOSTIC_ONLY', 'summary': summary, 'points': points,
          'input_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
          'limits': ['An incident cell plane is not proof of compiled-face coverage at the vertex.',
                     '0.19325 m is an observed EV87 scalar sample, not a universal wave bound.',
                     'This does not accept or reject the candidate or claim rendered water.']}
(ROOT/'root-nominal-margin.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(summary))
