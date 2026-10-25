"""Sample approved river/stream profile axes against the native physical surface.

This is a profile self-consistency diagnostic, not independent proof or a
boatability claim. Offsets and 5 cm depth are measured in addition to a wet axis.
Planned road crossing platforms/reservations and their triangle halo are separate.
"""
from pathlib import Path
import argparse
import json

import numpy as np
import shapely
from shapely.geometry import shape

from audit_fairway_triangles_v30 import sha,save
from v30_common import cell_planes,tri_sample

ROOT=Path(__file__).resolve().parents[2]


def runs(mask,s,q,depth,covered,engineered):
    edges=np.diff(np.r_[False,mask,False].astype(int))
    result=[]
    for a,b in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)):
        result.append(dict(start_m=float(s[a]),end_m=float(s[b-1]),length_m=float(s[b-1]-s[a]+.5),
                           xz=q[(a+b-1)//2].tolist(),worst_depth_m=float(depth[a:b].min()),
                           no_plane_samples=int((~covered[a:b]).sum()),
                           engineering_samples=int(engineered[a:b].sum())))
    return sorted(result,key=lambda r:-r['length_m'])


def line_diagnostic(q,s,polygon,h,planes,fixed):
    inworld=(q[:,0]>0)&(q[:,0]<12282)&(q[:,1]>0)&(q[:,1]<12282)
    inside=shapely.contains_xy(polygon,q[:,0],q[:,1])&inworld
    rr=np.clip(np.floor((12282-q[:,1])/6).astype(int),0,2046)
    cc=np.clip(np.floor(q[:,0]/6).astype(int),0,2046)
    pond=planes[rr,cc];ground=tri_sample(h,q[:,0],q[:,1])
    depth=np.maximum(.5,np.nan_to_num(pond,nan=-np.inf))-ground
    fixed_weight=np.clip(tri_sample(fixed,q[:,0],q[:,1]),0,1)
    engineering_any=fixed_weight>1e-8
    engineering_full=fixed_weight>=1-1e-8
    engineering_halo=engineering_any&~engineering_full
    dry=inside&(depth<=0)
    shallow=inside&(depth<.05-1e-5)
    breaks=runs(dry&~engineering_any,s,q,depth,np.isfinite(pond),engineering_any)
    shallow_breaks=runs(shallow&~engineering_any,s,q,depth,np.isfinite(pond),engineering_any)
    return dict(inside_design_samples=int(inside.sum()),outside_design_samples=int((~inside).sum()),
                dry_samples=int(dry.sum()),dry_unreserved_samples=int((dry&~engineering_any).sum()),
                engineering_dry_samples=int((dry&engineering_any).sum()),
                engineering_full_dry_samples=int((dry&engineering_full).sum()),
                engineering_halo_dry_samples=int((dry&engineering_halo).sum()),
                below_5cm_samples=int(shallow.sum()),below_5cm_unreserved_samples=int((shallow&~engineering_any).sum()),
                engineering_halo_below_5cm_samples=int((shallow&engineering_halo).sum()),
                unreserved_breaks=breaks,unreserved_breaks_over_6m=sum(b['length_m']>=6 for b in breaks),
                below_5cm_unreserved_breaks=shallow_breaks,
                below_5cm_unreserved_breaks_over_6m=sum(b['length_m']>=6 for b in shallow_breaks))


def summarize(group):
    return dict(profiles=len(group),sampled_km=sum(r['inside_design_samples'] for r in group)*.5/1000,
                dry_km=sum(r['dry_samples'] for r in group)*.5/1000,
                dry_unreserved_km=sum(r['dry_unreserved_samples'] for r in group)*.5/1000,
                engineering_full_dry_km=sum(r['engineering_full_dry_samples'] for r in group)*.5/1000,
                engineering_halo_dry_km=sum(r['engineering_halo_dry_samples'] for r in group)*.5/1000,
                below_5cm_km=sum(r['below_5cm_samples'] for r in group)*.5/1000,
                below_5cm_unreserved_km=sum(r['below_5cm_unreserved_samples'] for r in group)*.5/1000,
                engineering_halo_below_5cm_km=sum(r['engineering_halo_below_5cm_samples'] for r in group)*.5/1000,
                breaks_over_6m=sum(r['unreserved_breaks_over_6m'] for r in group),
                below_5cm_breaks_over_6m=sum(r['below_5cm_unreserved_breaks_over_6m'] for r in group))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();assert not a.out.exists()
    water=ROOT/'tests/water_v3/water_v3.geojson';streams=ROOT/'tests/water_v3/streams_candidates.geojson'
    profpath=ROOT/'tests/water_v3/profiles.npz'
    feats=[f for f in json.loads(water.read_text())['features'] if f['properties']['class']=='river']
    feats+=[f for f in json.loads(streams.read_text())['features'] if f['properties']['tier_m']>=2500]
    profiles=np.load(profpath);t=np.load(a.candidate)
    h=t['heights'].astype(float);planes=cell_planes(t['cls'],t['level'])
    fixed=(t['platform']|t['reserve']).astype(float)
    rows=[];missing=[]
    for f in feats:
        prop=f['properties'];key=prop.get('id')
        if key not in profiles.files:
            missing.append(prop);continue
        p=profiles[key][:,1:3]
        st=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        s=np.arange(0,st[-1]+1e-7,.5)
        q=np.column_stack([np.interp(s,st,p[:,i]) for i in (0,1)])
        polygon=shape(f['geometry'])
        tangent=np.gradient(q,axis=0)
        length=np.linalg.norm(tangent,axis=1)
        if np.any(length<1e-9):raise ValueError(f'Degenerate profile tangent: {key}')
        normal=np.column_stack((-tangent[:,1],tangent[:,0]))/length[:,None]
        center=line_diagnostic(q,s,polygon,h,planes,fixed)
        offsets=[dict(offset_m=off,**line_diagnostic(q+off*normal,s,polygon,h,planes,fixed)) for off in (-.5,.5)]
        rows.append(dict(id=key,name=prop.get('name',''),**{'class':prop['class']},
                         length_m=float(st[-1]),**center,offsets=offsets))
    summary={}
    for code in ('river','stream'):
        group=[r for r in rows if r['class']==code]
        summary[code]=summarize(group)
        summary[code]['offsets']=[dict(offset_m=off,**summarize([r['offsets'][i] for r in group])) for i,off in enumerate((-.5,.5))]
    result=dict(status='MEASURED_OFFLINE_PROFILE_SELF_CONSISTENCY',terrain_sha256=sha(a.candidate),
                sources={str(p):sha(p) for p in (water,streams,profpath)},
                code={str(p):sha(p) for p in (Path(__file__),Path(cell_planes.__code__.co_filename))},
                schema_version=2,step_m=.5,sea_level_m=.5,target_depth_m=.05,depth_tolerance_m=1e-5,
                summary=summary,profiles=rows,polygon_only_without_profile=missing,
                limits=['Native triangle prediction only; no engine, water material or navigation acceptance.',
                        'Road platform and crossing masks identify planned engineered interruptions; neither bridges nor culverts are placed here.',
                        'Six metres is a diagnostic reporting bin, not a replacement of an approved product criterion.',
                        'The axes are shared with the builder: this is self-consistency, not an independent physical consumer.',
                        'Axis offsets are clipped to approved polygons; polygon-only rivers need separate coverage.',
                        'The engineering halo is any mixed native triangle touching a fixed vertex; its dry length is explicit.',
                        'Three sampled lines do not prove every point of the one-metre strip. Exact extrema remain a separate producer diagnostic.'])
    save(a.out,result)
    print(json.dumps(dict(summary=summary,polygon_only_without_profile=len(missing),
                         worst=sorted([dict(id=r['id'],name=r['name'],**b) for r in rows for b in r['unreserved_breaks']],key=lambda b:-b['length_m'])[:12]),indent=2,ensure_ascii=False))


if __name__=='__main__':main()
