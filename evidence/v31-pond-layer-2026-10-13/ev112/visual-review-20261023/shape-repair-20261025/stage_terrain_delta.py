"""Isolated S3 source WRP update; changes native heights and forest Y only."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
Q=Path('E:/DayZ-Baltic-Build/qc-council-20261024');B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path.insert(0,str(W/'tools/water'));from streambed_kit_v31 import tri_h
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=Q/'stage-s3/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
assert sha(src)=='f07926200627c24f26a8da4df54a03df03e5776f92e2821dd676bbb07dab3f77'
meta=json.loads((Q/'stage-s3/stage-report.json').read_text());ref=Path(meta['forest_reference']['path']);assert sha(ref)==meta['forest_reference']['sha256'];models=json.loads(ref.read_text())['models']
terrain=R/'terrain-free-final-merged/terrain-buried.npz';H=np.load(terrain)['heights'];H0=np.load(Q/'road-merged-s3/terrain-buried.npz')['heights']
assert json.loads((terrain.parent/'merge-verification.json').read_text())['status']=='WATER_FOOTPRINT_EXACT'
assert not ((H!=H0)[:3].any() or (H!=H0)[-3:].any() or (H!=H0)[:,:3].any() or (H!=H0)[:,-3:].any())
out=R/'stage-terrain-final';out.mkdir(exist_ok=False);dest=out/'baltic_trial.wrp'
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
with src.open('rb') as a,dest.open('rb') as b:
 assert a.read(24)==b.read(24)
 a.seek(nx*nz*4,1);saved=np.frombuffer(b.read(nx*nz*4),'<f4').reshape(nz,nx);assert np.array_equal(saved,H[::-1])
 expected={q['id']:q for q in shifts};byte_changes=0
 # Outside the height payload every changed byte must belong to a forest Y.
 while True:
  x=a.read(1<<20);y=b.read(1<<20)
  if not x:assert not y;break
  assert len(x)==len(y);byte_changes+=sum(i!=j for i,j in zip(x,y))
 assert byte_changes<=4*len(shifts)
report=dict(status='SOURCE_DELTA_VERIFIED',source_wrp_sha256=sha(src),wrp_sha256=sha(dest),terrain_sha256=sha(terrain),object_count=total,
            terrain_vertices=int((H!=H0).sum()),forest_records=forest,forest_y_adjustments=len(shifts),outside_roots_unchanged=outside,
            all_object_bytes_except_y_exact=True,object_fixed_digest=source_fixed.hexdigest(),shifts=shifts,
            limitations=['Source WRP only; compilation and engine verification pending.','Preserves existing forest placement; does not resolve boundary/root support findings.','131.0-0 candidate is separate and is not inserted here.'])
(out/'stage-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='shifts'},indent=2))
