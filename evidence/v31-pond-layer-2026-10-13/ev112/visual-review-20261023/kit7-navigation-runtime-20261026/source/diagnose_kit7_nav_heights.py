"""Read-only discrimination of nav waypoint height versus exact packed Roadway."""
from pathlib import Path
import hashlib,json,sys
from collections import Counter
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/navigation'),str(W/'tools/water'),str(W/'tools/terrain')]
from verify_kit7_nav_ev112 import vector
from prepare_visual_probe_v31 import height
D=R/'kit7-nav-consumer-20261026';G=R/'kit7-packed-nav-discovery-20261026';O=R/'kit7-nav-height-diagnostic-20261026';O.mkdir(exist_ok=False)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
reference=read(D/'reference.json');result=read(D/'result.json');geometry=read(G/'geometry.json');meshes=np.load(G/'roadway.npz')
queries={q['name']:q for q in reference['queries']};failed_names={s.split('/')[0] for s in result['height_issues']}
samples=[]
for line in (D/'runtime.log').read_text(encoding='utf-8-sig').splitlines():
    fields=line.split(';')
    if fields[0]!='P' or fields[1] not in failed_names:continue
    name=fields[1];nav,ground,road=map(vector,fields[3:]);packed=[]
    for model in queries[name]['allowed_models']:
        key=model.split('\\')[-1]+'_dry';y=height(meshes[key],np.array(nav)[[0,2]])
        if y is not None:packed.append(dict(model=model,y=y))
    assert packed
    max_y=max(v['y'] for v in packed)
    samples.append(dict(query=name,index=int(fields[2]),nav=nav,terrain=ground,engine_roadway=road,packed=packed,
                        error_m=abs(nav[1]-road[1]),excess_m=max(0.,abs(nav[1]-road[1])-.801),
                        engine_minus_packed_m=road[1]-max_y,nav_minus_packed_m=nav[1]-max_y))
paths=[Path(__file__),D/'result.json',D/'runtime.log',D/'reference.json',G/'geometry.json',G/'roadway.npz']
summary=dict(status='DIAGNOSTIC_ONLY',path_cases=dict(Counter(c['status'] for c in result['cases'])),
             horizontal_local=dict(Counter(v['status'] for v in result['local_coverage'].values())),
             height_issue_count=len(result['height_issues']),failed_names=sorted(failed_names),samples=samples,
             inputs={str(p):sha(p) for p in paths},
             hypothesis='Generator detail-height approximation or wrong collision input; not isolated yet.',
             limits='No geometry correction, tolerance change or accepted graph. Surface agreement is checked only at these recorded waypoints.')
(O/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='inputs'},indent=2))
