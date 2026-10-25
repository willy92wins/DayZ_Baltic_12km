"""Consumer regressions: native edge dry gap, float32 WRP duplicate, invalid numeric inputs."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys
import numpy as np
P=Path(__file__).resolve().parents[4];B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013')
O=Path(sys.argv[1]);O.mkdir(parents=True,exist_ok=False)
R=B/'ev112-ot5-20261018/v6';K=B/'ev112-ot1-20261018/run-l'
S=P/'evidence/v31-pond-layer-2026-10-13/bridges/ev110/sites-ev110.json';T=P/'tools/terrain'
sys.path.insert(0,str(Path(__file__).parent));import gates_v6 as g
j=lambda p:json.loads(Path(p).read_text())
sites=j(S);run=g.gv.load_run(R);h0=np.load(K/'terrain-ev108.npz')['heights'].astype(float);env=np.load(K/'envelope-ev108.npy')
out={}
ok,d=g.g10(run,sites,h0,env);out['g10_positive']=dict(passed=ok,sites=d['sites'])
n=dict(run);n['H']=run['H'].copy();n['H'][898,1186]=np.float32(n['H'][898,1186]+1.648389)
good,detail=g.g10(n,sites,h0,env)
rep=next(s for s in run['rep']['sites'] if s['site']=='015-8');cl=g.resample(np.array(rep['channel']['centreline']),1.)
oldq=g.resample(cl,.5);oldh=g.gv.terr(n['H'],oldq[:,0],oldq[:,1])
dense=g.resample(np.array(rep['channel']['centreline']),.005);dh=g.gv.terr(n['H'],dense[:,0],dense[:,1])
target=detail['sites']['015-8']
out['g10_subsample']=dict(passed=bool(ok and not good and not target['pass_'] and target['dry_samples']>0 and (oldh<rep['level']).all() and (dh>=rep['level']).any()),old_samples_dry=int((oldh>=rep['level']).sum()),dense_samples_dry=int((dh>=rep['level']).sum()),target=target)
np.savez(O/'g10-mutated.npz',heights=n['H'].astype(np.float32))
pilot=B/'bridges/records.json';kit=K/'kit-records.json';merged=R/'records/records-merged.json'
if not merged.exists():
    candidates=list((R/'records').glob('*merged*.json'));assert len(candidates)==1;merged=candidates[0]
ok14,dd=g.g14(run,sites,merged,pilot,kit,R/'records/stage/baltic_trial.wrp',R/'records/stage-base/baltic_trial.wrp')
out['g14_positive']=dict(passed=ok14,details=dd)
kp=j(kit);dup=copy.deepcopy(kp[0]);dup['matrix'][9]+=1e-6
assert np.array_equal(np.float32(kp[0]['matrix']),np.float32(dup['matrix']))
kp.append(dup);(O/'kit-collapsed.json').write_text(json.dumps(kp))
mp=j(pilot)+kp+j(R/'bridge-records.json');(O/'merged-collapsed.json').write_text(json.dumps(mp))
args=[sys.executable,'-I',str(T/'merge_bridge_records_v31.py'),'--pilot',str(pilot),'--kit',str(O/'kit-collapsed.json'),'--bridges',str(R/'bridge-records.json'),'--sites',str(S),'--out',str(O/'refused.json')]
r=subprocess.run(args,capture_output=True,text=True);(O/'merge.log').write_text(r.stdout+r.stderr)
out['merge_float32']=dict(passed=r.returncode!=0 and not (O/'refused.json').exists() and 'float32' in r.stderr,rc=r.returncode)
stageargs=[sys.executable,'-I',str(T/'stage_bridges_v31.py'),str(R/'records/stage-base'),str(R/'terrain-br.npz'),str(O/'merged-collapsed.json'),str(O/'stage'),str(O/'stage-report.json')]
with (O/'stage.log').open('w') as f:rc=subprocess.run(stageargs,stdout=f,stderr=subprocess.STDOUT).returncode
assert rc==0, 'fixture staging failed'
gg,d=g.g14(run,sites,O/'merged-collapsed.json',pilot,O/'kit-collapsed.json',O/'stage/baltic_trial.wrp',R/'records/stage-base/baltic_trial.wrp')
out['g14_float32']=dict(passed=not gg and any('float32' in e for e in d['errors']) and any('float32' in e for e in d['stage']['errors']),details=d)
for name,key,value in [('nan-level','level',float('nan')),('negative-width','width',-8)]:
    q=O/name;q.mkdir();ss=copy.deepcopy(sites);ss[0][key]=value;(q/'sites.json').write_text(json.dumps(ss))
    outputs=[q/n for n in ('terrain.npz','envelope.npy','records.json','report.json')]
    args=[sys.executable,'-I',str(T/'bridges_v31.py'),str(K/'terrain-ev108.npz'),str(K/'envelope-ev108.npy'),str(q/'sites.json'),*map(str,outputs)]
    rr=subprocess.run(args,capture_output=True,text=True);(q/'run.log').write_text(rr.stdout+rr.stderr)
    out[name]=dict(passed=rr.returncode!=0 and not any(p.exists() for p in outputs),rc=rr.returncode)
result=dict(passed=all(e['passed'] for e in out.values()),cases=out,sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [T/'bridges_v31.py',T/'merge_bridge_records_v31.py',Path(__file__).with_name('gates_v6.py')]})
(O/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v['passed'] for k,v in out.items()}));sys.exit(0 if result['passed'] else 1)
