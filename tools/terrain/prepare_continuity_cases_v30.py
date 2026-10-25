"""Freeze residual diagnoses and engine points for the small-course candidate.

No editing: lower bounds reproduce the declared authoring constraints, while
the engine points are selected before loading any runtime log.
"""
from pathlib import Path
import argparse
import json

import numpy as np
from scipy.ndimage import distance_transform_edt

from audit_fairway_triangles_v30 import save,sha
from connect_small_watercourses_v30 import P,SOURCE,SOURCE_SHA
from v30_common import cell_planes,vertex_plane_bounds,grid_xz,tri_sample

ROOT=Path(__file__).resolve().parents[2]


def at_point(x,z):
    c,r=x/6,(12282-z)/6
    cc,rr=int(np.floor(c)),int(np.floor(r))
    u,v=c-cc,r-rr
    if u>=v:
        ids=np.array([rr*2048+cc,rr*2048+cc+1,(rr+1)*2048+cc+1])
        weights=np.array([1-u,u-v,v])
    else:
        ids=np.array([rr*2048+cc,(rr+1)*2048+cc,(rr+1)*2048+cc+1])
        weights=np.array([1-v,v-u,u])
    return ids,weights


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists() and sha(SOURCE)==SOURCE_SHA
    t=np.load(a.candidate);old=np.load(SOURCE)
    h=t['heights'].astype(float);original=old['heights'].astype(float)
    cls=t['cls'];plane=cell_planes(cls,t['level']);pmin,pmax=vertex_plane_bounds(plane)
    saved=np.load(a.candidate.parent/'continuity_constraints.npz')
    fixed=saved['fixed'];secondary=np.isin(cls,(5,6));dry=cls==0
    _,near=distance_transform_edt(dry,return_indices=True)
    nearest=old['level'][near[0],near[1]]
    lower=np.where(secondary,np.nan_to_num(pmin,nan=.5)-P['secondary_depth_m'],
                   np.maximum(P['dry_floor_m'],np.maximum(np.nan_to_num(pmax,nan=-np.inf),nearest)+P['bank_freeboard_m']))
    lower=np.minimum(original,np.maximum(original-P['max_cut_m'],lower))
    lower[fixed|~(secondary|dry)]=original[fixed|~(secondary|dry)]
    xx,zz=grid_xz()
    nature=np.load(ROOT/'tests/regional_outline_v1/reference.npz')['reserve'].astype(bool)
    border=(xx<12)|(zz<12)|(xx>12270)|(zz>12270)
    audit=json.loads((a.candidate.parent/'small-watercourses-v2.json').read_text())
    assert audit['terrain_sha256']==sha(a.candidate)
    rows=[];points=[]
    for course in audit['profiles']:
        for gap in course['unreserved_breaks']:
            if gap['length_m']<6:continue
            x,z=gap['xz'];ids,w=at_point(x,z)
            rr,cc=int(np.floor((12282-z)/6)),int(np.floor(x/6))
            water=max(.5,float(np.nan_to_num(plane[rr,cc],nan=-np.inf)))
            best=float(w@lower.ravel()[ids]);depth=water-float(w@h.ravel()[ids])
            markers=dict(border=bool(np.any(border.ravel()[ids]&(w>1e-8))),
                         nature_dry_land=bool(np.any((nature&dry).ravel()[ids]&(w>1e-8))),
                         other_fixed=bool(np.any(fixed.ravel()[ids]&(w>1e-8))),
                         dry_vertex_floor=bool(np.any(dry.ravel()[ids]&(w>1e-8))),
                         all_constraints_allow_5cm=bool(best<=water-.05+1e-5))
            reason='fixed_border' if markers['border'] else 'protected_vertex' if markers['other_fixed'] else (
                'remaining_after_steep_face_recovery' if markers['all_constraints_allow_5cm'] else 'depth_or_bank_floor_bound')
            rows.append(dict(id=course['id'],name=course['name'],**gap,midpoint_depth_m=depth,
                             midpoint_best_bounded_depth_m=water-best,reason=reason,markers=markers,
                             vertex_ids=ids.tolist(),weights=w.tolist(),
                             vertex_classes=cls.ravel()[ids].tolist(),
                             ground_vertices=h.ravel()[ids].tolist(),lower_vertices=lower.ravel()[ids].tolist()))
            points.append(dict(x=x,z=z,case=course['id']+'_residual',reason=reason))
    build=json.loads((a.candidate.parent/'build.json').read_text())
    ids,weights=saved['ids'],saved['weights']
    oldvals=np.sum(original.ravel()[ids]*weights,axis=1)
    vals=np.sum(h.ravel()[ids]*weights,axis=1)
    for item in build['profiles']:
        start,count=item['start'],item['count']
        if count==0:continue
        sl=slice(start,start+count)
        improve=oldvals[sl]-vals[sl]
        if improve.max()<=.04:continue
        i=start+int(np.argmax(improve));x,z=saved['xz'][i]
        points.append(dict(x=float(x),z=float(z),case=item['id']+'_improved',
                           reason='greatest_ground_delta_on_exact_core',height_delta_m=float(improve.max())))
    # Every restored-pond vertex plus strict interiors is small enough for full
    # readback. This mask is an authoring case selector, not an acceptance gate.
    pmaskpath=SOURCE.parent/'pond_repair_masks.npz'
    rr,cc=np.nonzero(np.load(pmaskpath)['changed'])
    assert len(rr)==75
    for r,c in zip(rr,cc):
        for dx,dz in ((0,0),(4,-2),(2,-4)):
            points.append(dict(x=float(c*6+dx),z=float(12282-r*6+dz),
                               case='restored_pond',reason='all_75_changed_vertices_and_triangle_interiors'))
    assert len(points)<=4096
    a.out.mkdir(parents=True)
    save(a.out/'engine-extra-points.json',dict(schema_version=1,terrain_sha256=sha(a.candidate),points=points,
                                             sources={str(p):sha(p) for p in (pmaskpath,Path(__file__))}))
    save(a.out/'residual-cases.json',dict(status='DIAGNOSED_NOT_RESOLVED',terrain_sha256=sha(a.candidate),
        cases=rows,reason_counts={k:sum(r['reason']==k for r in rows) for k in sorted({r['reason'] for r in rows})},
        limitations=['Causes are diagnosed at the midpoint; the whole gap may have mixed constraints.',
                     'A fixed boundary, nature ground or road is not altered to turn this report green.',
                     'No engine readback, connected flow, visible shoreline or navigation proof.']))
    print(json.dumps(dict(residual_cases=len(rows),engine_points=len(points),
                         reason_counts={k:sum(r['reason']==k for r in rows) for k in sorted({r['reason'] for r in rows})}),indent=2))


if __name__=='__main__':main()
