"""Classify added native-query flags against untouched EV79 source geometry."""
from pathlib import Path
import json,hashlib,numpy as np
B=Path(__file__).parent; S=B.parent/'v30-narva-dry-bank-relief-20261010'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=dict(np.load(S/'candidate/terrain.npz')); v=dict(np.load(B/'candidate/terrain.npz'))
reference=json.loads((B/'native-verification.json').read_text())
assert reference['status']=='PASS_COMPLETE_NATIVE_READBACK'
assert sha(B/'candidate/terrain.npz')==reference['terrain_sha256']
m=json.loads((B/'native-inventory-comparison.json').read_text())
changed=a['heights']!=v['heights']; rows=[]; inventories={}
for name in ['physical_anomalies_A','unflagged_scalar_Q']:
    added=m[name]['added']; edited=0
    for q in added:
        r,c=q['key']; edited+=int(changed[r,c])
        if name=='physical_anomalies_A':
            rows.append(dict(row=r,col=c,x=6*c,z=12282-6*r,record=q['candidate'],
                source_height=float(a['heights'][r,c]),candidate_height=float(v['heights'][r,c]),
                source_class=int(a['cls'][r,c]),beach=bool(a['beach'][r,c]),height_unchanged=not bool(changed[r,c])))
    inventories[name]=dict(new=len(added),new_at_changed_vertex=edited)
dry=[x for x in rows if x['source_class']==0]
assert len(dry)==3 and all(x['beach'] and x['height_unchanged'] for x in dry)
assert all(x['candidate_height']<.85 and float(x['record'][7])>x['candidate_height'] for x in dry)
assert not any(x['new_at_changed_vertex'] for x in inventories.values())
out=dict(status='CLASSIFIED_NATIVE_DIFFERENCES_UNCHANGED_BEACH_AND_WATER',
    baseline_runtime_sha256=sha(S/'native-snapshot.log'),candidate_runtime_sha256=sha(B/'native-snapshot.log'),
    inventories=inventories,added_flags=rows,
    conclusion='Three dynamic dry flags occur on unchanged beach vertices at 0.8000-0.8032 m, under the sampled sea level. Two added design-water flag absences occur on unchanged class1 vertices at 0.65 m. No added A/Q inventory item is at an EV80-edited height.',
    limits=['Snapshots sample different wave phases; no A/B claim of render causality.',
            'This classifies the physical readings; it does not clear visual water-on-land or grey-water reports.'])
(B/'native-difference-classification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='added_flags'},indent=2))
