"""Ensure lakes without an8.485m interior retain actual water-depth samples."""
from pathlib import Path
import json,math
import numpy as np
from shapely import points
from shapely.geometry import shape
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'tests/regional_outline_smoothing_v26'
h=np.load(OUT/'reference.npz')['candidate'];base=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz')['candidate'];records=[]
for f in json.loads((ROOT/'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson').read_text())['features']:
    if not f['properties']['body'].startswith('lake_'):continue
    g=shape(f['geometry'])
    if not g.buffer(-6*math.sqrt(2)).is_empty:continue
    x0,z0,x1,z1=g.bounds;x,z=np.meshgrid(np.arange(x0+.23,x1,1.37),np.arange(z0+.41,z1,1.37));q=np.c_[x.ravel(),z.ravel()];q=q[g.contains(points(q))];q=np.r_[q,[g.representative_point().coords[0]]];q=np.clip(q,.001,12281.999)
    level=f['properties']['level_m'];before=level-sample(base,q[:,0]+200000,q[:,1]);after=level-sample(h,q[:,0]+200000,q[:,1]);best=int(np.argmax(after));records.append(dict(body=f['properties']['body'],area_m2=g.area,samples=len(q),deep_before=int((before>=.15).sum()),deep_after=int((after>=.15).sum()),maximum_before_m=float(before.max()),maximum_after_m=float(after.max()),best_xz=q[best].tolist(),passed=bool(after.max()>=.15-1e-5)))
report=dict(status='PASS_SAMPLED_SMALL_LAKE_RETENTION' if all(r['passed'] for r in records) else 'FAIL',lakes=len(records),records=records,limits=['Only lakes without an8.485m core; sample proof of retained water, not water area or visual continuity.'])
(OUT/'small-lakes.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
