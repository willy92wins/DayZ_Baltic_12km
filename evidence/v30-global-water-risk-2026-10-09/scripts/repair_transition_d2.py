"""Complete the existing dry-floor transition, keeping native water consumers."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from shapely.geometry import shape
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009'); E=W/'evidence/v30-global-water-risk-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'))
from finish_shores_v30 import discard_steeper_land_faces
from v30_common import cell_planes
from audit_fairway_triangles_v30 import records
from audit_pond_topology import compare,controls
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008/candidate-c1r3p/terrain_valley.npz')
water_source=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
assert sha(source)=='9c3011b8af5279e807630d4e91512d2e95a434463d3523a5b4074e70bc7cc8f6'
assert sha(water_source)=='e0d35db0a7a26f9ec055d57f0c9573a1dd2c27911ec8b084274283f5884cffd1'
t=dict(np.load(source)); w=np.load(water_source); h=t['heights'].astype(float);wet=t['cls']>0
plane=cell_planes(w['cls'],w['level']); corridor=np.zeros_like(wet);nc=0
paths=[Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson'),W/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']
for path in paths:
    for f in json.loads(path.read_text())['features']:
        if f['properties'].get('kind','corridor24m')!='corridor24m':continue
        corridor.ravel()[np.unique(records(shape(f['geometry']),plane)['ids'])]=True;nc+=1
physical=np.zeros_like(wet)
refs=[W/'evidence/v30-valley-smoothing-2026-10-08/c1r3p-probe-reference.json',W/'evidence/v30-bug-recheck-2026-10-08/wave-fixed-reference.json']
for path in refs:
    for p in json.loads(path.read_text())['points']:
        r=int(np.floor((12282-p['z'])/6));c=int(np.floor(p['x']/6));physical[r:r+2,c:c+2]=True
fixed=wet|t['reserve']|t['platform']|t['beach']|corridor|physical
fixed[:2]=True;fixed[-2:]=True;fixed[:,:2]=True;fixed[:,-2:]=True
eligible=~fixed&(h>=1.4-1e-6)&(h<1.8-1e-5)
v=h.copy();v[eligible]=1.8
v,recovery=discard_steeper_land_faces(v,h,t['cls'])
out=B/'candidate-d2'
if out.exists():
    # A report-serialization repair may resume only an identical saved candidate.
    saved=dict(np.load(out/'terrain.npz'))
    assert all(np.array_equal(saved[k],v.astype(t['heights'].dtype) if k=='heights' else t[k],equal_nan=True) for k in t)
else:
    out.mkdir()
    np.savez_compressed(out/'terrain.npz',**dict(t,heights=v.astype(t['heights'].dtype)))
    np.savez_compressed(out/'scope.npz',fixed=fixed,corridor=corridor,physical=physical,eligible=eligible)
topology,_=compare(h,v,plane);topology['controls']=controls()
(E/'d2-pond-topology.json').write_text(json.dumps(topology,indent=2)+'\n')
report=dict(status='BUILT_PENDING_INDEPENDENT_GATES',terrain_sha256=sha(out/'terrain.npz'),source_sha256=sha(source),
    water_source_sha256=sha(water_source),changed_vertices=int((v!=h).sum()),eligible_vertices=int(eligible.sum()),
    max_raise=float((v-h).max()),corridors=nc,recovery=recovery,pond_topology=topology['status'],
    remaining_low_free=int((~fixed&(h>=1.4-1e-6)&(v<1.8-1e-5)).sum()),
    inputs={str(p):sha(p) for p in [*paths,*refs]})
(E/'d2-authoring.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
