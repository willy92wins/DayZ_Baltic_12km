"""Compare every compiled object with the editable staged WRP, with bounded memory.

The existing Livonia OPRW object locator is heuristic (terrain is not decoded).
Its result is accepted here only if the complete staged ID set, model names and
all float32 matrices match. This does not prove rendered geometry or terrain.
"""
from pathlib import Path
import sys,json,struct,hashlib,argparse,tempfile
import numpy as np
O=Path(__file__).parent;B=O.parent
P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(P/'tools/terrain'));from patch_surface_v31 import pbo_index,sha
sys.path.insert(0,str(B/'handoff-20261018/deps/forest-livonia'));import oprw_objects

def staged_objects(path):
 with Path(path).open('rb') as f:
  magic,tx,tz,nx,nz,cell=struct.unpack('<4s4If',f.read(24));assert magic==b'0WZD'
  f.seek(nx*nz*4+tx*tz*2,1);n=struct.unpack('<I',f.read(4))[0]
  for _ in range(n):
   while True:
    k=struct.unpack('<I',f.read(4))[0]
    if not k:break
    f.seek(k,1)
  while True:
   raw=f.read(56);assert len(raw)==56
   values=struct.unpack('<12f2I',raw);ident,k=values[-2:]
   if not k:assert not f.read(1);break
   name=f.read(k);assert len(name)==k
   yield ident,name.decode('ascii').rstrip('\0'),values[:12]

def differences(expected,got,model_names):
 return dict(ids=int(np.count_nonzero(expected['id']!=got['id'])),models=int(np.count_nonzero(expected['name']!=model_names[got['mi']])),
             matrices=int(np.count_nonzero(np.any(expected['m']!=got['m'],axis=1))),nonfinite=int(np.count_nonzero(~np.isfinite(got['m']).all(axis=1))))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--pbo',required=True);ap.add_argument('--staged',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 dest=Path(a.out);assert not dest.exists();dest.mkdir()
 _,index=pbo_index(a.pbo);off,n=index['baltic_trial.wrp']
 with open(a.pbo,'rb') as f:f.seek(off);wrp=f.read(n)
 assert wrp[:4]==b'OPRW';version=struct.unpack_from('<I',wrp,4)[0];assert version in (29,32),version
 extracted=dest/'compiled.wrp';extracted.write_bytes(wrp);del wrp
 d=oprw_objects.read(extracted);rec=d['rec'];names=np.array(d['models'],object);order=np.argsort(rec['id']);rec=rec[order]
 assert len(np.unique(rec['id']))==len(rec) and np.isfinite(rec['m']).all()
 dtype=[('id','<u4'),('name',object),('m','<f4',(12,))];rows=[];count=0;fails=dict(ids=0,models=0,matrices=0,nonfinite=0);missing=0;maxdiff=0.;control=None
 def check(chunk):
  nonlocal count,missing,maxdiff,control
  e=np.array(chunk,dtype=dtype);q=np.searchsorted(rec['id'],e['id']);valid=q<len(rec)
  valid[valid]&=rec['id'][q[valid]]==e['id'][valid];missing+=int((~valid).sum());count+=len(e)
  ev=e[valid];g=rec[q[valid]];diff=differences(ev,g,names)
  for k,v in diff.items():fails[k]+=v
  if len(ev):maxdiff=max(maxdiff,float(np.max(np.abs(ev['m']-g['m']))))
  if control is None and len(ev)>2:
   controls=[]
   for key in ('matrix','model','id'):
    bad=g[:3].copy()
    if key=='matrix':bad['m'][0,9]+=1.
    elif key=='model':bad['mi'][0]=(int(bad['mi'][0])+1)%len(names)
    else:bad['id'][0]^=1
    detected=any(differences(ev[:3],bad,names).values());assert detected;controls.append(dict(mutation=key,detected=detected))
   control=controls
 for row in staged_objects(a.staged):
  rows.append(row)
  if len(rows)>=50000:check(rows);rows=[]
 if rows:check(rows)
 ok=count==len(rec) and missing==0 and not any(fails.values()) and control is not None
 result=dict(result='PASS' if ok else 'FAIL',compiled_version=version,compiled_objects=len(rec),staged_objects=count,missing_staged_ids=missing,differences=fails,max_abs_matrix_difference=maxdiff,
             controls=control,pbo=dict(path=a.pbo,sha256=sha(a.pbo)),staged=dict(path=a.staged,sha256=sha(a.staged)),compiled_wrp_sha256=sha(extracted),
             locator_sha256=sha(oprw_objects.__file__),array_start=d['start'],array_end=d['end'],models=len(names),scope=__doc__)
 (dest/'result.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=1));sys.exit(0 if ok else 1)

if __name__=='__main__':main()
