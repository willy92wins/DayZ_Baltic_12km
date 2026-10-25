"""Screen both sides of F routes before native queries; freeze four two-leg routes."""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import LineString, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'terrain'))
from v30_common import tri_sample


@lru_cache(maxsize=4096)
def cell_polygon(row, col):
    return box(6 * col, 12282 - 6 * (row + 1), 6 * (col + 1), 12282 - 6 * row)


def touched_cells(start, end, width=2.1):
    """Exact closed intersections with a square-capped two-sided corridor.

    Shapely BaseGeometry.buffer (base.py:462) documents square caps extending
    by width. This rectangle contains the radius-width capsule, including ends.
    Padding enumerates both cells at exact grid boundaries; intersects is closed.
    """
    band = LineString([start, end]).buffer(width, cap_style='square')
    xmin, zmin, xmax, zmax = band.bounds
    cells = []
    for row in range(int(np.floor((12282-zmax)/6))-1, int(np.floor((12282-zmin)/6))+2):
        for col in range(int(np.floor(xmin/6))-1, int(np.floor(xmax/6))+2):
            if band.intersects(cell_polygon(row, col)):
                cells.append((row, col))
    return cells


def corners(h, cells):
    row, col = np.asarray(cells).T
    return np.stack([h[row,col], h[row,col+1], h[row+1,col], h[row+1,col+1]], axis=1)


def dry_clearance(he, hf, plane, field, cells):
    row, col = np.asarray(cells).T
    if row.min() < 0 or col.min() < 0 or row.max()+1 >= he.shape[0] or col.max()+1 >= he.shape[1]:
        return None
    levels = np.where(np.isfinite(plane[row,col])[:,None], field[row,col], .75)
    if not np.isfinite(levels).all():
        return None
    ec, fc = corners(he,cells), corners(hf,cells)
    return float(np.min(np.minimum(ec,fc) - np.max(levels,axis=1)[:,None]))


def disk_offsets():
    """Rings <=0.5m apart, arcs <=0.5m; sampled screening, not continuous proof."""
    offsets = [[0.,0.]]
    for radius in (.5,1.,1.5,2.,2.1):
        count = int(np.ceil(2*np.pi*radius/.5))
        angles = np.arange(count)*2*np.pi/count
        offsets.extend(np.column_stack([radius*np.cos(angles),radius*np.sin(angles)]).tolist())
    return np.asarray(offsets)


def midpoint(he, hf, start, end):
    start, end = np.asarray(start), np.asarray(end)
    length = float(np.linalg.norm(end-start))
    distances = np.linspace(0,length,int(np.ceil(length))+1)
    distances = distances[(distances >= 6) & (distances <= length-6)]
    xy = start[None,:] + distances[:,None]/length*(end-start)[None,:]
    if not len(xy):
        return None
    delta = np.abs(tri_sample(hf,xy[:,0],xy[:,1])-tri_sample(he,xy[:,0],xy[:,1]))
    # Stable order breaks ties by distance from start; only input terrain is used.
    for index in np.argsort(-delta, kind='stable'):
        if delta[index] < .1:
            break
        samples = xy[index] + disk_offsets()
        dd = np.abs(tri_sample(hf,samples[:,0],samples[:,1])-tri_sample(he,samples[:,0],samples[:,1]))
        if float(dd.min()) >= .05:
            return dict(xz=xy[index].tolist(),delta_m=float(delta[index]),
                        min_disk_sample_delta_m=float(dd.min()),disk_sample_count=len(samples),
                        distance_from_start_m=float(distances[index]))
    return None


def max_slope(h, cells):
    nw, ne, sw, se = corners(h,cells).T
    gradient = np.maximum(np.hypot(ne-nw,se-ne), np.hypot(se-sw,sw-nw))/6
    return float(np.degrees(np.arctan(gradient)).max())


def screen(he, hf, plane, field):
    if he.shape != hf.shape or he.shape != (2048,2048) or not np.isfinite(he).all() or not np.isfinite(hf).all():
        raise ValueError('Expected finite native E/F terrain grids')
    result = dict(status='PREPARATION_INCONCLUSIVE',routes=[],queries=[],
        policy=dict(centers_x=list(range(2892,2947,6)),centers_z=list(range(6804,6865,6)),
            half_extents_m=[12,18,24,30],band_radius_m=2.1,min_corner_clearance_m=.05,
            strong_delta_m=.1,min_strong_cells=2,midpoint_min_delta_m=.1,
            midpoint_disk_min_delta_m=.05,midpoint_end_distance_m=6.,
            ranking='Maximize distinct strong cells; nearest center to(2916,6834); longest segment. Midpoint must pass pre-run disk screen.'),
        limits=['Screened terrain and water only; no proof of absence of 3D objects.',
                'Disk delta samples are a screen; native waypoint coverage remains mandatory.'])
    for name,direction in [('ew',(1,0)),('ns',(0,1)),('ne_sw',(1,1)),('nw_se',(1,-1))]:
        choices=[];dry_count=0;strong_count=0
        for cx in result['policy']['centers_x']:
            for cz in result['policy']['centers_z']:
                for half in result['policy']['half_extents_m']:
                    start=np.array([cx,cz])-np.array(direction)*half
                    end=np.array([cx,cz])+np.array(direction)*half
                    cells=touched_cells(start,end)
                    clearance=dry_clearance(he,hf,plane,field,cells)
                    if clearance is None or clearance < .05:
                        continue
                    dry_count+=1
                    ec,fc=corners(he,cells),corners(hf,cells)
                    strong=[cell for cell,delta in zip(cells,np.max(np.abs(fc-ec),axis=1)) if delta >= .1]
                    if len(strong)<2:
                        continue
                    strong_count+=1
                    middle=midpoint(he,hf,start,end)
                    if middle is None:
                        continue
                    length=float(np.linalg.norm(end-start))
                    route=dict(name='f_patch_'+name,start_xz=start.tolist(),end_xz=end.tolist(),
                        midpoint=middle,length_m=length,min_corner_clearance_m=clearance,
                        touched_cells=cells,strong_cells=strong,
                        max_triangle_slope_e_deg=max_slope(he,cells),max_triangle_slope_f_deg=max_slope(hf,cells))
                    choices.append((len(strong),-((cx-2916)**2+(cz-6834)**2),length,route))
        choices.sort(key=lambda x:x[:3],reverse=True)
        selected=choices[0][3] if choices else None
        result['routes'].append(dict(direction=name,dry_candidates=dry_count,strong_candidates=strong_count,
                                     admissible_candidates=len(choices),selected=selected))
        if selected:
            positions=[selected['start_xz'],selected['midpoint']['xz'],selected['end_xz']]
            for leg in range(2):
                result['queries'].append(dict(name=selected['name']+'_'+str(leg+1),expect='path',
                    start=[positions[leg][0],0.,positions[leg][1]],
                    end=[positions[leg+1][0],0.,positions[leg+1][1]]))
    if len(result['queries'])==8:
        result['status']='PREPARED_GEOMETRIC_SCREEN_NOT_NATIVE_ACCEPTANCE'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('terrain-e','terrain-f','footprint'):
        p.add_argument('--'+name,type=Path,required=True)
        p.add_argument('--'+name+'-sha256',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():
        raise FileExistsError('Fresh output required')
    inputs={}
    for name in ('terrain_e','terrain_f','footprint'):
        path=getattr(a,name);digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=getattr(a,name+'_sha256'):
            raise ValueError('Input identity mismatch: '+name)
        inputs[name]=dict(path=str(path.resolve()),sha256=digest)
    he=np.load(a.terrain_e)['heights'];hf=np.load(a.terrain_f)['heights']
    with np.load(a.footprint) as water:
        result=screen(he,hf,water['plane'],water['field'])
    result.update(inputs=inputs,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],routes=[dict(direction=r['direction'],admissible=r['admissible_candidates'],selected=r['selected']) for r in result['routes']]),indent=2))
    raise SystemExit(0 if len(result['queries'])==8 else 2)


if __name__=='__main__':
    main()
