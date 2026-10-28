"""Profiles and previous dry-pilot exclusions for all sealed201models. No map changes."""
import os,time
STARTED=time.monotonic()
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import argparse,collections,importlib.util,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('profiles',HERE/'pilot_bank_profiles_ev112.py');require=g.require
meta=module('meta',HERE/'pilot_visible_surface_ev112.py')
CANDIDATE_SHA='1e85c73f2232e4d5f60d7f745b7d7a1cabb3c878efb543a4f9146b517faf7c85'
REQUIRED=('reserve','platform','narva','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_causeway','v31_shore_ramp')
OPTIONAL=('v31_road_repair','v31_road_mesh_repair','v31_continuous_pilot')
CLASSES=('ALL_DRY_PILOT_EXCLUDED','MIXED','ALL_POINT_FREE')

def load_npz(path):
    with np.load(path,allow_pickle=False) as f:return {k:f[k] for k in f.files}

def inputs(root,w,meter):
    pins={}
    def pin(path,digest=None):
        path=Path(path);actual=meter.sha(path)
        if digest:require(actual==digest,'input_changed:'+str(path))
        pins[str(path)]=actual;return path
    manifest_path=pin(w/'evidence/pilot-visible-surface-20261028/artifact-hashes.json')
    manifest=json.loads(manifest_path.read_bytes());raw=root/'pilot-visible-surface-extraction-20261028'
    mpath=pin(raw/'models.json',manifest[(raw/'models.json').relative_to(root).as_posix()]['sha256'])
    models=json.loads(mpath.read_bytes());require(collections.Counter(m['site'] for m in models)==meta.SITES,'coverage_sites')
    require(len(models)==len({m['model'] for m in models})==201,'coverage_models')
    for m in models:pin(raw/m['file'],m['sha256'])
    arrays={site:load_npz(pin(root/rel,digest)) for site,(rel,digest) in meta.ARRAYS.items()}
    candidate=load_npz(pin(root/'dry-bank-visual-water-pilot-20261027/candidate-surfaces.npz',CANDIDATE_SHA))
    g.candidate_guard(arrays['kit-7'],candidate,'kit-7')
    candidate_report=json.loads(pin(root/'dry-bank-visual-water-pilot-20261027/author-report.json').read_bytes())
    require(candidate_report['candidate_sha256']==CANDIDATE_SHA,'candidate_report_identity')
    solver=candidate_report['solver'];require(isinstance(solver['success'],bool) and solver['bounds_satisfied'],'solver_metadata')
    context=json.loads(pin(root/'dry-bank-visual-water-setup-20261027/context.json').read_bytes())
    source=context['paths'];oldpins=context['hashes']
    base=load_npz(pin(source['base'],oldpins[source['base']]))
    h=load_npz(pin(source['support'],oldpins[source['support']]))['heights'].astype(float)
    pond=load_npz(pin(source['footprint'],oldpins[source['footprint']]))['plane']
    masks={k:base[k] for k in REQUIRED};present=[k for k in OPTIONAL if k in base]
    masks.update({k:base[k] for k in present})
    require(all(a.shape==(2048,2048) and a.dtype==np.bool_ for a in masks.values()),'protection_shape')
    sys.path.insert(0,str(w/'tools/terrain'))
    for name in ('shape_repair_constraints_ev112.py','verify_roads_v30.py'):
        p=w/'tools/terrain'/name;pin(p,oldpins[str(p)])
    # Pin imported road-chain dependencies too; this helper only constructs a mask, no experiment.
    p=w/'tools/terrain/shape_repair_constraints_ev112.py';rmod=module('road_guard',p)
    guard,refs=rmod.s3_road_guard()
    for p,d in refs.items():require(oldpins.get(p)==d,'road_reference_changed');pin(p,d)
    masks['s3_road_guard']=guard
    pv=np.zeros((2048,2048),bool);q=np.isfinite(pond)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):pv[dr:dr+2047,dc:dc+2047]|=q
    masks['old_footprint_pond']=pv
    rr,cc=np.indices((2048,2048));masks['crossing_015_45_60m']=np.hypot(cc*6.-10397.4,12282-rr*6.-9421.9)<=60
    # Published areas are reused, not recomputed under a new policy.
    ep=pin(w/'evidence/pilot-visible-exposure-20261028/artifact-hashes.json');em=json.loads(ep.read_bytes())
    eraw=root/'pilot-visible-exposure-census-r2-20261028'
    mp=pin(eraw/'models.json',em[(eraw/'models.json').relative_to(root).as_posix()]['sha256'])
    exposure=json.loads(mp.read_bytes());require({m['model'] for m in exposure}=={m['model'] for m in models},'exposure_universe')
    for m in exposure:pin(eraw/m['file'],m['sha256'])
    for p in (Path(__file__),HERE/'pilot_bank_profiles_ev112.py',HERE/'pilot_visible_surface_ev112.py'):pin(p)
    return raw,models,arrays,candidate,h,masks,present,eraw,exposure,pins,solver

def assemble(raw,models,arrays):
    result={}
    for site,a in arrays.items():
        n=len(a['bed']);grid=np.zeros((n+16,39,3));seen=np.zeros(n+16,bool);records=[]
        for m in models:
            if m['site']!=site:continue
            f=load_npz(raw/m['file']);start=int(f['npz_start'])+8-int(f['cap_before'])
            g.attach_grid(grid,seen,start,f['source_grid'])
            records.append((m,f,start))
        require(seen.all(),'missing_rows:'+site)
        require(np.array_equal(grid[8:-8],a['bed']),'body_changed:'+site)
        require(np.array_equal(a['water'][:,0,1],a['water'][:,1,1]),'water_height_mismatch')
        water=np.concatenate((np.repeat(a['water'][:1],8,axis=0),a['water'],np.repeat(a['water'][-1:],8,axis=0)))
        station=np.r_[a['station'][0]-np.arange(8,0,-1),a['station'],a['station'][-1]+np.arange(1,9)]
        extra=np.zeros(n+16,bool);extra[:8]=True;extra[-8:]=True
        result[site]=(grid,water,station,extra,records)
    return result

def run(root,w,out,meter,preflight):
    raw,models,arrays,candidate,h,masks,present,eraw,exposure,pins,solver=inputs(root,w,meter)
    sites=assemble(raw,models,arrays);total=sum(len(v[0]) for v in sites.values())+len(sites['kit-7'][0])
    cost=dict(rows_baseline=sum(len(v[0]) for v in sites.values()),rows_candidate=len(sites['kit-7'][0]),total_profiles=total,models=201)
    meter.dump(out/'inputs.json',dict(pins=pins,optional_protections_present=present,
        candidate_solver=solver,
        old_footprint_not_proven_equivalent_to_v31_current_pond=True))
    if preflight:
        begin=time.monotonic();count=0
        for grid,water,station,extra,records in sites.values():
            for i in np.linspace(0,len(grid)-1,12,dtype=int):g.row_profile(grid[i],water[i],h,extrapolated=bool(extra[i]));count+=1
        cost['estimated_seconds_with_25pct_margin']=meter.memory()['seconds']+1.25*(time.monotonic()-begin)*total/count+30
        require(cost['estimated_seconds_with_25pct_margin']<=600,'profile_budget')
        meter.dump(out/'cost.json',cost);return dict(status='PROFILE_PREFLIGHT_ONLY',**cost)
    meter.dump(out/'cost.json',cost);(out/'sites').mkdir();face_reports=[];site_reports=[]
    emodels={m['model']:m for m in exposure}
    for site,(grid,water,station,extra,records) in sites.items():
        touched_by={name:g.native(mask,grid[:,:,(0,2)])>0 for name,mask in masks.items()}
        touched=np.logical_or.reduce(list(touched_by.values()));ground=g.native(h,grid[:,:,(0,2)])
        excluded,reasons,floor=g.dry_contract(grid,water[:,0,1],station,ground,touched,extra)
        variants={'baseline':grid}
        if site=='kit-7':
            cgrid=grid.copy();cgrid[8:-8]=candidate['bed'];variants['candidate']=cgrid
            require(np.array_equal(cgrid[excluded],grid[excluded]),'candidate_changes_excluded_points')
        arrays_out=dict(grid=grid,water=water,station=station,extra_cap=extra,ground=ground,excluded=excluded,floor=floor,
                        reason_names=np.array(list(reasons)),reasons=np.array(list(reasons.values())),
                        protection_names=np.array(list(touched_by)),protection_touch=np.array(list(touched_by.values())))
        profiles={}
        for variant,data in variants.items():
            profiles[variant]=[g.row_profile(row,water[i],h,extrapolated=bool(extra[i])) for i,row in enumerate(data)]
            arrays_out[variant+'_grid']=data
            arrays_out[variant+'_metrics']=np.array([[p['metrics'][k] for k in g.FIELDS] for p in profiles[variant]])
            for name in ('section_water_width','maximum_row_offaxis_residual','water_midpoint_minus_bed_centre','width_below_nominal_4p5'):
                arrays_out[variant+'_'+name]=np.asarray([p[name] for p in profiles[variant]])
        arrays_out['metric_fields']=np.array(g.FIELDS)
        target=out/'sites'/(site+'.npz');np.savez_compressed(target,**arrays_out)
        meter.dump(out/'sites'/(site+'-crossings.json'),{v:[p['crossings'] for p in rows] for v,rows in profiles.items()})
        totals=collections.defaultdict(float)
        for m,f,start in records:
            ex=excluded[start:start+len(f['source_grid'])]
            classes=g.face_classes(ex,f['source_triangles'])[f['bed_source_face']]
            ef=load_npz(eraw/emodels[m['model']]['file']);metrics=ef['metrics'];names=list(ef['fields'])
            require(len(classes)==len(metrics),'face_coverage')
            qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25])
            cols=f['source_triangles']%39
            qlo=abs(qs[cols]).min(axis=1)[f['bed_source_face']];qhi=abs(qs[cols]).max(axis=1)[f['bed_source_face']]
            domains=np.where(qhi<=2.25,'WET',np.where((qlo>=2.25)&(qhi<=4),'DRY_INNER',np.where(qlo>=4,'DRY_OUTER','BOUNDARY')))
            groups=[]
            for domain in sorted(set(domains)):
                for ci,cname in enumerate(CLASSES):
                    take=(classes==ci)&(domains==domain)
                    if not take.any():continue
                    fields=('above_H_area','corridor_rectangle_above_H_area','corridor_disc_inner_above_H_area','corridor_disc_uncertain_above_H_area')
                    values={k:float(metrics[take,names.index(k)].sum()) for k in fields}
                    groups.append(dict(domain=domain,dry_pilot_class=cname,faces=int(take.sum()),**values))
                    totals['faces']+=int(take.sum());totals[cname+'_road_area']+=values['corridor_rectangle_above_H_area']
            require(sum(v['faces'] for v in groups)==len(metrics),'partition_omission')
            require(abs(sum(v['corridor_rectangle_above_H_area'] for v in groups)-metrics[:,names.index('corridor_rectangle_above_H_area')].sum())<=1e-10,'partition_area')
            face_reports.append(dict(model=m['model'],site=site,groups=groups))
        point_domains=np.where(abs(qs)<=2.25,'WET',np.where(abs(qs)<=4,'DRY_INNER',np.where(abs(qs)<18,'DRY_OUTER','BORDER')))
        site_reports.append(dict(site=site,file=str(target.relative_to(out)),sha256=meter.sha(target),
             rows=len(grid),body_rows=len(grid)-16,extra_cap_rows=16,
             candidate_status=('BOUNDED_NOT_CONVERGED' if not solver['success'] else 'CONVERGED_NOT_ACCEPTED') if site=='kit-7' else 'NO_CANDIDATE',
             point_domains={name:int((point_domains==name).sum()*len(grid)) for name in set(point_domains)},
             section_reference={name:dict(minimum=float(arrays_out['baseline_'+name].min()),median=float(np.median(arrays_out['baseline_'+name])),maximum=float(arrays_out['baseline_'+name].max()))
                 for name in ('section_water_width','maximum_row_offaxis_residual')},
             width_below_nominal_rows=int(arrays_out['baseline_width_below_nominal_4p5'].sum()),
             maximum_water_midpoint_offset_m=float(np.linalg.norm(arrays_out['baseline_water_midpoint_minus_bed_centre'],axis=1).max()),
             free_points=int((~excluded).sum()),reasons={k:int(v.sum()) for k,v in reasons.items()},
             protection_touch_counts={k:int(v.sum()) for k,v in touched_by.items()},face_totals=dict(totals),
             profiles={v:{k:dict(minimum=float(a.min()),median=float(np.median(a)),maximum=float(a.max()))
                 for j,k in enumerate(g.FIELDS) for a in [arrays_out[v+'_metrics'][:,j]]} for v in variants}))
        meter.dump(out/'progress.json',dict(completed_sites=len(site_reports),last=site,measurement=meter.memory()))
    for p,d in pins.items():require(meter.sha(p)==d,'changed_after_census:'+p)
    require(sum(int(s['face_totals']['faces']) for s in site_reports)==185744,'global_face_coverage')
    meter.dump(out/'sites.json',site_reports);meter.dump(out/'face-partitions.json',face_reports)
    return dict(status='PROFILE_AND_DRY_CONTRACT_DIAGNOSTIC_PENDING_CONSUMER',**cost,
        limits=['Cross-sections only, no continuous longitudinal candidate coverage or render.',
          'CAP section water level/width extrapolated; no claim of water footprint there.',
          'Dry-pilot exclusions are not original v31 mask or human product constraints.',
          'Protection contact tested at mesh vertices, not all triangle interiors.',
          'Reasons overlap: sums of per-reason counts are not unique excluded vertices.',
          'Width below4.5 can reflect taper or quantization; water-direction offaxis residual retained, not silently accepted as a natural section.',
          'Unchanged XZ alone does not prove unchanged visible shoreline. No geometry modified.'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('worktree',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--preflight',action='store_true');a=ap.parse_args()
    a.root=a.root.resolve();a.worktree=a.worktree.resolve();a.output.mkdir(exist_ok=False)
    meter=module('meter',HERE/'water_constraint_diagnostic_ev112.py');meter.STARTED=STARTED;meter.MAX_SECONDS=120 if a.preflight else 600
    stop=meter.bounded(a.output)
    try:
        result=run(a.root,a.worktree,a.output,meter,a.preflight);result['measurement']=meter.memory();meter.dump(a.output/'report.json',result);print(json.dumps(result))
    except Exception as e:
        meter.dump(a.output/'failure.json',dict(type=type(e).__name__,error=str(e),measurement=meter.memory()));raise
    finally:stop.set()
