#!/usr/bin/env python
"""Independent reconstruction and audit of the EV93 seed queue. No author import."""
from __future__ import annotations
import hashlib,json,os,tempfile
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT=Path(r'E:/DayZ-Baltic-Build'); OUT=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/queue')
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'; CONS=ROOT/'v30-narva-dry-bank-relief-20261010/constraints.npz'
PRIOR=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'; P=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/plane.npy'; F=ROOT/'v30-narva-dry-bank-relief-20261010/candidate/visible-field.npy'
WRP=ROOT/'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
EV87=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'; PREFLIGHT=ROOT/'v30-global-strict-bank-relief-20261010/preflight.json'; LEDGER=ROOT/'v30-global-strict-bank-relief-20261010/queue-ledger.jsonl'
PLAN=ROOT/'v30-global-bank-extension-20261010/plan.md'
INPUTS={'B':B,'constraints':CONS,'prior':PRIOR,'P':P,'F':F,'WRP':WRP,'EV87':EV87,'preflight':PREFLIGHT,'ledger':LEDGER,'plan':PLAN}
EXPECTED={'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0','constraints':'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c','prior':'18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370','P':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0','F':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c','WRP':'3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6','EV87':'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27','preflight':'078112a24ffb7e5f0fa07777b55e9844820b4a246c686a7492fefe2aa2cbe85a','ledger':'ac87b33eb999f1250e2fa34ac9368f30a788fd1110dac9c0d138c7255ab69e76',
 'plan':'ccc018a9e1cc8a51b075a91905b1cbe7d3cdaf72040e51992f2ac55db8ad7e82'}
N=2048;CELL=6.0;Z0=12282.;SEA=.85;ANGLE=30.0001;PROM=.1;HALF=8;SEP=17

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def hashes():return {k:sha(p) for k,p in INPUTS.items()}
def load_npz(p):
 with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def vertex_water(p,f):
 out=np.full((N,N),SEA,np.float64);pv=np.nan_to_num(np.asarray(p,np.float64),nan=SEA)
 for i,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
  fv=np.nan_to_num(np.asarray(f[:,:,i],np.float64),nan=SEA);v=np.maximum(SEA,np.maximum(pv,fv))
  dst=out[dr:dr+N-1,dc:dc+N-1];np.maximum(dst,v,out=dst)
 return out
def slices(mask,kind):
 if kind=='diag':return (mask[:-1,:-1],mask[:-1,1:],mask[1:,:-1],mask[1:,1:])
 if kind=='vertical':return (mask[:-1,:-2],mask[:-1,1:-1],mask[1:,1:-1],mask[1:,2:])
 return (mask[:-2,:-1],mask[1:-1,:-1],mask[1:-1,1:],mask[2:,1:])
def edge_angles(h):
 h=np.asarray(h,np.float64);nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
 one=np.ones_like(nw);zero=np.zeros_like(nw)
 n0=np.cross(np.stack((6*one,ne-nw,zero),-1),np.stack((6*one,se-nw,-6*one),-1));n1=np.cross(np.stack((6*one,se-nw,-6*one),-1),np.stack((zero,sw-nw,-6*one),-1))
 n0/=np.linalg.norm(n0,axis=-1)[...,None];n1/=np.linalg.norm(n1,axis=-1)[...,None]
 result={}
 for name,a,b in (('diag',n0,n1),('vertical',n0[:,:-1],n1[:,1:]),('horizontal',n1[:-1,:],n0[1:,:])):
  result[name]=np.degrees(np.arctan2(np.linalg.norm(np.cross(a,b),axis=-1),np.einsum('ijk,ijk->ij',a,b)))
 return result
def seed_rebuild():
 base=load_npz(B);cons=load_npz(CONS);prior=load_npz(PRIOR);p=np.load(P,allow_pickle=False);f=np.load(F,allow_pickle=False);h=base['heights']
 assert h.shape==(N,N) and p.shape==(N-1,N-1) and f.shape==(N-1,N-1,4)
 assert not np.isinf(p).any() and not np.isinf(f).any()
 level=vertex_water(p,f);eligible=(base['cls']==0)&~cons['other_fixed'].astype(bool)&~cons['engineering_halo'].astype(bool)&~prior['large_lake_banks'].astype(bool)&(h.astype(np.float64)>level)
 vmax=np.full((N,N),-np.inf);hot=np.zeros((N,N),bool)
 for kind,a in edge_angles(h).items():
  for dst in slices(vmax,kind):np.maximum(dst,a,out=dst)
  for dst in slices(hot,kind):dst|=a>ANGLE
 prominent=np.zeros((N,N),bool);hd=h.astype(np.float64)
 prominent[:,1:-1]=(hd[:,1:-1]>hd[:,:-2]+PROM)&(hd[:,1:-1]>hd[:,2:]+PROM)
 prominent[1:-1,:]|=(hd[1:-1,:]>hd[:-2,:]+PROM)&(hd[1:-1,:]>hd[2:,:]+PROM)
 coords=np.argwhere(eligible&hot&prominent);order=np.lexsort((coords[:,1],coords[:,0],-vmax[coords[:,0],coords[:,1]]));coords=coords[order]
 wet=cons['wet_support'].astype(bool);dry=(base['cls']==0)&~wet&~base['reserve'].astype(bool)&~base['platform'].astype(bool)
 dist=distance_transform_edt(~np.isin(base['cls'],(3,5,6)),sampling=CELL);bank=dry&(dist<=96+1e-9);interior=dry&~bank
 rows=[]
 for i,(rr,cc) in enumerate(coords):
  r,c=int(rr),int(cc);v=float(hd[r,c]);pop='wet_support' if wet[r,c] else ('bank' if bank[r,c] else ('interior' if interior[r,c] else 'eligible_other'))
  rows.append({'seed_id':i,'row':r,'col':c,'x_m':c*CELL,'z_m':Z0-r*CELL,
   'max_incident_hinge_deg':float(vmax[r,c]),'prominence_ew_m':v-max(float(hd[r,c-1]),float(hd[r,c+1])),
   'prominence_ns_m':v-max(float(hd[r-1,c]),float(hd[r+1,c])),'population':pop,'sector':[r//64,c//64]})
 return rows
def reconstruct_layer(rows,n=N,half=HALF,sep=SEP):
 selected=[];expected=[]
 for i,x in enumerate(rows):
  r,c=x['row'],x['col']
  if r<half or c<half or r>=n-half or c>=n-half:
   expected.append({'state':'excluded_boundary','first_layer_id':None,'window17':None,'blocker_queue_ids':[]});continue
  blockers=[j for j,q in enumerate(selected) if max(abs(r-q['row']),abs(c-q['col']))<sep]
  if blockers:expected.append({'state':'pending_overlap','first_layer_id':None,'window17':None,'blocker_queue_ids':blockers})
  else:
   qid=len(selected);selected.append({'row':r,'col':c,'first_layer_id':qid})
   expected.append({'state':'first_layer','first_layer_id':qid,'window17':[r-half,c-half,r+half+1,c+half+1],'blocker_queue_ids':[]})
 return expected,selected
def fixture():
 rows=[{'row':20,'col':20},{'row':20,'col':37},{'row':22,'col':36},{'row':4,'col':30}]
 exp,sel=reconstruct_layer(rows,n=64,half=8,sep=17)
 return ([(x['state'],x['first_layer_id'],x['blocker_queue_ids']) for x in exp]==[
  ('first_layer',0,[]),('first_layer',1,[]),('pending_overlap',None,[0,1]),('excluded_boundary',None,[])]) and len(sel)==2

def atomic_json(p,obj):
 fd,tmp=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 except Exception:
  try:os.unlink(tmp)
  except OSError:pass
  raise

def main():
 pre=hashes();qpath=OUT/'queue.json';raw=json.loads(qpath.read_text(encoding='utf-8-sig'));report_path=OUT/'verification.json'
 actual_hashes=pre;gates={k:actual_hashes[k]==v for k,v in EXPECTED.items()}
 expected=seed_rebuild();ref=json.loads(LEDGER.read_text(encoding='utf-8-sig').splitlines()[0])['seeds'];rows=raw.get('seeds',[])
 gates['source_EV87_seed_order_matches_recomputed']=len(ref)==len(expected)==len(rows)==5450 and all(ref[i]['coordinates']==[expected[i]['row'],expected[i]['col']] and abs(float(ref[i]['max_incident_angle_deg'])-expected[i]['max_incident_hinge_deg'])<=1e-9 for i in range(min(len(ref),len(expected))))
 gates['queue_seed_ids_unique_complete']=len(rows)==5450 and [x.get('seed_id') for x in rows]==list(range(5450)) and len({(x.get('row'),x.get('col')) for x in rows})==5450
 exact_fields=('row','col','x_m','z_m','max_incident_hinge_deg','prominence_ew_m','prominence_ns_m','population','sector')
 eq=True
 if len(rows)!=len(expected):eq=False
 else:
  for a,e in zip(rows,expected):
   for key in exact_fields:
    if key in ('max_incident_hinge_deg','prominence_ew_m','prominence_ns_m'):
     if abs(float(a[key])-float(e[key]))>1e-9:eq=False
    elif a.get(key)!=e.get(key):eq=False
 gates['queue_rows_exactly_recomputed_from_pins']=eq
 expected_layer,selected=reconstruct_layer(expected)
 layerok=True
 if len(rows)!=len(expected_layer):layerok=False
 else:
  for a,e in zip(rows,expected_layer):
   for key,v in e.items():
    if a.get(key)!=v:layerok=False
 gates['first_layer_and_all_blockers_exact']=layerok
 pairwise=all(max(abs(a['row']-b['row']),abs(a['col']-b['col']))>=SEP for i,a in enumerate(selected) for b in selected[i+1:])
 windows=all(q['row']>=HALF and q['col']>=HALF and q['row']+HALF<N and q['col']+HALF<N for q in selected)
 gates['first_layer_nonoverlap']=pairwise
 gates['all_first_layer_windows_full']=windows
 gates['all_nonselected_have_explicit_reason_and_blockers']=all((x['state']=='excluded_boundary') or (x['state']=='pending_overlap' and bool(x['blocker_queue_ids'])) or x['state']=='first_layer' for x in rows)
 counts={p:sum(x['population']==p for x in rows) for p in ('bank','interior','wet_support','eligible_other')}
 layer_counts={p:sum(x['population']==p for x in rows if x['state']=='first_layer') for p in counts}
 pending_counts={p:sum(x['population']==p for x in rows if x['state']=='pending_overlap') for p in counts}
 boundary=sum(x['state']=='excluded_boundary' for x in rows)
 gates['counts_and_summary_exact']=(raw.get('counts',{}).get('all_seeds')==5450 and raw.get('counts',{}).get('first_layer')==len(selected) and raw.get('counts',{}).get('pending_overlap')==sum(x['state']=='pending_overlap' for x in rows) and raw.get('counts',{}).get('excluded_boundary')==boundary and raw.get('counts',{}).get('by_population')==counts and raw.get('counts',{}).get('first_layer_by_population')==layer_counts and raw.get('counts',{}).get('pending_overlap_by_population')==pending_counts)
 gates['selection_fixture_pass']=fixture()
 post=hashes();gates['all_source_hashes_unchanged']=pre==post and pre==EXPECTED
 status='PASS_EV93_QUEUE' if all(gates.values()) else 'FAIL_EV93_QUEUE'
 report={'status':status,'verifier_sha256':sha(Path(__file__)),'queue_sha256':sha(qpath),'materialization_sha256':sha(OUT/'materialization.json'),
  'inputs_sha256_before':pre,'inputs_sha256_after':post,'gates':gates,
  'counts':{'seeds':len(rows),'first_layer':len(selected),'pending_overlap':sum(x['state']=='pending_overlap' for x in rows),'excluded_boundary':boundary,'by_population':counts,'first_layer_by_population':layer_counts,'pending_overlap_by_population':pending_counts},
  'limits':['Queue only: no water atlas, terrain, solver, package, or engine run.','First-layer membership is greedy under EV87 seed order and Chebyshev >=17; overlap seeds remain pending, not resolved.']}
 if report_path.exists():raise RuntimeError(f'refusing to overwrite {report_path}')
 atomic_json(report_path,report)
 print(json.dumps({'status':status,'gates':gates,'counts':report['counts'],'report':str(report_path)},separators=(',',':')))
 if status!='PASS_EV93_QUEUE':raise SystemExit(1)
if __name__=='__main__':main()


