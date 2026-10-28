"""Isolated candidate from sealed201 census. No terrain, water or deployed writes."""
import os,time
START=time.monotonic()
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
import argparse,importlib.util,json
import numpy as np
import shapely
from shapely import Polygon,Point,STRtree
HERE=Path(__file__).resolve().parent
def mod(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
solver=mod('solver',HERE/'dry_bed_road_solver_ev112.py');require=solver.require
ex=mod('exposure',HERE/'pilot_visible_exposure_ev112.py');g=ex.g
surface=mod('surface',HERE/'deployed_surface_inventory_ev112.py')
profile=mod('profiles',HERE/'pilot_bank_profiles_ev112.py')

def nz(path):
    with np.load(path,allow_pickle=False) as f:return {k:f[k] for k in f.files}

def strip(rows,cols=39):
    return np.array([(a,b,c) for i in range(rows-1) for j in range(cols-1)
        for a,b,c in ((i*cols+j,(i+1)*cols+j,(i+1)*cols+j+1),(i*cols+j,(i+1)*cols+j+1,i*cols+j+1))],int)

def local_water(a,low,high):
    """Complete broadphase over sealed A, preserving conditional geometry."""
    v,m,instances,catalog=a;water_ids=np.flatnonzero(np.isin(m['kind'],[1,2]));groups={};bounds={}
    for mid in np.unique(m['model'][water_ids]):
        fs=water_ids[m['model'][water_ids]==mid];groups[int(mid)]=fs
        vs=v[fs][np.arange(4)[None,:]<m['vertices'][fs,None]];lo,hi=vs.min(0),vs.max(0)
        bounds[int(mid)]=np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
    polygons=[];refs=[];vertices=[];count=0
    for ii,(mid,pose) in enumerate(zip(instances['model_index'],instances['matrix'])):
        if int(mid) not in groups:continue
        box=surface.transform(bounds[int(mid)],pose)[:,[0,2]]
        if np.any(box.max(0)<low) or np.any(box.min(0)>high):continue
        count+=1;fs=groups[int(mid)];world=surface.transform(v[fs],pose)
        for fi,points in zip(fs,world):
            n=int(m['vertices'][fi]);xz=points[:n][:,[0,2]]
            if np.any(xz.max(0)<low) or np.any(xz.min(0)>high):continue
            polygons.append(Polygon(xz).convex_hull);vertices.append(points)
            refs.append([int(instances['ids'][ii]),int(fi),n,int(m['flags'][fi])])
    return polygons,np.array(vertices),np.array(refs,dtype=np.int64),count

def local_corridor(xy,edges,low,high):
    rects=[];nodes=set();used=[]
    for ei,(a,b,_) in enumerate(edges):
        a,b=int(a),int(b);line=xy[[a,b]]
        if np.any(line.max(0)+4/np.cos(np.pi/64)<low) or np.any(line.min(0)-4/np.cos(np.pi/64)>high):continue
        rects.append(ex.rect(*line));nodes.update((a,b));used.append(ei)
    pieces=rects+[ex.disc_bounds(xy[i])[1] for i in sorted(nodes)]
    return shapely.union_all(pieces),used

def geometry_parts(shape):
    return [p for p in shapely.get_parts(shape) if p.geom_type=='Polygon' and p.area>0]

def samples_for(triangles,points,faces,parts,road):
    sf=[];weights=[];clearance=[];pieces=[]
    for fi in faces:
        for p in parts[int(fi)]:
            for cut in geometry_parts(Polygon(p['polygon']).intersection(road)):
                q=np.array(cut.exterior.coords)[:-1]
                w=solver.barycentric(points[triangles[fi]],q)
                cc=g.evaluate(p['bed_plane'],q)-g.evaluate(p['terrain_plane'],q)
                sf.extend([int(fi)]*len(q));weights.extend(w);clearance.extend(cc)
                pieces.append(dict(face=int(fi),cell=list(p['cell']),polygon=q.tolist()))
    return np.array(sf,int),np.asarray(weights).reshape(-1,3),np.array(clearance),pieces

def run(root,w,out,meter,preflight=False):
    pins={}
    def pin(path,expected=None):
        d=meter.sha(path)
        if expected is not None:require(d==expected,'changed_input:'+str(path))
        pins[str(path)]=d;return path
    def manifest(folder):
        path=pin(w/'evidence'/folder/'artifact-hashes.json');result=json.loads(path.read_bytes())
        return result
    aman=manifest('deployed-surface-prototypes-20261028');a=root/'deployed-surface-prototypes-20261028'
    for rel,d in aman.items():pin(root/rel,d['sha256'])
    av=nz(a/'surface-prototypes.npz');inst=nz(a/'instances.npz');catalog=json.loads((a/'model-catalog.json').read_bytes())
    require(len(inst['ids'])==17818 and len(av['meta'])==539009,'A_coverage')
    a_data=(av['vertices'],av['meta'],inst,catalog)
    raw=root/'pilot-visible-surface-extraction-20261028';man=manifest('pilot-visible-surface-20261028')
    path=raw/'models.json';models=json.loads(pin(path,man[path.relative_to(root).as_posix()]['sha256']).read_bytes())
    require(len(models)==201 and len({x['model'] for x in models})==201,'model_coverage')
    eraw=root/'pilot-visible-exposure-census-r2-20261028';em=manifest('pilot-visible-exposure-20261028')
    ep=eraw/'models.json';ems={x['model']:x for x in json.loads(pin(ep,em[ep.relative_to(root).as_posix()]['sha256']).read_bytes())}
    sources={};seed_by_model={};selection=[]
    for m in models:
        f=nz(pin(raw/m['file'],m['sha256']));sources[m['model']]=f
        ee=ems[m['model']];ef=nz(pin(eraw/ee['file'],ee['sha256']));fields=list(ef['fields'])
        ix=[fields.index(k) for k in ('corridor_rectangle_above_H_area','corridor_disc_inner_above_H_area','corridor_disc_uncertain_above_H_area')]
        seed=np.any(ef['metrics'][:,ix]>0,axis=1);seed_by_model[m['model']]=seed
        selection.append(dict(model=m['model'],site=m['site'],seed_faces=int(seed.sum())))
    require(sum(x['seed_faces'] for x in selection)>0,'empty_selection')
    hp=root/'river-kit7-merged-byteexact-20261026/terrain-buried.npz';h=nz(pin(hp,ex.H_SHA))['heights']
    fp=root/'river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz';f=nz(pin(fp,ex.FP_SHA));wp,wf=f['plane'],f['field']
    rp=w.parents[2]/'tests/regional_foundation_roads_v6/reference.npz';road=nz(pin(rp,ex.ROAD_SHA));xy,edges=road['xy'],road['edges'];ex.road_guard(xy,edges)
    require(np.all(np.bincount(edges[:,:2].astype(int).ravel(),minlength=len(xy))>0),'isolated_road_node_needs_disc')
    for p in (Path(__file__),HERE/'dry_bed_road_solver_ev112.py',HERE/'pilot_visible_exposure_ev112.py',HERE/'pilot_surface_refinement_ev112.py',HERE/'deployed_surface_inventory_ev112.py',HERE/'pilot_bank_profiles_ev112.py'):pin(p)
    meter.dump(out/'selection.json',selection);reports=[]
    for site in sorted({x['site'] for x in selection if x['seed_faces']}):
        items=[m for m in models if m['site']==site];starts={m['model']:int(sources[m['model']]['npz_start'])+8-int(sources[m['model']]['cap_before']) for m in items}
        rows=max(starts[m['model']]+len(sources[m['model']]['source_grid']) for m in items)
        grid=np.zeros((rows,39,3));seen=np.zeros(rows,bool);t=strip(rows);seed=np.zeros(len(t),bool);covered=np.zeros(len(t),int);owners=np.full((len(t),2),-1,int)
        for mi,m in enumerate(items):
            f=sources[m['model']];start=starts[m['model']];profile.attach_grid(grid,seen,start,f['source_grid'])
            require((f['bed_source_face']>=0).all() and (f['bed_source_face']<len(f['source_triangles'])).all(),'source_face_index')
            mapping=f['bed_source_face']+start*76
            require(np.array_equal(t[mapping]-start*39,f['source_triangles'][f['bed_source_face']]),'face_mapping')
            seed[mapping]=seed_by_model[m['model']];covered[mapping]+=1;owners[mapping]=np.c_[np.full(len(mapping),m['model_index']),np.arange(len(mapping))]
        require(seen.all() and (covered==1).all(),'site_topology_coverage')
        p=grid.reshape(-1,3);domain,distance=solver.local_domain(p,t,seed)
        candidate_faces=np.flatnonzero(np.any(domain[t],axis=1)|seed)
        box=p[np.unique(t[candidate_faces])][:,[0,2]];low,high=box.min(0),box.max(0)
        water,wv,wr,wcount=local_water(a_data,low,high);wtree=STRtree(water)
        corridor,road_ids=local_corridor(xy,edges,low,high)
        parts={};wet_faces=[];water_hits=[];native_hits=[];protected_faces=[]
        for fi in candidate_faces:
            tri=p[t[fi]];poly=Polygon(tri[:,[0,2]]);parts[int(fi)]=g.refine(tri,h,wp,wf)
            hits=[int(i) for i in wtree.query(poly,predicate='intersects')]
            native=any(float((q['terrain']-q['water']).min())<=0 for q in parts[int(fi)])
            if hits or native:wet_faces.append(int(fi))
            if hits:water_hits.append(dict(face=int(fi),water=hits))
            if native:native_hits.append(int(fi))
            if poly.distance(Point(10397.4,9421.9))<=60:protected_faces.append(int(fi))
        free=domain.copy();fixed_grid=np.zeros(grid.shape[:2],bool);fixed_grid[[0,-1]]=True
        qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25]);fixed_grid[:,abs(qs)<=4]=True
        free[fixed_grid.ravel()]=False
        if wet_faces:free[np.unique(t[wet_faces])]=False
        if protected_faces:free[np.unique(t[protected_faces])]=False
        sf,weights,clearance,cut_pieces=samples_for(t,p,candidate_faces,parts,corridor)
        wholly_fixed=(weights*free[t[sf]]).sum(1)==0;violations=np.flatnonzero(wholly_fixed&(clearance>1e-9))
        stem=site;np.savez_compressed(out/(stem+'-inputs.npz'),grid=grid,triangles=t,owners=owners,seed=seed,domain=domain,distance=distance,free=free,sample_faces=sf,weights=weights,clearance=clearance,wet_faces=np.asarray(wet_faces,int),native_hits=np.asarray(native_hits,int),protected_faces=np.asarray(protected_faces,int),water_vertices=wv,water_refs=wr)
        meter.dump(out/(stem+'-geometry.json'),dict(corridor=shapely.to_geojson(corridor),road_edges=road_ids,water_hits=water_hits,pieces=cut_pieces,model_rows=[dict(model=m['model'],index=m['model_index'],start=starts[m['model']],rows=len(sources[m['model']]['source_grid'])) for m in items]))
        report=dict(site=site,models=len(items),seed_faces=int(seed.sum()),candidate_faces=len(candidate_faces),free_vertices=int(free.sum()),water_faces=len(water),water_instances=wcount,wet_frozen_faces=len(wet_faces),samples=len(sf),fixed_conflict_samples=len(violations),maximum_fixed_conflict=float(clearance[violations].max()) if len(violations) else None)
        if len(violations):
            report['status']='INFEASIBLE_FIXED_SUPPORT';meter.dump(out/(stem+'-fixed-conflicts.json'),[dict(sample=int(j),face=int(sf[j]),bary=weights[j].tolist(),clearance=float(clearance[j]),source=owners[sf[j]].tolist(),fixed_vertices=t[sf[j]].tolist()) for j in violations])
        elif preflight:report['status']='PREFLIGHT_FEASIBLE_SUPPORT_ONLY'
        else:
            minimum=min(float(q['terrain'].min()) for plist in parts.values() for q in plist)
            candidate,result=solver.solve(p,t,free,sf,weights,clearance,support_minimum=minimum);report.update(result)
            if candidate is not None:
                np.savez_compressed(out/(stem+'-candidate.npz'),grid=candidate.reshape(grid.shape))
                modified=np.any((candidate[:,1]!=p[:,1])[t],axis=1)
                require(not np.any(modified[np.asarray(wet_faces,int)]),'modified_water_face')
                require(not np.any(modified[np.asarray(protected_faces,int)]),'modified_015_face')
                # Newly buried regions, for diagnosis rather than acceptance by area.
                buried=[];total=0.
                for fi in np.flatnonzero(modified):
                    for old,new in zip(parts[int(fi)],g.refine(candidate[t[fi]],h,wp,wf)):
                        positive=ex.polygon(g.sign_regions(old,'terrain')['above_polygon']);negative=ex.polygon(g.sign_regions(new,'terrain')['below_polygon'])
                        shape=positive.intersection(negative)
                        if shape.area>0:total+=float(shape.area);buried.append(dict(face=int(fi),geometry=shapely.to_geojson(shape)))
                report.update(changed_faces=int(modified.sum()),newly_buried_face_area_m2=total)
                meter.dump(out/(stem+'-newly-buried.json'),buried)
        reports.append(report);meter.dump(out/'progress.json',dict(sites=reports,measurement=meter.memory()))
    for p,d in pins.items():require(meter.sha(p)==d,'changed_after:'+p)
    meter.dump(out/'inputs.json',pins)
    return dict(status='PREFLIGHT_ONLY' if preflight else 'CANDIDATE_STAGE_COMPLETE_NOT_ACCEPTED',models_screened=201,sites=reports,measurement=meter.memory())

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('worktree',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--preflight',action='store_true');a=ap.parse_args();a.output.mkdir(exist_ok=False)
    meter=mod('meter',HERE/'water_constraint_diagnostic_ev112.py');meter.STARTED=START;meter.MAX_SECONDS=120 if a.preflight else 600;stop=meter.bounded(a.output)
    try:result=run(a.root,a.worktree,a.output,meter,a.preflight);meter.dump(a.output/'report.json',result);print(json.dumps(result))
    except Exception as error:meter.dump(a.output/'failure.json',dict(type=type(error).__name__,error=str(error),measurement=meter.memory()));raise
    finally:stop.set()
