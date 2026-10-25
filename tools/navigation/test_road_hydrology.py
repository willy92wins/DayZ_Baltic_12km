"""Reject water-plane, island and reserve damage against a real accepted ASC."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import rasterio
from shapely.geometry import shape
from verify_road_hydrology import audit,ROOT,EV

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--positive',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
    receipt=json.loads(a.positive.read_text(encoding='utf-8'));asc=next(a.folder.glob('*.asc'));sha=hashlib.sha256(asc.read_bytes()).hexdigest()
    assert receipt['status']=='PASS_OFFLINE_HYDROLOGY_AND_PROTECTED_LAND' and sha==receipt['asc_sha256']
    with rasterio.open(asc) as ds:h=ds.read(1)
    water=shape(json.loads((EV/'water-surfaces-contour-v2.geojson').read_text(encoding='utf-8'))['features'][0]['geometry']).representative_point()
    island=shape(json.loads((EV/'protected-islands-game.json').read_text(encoding='utf-8'))['features'][0]['geometry']).representative_point()
    reserve=np.load(ROOT/'tests/regional_outline_v3/reference.npz')['reserve'];parent=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');rr,cc=np.nonzero(reserve&~(parent['wet']|parent['ocean']))
    tests=[('changed_water_plane',int((12282-water.y)//6),int(water.x//6),.25,'water_native_cells_exact'),('island_sunk',int((12282-island.y)//6),int(island.x//6),-100.,'protected_land_planes'),('reserve_sunk',int(rr[len(rr)//2]),int(cc[len(cc)//2]),-100.,'reserve_dry_classification_preserved')]
    records=[]
    for name,row,col,delta,key in tests:
        changed=h.copy();changed[row:row+2,col:col+2]+=delta;r=audit(a.folder,changed,outline_v33_parent=receipt.get('outline_v33_parent',False))
        assert r['status'].startswith('FAIL_') and not r['checks'][key],(name,r['checks'])
        records.append(dict(name=name,status='EXPECTED_REJECTION',target_check=key));print(json.dumps(records[-1]),flush=True)
    result=dict(status='PASS_REAL_HYDROLOGY_AND_THREE_NEGATIVES',asc_sha256=sha,positive_sha256=hashlib.sha256(a.positive.read_bytes()).hexdigest(),controls=records)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
