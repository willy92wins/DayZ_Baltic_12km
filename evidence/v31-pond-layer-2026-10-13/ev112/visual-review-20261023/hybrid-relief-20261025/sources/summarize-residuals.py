from pathlib import Path
from collections import Counter
import hashlib,json
R=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[R/'guarded-relief-batch-e/shape-screen.json',R/'guarded-relief-batch-d/shape-screen.json',R/'guarded-relief-batch-e-replay/report.json']
e,d,a=[json.loads(p.read_text()) for p in paths]
rectangles=lambda doc:[f for f in doc['findings'] if f['kind']=='rectangular_terrain_transition']
assert rectangles(e)==rectangles(d)
remaining=[dict(cluster=x['cluster'],groups=x['groups'],status=x['status'],reason=x.get('reason'),error=x.get('error'),checks=x.get('checks')) for x in a['clusters'] if x['status']!='LOCAL_CHECKS_PASS']
domains={}
for kind in ('native_spike','native_pit','rectangular_terrain_transition'):
    rows=[f for f in e['findings'] if f['kind']==kind]
    domains[kind]=dict(total=len(rows),exact_tag_combinations=dict(Counter(' + '.join(sorted(f['domains'])) for f in rows)))
out=dict(status='RESIDUALS_OPEN',counts=e['finding_counts'],tag_combinations=domains,rejected_target_clusters=remaining,rectangle_findings_unchanged=rectangles(e),inputs={str(p):sha(p) for p in paths},limits=['A screen finding is not a uniquely confirmed visual defect.','Domain tags are descriptive and do not authorize changing protected heights.','Failed SLSQP is not proof of geometric impossibility.','The 10 unapplied target groups are a subset of all remaining findings.'])
(R/'guarded-relief-batch-e/residuals.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(counts=e['finding_counts'],pending_target_clusters=[dict(cluster=x['cluster'],groups=len(x['groups']),status=x['status']) for x in remaining],rectangles=rectangles(e)),indent=2))
