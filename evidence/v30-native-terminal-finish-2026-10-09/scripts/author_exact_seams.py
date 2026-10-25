"""Fill compiled subcell seams with symmetric, exactly placed pond pieces."""
from pathlib import Path
import hashlib,io,json,sys,shutil
import numpy as np
import shapely
from shapely.geometry import Polygon,box
from shapely.affinity import rotate

B=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009')
BASE=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(BASE))
from author_global_visual import py3d,polygons,sha,read
from audit_global_coverage import wet_shape

def main():
    source=B/'compile-seams/source/baltic_water_v30';source.mkdir(parents=True,exist_ok=True)
    assert not list(source.glob('*.p3d')),'Preserve existing authored models'
    for name in ('config.cpp','$PBOPREFIX$'):shutil.copy2(BASE/'compile/source/baltic_water_v30'/name,source/name)
    report=json.loads((B/'initial-coverage.json').read_text());assert report['status']=='FAIL_GLOBAL_COMPILED_COVERAGE'
    wp=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';stage=json.loads((B/'stage.json').read_text());assert sha(wp)==stage['world_source_sha256'] and stage['old_world_source_sha256']==report['world_source_sha256']
    nextid=max(o['id'] for o in read(wp)['objects'])+1
    h=np.load(B/'candidate/terrain.npz')['heights'].astype(float)
    p=np.load('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy');field=np.load(BASE/'preserved-field.npy')
    rows=[]
    for i,entry in enumerate(report['uncovered_cells']):
        r,c=entry['row'],entry['col'];level=float(p[r,c]);f=field[r,c]
        physical_gap=shapely.from_geojson(entry['physical_geometry']).intersection(wet_shape(r,c,h,np.full(4,level)))
        visible_gap=shapely.from_geojson(entry['visual_geometry']).intersection(wet_shape(r,c,h,f))
        gap=shapely.union_all([physical_gap,visible_gap]);assert gap.area>0
        cell=box(c*6,12276-r*6,c*6+6,12282-r*6);origin=np.array([c*6+3,level,12279-r*6])
        margin=gap.buffer(.001,join_style='mitre').intersection(cell)
        geom=shapely.union_all([margin,rotate(margin,180,origin=(origin[0],origin[2]))])
        assert geom.difference(cell).area<1e-12
        # Source coordinates are quantized symmetrically about the exact cell centre.
        def quantize(xy):return np.round(xy-origin[[0,2]],6)+origin[[0,2]]
        geom=shapely.transform(geom,quantize)
        assert gap.difference(geom).area<1e-10
        x0,z0,x1,z1=geom.bounds
        assert abs(x0+x1-2*origin[0])<1e-8 and abs(z0+z1-2*origin[2])<1e-8
        nw=(c*6,12282-r*6);ne=(c*6+6,12282-r*6);sw=(c*6,12276-r*6);se=(c*6+6,12276-r*6)
        triangles=[]
        for kind,base in enumerate((Polygon([nw,ne,se]),Polygon([nw,sw,se]))):
            for part in polygons(geom.intersection(base)):
                if part.area>1e-12:
                    for triangle in shapely.constrained_delaunay_triangles(part).geoms:triangles.append((triangle,kind))
        assert geom.symmetric_difference(shapely.union_all([q[0] for q in triangles])).area<1e-9
        model=py3d.P3D()
        for resolution in (1,1e13,1e15,3e15):
            lod=py3d.LOD();lod.resolution=resolution
            if resolution==1e13:lod.properties.update({'damage':'no','class':'pond'})
            elif resolution==1e15:
                for x,z in ((x0,z0),(x0,z1),(x1,z0),(x1,z1)):
                    point=py3d.Point();point.coords=(x-origin[0],0,z-origin[2]);lod.points.append(point)
            else:
                lod.facenormals.append((0,-1,0) if resolution==1 else (0,1,0));index={}
                if resolution==1:lod.properties['lodnoshadow']='1'
                for triangle,kind in triangles:
                    xy=np.asarray(triangle.exterior.coords)[:3]
                    v1,v2=xy[1]-xy[0],xy[2]-xy[0]
                    if v1[0]*v2[1]-v1[1]*v2[0]<0:xy=xy[::-1]
                    face=py3d.Face(lod.points,lod.facenormals)
                    face.texture=r'dz\data\data\normalmap1_dxt5.paa' if resolution==1 else r'dz\surfaces\data\roadway\water_ext.paa'
                    face.material=r'dz\water\ponds\data\pond_moss_1.rvmat' if resolution==1 else ''
                    for x,z in xy:
                        fc=(x-c*6)/6;fr=(12282-r*6-z)/6
                        water=f[0]+fc*(f[1]-f[0])+fr*(f[3]-f[1]) if kind==0 else f[0]+fr*(f[2]-f[0])+fc*(f[3]-f[2])
                        key=(round(x-origin[0],6),round(water-level,7) if resolution==1 else 0.,round(z-origin[2],6))
                        if key not in index:
                            index[key]=len(lod.points);point=py3d.Point();point.coords=key;lod.points.append(point)
                        vertex=py3d.Vertex(lod.points,lod.facenormals);vertex.point_index=index[key];vertex.normal_index=0;vertex.uv=(key[0]/16,key[2]/16);face.vertices.append(vertex)
                    lod.faces.append(face)
            model.lods.append(lod)
        name=f'terminalseam_{r:04}_{c:04}.p3d';model.save(str(source/name));reread=py3d.P3D(io.BytesIO((source/name).read_bytes()))
        assert [len(l.faces) for l in reread.lods]==[len(triangles),0,0,len(triangles)]
        rows.append(dict(object_id=nextid+i,model=name,row=r,col=c,origin=origin.tolist(),sha256=sha(source/name),
                         physical_gap_m2=physical_gap.area,visible_gap_m2=visible_gap.area,footprint_m2=geom.area,
                         geometry=shapely.to_geojson(geom),gap_geometry=shapely.to_geojson(gap),faces=len(triangles)))
    out=dict(status='SYMMETRIC_SEAM_PIECES_AUTHORED_NOT_COMPILED',models=len(rows),rows=rows,
             audit_sha256=sha(B/'initial-coverage.json'),field_sha256=sha(BASE/'preserved-field.npy'),
             maximum_overlap_margin_m=.001,total_raw_footprint_m2=sum(r['footprint_m2'] for r in rows),
             rationale='Same native cell and water level; symmetric geometry gives exact XZ centre without external memory bounds.')
    (B/'seam-authoring.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
