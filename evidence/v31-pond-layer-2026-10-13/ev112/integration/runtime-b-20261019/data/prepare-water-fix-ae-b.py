"""Four-vertex physical candidate. Shore change is wholly underwater, preserving its waterline and dry control."""
from pathlib import Path
import numpy as np,json,sys,hashlib
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=O/'water-fix-b';D.mkdir(exist_ok=False)
sys.path.insert(0,str(P/'tools/water'));import shore_ramp_v31 as sr;import streambed_kit_v31 as kit
sys.path.insert(0,str(P/'tools/terrain'));from v30_common import tri_sample
a=dict(np.load(O/'terrain-ev112-c.npz'));old=a['heights'];h=old.copy();f=np.load(O/'fp-ev112-c/footprint.npz');W,fp=sr.corner_water(f['plane'],f['field'])
ps=json.loads((O/'probe-c/points.json').read_text());p=next(p for p in ps if p['id']==3836);r,c,w=kit.tri_weights(np.array([[p['x'],p['z']]]));assert (int(r[0,2]),int(c[0,2]))==(324,1135)
shore_target=float(old[324,1135])-(float(tri_sample(old,[p['x']],[p['z']])[0])-.446)/float(w[0,2])
patch=[(796,1721,1.72),(963,1876,1.90),(631,1685,1.65),(324,1135,shore_target)];entries=[]
for r,c,target in patch:
 assert not any(a[k][r,c] for k in ('reserve','platform','narva','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_lagoon'))
 assert np.hypot(c*6-10397.4,12282-r*6-9421.9)>60
 for k,(dr,dc) in enumerate(sr.COFF):
  water=W[r-dr,c-dc,k];assert (old[r,c]<water)==(target<water)
 h[r,c]=target;entries.append(dict(row=r,col=c,x=c*6,z=12282-r*6,before=float(old[r,c]),after=float(h[r,c])))
# All vertices of every triangle incident to the changed shore vertex were and remain under sea.
incident=[]
for cr in (323,324):
 for cl in (1134,1135):
  for ti,tr in enumerate(sr.TRIS):
   verts=[(cr+sr.COFF[k][0],cl+sr.COFF[k][1]) for k in tr]
   if (324,1135) in verts:
    assert all(old[rr,cc]<.75 and h[rr,cc]<.75 for rr,cc in verts)
    incident.append(dict(cell=[cr,cl],triangle=ti,vertices=verts))
xs=[p['x'] for p in ps];zs=[p['z'] for p in ps];b=tri_sample(old,xs,zs);after=tri_sample(h,xs,zs);changes=[dict(id=p['id'],family_id=p['family_id'],family=p['family'],kind=p['kind'],before=float(x),after=float(y)) for p,x,y in zip(ps,b,after) if abs(x-y)>1e-6]
assert not any(e['family']=='shores' and e['kind']=='shore_dry' for e in changes)
a['heights']=h;np.savez_compressed(D/'terrain.npz',**a)
out=dict(status='EXPERIMENTAL_NOT_ACCEPTED',patch=entries,incident_sea_triangles_all_wet=incident,probe_height_changes=changes,terrain_sha256=hashlib.sha256((D/'terrain.npz').read_bytes()).hexdigest(),masks_unchanged=True,footprint_unchanged=True,protected_vertices_changed=0,scope='No gate, source, records or deployed PBO changed. Original strict FAIL remains. Four vertices: 0.15m axis lowering, two 0.19m old-bed raises, underwater shore vertex lowering without any incident shoreline or dry probe change.')
(D/'candidate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
