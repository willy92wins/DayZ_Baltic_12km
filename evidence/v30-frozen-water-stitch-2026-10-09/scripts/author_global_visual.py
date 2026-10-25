"""Extend only visible LODs on existing pond instances; retain all other LOD bytes."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import math
import shutil
import sys

import numpy as np
import shapely
from shapely.geometry import Polygon, box
from scipy.spatial import cKDTree

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B10=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
F=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
sys.path[:0]=[str(W/'tools/navigation'),str(W/'tools/terrain'),str(W/'tools/water'),str(W/'tools/playtest')]
from water_mesh import py3d,polygons
from wrp0wzd import read
from engine_water_model import ODOL
from attach_navmesh import read_pbo

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def lod_bytes(lod):
    stream=io.BytesIO();lod.write(stream);return stream.getvalue()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    gate=json.loads((B/'preserved-field-audit.json').read_text())
    assert gate['status']=='PASS_SOURCE_FIELD_ONLY' and all(gate['gates'].values())
    fieldpath=B/'preserved-field.npy';assert sha(fieldpath)==gate['source_identities'][str(fieldpath)]
    field=np.load(fieldpath)
    oldwater=Path('P:/Mods/@DayZ_Baltic_HaloFixV3/Addons/baltic_water_v30.pbo')
    assert sha(oldwater)=='4ac3cb01770dbbd825df24bd4e5869869a56188cf40acc17cb882ecb2f86539b'
    _,_,packed=read_pbo(oldwater)
    worldpath=B10/'halo-fix-v4/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    assert sha(worldpath)=='3cbad873651ab00c2122ad4d8f1e6d60471134cecc3186e95311e30cb81065e3'
    world=read(worldpath)
    objects=[o for o in world['objects'] if o['name'].startswith('baltic_water_v30')]
    pilot=json.loads((W/'evidence/v30-water-visual-fix-2026-10-08/stitch-authoring.json').read_text())
    protected={row['model'] for row in pilot['models']};assert len(protected)==538
    source=B/'compile/source/baltic_water_v30'
    source.mkdir(parents=True,exist_ok=args.resume)
    for name in ('config.cpp','$PBOPREFIX$'):
        original=F/'water/source/baltic_water_v30'/name
        if (source/name).exists():assert (source/name).read_bytes()==original.read_bytes()
        else:shutil.copyfile(original,source/name)
    ledger=B/'authoring-progress.jsonl';records=[]
    if ledger.exists():
        assert args.resume
        records=[json.loads(line) for line in ledger.read_text().splitlines()]
        for row in records:
            if row.get('new_model'):assert sha(source/row['new_model'])==row['new_sha256']
    done={row['object_id'] for row in records};cache={}
    roots=[B10/'halo-fix-v3/compile/source/baltic_water_v30',F/'water/source/baltic_water_v30']
    compiled=B10/'halo-fix-v3/water/temp/baltic_water_v30'
    for obj in objects:
        if obj['id'] in done:continue
        name=obj['name'].replace('\\','/').split('/')[-1]
        if name in protected:
            row=dict(object_id=obj['id'],old_model=name,unchanged='frozen_pilot')
        else:
            if name not in cache:
                paths=[root/name for root in roots if (root/name).exists()]
                assert paths,('No current MLOD',name)
                path=paths[0]
                assert (compiled/name).read_bytes()==packed[name],('Compiled input identity',name)
                od=ODOL.from_file(str(compiled/name));bc=od.model_info.bounding_center
                center=np.array([bc.x,bc.y,bc.z]);native=min(od.lods,key=lambda l:abs(l.resolution-1))
                vertices=np.array([(v.x,v.y,v.z) for v in native.vertices])+center
                raw=path.read_bytes();model=py3d.P3D(io.BytesIO(raw));lod=model.lods[0]
                assert abs(lod.resolution-1)<1e-6
                original=np.array([p.coords for p in lod.points])
                err=max(cKDTree(original).query(vertices)[0].max(),cKDTree(vertices).query(original)[0].max())
                assert err<2e-5,(name,'MLOD differs from compiled source',err)
                cache[name]=(raw,center,sha(path),err)
            raw,center,source_sha,source_error=cache[name]
            matrix=np.array(obj['matrix']);rot=matrix[:9].reshape(3,3);position=matrix[9:12]
            assert np.array_equal(rot,np.eye(3)),('Nonhorizontal instance',obj['id'])
            origin=position-center
            model=py3d.P3D(io.BytesIO(raw));lod=model.lods[0]
            assert len({(face.texture,face.material) for face in lod.faces})==1
            geom=shapely.union_all([Polygon([(v.point.coords[0]+origin[0],v.point.coords[2]+origin[2]) for v in f.vertices]) for f in lod.faces])
            x0,z0,x1,z1=geom.bounds
            r0=max(0,math.floor((12282-z1)/6));r1=min(2047,math.ceil((12282-z0)/6))
            c0=max(0,math.floor(x0/6));c1=min(2047,math.ceil(x1/6))
            subset=field[r0:r1,c0:c1]
            if not np.any(np.isfinite(subset)&(np.abs(subset-origin[1])>1e-5)):
                row=dict(object_id=obj['id'],old_model=name,unchanged='constant_field')
            else:
                frozen=[lod_bytes(l) for l in model.lods[1:]]
                triangles=[];unknown_area=0.0
                for r in range(r0,r1):
                    for c in range(c0,c1):
                        nw=(c*6,12282-r*6);ne=(nw[0]+6,nw[1]);sw=(nw[0],nw[1]-6);se=(ne[0],sw[1])
                        for kind,tri in enumerate((Polygon([nw,se,ne]),Polygon([nw,sw,se]))):
                            for part in polygons(geom.intersection(tri)):
                                if part.area<=1e-10:continue
                                levels=field[r,c]
                                if not np.isfinite(levels).all():
                                    unknown_area+=part.area;levels=np.full(4,origin[1])
                                for piece in shapely.constrained_delaunay_triangles(part).geoms:
                                    triangles.append((piece,r,c,kind,levels))
                exterior=geom.difference(box(0,0,12282,12282))
                for part in polygons(exterior):
                    if part.area>1e-10:
                        for piece in shapely.constrained_delaunay_triangles(part).geoms:
                            triangles.append((piece,0,0,0,np.full(4,origin[1])))
                coverage=shapely.union_all([t[0] for t in triangles])
                coverage_error=geom.symmetric_difference(coverage).area
                assert coverage_error<1e-4,(name,coverage_error)
                new=py3d.LOD();new.resolution=lod.resolution;new.properties.update(lod.properties)
                new.facenormals.append((0,-1,0));index={};maxdelta=0.0
                for tri,r,c,kind,f in triangles:
                    xy=np.asarray(tri.exterior.coords)[:3,:2];v1,v2=xy[1]-xy[0],xy[2]-xy[0]
                    if v1[0]*v2[1]-v1[1]*v2[0]<0:xy=xy[::-1]
                    face=py3d.Face(new.points,new.facenormals);face.texture=lod.faces[0].texture;face.material=lod.faces[0].material
                    for x,z in xy:
                        fc=(x-c*6)/6;fr=(12282-r*6-z)/6
                        height=f[0]+fc*(f[1]-f[0])+fr*(f[3]-f[1]) if kind==0 else f[0]+fr*(f[2]-f[0])+fc*(f[3]-f[2])
                        maxdelta=max(maxdelta,abs(height-origin[1]))
                        key=(round(x-origin[0],6),round(height-origin[1],7),round(z-origin[2],6))
                        if key not in index:
                            index[key]=len(new.points);point=py3d.Point();point.coords=key;new.points.append(point)
                        vertex=py3d.Vertex(new.points,new.facenormals);vertex.point_index=index[key];vertex.normal_index=0
                        vertex.uv=(key[0]/16,key[2]/16);face.vertices.append(vertex)
                    new.faces.append(face)
                if maxdelta<=1e-5:
                    row=dict(object_id=obj['id'],old_model=name,unchanged='constant_clipped_geometry')
                else:
                    name_new=f'globalvis_{obj["id"]}.p3d';path=source/name_new;assert not path.exists()
                    model.lods[0]=new;model.save(str(path));got=py3d.P3D(io.BytesIO(path.read_bytes()))
                    assert frozen==[lod_bytes(l) for l in got.lods[1:]],name_new
                    row=dict(object_id=obj['id'],old_model=name,new_model=name_new,old_mlod_sha256=source_sha,
                             old_compiled_sha256=sha(compiled/name),new_sha256=sha(path),source_native_error_m=float(source_error),
                             old_center=center.tolist(),old_matrix=matrix.tolist(),origin=origin.tolist(),
                             old_faces=len(lod.faces),new_faces=len(new.faces),max_all_geometry_delta_m=maxdelta,
                             footprint_error_m2=float(coverage_error),unmodeled_field_area_m2=float(unknown_area),
                             nonvisual_mlod_bytes_exact=True)
        records.append(row)
        with ledger.open('a',encoding='utf-8') as log:log.write(json.dumps(row)+'\n')
        if len(records)%250==0:print('Processed',len(records),'of',len(objects),'authored',sum('new_model' in r for r in records),flush=True)
    changed=[r for r in records if 'new_model' in r]
    report=dict(status='GLOBAL_VISUAL_AUTHORED_NOT_COMPILED',world_sha256=sha(worldpath),water_sha256=sha(oldwater),
                field_sha256=sha(fieldpath),instances=len(objects),changed_instances=len(changed),frozen_pilot=538,
                unchanged_instances=len(records)-len(changed),maximum_unmodeled_area_m2=max((r['unmodeled_field_area_m2'] for r in changed),default=0),
                models=changed,limits=['All nonvisual MLOD bytes retained; compiled physical LODs and boundary seams must still pass.',
                                      'Unmodeled 1 cm border fragments keep their previous level and require compiled visibility analysis.'])
    (B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='models'},indent=2))


if __name__=='__main__':main()
