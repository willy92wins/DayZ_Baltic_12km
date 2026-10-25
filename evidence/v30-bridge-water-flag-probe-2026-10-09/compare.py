from pathlib import Path
import json, csv, hashlib
import numpy as np

B=Path(__file__).parent; R=B.parent; A=R/'v30-strict-dry-composition-20261009'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
aa=json.loads((A/'dryfloor-fullwater-verification.json').read_text())
bb=json.loads((B/'bridge-omission-fullwater-verification.json').read_text())
assert aa['status']==bb['status']=='PASS_COMPLETE_NATIVE_READBACK'
assert aa['terrain_sha256']==bb['terrain_sha256']
assert aa['pbo']['baltic_water_v30.pbo']==bb['pbo']['baltic_water_v30.pbo']
assert json.loads((B/'deploy.json').read_text())['changed_entries']==['baltic_trial.wrp']
def rows(path):
    return {(int(r['row']),int(r['col'])):r for r in csv.DictReader(path.open())}
before=rows(A/'dryfloor-physical-anomalies.csv')
after=rows(B/'bridge-omission-physical-anomalies.csv')
target={(897,395),(898,394),(899,413),(900,413),(901,414)}
flowA={k for k,v in before.items() if int(v['cls'])==3}
flowB={k for k,v in after.items() if int(v['cls'])==3}
h=np.load(A/'candidate/terrain.npz')['heights']; p=np.load(A/'candidate/plane.npy')
points=[]
for r,c in sorted(target):
    levels=[float(p[rr,cc]) for rr,cc in [(r,c),(r-1,c),(r,c-1),(r-1,c-1)] if np.isfinite(p[rr,cc])]
    points.append(dict(row=r,col=c,ground=float(h[r,c]),incident_levels=levels,
        minimum_nominal_depth_m=min(levels)-float(h[r,c]),
        missing_with_bridge=(r,c) in flowA,missing_without_bridge=(r,c) in flowB))
gates=dict(all_five_change=flowA-flowB==target,no_new_flow_flags=not(flowB-flowA),
    thirteen_controls_exact=flowB==flowA-target and len(flowB)==13,
    wet_in_all_incident_planes=all(x['minimum_nominal_depth_m']>=.10 for x in points),
    four_million_readback=aa['vertices']==bb['vertices']==4194304,
    source_stage_exact=json.loads((B/'stage.json').read_text())['other_objects_exact'])
negatives=dict(four_changes_rejected=(flowA-flowB-{next(iter(target))})!=target,
    an_extra_change_rejected=(flowA-flowB|{next(iter(flowB))})!=target)
assert all(negatives.values())
report=dict(status='PASS_BRIDGE_OBJECT_CAUSES_QUERY_SUPPRESSION' if all(gates.values()) else 'INCONCLUSIVE',gates=gates,
    target_points=points,controls=sorted([list(x) for x in flowB]),negatives=negatives,
    before_by_class=aa['missing_by_class'],after_by_class=bb['missing_by_class'],
    source_A_sha256=sha(A/'dryfloor-fullwater-runtime.log'),source_B_sha256=sha(B/'bridge-omission-fullwater-runtime.log'),
    limits=['Only bridge objects differed; the exact native implementation inside the bridge remains opaque.',
        'These five class anomalies are object-dependent water-query results, not missing water geometry.',
        'Ocean counts and unflagged scalar queries vary with wave phase and are not an effect-size measure.',
        'Diagnostic removal is never promoted. The terrain baseline retains all nine bridges.'])
(B/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
