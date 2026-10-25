"""Bounded, monotone bed/bank correction along approved small watercourse cores.

No water classification or level changes. Exact polygon/native-triangle extrema
replace vertex-only acceptance. Infeasible rows are reported, never hidden by
extending depth bounds or excavating an engineered/nature land vertex.
"""
from pathlib import Path
import argparse
import json

import numpy as np
from scipy.ndimage import distance_transform_edt
from shapely.geometry import LineString,box,shape,mapping

from audit_fairway_triangles_v30 import records,save,sha
from finish_shores_v30 import protect_corridors,discard_steeper_land_faces
from v30_common import cell_planes,grid_xz,vertex_plane_bounds

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path('E:/DayZ-Baltic-Build/v30-pond-recovery/terrain_v30.npz')
SOURCE_SHA='2f954ad52893a78181df0f607ddd5e490a470fe9c634bcf30736ed1aef4c179a'
DESIGN=ROOT/'tests/water_v3'
NATURE=ROOT/'tests/regional_outline_v1/reference.npz'
P=dict(core_width_m=1.,depth_m=.0501,max_cut_m=3.,secondary_depth_m=1.2,
       dry_floor_m=1.4001,bank_freeboard_m=.0501,iterations=128,border_fixed_m=12.)


def constraints(planes,design):
    water=design/'water_v3.geojson';streams=design/'streams_candidates.geojson'
    profpath=design/'profiles.npz'
    feats=[f for f in json.loads(water.read_text())['features'] if f['properties']['class']=='river']
    feats += [f for f in json.loads(streams.read_text())['features'] if f['properties']['tier_m']>=2500]
    prof=np.load(profpath);domain=box(0,0,12282,12282)
    rows=[];meta=[];geoms=[];cursor=0
    for f in feats:
        prop=f['properties'];key=prop.get('id')
        if key not in prof.files:continue
        core=LineString(prof[key][:,1:3]).buffer(P['core_width_m']/2,cap_style='flat',join_style='round',quad_segs=4)
        core=core.intersection(shape(f['geometry'])).intersection(domain)
        if core.is_empty:continue
        rec=records(core,planes);rows.append(rec)
        meta.append(dict(id=key,name=prop.get('name',''),**{'class':prop['class']},start=cursor,count=len(rec['ids']),faces=rec['faces']))
        geoms.append(dict(type='Feature',properties=meta[-1],geometry=mapping(core)))
        cursor+=len(rec['ids'])
    combined={k:np.concatenate([r[k] for r in rows]) for k in ('ids','weights','xz','level')}
    return combined,meta,geoms,[water,streams,profpath]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--source',type=Path,default=SOURCE)
    ap.add_argument('--source-sha',default=SOURCE_SHA)
    ap.add_argument('--design',type=Path,default=DESIGN)
    ap.add_argument('--nature',type=Path,default=NATURE)
    a=ap.parse_args();assert not a.out.exists() and (a.source_sha=='any' or sha(a.source)==a.source_sha)
    t=np.load(a.source);old=t['heights'].astype(float);cls=t['cls'];level=t['level'].astype(float)
    plane=cell_planes(cls,level);pmin,pmax=vertex_plane_bounds(plane)
    _,margin,_,_=protect_corridors(plane)
    naturepath=a.nature
    nature=np.load(naturepath)['reserve'].astype(bool)
    xx,zz=grid_xz();secondary=np.isin(cls,(5,6));dry=cls==0
    fixed=margin|t['platform']|t['reserve']|t['narva']|t['beach']
    fixed|=nature&~secondary
    fixed|=(xx<P['border_fixed_m'])|(zz<P['border_fixed_m'])|(xx>12282-P['border_fixed_m'])|(zz>12282-P['border_fixed_m'])
    mutable=(secondary|dry)&~fixed
    _,near=distance_transform_edt(dry,return_indices=True)
    nearlevel=level[near[0],near[1]]
    low=np.where(secondary,np.nan_to_num(pmin,nan=.5)-P['secondary_depth_m'],
                 np.maximum(P['dry_floor_m'],np.maximum(np.nan_to_num(pmax,nan=-np.inf),nearlevel)+P['bank_freeboard_m']))
    low=np.minimum(old,np.maximum(old-P['max_cut_m'],low))
    low[~mutable]=old[~mutable]
    rec,meta,geoms,sources=constraints(plane,a.design)
    ids=rec['ids'];weights=np.maximum(rec['weights'],0);target=rec['level']-P['depth_m']
    original=np.sum(old.ravel()[ids]*weights,axis=1)
    feasible=np.sum(low.ravel()[ids]*weights,axis=1)<=target+1e-8
    need=original>target+1e-5
    use=need&feasible
    assert use.any()
    # No arithmetic outside the few vertices used by feasible failing faces.
    local=np.unique(ids[use]);allowed=np.zeros_like(mutable)
    allowed.ravel()[local]=True;allowed&=mutable
    low[~allowed]=old[~allowed]
    h=old.ravel().copy();lower=low.ravel()
    workids=ids[use];workweights=weights[use];worktarget=target[use]
    history=[]
    for iteration in range(P['iterations']):
        residual=np.sum(h[workids]*workweights,axis=1)-worktarget
        active=residual>1e-5
        history.append(dict(iteration=iteration,rows=int(active.sum()),max_deficit_m=float(max(0,residual.max()))))
        if not active.any():break
        ri=workids[active];ww=workweights[active];cap=np.maximum(0,h[ri]-lower[ri])
        eligible=cap>1e-8
        coeff=np.where(eligible,ww,0.)
        denom=np.sum(coeff*coeff,axis=1)
        if np.any(denom<=1e-14):raise ValueError('Feasibility changed during projection')
        step=np.minimum(cap,residual[active,None]*coeff/denom[:,None])
        correction=np.zeros_like(h)
        np.maximum.at(correction,ri.ravel(),step.ravel())
        h=np.maximum(lower,h-correction)
    else:raise ValueError('Projection exceeded its declared iteration budget')
    h=h.reshape(old.shape)
    candidate,recovery=discard_steeper_land_faces(h,old,cls)
    candidate=candidate.astype('float32');changed=candidate!=t['heights']
    assert changed.any() and not (changed&~allowed).any() and not (changed&fixed).any()
    assert np.all(candidate<=old+1e-6) and (old-candidate).max()<=P['max_cut_m']+1e-5
    after=np.sum(candidate.ravel()[ids]*weights,axis=1)
    for m in meta:
        sl=slice(m['start'],m['start']+m['count'])
        m.update(before_rows_below_target=int(need[sl].sum()),infeasible_rows=int((need&~feasible)[sl].sum()),
                 remaining_rows_below_target=int((after>target+1e-5)[sl].sum()),
                 min_depth_before_m=float((rec['level']-original)[sl].min()),
                 min_depth_after_m=float((rec['level']-after)[sl].min()))
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out/'terrain_v30.npz',**{k:candidate if k=='heights' else t[k] for k in t.files})
    with (a.out/'baltic_terrain_v30.asc').open('x',encoding='ascii',newline='\n') as stream:
        stream.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(stream,candidate,fmt='%.9g')
    np.savez_compressed(a.out/'continuity_constraints.npz',**rec,feasible=feasible,changed=changed,allowed=allowed,fixed=fixed)
    save(a.out/'cores.geojson',dict(type='FeatureCollection',features=geoms))
    remain=(after>target+1e-5)
    result=dict(status='BUILT_PENDING_GROUPED_GATES',source_sha256=sha(a.source) if a.source_sha=='any' else a.source_sha,params=P,
                candidate_sha256=sha(a.out/'terrain_v30.npz'),asc_sha256=sha(a.out/'baltic_terrain_v30.asc'),
                changed_vertices=int(changed.sum()),wet_vertices=int((changed&secondary).sum()),dry_vertices=int((changed&dry).sum()),
                nature_water_vertices=int((changed&nature).sum()),max_cut_m=float((old-candidate).max()),
                rows=len(ids),before_below_target=int(need.sum()),infeasible_before=int((need&~feasible).sum()),
                remaining_below_target=int(remain.sum()),feasible_remaining=int((remain&feasible).sum()),
                face_recovery=recovery,iterations=history,profiles=meta,
                inputs={str(p):sha(p) for p in (a.source,naturepath,*sources,Path(__file__),
                        Path(cell_planes.__code__.co_filename),Path(records.__code__.co_filename),
                        Path(protect_corridors.__code__.co_filename))},
                limits=['Existing water classes/levels/pieces remain exact; the source already includes the four restored ponds.',
                        'Unchanged engineering/fixed-border constraints and depth bounds can leave residual interruptions; listed per profile.',
                        'Nature land and biome data are unchanged; only already-wet small-course beds may lower.',
                        'Physical readback, water appearance and navigation require the engine.'])
    save(a.out/'build.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('profiles','inputs','limits','iterations')},indent=2))


if __name__=='__main__':main()
