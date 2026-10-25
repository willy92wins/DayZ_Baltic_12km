from pathlib import Path
import hashlib, json, math, time, re, importlib.util
import numpy as np
from scipy.ndimage import distance_transform_edt
B=Path(__file__).resolve().parent
source_path=B/'author-executed.py'
spec=importlib.util.spec_from_file_location('ev80_exact_author',source_path)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
source_text=source_path.read_text(encoding='utf-8-sig')
def _probe_return(loc, reason):
 keys=('r','c','old_h','new_h','patch_now','patch_src','src_hinge','now_hinge','sectors','sector_caps','hinge_categories','p99_bank','p99_interior','source','water_floor','src_pairs')
 ctx={k:loc[k] for k in keys};ctx['reason']=reason;ctx['proposal']=float(loc['new_h']);ctx['patch_now']=loc['patch_now'].copy();ctx['patch_src']=loc['patch_src'].copy();ctx['src_hinge']=list(loc['src_hinge']);ctx['now_hinge']=list(loc['now_hinge']);ctx['sectors']=list(loc['sectors']);ctx['sector_caps']=dict(loc['sector_caps']);ctx['hinge_categories']=list(loc['hinge_categories']);ctx['source_h']=float(loc['source'][loc['r'],loc['c']]);ctx['water_floor_value']=float(loc['water_floor'][loc['r'],loc['c']]);return None,reason,ctx
for reason in ('float32_slope_rejected','float32_sector_rejected','float32_new_over30_rejected','float32_bank_p99_rejected','float32_interior_p99_rejected'):
 source_text=source_text.replace(f"return None, '{reason}'",f"return _probe_return(locals(), '{reason}')")
ns=dict(a.__dict__);ns['_probe_return']=_probe_return;ns['__name__']='ev80_exact_author_instrumented';exec(compile(source_text,str(source_path),'exec'),ns);solve=ns['solve_node']
# Independent direct checker for a proposed float32 height; no writes or parameter relaxations.
def check(ctx,hf):
 patch=ctx['patch_now'].copy(); patch[2,2]=float(hf)
 src_pairs=a.norm_coeffs(ctx['patch_src']); faces=[]; bad=[]
 for tri_i,tri in zip(a.INCIDENT,[a.TRIANGLES[i] for i in a.INCIDENT]):
  n=a.direct_face_normal(patch,tri); slope=math.degrees(math.atan2(math.hypot(n[0],n[2]),abs(n[1])))
  cap=max(35.0,a.face_slope_deg(src_pairs[tri_i]));faces.append((slope,cap))
  if slope>cap+2e-8: bad.append('slope')
 hinges=[]
 for i,(edge,(ta,tb)) in enumerate(a.HINGES):
  val=a.direct_hinge_deg(patch,a.TRIANGLES[ta],a.TRIANGLES[tb]);hinges.append(val)
  if val>ctx['sector_caps'][ctx['sectors'][i]]+2e-8:bad.append('sector')
  srcang=ctx['src_hinge'][i]; kind=ctx['hinge_categories'][i]
  if srcang<=30.0+a.EPS_ANGLE and val>30.0+2e-8:bad.append('new_over30')
  cap=ctx['p99_bank'] if kind=='bank' else (ctx['p99_interior'] if kind=='interior' else None)
  if cap is not None and srcang<=cap+a.EPS_ANGLE and val>cap+2e-8:bad.append(kind+'_p99')
 old=ctx['old_h']; src=ctx['source_h']; delta=float(np.float32(hf))-old
 if abs(delta)<1e-8:bad.append('no_move')
 if float(hf)<min(src,1.8)-1e-8 or float(hf)<ctx['water_floor_value']-1e-8:bad.append('floor')
 if abs(float(hf)-src)>2.0+1e-8:bad.append('budget')
 before=sum(x*x for x in ctx['now_hinge']); after=sum(x*x for x in hinges)
 if before<=1e-18 or (before-after)/before<1e-4:bad.append('benefit')
 return sorted(set(bad)), {'max_slope_excess_deg':max((x-y for x,y in faces),default=0.0),'max_sector_excess_deg':max((hinges[i]-ctx['sector_caps'][ctx['sectors'][i]] for i in range(len(hinges))),default=0.0),'min_benefit_fraction':(before-after)/before if before else None}
# Exact EV79 input and selector setup from author-executed; avoid main().
if a.sha(a.TERRAIN)!=a.EXPECTED_SHA: raise RuntimeError('EV79 source hash mismatch')
terrain=np.load(a.TERRAIN); src=terrain['heights'].copy(); cur=src.copy(); cls=terrain['cls']
con=np.load(a.CONSTRAINTS); fixed=con['fixed'].astype(bool,copy=False); wet=con['wet_support'].astype(bool,copy=False); eng=terrain['reserve']|terrain['platform']
rep=json.loads(a.BASELINE_REPORT.read_text(encoding='utf-8')); p99b=float(rep['angles']['stats']['bank']['candidate']['p99']);p99i=float(rep['angles']['stats']['interior']['candidate']['p99'])
p=np.load(a.SOURCE/'plane.npy',mmap_mode='r');f=np.load(a.SOURCE/'visible-field.npy',mmap_mode='r');floor=a.incident_water_floor(src,p,f)
flow=np.isin(cls,(3,5,6)); distance=distance_transform_edt(~flow,sampling=a.STEP); selector=(cls==0)&(distance<=96.0+1e-9)&~fixed&a.source_fold_nodes(src); rr,cc=np.nonzero(selector)
ev80=np.load(B/'candidate'/'terrain.npz')['heights']
started=time.monotonic(); counts={}; cases=[]; accepted=0; rejected=0
for idx,(r,c) in enumerate(zip(rr.tolist(),cc.tolist())):
 if time.monotonic()-started>180: break
 out=solve(r,c,cur,src,cls,fixed,wet,eng,distance,floor,p99b,p99i)
 if len(out)==3:
  _,reason,ctx=out;counts[reason]=counts.get(reason,0)+1;rejected+=1
  if reason.startswith('float32_'):
   base=np.float32(ctx['proposal']); old=np.float32(ctx['old_h']); vals=[]; val=base
   for ulps in (1,2):
    val=np.nextafter(val,old,dtype=np.float32); bad,metrics=check(ctx,val); vals.append({'ulps_toward_identity':ulps,'value':float(val),'violations':bad,'metrics':metrics})
   cases.append({'row':int(r),'col':int(c),'reason':reason,'old_height':ctx['old_h'],'proposal_float32':float(base),'one_ulp':vals[0],'two_ulp':vals[1]})
 else:
  out,reason=out;counts[reason]=counts.get(reason,0)+1
  if reason=='accepted':cur[r,c]=np.float32(out);accepted+=1
 if idx%500==0: print(f'PROGRESS {idx}/{len(rr)} accepted={accepted} sec={time.monotonic()-started:.1f}',flush=True)
elapsed=time.monotonic()-started
same=(idx+1==len(rr) and np.array_equal(cur,ev80))
sha_replay=hashlib.sha256(np.ascontiguousarray(cur).tobytes()).hexdigest();sha_ev80=hashlib.sha256(np.ascontiguousarray(ev80).tobytes()).hexdigest()
# Targeted summary for p99 reason; rescue only if both the one/two ULP candidate and all direct invariants pass.
p99=[x for x in cases if x['reason']=='float32_bank_p99_rejected']
rescue1=sum(not x['one_ulp']['violations'] for x in p99);rescue2=sum((not x['one_ulp']['violations']) or (not x['two_ulp']['violations']) for x in p99)
report_out={'status':'REPLAY_EXACT' if same else ('INCONCLUSIVE_TIMEOUT' if elapsed>180 or idx+1<len(rr) else 'FAIL_REPLAY_MISMATCH'),'source_author_sha256':a.sha(source_path),'expected_candidate_sha256':a.sha(B/'candidate'/'terrain.npz'),'selector_expected':int(len(rr)),'selector_processed':int(idx+1),'accepted':accepted,'rejected':rejected,'reason_counts':counts,'elapsed_seconds':round(elapsed,3),'candidate_height_array_sha256_replay':sha_replay,'candidate_height_array_sha256_ev80':sha_ev80,'height_arrays_byte_identical':same,'bank_p99':{'rejected':len(p99),'rescuable_at_one_ulp':rescue1,'rescuable_at_one_or_two_ulp':rescue2,'examples':p99[:12]},'all_float32_reject_samples':cases,'scope':'Diagnostic replay only; no NPZ or terrain written; neighboring nodes not changed by ULP probes; no thresholds relaxed.'}
out=B/'numeric-boundary-replay.json';out.write_text(json.dumps(report_out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:report_out[k] for k in ('status','selector_expected','selector_processed','accepted','reason_counts','elapsed_seconds','height_arrays_byte_identical','bank_p99') if k!='bank_p99'},ensure_ascii=False))
print('P99',json.dumps({k:v for k,v in report_out['bank_p99'].items() if k!='examples'}))
if not same: raise SystemExit(3)



