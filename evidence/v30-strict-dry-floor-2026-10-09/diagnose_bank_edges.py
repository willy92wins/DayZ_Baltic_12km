from pathlib import Path
import sys,json
import numpy as np
from scipy.ndimage import distance_transform_edt,label
B=Path(__file__).parent;R=B.parent
sys.path.insert(0,str(R/'v30-surface-crease-audit-20261009'))
from audit_native_surface import hinges,incident_all,incident_any
t=np.load(R/'v30-volkhov-stable-derivatives-20261009/candidate/terrain.npz');h=t['heights'].astype(float);v=np.load(B/'candidate/terrain.npz')['heights'].astype(float);p=np.load(R/'v30-volkhov-stable-derivatives-20261009/candidate/plane.npy');d=np.load(B/'constraints.npz');allowed=d['allowed'];target=d['target']
pmax=np.full(h.shape,-np.inf)
for dr,dc in [(0,0),(0,1),(1,0),(1,1)]:np.fmax(pmax[dr:dr+2047,dc:dc+2047],p,out=pmax[dr:dr+2047,dc:dc+2047])
dry=(h>=pmax)&(h>=.85);natural=dry&~t['reserve']&~t['platform'];bank=natural&(distance_transform_edt(dry)*6<=54)
threshold=json.loads((B/'verification.json').read_text())['angles']['natural_bank']['before']['p99_degrees']
offsets={'diagonal':[(0,0),(0,1),(1,0),(1,1)],'vertical':[(0,0),(0,1),(1,1),(1,2)],'horizontal':[(0,0),(1,0),(1,1),(2,1)]}
marks=np.zeros(h.shape,bool);rows=[]
for (kind,a),(_,b) in zip(hinges(h),hinges(v)):
    hit=incident_all(bank,kind)&incident_any(allowed,kind)&(b>np.maximum(a,threshold)+1e-5)
    for r,c in zip(*np.nonzero(hit)):
        ids=[(int(r+dr),int(c+dc)) for dr,dc in offsets[kind]]
        for rr,cc in ids:marks[rr,cc]=True
        rows.append(dict(kind=kind,row=int(r),col=int(c),before=float(a[r,c]),after=float(b[r,c]),vertices=[dict(row=rr,col=cc,before=float(h[rr,cc]),after=float(v[rr,cc]),allowed=bool(allowed[rr,cc]),target=bool(target[rr,cc])) for rr,cc in ids]))
repair=(distance_transform_edt(~marks,sampling=6)<=12)&allowed
labels,n=label(repair,structure=np.ones((3,3)));sizes=np.bincount(labels.ravel())[1:]
np.savez_compressed(B/'bank-repair-domain.npz',marks=marks,repair=repair,labels=labels)
report=dict(status='READ_ONLY_FAILED_GATE_DIAGNOSIS',threshold_degrees=threshold,offending_edges=len(rows),repair_vertices=int(repair.sum()),components=n,sizes=sizes.tolist(),edges=rows)
(B/'bank-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='edges'},indent=2));print(json.dumps(rows[:4],indent=2))
