"""Exercise new CLI refusal paths against real frozen source with isolated output."""
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/water'));from review_compact_collision_v31 import load
A=R/'river-kit7-midpoint-a-20261026';O=R/'kit7-contact-only-negative-controls-20261026';O.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
author=read(A/'author-report.json');name='cs_kit_7_0024.p3d';i=next(i for i in author['instances'] if i['model'].endswith(name))
p=A/'source'/i['model'].replace('\\','/');_,lods,_=load(p);xyz=np.array([v.coords for v in lods[1].points])+i['origin'];corner=xyz[xyz[:,0].argmin()]
target=O/'boundary-target.json';target.write_text(json.dumps({name:[dict(id=0,x=float(corner[0]),z=float(corner[2]))]}))
operator=W/'tools/water/overlap_stream_collision_v31.py';before={str(q):sha(q) for q in [p,A/'author-report.json',operator]};rows=[]
for label,extra in [('missing-targets',[]),('conflicting-flags',['--contact-targets',str(target),'--minimal-bbox-anchors']),('changed-bounds',['--contact-targets',str(target)])]:
 dest=O/label
 args=[sys.executable,'-I',str(operator),str(A),str(dest),'--models',name,'--expected-author-sha256',sha(A/'author-report.json'),'--contact-only',*extra]
 q=subprocess.run(args,capture_output=True,timeout=120,creationflags=0x08000000);(O/(label+'.stdout.log')).write_bytes(q.stdout);(O/(label+'.stderr.log')).write_bytes(q.stderr)
 assert q.returncode!=0 and not (dest/'overlap-report.json').exists()
 if label=='changed-bounds':assert b'AssertionError' in q.stderr and (b'delta_min' in q.stderr or b'delta_max' in q.stderr)
 else:assert q.returncode==2 and not dest.exists() and b'--contact-only requires targets' in q.stderr
 rows.append(dict(name=label,rejected=True,exit_code=q.returncode))
assert all(sha(Path(p))==h for p,h in before.items())
report=dict(status='CONTACT_ONLY_NEGATIVE_CONTROLS_PASS',cases=rows,inputs=before,inputs_unchanged=True,limits='CLI/source controls only; no native acceptance.')
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

