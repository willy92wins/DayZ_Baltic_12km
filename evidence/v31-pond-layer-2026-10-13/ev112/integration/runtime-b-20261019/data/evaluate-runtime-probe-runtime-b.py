"""Evaluate a freshly captured server log; never launches or changes DayZ state.
Usage: script raw-log fresh-attempt-directory. Retains every family's raw verdict.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,shutil
import numpy as np
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');Q=O/'probe-runtime-b'
sys.path.insert(0,str(O));from eval_bridge_regression_ev112 import load_rows
sys.path.insert(0,str(P/'tools/terrain'));from v30_common import tri_sample
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
consumer_source=O/'eval_bridge_regression_ev112.py'
consumer_controls=[O/'probe-framing-after/controls.json',O/'bridge-regression-framing-controls/controls.json']
assert all(json.loads(p.read_text())['status']=='PASS' and json.loads(p.read_text())['tool_sha256']==sha(consumer_source) for p in consumer_controls)
raw=Path(sys.argv[1]);D=Path(sys.argv[2]);assert not D.exists();manifest=json.loads((Q/'manifest.json').read_text())
assert all(sha(p)==h for p,h in manifest['inputs'].items())
points=json.loads((Q/'points.json').read_text());rows=load_rows(raw,points);assert len(points)==4114
D.mkdir(parents=True);shutil.copyfile(raw,D/'baltic_bridge_probe_v2.log')
for name in ('points.json','families.json','bridges-points.json','shores-points.json','dam-points.json'):shutil.copyfile(Q/name,D/name)
runs=[]
def run(name,args,cwd=D):
 cmd=[sys.executable,'-I',*map(str,args)]
 with (D/(name+'.log')).open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT).returncode
 runs.append(dict(step=name,rc=rc,cmd=cmd));print(name,rc,flush=True);return rc
assert run('split',[P/'evidence/v31-pond-layer-2026-10-13/ev110/probe/split_log.py',D/'baltic_bridge_probe_v2.log',D])==0
run('bridges-shores',[O.parent/'ev110/probe/eval_bridges_shores.py'])
run('bridge-regression',[O/'eval_bridge_regression_ev112.py',O.parent/'ev110/probe/bridges-points.json',O.parent/'ev110/probe/split/bridges-baltic_bridge_probe_v2.log',D/'bridges-points.json',D/'split/bridges-baltic_bridge_probe_v2.log',D/'bridge-regression.json'])
run('kit',[P/'evidence/v31-pond-layer-2026-10-13/ev112/ot1/gates/gate_g8_engine_probe.py',O/'water-fix-b/kit','--log',D/'split/kit-baltic_bridge_probe_v2.log'])
shutil.copyfile(O/'water-fix-b/kit/gate-g8.json',D/'kit-g8.json')
run('dam',[P/'tools/water/eval_dam_probe_v31.py',D/'dam-points.json',D/'split/dam-baltic_bridge_probe_v2.log',D/'dam.json'])
h=np.load(O/'water-fix-b/terrain.npz')['heights'];ground=tri_sample(h,[p['x'] for p in points],[p['z'] for p in points]);error=np.array([abs(rows[p['id']]['ground']-g) for p,g in zip(points,ground)])
ground_diag={fam:dict(points=sum(p['family']==fam for p in points),maximum=float(error[[p['family']==fam for p in points]].max())) for fam in sorted({p['family'] for p in points})}
read=lambda n:json.loads((D/n).read_text())
checks=dict(bridges_shores=read('eval-bridges-shores.json')['pass'],no_bridge_regression=read('bridge-regression.json')['status']=='PASS',kit=read('kit-g8.json')['passed'],dam=read('dam.json')['pass'],commands=all(r['rc']==0 for r in runs))
res=dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,steps=runs,raw_log_sha256=sha(raw),points_sha256=sha(Q/'points.json'),terrain_sha256=sha(O/'water-fix-b/terrain.npz'),consumer_sha256=sha(consumer_source),evaluator_sha256=sha(__file__),consumer_controls_sha256={str(p):sha(p) for p in consumer_controls},ground_match_diagnostic_by_family=ground_diag,limits='Server probe only; no personal visual acceptance or FPS result.')
(D/'acceptance.json').write_bytes((json.dumps(res,indent=2)+'\n').encode());print(json.dumps(res),flush=True);sys.exit(0 if all(checks.values()) else 1)
