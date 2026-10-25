"""Inspect actual written model faces and packed bytes before native placement."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
from shapely import STRtree
from shapely.geometry import Polygon
from shapely.affinity import translate
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
sys.path.insert(0,str(ROOT/'tools/playtest'))
sys.path.insert(0,r'C:\Users\guill\.agents\skills\dayz-p3d-debinarizer\scripts')
sys.path.insert(0,r'C:\Users\guill\DayZ-Modding-Knowledge-Pack\tools\py3d')
from attach_navmesh import read_pbo
from odol_reader import ODOL
import py3d

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--version',choices=['v1','v2'],default='v1')
    version=parser.parse_args().version
    meta=json.loads((EV/f'regional-water-assets-{version}.json').read_text())
    raw,props,entries=read_pbo(ROOT/f'build-output/regional_water_assets_{version}/baltic_water.pbo')
    assert props['prefix']=='baltic_water'
    assert set(entries)=={'config.bin'}|{m['name']+'.p3d' for m in meta['models']}
    assert entries['config.bin'].startswith(b'\0raP')
    footprints={};centres={};model_report=[]
    source=ROOT/f'tests/regional_foundation_water_assets_{version}/source/baltic_water'
    for i,model in enumerate(meta['models']):
        name=model['name'];p=source/f'{name}.p3d';b=p.read_bytes()
        assert hashlib.sha256(b).hexdigest()==model['sha256']
        assert entries[name+'.p3d']==(ROOT/f'build-temp/regional_water_assets_{version}/baltic_water/{name}.p3d').read_bytes()
        with p.open('rb') as handle:m=py3d.P3D(handle)
        road=next(l for l in m.lods if l.resolution==float(np.float32(3e15)))
        assert all(abs(point.coords[1])<1e-7 for point in road.points)
        polys=[]
        for face in road.faces:
            assert face.texture==r'dz\surfaces\data\roadway\water_ext.paa'
            positions=[road.points[v.point_index].coords for v in face.vertices]
            polys.append(Polygon([(p[0],p[2]) for p in positions]))
        g=unary_union(polys);assert g.is_valid
        footprints[name]=g
        odol=ODOL.from_bytes(entries[name+'.p3d']);assert odol.version==55 and not odol.lod_errors
        c=odol.model_info.bounding_center;centres[name]=[c.x,c.y,c.z]
        model_report.append({'name':name,'compiled_sha256':hashlib.sha256(entries[name+'.p3d']).hexdigest(),
                             'bounding_center':centres[name],'roadway_area_m2':g.area})
        if i%500==0:print(f'Inspected {i}/{len(meta["models"])} models',flush=True)
    objects=[];geometries=[];levels=[];csv=[]
    for pose in meta['instances']:
        name=Path(pose['model'].replace('\\','/')).stem
        pos=pose['position'];centre=centres[name]
        native=[float(a+b) for a,b in zip(pos,centre)]
        g=translate(footprints[name],xoff=pos[0],yoff=pos[2])
        assert abs(g.area-pose['area_m2'])<.02
        geometries.append(g);levels.append(pos[1]);objects.append(dict(pose,native_position=native,bounding_center=centre))
        csv.append(f'"{name}";{native[0]+200000:.9f};{native[2]:.9f};0;0;0;1;{native[1]:.9f};')
    tree=STRtree(geometries);pairs=tree.query(geometries,predicate='intersects')
    select=pairs[0]<pairs[1];a=pairs[0][select];b=pairs[1][select]
    delta=abs(np.asarray(levels)[a]-np.asarray(levels)[b]);bad=[]
    for j in np.flatnonzero(delta>.05001):
        ia,ib=int(a[j]),int(b[j]);overlap=geometries[ia].intersection(geometries[ib])
        if overlap.area>1e-5 or overlap.length>.02:
            bad.append({'a':ia,'b':ib,'height_difference_m':float(delta[j]),'overlap_area_m2':overlap.area,
                        'bounds_xz':list(overlap.bounds),'body_a':objects[ia]['body'],'body_b':objects[ib]['body']})
    report={'status':'PASS_OFFLINE_MODELS_AND_PLACEMENT' if not bad else 'FAIL_WATER_JOINT_HEIGHT',
            'pbo_sha256':hashlib.sha256(raw).hexdigest(),'pbo_bytes':len(raw),'instances':len(objects),'models':len(model_report),
            'adjacent_pairs':len(a),'max_pair_difference_m':float(delta.max()),'bad_joints':bad,
            'models_compiled':model_report,'native_objects':objects,
            'limits':['Native editor import and in-game regional consumers remain required.']}
    (EV/f'regional-water-assets-verification-{version}.json').write_text(json.dumps(report,indent=2)+'\n')
    out=ROOT/f'tests/regional_foundation_water_assets_{version}/water_objects_absolute.txt'
    out.write_text('\n'.join(csv)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('models_compiled','native_objects','bad_joints')},indent=2))
    print(json.dumps({'bad_joints':len(bad),'examples':bad[:8]},indent=2))
    raise SystemExit(0 if not bad else 1)

if __name__=='__main__':main()
