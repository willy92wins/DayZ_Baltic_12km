"""Reproduce the corrected reference from frozen water, never terrain reclassification."""
from pathlib import Path
import hashlib,json,sys
import numpy as np

B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
OUT=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from derive_connected_visual_field import make_field
from v30_common import cell_planes
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    terrain=B/'measured-bank-bed-r2/terrain.npz'
    water=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
    assert sha(terrain)=='e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c'
    assert sha(water)=='e0d35db0a7a26f9ec055d57f0c9573a1dd2c27911ec8b084274283f5884cffd1'
    h=np.load(terrain)['heights'].astype(float);t=np.load(water);plane=cell_planes(t['cls'],t['level'],sea_cut=.51)
    field=make_field(h,plane);destination=B/'frozen-field-reference';destination.mkdir(exist_ok=True)
    for name,value in [('plane.npy',plane),('field.npy',field)]:
        path=destination/name
        if path.exists():assert np.array_equal(np.load(path),value,equal_nan=True)
        else:np.save(path,value)
    assert sha(destination/'field.npy')=='cc2554e100606772ba60ed1bc6b78aab6d9ff9ede9e057d22cdaee2c6843d03f'
    report=dict(status='PASS_FROZEN_REFERENCE_REPRODUCTION',terrain_sha256=sha(terrain),water_sha256=sha(water),
                field_sha256=sha(destination/'field.npy'),plane_sha256=sha(destination/'plane.npy'),
                rule='Ground from current terrain; classes and levels exclusively from the frozen water source; cutoff 0.51 m.')
    (OUT/'frozen-reference-reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
