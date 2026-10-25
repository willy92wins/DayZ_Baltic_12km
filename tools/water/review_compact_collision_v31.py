"""Independent saved-MLOD closure, convexity and full planar-overlay consumer."""
if not __debug__:
    raise RuntimeError('Validation requires assertions enabled; do not use python -O')
import argparse,hashlib,io,json,sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.strtree import STRtree
sys.path[:0]=[str(Path(__file__).resolve().parent),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
import py3d
from mesh_quality_v31 import closed_component
from collision_contact_union_v31 import lower_coverage,coverage_certificate


def load(path):
    data=Path(path).read_bytes();f=io.BytesIO(data);header=f.read(12);lods=[];blobs=[]
    for _ in range(4):
        start=f.tell();lods.append(py3d.LOD(f));blobs.append(data[start:f.tell()])
    if f.tell()!=len(data):raise ValueError('unexpected model trailer')
    return header,lods,blobs


def vertices(lod,faces):
    return np.array([[lod.points[v.point_index].coords for v in face.vertices] for face in faces])


def height(tri,xy):
    # Barycentric interpolation, independent of the author's plane equations.
    a=tri[:,0][:,[0,2]];b=tri[:,1][:,[0,2]]-a;c=tri[:,2][:,[0,2]]-a;q=xy-a
    cross=lambda u,v:u[:,0]*v[:,1]-u[:,1]*v[:,0]
    det=cross(b,c);u=cross(q,c)/det;v=cross(b,q)/det
    return tri[:,0,1]+u*(tri[:,1,1]-tri[:,0,1])+v*(tri[:,2,1]-tri[:,0,1])


def overlay(source,roof,vertical_limit=.02,horizontal_limit=.01):
    source=np.asarray(source,float);roof=np.asarray(roof,float)
    for triangles in (source,roof):
        if triangles.ndim!=3 or triangles.shape[1:]!=(3,3) or not len(triangles) or not np.isfinite(triangles).all():
            raise ValueError('finite nonempty triangles required')
    if not np.isfinite([vertical_limit,horizontal_limit]).all() or min(vertical_limit,horizontal_limit)<0:
        raise ValueError('finite nonnegative contact tolerances required')
    a=np.array([Polygon(t[:,[0,2]]) for t in source]);b=np.array([Polygon(t[:,[0,2]]) for t in roof])
    if any(not p.is_valid or p.area<=0 for p in (*a,*b)):raise ValueError('invalid projected triangle')
    tree=STRtree(a);minimum=np.inf;maximum=-np.inf;pairs=0;points=0
    regions=[[] for _ in a];extrema={}
    for start in range(0,len(b),512):
        bi,ai=tree.query(b[start:start+512],predicate='intersects');bi=bi+start
        intersection=shapely.intersection(b[bi],a[ai]);xy,which=shapely.get_coordinates(intersection,return_index=True)
        if len(xy):
            roof_y=height(roof[bi[which]],xy);source_y=height(source[ai[which]],xy);error=roof_y-source_y
            for key,index,improves in (('minimum_pair',int(error.argmin()),error.min()<minimum),('maximum',int(error.argmax()),error.max()>maximum)):
                if improves:extrema[key]=dict(source_triangle=int(ai[which[index]]),roof_triangle=int(bi[which[index]]),xz=xy[index].tolist(),source_y=float(source_y[index]),roof_y=float(roof_y[index]),error_m=float(error[index]))
            minimum=min(minimum,float(error.min()));maximum=max(maximum,float(error.max()))
        lower_coverage(a,roof,source,bi,ai,intersection,height,-vertical_limit-1e-7,regions)
        pairs+=len(ai);points+=len(xy)
    lower=coverage_certificate(a,regions)
    original=shapely.union_all(a);candidate=shapely.union_all(b)
    missing=float(original.difference(candidate.buffer(1e-7)).area)
    excessive=float(candidate.difference(original.buffer(horizontal_limit+1e-7)).area)
    checks=dict(nonempty_overlay=bool(points),full_source_covered=missing<=1e-6,
                no_excessive_horizontal_extension=excessive<=1e-6,
                vertical_contact_error=lower['covered'] and maximum<=vertical_limit+1e-7)
    return dict(checks=checks,source_triangles=len(source),roof_triangles=len(roof),overlay_pairs=pairs,refinement_vertices=points,
                minimum_pair_height_error_m=minimum,maximum_height_error_m=maximum,lower_contact_coverage=lower,extrema=extrema,missing_area_m2=missing,
                excessive_horizontal_area_m2=excessive,vertical_limit_m=vertical_limit,horizontal_limit_m=horizontal_limit)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('original',type=Path);p.add_argument('candidate',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    if a.report.exists():raise FileExistsError(a.report)
    old=json.loads((a.original/'author-report.json').read_text());new=json.loads((a.candidate/'author-report.json').read_text())
    before={i['model']:i for i in old['instances']};after={i['model']:i for i in new['instances']};assert len(before)==len(old['instances']) and set(before)==set(after) and len(after)==len(new['instances'])
    all_source=[];all_roof=[];source_labels=[];roof_labels=[];checks={};models=[]
    for name in before:
        source=a.original/'source'/name.replace('\\','/');candidate=a.candidate/'source'/name.replace('\\','/')
        assert hashlib.sha256(source.read_bytes()).hexdigest()==before[name]['sha256']
        assert hashlib.sha256(candidate.read_bytes()).hexdigest()==after[name]['sha256']
        assert before[name]['origin']==after[name]['origin'];origin=np.array(before[name]['origin'])
        oh,ol,ob=load(source);nh,nl,nb=load(candidate);assert oh==nh and all(ob[i]==nb[i] for i in (0,2,3))
        bed=vertices(ol[0],[f for f in ol[0].faces if 'water_streambed.rvmat' not in f.material])+origin
        geo=nl[1];invalid=0;nonconvex=0;assigned=[]
        face_components={}
        for component,selection in geo.selections.items():
            faces=list(selection.faces);tri=vertices(geo,faces);closure=closed_component(tri)
            face_components.update((id(face),component) for face in faces)
            invalid+=not closure['closed'] or closure['signed_volume']>=0
            normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None]
            pts=np.unique(tri.reshape(-1,3),axis=0)
            # All other vertices must lie on the inward side of every face.
            distances=np.einsum('fpc,fc->fp',pts[None]-tri[:,0,None],normal)
            nonconvex+=bool(distances.min()<-1e-6);assigned.extend(id(face) for face in faces)
        assert len(assigned)==len(set(assigned))==len(geo.faces) and set(assigned)=={id(face) for face in geo.faces}
        triangles=vertices(geo,geo.faces)+origin;normal=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);roof=triangles[normal[:,1]<-1e-10]
        checks[name]=not invalid and not nonconvex and len(geo.selections)==after[name]['collision_components']
        models.append(dict(model=name,components=len(geo.selections),invalid_components=int(invalid),nonconvex_components=int(nonconvex),non_geometry_lods_byte_exact=True))
        source_labels.extend(dict(model=name,local_bed_triangle=i) for i in range(len(bed)))
        roof_labels.extend(dict(model=name,component=face_components[id(geo.faces[i])],local_geometry_triangle=int(i)) for i in np.flatnonzero(normal[:,1]<-1e-10))
        all_source.extend(bed);all_roof.extend(roof)
    source=np.asarray(all_source);contact=overlay(source,np.asarray(all_roof))
    for item in contact['extrema'].values():
        item['source']=source_labels[item['source_triangle']];item['roof']=roof_labels[item['roof_triangle']]
    self_contact=overlay(source,source,vertical_limit=1e-6,horizontal_limit=0.)
    checks['source_single_valued']=max(abs(self_contact['minimum_pair_height_error_m']),abs(self_contact['maximum_height_error_m']))<=1e-6 and all(self_contact['checks'].values())
    passed=all(checks.values()) and all(contact['checks'].values())
    result=dict(status='SAVED_COLLISION_PASS' if passed else 'FAIL',models=models,contact=contact,
                source_single_valued=checks['source_single_valued'],source_self_overlay=self_contact,
                reviewer_sources={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (Path(__file__),Path(__file__).with_name('collision_contact_union_v31.py'),Path(py3d.__file__))},
                py3d_dependency_sources={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(Path(py3d.__file__).parent.rglob('*.py'))},
                source_author_sha256=hashlib.sha256((a.original/'author-report.json').read_bytes()).hexdigest(),candidate_author_sha256=hashlib.sha256((a.candidate/'author-report.json').read_bytes()).hexdigest(),
                scope='Exact planar refinement of saved MLOD surfaces, closure and convexity. Binary/engine/performance acceptance remain separate.')
    a.report.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2));sys.exit(0 if passed else 1)


if __name__=='__main__':main()
