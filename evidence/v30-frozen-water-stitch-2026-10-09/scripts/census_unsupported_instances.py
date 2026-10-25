"""Find every compiled pond instance with zero support in its frozen level cells."""
from pathlib import Path
import json,sys,time
import numpy as np
import shapely
from shapely.geometry import Polygon,box
from shapely.affinity import translate

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from author_global_visual import W,B10,sha,ODOL,read,read_pbo
from audit_frozen_visual import clip,UNIT


def submerged_polygon(r,c,kind,heights,water):
    xy=np.array([[c*6,12282-r*6],[(c+1)*6,12282-r*6],[(c+1)*6,12276-r*6]]) if kind==0 else np.array([[c*6,12282-r*6],[c*6,12276-r*6],[(c+1)*6,12276-r*6]])
    corners=[heights[r,c],heights[r,c+1] if kind==0 else heights[r+1,c],heights[r+1,c+1]]
    weights=clip(UNIT,water-np.array(corners))
    return Polygon(weights@xy) if len(weights)>=3 else Polygon()


def main():
    start=time.monotonic()
    water=Path('P:/Mods/@DayZ_Baltic_HaloFixV3/Addons/baltic_water_v30.pbo')
    assert sha(water)=='4ac3cb01770dbbd825df24bd4e5869869a56188cf40acc17cb882ecb2f86539b'
    _,_,packed=read_pbo(water)
    wp=B10/'halo-fix-v4/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(wp)=='3cbad873651ab00c2122ad4d8f1e6d60471134cecc3186e95311e30cb81065e3'
    objects=[o for o in read(wp)['objects'] if o['name'].startswith('baltic_water_v30')]
    plane=np.load(B10/'frozen-field-reference/plane.npy')
    t=np.load(B10/'measured-bank-bed-r2/terrain.npz');h=t['heights'].astype(float)
    cached=json.loads((B10/'compiled-model-domains.json').read_text());models={};unsupported=[]
    full=box(0,0,12282,12282)
    for n,obj in enumerate(objects):
        name=obj['name'].replace('\\','/').split('/')[-1];path=B10/'halo-fix-v3/water/temp/baltic_water_v30'/name
        if name not in models:
            assert path.read_bytes()==packed[name]
            entry=cached.get(name)
            if entry and entry['sha256']==sha(path):
                models[name]=(shapely.from_wkb(entry['wkb']),entry['y'])
            else:
                od=ODOL.from_file(str(path));lod=min(od.lods,key=lambda l:abs(l.resolution-3e15))
                v=np.array([(v.x,v.y,v.z) for v in lod.vertices]);assert np.ptp(v[:,1])<1e-6
                models[name]=(shapely.union_all([Polygon(v[f.vertex_indices][:,[0,2]]) for f in lod.faces]),float(v[0,1]))
        local,y=models[name];mat=np.array(obj['matrix']);assert np.array_equal(mat[:9].reshape(3,3),np.eye(3))
        geom=translate(local,xoff=mat[9],yoff=mat[11]);level=y+mat[10]
        x0,z0,x1,z1=geom.bounds
        cs=np.arange(max(0,int(np.floor(x0/6))),min(2046,int(np.floor(x1/6)))+1)
        rs=np.arange(max(0,int(np.floor((12282-z1)/6))),min(2046,int(np.floor((12282-z0)/6)))+1)
        cc,rr=np.meshgrid(cs,rs);cc,rr=cc.ravel(),rr.ravel()
        own=np.abs(plane[rr,cc]-level)<1e-5
        supported=float(shapely.area(shapely.intersection(geom,shapely.box(cc[own]*6,12276-rr[own]*6,cc[own]*6+6,12282-rr[own]*6))).sum())
        if supported==0:
            visible=0.;dry_visible=0.;expected=0.;parts=[]
            for r,c in zip(rr,cc):
                cell=geom.intersection(box(c*6,12276-r*6,c*6+6,12282-r*6))
                if cell.area==0:continue
                for kind in (0,1):
                    wet=cell.intersection(submerged_polygon(r,c,kind,h,level));visible+=wet.area
                    classes=[t['cls'][r,c],t['cls'][r,c+1] if kind==0 else t['cls'][r+1,c],t['cls'][r+1,c+1]]
                    if all(x==0 for x in classes):dry_visible+=wet.area
                    if np.isfinite(plane[r,c]):expected+=cell.intersection(submerged_polygon(r,c,kind,h,plane[r,c])).area
                parts.append(dict(row=int(r),col=int(c),expected_plane=float(plane[r,c]) if np.isfinite(plane[r,c]) else None,area_m2=float(cell.area)))
            unsupported.append(dict(object_id=obj['id'],model=name,level_m=float(level),area_m2=float(geom.area),
                matching_frozen_band_area_m2=supported,above_ground_m2=float(visible),above_fully_dry_faces_m2=float(dry_visible),
                intended_water_overlap_m2=float(expected),outside_map_m2=float(geom.difference(full).area),
                geometry=shapely.to_geojson(geom),cells=parts))
        if (n+1)%4000==0:print('Censused',n+1,'unsupported',len(unsupported),flush=True)
    report=dict(status='COMPILED_UNSUPPORTED_INVENTORY_NOT_REMOVAL_APPROVAL',instances=len(objects),models=len(models),
                unsupported=unsupported,unsupported_count=len(unsupported),water_sha256=sha(water),world_sha256=sha(wp),
                elapsed_s=time.monotonic()-start,limits=['Zero source-band support does not alone authorize removal: intended wet coverage and overlap with retained compiled models still need verification.'])
    (B/'unsupported-instances.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='unsupported'},indent=2))


if __name__=='__main__':main()
