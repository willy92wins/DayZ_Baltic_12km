"""Native positive depth without presence flags: expose, do not silently accept."""
from pathlib import Path
import json,csv,sys
from collections import Counter
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09';B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import cell_planes,vertex_plane_bounds
t=dict(np.load(B/'measured-bank-bed-r1/terrain.npz'))
w=np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz');pmin,pmax=vertex_plane_bounds(cell_planes(w['cls'],w['level'],sea_cut=.51))
rows=[]
for p in csv.DictReader((E/'halo-r2-unflagged-scalar-queries.csv').open(),delimiter=';'):
    r,c=int(p['row']),int(p['col']);g,plane,depth=map(float,(p['ground'],p['plane'],p['depth']))
    lo,hi=pmin[r,c],pmax[r,c]
    sea=.64<=plane<=.86
    pond=np.isfinite(hi) and lo-.02501<=plane<=hi+.02501
    rows.append(dict(row=r,col=c,x=c*6,z=12282-r*6,ground=g,plane=plane,depth=depth,clearance_nominal=g-plane,
        minimum_plane=None if not np.isfinite(lo) else float(lo),maximum_plane=None if not np.isfinite(hi) else float(hi),
        plane_source='sea_range' if sea and not pond else 'pond_source_range' if pond else 'unclassified',
        protected={k:bool(t[k][r,c]) for k in ('reserve','platform','beach')}))
author=json.loads((E/'halo-fix-r2-authoring.json').read_text());allowed={p['object_id'] for p in author['changes'] if p['closed_micro_points']}
delta=json.loads((B/'compiled-domain-discrepancies-halo-r2.json').read_text())
seams=all(p['object_id'] in allowed and p['expected_level'] is not None and 0<=p['expected_level']-p['level']<=.02501 for p in delta)
assert seams and len(delta)==10
out=dict(status='WAVE_CONTACTS_REQUIRE_TEMPORAL_CLASSIFICATION',points=rows,counts=dict(Counter(p['plane_source'] for p in rows)),
    protected={k:sum(p['protected'][k] for p in rows) for k in ('reserve','platform','beach')},
    nominal_above_ground=sum(p['clearance_nominal']<0 for p in rows),min_nominal_clearance=min(p['clearance_nominal'] for p in rows),
    max_native_positive_depth=max(p['depth'] for p in rows),compiled_nontrivial_mismatches_all_authorized_seam_overlaps=seams,
    limits=['Presence flags are false at all 231 points; positive depth must not be silently treated as dry.','The scalar height API can return surfaces other than water. Matching source plane is evidence for a wave contact hypothesis; a temporal and compiled-coverage check remains required.','Not the visually confirmed inland residual, whose native depth stays negative.'])
(E/'scalar-wave-contact-classification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='points'},indent=2))
