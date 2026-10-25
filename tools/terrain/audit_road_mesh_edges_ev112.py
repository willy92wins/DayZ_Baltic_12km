"""Independent piecewise-linear extrema on native triangle edge crossings.

Same frozen P11 stations and exclusions. This strengthens transverse extrema
between the 17 legacy samples; exact native slopes on each adjacent eligible
centre-line segment are reported too. No physical road or visual acceptance.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_roads_v30 as legacy

def segment_breaks(a,b,step=6.):
    a,b=np.asarray(a,float),np.asarray(b,float)
    if a.shape!=(2,) or b.shape!=(2,) or not np.isfinite([a,b]).all():raise ValueError('invalid segment')
    ts=[0.,1.]
    for u,v in ((a[0],b[0]),(a[1],b[1]),(a.sum(),b.sum())):
        if abs(v-u)<1e-12:continue
        levels=np.arange(np.floor(min(u,v)/step)+1,np.ceil(max(u,v)/step))*step
        ts.extend(((levels-u)/(v-u)).tolist())
    t=np.unique(np.clip(ts,0,1));return t,a[None,:]+t[:,None]*(b-a)

def native(H,q):
    # Independent interpolation, north-up NW-SE. No clamp of outside points.
    c=q[:,0]/6;r=(12282-q[:,1])/6
    if ((c<0)|(r<0)|(c>H.shape[1]-1)|(r>H.shape[0]-1)).any():raise ValueError('point outside terrain')
    ci=np.minimum(np.floor(c).astype(int),H.shape[1]-2);ri=np.minimum(np.floor(r).astype(int),H.shape[0]-2)
    u=c-ci;v=r-ri;a=H[ri,ci];b=H[ri,ci+1];d=H[ri+1,ci];e=H[ri+1,ci+1]
    return np.where(u>=v,a+u*(b-a)+v*(e-b),a+v*(d-a)+u*(e-d))

def native_slopes(H,points):
    """Directional planar derivatives; avoid cancellation at almost-zero pieces."""
    delta=np.diff(points,axis=0);length=np.linalg.norm(delta,axis=1)
    ok=length>1e-9;mid=(points[:-1]+points[1:])[ok]/2
    c=mid[:,0]/6;r=(12282-mid[:,1])/6
    ci=np.minimum(np.floor(c).astype(int),H.shape[1]-2);ri=np.minimum(np.floor(r).astype(int),H.shape[0]-2)
    up=c-ci>=r-ri;a=H[ri,ci];b=H[ri,ci+1];d=H[ri+1,ci];e=H[ri+1,ci+1]
    gradient=np.column_stack((np.where(up,b-a,e-d),np.where(up,b-e,a-d)))/6
    return np.abs((gradient*delta[ok]/length[ok,None]).sum(axis=1))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('terrain',type=Path);ap.add_argument('water',type=Path);ap.add_argument('out',type=Path)
    ap.add_argument('--expected-coverage',required=True);a=ap.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    H=np.load(a.terrain)['heights'].astype(float);water=np.load(a.water)['wet']
    old=legacy.evaluate(H,water,a.expected_coverage)
    if not old['coverage_matches_reference']:raise ValueError('coverage differs from frozen P11 reference')
    wd=distance_transform_edt(~water)*6;fail=[];crossmax=grademax=0.;crosscount=gradecount=0
    for chain,p in enumerate(legacy.road_chains()):
        if len(p)<4:continue
        p=np.asarray(p);s0=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        s=np.linspace(0,s0[-1],int(np.ceil(s0[-1]))+1);q=np.column_stack([np.interp(s,s0,p[:,d]) for d in (0,1)])
        tan=np.gradient(q,axis=0);normal=np.column_stack([-tan[:,1],tan[:,0]])/np.linalg.norm(tan,axis=1)[:,None]
        rr=np.clip(np.rint((12282-q[:,1])/6).astype(int),0,2047);cc=np.clip(np.rint(q[:,0]/6).astype(int),0,2047)
        limits=legacy.LIMITS
        valid=(wd[rr,cc]>limits['water_clear_m'])&(np.linalg.norm(q-legacy.NARVA,axis=1)>limits['narva_clear_m'])&(s>limits['end_margin_m'])&(s<s0[-1]-limits['end_margin_m'])
        for i in np.flatnonzero(valid):
            _,points=segment_breaks(q[i]-normal[i]*4,q[i]+normal[i]*4)
            spread=float(np.ptp(native(H,points)));crossmax=max(crossmax,spread);crosscount+=1
            if spread>legacy.LIMITS['cross_m']+1e-10:fail.append(dict(check='cross',chain=chain,station_m=float(s[i]),x=float(q[i,0]),z=float(q[i,1]),value=spread))
        for i in np.flatnonzero(valid[:-1]&valid[1:]):
            # Include original GIS bends between neighbouring legacy stations.
            ss=np.r_[s[i],s0[(s0>s[i])&(s0<s[i+1])],s[i+1]]
            qq=np.column_stack([np.interp(ss,s0,p[:,d]) for d in (0,1)])
            for start,end,sa,sb in zip(qq[:-1],qq[1:],ss[:-1],ss[1:]):
                t,points=segment_breaks(start,end);length=np.linalg.norm(end-start)
                slopes=native_slopes(H,points);g=float(slopes.max());grademax=max(grademax,g);gradecount+=len(slopes)
                if g>legacy.LIMITS['grade']+1e-10:fail.append(dict(check='grade',chain=chain,station_m=float(sa),x=float(start[0]),z=float(start[1]),value=g))
    assert crosscount==old['samples'],'native consumer station coverage diverged'
    report=dict(status='OFFLINE_MESH_PASS' if crosscount and gradecount and not fail else 'FAIL',
        coverage_sha256=old['coverage_sha256'],cross_sections=crosscount,grade_intervals=gradecount,
        cross_max_m=crossmax,grade_max=grademax,failures=fail,failure_count=len(fail),
        inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.terrain,a.water,Path(__file__),Path(legacy.__file__))},
        limits=['Exact transverse extrema only at frozen P11 stations; not every longitudinal cross-section.',
                'Exact native slopes on eligible centreline; P11 chord remains measured by the legacy judge.',
                'Wet/Narva/end exclusions remain pending; no physical roads, driving or visual verdict.'])
    a.out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('failures','inputs','limits')},indent=2))
    raise SystemExit(0 if report['status']=='OFFLINE_MESH_PASS' else 1)

if __name__=='__main__':main()
