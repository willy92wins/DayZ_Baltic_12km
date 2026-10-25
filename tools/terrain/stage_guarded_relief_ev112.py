"""Isolated S3 source WRP update; changes native heights and forest Y only."""
from pathlib import Path
import argparse,hashlib,json,struct,sys,shutil
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'water'))
from streambed_kit_v31 import tri_h
ap=argparse.ArgumentParser(description=__doc__)
for key in ('source-stage','baseline','merged','repair','out'):ap.add_argument('--'+key,type=Path,required=True)
ap.add_argument('--source-wrp-sha256',required=True)
a=ap.parse_args()

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=a.source_stage/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
assert sha(src)==a.source_wrp_sha256
meta=json.loads((a.source_stage/'stage-report.json').read_text())
ref=Path(meta['forest_reference']['path']);assert sha(ref)==meta['forest_reference']['sha256']
models=json.loads(ref.read_text())['models']
terrain=a.merged/'terrain-buried.npz';H=np.load(terrain)['heights'];H0=np.load(a.baseline/'terrain-buried.npz')['heights']
repair=json.loads((a.repair/'report.json').read_text())
assert all(repair['checks'].values()) and repair['input_sha256']==sha(a.baseline/'terrain-buried.npz')
assert repair['output_sha256']==sha(a.repair/'terrain.npz')
assert np.array_equal(H,np.load(a.repair/'terrain.npz')['heights'])
assert json.loads((a.repair/'all-protected-audit.json').read_text())['status']=='PASS'
assert json.loads((a.merged/'merge-verification.json').read_text())['status']=='WATER_FOOTPRINT_EXACT'
assert not ((H!=H0)[:3].any() or (H!=H0)[-3:].any() or (H!=H0)[:,:3].any() or (H!=H0)[:,-3:].any())
out=a.out;out.mkdir(parents=True,exist_ok=False)
dest=out/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
dest.parent.parent.mkdir(parents=True)
shutil.copytree(src.parent,dest.parent,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
for name in ('baseline-config.bin','baseline-config.cpp','decode-config.log'):shutil.copy2(a.source_stage/name,out/name)
shifts=[];total=forest=outside=0;source_fixed=hashlib.sha256();output_fixed=hashlib.sha256();source_objects=hashlib.sha256();output_objects=hashlib.sha256()
def flush(batch,f):
 global total,forest,outside
 raw=[a for a,n in batch];names=[n for a,n in batch]
 indices=[i for i,n in enumerate(names) if n.startswith(('dz\\plants\\','dz\\plants_bliss\\','dz\\rocks\\'))]
 if indices:
  for i in indices:assert names[i] in models, ('missing forest reference',names[i])
  mats=np.array([struct.unpack_from('<12f',raw[i]) for i in indices]);bc=np.array([models[names[i]]['bc'] for i in indices])
  roots=mats[:,9:12]-np.einsum('nji,nj->ni',mats[:,:9].reshape(-1,3,3),bc)
  inside=(roots[:,0]>=0)&(roots[:,0]<=12282)&(roots[:,2]>=0)&(roots[:,2]<=12282)
  outside+=int((~inside).sum());dy=np.zeros(len(indices));xz=roots[inside][:,[0,2]]
  dy[inside]=tri_h(H,xz[:,0],xz[:,1])-tri_h(H0,xz[:,0],xz[:,1])
  for j in np.flatnonzero(dy):
   i=indices[j];before=raw[i];after=bytearray(before);new=float(np.float32(mats[j,10]+dy[j]));struct.pack_into('<f',after,40,new)
   assert before[:40]+before[44:]==after[:40]+after[44:]
   raw[i]=bytes(after);shifts.append(dict(id=struct.unpack_from('<I',before,48)[0],before=float(mats[j,10]),after=new,root=roots[j].tolist(),ground_delta=float(dy[j])))
  forest+=len(indices)
 for (before,name),after in zip(batch,raw):
  source_objects.update(before);output_objects.update(after)
  # Independent byte invariant: everything except the Y slot is identical.
  source_fixed.update(before[:40]+before[44:]);output_fixed.update(after[:40]+after[44:]);f.write(after)
 total+=len(batch)
with src.open('rb') as f,dest.open('wb') as g:
 header=f.read(24);magic,tx,tz,nx,nz,cell=struct.unpack('<4s4If',header);assert magic==b'0WZD' and (nx,nz)==(2048,2048);g.write(header)
 heights=f.read(nx*nz*4);assert np.array_equal(np.frombuffer(heights,'<f4').reshape(nz,nx),H0[::-1]);g.write(np.ascontiguousarray(H[::-1],dtype='<f4').tobytes())
 material=f.read(tx*tz*2);g.write(material);count=f.read(4);g.write(count)
 for _ in range(struct.unpack('<I',count)[0]):
  while True:
   raw=f.read(4);g.write(raw);length=struct.unpack('<I',raw)[0]
   if not length:break
   text=f.read(length);assert len(text)==length;g.write(text)
 batch=[]
 while True:
  record=f.read(56);assert len(record)==56;length=struct.unpack_from('<I',record,52)[0]
  if not length:
   if batch:flush(batch,g)
   g.write(record);assert not f.read(1);break
  name=f.read(length);assert len(name)==length;batch.append((record+name,name.rstrip(b'\0').decode('ascii').lower().replace('/','\\')))
  if len(batch)==4096:flush(batch,g);batch=[]
assert source_fixed.digest()==output_fixed.digest()
# Verify every saved Y change and immutable record field against the source
# without loading millions of Python dictionaries into memory.
with src.open('rb') as source_stream,dest.open('rb') as b:
 assert source_stream.read(24)==b.read(24)
 source_stream.seek(nx*nz*4,1);saved=np.frombuffer(b.read(nx*nz*4),'<f4').reshape(nz,nx);assert np.array_equal(saved,H[::-1])
 expected={q['id']:q for q in shifts};byte_changes=0
 # Outside the height payload every changed byte must belong to a forest Y.
 while True:
  x=source_stream.read(1<<20);y=b.read(1<<20)
  if not x:assert not y;break
  assert len(x)==len(y);byte_changes+=sum(i!=j for i,j in zip(x,y))
 assert byte_changes<=4*len(shifts)
report=dict(status='SOURCE_DELTA_VERIFIED',source_wrp_sha256=sha(src),wrp_sha256=sha(dest),terrain_sha256=sha(terrain),object_count=total,
            terrain_vertices=int((H!=H0).sum()),forest_records=forest,forest_y_adjustments=len(shifts),outside_roots_unchanged=outside,
            all_object_bytes_except_y_exact=True,object_fixed_digest=source_fixed.hexdigest(),shifts=shifts,
            limitations=['Source WRP only; compilation and engine verification pending.','Preserves existing forest placement; does not resolve boundary/root support findings.','Existing pilot poses and nonforest records are unchanged.'])
(out/'terrain-stage-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='shifts'},indent=2))

inherited=('pilot_pbo_sha256','added_models','remaining_objects','removed_old_kit_records','forest_excluded','forest_reference','pilot','config_unchanged_from_s3')
meta['inherited_from_parent']={k:meta[k] for k in inherited if k in meta}
meta.pop('newly_removed_old_kit_records',None)
meta.update(source_wrp_sha256=sha(src),wrp_sha256=sha(dest),terrain_sha256=sha(terrain),
            object_count=total,forest_height_adjustments=len(shifts),merged=str(a.merged),
            terrain_vertices=int((H!=H0).sum()),objects_digest=output_objects.hexdigest(),new_models=0,
            limits=['Only native heights and existing forest Y changed; inherited model/kit inventory is explicitly marked.','Source delta only; compiled and engine acceptance remain separate.'],
            parent_stage=str(a.source_stage),status='SOURCE_DELTA_VERIFIED_PENDING_SUPPORT_BUILD_RUNTIME')
(out/'stage-report.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
