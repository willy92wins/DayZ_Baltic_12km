from pathlib import Path
import hashlib,io,json,struct,sys,time
import numpy as np
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(__file__).parent
sys.path[:0]=[str(W/'tools/water'),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
import py3d
from compact_stream_collision_v31 import partition,add_component
import compact_stream_collision_v31 as packing
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=R/'river-131-a';out=R/'river-131-compact-a';out.mkdir(exist_ok=False);src=out/'source/baltic_stream_pilot';src.mkdir(parents=True);prov=out/'provenance';prov.mkdir()
author=json.loads((old/'author-report.json').read_text());(prov/'input-author-report.json').write_bytes((old/'author-report.json').read_bytes())
for path in (Path(__file__),Path(packing.__file__)): (prov/path.name).write_bytes(path.read_bytes())
for name in ('terrain.npz','envelope.npy','cover.npy','131.0-0-surfaces.npz'):(out/name).write_bytes((old/name).read_bytes())
for name in ('config.cpp','$PBOPREFIX$'):(src/name).write_bytes((old/'source/baltic_stream_pilot'/name).read_bytes())
rows=[]
for inst in author['instances']:
 t=time.monotonic();name=inst['model'].split('\\')[-1];path=old/'source/baltic_stream_pilot'/name;assert sha(path)==inst['sha256'];data=path.read_bytes();f=io.BytesIO(data);header=f.read(12);assert struct.unpack('<4sII',header)==(b'MLOD',257,4)
 blobs=[];visual=None
 for index in range(4):
  start=f.tell();lod=py3d.LOD(f);blobs.append(data[start:f.tell()])
  if index==0:visual=lod
 assert f.tell()==len(data)
 ids={v.point_index for face in visual.faces if 'water_streambed.rvmat' not in face.material for v in face.vertices};count=max(ids)+1
 assert ids==set(range(count)) and count%39==0
 grid=np.array([p.coords for p in visual.points[:count]]).reshape(-1,39,3)
 parts=partition(grid,vertical_budget=.03,horizontal_budget=.01);geo=py3d.LOD();geo.resolution=1e13;geo.properties.update({'class':'house','damage':'no'});volumes=[];shifts=[]
 for index,part in enumerate(parts,1):
  shift=float(np.ceil(max(0.,part['roof_upper_error_bound_m'])/2*512)/512);part['points']=part['points'].copy();part['points'][:,1]-=shift
  volumes.append(add_component(py3d,geo,part,index));shifts.append(shift)
 single=py3d.P3D();single.lods.append(geo);temp=prov/(name+'.geometry-lod');single.save(str(temp));geometry=temp.read_bytes()[12:]
 candidate=header+blobs[0]+geometry+blobs[2]+blobs[3];dest=src/name;dest.write_bytes(candidate)
 # Preserve original byte segments, not a lossy read/write of visual data.
 raw=io.BytesIO(candidate);raw.seek(12);saved=[]
 for index in range(4):
  start=raw.tell();py3d.LOD(raw);saved.append(candidate[start:raw.tell()])
 assert all(saved[i]==blobs[i] for i in (0,2,3)) and raw.tell()==len(candidate)
 prior_count=inst['collision_components'];inst.update(source_collision_components=prior_count,collision_components=len(parts),signed_collision_volume=float(sum(volumes)),sha256=sha(dest))
 row=dict(model=name,before_components=prior_count,after_components=len(parts),before_bytes=len(data),after_bytes=len(candidate),non_geometry_lods_byte_exact=True,
          max_centering_shift_m=max(shifts),local_roof_bound_m=max(p['roof_upper_error_bound_m'] for p in parts),seconds=time.monotonic()-t)
 rows.append(row);print(row,flush=True)
report=dict(status='CANDIDATE_GLOBAL_OVERLAY_PENDING',input_author_sha256=sha(old/'author-report.json'),packing_source_sha256=sha(packing.__file__),author_source_sha256=sha(__file__),
            raw_roof_budget_m=.03,horizontal_budget_m=.01,required_global_vertical_error_m=.02,
            before_components=sum(r['before_components'] for r in rows),after_components=sum(r['after_components'] for r in rows),models=rows,
            limitations=['Full-mesh overlay, closure, binary and engine checks required.','No map-wide performance acceptance.'])
author['collision_packing']=report;(out/'author-report.json').write_text(json.dumps(author,indent=2),encoding='utf-8');(out/'packing-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='models'},indent=2))
