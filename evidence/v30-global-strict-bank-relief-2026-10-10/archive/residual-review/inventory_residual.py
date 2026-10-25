"""Read-only EV87 residual inventory; uses independent EV87 verifier geometry helpers."""
import csv,hashlib,importlib.util,json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(r'E:/DayZ-Baltic-Build')
OUT=ROOT/'v30-global-strict-bank-relief-20261010'
DEST=OUT/'residual-review'
VERIFY=OUT/'review-independent/verify_ev87.py'
B_PATH=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
C_PATH=OUT/'candidate-terrain.npz'
EV79=ROOT/'v30-narva-dry-bank-relief-20261010'
CONS_PATH=EV79/'constraints.npz'
PRIOR_PATH=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
P_PATH=EV79/'candidate/plane.npy';F_PATH=EV79/'candidate/visible-field.npy'
N=2048;CELL=6.0;Z0=12282.0;SECTOR=64

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def load_npz(p):
 with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def percentile_summary(values):
 if not values:return {'count':0,'min':None,'median':None,'max':None}
 a=np.asarray(values,dtype=np.float64)
 return {'count':int(a.size),'min':float(a.min()),'median':float(np.median(a)),'max':float(a.max())}

def main():
 DEST.mkdir(parents=True,exist_ok=True)
 v=module('ev87_residual_independent',VERIFY)
 b=load_npz(B_PATH);c=load_npz(C_PATH);cons=load_npz(CONS_PATH);prior=load_npz(PRIOR_PATH)
 p=np.load(P_PATH,allow_pickle=False);f=np.load(F_PATH,allow_pickle=False)
 hb=np.asarray(b['heights']);hc=np.asarray(c['heights'])
 assert hb.shape==hc.shape==(N,N) and hb.dtype==hc.dtype
 elig_b,level_b=v._ev87_eligible(b,cons,prior,hb,p,f)
 elig_c,level_c=v._ev87_eligible(b,cons,prior,hc,p,f)
 angles_b=dict(v.edge_angles(hb));angles_c=dict(v.edge_angles(hc))
 seeds_b,_,_=v._ev87_selector(hb,elig_b,angles_b)
 seeds_c,_,_=v._ev87_selector(hc,elig_c,angles_c)
 header,patches,final=(lambda ev:(ev[0],[x for x in ev[1:-1] if x.get('event')=='patch'],ev[-1]))(
  [json.loads(line) for line in (OUT/'queue-ledger.jsonl').read_text(encoding='utf-8').splitlines()])
 assert final['status']=='COMPLETE' and len(patches)==955
 patch_by_center={tuple(q['center']):q for q in patches}
 excluded_by_center={tuple(q['coordinates']):q for q in header['excluded']}
 accepted_focus_delta=[]
 for q in patches:
  if q['state']=='accepted':
   r,col=q['center'];accepted_focus_delta.append(float(hc[r,col])-float(hb[r,col]))
 reason_counts=Counter();reason_detail_counts=Counter();state_counts=Counter()
 for q in patches:
  state_counts[q['state']]+=1
  if q['state']!='accepted':
   raw=str(q.get('reason','unspecified'));reason_detail_counts[raw]+=1
   if q['state']=='rejected_lp':
    category='LP infeasible (HiGHS status 8)' if raw.startswith('linprog:2:') else 'LP failure'
    reason_counts[category]+=1
   else:
    for reason in raw.split(';'):reason_counts[reason]+=1

 def angular_counts(angles):
  result={}
  total_hot=total_over30=0
  for kind,a in angles.items():
   over=int(np.count_nonzero(a>30.0));hot=int(np.count_nonzero(a>30.0001));total_over30+=over;total_hot+=hot
   result[kind]={'hinges':int(a.size),'over30deg':over,'hot_over30_0001deg':hot,'max_deg':float(np.max(a))}
  result['total']={'hinges':sum(x['hinges'] for k,x in result.items() if k!='total'),'over30deg':total_over30,'hot_over30_0001deg':total_hot}
  return result
 angle_count_b=angular_counts(angles_b);angle_count_c=angular_counts(angles_c)
 # Recomputed residual seeds are the only rows in this CSV; original sampler exclusions alone do not qualify.
 residual_rows=[];sector_rows=defaultdict(lambda:{'residual_seeds':0,'max_incident_deg':0.0,'hot_hinges_diag':0,'hot_hinges_vertical':0,'hot_hinges_horizontal':0})
 for s in seeds_c:
  r,col=map(int,s['center']);coord=(r,col);old=patch_by_center.get(coord);ex=excluded_by_center.get(coord)
  state=old['state'] if old else ('sampler_excluded:'+str(ex.get('reason')) if ex else 'not_in_original_seed_inventory')
  prominence=float(v._ev87_prominence_m(hc,r,col));sector=(r//SECTOR,col//SECTOR)
  row={'row':r,'col':col,'x_m':float(col*CELL),'z_m':float(Z0-r*CELL),'max_incident_angle_deg':float(s['max_incident_angle_deg']),
       'axial_prominence_m':prominence,'sector_row64':sector[0],'sector_col64':sector[1],
       'original_patch_state':state,'original_queue_id':old['queue_id'] if old else None}
  residual_rows.append(row);q=sector_rows[sector];q['residual_seeds']+=1;q['max_incident_deg']=max(q['max_incident_deg'],row['max_incident_angle_deg'])
 for kind,a in angles_c.items():
  rr,cc=np.nonzero(a>30.0001)
  for r,col in zip(rr,cc):sector_rows[(int(r)//SECTOR,int(col)//SECTOR)]['hot_hinges_'+kind]+=1
 with (DEST/'residual-seeds.csv').open('w',newline='',encoding='utf-8') as fcsv:
  writer=csv.DictWriter(fcsv,fieldnames=list(residual_rows[0]) if residual_rows else ['row','col','x_m','z_m','max_incident_angle_deg','axial_prominence_m','sector_row64','sector_col64','original_patch_state','original_queue_id'])
  writer.writeheader();writer.writerows(residual_rows)
 sectors=[{'sector_row64':r,'sector_col64':col,'x_min_m':col*SECTOR*CELL,'x_max_m':(col+1)*SECTOR*CELL,
            'z_min_m':Z0-(r+1)*SECTOR*CELL,'z_max_m':Z0-r*SECTOR*CELL,**v}
           for (r,col),v in sorted(sector_rows.items()) if v['residual_seeds'] or any(v[k] for k in ('hot_hinges_diag','hot_hinges_vertical','hot_hinges_horizontal'))]
 payload={'status':'OFFLINE_RESIDUAL_INVENTORY_NOT_ARTISTIC_VALIDATION','geometry_method':{
   'hot_hinge':'dihedral angle >30.0001 degrees','prominence':'strict axial peak >0.1m over both cardinal neighbors on at least one axis',
   'eligibility':'EV87 independent _ev87_eligible: class0, not other_fixed/engineering_halo/large_lake_banks, and height>max(P/F/sea level)',
   'seed_order':'recomputed independent verifier order, np.argwhere row-major; candidate residual inventory only; no optimizer calls',
   'sectors':'64x64 grid-cell blocks, matching EV87 verifier sector partition; cell width 6m =>384m'},
  'hashes':{'B_sha256':sha(B_PATH),'candidate_sha256':sha(C_PATH),'EV79_constraints_sha256':sha(CONS_PATH),
            'prior_constraints_sha256':sha(PRIOR_PATH),
            'P_sha256':sha(P_PATH),'F_sha256':sha(F_PATH),'ledger_sha256':sha(OUT/'queue-ledger.jsonl'),
            'verifier_sha256':sha(VERIFY),'analysis_script_sha256':sha(__file__)},
  'counts':{'B_eligible_vertices':int(elig_b.sum()),'candidate_eligible_vertices':int(elig_c.sum()),
            'B_recomputed_hot_prominent_seeds':len(seeds_b),'candidate_residual_hot_prominent_seeds':len(seeds_c),
            'B_angular_hinges':angle_count_b,'candidate_angular_hinges':angle_count_c,
            'EV87_original_queue_selected':len(patches),'EV87_original_queue_states':dict(state_counts),
            'accepted_focus_descent_m':percentile_summary(accepted_focus_delta),
            'rejected_reason_counts':dict(reason_counts),'rejected_raw_reason_counts':dict(reason_detail_counts),
            'residual_seeds_still_from_accepted_patches':sum(1 for x in residual_rows if x['original_patch_state']=='accepted'),
            'residual_seeds_from_rejected_patches':sum(1 for x in residual_rows if str(x['original_patch_state']).startswith('rejected_')),
            'residual_seeds_originally_sampler_excluded':sum(1 for x in residual_rows if str(x['original_patch_state']).startswith('sampler_excluded:')),
            'residual_seeds_not_in_original_inventory':sum(1 for x in residual_rows if x['original_patch_state']=='not_in_original_seed_inventory')},
  'sectors_with_residuals_or_hot_hinges':sectors,
  'outputs':{'residual_csv':str(DEST/'residual-seeds.csv'),'residual_csv_sha256':sha(DEST/'residual-seeds.csv')}}
 out=DEST/'residual-inventory.json';out.write_text(json.dumps(payload,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
 out_hash=sha(out);(DEST/'residual-inventory.sha256').write_text(out_hash+'  residual-inventory.json\n',encoding='ascii')
 print(json.dumps({'status':payload['status'],'B_seeds':len(seeds_b),'candidate_residual_seeds':len(seeds_c),'B_hot_hinges':angle_count_b['total']['hot_over30_0001deg'],'candidate_hot_hinges':angle_count_c['total']['hot_over30_0001deg'],
  'accepted_focus_descent':payload['counts']['accepted_focus_descent_m'],'rejected_reasons':dict(reason_counts),'json_sha256':out_hash,'csv_sha256':payload['outputs']['residual_csv_sha256']},ensure_ascii=False))

if __name__=='__main__':main()
