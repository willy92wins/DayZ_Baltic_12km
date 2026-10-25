"""Read-only certificate: is the floor conflict real without the 1 mm margin?"""
from pathlib import Path
import json
import sys
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/terrain'))
from audit_fairway_triangles_v30 import records,depths,sha
from v30_common import cell_planes

source=Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008/combined/terrain_inland.npz')
corridors=Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson')
t=np.load(source);h=t['heights'].astype(float);cls=t['cls'];level=t['level'];platform=t['platform']
plane=cell_planes(cls,level,sea_cut=.51)
r,c=np.indices(h.shape)
narva=np.hypot(c*6-2417.1428225906,12282-r*6-6889.8850822322)<=620
mutable=(cls==3)&~platform&~narva
recs=[records(shape(f['geometry']),plane) for f in json.loads(corridors.read_text())['features']]
out=[]
for target in (1.,.99):
    ids=[];weights=[];need=[]
    for rec in recs:
        d=depths(h,rec);use=d<target
        ids.append(rec['ids'][use]);weights.append(rec['weights'][use]);need.append(target-d[use])
    ids,weights,need=np.concatenate(ids),np.concatenate(weights),np.concatenate(need)
    variables=np.unique(ids[mutable.ravel()[ids]])
    lookup=np.full(h.size,-1,dtype=np.int32);lookup[variables]=np.arange(len(variables))
    cols=lookup[ids];use=(cols>=0)&(weights>0)
    rows=np.broadcast_to(np.arange(len(ids))[:,None],ids.shape)
    matrix=coo_matrix((weights[use],(rows[use],cols[use])),shape=(len(ids),len(variables))).tocsr()
    bound=np.full(len(variables),.1)
    high=level.ravel()[variables]>=2
    bound[high]=np.minimum(bound[high],np.maximum(0,h.ravel()[variables[high]]-1))
    result=linprog(np.ones(len(variables)),A_ub=-matrix,b_ub=-need,
                   bounds=np.column_stack([np.zeros(len(variables)),bound]),method='highs')
    # An individual inequality with insufficient capacity is a directly
    # inspectable impossibility witness, independent of the solver status.
    cap=matrix@bound
    impossible=np.flatnonzero(cap<need-1e-7)
    out.append(dict(target_depth_m=target,feasible=result.success,message=result.message,
                    variables=len(variables),constraints=len(need),impossible_rows=len(impossible),
                    witnesses=[dict(ids=ids[k].tolist(),weights=weights[k].tolist(),need_m=float(need[k]),
                                    capacity_m=float(cap[k])) for k in impossible[:5]]))
report=dict(status='FLOOR_CONFLICT_CERTIFICATE',source_sha256=sha(source),corridors_sha256=sha(corridors),
            results=out,scope='Only existing mutable navigable vertices, maximum lowering 0.1 m; no terrain authored.')
Path(__file__).with_name('floor-feasibility.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=1))
