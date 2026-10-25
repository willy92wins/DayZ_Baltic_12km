"""Revisit the frozen EV44 dry-centre stations against EV95; never edit terrain."""
from pathlib import Path
import hashlib, json, csv
import numpy as np

R = Path('E:/DayZ-Baltic-Build')
G = R / 'v30-global-bank-extension-20261010'
HERE = Path(__file__).resolve().parent
ATTR = R / 'v30-crossing-attribution-20261009/attribution.json'
EXACT = R / 'v30-hydro-design-census-20261009/exact-sections.json'
CENSUS = EXACT.with_name('census.json')
PROFILES = R / 'v30-v11/design/profiles.npz'
H = G / 'global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz'
P = G / 'build-focal/candidate/plane.npy'
F = G / 'build-focal/candidate/visible-field.npy'
EXPECTED = {H:'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
 P:'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 F:'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def require(ok, message):
    if not ok: raise RuntimeError(message)

def sample(h,p,f,q):
    cx=q[:,0]/6.; ry=(12282.-q[:,1])/6.
    c=np.floor(cx).astype(int);r=np.floor(ry).astype(int)
    require(np.all((r>=0)&(c>=0)&(r<h.shape[0]-1)&(c<h.shape[1]-1)), 'point outside native cells')
    a=cx-c;b=ry-r; upper=a>=b
    # Cast corner values before differences: interpolate native float32 heights in float64.
    nw=h[r,c].astype(float);ne=h[r,c+1].astype(float)
    sw=h[r+1,c].astype(float);se=h[r+1,c+1].astype(float)
    ground=np.where(upper,(1-a)*nw+(a-b)*ne+b*se,(1-b)*nw+(b-a)*sw+a*se)
    corners=f[r,c].astype(float)
    visible=np.where(upper,(1-a)*corners[:,0]+(a-b)*corners[:,1]+b*corners[:,3],
                    (1-b)*corners[:,0]+(b-a)*corners[:,2]+a*corners[:,3])
    physical=p[r,c].astype(float)
    return ground,physical,visible,r,c

def fixtures():
    rr,cc=np.indices((3,3));h=(12*cc+18*rr+5).astype(np.float32)
    p=np.full((2,2),100.);f=np.full((2,2,4),100.)
    q=np.array([[1.,12277.],[5.,12281.],[7.,12280.],[10.,12271.]])
    ground,physical,visible,_,_=sample(h,p,f,q)
    require(np.allclose(ground,2*q[:,0]+3*(12282-q[:,1])+5,rtol=0,atol=1e-11),'analytic triangle fixture')
    require(np.all(physical==100)&np.all(visible==100),'constant plane fixture')
    p[0,0]=np.nan;f[0,0]=np.nan
    _,physical,visible,_,_=sample(h,p,f,q)
    require(np.all(np.isnan(physical[:2])) and np.all(np.isnan(visible[:2])), 'absent plane must remain absent')
    require(np.all(np.isfinite(physical[2:])), 'negative must not remove other cells')

def main():
    fixtures()
    out=HERE/'run-01';require(not out.exists(),'create-only output exists')
    json_bytes={p:p.read_bytes() for p in (ATTR,EXACT,CENSUS)}
    attr=json.loads(json_bytes[ATTR]);exact=json.loads(json_bytes[EXACT]);census=json.loads(json_bytes[CENSUS])
    parsed_json_sha={p:hashlib.sha256(data).hexdigest() for p,data in json_bytes.items()}
    inherited={Path(p):digest for p,digest in attr['inputs'].items()}
    expected_inputs={**inherited,**EXPECTED,PROFILES:census['profile_sha256']}
    paths=[*inherited,*EXPECTED,PROFILES,ATTR,CENSUS,Path(__file__)]
    start={str(p):sha(p) for p in paths}
    for p,digest in expected_inputs.items():
        require(start[str(p)]==digest, f'input drift: {p}')
    for p,digest in parsed_json_sha.items():
        require(start[str(p)]==digest, f'JSON changed since parsing: {p}')
    old_h_path=next(p for p in inherited if p.name=='terrain.npz')
    old_p_path=next(p for p in inherited if p.name=='plane.npy')
    old_f_path=next(p for p in inherited if p.name=='preserved-field.npy')
    with np.load(old_h_path,allow_pickle=False) as z: old_h=z['heights']
    with np.load(H,allow_pickle=False) as z: h=z['heights']
    old_p=np.load(old_p_path,mmap_mode='r');old_f=np.load(old_f_path,mmap_mode='r')
    p=np.load(P,mmap_mode='r');f=np.load(F,mmap_mode='r')
    rows=[];points=[]
    frozen={(x['id'],x['start_s'],x['end_s']):x for x in attr['rows']}
    with np.load(PROFILES,allow_pickle=False) as profiles:
        for alarm in exact['rows']:
            if alarm['status']!='EXACT_DRY_CONFIRMED':continue
            gap=alarm['original_gap'];key=(gap['id'],gap['start_s'],gap['end_s']);original=frozen[key]
            a=profiles[gap['id']];station=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(a[:,1:3],axis=0),axis=1))]
            ss=np.arange(max(station[0],gap['start_s']-2),min(station[-1],gap['end_s']+2)+.01,.25)
            require(len(ss)==alarm['sections'],'frozen station count differs')
            dry=np.zeros(len(ss),bool)
            for begin,end,_ in alarm['physical_dry_intervals']:dry[begin:end+1]=True
            s=ss[dry];q=np.c_[np.interp(s,station,a[:,1]),np.interp(s,station,a[:,2])]
            require(len(q)==original['dry_stations'],'frozen dry cohort differs')
            old_g,old_level,old_vis,_,_=sample(old_h,old_p,old_f,q)
            require(np.all(~np.isfinite(old_level)|(old_level-old_g<=.011)),'historical cohort no longer replays dry')
            ground,level,visible,rr,cc=sample(h,p,f,q)
            depth=level-ground;vdepth=visible-ground
            no_p=~np.isfinite(level);no_f=~np.isfinite(visible)
            counts=dict(no_physical_plane=int(no_p.sum()),physical_above_ground=int(np.count_nonzero(~no_p&(depth>0))),
                        physical_depth_over_1cm=int(np.count_nonzero(~no_p&(depth>.01))),
                        no_visible_field=int(no_f.sum()),visible_above_ground=int(np.count_nonzero(~no_f&(vdepth>0))))
            rows.append(dict(id=key[0],start_s=key[1],end_s=key[2],stations=len(q),**counts,
                             max_physical_depth_m=float(depth[~no_p].max()) if np.any(~no_p) else None,
                             ground_change_max_abs_m=float(np.max(np.abs(ground-old_g))),
                             all_centre_stations_wet_over_1cm=counts['physical_depth_over_1cm']==len(q)))
            for i in range(len(q)):
                points.append(dict(id=key[0],gap_start_s=key[1],s=float(s[i]),x=float(q[i,0]),z=float(q[i,1]),
                  r=int(rr[i]),c=int(cc[i]),old_ground=float(old_g[i]),ground=float(ground[i]),
                  physical_depth=None if no_p[i] else float(depth[i]),visible_depth=None if no_f[i] else float(vdepth[i])))
    require(len(rows)==45 and len(points)==4592,'frozen population must be 45 / 4592')
    finish={str(path):sha(path) for path in paths};require(start==finish,'inputs changed during audit')
    report=dict(status='CURRENT_CENTRE_STATION_DIAGNOSIS_NOT_CROSSING_ACCEPTANCE',terrain_sha256=EXPECTED[H],
       rows=rows,totals={key:sum(row[key] for row in rows) for key in counts},crossings=len(rows),stations=len(points),
       fully_wet_centre_cohorts=sum(row['all_centre_stations_wet_over_1cm'] for row in rows),
       inputs_start=start,inputs_end=finish,readset_equal=True,
       controls=['analytic_plane_both_native_triangles','constant_P_F','missing_plane_remains_missing','historical_4592_station_replay'],
       limitations=['Only the frozen 4592 centre stations; no full-width or longitudinal route acceptance.',
        'P/F are the current analytical fields, not a new enumeration of compiled ODOL faces or native water flags.',
        'Does not classify intentional fords/culverts, repair a road reserve, or explain gray render rectangles.',
        'ATTR and CENSUS are live evidence snapshots hashed with their parsed bytes; the profile is linked by the census hash field, not by a separate signed approval.'])
    out.mkdir()
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    with (out/'stations.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(points[0]));writer.writeheader();writer.writerows(points)
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','inputs_start','inputs_end','limitations')},indent=2))

if __name__=='__main__':main()
