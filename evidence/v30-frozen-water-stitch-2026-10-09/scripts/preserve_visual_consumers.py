"""Single repair: preserve one shallow body and the already compiled pilot field."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

OUT=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(OUT))
from audit_frozen_visual import W,B,domain,cell_planes,sha

h=np.load(B/'measured-bank-bed-r2/terrain.npz')['heights'].astype(float)
water=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
t=np.load(water);p=cell_planes(t['cls'],t['level'],sea_cut=.51)
assert sha(water)=='e0d35db0a7a26f9ec055d57f0c9573a1dd2c27911ec8b084274283f5884cffd1'
original=B/'frozen-field-reference/field.npy'
f=np.load(original)
legacy_path=Path('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008/stitched-water/visual_vertex_levels.npy')
legacy=np.load(legacy_path)
author=json.loads((W/'evidence/v30-curved-channel-pilot-2026-10-08/flat-water-authoring.json').read_text())
assert len(author['new_poses'])==538
mask=np.zeros_like(h,dtype=bool)
for tx,tz in author['affected_tiles']:
    # 1 cm halo intersects the neighboring native cells. Lock all support nodes.
    r0=max(0,2039-8*tz-1);r1=min(2048,2047-8*tz+2)
    c0=max(0,tx*8-1);c1=min(2048,tx*8+10)
    mask[r0:r1,c0:c1]=True
values=np.where(mask,legacy,np.nan)
pilot_mask=mask.copy()
d=domain(h,p); rr,cc=d['cells']
triangles=np.flatnonzero(d['labels']==768)
assert abs(d['body_area'][768]-1.7867487986845414)<1e-8
cells=np.unique(triangles//2)
assert {(int(rr[i]),int(cc[i])) for i in cells}=={(1813,1955),(1813,1956),(1814,1955),(1814,1956)}
target=float(p[rr[cells],cc[cells]].max())
body_nodes=[]
for i in cells:
    r,c=int(rr[i]),int(cc[i])
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):
        assert not pilot_mask[r+dr,c+dc], 'Unexpected intersection with frozen pilot'
        mask[r+dr,c+dc]=True;values[r+dr,c+dc]=target
        body_nodes.append((r+dr,c+dc))
for slot,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
    m=mask[dr:dr+2047,dc:dc+2047]&np.isfinite(p)
    v=values[dr:dr+2047,dc:dc+2047]
    f[:,:,slot][m]=v[m]
out=OUT/'preserved-field.npy';assert not out.exists();np.save(out,f)
report=dict(status='SOURCE_REPAIR_REQUIRES_CONSUMER',original_field_sha256=sha(original),field_sha256=sha(out),
            frozen_pilot_models=538,pilot_field_sha256=sha(legacy_path),locked_vertices=int(mask.sum()),
            shallow_component=768,shallow_plane_m=target,body_nodes=sorted(set(body_nodes)),
            terrain_unchanged=True,physical_lods_unchanged='No model authored yet',
            limits=['Local consumer constraints, not an accepted field. Global gates run next.',
                    'Locking all support vertices of 1 cm pilot halos preserves that interpolation before float32 compilation checks.'])
(OUT/'source-repair.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
