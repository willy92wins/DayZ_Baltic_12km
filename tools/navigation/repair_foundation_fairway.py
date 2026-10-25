"""Resolve the single v7 island-bank/fairway conflict at an unfixed bed vertex.

Choose the largest contributor to the failed sample that is neither an island
support nor a road vertex. Lower only that vertex, bounded by the accepted v4
bed. Full regional slopes, roads and vector-water depth are checked separately.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import rasterio
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_foundation_combined_v8'


def main():
    assert not OUT.exists(),'Fresh candidate required'
    ref=np.load(ROOT/'tests/regional_foundation_combined_v7/reference.npz')
    prior=np.load(ROOT/'tests/regional_foundation_combined_v4/reference.npz')['candidate']
    h=ref['candidate'].copy()
    report=json.loads((EV/'contour-water-consumers-terrain-v7.json').read_text())
    failed=[p for r in report['rivers'] for p in r['bad_examples']]
    assert len(failed)==1 and sum(r['shallow'] for r in report['rivers'])==1
    fixed=set(ref['road_fixed_vertices'].tolist());changes=[]
    for p in failed:
        x,z=p['xz'];col=x/6;row=(12282-z)/6;ci,ri=int(col),int(row);a,b=col-ci,row-ri
        if b<=a:terms=[(ri,ci,1-a),(ri,ci+1,a-b),(ri+1,ci+1,b)]
        else:terms=[(ri,ci,1-b),(ri+1,ci,b-a),(ri+1,ci+1,a)]
        choices=[(r,c,w) for r,c,w in terms if w>0 and r*2048+c not in fixed and not ref['island_support'][r,c] and h[r,c]>prior[r,c]]
        r,c,w=max(choices,key=lambda v:v[2])
        old=float(h[r,c]);target=old-(3.05-p['depth'])/w
        assert target>=prior[r,c],(target,prior[r,c])
        h[r,c]=target
        changes.append(dict(vertex_xz=[c*6,12282-r*6],before=old,after=float(h[r,c]),sample_xz=[x,z],target_sample_depth_m=3.05))
    assert np.array_equal(h.ravel()[ref['road_fixed_vertices']],ref['candidate'].ravel()[ref['road_fixed_vertices']])
    assert np.all(h>=ref['island_minimum'])
    OUT.mkdir(parents=True)
    asc=OUT/'baltic_regional_foundation_v8.asc'
    with asc.open('w',encoding='ascii',newline='\n') as f:
        f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(f,h,fmt='%.9g')
    with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),h)
    data={k:ref[k] for k in ref.files};data.update(candidate=h,changed=h!=ref['base'])
    np.savez_compressed(OUT/'reference.npz',**data)
    result=dict(status='LOCAL_REPAIR_REQUIRES_REGIONAL_GATES',changes=changes,asc_sha256=hashlib.sha256(asc.read_bytes()).hexdigest())
    (EV/'fairway-island-repair-v8.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
