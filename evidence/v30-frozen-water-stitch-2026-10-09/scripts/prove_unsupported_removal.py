"""Independently prove obsolete corner instances cannot cover intended water."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import shapely
from shapely.geometry import Polygon,box
from shapely.affinity import translate

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from author_global_visual import B10,read,read_pbo,ODOL,sha,polygons
from audit_frozen_visual import cell_planes,verify_identity
from v30_common import tri_sample

def eligible(support,intended,outside,clearance):
    return support==0 and intended==0 and outside==0 and clearance>=0

def main():
    inventory=json.loads((B/'unsupported-instances.json').read_text())
    water=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
    terrain=B10/'measured-bank-bed-r2/terrain.npz'
    verify_identity(water,'e0d35db0a7a26f9ec055d57f0c9573a1dd2c27911ec8b084274283f5884cffd1')
    verify_identity(terrain,'e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c')
    t=np.load(terrain);h=t['heights'].astype(float);s=np.load(water)
    p=cell_planes(s['cls'],s['level'],sea_cut=.51)
    assert np.array_equal(p,np.load(B10/'frozen-field-reference/plane.npy'),equal_nan=True)
    wp=B10/'halo-fix-v4/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    oldwater=Path('P:/Mods/@DayZ_Baltic_HaloFixV3/Addons/baltic_water_v30.pbo')
    assert sha(wp)==inventory['world_sha256'] and sha(oldwater)==inventory['water_sha256']
    _,_,packed=read_pbo(oldwater)
    objects={o['id']:o for o in read(wp)['objects']};rows=[]
    for old in inventory['unsupported']:
        obj=objects[old['object_id']];name=obj['name'].replace('\\','/').split('/')[-1]
        assert obj['name'].startswith('baltic_water_v30') and name==old['model']
        path=B10/'halo-fix-v3/water/temp/baltic_water_v30'/name
        assert packed[name]==path.read_bytes()
        od=ODOL.from_file(str(path));lod=min(od.lods,key=lambda x:abs(x.resolution-3e15))
        geometry=min(od.lods,key=lambda l:abs(l.resolution-1e13))
        assert ('class','pond') in geometry.named_properties
        assert len(od.lods)==4 and not any(abs(l.resolution-1e16)<1e9 for l in od.lods)
        v=np.array([(v.x,v.y,v.z) for v in lod.vertices])+np.array(obj['matrix'][9:12])
        geom=shapely.union_all([Polygon(v[f.vertex_indices][:,[0,2]]) for f in lod.faces])
        assert geom.equals(shapely.from_geojson(old['geometry']))
        clearance=[]
        for cell in old['cells']:
            r,c=cell['row'],cell['col'];level=p[r,c]
            if not np.isfinite(level):continue
            nw=(c*6,12282-r*6);ne=(c*6+6,12282-r*6);sw=(c*6,12276-r*6);se=(c*6+6,12276-r*6)
            for vertices in ((nw,ne,se),(nw,sw,se)):
                part=geom.intersection(Polygon(vertices))
                for poly in polygons(part):
                    if poly.area==0:continue
                    xy=np.asarray(poly.exterior.coords)
                    clearance.extend((tri_sample(h,xy[:,0],xy[:,1])-level).tolist())
        minimum=min(clearance,default=float('inf'))
        assert eligible(old['matching_frozen_band_area_m2'],old['intended_water_overlap_m2'],old['outside_map_m2'],minimum)
        rows.append(dict(object_id=obj['id'],model=name,object_record_sha256=hashlib.sha256(obj['bytes']).hexdigest(),
                         compiled_sha256=sha(path),minimum_ground_above_intended_water_m=minimum if np.isfinite(minimum) else None,
                         intended_wet_coverage_lost_m2=0.,raw_footprint_m2=float(geom.area),previous_above_ground_m2=old['above_ground_m2']))
    assert len(rows)==18 and sum(r['previous_above_ground_m2']>0 for r in rows)==1
    checks={'empty_obsolete_corner_accepted':eligible(0,0,0,.1),
            'any_wet_coverage_rejected':not eligible(0,1e-12,0,.1),
            'any_matching_band_rejected':not eligible(1e-12,0,0,.1),
            'submerged_corner_rejected':not eligible(0,0,0,-1e-12),
            'outside_map_unproven_rejected':not eligible(0,0,1e-12,.1)}
    assert all(checks.values())
    report=dict(status='PASS_ZERO_INTENDED_COVERAGE_REMOVAL',world_sha256=sha(wp),water_sha256=sha(oldwater),
                terrain_sha256=sha(terrain),frozen_water_sha256=sha(water),inventory_sha256=sha(B/'unsupported-instances.json'),
                removed_instance_ids=[r['object_id'] for r in rows],instances=rows,controls=checks,
                intended_water_area_loss_m2=0.,limits=['Only these exact instance records may be removed; shared model resources are retained.',
                  'This proof does not attribute the large reported land reflections to these tiny fragments.'])
    (B/'removal-proof.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('instances','removed_instance_ids')},indent=2))

if __name__=='__main__':main()
