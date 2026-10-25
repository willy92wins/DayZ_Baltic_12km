"""One bounded joint depth/slope solve for residual small-course interruptions.

The accepted authoring candidate is immutable. Each spatial group has one SLSQP
attempt; only a float32-feasible local result is incorporated. No level, mask,
road, protected dry nature ground, navigable corridor or border is changed.
"""
from pathlib import Path
import argparse
import json
import time

import numpy as np
import scipy
from scipy.ndimage import distance_transform_edt
from scipy.optimize import minimize
import shapely
from shapely.geometry import Point,shape,mapping

from audit_fairway_triangles_v30 import save,sha
from connect_small_watercourses_v30 import P
from v30_common import cell_planes,vertex_plane_bounds,grid_xz

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path('E:/DayZ-Baltic-Build/v30-watercourse-continuity/terrain_v30.npz')
EXPECTED='40d8cfd9874e9260464f9e3c38c07d81a15c8aed374083a52c98f042c0161c2e'
BASE=Path('E:/DayZ-Baltic-Build/v30-pond-recovery/terrain_v30.npz')
BASE_SHA='2f954ad52893a78181df0f607ddd5e490a470fe9c634bcf30736ed1aef4c179a'
SETTINGS=dict(radius_m=30.,max_groups=10,max_variables=500,max_iterations=300,max_seconds_per_group=120.,
              ftol=1e-10,depth_target_m=.0501,float_depth_tolerance_m=2e-5,slope_tolerance_deg=.00009)


class TimeBudget(Exception):
    pass


def affected_faces(vertex_ids):
    r,c=np.divmod(vertex_ids,2048)
    cells=np.unique(np.concatenate([(r+dr)*2047+c+dc for dr in (-1,0) for dc in (-1,0)]))
    rr,cc=np.divmod(cells,2047)
    keep=(rr>=0)&(rr<2047)&(cc>=0)&(cc<2047)
    rr,cc=rr[keep],cc[keep]
    nw=rr*2048+cc;ne=nw+1;sw=nw+2048;se=sw+1
    # Same two gradient components, exchanged on the lower triangle.
    return np.concatenate([np.column_stack((nw,ne,se)),np.column_stack((nw,sw,se))])


def dense_rows(ids,weights,lookup,n):
    out=np.zeros((len(ids),n),float)
    for i in range(3):
        cols=lookup[ids[:,i]];valid=cols>=0
        out[np.flatnonzero(valid),cols[valid]]+=weights[valid,i]
    return out


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists() and sha(SOURCE)==EXPECTED and sha(BASE)==BASE_SHA
    t=np.load(SOURCE);base=np.load(BASE)
    initial=t['heights'].astype(float);original=base['heights'].astype(float);h=initial.copy()
    cls=t['cls'];plane=cell_planes(cls,t['level']);pmin,pmax=vertex_plane_bounds(plane)
    savedpath=SOURCE.parent/'continuity_constraints.npz';saved=np.load(savedpath)
    fixed=saved['fixed'];secondary=np.isin(cls,(5,6));dry=cls==0
    _,near=distance_transform_edt(dry,return_indices=True)
    nearlevel=base['level'][near[0],near[1]]
    low=np.where(secondary,np.nan_to_num(pmin,nan=.5)-P['secondary_depth_m'],
                 np.maximum(P['dry_floor_m'],np.maximum(np.nan_to_num(pmax,nan=-np.inf),nearlevel)+P['bank_freeboard_m']))
    low=np.minimum(original,np.maximum(original-P['max_cut_m'],low))
    low[fixed|~(secondary|dry)]=initial[fixed|~(secondary|dry)]
    water=ROOT/'tests/water_v3/water_v3.geojson';streams=ROOT/'tests/water_v3/streams_candidates.geojson'
    feats=[f for f in json.loads(water.read_text())['features'] if f['properties']['class']=='river']
    feats += [f for f in json.loads(streams.read_text())['features'] if f['properties']['tier_m']>=2500]
    support=shapely.union_all([shape(f['geometry']) for f in feats]).buffer(8.486)
    casepath=SOURCE.parent/'local-cases/residual-cases.json'
    cases=json.loads(casepath.read_text())['cases']
    cases=[c for c in cases if c['reason']=='remaining_after_steep_face_recovery']
    assert len(cases)==10
    groups=shapely.get_parts(shapely.union_all([Point(c['xz']).buffer(SETTINGS['radius_m']) for c in cases]))
    groups=sorted(groups,key=lambda p:p.bounds)
    assert 0<len(groups)<=SETTINGS['max_groups']
    xx,zz=grid_xz();results=[]
    all_ids=saved['ids'];all_w=np.maximum(saved['weights'],0);target=saved['level']-SETTINGS['depth_target_m']
    a.out.mkdir(parents=True)
    for number,g in enumerate(groups):
        start=time.monotonic();x0,z0,x1,z1=g.bounds
        bounds=(xx>=x0)&(xx<=x1)&(zz>=z0)&(zz<=z1)&~fixed&(secondary|dry)&(h>low+1e-5)
        rr,cc=np.nonzero(bounds);coords=shapely.points(xx[rr,cc],zz[rr,cc])
        keep=shapely.covers(g,coords)&shapely.covers(support,coords)
        variables=rr[keep]*2048+cc[keep]
        result=dict(group=number,variables=len(variables),bounds=list(g.bounds),
                    cases=[c for c in cases if g.covers(Point(c['xz']))])
        if len(variables)==0 or len(variables)>SETTINGS['max_variables']:
            result['status']='SKIPPED_VARIABLE_BUDGET';results.append(result);continue
        lookup=np.full(2048*2048,-1,np.int32);lookup[variables]=np.arange(len(variables))
        relevant=np.any(lookup[all_ids]>=0,axis=1)&saved['feasible']
        ids,ww=all_ids[relevant],all_w[relevant]
        startheights=h.ravel()[variables].copy();capacity=np.maximum(0,startheights-low.ravel()[variables])
        A=dense_rows(ids,ww,lookup,len(variables))
        b=np.sum(h.ravel()[ids]*ww,axis=1)-target[relevant]
        failing=b>1e-5;reachable=(A@capacity>=b-1e-8)
        result.update(already_satisfied_rows=int((~failing).sum()),local_unreachable_rows=int((failing&~reachable).sum()))
        A,b=A[failing&reachable],b[failing&reachable]
        if not len(b):
            result['status']='NO_LOCALLY_REACHABLE_DEPTH_ROW';results.append(result);continue
        # Repeated polygon intersection vertices create duplicate linear rows.
        unique=np.unique(np.round(np.column_stack((A,b)),12),axis=0)
        A,b=unique[:,:-1],unique[:,-1]
        faces=affected_faces(variables)
        coeff1=np.tile(np.array([-1.,1.,0.])/6,(len(faces),1))
        coeff2=np.tile(np.array([0.,-1.,1.])/6,(len(faces),1))
        B1=dense_rows(faces,coeff1,lookup,len(variables));B2=dense_rows(faces,coeff2,lookup,len(variables))
        g1=np.sum(h.ravel()[faces]*coeff1,axis=1);g2=np.sum(h.ravel()[faces]*coeff2,axis=1)
        o1=np.sum(original.ravel()[faces]*coeff1,axis=1);o2=np.sum(original.ravel()[faces]*coeff2,axis=1)
        limit2=np.maximum(np.tan(np.radians(35.))**2,o1*o1+o2*o2)
        iterations=0
        def slope(y):
            u,v=g1-B1@y,g2-B2@y
            return limit2-u*u-v*v
        def slope_jac(y):
            u,v=g1-B1@y,g2-B2@y
            return 2*u[:,None]*B1+2*v[:,None]*B2
        def progress(y):
            nonlocal iterations
            iterations+=1
            if time.monotonic()-start>SETTINGS['max_seconds_per_group']:raise TimeBudget()
        try:
            solved=minimize(lambda y:float(y@y),np.zeros(len(variables)),jac=lambda y:2*y,method='SLSQP',
                bounds=list(zip(np.zeros(len(variables)),capacity)),
                constraints=[dict(type='ineq',fun=lambda y:A@y-b,jac=lambda y:A),
                             dict(type='ineq',fun=slope,jac=slope_jac)],callback=progress,
                options=dict(maxiter=SETTINGS['max_iterations'],ftol=SETTINGS['ftol'],disp=False))
            new=(startheights-solved.x).astype('float32').astype(float)
            y=startheights-new
            worst_depth_deficit=float(np.max(b-A@y))
            u,v=g1-B1@y,g2-B2@y
            angle=np.degrees(np.arctan(np.hypot(u,v)))
            oldangle=np.degrees(np.arctan(np.hypot(o1,o2)))
            worsened=(angle>35.0001)&(angle>oldangle+SETTINGS['slope_tolerance_deg'])
            bounded=bool(np.all(y>=-1e-6) and np.all(y<=capacity+2e-6))
            feasible=bounded and not worsened.any() and worst_depth_deficit<=SETTINGS['float_depth_tolerance_m']
            result.update(solver_success=bool(solved.success),message=str(solved.message),iterations=int(solved.nit),
                depth_rows=len(b),depth_max_deficit_m=worst_depth_deficit,new_or_worsened_faces=int(worsened.sum()),
                bounded=bounded,accepted_float32=bool(feasible))
            if feasible and np.any(new<startheights-1e-6):
                h.ravel()[variables]=new
                result.update(status='ACCEPTED_LOCAL_FEASIBLE',changed_vertices=int((new!=startheights).sum()),
                              max_additional_cut_m=float(y.max()))
            else:result['status']='RETAINED_SOURCE'
        except TimeBudget:
            result.update(status='RETAINED_SOURCE_TIME_BUDGET',iterations=iterations)
        result['seconds']=time.monotonic()-start
        results.append(result)
        save(a.out/f'group-{number:02d}.json',result)
        print(json.dumps({k:v for k,v in result.items() if k!='cases'},ensure_ascii=False),flush=True)
    h=h.astype('float32');changed=h!=t['heights']
    assert not (changed&fixed).any() and np.all(h<=initial+1e-6)
    np.savez_compressed(a.out/'terrain_v30.npz',**{k:h if k=='heights' else t[k] for k in t.files})
    with (a.out/'baltic_terrain_v30.asc').open('x',encoding='ascii',newline='\n') as stream:
        stream.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(stream,h,fmt='%.9g')
    inputs=[SOURCE,BASE,savedpath,casepath,water,streams,Path(__file__),Path(cell_planes.__code__.co_filename),
            Path(minimize.__code__.co_filename)]
    save(a.out/'build.json',dict(status='BUILT_PENDING_GROUPED_GATES' if changed.any() else 'NO_GEOMETRY_CHANGE',
        settings=SETTINGS,scipy_version=scipy.__version__,source_sha256=EXPECTED,
        candidate_sha256=sha(a.out/'terrain_v30.npz'),asc_sha256=sha(a.out/'baltic_terrain_v30.asc'),
        changed_vertices=int(changed.sum()),max_additional_cut_m=float((initial-h).max()),groups=results,
        inputs={str(p):sha(p) for p in inputs},
        limits=['One attempt per spatial group; skipped/rejected groups retain the source.',
                'No full continuity, native import, engine or navmesh acceptance.',
                'Water pieces remain those of the pond recovery because all non-height fields are identical.']))
    print(json.dumps(dict(changed_vertices=int(changed.sum()),accepted_groups=sum(r['status']=='ACCEPTED_LOCAL_FEASIBLE' for r in results)),indent=2))


if __name__=='__main__':main()
