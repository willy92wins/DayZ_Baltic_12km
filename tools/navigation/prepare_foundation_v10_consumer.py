"""V5 keeps every V4 sample and threshold, binding expected heights to frozen V10."""
from pathlib import Path
import csv,hashlib,json
import numpy as np
import rasterio
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/regional-foundation-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parent=EV/'consumer-reference-v4.json'
    assert sha(parent)=='44f798527c4f6c04e95267ba17df75eae58ae9b8cceede8fad26715d601457cf'
    ref=json.loads(parent.read_text())
    old=ROOT/'missions/BalticFoundationConsumerV4.BalticTrial'
    dest=ROOT/'missions/BalticFoundationConsumerV5.BalticTrial'
    manifest=EV/'consumer-reference-v5.json'
    navdest=EV/'foundation-nav-reference-v5.json'
    assert not any(p.exists() for p in (dest,manifest,navdest))
    paths={'water_file':old/'water-points.csv','nav_file':old/'nav-points.csv',
           'mission':old/'init.c','nav_reference':EV/'foundation-nav-reference-v4.json'}
    for key,path in paths.items():assert sha(path)==ref[key+'_sha256'],key
    asc=ROOT/'tests/regional_foundation_combined_v10/baltic_regional_foundation_v10.asc'
    assert sha(asc)=='8e25fab25e8f0909fdda302ed4ba3db4c43884c523920f5ef3424db90780eb8b'
    with rasterio.open(asc) as ds:h=ds.read(1)
    rows=list(csv.reader(paths['water_file'].read_text().splitlines(),delimiter=';'))
    coords=np.array([[float(v) for v in r[2].split()] for r in rows],dtype='float32').astype(float)
    ground=sample(h,coords[:,0]+200000,coords[:,2])
    changed=0
    for row,bottom in zip(rows,ground):
        value=f'{bottom:.9g}'
        changed+=row[3]!=value
        row[3]=value
        if row[0]=='W':assert float(row[4])-bottom>=float(row[5])-.000001
        else:assert bottom>=1.25
    nav=json.loads(paths['nav_reference'].read_text())
    for point in nav['points']:point['y']=float(sample(h,point['x']+200000,point['z']))
    for route in nav['routes']:
        for name in ('start','end'):
            v=route[name];v[1]=float(sample(h,v[0]+200000,v[2]))
    nav['header']='BALTIC_FOUNDATION_NAV_V5'
    navrows=list(csv.reader(paths['nav_file'].read_text().splitlines(),delimiter=';'))
    routes={r['name']:r for r in nav['routes']}
    for row in navrows:
        if row[0]=='Q' and row[1]!='negative':
            route=routes[row[1]]
            row[2]=' '.join(map(str,route['start']));row[3]=' '.join(map(str,route['end']))
    dest.mkdir()
    for filename,content in [('water-points.csv',rows),('nav-points.csv',navrows)]:
        with (dest/filename).open('w',newline='',encoding='utf-8') as f:
            csv.writer(f,delimiter=';',lineterminator='\n').writerows(content)
    (dest/'init.c').write_text(paths['mission'].read_text().replace('_V4','_V5').replace('_v4.log','_v5.log'))
    navdest.write_text(json.dumps(nav,indent=2)+'\n')
    ref.update(asc_sha256=sha(asc),terrain_version='v10',probe_version='v5',
               parent_reference_sha256=sha(parent),query_coordinates_unchanged=True,
               height_fields_changed=changed,
               water_file_sha256=sha(dest/'water-points.csv'),nav_file_sha256=sha(dest/'nav-points.csv'),
               nav_reference_sha256=sha(navdest),mission_sha256=sha(dest/'init.c'))
    manifest.write_text(json.dumps(ref,indent=2)+'\n')
    print(json.dumps(dict(status='FROZEN_BEFORE_ENGINE',manifest_sha256=sha(manifest),
                         unchanged_sample_count=len(rows),height_fields_changed=changed),indent=2))

if __name__=='__main__':main()
