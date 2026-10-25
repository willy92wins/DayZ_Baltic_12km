from pathlib import Path
import json,numpy as np
B=Path(__file__).parent;R=B.parent
report=json.loads((B/'boundary-feasibility.json').read_text());scope=np.load(R/'v30-low-dry-domain-classification-20261009/domain.npz');old=np.load(R/'v30-native-hinge-finish-20261009/constraints.npz');t=np.load(R/'v30-strict-dry-composition-20261009/candidate/terrain.npz')
results=[]
for e in report['edges']:
    if e['unavoidable_local_excess']<=1e-5:continue
    rows=[]
    for v in e['vertices']:
        if v['allowed']:continue
        r,c=v['row'],v['col'];rows.append(dict(row=r,col=c,actual_wet_face=bool(scope['wet_face_support'][r,c]),earlier_fixed=bool(scope['fixed'][r,c]),cls=int(t['cls'][r,c]),large_lake=bool(old['large_lake_banks'][r,c])))
    results.append(dict(target=e['target_vertex'],fixed_neighbours=rows))
out=dict(status='READ_ONLY_EXACT_SUPPORT_DISCRIMINATOR',edges=results,all_fixed_neighbours=sum(len(e['fixed_neighbours']) for e in results),actual_wet_neighbours=sum(v['actual_wet_face'] for e in results for v in e['fixed_neighbours']))
(B/'exact-support-discriminator.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='edges'},indent=2))
