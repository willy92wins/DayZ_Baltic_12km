from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from scipy.ndimage import label,find_objects
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path.insert(0,str(W/'tools/terrain'))
import despike_v31 as D
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=R/'combined-merged';z=np.load(base/'terrain-buried.npz');a={k:z[k] for k in z.files};h=a['heights'].astype(float)
env=np.load(base/'envelope.npy');fp=base/'bury-work/fp0/footprint.npz'
shore=D.shoreline_vertices(h,fp,np.ones_like(h,bool))
free,prot,_=D.free_domain(a,env,[str(B/'records-nonforest.json')],shore)
road=np.load(R/'terrain-free-final/domains.npz')['road'];free&=~road
for key in ('v31_dam','v31_causeway','v31_shore_ramp','v31_continuous_pilot','v31_road_repair','v31_road_mesh_repair'):
    if key in a:free&=~a[key]
rr,cc=np.mgrid[:2048,:2048];free&=np.hypot(cc*6.-10397.4,12282.-rr*6.-9421.9)>60
pk,pt=D.prominence(h)
floor=np.minimum(h,D.lower_floor(a,env));lo=np.where(free,np.maximum(h-.75,floor),h);hi=np.where(free,h+.75,h)
reports=[]
for kind,field in [('peak',pk),('pit',pt)]:
    groups,n=label(field>.3,structure=np.ones((3,3)))
    for group,sl in enumerate(find_objects(groups),1):
        coords=np.argwhere(groups[sl]==group)+[sl[0].start,sl[1].start]
        target={tuple(c) for c in coords};constraints={};impossible=[]
        for r,c in target:
            for dr in (-1,0):
                for dc in (-1,0):
                    for shape,(points,ring) in enumerate(D.rings()):
                        pp=[(r+dr+x,c+dc+y) for x,y in points];qq=[(r+dr+x,c+dc+y) for x,y in ring]
                        if (r,c) not in pp or any(min(x)<0 or max(x)>=2048 for x in pp+qq):continue
                        aa,bb=(pp,qq) if kind=='peak' else (qq,pp)
                        before=min(h[x] for x in aa)-max(h[x] for x in bb)
                        if before<=.3:continue
                        bound=min(lo[x] for x in aa)-max(hi[x] for x in bb)
                        key=(r+dr,c+dc,shape);constraints[key]=float(bound)
                        if bound>.29999:impossible.append(key)
        reports.append(dict(kind=kind,representative=coords[0].tolist(),vertices=len(coords),
                            protected_vertices=int(sum(not free[x] for x in target)),
                            fault_shapes=len(constraints),independently_feasible=bool(constraints and not impossible),
                            impossible_shapes=len(set(impossible)),bounds_max_m=max(constraints.values(),default=None),
                            domains=sorted({key for key,m in prot.items() if any(m[x] for x in target)}),
                            target_vertices=coords.tolist()))
out=R/'guarded-relief-discovery';out.mkdir(exist_ok=False)
np.savez_compressed(out/'domains.npz',free=free,road=road,shore=shore)
result=dict(status='BOUND_FEASIBILITY_ONLY_NOT_A_CORRECTION',terrain_sha256=sha(base/'terrain-buried.npz'),
            footprint_sha256=sha(fp),groups=reports,summary=dict(collections.Counter((x['kind']+'_feasible_'+str(x['independently_feasible'])) for x in reports)),
            limits=['Independent box feasibility is necessary, not sufficient for coupled prominence, crease or water constraints.','Protected heights, shoreline edge endpoints, roads and 015-45 remain fixed.'])
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['summary']))
