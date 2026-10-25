"""Do not accept a narrower cap if its native contour becomes more angular."""
from pathlib import Path
import json,sys
import numpy as np
from shapely.geometry import Polygon
B=Path('E:/DayZ-Baltic-Build/v30-river-end-tapers-20261009')
sys.path.insert(0,str(B))
from author_msta_taper import native_polygon
a=json.loads((B/'candidate-msta/authoring.json').read_text());p=np.load(B/'candidate-msta/frozen_planes.npy')
h=np.load('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/measured-bank-bed-r2/terrain.npz')['heights']
v=np.load(B/'candidate-msta/terrain.npz')['heights']


def turns(grid):
    g=native_polygon(grid,p,a['box'])
    poly=max([q for q in getattr(g,'geoms',[g]) if q.geom_type=='Polygon'],key=lambda q:q.area)
    ring=poly.exterior
    values=[]
    for s in np.arange(0,ring.length,1):
        pt=np.array(ring.interpolate(s).coords[0])
        if pt[0]<12186:continue
        aa=pt-np.array(ring.interpolate((s-3)%ring.length).coords[0]);bb=np.array(ring.interpolate((s+3)%ring.length).coords[0])-pt
        angle=np.degrees(np.arccos(np.clip(aa.dot(bb)/(np.linalg.norm(aa)*np.linalg.norm(bb)),-1,1)))
        values.append(angle)
    return dict(samples=len(values),mean_deg=float(np.mean(values)),p90_deg=float(np.percentile(values,90)),max_deg=float(max(values)),over_30_fraction=float(np.mean(np.array(values)>30)))


before,after=turns(h),turns(v)
gate=after['p90_deg']<=before['p90_deg'] and after['over_30_fraction']<=before['over_30_fraction']
report=dict(status='PASS_NATIVE_TURNS_RUNTIME_PENDING' if gate else 'FAIL_NATIVE_TURNS_NOT_FOR_PACKAGING',
    before=before,after=after,method='Native contour, 1 m arc samples, 3 m each side, x>=12186; no target-ellipse input.',
    consequence='The previous PASS is limited to physical/width gates. Shape acceptance additionally requires this contour gate and a runtime view.')
(B/'msta-turns.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
