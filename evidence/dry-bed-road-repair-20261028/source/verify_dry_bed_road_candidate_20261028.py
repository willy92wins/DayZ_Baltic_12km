"""Independent GEOS/native consumer. Never imports candidate or solver/refiner."""
import os,time
START=time.monotonic()
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import argparse,hashlib,heapq,json,math,importlib.util
import numpy as np
import shapely
from shapely import Polygon,Point,STRtree

def require(ok,why):
    if not bool(ok):raise ValueError(why)
def nz(path):
    with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def native_parts(tri,h,wp,wf):
    footprint=Polygon(tri[:,[0,2]]);low=np.floor(footprint.bounds[:2]).astype(int);high=np.ceil(footprint.bounds[2:]).astype(int);top=(len(h)-1)*6
    for r in range(max(0,int((top-high[1])//6)),min(len(h)-2,int((top-low[1])//6))+1):
        for c in range(max(0,int(low[0]//6)),min(len(h)-2,int(high[0]//6))+1):
            corners=np.array([[c*6,top-r*6],[(c+1)*6,top-r*6],[c*6,top-(r+1)*6],[(c+1)*6,top-(r+1)*6]],float)
            heights=np.array([h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]],float)
            water=wf[r,c] if np.isfinite(wp[r,c]) else np.ones(4)*.75
            for ids in ([0,1,3],[0,2,3]):
                base=corners[ids];cut=footprint.intersection(Polygon(base))
                if cut.area>0:yield cut,base,heights[ids],water[ids]
def interp(xz,y,points):
    uv=np.linalg.solve((xz[1:]-xz[0]).T,(np.asarray(points)-xz[0]).T).T
    return y[0]+uv@(y[1:]-y[0])
def clip_sign(points,values):
    out=[]
    for j,a in enumerate(points):
        k=(j+1)%len(points);b=points[k];va,vb=values[j],values[k]
        if va>=0:out.append(a)
        if va*vb<0:out.append((vb*a-va*b)/(vb-va))
    return Polygon(out) if len(out)>=3 else Polygon()
def perimeter_corridor(xy,edges,lo,hi):
    ab=xy[edges[:,:2].astype(int)];radius=4/math.cos(math.pi/64)
    take=(np.all(ab.max(1)+radius>=lo,axis=1)&np.all(ab.min(1)-radius<=hi,axis=1));polys=[]
    for a,b in ab[take]:
        d=b-a;d=np.array([-d[1],d[0]])*(4/np.linalg.norm(d));polys.append(Polygon([a+d,b+d,b-d,a-d]))
    for node in np.unique(edges[take,:2].astype(int)):
        angles=np.arange(64)*math.tau/64;polys.append(Polygon(xy[node]+radius*np.c_[np.cos(angles),np.sin(angles)]))
    return shapely.union_all(polys)
def domain(points,t,seeds):
    adjacency=[{} for _ in points]
    for tri in t:
        for a,b in zip(tri,np.roll(tri,-1)):
            length=float(np.linalg.norm(points[a,[0,2]]-points[b,[0,2]]));adjacency[a][int(b)]=length;adjacency[b][int(a)]=length
    dist=np.full(len(points),np.inf);starts=np.unique(t[seeds]);queue=[]
    for i in starts:dist[i]=0.;heapq.heappush(queue,(0.,int(i)))
    while queue:
        d,i=heapq.heappop(queue)
        if d!=dist[i]:continue
        for j,length in adjacency[i].items():
            nd=d+length
            if nd<=12 and nd<dist[j]:dist[j]=nd;heapq.heappush(queue,(nd,j))
    return dist<12
def actual_water(root,lo,hi):
    a=root/'deployed-surface-prototypes-20261028';z=nz(a/'surface-prototypes.npz');instances=nz(a/'instances.npz');v,m=z['vertices'],z['meta'];polys=[];refs=[]
    for model in np.unique(m['model'][np.isin(m['kind'],[1,2])]):
        fs=np.flatnonzero((m['model']==model)&np.isin(m['kind'],[1,2]));flat=v[fs][np.arange(4)[None,:]<m['vertices'][fs,None]];center=(flat.min(0)+flat.max(0))/2;extent=(flat.max(0)-flat.min(0))/2
        for ii in np.flatnonzero(instances['model_index']==model):
            pose=instances['matrix'][ii];matrix=pose[:9].reshape(3,3);wc=center@matrix+pose[9:];we=extent@abs(matrix)
            if np.any((wc+we)[[0,2]]<lo) or np.any((wc-we)[[0,2]]>hi):continue
            for fi in fs:
                n=int(m['vertices'][fi]);world=np.einsum('ij,jk->ik',v[fi,:n],matrix)+pose[9:];xz=world[:,[0,2]]
                if np.any(xz.max(0)<lo) or np.any(xz.min(0)>hi):continue
                polys.append(Polygon(xz).convex_hull);refs.append((int(instances['ids'][ii]),int(fi),n,int(m['flags'][fi])))
    return polys,refs

def verify(root,w,raw,out,meter):
    pins=json.loads((raw/'inputs.json').read_bytes())
    artifact_pins={str(p):sha(p) for p in raw.iterdir() if p.suffix in ('.json','.npz')}
    artifact_pins[str(Path(__file__))]=sha(Path(__file__))
    for path,d in pins.items():require(sha(path)==d,'input_changed:'+path)
    # Independent sealed references, not a producer-supplied seed/coverage claim.
    for name in ('pilot-visible-surface-20261028','pilot-visible-exposure-20261028','deployed-surface-prototypes-20261028'):
        for rel,row in json.loads((w/'evidence'/name/'artifact-hashes.json').read_bytes()).items():
            p=root/rel
            if str(p) in pins:require(sha(p)==row['sha256'],'sealed_input_changed:'+rel)
    sr=root/'pilot-visible-surface-extraction-20261028';models=json.loads((sr/'models.json').read_bytes());er=root/'pilot-visible-exposure-census-r2-20261028';em={m['model']:m for m in json.loads((er/'models.json').read_bytes())}
    require(len(models)==len(em)==201,'model_universe')
    selected={};expected_selection=[]
    for m in models:
        record=em[m['model']];require(sha(er/record['file'])==record['sha256'],'census_changed')
        f=nz(er/record['file']);names=list(f['fields']);indices=[names.index(k) for k in ('corridor_rectangle_above_H_area','corridor_disc_inner_above_H_area','corridor_disc_uncertain_above_H_area')]
        seed=np.any(f['metrics'][:,indices]>0,axis=1);selected[m['model']]=seed
        expected_selection.append(dict(model=m['model'],site=m['site'],seed_faces=int(seed.sum())))
    require(json.loads((raw/'selection.json').read_bytes())==expected_selection,'selection_mismatch')
    sites={m['site'] for m in models if selected[m['model']].any()};report=json.loads((raw/'report.json').read_bytes());require({x['site'] for x in report['sites']}==sites,'site_omitted')
    h=nz(root/'river-kit7-merged-byteexact-20261026/terrain-buried.npz')['heights'];water=nz(root/'river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz');wp,wf=water['plane'],water['field'];road=nz(w.parents[2]/'tests/regional_foundation_roads_v6/reference.npz');xy,edges=road['xy'],road['edges'];results=[]
    for site in sorted(sites):
        f=nz(raw/(site+'-inputs.npz'));candidate=nz(raw/(site+'-candidate.npz'))['grid'];grid=f['grid'];rows=len(grid);t=np.array([[i*39+j,(i+1)*39+j,(i+1)*39+j+1] if k==0 else [i*39+j,(i+1)*39+j+1,i*39+j+1] for i in range(rows-1) for j in range(38) for k in range(2)])
        require(np.array_equal(t,f['triangles']),'triangles_changed');seed=np.zeros(len(t),bool);seen=np.zeros(len(t),int);owners=np.full((len(t),2),-1,int)
        for m in models:
            if m['site']!=site:continue
            require(sha(sr/m['file'])==m['sha256'],'source_model_changed');src=nz(sr/m['file']);start=int(src['npz_start'])+8-int(src['cap_before']);n=len(src['source_grid']);require(np.array_equal(grid[start:start+n],src['source_grid']),'assembly_changed')
            mapping=src['bed_source_face']+start*76;seed[mapping]=selected[m['model']];seen[mapping]+=1;owners[mapping]=np.c_[np.full(len(mapping),m['model_index']),np.arange(len(mapping))]
        require((seen==1).all() and np.array_equal(owners,f['owners']) and np.array_equal(seed,f['seed']),'face_or_seed_identity')
        p=grid.reshape(-1,3);new=candidate.reshape(-1,3);require(candidate.shape==grid.shape and np.isfinite(candidate).all(),'candidate_shape');require(np.array_equal(p[:,[0,2]],new[:,[0,2]]) and (new[:,1]<=p[:,1]).all(),'XZ_or_raised')
        domain_mask=domain(p,t,seed);require(np.array_equal(domain_mask,f['domain']),'domain_mismatch');faces=np.flatnonzero(np.any(domain_mask[t],axis=1)|seed);box=p[np.unique(t[faces])][:,[0,2]];lo,hi=box.min(0),box.max(0)
        shapes,refs=actual_water(root,lo,hi);require(set(refs)==set(map(tuple,f['water_refs'].tolist())),'water_inventory_omitted');tree=STRtree(shapes);corridor=perimeter_corridor(xy,edges,lo,hi)
        free=domain_mask.copy();fixed=np.zeros(grid.shape[:2],bool);fixed[[0,-1]]=True;qs=np.unique(np.r_[np.arange(-18,19),-2.25,2.25]);fixed[:,abs(qs)<=4]=True;free[fixed.ravel()]=False
        wet=[];protected=[];native=[];parts={}
        for fi in faces:
            tri=p[t[fi]];poly=Polygon(tri[:,[0,2]]);parts[int(fi)]=list(native_parts(tri,h,wp,wf));wet_native=False
            require(abs(sum(c.area for c,*_ in parts[int(fi)])-poly.area)<=1e-7,'native_area_gap')
            for cut,base,hh,ww in parts[int(fi)]:
                pts=np.asarray(cut.exterior.coords)[:-1]
                if (interp(base,hh,pts)-interp(base,ww,pts)).min()<=0:wet_native=True
            if wet_native:native.append(int(fi))
            if len(tree.query(poly,predicate='intersects')) or wet_native:wet.append(int(fi))
            if poly.distance(Point(10397.4,9421.9))<=60:protected.append(int(fi))
        if wet:free[np.unique(t[wet])]=False
        if protected:free[np.unique(t[protected])]=False
        require(np.array_equal(free,f['free']) and np.array_equal(wet,f['wet_faces']) and np.array_equal(native,f['native_hits']),'free_or_wet_mismatch')
        require(np.array_equal(p[~free],new[~free]),'fixed_point_changed');changed=new[:,1]!=p[:,1];require(changed.any(),'empty_candidate');require(np.array_equal(new[changed,1]*512,np.floor(new[changed,1]*512)),'quantization')
        minimum=min(float(interp(base,hh,np.asarray(cut.exterior.coords)[:-1]).min()) for plist in parts.values() for cut,base,hh,ww in plist)
        floor=float(np.floor((minimum-.03)*512)/512);require((new[changed,1]>=floor).all(),'descent_envelope_exceeded')
        modified=np.any(changed[t],axis=1);require(not np.any(modified[np.asarray(wet,int)]) and not np.any(modified[np.asarray(protected,int)]),'protected_face_changed')
        maximum=-math.inf;checked=0;new_buried=0.;baseline_area=0.;candidate_area=0.
        for fi in np.flatnonzero(modified|seed):
            for cut,base,hh,ww in parts[int(fi)]:
                points=np.asarray(cut.exterior.coords)[:-1];native_h=interp(base,hh,points);old_d=interp(p[t[fi]][:,[0,2]],p[t[fi],1],points)-native_h;new_d=interp(new[t[fi]][:,[0,2]],new[t[fi],1],points)-native_h
                above=clip_sign(points,old_d);below=clip_sign(points,-new_d);new_buried+=above.intersection(below).area
                road_cut=cut.intersection(corridor)
                for rc in shapely.get_parts(road_cut):
                    if rc.geom_type!='Polygon' or rc.area==0:continue
                    v=np.asarray(rc.exterior.coords)[:-1];d=interp(new[t[fi]][:,[0,2]],new[t[fi],1],v)-interp(base,hh,v)
                    maximum=max(maximum,float(d.max()));checked+=len(v);candidate_area+=clip_sign(v,d).area
                baseline_area+=above.intersection(corridor).area
        require(checked>0 and maximum<=1e-9 and candidate_area<=1e-7,'corridor_still_exposed')
        result=dict(site=site,changed_vertices=int(changed.sum()),changed_faces=int(modified.sum()),checked_points=checked,maximum_corridor_B_H=maximum,baseline_exposed_corridor_area=baseline_area,candidate_exposed_corridor_area=candidate_area,newly_buried_area=new_buried,actual_water_faces=len(refs),wet_frozen_faces=len(wet))
        declared=next(x for x in report['sites'] if x['site']==site);require(abs(new_buried-declared['newly_buried_face_area_m2'])<=1e-7,'buried_area_mismatch');results.append(result)
    for path,d in pins.items():require(sha(path)==d,'input_changed_after:'+path)
    for path,d in artifact_pins.items():require(sha(path)==d,'artifact_changed_after:'+path)
    meter.dump(out/'artifact-pins.json',artifact_pins)
    return dict(status='DRY_BED_ROAD_CANDIDATE_INDEPENDENTLY_VERIFIED',models=201,sites=results,measurement=meter.memory(),limitations=['Numerical bed candidate only. No MLOD, collision, engine or visual acceptance. Native water nominal; waves unverified.'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('worktree',type=Path);ap.add_argument('raw',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(exist_ok=False)
    sp=importlib.util.spec_from_file_location('meter',a.worktree/'tools/quality/water_constraint_diagnostic_ev112.py');meter=importlib.util.module_from_spec(sp);sp.loader.exec_module(meter);meter.STARTED=START;meter.MAX_SECONDS=600;stop=meter.bounded(a.output)
    try:result=verify(a.root,a.worktree,a.raw,a.output,meter);meter.dump(a.output/'report.json',result);print(json.dumps(result))
    except Exception as e:meter.dump(a.output/'failure.json',dict(type=type(e).__name__,error=str(e),measurement=meter.memory()));raise
    finally:stop.set()
