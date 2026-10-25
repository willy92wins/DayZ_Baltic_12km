from pathlib import Path
import json,collections,sys
O=Path(__file__).parent;D=O/'runtime-eval-ae-20261019'
sys.path.insert(0,str(O));from eval_bridge_regression_ev112 import load_rows
ps=json.loads((O/'probe-c/points.json').read_text());rows=load_rows(D/'baltic_bridge_probe_v2.log',ps)
print('POINT_FIELDS',list(ps[0]))
bad=[]
for p in ps:
 r=rows[p['id']]
 if p['family']=='kit' and p.get('expect') in ('wet','dry','test'):
  fails=(r['depth']>0) if p['expect']=='dry' else (r['depth']<=0)
  if fails:bad.append(dict(point=p,row=r))
print('FAIL_KINDS',collections.Counter((x['point']['kind'],x['point']['expect']) for x in bad))
for x in bad:
 if x['point']['expect']!='test':print('REQUIRED_FAIL',json.dumps(x))
print('CONCRETE_SITE_COUNTS',collections.Counter(x['point'].get('site') for x in bad if x['point']['expect']=='test'))
for p in ps:
 if p['family']=='shores' and p.get('expect')=='wet' and rows[p['id']]['depth']<=0: print('SHORE_FAIL',json.dumps(dict(point=p,row=rows[p['id']])))
(D/'all-kit-failures.json').write_text(json.dumps(bad,indent=2)+'\n')
