from pathlib import Path
import numpy as np,json
E=Path(__file__).parent;R=E.parent
t=np.load(R/'v30-complete-dry-surface-20261009/candidate/terrain.npz');P=np.load(R/'v30-remaining-exact-dry-support-20261009/candidate/plane.npy')
b=json.loads((E/'bridge-water-inventory.json').read_text())
rows=[]
for x,z in [(2417,6889),(2370,6840),(2460,6840),(2400,6950),(2320,7050),(2400,6816),(2400,6864),(2448,6864),(2448,6816)]:
    c=round(x/6);r=round((12282-z)/6)
    objects=[o for o in b['nearby_water'] if abs(o['matrix'][9]-x)<35 and abs(o['matrix'][11]-z)<35]
    rows.append(dict(x=x,z=z,row=r,col=c,ground=float(t['heights'][r,c]),cls=int(t['cls'][r,c]),level=float(t['level'][r,c]),plane=float(P[r,c]) if np.isfinite(P[r,c]) else None,near_objects=objects))
(E/'bridge-water-point-data.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps([{k:v for k,v in q.items() if k!='near_objects'}|dict(near_objects=[(o['id'],o['matrix'][10]) for o in q['near_objects']]) for q in rows],indent=2))
