"""One unconstrained objective diagnostic; never writes an accepted terrain."""
from pathlib import Path
import argparse, gc, hashlib, importlib.util, json, sys, threading, time
import numpy as np
from scipy.sparse.linalg import LinearOperator, cg

HERE=Path(__file__).resolve().parent
PROTO=HERE.parent
OP=PROTO/'global-structured-operator'
PREP=PROTO/'global-dry-solve/prepared-01'
H=PROTO.parent/'build-wide-slope/candidate/terrain.npz'
PINS={
 H:'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
 OP/'structured_operator.py':'d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a',
 OP/'optimized-normal/fused_normal.py':'19a3e3a493f643702e66aaf265c705739535d386412f74659369d7746117ffaa',
 OP/'measure_global_actions.py':'a05a5f47b775567105c3e588e7106b4b365b58d259f018dca4f243f57d2da37b',
 PREP/'bounds.npz':'b0c4499776148b080049a528807e31a62d5fd11ba90fcaae5a7881124cde81fb',
 PREP/'receipt.json':'9e55afb4b736a3b558d3e631c62fa94c98a0ae2bb7da4e5513850375758869f3',
 PREP/'independent-review.json':'d454b78bf8721a9f6477001bb1e5ba77ed4716fc1fdd03232a6084cc6612bf85',
}
MAX_SECONDS=300.
MAX_PEAK=3*1024**3
MIN_FREE=6*1024**3

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()

def load(p,name):
 data=p.read_bytes()
 if hashlib.sha256(data).hexdigest()!=PINS[p]:raise ValueError('Source pin drift '+str(p))
 spec=importlib.util.spec_from_loader(name,loader=None,origin=str(p))
 m=importlib.util.module_from_spec(spec);m.__file__=str(p);sys.modules[name]=m
 exec(compile(data,str(p),'exec'),m.__dict__)
 return m

def constraints(op,x,lo,hi,radii):
 """Direct grid oracle, not C residuals or rounded angles."""
 full=op.base.copy();full[tuple(op.variables.T)]=x
 below=np.maximum(0.,lo-x);above=np.maximum(0.,x-hi)
 flat=full.ravel();order=flat[op.d8_witnesses]-flat[op.d8_centers]
 count=0;excess=0.
 for r0 in range(0,full.shape[0]-1,128):
  r1=min(full.shape[0]-1,r0+128)
  nw=full[r0:r1,:-1];ne=full[r0:r1,1:];sw=full[r0+1:r1+1,:-1];se=full[r0+1:r1+1,1:]
  g=np.stack((np.sqrt((ne-nw)**2+(ne-se)**2),np.sqrt((se-sw)**2+(nw-sw)**2)),axis=-1)
  e=g-radii.reshape(full.shape[0]-1,full.shape[1]-1,2)[r0:r1]
  count+=int(np.count_nonzero(e>0));excess=max(excess,float(e.max(initial=0.)))
 return {'below_box':int(np.count_nonzero(below)),'above_box':int(np.count_nonzero(above)),
         'box_max_violation_m':float(max(below.max(initial=0),above.max(initial=0))),
         'D8_violations':int(np.count_nonzero(order>0)),'D8_max_violation_m':float(order.max(initial=0)),
         'face_radius_violations':count,'face_max_violation_m':excess}

class Guard:
 def __init__(self,mem,started=None):
  self.mem=mem;self.started=time.perf_counter() if started is None else float(started);self.failure=None;self.samples=[];self.stop=threading.Event()
  self.thread=threading.Thread(target=self.watch,daemon=True)
 def watch(self):
  while not self.stop.wait(.25):
   try:self.sample()
   except Exception as e:self.failure=self.failure or f'{type(e).__name__}: {e}'
 def sample(self):
  snap={'seconds':time.perf_counter()-self.started,'peak':self.mem.process_peak_working_set(),
        'free':self.mem.memory_status()['available_physical_bytes']}
  self.samples.append(snap)
  if snap['seconds']>MAX_SECONDS:raise TimeoutError('300 second budget')
  if snap['peak']>MAX_PEAK:raise MemoryError('3 GiB process peak')
  if snap['free']<MIN_FREE:raise MemoryError('6 GiB free reserve')
  return snap
 def check(self):
  if self.failure:raise RuntimeError(self.failure)
  return self.sample()
 def close(self):
  self.stop.set();self.thread.join(timeout=2.)

def run(review_sha):
 started=time.perf_counter()
 if not __debug__:raise RuntimeError('Optimized Python forbidden')
 review=HERE/'independent-review.json';plan=HERE/'PLAN.md';source=Path(__file__).resolve()
 if sha(review)!=review_sha.lower():raise ValueError('Review pin mismatch')
 doc=json.loads(review.read_text(encoding='utf-8-sig'))
 if doc.get('status')!='PASS_ONE_OBJECTIVE_SCREEN' or doc.get('source_sha256')!=sha(source) or doc.get('plan_sha256')!=sha(plan):raise ValueError('Unreviewed source/plan')
 for p,h in PINS.items():
  if sha(p)!=h:raise ValueError('Input changed '+str(p))
 readset={str(p):sha(p) for p in [*PINS,source,plan,review]}
 mem=load(OP/'measure_global_actions.py','screen_memory')
 opmod=load(OP/'structured_operator.py','screen_operator')
 fused=load(OP/'optimized-normal/fused_normal.py','screen_fused')
 # Reserve the full proposed process cap before allocating the operator.
 if mem.memory_status()['available_physical_bytes']<MIN_FREE+MAX_PEAK:raise MemoryError('Insufficient free RAM for conservative cap + reserve')
 out=HERE/'run-01';out.mkdir(exist_ok=False)
 receipt={'status':'STARTED','source_readset_start':readset,'terrain_written':False,'accepted':False}
 (out/'started.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
 guard=Guard(mem,started);guard.thread.start();latest={};history=[]
 try:
  guard.check()
  with np.load(H,allow_pickle=False) as z:base=z['heights'].astype(np.float64)
  with np.load(PREP/'bounds.npz',allow_pickle=False) as z:
   variables=z['variables_rc'];x0=z['baseline_values'];lo=z['lower_float32'].astype(np.float64);hi=z['upper_float32'].astype(np.float64);radii=z['face_radii']
  if base.shape!=(2048,2048) or len(variables)!=2712136 or not np.array_equal(base[tuple(variables.T)],x0):raise ValueError('Domain/base identity')
  op=opmod.build_operators(base,variables);action=fused.FusedNormalAction(op);guard.check()
  rhs=op.rmatvec_a(op.rhs_a)
  normal=LinearOperator((op.n,op.n),matvec=action.a_normal,dtype=np.float64)
  precond=LinearOperator((op.n,op.n),matvec=lambda x:x/op.diag_a,dtype=np.float64)
  iterations=0;last_progress=0.;last_x=None
  def callback(x):
   nonlocal iterations,last_progress,last_x
   iterations+=1;last_x=x
   snap=guard.check()
   if iterations==1 or iterations%25==0 or snap['seconds']-last_progress>=30.:
    latest.update({'CG_iteration':iterations,**snap});history.append(latest.copy());last_progress=snap['seconds']
    print(json.dumps({'progress':latest}),flush=True)
  x,info=cg(normal,rhs,x0=x0,rtol=1e-12,atol=1e-13,maxiter=1000,M=precond,callback=callback)
  guard.check()
  residual=float(np.linalg.norm(action.a_normal(x)-rhs));target=max(1e-13,1e-12*float(np.linalg.norm(rhs)))
  receipt.update({'cg_info':int(info),'iterations':iterations,'residual_l2':residual,'residual_target':target})
  if info or residual>target:raise RuntimeError('PCG not independently converged')
  def cost(v):
   residual=op.matvec_a(v)-op.rhs_a
   return float(np.dot(residual,residual))
  raw=x.astype(np.float32).astype(np.float64)
  receipt.update({'objective_baseline':cost(x0),'objective_x64':cost(x),'objective_raw32':cost(raw),
                  'x64_constraints':constraints(op,x,lo,hi,radii),
                  'raw32_constraints':constraints(op,raw,lo,hi,radii),
                  'changed_nodes_raw32':int(np.count_nonzero(raw!=x0))})
  guard.check()
  receipt['source_readset_end']={p:sha(Path(p)) for p in readset}
  if readset!=receipt['source_readset_end']:raise RuntimeError('Readset drift')
  dest=out/'unaccepted-continuous-vector.npz'
  np.savez_compressed(dest,variables_rc=variables,solution_float64=x)
  guard.check()
  receipt.update({'status':'COMPLETE_OBJECTIVE_DIAGNOSTIC_UNACCEPTED','vector_path':str(dest),'vector_sha256':sha(dest)})
 except Exception as e:
  receipt.update({'status':'TERMINAL_DIAGNOSTIC_FAILURE','error':f'{type(e).__name__}: {e}'})
 finally:
  guard.close()
  try:
   guard.check()
   endset={p:sha(Path(p)) for p in readset}
   guard.check()
  except Exception as final_error:
   endset=None
   receipt.update({'status':'TERMINAL_FINAL_GUARD_FAILURE','final_error':f'{type(final_error).__name__}: {final_error}'})
  receipt.update({'elapsed_seconds':time.perf_counter()-guard.started,'progress':history,
     'peak_bytes':max((s['peak'] for s in guard.samples),default=0),'minimum_free_bytes':min((s['free'] for s in guard.samples),default=None),
     'watchdog_failure':guard.failure,'source_readset_end':endset})
  receipt['source_readset_equal']=readset==receipt['source_readset_end']
  if endset is not None and not receipt['source_readset_equal']:receipt['status']='TERMINAL_SOURCE_DRIFT'
  (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(receipt,indent=2),flush=True)
 return receipt

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--review-sha256',required=True)
 args=parser.parse_args();result=run(args.review_sha256)
 raise SystemExit(0 if result['status']=='COMPLETE_OBJECTIVE_DIAGNOSTIC_UNACCEPTED' else 1)
