"""Read-only source/geometry discriminator before the one-model MLOD plan."""
from pathlib import Path
import hashlib,json,sys,time,struct
import numpy as np
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'dry-road-mlod-discovery-20261028';O.mkdir(exist_ok=False);start=time.monotonic()
sys.dont_write_bytecode=True;sys.path.insert(0,str(W/'tools/water'));from review_compact_collision_v31 import load
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=R/'pilot-kit7-fc-20261026/source/baltic_stream_pilot/cs_kit_118_0000.p3d';assert sha(p)=='bbf4d5e40dfcb3bf5216981f10cbf21db681d403ea51c4e20676956289207c5a'
candidate=R/'dry-bed-road-candidate-20261028/kit-118-candidate.npz';assert sha(candidate)=='93168efe934d9ff8a95bde1ceff3e54d0667bb0b358b36c0b7c028a443fa707d'
header,lods,blobs=load(p);assert struct.unpack('<4sII',header)==(b'MLOD',257,4)
original=np.load(R/'pilot-visible-surface-extraction-20261028/models/cs_kit_118_0000.npz');grid=original['source_grid'];new=np.load(candidate)['grid'][:len(grid)];origin=np.array([8262.,7.,8934.]);old=grid.reshape(-1,3)-origin;desired=new.reshape(-1,3)-origin;delta=desired-old
index={tuple(v):i for i,v in enumerate(old)};assert len(index)==len(old);surfaces=[]
for li in (0,3):
 l=lods[li];xyz=np.array([x.coords for x in l.points]);assert np.array_equal(xyz[:len(old)],old)
 assert len(xyz)==845 and len(l.facenormals)==845 and len(l.faces)==1544
 assert struct.unpack_from('<4s6I',blobs[li])==(b'P3DM',28,256,len(l.points),len(l.facenormals),len(l.faces),0)
 faces=l.faces[:1520];tris=np.array([[v.point_index for v in f.vertices] for f in faces]);assert tris.max()<819
 cross=np.cross(old[tris[:,1]]-old[tris[:,0]],old[tris[:,2]]-old[tris[:,0]]);cross/=np.linalg.norm(cross,axis=1)[:,None];accum=np.zeros_like(old)
 for j in range(3):np.add.at(accum,tris[:,j],cross)
 accum/=np.linalg.norm(accum,axis=1)[:,None]
 if li==3:accum=-accum
 assert np.array_equal(accum.astype(np.float32),np.array(l.facenormals[:819],np.float32))
 assert all(v.point_index==v.normal_index for f in l.faces for v in f.vertices)
 surfaces.append(dict(lod=li,bed_vertices=len(old),changed_y=int(np.count_nonzero(delta[:,1])),normal_algorithm_reproduces_source_float32=True))
geo=lods[1];gpoints=np.array([x.coords for x in geo.points]);normal_ids=[];face_index={id(f):i for i,f in enumerate(geo.faces)};point_index={id(p):i for i,p in enumerate(geo.points)};mapping=[];components=[];seen_faces=[];seen_points=[]
expected={tuple(sorted(tuple(v) for v in old[t])) for t in original['source_triangles']}
for name,sel in geo.selections.items():
 ids=[point_index[id(x)] for x in sel.points];fs=[face_index[id(x)] for x in sel.faces];assert len(ids)==6 and len(fs)==8
 coords=gpoints[ids];tops=[];bottoms=[]
 for gi in ids:
  xyz=gpoints[gi];key=tuple(xyz)
  if key in index:tops.append(index[key]);mapping.append([gi,index[key],0.])
  else:
   key=tuple(xyz+[0,180/512,0]);assert key in index;bottoms.append(index[key]);mapping.append([gi,index[key],-180/512])
 assert sorted(tops)==sorted(bottoms) and len(tops)==3;assert tuple(sorted(tuple(v) for v in old[tops])) in expected
 changed=bool(np.any(delta[tops,1]));components.append(dict(name=name,changed=changed,points=ids,faces=fs));seen_faces+=fs;seen_points+=ids
 for fi in fs:
  f=geo.faces[fi];inds=[v.point_index for v in f.vertices];ns={v.normal_index for v in f.vertices};assert len(ns)==1;normal_ids.extend(ns)
  tri=gpoints[inds];normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal)
  assert np.array_equal(normal.astype(np.float32),np.array(geo.facenormals[next(iter(ns))],np.float32))
assert sorted(seen_faces)==list(range(12160)) and sorted(seen_points)==list(range(9120)) and sorted(normal_ids)==list(range(12160))
assert np.array_equal(old.min(0),desired.min(0)) and np.array_equal(old.max(0),desired.max(0))
np.savez_compressed(O/'geometry-map.npz',mapping=np.array(mapping),delta=delta,source_local=old,candidate_local=desired)
(O/'components.json').write_text(json.dumps(components,indent=2)+'\n')
result=dict(status='SINGLE_MLOD_EXACT_PRISM_MAPPING_CONFIRMED',source_sha256=sha(p),candidate_sha256=sha(candidate),surfaces=surfaces,geometry=dict(components=1520,faces=12160,vertices=9120,changed_components=sum(x['changed'] for x in components),mass=sum(x.mass for x in geo.points),depth=180/512),bounds_unchanged=True,seconds=time.monotonic()-start)
(O/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
