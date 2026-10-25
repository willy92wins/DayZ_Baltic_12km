"""Remove raster-corner overreach from V25's 30m geometric water exclusion."""
from pathlib import Path
import hashlib, json, shutil
import numpy as np
from rasterio.features import rasterize
from affine import Affine
from shapely.geometry import shape, Point

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'tests/regional_road_network_v25_constraints'
OUT=ROOT/'tests/regional_road_network_v26_constraints'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert not OUT.exists();OUT.mkdir()
    receipt=json.loads((SOURCE/'build-receipt.json').read_text())
    assert sha(SOURCE/'constraints.npz')==receipt['constraints_sha256']=='3469600d0938243d724f08df966565d816e476aec665ece3f60e611302eace7e'
    assert sha(SOURCE/'variables.npz')==receipt['variables_sha256']=='bf8609277742198917e7f312796668c49ae342511186c591fd63c4131734820f'
    data=np.load(SOURCE/'variables.npz');polys=[]
    for name,digest in receipt['exact_water_sources'].items():
        p=ROOT/'evidence/regional-foundation-v1'/name;assert sha(p)==digest
        polys.extend(shape(f['geometry']) for f in json.loads(p.read_text())['features'])
    cells=rasterize([(g,1) for g in polys],out_shape=(2047,2047),transform=Affine(6,0,0,0,-6,12282),all_touched=True,dtype='uint8').astype(bool)
    corners=np.zeros((2048,2048),bool)
    for dy,dx in ((0,0),(0,1),(1,0),(1,1)):corners[dy:2047+dy,dx:2047+dx]|=cells
    # Raster sample centres coincide with the native vertices. Buffer true
    # geometry, not already-expanded cell corners. The explicit corner union
    # additionally makes every native water face immutable.
    exact30=rasterize([(g.buffer(30,quad_segs=64),1) for g in polys],out_shape=(2048,2048),transform=Affine(6,0,-3,0,-6,12285),all_touched=False,dtype='uint8').astype(bool)
    protected=exact30|corners;fixed=protected.ravel()[data['indices']]
    point=Point(7656,9750);distance=min(point.distance(g) for g in polys)
    k=int(np.flatnonzero(data['indices']==((12282-9750)//6)*2048+7656//6)[0])
    assert distance>37 and data['force_unchanged'][k] and not fixed[k]
    assert np.all(protected[corners])
    shutil.copyfile(SOURCE/'constraints.npz',OUT/'constraints.npz')
    np.savez_compressed(OUT/'variables.npz',**{k:data[k] for k in data.files if k!='force_unchanged'},force_unchanged=fixed)
    receipt.update(status='FROZEN_CONSTRAINTS_ONLY',geometric_water_exclusion='native vertices within true 30m buffer plus all corners of water-intersecting native faces',previous_mask_variables_sha256=receipt['variables_sha256'],variables_sha256=sha(OUT/'variables.npz'),additional_frozen_variables=int(fixed.sum()),mask_regression_control=dict(xz=[7656,9750],water_distance_m=distance,previously_fixed=True,now_fixed=False),no_constraint_row_changes=sha(OUT/'constraints.npz')==receipt['constraints_sha256'])
    assert receipt['no_constraint_row_changes']
    (OUT/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='routes'}))


if __name__=='__main__':main()
