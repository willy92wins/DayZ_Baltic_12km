"""Explain the rejected diagnostic; does not author or repair terrain."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path('E:/DayZ-Baltic-Build'); O=Path(__file__).parent
D4=R/'v30-coupled-shore-feasibility-20261010/feasibility.json'
bp=R/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
xp=O/'diagnostic-vector.npz'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=np.load(bp)['heights']; h=np.load(xp)['heights']; d=json.loads(D4.read_text())
vertices={tuple(q['vertex']) for q in d['scalar_delta_bounds']}; edges=set()
for r,c in vertices:
 for dr in (-1,0,1):
  for dc in (-1,0,1):
   if dr or dc:edges.add(tuple(sorted(((r,c),(r+dr,c+dc)))))
bad=[]
for u,v in sorted(edges):
 a=float(b[u])-float(b[v]); z=float(h[u])-float(h[v])
 if (a>0 and z<0) or (a<0 and z>0) or (a==0 and z!=0):
  bad.append({'edge':[u,v],'B_heights':[float(b[u]),float(b[v])],
              'diagnostic_heights':[float(h[u]),float(h[v])],
              'reversal_m':abs(z), 'both_variable':u in vertices and v in vertices})
bounds_bad=[]
for q in d['scalar_delta_bounds']:
 v=tuple(q['vertex']);lo,hi=q['delta_bounds'];delta=float(h[v])-float(b[v])
 if delta<lo or delta>hi:bounds_bad.append({'vertex':v,'delta':delta,'bounds':[lo,hi],
                                         'violation_m':max(lo-delta,delta-hi)})
report={'status':'REJECTED_DIAGNOSTIC_ANALYSIS_NO_CANDIDATE',
 'inputs':{str(p):sha(p) for p in (D4,bp,xp,Path(__file__))},
 'order_edges':len(edges),'order_failures':bad,'bound_failures':bounds_bad,
 'changed':int(np.count_nonzero(h!=b)),
 'max_order_violation_m':max((x['reversal_m'] for x in bad),default=0.),
 'max_bound_violation_m':max((x['violation_m'] for x in bounds_bad),default=0.)}
(O/'numeric-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('order_edges','changed','max_order_violation_m','max_bound_violation_m')}))
print(json.dumps({'order_failures':bad,'bounds_failures':bounds_bad}))
