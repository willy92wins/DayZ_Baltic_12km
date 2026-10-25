"""Polygon certificate for the lower bound of a union's upper contact surface.

An internal roof can lie below the bed while another convex part covers it.
For every source triangle, union the projected roof regions whose height is
at least source-minus-tolerance. Complete coverage proves the lower bound
over the whole surface. The caller separately bounds EVERY roof from above.
"""
import numpy as np
import shapely
from shapely.geometry import Polygon


def clip_linear_minimum(polygon,values,minimum):
    points=np.asarray(polygon.exterior.coords)[:-1]
    values=np.asarray(values,float)
    if len(points)!=len(values) or not np.isfinite(values).all():raise ValueError('invalid clipping values')
    result=[];previous=points[-1];pv=values[-1]
    for current,cv in zip(points,values):
        pin=pv>=minimum;cin=cv>=minimum
        if pin!=cin:
            fraction=(minimum-pv)/(cv-pv);result.append(previous+fraction*(current-previous))
        if cin:result.append(current)
        previous,pv=current,cv
    if len(result)<3:return None
    clipped=Polygon(result)
    if not clipped.is_valid:raise ValueError('invalid clipped contact polygon')
    return clipped if clipped.area>0 else None


def lower_coverage(source_polygons,roof,source,roof_ids,source_ids,intersections,height,minimum,regions):
    """Accumulate exact acceptable regions from one batch of triangle pairs."""
    coordinates,which=shapely.get_coordinates(intersections,return_index=True)
    if not len(coordinates):return
    errors=height(roof[roof_ids[which]],coordinates)-height(source[source_ids[which]],coordinates)
    lows=np.full(len(intersections),np.inf);highs=np.full(len(intersections),-np.inf)
    np.minimum.at(lows,which,errors);np.maximum.at(highs,which,errors)
    for pair,polygon in enumerate(intersections):
        if polygon.geom_type!='Polygon' or polygon.area<=0 or highs[pair]<minimum:continue
        if lows[pair]>=minimum:good=polygon
        else:
            xy=np.asarray(polygon.exterior.coords)[:-1]
            value=height(np.repeat(roof[roof_ids[pair]][None],len(xy),axis=0),xy)-height(np.repeat(source[source_ids[pair]][None],len(xy),axis=0),xy)
            good=clip_linear_minimum(polygon,value,minimum)
        if good is not None:regions[int(source_ids[pair])].append(good)


def coverage_certificate(source_polygons,regions):
    if not len(source_polygons) or len(source_polygons)!=len(regions):raise ValueError('complete source triangle coverage required')
    total=0.;worst=[]
    for index,(polygon,pieces) in enumerate(zip(source_polygons,regions)):
        accepted=shapely.union_all(pieces)
        missing=polygon.difference(accepted.buffer(1e-7));area=float(missing.area)
        total+=area
        if area>1e-8:worst.append(dict(source_triangle=index,area_m2=area,xy=list(missing.representative_point().coords[0])))
    return dict(covered=bool(total<=1e-6 and not worst),uncovered_area_m2=total,uncovered_triangles=worst[:20],uncovered_triangle_count=len(worst))
