"""Diagnostic only: does the rounded vector water remain connected after native sampling?"""
from pathlib import Path
import json,sys
import numpy as np,shapely
from shapely.geometry import shape
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
sys.argv=[sys.argv[0],'b1']
scope={};code=(B/'verify_contour_valley.py').read_text()
exec(code[:code.index('cut=before.boundary')],scope)
h,water=scope['h'],scope['water']
design=np.load(B/'contour-design.npz');sd=design['sd'];zone=np.load(B/'candidate-b/masks.npz')['edited_shore']
def parts(g):return [p for p in getattr(g,'geoms',[g]) if p.geom_type=='Polygon' and p.area>=1.]
def details(g):
    p=parts(g);return dict(components=len(p),areas_m2=[q.area for q in p],bounds=[list(q.bounds) for q in p])
native_from_signed=h.copy();use=zone&np.isfinite(water)&np.isfinite(sd)
native_from_signed[use]=water[use]+.25*sd[use]
sampled=scope['wet_polygon'](native_from_signed)
target=shape(json.loads((scope['E']/'contour-design.geojson').read_text())['smoothed'])
out=dict(status='DIAGNOSTIC_ONLY',source=details(scope['before']),vector_target=details(target),native_sampling_of_target=details(sampled),B1=details(scope['after']),mismatches_B1_to_target=int(((scope['v']<water)!=(sd<0))[use].sum()),limits=['No depth or road acceptance; synthetic distance heights only isolate loss introduced by native sampling. No artifact built or deployed.'])
(scope['E']/'grid-representability.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
