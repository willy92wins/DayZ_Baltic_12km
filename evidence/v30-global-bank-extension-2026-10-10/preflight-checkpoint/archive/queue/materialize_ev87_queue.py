#!/usr/bin/env python
"""Materialize the EV87 seed inventory and EV93's first 17x17 layer. No terrain writes."""
from __future__ import annotations
import hashlib, json, os, tempfile
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT=Path(r'E:/DayZ-Baltic-Build')
OUT=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/queue')
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
CONS=ROOT/'v30-narva-dry-bank-relief-20261010/constraints.npz'
PRIOR=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
P=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
F=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'
WRP=ROOT/'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
EV87=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
PREFLIGHT=ROOT/'v30-global-strict-bank-relief-20261010/preflight.json'
LEDGER=ROOT/'v30-global-strict-bank-relief-20261010/queue-ledger.jsonl'
PLAN=ROOT/'v30-global-bank-extension-20261010/plan.md'
N=2048; CELL=6.0; Z0=12282.0; SEA=0.85; ANGLE=30.0001; PROM=0.1; HALF=8; SEPARATION=17
EXPECTED={
 'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 'constraints':'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
 'prior':'18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
 'P':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 'F':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
 'WRP':'3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6',
 'EV87':'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
 'preflight':'078112a24ffb7e5f0fa07777b55e9844820b4a246c686a7492fefe2aa2cbe85a',
 'ledger':'ac87b33eb999f1250e2fa34ac9368f30a788fd1110dac9c0d138c7255ab69e76',
 'plan':'ccc018a9e1cc8a51b075a91905b1cbe7d3cdaf72040e51992f2ac55db8ad7e82'
}
PATHS={'B':B,'constraints':CONS,'prior':PRIOR,'P':P,'F':F,'WRP':WRP,'EV87':EV87,'preflight':PREFLIGHT,'ledger':LEDGER,'plan':PLAN}

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def pin_inputs():
 got={k:sha(v) for k,v in PATHS.items()}
 for k,want in EXPECTED.items():
  if got[k]!=want:raise RuntimeError(f'{k} identity mismatch: {got[k]} != {want}')
 return got

def load_npz(path):
 with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}

def water_vertex_level(p,f):
 out=np.full((N,N),SEA,dtype=np.float64)
 pv=np.nan_to_num(np.asarray(p,dtype=np.float64),nan=SEA)
 for i,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
  fv=np.nan_to_num(np.asarray(f[:,:,i],dtype=np.float64),nan=SEA)
  lvl=np.maximum(SEA,np.maximum(pv,fv))
  np.maximum(out[dr:dr+N-1,dc:dc+N-1],lvl,out=out[dr:dr+N-1,dc:dc+N-1])
 return out

def edge_slices(mask,kind):
 if kind=='diag':return (mask[:-1,:-1],mask[:-1,1:],mask[1:,:-1],mask[1:,1:])
 if kind=='vertical':return (mask[:-1,:-2],mask[:-1,1:-1],mask[1:,1:-1],mask[1:,2:])
 return (mask[:-2,:-1],mask[1:-1,:-1],mask[1:-1,1:],mask[2:,1:])

def angles_by_edge(h):
 nw,ne,sw,se=(np.asarray(h,dtype=np.float64)[:-1,:-1],np.asarray(h,dtype=np.float64)[:-1,1:],
              np.asarray(h,dtype=np.float64)[1:,:-1],np.asarray(h,dtype=np.float64)[1:,1:])
 one=np.ones_like(nw);zero=np.zeros_like(nw)
 a=np.cross(np.stack((6*one,ne-nw,zero),axis=-1),np.stack((6*one,se-nw,-6*one),axis=-1))
 b=np.cross(np.stack((6*one,se-nw,-6*one),axis=-1),np.stack((zero,sw-nw,-6*one),axis=-1))
 a/=np.linalg.norm(a,axis=-1)[...,None];b/=np.linalg.norm(b,axis=-1)[...,None]
 pairs=(('diag',a,b),('vertical',a[:,:-1],b[:,1:]),('horizontal',b[:-1,:],a[1:,:]))
 result={}
 for name,x,y in pairs:
  result[name]=np.degrees(np.arctan2(np.linalg.norm(np.cross(x,y),axis=-1),np.einsum('ijk,ijk->ij',x,y)))
 return result

def node_angle_stats(angles):
 vmax=np.full((N,N),-np.inf,dtype=np.float64);hot=np.zeros((N,N),dtype=bool)
 for kind,a in angles.items():
  for dst,v in zip(edge_slices(vmax,kind),np.broadcast_arrays(a,a,a,a)):
   np.maximum(dst,v,out=dst)
  for dst in edge_slices(hot,kind):dst|=(a>ANGLE)
 return vmax,hot

def populations(base,cons):
 wet=np.asarray(cons['wet_support'],dtype=bool)
 dry=(base['cls']==0)&~wet&~np.asarray(base['reserve'],dtype=bool)&~np.asarray(base['platform'],dtype=bool)
 dist=distance_transform_edt(~np.isin(base['cls'],(3,5,6)),sampling=CELL)
 bank=dry&(dist<=96.0+1e-9)
 interior=dry&~bank
 return wet,bank,interior

def reconstruct_seeds():
 base=load_npz(B);cons=load_npz(CONS);prior=load_npz(PRIOR);p=np.load(P,allow_pickle=False);f=np.load(F,allow_pickle=False)
 h=base['heights']
 if h.shape!=(N,N) or base['cls'].shape!=(N,N) or p.shape!=(N-1,N-1) or f.shape!=(N-1,N-1,4):raise RuntimeError('source dimensions differ')
 if np.isinf(p).any() or np.isinf(f).any():raise RuntimeError('P/F contains infinity')
 level=water_vertex_level(p,f)
 eligible=(base['cls']==0)&~np.asarray(cons['other_fixed'],dtype=bool)&~np.asarray(cons['engineering_halo'],dtype=bool)
 eligible &= ~np.asarray(prior['large_lake_banks'],dtype=bool)&(h.astype(np.float64)>level)
 angles=angles_by_edge(h);vmax=np.full((N,N),-np.inf,dtype=np.float64);hot=np.zeros((N,N),dtype=bool)
 for kind,a in angles.items():
  for dst in edge_slices(vmax,kind):np.maximum(dst,a,out=dst)
  for dst in edge_slices(hot,kind):dst|=a>ANGLE
 prominent=np.zeros((N,N),dtype=bool)
 prominent[:,1:-1]=(h[:,1:-1].astype(np.float64)>h[:,:-2].astype(np.float64)+PROM)&(h[:,1:-1].astype(np.float64)>h[:,2:].astype(np.float64)+PROM)
 prominent[1:-1,:]|=(h[1:-1,:].astype(np.float64)>h[:-2,:].astype(np.float64)+PROM)&(h[1:-1,:].astype(np.float64)>h[2:,:].astype(np.float64)+PROM)
 coords=np.argwhere(eligible&hot&prominent)
 order=np.lexsort((coords[:,1],coords[:,0],-vmax[coords[:,0],coords[:,1]]))
 ordered=coords[order]
 wet,bank,interior=populations(base,cons)
 rows=[]
 for rank,(r0,c0) in enumerate(ordered):
  r,c=int(r0),int(c0); val=float(h[r,c]); ew=val-max(float(h[r,c-1]),float(h[r,c+1])); ns=val-max(float(h[r-1,c]),float(h[r+1,c]))
  if wet[r,c]:pop='wet_support'
  elif bank[r,c]:pop='bank'
  elif interior[r,c]:pop='interior'
  else:pop='eligible_other'
  rows.append({'seed_id':rank,'row':r,'col':c,'x_m':c*CELL,'z_m':Z0-r*CELL,
               'max_incident_hinge_deg':float(vmax[r,c]),'prominence_ew_m':ew,'prominence_ns_m':ns,
               'population':pop,'sector':[r//64,c//64]})
 return rows

def greedy_layer(rows):
 layer=[]
 selected_coords=[]
 for seed in rows:
  r,c=seed['row'],seed['col']
  if r<HALF or c<HALF or r>=N-HALF or c>=N-HALF:
   seed.update(state='excluded_boundary',window17=None,blocker_queue_ids=[])
   continue
  blockers=[int(prev['first_layer_id']) for prev in layer
            if max(abs(r-prev['row']),abs(c-prev['col']))<SEPARATION]
  if blockers:
   seed.update(state='pending_overlap',window17=None,blocker_queue_ids=blockers)
  else:
   qid=len(layer);window=[r-HALF,c-HALF,r+HALF+1,c+HALF+1]
   seed.update(state='first_layer',first_layer_id=qid,window17=window,blocker_queue_ids=[])
   layer.append(seed);selected_coords.append((r,c))
 return layer

def atomic_json(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 except Exception:
  try:os.unlink(tmp)
  except OSError:pass
  raise

def main():
 before=pin_inputs();rows=reconstruct_seeds()
 if len(rows)!=5450:raise RuntimeError(f'expected 5450 EV87 seeds, found {len(rows)}')
 reference=json.loads(LEDGER.read_text(encoding='utf-8-sig').splitlines()[0])['seeds']
 if len(reference)!=len(rows):raise RuntimeError('frozen EV87 ledger seed count mismatch')
 for expected,actual in zip(reference,rows):
  if expected['coordinates']!=[actual['row'],actual['col']] or abs(float(expected['max_incident_angle_deg'])-actual['max_incident_hinge_deg'])>1e-9:
   raise RuntimeError(f"frozen EV87 seed/order mismatch at rank {actual['seed_id']}")
 layer=greedy_layer(rows)
 counts={k:sum(x['population']==k for x in rows) for k in ('bank','interior','wet_support','eligible_other')}
 layer_counts={k:sum(x['population']==k for x in layer) for k in counts}
 blocked_counts={k:sum(x['state']=='pending_overlap' and x['population']==k for x in rows) for k in counts}
 payload={'schema':'EV93-seed-queue-v1','status':'MATERIALIZED_NO_TERRAIN_OR_SOLVER',
  'inputs_sha256':before,'parameters':{'selector':'exact EV87 eligible + incident hinge >30.0001deg + axial d1 >0.1m EW OR NS',
  'seed_order':'descending max incident angle; row then col ascending tie break','window17_half_width_nodes':HALF,
  'window17_bounds':'[r-8,c-8,r+9,c+9), complete required','separation':'Chebyshev distance >=17 nodes',
  'first_layer':'greedy in frozen seed order; all prior selected centers with distance <17 recorded as blockers'},
  'counts':{'all_seeds':len(rows),'first_layer':len(layer),'pending_overlap':sum(x['state']=='pending_overlap' for x in rows),
  'excluded_boundary':sum(x['state']=='excluded_boundary' for x in rows),'by_population':counts,
  'first_layer_by_population':layer_counts,'pending_overlap_by_population':blocked_counts},
  'seeds':rows}
 qpath=OUT/'queue.json'
 if qpath.exists():raise RuntimeError(f'refusing to overwrite {qpath}')
 atomic_json(qpath,payload)
 after=pin_inputs()
 if before!=after:raise RuntimeError('source changed while materializing queue')
 report={'status':'EV93_QUEUE_MATERIALIZED','queue_path':str(qpath),'queue_sha256':sha(qpath),
  'builder_sha256':sha(Path(__file__)),'inputs_sha256_before':before,'inputs_sha256_after':after,
  'counts':payload['counts'],'parameters':payload['parameters']}
 atomic_json(OUT/'materialization.json',report)
 print(json.dumps({'status':report['status'],'counts':report['counts'],'queue_sha256':report['queue_sha256']},separators=(',',':')))
if __name__=='__main__':main()




