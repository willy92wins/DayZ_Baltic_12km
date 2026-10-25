"""Author horizontal pond geometry using only installed vanilla material paths.

Coordinates are baked at scale one. Never copy/edit installed ODOL geometry.
DayZ py3d Face supports three vertices (__init__.py:1438,1453).
"""
from pathlib import Path
import math,sys
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import box
from shapely.ops import unary_union
sys.path.insert(0,r'C:\Users\guill\DayZ-Modding-Knowledge-Pack\tools\py3d')
import py3d
assert py3d.IS_DAYZ_FORK

def polygons(g):
    if g.geom_type=='Polygon':yield g
    elif hasattr(g,'geoms'):
        for part in g.geoms:yield from polygons(part)

def write_water_mesh(geometry,path,origin,spacing=16,uv_local=False):
    triangles=[]
    x0,z0,x1,z1=geometry.bounds
    for x in range(math.floor(x0/spacing)*spacing,math.ceil(x1/spacing)*spacing,spacing):
        for z in range(math.floor(z0/spacing)*spacing,math.ceil(z1/spacing)*spacing,spacing):
            for p in polygons(geometry.intersection(box(x,z,x+spacing,z+spacing))):
                if p.area<1e-7:continue
                triangles.extend(constrained_delaunay_triangles(p).geoms)
    coverage=unary_union(triangles)
    error=geometry.symmetric_difference(coverage).area
    assert error<1e-4,(error,geometry.area)
    faces=[]
    for t in triangles:
        p=np.asarray(t.exterior.coords)[:3,:2]
        cross=(p[1,0]-p[0,0])*(p[2,1]-p[0,1])-(p[1,1]-p[0,1])*(p[2,0]-p[0,0])
        if cross<0:p=p[::-1]
        faces.append(p)
    model=py3d.P3D()
    for resolution in (1,1e13,1e15,3e15):
        lod=py3d.LOD();lod.resolution=resolution
        if resolution==1e13:lod.properties.update({'damage':'no','class':'pond'})
        elif resolution==1e15:
            for x,z in [(x0,z0),(x1,z0),(x0,z1),(x1,z1)]:
                p=py3d.Point();p.coords=(x-origin[0],0,z-origin[1]);lod.points.append(p)
        else:
            lod.facenormals.append((0,-1,0) if resolution==1 else (0,1,0))
            if resolution==1:lod.properties['lodnoshadow']='1'
            indexed={}
            for points in faces:
                face=py3d.Face(lod.points,lod.facenormals)
                face.texture=r'dz\data\data\normalmap1_dxt5.paa' if resolution==1 else r'dz\surfaces\data\roadway\water_ext.paa'
                face.material=r'dz\water\ponds\data\pond_moss_1.rvmat' if resolution==1 else ''
                for x,z in points:
                    key=(round(x-origin[0],6),round(z-origin[1],6))
                    if key not in indexed:
                        indexed[key]=len(lod.points)
                        point=py3d.Point();point.coords=(key[0],0,key[1]);lod.points.append(point)
                    v=py3d.Vertex(lod.points,lod.facenormals)
                    v.point_index=indexed[key];v.normal_index=0
                    v.uv=(key[0]/16,key[1]/16) if uv_local else (x/25,z/25)
                    face.vertices.append(v)
                lod.faces.append(face)
        model.lods.append(lod)
    model.save(str(path))
    with Path(path).open('rb') as handle:reread=py3d.P3D(handle)
    assert [len(l.faces) for l in reread.lods]==[len(faces),0,0,len(faces)]
    return {'triangles':len(faces),'points':len(model.lods[0].points),'area_m2':geometry.area,'coverage_error_m2':error}
