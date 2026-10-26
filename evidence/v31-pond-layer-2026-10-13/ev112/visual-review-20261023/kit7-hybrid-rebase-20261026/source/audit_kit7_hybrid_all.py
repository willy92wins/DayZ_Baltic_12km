from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path.insert(0,str(W/'tools/terrain'))
import despike_v31 as D
import census_pyramids_v31 as P
from repair_free_shapes_ev112 import s3_road_guard
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tp=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz';cp=R/'kit7-hybrid-pilot-20261026/candidate/terrain.npz'
z=np.load(tp);arrays={k:z[k] for k in z.files};h=arrays['heights'];v=np.load(cp)['heights']
env=np.load(R/'river-kit7-merged-byteexact-20261026/envelope.npy');fp=R/'river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz'
shore=D.shoreline_vertices(h.astype(float),fp,np.ones_like(h,bool))
free,_,_=D.free_domain(arrays,env,[str(B/'records-nonforest.json')],shore)
road,road_hashes=s3_road_guard();free&=~road
for key in ('v31_dam','v31_causeway','v31_shore_ramp','v31_continuous_pilot','v31_road_repair','v31_road_mesh_repair'):
    if key in arrays:free&=~arrays[key]
rr,cc=np.indices(h.shape);free&=np.hypot(cc*6.-10397.4,12282.-rr*6.-9421.9)>60
stored=np.load(R/'kit7-remaining-relief-discovery-20261026/domains.npz')
provenance={key:bool(np.array_equal(value,stored[key])) for key,value in [('free',free),('shore',shore),('road',road)]}
assert all(provenance.values())
pk,pt,*_=P.prominence(h.astype(float));checks=[]
for kind,field in [('peak',pk),('pit',pt)]:
    for r,c in np.argwhere((field>.3)&~free):
        sl=np.s_[max(0,r-4):r+5,max(0,c-4):c+5]
        near=(np.hypot(rr[sl]-r,cc[sl]-c)<=4)&free[sl]
        if not ((v[sl]!=h[sl])&near).any():continue
        bound=np.maximum(h[sl],h[r,c]) if kind=='peak' else np.minimum(h[sl],h[r,c])
        bad=((v[sl]>bound) if kind=='peak' else (v[sl]<bound))&near
        checks.append(dict(kind=kind,vertex=[int(r),int(c)],violations=int(bad.sum())))
result=dict(status='PASS' if not any(x['violations'] for x in checks) else 'FAIL',provenance=provenance,
            affected_protected_extrema=len(checks),checks=checks,road_inputs=road_hashes,
            inputs={str(p):sha(p) for p in (tp,cp,fp,B/'records-nonforest.json',Path(__file__))})
(R/'kit7-hybrid-pilot-20261026/candidate/all-protected-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','inputs','road_inputs')}))
print('violations',sum(x['violations'] for x in checks))
