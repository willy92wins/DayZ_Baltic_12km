"""Independent interior-depth audit for every standing-water polygon."""
from pathlib import Path
import argparse,json, math
import numpy as np
from shapely import points,prepare
from shapely.geometry import shape
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/regional-foundation-v1'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',default='v9');args=ap.parse_args()
    h=np.load(ROOT/f'tests/regional_foundation_combined_{args.version}/reference.npz')['candidate']
    records=[]
    for f in json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']:
        body=f['properties']['body']
        if not body.startswith('lake_'): continue
        g=shape(f['geometry']); inner=g.buffer(-1)
        if inner.is_empty: inner=g
        prepare(inner)
        x0,z0,x1,z1=inner.bounds
        xx,zz=np.meshgrid(np.arange(max(6,math.ceil(x0/6)*6),min(12282,x1),6),np.arange(max(6,math.ceil(z0/6)*6),min(12282,z1),6))
        p=np.c_[xx.ravel(),zz.ravel()];p=p[inner.contains(points(p))]
        if not len(p):p=np.array([g.representative_point().coords[0]])
        level=f['properties']['level_m'];depth=level-sample(h,p[:,0]+200000,p[:,1])
        best=np.argsort(-depth)[:5]
        records.append(dict(body=body,area_m2=g.area,level_m=level,points=len(p),deep_points=int((depth>=.15).sum()),max_depth_m=float(depth.max()),best=[dict(xz=p[i].tolist(),depth=float(depth[i])) for i in best]))
    report=dict(status='PASS_LAKE_INTERIOR_SAMPLES' if all(r['deep_points'] for r in records) else 'FAIL',lakes=len(records),insufficient_five=[r for r in records if r['deep_points']<5],records=records)
    output=EV/f'lake-interior-audit-{args.version}.json'
    assert not output.exists(),'Preserve evidence'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))

if __name__=='__main__':main()
