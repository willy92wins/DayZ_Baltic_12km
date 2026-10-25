"""Continuous source-road bands and piecewise-affine chord bounds."""
import json
import numpy as np
from affine import Affine
from rasterio.features import rasterize
from shapely.geometry import Polygon, shape
from build_road_constraints_v25 import breaks, position


def water_exclusion(root, sha):
    pins={'water-surfaces-contour-v2.geojson':'df860f693a1bf0115cb4af65a13cea5f8006a5a21bc9bca1d88276b83802ccdc',
          'ocean-game.json':'c72aaafd6ee35abfcdec180135571e34b9c5eaefb42d3bca1bfbabad6493f757'}
    geos=[]
    for name,digest in pins.items():
        p=root/'evidence/regional-foundation-v1'/name;assert sha(p)==digest
        geos.extend(shape(f['geometry']) for f in json.loads(p.read_text())['features'])
    cells=rasterize([(g,1) for g in geos],out_shape=(2047,2047),transform=Affine(6,0,0,0,-6,12282),all_touched=True,dtype='uint8').astype(bool)
    protected=rasterize([(g.buffer(30,quad_segs=64),1) for g in geos],out_shape=(2048,2048),transform=Affine(6,0,-3,0,-6,12285),all_touched=False,dtype='uint8').astype(bool)
    for dy,dx in ((0,0),(0,1),(1,0),(1,1)):protected[dy:2047+dy,dx:2047+dx]|=cells
    return protected


def route_geometry(route):
    p=np.asarray(route['source_polyline'])
    station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    lo,hi=route['solve_start_m'],route['solve_end_m']
    eligibility=breaks(p,station,[(np.array([1.,0.]),3.),(np.array([0.,1.]),3.)],circle=True)
    return p,station,lo,hi,eligibility


def add_bands(routes,dry,band,touched):
    count=0;joins=0
    angle=np.arange(16)*np.pi/8
    circle=np.column_stack([np.cos(angle),np.sin(angle)])*(4.001/np.cos(np.pi/16))
    for number,route in enumerate(routes):
        p,station,lo,hi,eligibility=route_geometry(route)
        cuts=np.unique(np.r_[lo,eligibility[(eligibility>lo)&(eligibility<hi)],hi])
        mid=(cuts[:-1]+cuts[1:])/2;valid=dry(position(p,station,mid))
        start,end=cuts[:-1][valid],cuts[1:][valid]
        for aa,bb in zip(start,end):
            a,b=position(p,station,[aa,bb]);tangent=(b-a)/np.linalg.norm(b-a);normal=np.array([-tangent[1],tangent[0]])
            poly=Polygon([a+normal*4,b+normal*4,b-normal*4,a-normal*4])
            for tri in touched(poly):band(tri,normal,tangent)
            count+=1
        knots=np.r_[lo,station[(station>lo)&(station<hi)],hi];q=position(p,station,knots)
        for i in range(1,len(q)-1):
            if not np.any((start<knots[i]+.5)&(end>knots[i]-.5)):continue
            directions=[q[i]-q[i-1],q[i+1]-q[i]];directions=[v/np.linalg.norm(v) for v in directions]
            bisector=directions[0]+directions[1];assert np.linalg.norm(bisector)>1e-6
            directions.append(bisector/np.linalg.norm(bisector))
            for tri in touched(Polygon(q[i]+circle)):
                for tangent in directions:band(tri,np.array([-tangent[1],tangent[0]]),tangent)
            joins+=1
        if number%10==0:print(json.dumps(dict(stage='continuous_geometry',route=number,total=len(routes))),flush=True)
    return dict(eligible_band_intervals=count,eligible_corner_disks=joins)


def add_chords(routes,dry,bound,weights):
    count=0
    for route in routes:
        p,station,lo,hi,eligibility=route_geometry(route)
        native=breaks(p,station,[(np.array([1.,0.]),0.),(np.array([0.,1.]),0.),(np.array([1.,1.]),0.)])
        events=np.union1d(native,eligibility)
        cuts=np.unique(np.r_[lo+3,hi-3,events-3,events,events+3]);cuts=cuts[(cuts>=lo+3)&(cuts<=hi-3)]
        if len(cuts)<2:continue
        mid=(cuts[:-1]+cuts[1:])/2
        eligible=np.logical_and.reduce([dry(position(p,station,mid+s)) for s in (-3,0,3)])
        ends=np.unique(np.r_[cuts[:-1][eligible],cuts[1:][eligible]])
        points=np.array([position(p,station,ends+s) for s in (-3,0,3)])
        ix,w=weights(points.reshape(-1,2));ix=ix.reshape(3,-1,3);w=w.reshape(3,-1,3)
        for i in range(len(ends)):
            indices=ix[:,i,:].ravel();coeff=(w[:,i,:]*np.array([-.5,1.,-.5])[:,None]).ravel()
            bound(indices,coeff,.022);bound(indices,-coeff,.022)
        count+=len(ends)
    return count
