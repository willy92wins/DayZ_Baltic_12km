"""Bound native terrain planes over exact protected-land polygon intersections."""
from pathlib import Path
import json,hashlib
import numpy as np
from rasterio.features import rasterize
from rasterio.transform import Affine
from shapely import polygons,intersection,area,get_coordinates
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'

def minimum_margin(h,g,target):
    if g.is_empty:return float('inf'),0
    cells=rasterize([(g,1)],out_shape=(2047,2047),transform=Affine(6,0,0,0,-6,12282),all_touched=True,dtype='uint8')
    rr,cc=np.nonzero(cells);x=cc*6;z=12282-rr*6
    coords=[np.c_[x,z],np.c_[x+6,z],np.c_[x,z-6],np.c_[x+6,z-6]]
    heights=[h[rr,cc],h[rr,cc+1],h[rr+1,cc],h[rr+1,cc+1]]
    smallest=float('inf');count=0
    for inds in ([0,1,3],[0,3,2]):
        triangles=np.stack([coords[k] for k in inds],axis=1)
        clips=intersection(polygons(triangles),g);valid=area(clips)>1e-9
        if not valid.any():continue
        # Solve y = a*x_relative + b*z_relative + c independently of the
        # producer's sample() interpolation and LP coefficient construction.
        corners=triangles[valid];origin=corners[:,0,:].copy()
        matrix=np.concatenate([corners-origin[:,None,:],np.ones((len(corners),3,1))],axis=2)
        plane=np.linalg.solve(matrix,np.stack([heights[k][valid] for k in inds],axis=1)[...,None])[...,0]
        p,index=get_coordinates(clips[valid],return_index=True)
        relative=p-origin[index]
        values=np.sum(plane[index,:2]*relative,axis=1)+plane[index,2]-target
        smallest=min(smallest,float(values.min()));count+=len(p)
    return smallest,count

def main():
    out=EV/'protected-island-native-plane-v9.json';assert not out.exists()
    h=np.load(ROOT/'tests/regional_foundation_combined_v9/reference.npz')['candidate']
    source=EV/'protected-islands-game.json';features=json.loads(source.read_text())['features']
    water=json.loads((EV/'island-support-v7.json').read_text())['islands']
    records=[]
    for i,f in enumerate(features):
        g=shape(f['geometry']);level=water[i]['adjacent_water_ceiling_m']
        shore,ns=minimum_margin(h,g,level)
        core,nc=minimum_margin(h,g.buffer(-6),level+.35)
        # Small islands without a six-metre interior keep a dry representative.
        p=g.representative_point();x,z=p.x,p.y;r=(12282-z)/6;c=x/6;ri,ci=int(r),int(c);a,b=c-ci,r-ri
        y=(h[ri,ci]*(1-a)+h[ri,ci+1]*(a-b)+h[ri+1,ci+1]*b) if b<=a else (h[ri,ci]*(1-b)+h[ri+1,ci]*(b-a)+h[ri+1,ci+1]*a)
        records.append(dict(index=i,shore_margin_m=shore,core_margin_m=core if nc else None,representative_freeboard_m=float(y-level),shore_vertices_checked=ns,core_vertices_checked=nc,passed=bool(shore>=-1e-5 and core>=-1e-5 and y>=level+.35-1e-5)))
    result=dict(status='PASS_OFFLINE_PROTECTED_LAND_PLANES' if all(r['passed'] for r in records) else 'FAIL',islands=len(records),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),minimum_shore_margin_m=min(r['shore_margin_m'] for r in records),records=records,limits=['Plane bounds over the source land polygons. Native export and runtime water classification remain separate gates.'])
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2));print(json.dumps([r for r in records if not r['passed']],indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)
if __name__=='__main__':main()
