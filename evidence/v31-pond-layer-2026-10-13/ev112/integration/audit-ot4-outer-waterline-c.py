"""Additional diagnostic, outside the original central OT4 acceptance domain. No changed criterion."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial import cKDTree
O=Path(__file__).parent;sys.path.insert(0,str(O.parent/'ev110/scripts/shore-gates'));import gatelib as G
findings=json.loads((O/'review-terrain-r1-evidence-c/findings.json').read_text())
xy=np.array(findings['ot4_coverage']['outside_touching_final_shore_xz'])
sites={'c2':(10235,9398),'c3':(8568,10414),'c4':(10417,9426),'c5':(8227,10468),'c6':(3588,6867),'c7':(9678,2661)}
site_id=cKDTree(np.array(list(sites.values()))).query(xy)[1]
owner=np.full((2048,2048),-1,np.int16)
rc=np.c_[np.rint((G.ZTOP-xy[:,1])/6).astype(int),np.rint(xy[:,0]/6).astype(int)]
owner[rc[:,0],rc[:,1]]=site_id
h=np.load(O/'terrain-ev112-c.npz')['heights'].astype(float);f=np.load(O/'fp-ev112-c/footprint.npz')
q,v,geo=G.wiggle_map(h,G.corner_water(f['plane'].astype(float),f['field'].astype(float)),full=True)
r,c,A=G.point_triangle(q[:,0],q[:,1]);ids=np.stack([owner[r,c],np.where(A,owner[r,c+1],owner[r+1,c]),owner[r+1,c+1]],1)
so=G.segment_owners(owner,geo['cell'],geo['tri'])
prior=np.load(O/'shores/terrain-shores-work/owner.npy');ps=G.segment_owners(prior,geo['cell'],geo['tri']);covered=(ps>=0).any(1)
coverage_vertex=np.zeros_like(owner,dtype=bool)
for (r,c),tri in zip(geo['cell'][covered],geo['tri'][covered]):
 coverage_vertex[r,c]=True;coverage_vertex[r+1,c+1]=True
 if tri==0:coverage_vertex[r,c+1]=True
 else:coverage_vertex[r+1,c]=True
rows=[]
for sid,name in enumerate(sites):
 keep=(ids==sid).any(1)&np.isfinite(v);where=np.flatnonzero(keep);j=where[np.argmax(v[where])] if len(where) else None
 rows.append(dict(site=name,vertices=int((site_id==sid).sum()),vertices_incident_to_G2_treated_waterline=int(coverage_vertex[rc[site_id==sid,0],rc[site_id==sid,1]].sum()),samples=int(keep.sum()),p90=float(np.percentile(v[keep],90)) if keep.any() else None,maximum=float(v[j]) if j is not None else None,maximum_xz=q[j].tolist() if j is not None else None,coverage=G.coverage(geo,(so==sid).any(1))))
result=dict(status='DIAGNOSTIC_OUTSIDE_ORIGINAL_OT4_DOMAIN',scope=__doc__,terrain_sha256=G.sha(O/'terrain-ev112-c.npz'),consumer_sha256=G.sha(Path(G.__file__)),vertices=len(xy),vertices_incident_to_G2_treated_waterline=int(coverage_vertex[rc[:,0],rc[:,1]].sum()),groups=rows)
hb=np.load(O/'causeway/terrain-cw.npz')['heights'].astype(float)
qb,vb,gb=G.wiggle_map(hb,G.corner_water(f['plane'].astype(float),f['field'].astype(float)),full=True)
r,c,A=G.point_triangle(qb[:,0],qb[:,1]);ib=np.stack([owner[r,c],np.where(A,owner[r,c+1],owner[r+1,c]),owner[r+1,c+1]],1)
for sid,row in enumerate(rows):
 keep=(ib==sid).any(1)&np.isfinite(vb)
 row['diagnostic_before_OT4_with_final_water_plane']=dict(samples=int(keep.sum()),p90=float(np.percentile(vb[keep],90)) if keep.any() else None,maximum=float(vb[keep].max()) if keep.any() else None)
result['comparison_limit']='Before heights on the final water plane, to isolate geometry; not a pre-OT4 footprint/topology acceptance.'
(O/'ot4-outer-waterline-c.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result),flush=True)
