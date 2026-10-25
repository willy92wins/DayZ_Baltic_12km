from pathlib import Path
import sys,json,copy,hashlib,subprocess
O=Path(__file__).parent;D=O/'bridge-regression-framing-controls';D.mkdir(exist_ok=False);sys.path.insert(0,str(O));import eval_bridge_regression_ev112 as G
bp=O.parent/'ev110/probe/bridges-points.json';bl=O.parent/'ev110/probe/split/bridges-baltic_bridge_probe_v2.log';p=json.loads(bp.read_text());rows=G.load_rows(bl,p);assert G.judge(p,rows,p,rows)['status']=='PASS'
cases={};road=next(x for x in p if x['kind']=='road');wet=next(x for x in p if x['kind']=='under' and rows[x['id']]['depth']>0)
for name,k,f,value in [('road-step',road['id'],'roadY',rows[road['id']]['roadY']+1),('dry-under',wet['id'],'depth',-1),('new-sea',wet['id'],'sea',True),('surface-error',wet['id'],'surface',rows[wet['id']]['surface']+.1)]:
 n=copy.deepcopy(rows);n[k][f]=value;r=G.judge(p,rows,p,n);assert r['status']=='FAIL';cases[name]=dict(detected=True,failed_sites=r['failed_sites'])
for name,mutate in [('missing-row',lambda lines:[x for x in lines if not x.startswith('P;0;')]),('nonfinite-surface',lambda lines:[(';'.join(x.split(';')[:5]+['nan']+x.split(';')[6:]) if x.startswith('P;0;') else x) for x in lines])]:
 f=D/(name+'.log');f.write_text('\n'.join(mutate(bl.read_text().splitlines()))+'\n');got=None
 try:G.load_rows(f,p)
 except ValueError as e:got=str(e)
 assert got;cases[name]=dict(detected=True,reason=got)
out=dict(status='PASS',scope='Consumer controls on real historical EV110 data. No EV112 runtime is claimed.',baseline_self_comparison='PASS',tool_sha256=hashlib.sha256((O/'eval_bridge_regression_ev112.py').read_bytes()).hexdigest(),cases=cases);(D/'controls.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print(json.dumps(out),flush=True)
