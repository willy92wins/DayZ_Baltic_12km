"""Candidate convex packing of a saved stream bed; visual/water LODs stay exact.

Local sufficient upper-surface bound: for each source triangle, choose a hull
roof plane whose error at all three vertices is <= the budget. The hull roof
is the minimum of these planes, so this bounds the whole triangle, not just
samples. A separate full-mesh overlay must check interactions between pieces.
This module does not accept runtime collision or map-wide performance.
"""
if not __debug__:
    raise RuntimeError('Authoring requires assertions enabled; do not use python -O')
import numpy as np
from scipy.spatial import ConvexHull, QhullError
from shapely.geometry import Polygon, MultiPoint
from shapely.strtree import STRtree
import shapely


def triangles(n,m):
    return np.array([(a,b,c) for i in range(n-1) for j in range(m-1)
                     for a,b,c in ((i*m+j,(i+1)*m+j,(i+1)*m+j+1),(i*m+j,(i+1)*m+j+1,i*m+j+1))],int)


def hull_for(top):
    top=np.asarray(top,float);bottom=top.copy();bottom[:,1]=top[:,1].min()-180/512
    points=np.unique(np.vstack((top,bottom)),axis=0)
    hull=ConvexHull(points)
    used=hull.vertices;inverse=np.full(len(points),-1,int);inverse[used]=np.arange(len(used))
    return points[used],inverse[hull.simplices],hull.equations,hull.volume


def fit_grid(grid,vertical_budget=.015,horizontal_budget=.002):
    n,m=grid.shape[:2];top=grid.reshape(-1,3);tri=triangles(n,m)
    points,faces,equations,volume=hull_for(top)
    boundary=np.concatenate((grid[0],grid[1:,-1],grid[-1,-2::-1],grid[-2:0:-1,0]))
    domain=Polygon(boundary[:,[0,2]])
    if not domain.is_valid or domain.area<=0:raise ValueError('invalid bed block footprint')
    projected=MultiPoint(top[:,[0,2]]).convex_hull
    if projected.difference(domain.buffer(horizontal_budget)).area>1e-9:return None
    roof=equations[equations[:,1]>1e-8]
    if not len(roof):raise ValueError('convex component has no roof')
    heights=-(roof[:,0,None]*top[None,:,0]+roof[:,2,None]*top[None,:,2]+roof[:,3,None])/roof[:,1,None]
    error=heights-top[None,:,1]
    bound=float(error[:,tri].max(axis=2).min(axis=0).max())
    if bound>vertical_budget+1e-9:
        # An extremum at a source vertex is an inexpensive rejection. If the
        # sufficient bound is merely loose, solve the exact common planar
        # refinement instead of splitting otherwise acceptable components.
        if error.min(axis=0).max()>vertical_budget+1e-9:return None
        source=top[tri];roof_tri=points[faces[equations[:,1]>1e-8]]
        ap=np.array([Polygon(t[:,[0,2]]) for t in source]);bp=np.array([Polygon(t[:,[0,2]]) for t in roof_tri])
        ia,ib=STRtree(bp).query(ap,predicate='intersects')
        intersections=shapely.intersection(ap[ia],bp[ib]);xy,which=shapely.get_coordinates(intersections,return_index=True)
        if not len(xy):raise ValueError('empty roof/source intersection')
        def height(t,xy):
            normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
            return t[:,0,1]-(normal[:,0]*(xy[:,0]-t[:,0,0])+normal[:,2]*(xy[:,1]-t[:,0,2]))/normal[:,1]
        exact=height(roof_tri[ib[which]],xy)-height(source[ia[which]],xy)
        if not np.isfinite(exact).all():raise ValueError('nonfinite exact roof refinement')
        bound=float(exact.max())
        if bound>vertical_budget+1e-9:return None
    return dict(points=points,faces=faces,volume=float(volume),roof_upper_error_bound_m=max(0.,bound),source_triangles=len(tri))


def partition(grid,vertical_budget=.015,horizontal_budget=.002):
    grid=np.asarray(grid,float)
    if grid.ndim!=3 or grid.shape[2]!=3 or min(grid.shape[:2])<2 or not np.isfinite(grid).all():
        raise ValueError('finite bed grid required')
    output=[]
    def split(g):
        try:part=fit_grid(g,vertical_budget,horizontal_budget)
        except QhullError:part=None
        if part is not None:output.append(part);return
        n,m=g.shape[:2]
        if n==m==2:
            top=g.reshape(-1,3)
            for tri in triangles(n,m):
                points,faces,equations,volume=hull_for(top[tri])
                output.append(dict(points=points,faces=faces,volume=float(volume),roof_upper_error_bound_m=0.,source_triangles=1))
            return
        length=np.linalg.norm(g[-1,m//2]-g[0,m//2]);width=np.linalg.norm(g[n//2,-1]-g[n//2,0])
        if n>2 and (m==2 or length>=width):
            mid=(n-1)//2;split(g[:mid+1]);split(g[mid:])
        else:
            mid=(m-1)//2;split(g[:,:mid+1]);split(g[:,mid:])
    split(grid)
    assert sum(p['source_triangles'] for p in output)==2*(grid.shape[0]-1)*(grid.shape[1]-1)
    return output


def add_component(py3d,lod,part,index):
    points,faces=part['points'],part['faces'];centre=points.mean(0);offset=len(lod.points)
    selection=py3d.Selection(lod.points,lod.faces);signed_volume=0.
    for xyz in points:
        point=py3d.Point();point.coords=tuple(xyz);point.mass=1;lod.points.append(point)
        selection.points[point]=1
    for ids0 in faces:
        ids=ids0.copy();t=points[ids];normal=np.cross(t[1]-t[0],t[2]-t[0])
        if normal@(t.mean(0)-centre)>0:ids=ids[::-1];t=points[ids];normal=-normal
        norm=np.linalg.norm(normal);assert norm>1e-10;normal/=norm
        ni=len(lod.facenormals);lod.facenormals.append(tuple(normal));face=py3d.Face(lod.points,lod.facenormals)
        for idx in ids:
            vertex=py3d.Vertex(lod.points,lod.facenormals);vertex.point_index=int(offset+idx);vertex.normal_index=ni;vertex.uv=(0.,0.);face.vertices.append(vertex)
        lod.faces.append(face);selection.faces[face]=1
        signed_volume+=np.dot(t[0]-centre,np.cross(t[1]-centre,t[2]-centre))/6
    assert signed_volume<0 and abs(signed_volume+part['volume'])<1e-6
    lod.selections[f'Component{index:04d}']=selection
    return signed_volume
