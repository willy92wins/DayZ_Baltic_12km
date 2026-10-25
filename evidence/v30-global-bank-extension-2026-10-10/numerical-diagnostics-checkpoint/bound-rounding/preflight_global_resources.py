#!/usr/bin/env python
"""Read-only global EV95 domain/operator resource preflight; no solver or terrain writes."""
from __future__ import annotations
import hashlib, importlib.util, json, math, os, sys, time
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.ndimage import minimum_filter

ROOT=Path(r'E:/DayZ-Baltic-Build')
G=ROOT/'v30-global-bank-extension-20261010'
HERE=G/'global-operator-prototype/global-sizing-ev95'
OUT=HERE/'run-05'
B_PATH=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
H_PATH=G/'build-wide-slope/candidate/terrain.npz'
S_PATH=G/'compound-selection/run-02/selection.json'
S_CAND=G/'compound-selection/run-02/candidate-terrain.npz'
EV79=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/terrain.npz'
CONS=ROOT/'v30-narva-dry-bank-relief-20261010/constraints.npz'
PRIOR=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
P_PATH=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'
F_PATH=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'
WATER=G/'global-operator-prototype/global-water-guard-ev95/run-01/water-guard.npz'
CIVIL=G/'global-operator-prototype/global-civil-ev95/run-01/civil-mask.npz'
WATER_META=WATER.with_name('inventory.json')
CIVIL_META=CIVIL.with_name('inventory.json')
INDEX_MANIFEST=G/'ev93-face-index/runs/20261010T092417Z-63d4cec3/manifest.json'
CORRIDORS=Path(r'E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson')
EV87=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
FOCAL_READER=G/'global-operator-prototype/real-sector-preflight/focus-unit/verify_focal_composition.py'
PROTO=G/'global-operator-prototype/prototype.py'
CP=G/'global-operator-prototype/face-slope-cone-pilot/pilot.py'
EV82_AUTHOR=ROOT/'v30-mixed-bank-incremental-fixed-20261010/author.py'
D8=G/'constrained-pilot/d8_sparse_pilot.py'
WATER_HELPER=G/'global-operator-prototype/real-sector-preflight/prepare_water_footprint.py'
SECTOR_HELPER=G/'global-operator-prototype/real-sector-preflight/verify_real_sector.py'
EV94_PREP=G/'global-operator-prototype/real-sector-preflight/ev94-rebase/prepare_ev94.py'
N=2048; CELL=6.; SEA=.85; EPS=1e-4; DELTA=2.; CAP=.5; FOCUS=(840,370)
PINS={
 str(B_PATH):'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 str(H_PATH):'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
 str(S_PATH):'3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b',
 str(S_CAND):'6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d',
 str(EV79):'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
 str(CONS):'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
 str(PRIOR):'18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
 str(P_PATH):'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 str(F_PATH):'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
 str(WATER):'997a1510ffd7194cf7f25fc9a26a1fed9c580586d63952f0dfd70fce565c1926',
 str(WATER_META):'39e26373fee324e8b0e7334dd8333d3fb7373b9cc55c226350e2c607b592ce82',
 str(CIVIL):'46faaf22e2cfefc8137e2b555227a985cfe212265694f1bce106281937c9ffe3',
 str(CIVIL_META):'cdebbbce50644407642e791388e44c40b15499041844607650b885d1bc618856',
 str(INDEX_MANIFEST):'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
 str(CORRIDORS):'28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343',
 str(EV87):'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
 str(FOCAL_READER):'e5228392386606e495579f28b1cfa8ecd6d58aff1eb9f2967f4480e8440aecb2',
 str(PROTO):'5b4b8f08e5205e1f9cc90bcc8e82e61dade45bb82bd22da8ee69303aa4475cc4',
 str(CP):'d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a',
 str(EV82_AUTHOR):'9b7c5374b7c78c3604bb2763ef8b7b4d16dc4bf18fc57091233ad435876cb74b',
 str(D8):'6b5281d9750c30fc5b27171aaec2af59dee88411a66bf5b08e5105866f08252c',
 str(WATER_HELPER):'9f5f9952aaa23f5d673ec4c8375a2cc0d0759e0634d3093a08e23c50437728f1',
 str(SECTOR_HELPER):'703f29380b0359df61a3d699573d68c6abdbe7a9688806e5c09867fd787a343e',
 str(EV94_PREP):'4f436164fea35e8241ceb50f6090271ca89ac5c2184a693195d2b40334b64124',
}

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def memory_snapshot():
 import ctypes
 from ctypes import wintypes
 class MEMORYSTATUSEX(ctypes.Structure):
  _fields_=[('dwLength',wintypes.DWORD),('dwMemoryLoad',wintypes.DWORD),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
 class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
  _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
 kernel=ctypes.WinDLL('kernel32',use_last_error=True); psapi=ctypes.WinDLL('psapi',use_last_error=True)
 kernel.GlobalMemoryStatusEx.argtypes=[ctypes.POINTER(MEMORYSTATUSEX)];kernel.GlobalMemoryStatusEx.restype=wintypes.BOOL
 kernel.GetCurrentProcess.argtypes=[];kernel.GetCurrentProcess.restype=ctypes.c_void_p
 psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(PROCESS_MEMORY_COUNTERS),wintypes.DWORD];psapi.GetProcessMemoryInfo.restype=wintypes.BOOL
 ms=MEMORYSTATUSEX();ms.dwLength=ctypes.sizeof(ms)
 if not kernel.GlobalMemoryStatusEx(ctypes.byref(ms)):raise OSError(f'GlobalMemoryStatusEx failed: {ctypes.get_last_error()}')
 pm=PROCESS_MEMORY_COUNTERS();pm.cb=ctypes.sizeof(pm)
 if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(pm),pm.cb):raise OSError(f'GetProcessMemoryInfo failed: {ctypes.get_last_error()}')
 return {'available_physical_bytes':int(ms.ullAvailPhys),'total_physical_bytes':int(ms.ullTotalPhys),'process_working_set_bytes':int(pm.WorkingSetSize),'process_peak_working_set_bytes':int(pm.PeakWorkingSetSize)}
def pin_all():
 out={}
 for p,want in PINS.items():
  q=Path(p)
  if not q.is_file(): raise FileNotFoundError(q)
  got=sha(q)
  if len(want)==64 and got!=want: raise RuntimeError(f'pin mismatch {q}: {got} != {want}')
  out[p]=got
 return out
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m
def add_cell_corners(mask,cells):
 cells=np.asarray(cells,bool)
 if cells.shape!=(N-1,N-1): raise ValueError('cell mask shape')
 mask[:-1,:-1] |= cells; mask[:-1,1:] |= cells; mask[1:,:-1] |= cells; mask[1:,1:] |= cells
def inward32(raw,lower):
 raw=np.asarray(raw,np.float64); v=raw.astype(np.float32); vf=v.astype(np.float64)
 bad=(vf<raw) if lower else (vf>raw)
 v[bad]=np.nextafter(v[bad],np.float32(np.inf if lower else -np.inf),dtype=np.float32)
 return v
def cross_tri(lev,ground,ids):
 d=np.stack([lev[...,i]-ground[...,i] for i in ids],axis=-1)
 return np.all(np.isfinite(d),axis=-1) & (np.any(d==0.,axis=-1)|((np.min(d,axis=-1)<0)&(np.max(d,axis=-1)>0)))
def p9_cells_exact(p,corridors):
 from shapely.geometry import box, shape
 out=np.zeros((N-1,N-1),bool)
 for feat in corridors['features']:
  geom=shape(feat['geometry']); minx,minz,maxx,maxz=geom.bounds
  c0=max(0,int(math.floor(minx/CELL))); c1=min(N-1,int(math.floor(maxx/CELL))+1)
  r0=max(0,int(math.floor((12282.-maxz)/CELL))); r1=min(N-1,int(math.floor((12282.-minz)/CELL))+1)
  if r0>=r1 or c0>=c1: continue
  for r,c in np.argwhere(~np.isfinite(p[r0:r1,c0:c1])).tolist():
   rr=r0+r; cc=c0+c
   if out[rr,cc]: continue
   cell=box(cc*CELL,12282-(rr+1)*CELL,(cc+1)*CELL,12282-rr*CELL)
   if geom.intersection(cell).area>0.: out[rr,cc]=True
 return out
def window_masks(selection,reader):
 ids=selection.get('retained_unit_ids'); units=selection.get('units')
 if not isinstance(ids,list) or len(ids)!=499 or len(set(ids))!=499 or not isinstance(units,list): raise ValueError('retained selection schema/count')
 by={x['unit_id']:x for x in units}; halo=np.zeros((N,N),bool); core=np.zeros_like(halo); reads={}
 origins={'legacy':0,'crest':0}; windows=[]
 for uid in ids:
  row=by[uid]; meta,_,_=reader.local_artifact(row,list(FOCUS)); origin=row['origin']; origins[origin]+=1
  win=list(map(int,meta['window'])); windows.append(win)
  if len(win)!=4 or win[1]-win[0]!=17 or win[3]-win[2]!=17: raise ValueError(f'window {uid} invalid')
  r0,r1,c0,c1=win
  if not (0<=r0<r1<=N and 0<=c0<c1<=N): raise ValueError(f'window {uid} out of bounds')
  halo[max(0,r0-2):min(N,r1+2),max(0,c0-2):min(N,c1+2)]=True
  core[r0:r1,c0:c1]=True
  ap=Path(row['source_artifact_path']).resolve(); reads[str(ap)]=sha(ap)
  body=json.loads(ap.read_text(encoding='utf-8'))
  if origin=='crest':
   sp=Path(body['source_result_path']).resolve(); reads[str(sp)]=sha(sp); sr=json.loads(sp.read_text(encoding='utf-8'))
   if sr.get('delta_path'):
    dp=Path(sr['delta_path']).resolve(); reads[str(dp)]=sha(dp)
  elif body.get('delta_path'):
   dp=Path(body['delta_path']).resolve(); reads[str(dp)]=sha(dp)
  if window_gap(win,FOCUS)<=2: raise ValueError(f'retained window touches explicit focus halo: {uid}')
  if len(reads)>3000: raise RuntimeError('unexpectedly large selection readset')
 if origins!={'legacy':332,'crest':167}: raise ValueError(f'origin distribution {origins}')
 return halo,core,windows,origins,reads
def window_gap(w,p):
 r0,r1,c0,c1=w;r,c=p
 return max(max(r0-r,0,r-(r1-1)),max(c0-c,0,c-(c1-1)))
def bool_shift(var,dr,dc):
 h,w=var.shape; out=np.zeros_like(var)
 r0=max(0,-dr);r1=min(h,h-dr);c0=max(0,-dc);c1=min(w,w-dc)
 out[r0:r1,c0:c1]=var[r0+dr:r1+dr,c0+dc:c1+dc]
 return out
def operator_counts(var,B):
 # Exact pattern counts for prototype.py's forward xx/zz/xz stencils plus fidelity.
 h,w=var.shape; arows=0; annz=0
 for kind,offsets in [('xx',((0,0),(0,1),(0,2))),('zz',((0,0),(1,0),(2,0))),('xz',((0,0),(0,2),(2,0),(2,2)))]:
  rh=h-(2 if kind!='xx' else 0); cw=w-(2 if kind!='zz' else 0)
  act=np.zeros((rh,cw),bool); cnt=np.zeros((rh,cw),np.uint8)
  for dr,dc in offsets:
   q=var[dr:dr+rh,dc:dc+cw]; act |= q; cnt += q
  arows+=int(np.count_nonzero(act)); annz+=int(cnt[act].sum(dtype=np.int64))
 arows+=int(var.sum());annz+=int(var.sum())
 # D8: every non-strict local center has one lexicographic minimum witness.
 pad=np.pad(B.astype(np.float64),1,constant_values=np.inf); h,w=B.shape
 mn=np.full((h,w),np.inf,np.float64)
 offsets=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
 for dr,dc in offsets:
  mn=np.minimum(mn,pad[1+dr:1+dr+h,1+dc:1+dc+w])
 nonstrict=B.astype(np.float64)>=mn
 # Detect witness variable with ordered neighbor scan without materializing Python rows.
 pending=nonstrict.copy(); wvar=np.zeros((h,w),bool); got=np.zeros((h,w),bool)
 for dr,dc in offsets:
  nb=pad[1+dr:1+dr+h,1+dc:1+dc+w]
  take=pending & (nb==mn)
  if dr<0: rs=slice(-dr,h); rd=slice(0,h+dr)
  elif dr>0: rs=slice(0,h-dr); rd=slice(dr,h)
  else: rs=slice(0,h); rd=slice(0,h)
  if dc<0: cs=slice(-dc,w); cd=slice(0,w+dc)
  elif dc>0: cs=slice(0,w-dc); cd=slice(dc,w)
  else: cs=slice(0,w); cd=slice(0,w)
  wvar[rs,cs][take[rs,cs]] = var[rd,cd][take[rs,cs]]
  got |= take; pending &= ~take
 if np.any(pending): raise AssertionError('D8 witness missing')
 crows=int(nonstrict.sum()); cnnz=int((nonstrict & var).sum())+int((nonstrict & wvar).sum())
 # G has two derivative rows for each triangle; every row exists, structural zeros retained.
 # Per cell, tri0 x=(NE-NW), z=(NE-SE); tri1 x=(SE-SW), z=(NW-SW).
 nw=var[:-1,:-1]; ne=var[:-1,1:]; sw=var[1:,:-1]; se=var[1:,1:]
 grows=4*(h-1)*(w-1)
 gnz=int(nw.sum()+ne.sum()+se.sum()+ne.sum()+se.sum()+sw.sum()+nw.sum()+sw.sum())
 return {'A':{'rows':arows,'nnz':annz},'C':{'rows':crows,'nnz':cnnz},'G':{'rows':grows,'nnz':gnz},
         'd8_nonstrict_centers':crows,'variables':int(var.sum())}
def csr_bytes(m,nnz):return 12*int(nnz)+4*(int(m)+1)
def matrix_storage(counts,n):
 out={}; csr=tr=0
 for k in ('A','C','G'):
  m=counts[k]['rows']; z=counts[k]['nnz']; a=csr_bytes(m,z); t=12*z+4*(n+1)
  out[k]={'shape':[m,n],'nnz':z,'csr_bytes':a,'transpose_shape':[n,m],'transpose_indptr_bytes':4*(n+1),'transpose_csr_bytes':t}
  csr+=a;tr+=t
 return out,csr,tr
def fixtures(proto,cp):
 # Contract: lower rounds up, upper down, each to the closest float32.
 seed=np.array([-12.3,-1.,0.,1.,6.675,180.5],np.float32)
 up=np.nextafter(seed,np.float32(np.inf)).astype(np.float64)
 raw=np.concatenate((seed.astype(np.float64)+(up-seed.astype(np.float64))*.4,seed.astype(np.float64)))
 low=inward32(raw,True);high=inward32(raw,False)
 if np.any(low.astype(np.float64)<raw) or np.any(high.astype(np.float64)>raw):raise AssertionError('bound rounded outside real interval')
 if np.any(np.nextafter(low,np.float32(-np.inf)).astype(np.float64)>=raw) or np.any(np.nextafter(high,np.float32(np.inf)).astype(np.float64)<=raw):raise AssertionError('bound is not closest inward float32')
 B=np.arange(9*10,dtype=np.float32).reshape(9,10)/7
 nodes=np.array([[3,3],[3,4],[5,6],[7,9]],np.int32);var=np.zeros(B.shape,bool);var[tuple(nodes.T)]=True
 counts=operator_counts(var,B)
 st=proto.all_stencils(B.shape,nodes); rec=proto.row_records(B,nodes,st); A,_=proto.csr_from_records(rec,len(nodes))
 if counts['A']!={'rows':A.shape[0],'nnz':A.nnz}:raise AssertionError(f'A count mismatch {counts["A"]} vs {A.shape,A.nnz}')
 witness,_=cp.d8_witnesses(B);C,_=cp.build_d8(B,nodes,witness)
 if counts['C']!={'rows':C.shape[0],'nnz':C.nnz}:raise AssertionError(f'C count mismatch {counts["C"]} vs {C.shape,C.nnz}')
 G,*_=cp.build_face_operator(B,nodes)
 if counts['G']!={'rows':G.shape[0],'nnz':G.nnz}:raise AssertionError(f'G count mismatch {counts["G"]} vs {G.shape,G.nnz}')
 # Negative: corrupting one stencil membership must differ from exact CSR count.
 bad=var.copy();bad[0,0]=True
 bc=operator_counts(bad,B)
 if bc['A']==counts['A']:raise AssertionError('negative variable perturbation undetected')
 return {'status':'PASS','tests':['closest inward float32 bounds including signed/subnormal/exact values','A placements/nnz vs CP CSR','D8 row and witness nnz vs CP CSR','G structural rows/nnz vs CP CSR','negative changed mask changes count'], 'small_counts':counts}

def run():
 OUT.mkdir(parents=True,exist_ok=False)
 started=time.perf_counter(); own=Path(__file__).resolve(); own_sha=sha(own); read_start=pin_all()
 memory_start=memory_snapshot(); ws_start=memory_start['process_working_set_bytes']; ram_start=memory_start['available_physical_bytes']
 ev87=load_module('ev87_sizing_pinned',EV87);proto=load_module('prototype_sizing_pinned',PROTO);cp=load_module('cp_sizing_pinned',CP)
 reader=load_module('focal_reader_sizing_pinned',FOCAL_READER)
 with np.load(B_PATH,allow_pickle=False) as z:B={k:z[k] for k in z.files}
 with np.load(H_PATH,allow_pickle=False) as z:H={k:z[k] for k in z.files}
 with np.load(S_CAND,allow_pickle=False) as z:S={k:z[k] for k in z.files}
 with np.load(EV79,allow_pickle=False) as z:O={k:z[k] for k in z.files}
 with np.load(CONS,allow_pickle=False) as z:cons={k:z[k] for k in z.files}
 with np.load(PRIOR,allow_pickle=False) as z:prior={k:z[k] for k in z.files}
 P=np.load(P_PATH,allow_pickle=False)
 F=np.load(F_PATH,allow_pickle=False)
 with np.load(WATER,allow_pickle=False) as z:wa={k:z[k] for k in z.files}
 with np.load(CIVIL,allow_pickle=False) as z:ca={k:z[k] for k in z.files}
 for name,d in [('B',B),('H',H),('S',S),('O',O)]:
  if d['heights'].shape!=(N,N) or d['heights'].dtype!=np.float32:raise ValueError(f'{name} height schema')
 b=B['heights'];h=H['heights'];s=S['heights'];o=O['heights'];p=np.asarray(P);p32_reference=np.asarray(P,np.float32)
 if p.shape!=(N-1,N-1) or F.shape!=(N-1,N-1,4):raise ValueError('P/F shape')
 if P.dtype!=np.float64 or F.dtype!=np.float64:raise ValueError('P/F source dtype must remain float64')
 for name,d in [('H',H),('S',S)]:
  for key in set(B)-{'heights'}:
   if key not in d or not np.array_equal(B[key],d[key],equal_nan=True):raise ValueError(f'{name} metadata drift from B: {key}')
 delta=h!=b; sd=s!=b
 if int(delta.sum())!=66058 or int(sd.sum())!=30066 or np.any(sd & (s!=h)):raise ValueError('EV95/selection delta relation does not match pinned composition')
 selection=json.loads(S_PATH.read_text(encoding='utf-8'))
 if selection.get('status')!='SELECTED' or len(selection.get('retained_unit_ids',[]))!=499:raise ValueError('selection status/count')
 halo,core,windows,origins,selected_reads=window_masks(selection,reader)
 if not np.all(h[halo]==s[halo]):raise ValueError('EV95 candidate does not preserve retained window+halo2 values from accepted composite')
 # Formula follows EV87 vertex_levels: P and F are independent, both maxed with SEA.
 levels=ev87.vertex_levels(p,F)
 eligible,_=ev87._ev87_eligible(H,cons,prior,h.astype(np.float64),p,F)
 eligible_before_guards=eligible.copy()
 # Exactly recreate contact/partial masks from the water-footprint contract on native NW-SE triangles.
 ground=(h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:])
 gv=np.stack(ground,axis=-1).astype(np.float64)
 reasons=np.zeros((N-1,N-1),np.uint8); tri0=(0,1,3);tri1=(0,2,3)
 for level,name in [(np.full_like(p,SEA,dtype=np.float64),'sea'),(p.astype(np.float64),'P')]:
  finite=np.isfinite(level)
  for tri in (tri0,tri1):
   cr=cross_tri(np.broadcast_to(level[...,None],gv.shape),gv,tri)
   if name=='sea':reasons[cr]|=1
   else:reasons[finite & cr]|=2
 for tri in (tri0,tri1):
  fv=np.stack([F[...,i] for i in tri],axis=-1)
  fin=np.isfinite(fv); partial=fin.any(axis=-1)&~fin.all(axis=-1)
  reasons[partial]|=4
  deltaf=fv-gv[...,list(tri)]
  cross=np.all(fin,axis=-1)&np.all(np.isfinite(deltaf),axis=-1)&(np.any(deltaf==0,axis=-1)|((np.min(deltaf,axis=-1)<0)&(np.max(deltaf,axis=-1)>0)))
  reasons[cross]|=8
 if np.isinf(p).any() or np.isinf(F).any():raise ValueError('P/F infinity is invalid; only NaN encodes unknown')
 # Quantify the prior float32-P path without using it for any gate.
 p32_cross=np.zeros((N-1,N-1),bool)
 for tri in (tri0,tri1):
  p32_cross |= np.isfinite(p32_reference) & cross_tri(np.broadcast_to(p32_reference[...,None],gv.shape),gv,tri)
 p64_cross=(reasons&2)!=0
 levels32_reference=ev87.vertex_levels(p32_reference,F)
 p_precision_diag={'source_P_dtype':str(P.dtype),'analysis_P_dtype':str(p.dtype),'finite_samples_changed_by_prior_f32_cast':int(np.count_nonzero(np.isfinite(p)&(p!=p32_reference.astype(np.float64)))),'max_abs_finite_cast_error_m':float(np.max(np.abs(p[np.isfinite(p)]-p32_reference.astype(np.float64)[np.isfinite(p)]))),'cross_cells_float64':int(p64_cross.sum()),'cross_cells_prior_float32_cast':int(p32_cross.sum()),'cross_cell_symmetric_difference':int(np.count_nonzero(p64_cross^p32_cross)),'vertex_level_values_changed_by_prior_cast':int(np.count_nonzero(levels!=levels32_reference)),'vertex_level_max_abs_change_m':float(np.max(np.abs(levels-levels32_reference)))}
 shore=reasons!=0; partial=(reasons&4)!=0
 corridors=json.loads(CORRIDORS.read_text(encoding='utf-8')); p9=p9_cells_exact(p,corridors)
 water_cells=np.asarray(wa['face_bbox_cells'],bool); civil_cells=np.asarray(ca['road_guard_cells']|ca['bridge_cells'],bool)
 if water_cells.shape!=(N-1,N-1) or civil_cells.shape!=(N-1,N-1):raise ValueError('guard cell mask shape')
 water_nodes=np.asarray(wa['fixed_vertices'],bool).copy();water_nodes_check=np.zeros_like(water_nodes);add_cell_corners(water_nodes_check,water_cells)
 if not np.array_equal(water_nodes,water_nodes_check):raise ValueError('water guard fixed_vertices != bbox cell corner union')
 fixed_sem=(cons['other_fixed'].astype(bool)|cons['engineering_halo'].astype(bool)|prior['large_lake_banks'].astype(bool))
 water_cell_block=np.zeros((N,N),bool);add_cell_corners(water_cell_block,water_cells|shore|partial|p9)
 civil_nodes=np.asarray(ca['fixed_vertices'],bool)
 p9_nodes=np.zeros((N,N),bool);add_cell_corners(p9_nodes,p9)
 protected= fixed_sem | water_cell_block | water_nodes | civil_nodes | halo
 focusmask=np.zeros((N,N),bool);focusmask[FOCUS]=True;protected|=focusmask
 # EV79 ±2 step bounds from H, intersected with the EV82 baseline B +0.5m cap; inward f32.
 floor=np.minimum(o.astype(np.float64),levels.astype(np.float64)+EPS)
 lo_raw=np.maximum.reduce((h.astype(np.float64)-DELTA,floor,np.minimum(o.astype(np.float64),1.8),o.astype(np.float64)-DELTA))
 hi_raw=np.minimum.reduce((h.astype(np.float64)+DELTA,o.astype(np.float64)+DELTA,b.astype(np.float64)+CAP))
 lo=inward32(lo_raw,True); hi=np.minimum(inward32(np.minimum(h.astype(np.float64)+DELTA,o.astype(np.float64)+DELTA),False),inward32(b.astype(np.float64)+CAP,False))
 bounds_bad=(lo>hi)|~np.isfinite(lo)|~np.isfinite(hi)
 eligible &= ~protected & ~bounds_bad
 # Scenario EV95 delta held fixed is a sensitivity case, not the chosen policy.
 varA=eligible.copy();varB=eligible & ~delta
 caa=operator_counts(varA,h);cbb=operator_counts(varB,h)
 # P9 records exact positive-area unknown-P corridor cells; preserve unknown outside this set as OPEN.
 reason_bits=np.zeros((N,N),np.uint16)
 for bit,mask in [(1,B['cls']!=0),(2,cons['other_fixed'].astype(bool)),(4,cons['engineering_halo'].astype(bool)),(8,prior['large_lake_banks'].astype(bool)),(16,water_nodes),(32,civil_nodes),(64,p9_nodes),(128,water_cell_block),(256,halo),(512,focusmask),(1024,bounds_bad),(2048,delta)]:reason_bits[mask]|=bit
 masks_path=OUT/'masks.npz';np.savez_compressed(masks_path,ev95_variable=varA.astype(np.uint8),ev95_delta_fixed_variable=varB.astype(np.uint8),eligible_before_guards=eligible_before_guards.astype(np.uint8),retained_499_halo2=halo.astype(np.uint8),p9_unknown_nodes=p9_nodes.astype(np.uint8),water_bbox_nodes=water_nodes.astype(np.uint8),civil_nodes=civil_nodes.astype(np.uint8),water_shore_partial_nodes=water_cell_block.astype(np.uint8),reason_bits=reason_bits)
 fixture=fixtures(proto,cp)
 counts_out={};memory={}
 for scenario,cnt,n in [('EV95_delta_variable',caa,caa['variables']),('EV95_delta_fixed_sensitivity',cbb,cbb['variables'])]:
  mats,csr,tr=matrix_storage(cnt,n)
  arows=cnt['A']['rows']; crows=cnt['C']['rows']; grows=cnt['G']['rows']
  vectors=8*(22*n+4*crows+8*grows) + 8*arows + 8*crows + 8*grows
  solver_storage=csr+tr+vectors
  assembly_extra=csr+tr # conservative duplicate during conversion; excludes Python record objects
  counts_out[scenario]={**cnt,'matrix_bytes':mats}
  memory[scenario]={'csr_all_matrices_bytes':csr,'csr_transposes_bytes':tr,'csr_plus_transposes_bytes':csr+tr,
   'solver_vectors_rhs_projections_bytes_estimate':vectors,'steady_numeric_bytes_estimate':solver_storage,
   'conversion_duplicate_csr_upper_bytes':assembly_extra,'conversion_peak_numeric_upper_bytes':solver_storage+assembly_extra,
   'python_row_record_lists_included':False,'note':'CSR byte counts exact for int32 indices/indptr and float64 data; vector counts are conservative sizing estimates, not measured solver peak.'}
 read_start.update(selected_reads)
 read_end=pin_all(); own_end=sha(own); memory_end=memory_snapshot()
 for rp,rd in selected_reads.items():
  if not Path(rp).is_file() or sha(rp)!=rd: raise RuntimeError(f'selected artifact changed: {rp}')
  read_end[rp]=rd
 if read_start!=read_end or own_sha!=own_end:raise RuntimeError('readset/source changed during preflight')
 report={'schema':'ev95.global-resource-preflight.v1','status':'READ_ONLY_RESOURCE_PREFLIGHT_COMPLETE','source_readset_start':read_start,'source_readset_end':read_end,'self_sha256':own_sha,
  'masks_artifact':{'path':str(masks_path),'sha256':sha(masks_path),'npz_bytes':masks_path.stat().st_size},
  'identity':{'B_sha256':read_start[str(B_PATH)],'EV95_sha256':read_start[str(H_PATH)],'selection_sha256':read_start[str(S_PATH)],'selected_candidate_sha256':read_start[str(S_CAND)],'retained_artifact_readset_start_end_equal':True,'retained_artifact_count':len(selected_reads),'retained_artifact_readset_sha256':hashlib.sha256(json.dumps(selected_reads,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'EV95_delta_vertices':int(delta.sum()),'selection_delta_vertices':int(sd.sum()),'selection_delta_subset_EV95_and_values_equal':True,'retained_windows':499,'origin_counts':origins,'retained_halo2_vertices':int(halo.sum()),'retained_rect_vertices':int(core.sum()),'focus_rc':list(FOCUS),'focus_pinned_explicitly':bool(halo[FOCUS] or focusmask[FOCUS]),'focus_height_m_EV95':float(h[FOCUS]),'selected_subcomposition_focus_height_m':float(s[FOCUS]),'focus_source':'EV95 full candidate/focal composition; selected-unit candidate alone is B plus 499 windows and does not contain focal change'},
  'domain':{'EV87_eligible_before_global_guards':int(eligible_before_guards.sum()),'EV95_delta_variable_after_guards':caa['variables'],'EV95_delta_fixed_sensitivity_after_guards':cbb['variables'],'reason_bit_legend':{'1':'cls!=0','2':'other_fixed','4':'engineering_halo','8':'large_lake_banks','16':'water bbox vertices','32':'civil road/bridge vertices','64':'P9 unknown corridor vertices','128':'P/F/SEA crossing/contact or partial-F incident vertices','256':'499 retained window+Chebyshev halo2','512':'explicit focus pin','1024':'infeasible physical bounds','2048':'EV95 delta; only sensitivity scenario'},'overlap_counts':{'eligible_water_bbox':int((eligible_before_guards & water_nodes).sum()),'eligible_civil':int((eligible_before_guards & civil_nodes).sum()),'eligible_retained_halo':int((eligible_before_guards & halo).sum()),'eligible_P9':int((eligible_before_guards & p9_nodes).sum()),'eligible_shore_partial':int((eligible_before_guards & water_cell_block).sum()),'eligible_wet_support_diagnostic_not_automatically_frozen':int((eligible_before_guards & cons['wet_support'].astype(bool)).sum())},'P_precision_diagnostic_prior_f32_cast_not_used_for_gates':p_precision_diag,'water_cells':{'bbox_guard_cells':int(water_cells.sum()),'P_cross_or_contact_cells':int(((reasons&2)!=0).sum()),'F_cross_or_contact_cells':int(((reasons&8)!=0).sum()),'SEA_cross_or_contact_cells':int(((reasons&1)!=0).sum()),'F_partial_cells':int(partial.sum()),'P9_unknown_positive_area_cells':int(p9.sum()),'P_unknown_outside_P9_remains_open':True},'civil_guard_vertices':int(civil_nodes.sum()),'bounds':{'infeasible_vertices':int(bounds_bad.sum()),'floor_min_m':float(np.min(floor)),'upper_cap':'min(EV79 total +2m, EV82 current +0.5m)','lower':'max(EV79 total -2m, min(EV79, P/F/SEA vertex level +1e-4), min(EV79,1.8m))'}},
  'operator_counts':counts_out,'memory_estimate':memory,'runtime_snapshot':{'start':memory_start,'end':memory_end,'elapsed_seconds':time.perf_counter()-started,'note':'OS memory is volatile. No solver or map mutation was run.'},
  'fixtures':fixture,'limits':['Water protection uses conservative global face-bbox cells; no exact ODOL clipping was repeated.','Exact P9 mask uses positive-area intersection of P-NaN cells with approved corridor polygons.','P/F/SEA crossing/contact and F-partial masks are reconstructed per NW-SE native triangle.','Counts describe the stated CP row structure; resource bytes for CSR are exact under int32/float64 layout, but solver/assembly peak is an estimate and Python row-record lists are excluded.','No performance or feasibility acceptance is inferred from this resource preflight.']}
 report_path=OUT/'preflight.json'; tmp=report_path.with_suffix('.json.tmp');tmp.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8');os.replace(tmp,report_path)
 print(json.dumps({'status':report['status'],'report':str(report_path),'variables':{k:v['variables'] for k,v in counts_out.items()},'memory':{k:v['conversion_peak_numeric_upper_bytes'] for k,v in memory.items()},'available_bytes':ram_start},indent=2))
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--self-test',action='store_true');a=p.parse_args()
 if a.self_test:
  proto=load_module('prototype_fixture',PROTO);cp=load_module('cp_fixture',CP);print(json.dumps(fixtures(proto,cp),indent=2));return 0
 if not a.run:p.error('use --self-test or --run')
 run();return 0
if __name__=='__main__':raise SystemExit(main())
