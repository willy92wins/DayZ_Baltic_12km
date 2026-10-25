"""Repair seven supported halo failures; retire obsolete instances separately."""
from pathlib import Path
import io,json,sys,shutil
import numpy as np

B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from author_global_visual import py3d,sha,lod_bytes


def reference_cell(x,z,plane,level):
    r=int(np.clip(np.floor((12282-z)/6),0,2046));c=int(np.clip(np.floor(x/6),0,2046))
    choices=[]
    for rr in range(max(0,r-1),min(2047,r+2)):
        for cc in range(max(0,c-1),min(2047,c+2)):
            if not np.isfinite(plane[rr,cc]) or abs(plane[rr,cc]-level)>1e-4:continue
            dx=max(cc*6-x,0,x-(cc+1)*6);dz=max(12282-(rr+1)*6-z,0,z-(12282-rr*6))
            choices.append((np.hypot(dx,dz),rr,cc))
    assert choices,('No independent original-band support for halo',x,z,level)
    distance,rr,cc=min(choices)
    assert distance<=.0115,('Halo extends beyond its documented 1 cm overlap',x,z,distance)
    return rr,cc,float(distance)


def main():
    original=json.loads((B/'authoring.json').read_text())
    failures=json.loads((B/'compiled-verification.json').read_text())['failed_models']
    assert len(failures)==8 and all(r['gates']['physical'] and r['gates']['visible_field'] for r in failures)
    proof=json.loads((B/'removal-proof.json').read_text())
    assert proof['status']=='PASS_ZERO_INTENDED_COVERAGE_REMOVAL'
    removed=set(proof['removed_instance_ids'])
    failures=[r for r in failures if r['object_id'] not in removed]
    assert len(failures)==7
    source=B/'compile-r2/source/baltic_water_v30';source.mkdir(parents=True,exist_ok=True)
    for name in ('config.cpp','$PBOPREFIX$'):shutil.copy2(B/'compile/source/baltic_water_v30'/name,source/name)
    field=np.load(B/'preserved-field.npy')
    plane=np.load('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
    mapping={r['object_id']:r for r in original['models']};repairs=[]
    for failure in failures:
        row=mapping[failure['object_id']];name=row['new_model'];oldpath=B/'compile/source/baltic_water_v30'/name
        assert sha(oldpath)==row['new_sha256']
        model=py3d.P3D(io.BytesIO(oldpath.read_bytes()));lod=model.lods[0];origin=np.array(row['origin'])
        frozen=[lod_bytes(l) for l in model.lods[1:]]
        new=py3d.LOD();new.resolution=lod.resolution;new.properties.update(lod.properties);new.facenormals.append((0,-1,0))
        index={};altered=[]
        for fi,oldface in enumerate(lod.faces):
            pts=np.array([v.point.coords for v in oldface.vertices])+origin
            x,z=pts[:,0].mean(),pts[:,2].mean()
            r=int(np.clip(np.floor((12282-z)/6),0,2046));c=int(np.clip(np.floor(x/6),0,2046))
            unknown=not np.isfinite(plane[r,c]) and 0<=x<=12282 and 0<=z<=12282
            if unknown:
                rr,cc,distance=reference_cell(x,z,plane,origin[1]);f=field[rr,cc]
                for vertex in pts:
                    fc=(vertex[0]-cc*6)/6;fr=(12282-rr*6-vertex[2])/6
                    vertex[1]=f[0]+fc*(f[1]-f[0])+fr*(f[3]-f[1]) if fc>=fr else f[0]+fr*(f[2]-f[0])+fc*(f[3]-f[2])
                altered.append(dict(face=fi,source_row=rr,source_col=cc,distance_m=distance))
            face=py3d.Face(new.points,new.facenormals);face.texture=oldface.texture;face.material=oldface.material
            for pt,oldvertex in zip(pts,oldface.vertices):
                key=tuple(round(float(v),7 if i==1 else 6) for i,v in enumerate(pt-origin))
                if key not in index:
                    index[key]=len(new.points);point=py3d.Point();point.coords=key;new.points.append(point)
                vertex=py3d.Vertex(new.points,new.facenormals);vertex.point_index=index[key];vertex.normal_index=0;vertex.uv=oldvertex.uv;face.vertices.append(vertex)
            new.faces.append(face)
        assert altered,name
        model.lods[0]=new
        stream=io.BytesIO();model.write(stream);raw=stream.getvalue()
        if (source/name).exists():assert (source/name).read_bytes()==raw,'Existing repair differs; preserve it.'
        else:(source/name).write_bytes(raw)
        got=py3d.P3D(io.BytesIO((source/name).read_bytes()))
        assert frozen==[lod_bytes(l) for l in got.lods[1:]]
        repairs.append(dict(object_id=row['object_id'],model=name,before_sha256=sha(oldpath),after_sha256=sha(source/name),
                            corrected_faces=altered,nonvisual_bytes_exact=True,face_count_unchanged=len(lod.faces)==len(new.faces)))
    (B/'halo-repair.json').write_text(json.dumps(dict(status='SOURCE_HALO_REPAIR_NOT_COMPILED',repairs=repairs,
        rule='Extrapolate the adjoining original-band native triangle field over existing <=1 cm footprint only; no footprint or physical LOD edits.'),indent=2)+'\n')
    print(json.dumps({'models':len(repairs),'faces':sum(len(r['corrected_faces']) for r in repairs)}))


if __name__=='__main__':main()
