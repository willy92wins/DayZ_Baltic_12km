from pathlib import Path
import csv,json,hashlib
import numpy as np
B=Path(__file__).parent;R=B.parent;OLD=R/'v30-base-surface-runtime-20261009'
h=np.load(R/'v30-remaining-exact-dry-support-20261009/candidate/terrain.npz')['heights']
v=np.load(B/'candidate/terrain.npz')['heights']
def rows(path):
    with path.open(newline='') as f:return {(int(q['row']),int(q['col'])):q for q in csv.DictReader(f)}
a=rows(OLD/'base-surface-physical-anomalies.csv');b=rows(B/'narva-drybank-physical-anomalies.csv')
def scalar(path):
    out={}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('Q;'):
            q=line.split(';');out[(int(q[1]),int(q[2]))]=q
    return out
qa,qb=scalar(OLD/'native-snapshot.log'),scalar(B/'native-snapshot.log')
def describe(keys,old,new):
    ans=[]
    for r,c in sorted(keys):
        ans.append(dict(row=r,col=c,x=c*6,z=12282-r*6,source_height=float(h[r,c]),candidate_height=float(v[r,c]),height_changed=bool(h[r,c]!=v[r,c]),source_record=old.get((r,c)),candidate_record=new.get((r,c))))
    return ans
out=dict(status='NATIVE_INVENTORY_COMPARISON_NOT_RENDER_ACCEPTANCE',
    missing_presence=dict(source=len(a),candidate=len(b),common=len(set(a)&set(b)),new=describe(set(b)-set(a),a,b),no_longer=describe(set(a)-set(b),a,b)),
    positive_scalar_without_presence=dict(source=len(qa),candidate=len(qb),common=len(set(qa)&set(qb)),new=describe(set(qb)-set(qa),qa,qb),no_longer=describe(set(qa)-set(qb),qa,qb)),
    dry_physical_anomalies=0,
    limits=['Runs sample different native ocean wave phases; flags/scalars cannot be equated to visual water.',
            'Exact source/compiled water exposure and frozen heights at wet faces rule out changed terrain there, but do not diagnose native scalar/wave behavior.'])
(B/'native-inventory-comparison.json').write_text(json.dumps(out,indent=2)+'\n')
for key in ['missing_presence','positive_scalar_without_presence']:
    q=out[key];print(key,dict(source=q['source'],candidate=q['candidate'],common=q['common'],added=len(q['new']),removed=len(q['no_longer']),added_at_changed_heights=sum(v['height_changed'] for v in q['new'])))
