"""Offline planning screen of planar interpolation, never a generator result."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain')]
from prepare_visual_probe_v31 import height
from streambed_kit_v31 import tri_h
O=R/'kit7-nav-fine-width-diagnostic-20261027';O.mkdir(exist_ok=False)
M=R/'kit7-packed-nav-discovery-20261026/roadway.npz';T=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
H=np.load(T)['heights'];npz=np.load(M);meshes=[npz[k] for k in npz.files if k.endswith('_dry')]
low=np.array([v[:,:,[0,2]].min(axis=(0,1)) for v in meshes]);high=np.array([v[:,:,[0,2]].max(axis=(0,1)) for v in meshes])
known=set(json.loads((R/'kit7-nav-after12-screen-20261027/result.json').read_text())['known_queries'])
samples=[]
for line in (R/'kit7-nav12-consumer-20261027/runtime.log').read_text(encoding='utf-8-sig').splitlines():
    f=line.split(';')
    if f[0]=='P' and f[1] in known:
        points=[[float(v) for v in a.strip('<>').split(',')] for a in f[3:]]
        samples.append(dict(query=f[1],index=int(f[2]),nav=points[0],engine_roadway=points[2],excess_m=abs(points[0][1]-points[2][1])-.801))
assert len(samples)==14
def top(q):
    values=[float(tri_h(H,*q))]
    for ix in np.flatnonzero(np.all(q>=low-1e-7,axis=1)&np.all(q<=high+1e-7,axis=1)):
        y=height(meshes[ix],q)
        if y is not None:values.append(y)
    return max(values)
rows=[]
for width in [8.,9.5,9.625,9.75,9.875,10.,10.125,10.25,10.375,10.5,12.]:
    result=[]
    for s in samples:
        q=np.array(s['nav'])[[0,2]];x,z=np.floor(q/width)*width
        corners=np.array([[x,z+width],[x+width,z+width],[x+width,z],[x,z]])
        v=np.array([[p[0],top(p),p[1]] for p in corners])
        predictions=[height(v[np.array(ids)],q) for ids in [[[0,1,2],[0,2,3]],[[0,1,3],[1,2,3]]]]
        result.append(dict(query=s['query'],index=s['index'],failed_native=s['excess_m']>0,physical_y=s['engine_roadway'][1],predicted_y=predictions,worst_error=max(abs(y-s['engine_roadway'][1]) for y in predictions)))
    rows.append(dict(tile_width=width,grid_side=int(12288//width),tile_count=int(12288//width)**2,maximum_error_m=max(v['worst_error'] for v in result),samples=result))
prior=json.loads((R/'kit7-nav-after12-screen-20261027/result.json').read_text())
for width in (8.,12.):
    before=next(x for x in prior['candidates'] if x['tile_width']==width)
    after=next(x for x in rows if x['tile_width']==width)
    assert abs(before['maximum_known14_estimate_m']-after['maximum_error_m'])<1e-9
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=dict(status='PLANNING_ESTIMATE_ONLY',candidates=rows,inputs={str(p):sha(p) for p in [Path(__file__),M,T,R/'kit7-nav12-consumer-20261027/runtime.log',R/'kit7-nav-after12-screen-20261027/result.json']},limits=['Corner heights from terrain and dry packed Roadway, not generated navigation polygons.','No obstacle contour, polygon partition, voxel quantisation or wet floor simulation.','Both quad diagonals screened at the same fourteen existing waypoints. All native607 checks remain mandatory.'])
(O/'result.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps([{k:v for k,v in row.items() if k!='samples'} for row in rows],indent=2))
