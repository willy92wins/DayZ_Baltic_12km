from pathlib import Path
import hashlib,json,mmap,struct,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');Q=Path('E:/DayZ-Baltic-Build/qc-council-20261024')
sys.path.insert(0,str(W/'tools/navigation'));from waterway_common import sample
stage=R/'stage-terrain-final';report=json.loads((stage/'stage-report.json').read_text());shifts={x['id']:x for x in report['shifts']};seen=set()
ref=Path(json.loads((Q/'stage-s3/stage-report.json').read_text())['forest_reference']['path']);models=json.loads(ref.read_text())['models']
src=Q/'stage-s3/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';dst=stage/'baltic_trial.wrp';h0=np.load(Q/'road-merged-s3/terrain-buried.npz')['heights'].astype(float);h=np.load(R/'terrain-free-final-merged/terrain-buried.npz')['heights'].astype(float)
objects=0;maxerror=0.
with src.open('rb') as sf,dst.open('rb') as df,mmap.mmap(sf.fileno(),0,access=mmap.ACCESS_READ) as a,mmap.mmap(df.fileno(),0,access=mmap.ACCESS_READ) as b:
 assert a.size()==b.size() and a[:24]==b[:24]
 _,tx,tz,nx,nz,_=struct.unpack('<4s4If',a[:24]);offset=24+nx*nz*4;start=offset;offset+=tx*tz*2;n=struct.unpack_from('<I',a,offset)[0];offset+=4
 for _ in range(n):
  while True:
   length=struct.unpack_from('<I',a,offset)[0];offset+=4
   if not length:break
   offset+=length
 assert a[start:offset]==b[start:offset]
 while True:
  ident,length=struct.unpack_from('<II',a,offset+48);size=56+length;before=a[offset:offset+size];after=b[offset:offset+size]
  if not length:assert before==after and offset+size==a.size();break
  if ident not in shifts:assert before==after,('unexpected object delta',ident)
  else:
   assert before[:40]+before[44:]==after[:40]+after[44:]
   name=before[56:].rstrip(b'\0').decode('ascii').lower().replace('/','\\');assert name.startswith(('dz\\plants\\','dz\\plants_bliss\\','dz\\rocks\\'))
   matrix=np.array(struct.unpack_from('<12f',before));root=matrix[9:12]-matrix[:9].reshape(3,3).T.dot(models[name]['bc'])
   expected=matrix[10]+float(sample(h,np.array([root[0]+200000]),np.array([root[2]]))[0]-sample(h0,np.array([root[0]+200000]),np.array([root[2]]))[0])
   actual=struct.unpack_from('<f',after,40)[0];error=abs(actual-expected);maxerror=max(maxerror,error)
   assert error<=2*abs(float(np.spacing(np.float32(max(abs(actual),abs(expected))))))+1e-7,(ident,error)
   seen.add(ident)
  objects+=1;offset+=size
assert seen==set(shifts) and objects==report['object_count']
result=dict(status='INDEPENDENT_SOURCE_DELTA_PASS',objects=objects,forest_y_verified=len(seen),nonshifted_objects_byte_exact=objects-len(seen),max_ground_consumer_error_m=maxerror,wrp_sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),consumer_sha256=hashlib.sha256(Path(sample.__code__.co_filename).read_bytes()).hexdigest(),scope='Independent native-ground interpolation and byte comparison; root-disc/engine/navmesh acceptance remains pending.')
(stage/'independent-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
