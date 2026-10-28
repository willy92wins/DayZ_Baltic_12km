"""Continuous Visual/H/W and reference-road corridor diagnostic for sealed Visual201."""
import os,time
STARTED=time.monotonic()
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
import argparse,collections,hashlib,importlib.util,json,math
from pathlib import Path
import numpy as np
import shapely
from shapely import Polygon,STRtree
HERE=Path(__file__).resolve().parent
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('common_refinement',HERE/'pilot_surface_refinement_ev112.py')
incidence=module('exact_incidence',HERE/'pilot_exact_incidence_ev112.py')
require=g.require
NAMES=('area','above_H_area','below_H_area','contact_H_area','above_H_at_or_below_nominal_W_area',
       'above_H_at_or_below_visual_W_area','above_H_without_visual_W_footprint_area',
       'corridor_rectangle_above_H_area','corridor_rectangle_at_or_below_visual_W_area',
       'corridor_disc_inner_above_H_area','corridor_disc_uncertain_above_H_area',
       'min_B_H','max_B_H','min_B_nominal_W','max_B_nominal_W','intersecting_visual_water_faces',
       'nominal_visual_water_min_delta','nominal_visual_water_max_delta')
H_SHA='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
FP_SHA='084171b0e29df5c220f9d5aab42a3dc683a2f70a07579f08cd930dfd109e716b'
ROAD_SHA='94ecbca61bd5ba9ba61f89b765b043676a4a65703729a0b69009ae233984a1c2'

def polygon(p):
    return Polygon(p) if len(p)>=3 and g.area(p)>0 else Polygon()

def rect(a,b,width=4.):
    a,b=np.asarray(a,float),np.asarray(b,float)
    require(a.shape==b.shape==(2,) and np.isfinite([a,b]).all(),'road_point')
    d=b-a;require(np.linalg.norm(d)>0,'zero_length_road_edge')
    normal=np.array([-d[1],d[0]])*width/np.linalg.norm(d)
    return Polygon([a+normal,b+normal,b-normal,a-normal])

def disc_bounds(point,radius=4.,sides=64):
    """Inner/outer bounds, never pretend polygon is exact circular corridor."""
    theta=np.arange(sides)*2*np.pi/sides
    unit=np.c_[np.cos(theta),np.sin(theta)]
    return Polygon(point+radius*unit),Polygon(point+(radius/np.cos(np.pi/sides))*unit)

def corridor(xy,edges):
    rectangles=[rect(xy[int(a)],xy[int(b)]) for a,b,_ in edges]
    degree=np.zeros(len(xy),int)
    for a,b,_ in edges:degree[int(a)]+=1;degree[int(b)]+=1
    # Discs around ALL vertices include joints and endpoints. Bounds stay separate.
    disc=[disc_bounds(p) for p in xy]
    return rectangles,[v[0] for v in disc],[v[1] for v in disc],degree

def road_guard(xy,edges):
    require(xy.shape==(36428,2) and edges.shape==(36467,3) and
            np.isfinite(xy).all() and np.isfinite(edges).all() and
            (edges[:,:2]>=0).all() and (edges[:,:2]<len(xy)).all() and
            np.array_equal(edges[:,:2],edges[:,:2].astype(np.int64)),'road_universe')
    lengths=np.linalg.norm(xy[edges[:,1].astype(int)]-xy[edges[:,0].astype(int)],axis=1)
    require((lengths>0).all() and np.max(abs(lengths-edges[:,2]))<=1e-9,'road_lengths')

def summarize_regions(metrics,categories):
    aggregates={}
    require(set(categories)<=set(('BODY','CAP_START','CAP_END')),'region_category')
    for category in ('BODY','CAP_START','CAP_END'):
        z=metrics[categories==category]
        if not len(z):continue
        aggregates[category]={k:float(np.nansum(z[:,i])) for i,k in enumerate(NAMES[:11])}
        aggregates[category].update(faces=len(z),min_B_H=float(z[:,11].min()),max_B_H=float(z[:,12].max()))
    return aggregates

def regions_for_face(tri,h,wp,wf,water,water_tree,rects,rect_tree,inners,outers,disc_tree):
    parts=g.refine(tri,h,wp,wf);foot=polygon(tri[:,(0,2)])
    wids=[int(i) for i in water_tree.query(foot) if incidence.positive_pair(tri[:,(0,2)],water[int(i)][:,(0,2)])]
    rids=rect_tree.query(foot);dids=disc_tree.query(foot)
    road=shapely.union_all([rects[i] for i in rids])
    # Disc contributions outside rectangles are conservative joint/end additions.
    inner=shapely.difference(shapely.union_all([inners[i] for i in dids]),road)
    outer=shapely.difference(shapely.union_all([outers[i] for i in dids]),road)
    uncertain=shapely.difference(outer,inner)
    metrics=dict.fromkeys(NAMES,0.)
    metrics.update(min_B_H=math.inf,max_B_H=-math.inf,min_B_nominal_W=math.inf,max_B_nominal_W=-math.inf,
                   nominal_visual_water_min_delta=math.inf,nominal_visual_water_max_delta=-math.inf)
    exposed=[];peaks=[];layer_refs=set()
    for p in parts:
        rr=g.sign_regions(p,'terrain');wr=g.sign_regions(p,'water')
        metrics['area']+=p['area'];metrics['above_H_area']+=rr['above_area']
        metrics['below_H_area']+=rr['below_area'];metrics['contact_H_area']+=rr['contact_area']
        metrics['min_B_H']=min(metrics['min_B_H'],rr['minimum']);metrics['max_B_H']=max(metrics['max_B_H'],rr['maximum'])
        metrics['min_B_nominal_W']=min(metrics['min_B_nominal_W'],wr['minimum']);metrics['max_B_nominal_W']=max(metrics['max_B_nominal_W'],wr['maximum'])
        j=int(np.argmax(p['bed']-p['terrain']))
        peaks.append((rr['maximum'],p['polygon'][j].tolist(),p['cell']))
        ep=rr['above_polygon'] if rr['above_area'] else np.empty((0,2))
        eg=polygon(ep)
        if not eg.is_empty:exposed.append(eg)
        if len(ep):
            diff=g.evaluate(p['bed_plane'],ep)-g.evaluate(p['water_coeff'],ep)
            metrics['above_H_at_or_below_nominal_W_area']+=g.area(g.clip(ep,diff,False))
        actual_footprints=[];under=[]
        for wi in wids:
            wt=water[int(wi)]
            cut=g.triangle_intersection(p['polygon'],wt[:,(0,2)])
            cut,used_exact,exact_positive=incidence.guarded_intersection(tri[:,(0,2)],p['native_triangle'],wt[:,(0,2)],cut,g.area(cut))
            if (used_exact and not exact_positive) or (not used_exact and g.area(cut)==0):continue
            coeff=g.plane(wt[:,(0,2)],wt[:,1]);layer_refs.add(int(wi))
            actual_footprints.append(polygon(cut))
            delta=g.evaluate(coeff,cut)-g.evaluate(p['water_coeff'],cut)
            metrics['nominal_visual_water_min_delta']=min(metrics['nominal_visual_water_min_delta'],float(delta.min()))
            metrics['nominal_visual_water_max_delta']=max(metrics['nominal_visual_water_max_delta'],float(delta.max()))
            if len(ep):
                ce=g.triangle_intersection(ep,wt[:,(0,2)])
                if g.area(ce)>0:
                    d=g.evaluate(p['bed_plane'],ce)-g.evaluate(coeff,ce)
                    under.append(polygon(g.clip(ce,d,False)))
        ug=shapely.union_all(under);wg=shapely.union_all(actual_footprints)
        metrics['above_H_at_or_below_visual_W_area']+=float(ug.area)
        metrics['above_H_without_visual_W_footprint_area']+=float(shapely.difference(eg,wg).area)
        metrics['corridor_rectangle_above_H_area']+=float(shapely.intersection(eg,road).area)
        metrics['corridor_rectangle_at_or_below_visual_W_area']+=float(shapely.intersection(ug,road).area)
        metrics['corridor_disc_inner_above_H_area']+=float(shapely.intersection(eg,inner).area)
        metrics['corridor_disc_uncertain_above_H_area']+=float(shapely.intersection(eg,uncertain).area)
    metrics['intersecting_visual_water_faces']=len(layer_refs)
    for k in ('nominal_visual_water_min_delta','nominal_visual_water_max_delta'):
        if not math.isfinite(metrics[k]):metrics[k]=float('nan')
    return metrics,exposed,max(peaks),len(parts),sorted(layer_refs)

def inputs(root,worktree,meter):
    raw=root/'pilot-visible-surface-extraction-20261028'
    evidence=worktree/'evidence/pilot-visible-surface-20261028/artifact-hashes.json'
    manifest=json.loads(evidence.read_bytes());pins={str(evidence):meter.sha(evidence)}
    def pin(p,digest):
        require(meter.sha(p)==digest,'input_changed:'+str(p));pins[str(p)]=digest
    for name in ('models.json','report.json','inputs.json'):
        p=raw/name;pin(p,manifest[p.relative_to(root).as_posix()]['sha256'])
    models=json.loads((raw/'models.json').read_bytes())
    require(len(models)==201 and len({x['model'] for x in models})==201,'model_coverage')
    for m in models:pin(raw/m['file'],m['sha256'])
    previous=json.loads((raw/'inputs.json').read_bytes())['pins']
    for name,digest in previous.items():
        p=Path(name);pin(p if p.is_absolute() else worktree/p,digest)
    hp=root/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
    fp=root/'river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz'
    # The explicit primary checkout is the independent road reference used by B.
    rp=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/tests/regional_foundation_roads_v6/reference.npz')
    for p,d in ((hp,H_SHA),(fp,FP_SHA),(rp,ROAD_SHA)):pin(p,d)
    with np.load(hp) as f:h=f['heights']
    with np.load(fp) as f:wp=f['plane'];wf=f['field']
    with np.load(rp) as f:xy=f['xy'];edges=f['edges']
    road_guard(xy,edges)
    require(h.shape==(2048,2048) and wp.shape==(2047,2047) and wf.shape==(2047,2047,4),'grid_shape')
    water=[];water_ref=[]
    for m in models:
        with np.load(raw/m['file']) as f:
            require(np.all(f['bed_n']==3) and np.all(f['water_n']==3),'nontriangle_requires_new_partition')
            require(not np.any(f['bed_flags']) and not np.any(f['water_flags']),'ambiguous_pilot_faces')
            for i,tri in enumerate(f['water'][:,:3]):water.append(tri);water_ref.append([m['model_index'],i])
    return raw,models,pins,h,wp,wf,xy,edges,np.asarray(water),water_ref

def run(root,worktree,out,meter,preflight):
    raw,models,pins,h,wp,wf,xy,edges,water,water_ref=inputs(root,worktree,meter)
    water_shapes=[polygon(t[:,(0,2)]) for t in water];water_tree=STRtree(water_shapes)
    rects,inners,outers,degree=corridor(xy,edges)
    rect_tree=STRtree(rects);disc_tree=STRtree(outers)
    cost=dict(models=201,bed_faces=sum(m['faces']['bed'] for m in models),actual_water_faces=len(water),
              road_edges=len(edges),road_nodes=len(xy),disc_radial_outer_excess_m=4/np.cos(np.pi/64)-4)
    if preflight:
        timings=[];selected=[]
        for site in sorted({m['site'] for m in models}):
            subset=[m for m in models if m['site']==site]
            selected.extend(subset[i] for i in sorted({0,len(subset)//2,len(subset)-1}))
        for m in selected:
            with np.load(raw/m['file']) as f:faces=f['bed'][:,:3]
            begin=time.monotonic()
            for fi in np.linspace(0,len(faces)-1,16,dtype=int):
                regions_for_face(faces[fi],h,wp,wf,water,water_tree,rects,rect_tree,inners,outers,disc_tree)
            timings.append(dict(model=m['model'],faces=16,seconds=time.monotonic()-begin))
        seconds_per_face=sum(t['seconds'] for t in timings)/sum(t['faces'] for t in timings)
        estimated=1.25*seconds_per_face*cost['bed_faces']+meter.memory()['seconds']+15
        cost.update(benchmark=timings,estimated_seconds_with_25pct_margin=estimated,
                    estimator_limit='Stratified first/middle/last model per site; not worst-case guarantee.600s watchdog remains.')
    meter.dump(out/'cost.json',cost)
    meter.dump(out/'inputs.json',dict(pins=pins,producer_sha256=meter.sha(__file__),
        kernel_sha256=meter.sha(HERE/'pilot_surface_refinement_ev112.py'),incidence_sha256=meter.sha(HERE/'pilot_exact_incidence_ev112.py'),water_refs=water_ref))
    if preflight:
        require(estimated<=600,'INCONCLUSIVE_ESTIMATED_RUNTIME_EXCEEDS_BUDGET')
        return dict(status='EXPOSURE_PREFLIGHT_ONLY',**cost)
    summaries=[];all_extrema=[];(out/'models').mkdir()
    for model in models:
        with np.load(raw/model['file']) as f:
            faces=f['bed'][:,:3];mapped=f['bed_source_face']
            require(np.all(mapped>=0),'unmapped_faces_require_independent_labels')
            categories=f['source_category'][mapped]
        metrics=[];exposed=[];peaks=[];parts_count=0;layer_records=[]
        for fi,face in enumerate(faces):
            row,polys,peak,parts,layers=regions_for_face(face,h,wp,wf,water,water_tree,rects,rect_tree,inners,outers,disc_tree)
            metrics.append([row[k] for k in NAMES]);exposed+=polys;parts_count+=parts
            peaks.append(dict(face=fi,region=str(categories[fi]),max_B_H=peak[0],xz=peak[1],native_face=list(peak[2])))
            if layers:layer_records.append([fi,layers])
        m=np.asarray(metrics,float)
        expo=shapely.union_all(exposed);bed_union=shapely.union_all([polygon(x[:,(0,2)]) for x in faces])
        aggregates=summarize_regions(m,categories)
        target=out/'models'/Path(model['file']).name
        np.savez_compressed(target,metrics=m,fields=np.array(NAMES),categories=categories)
        worst=sorted(peaks,key=lambda x:x['max_B_H'],reverse=True)[:12]
        all_extrema.append(dict(model=model['model'],site=model['site'],peaks=worst))
        summary=dict(model=model['model'],site=model['site'],faces=len(faces),native_parts=parts_count,regions=aggregates,
            all_categories_exposed_union_area=float(expo.area),all_categories_exposed_geometry_type=expo.geom_type,
            all_categories_exposed_components=len(expo.geoms) if hasattr(expo,'geoms') else int(not expo.is_empty),
            projected_face_area_sum=float(m[:,0].sum()),projected_footprint_union_area=float(bed_union.area),
            projected_overlap_or_numerical_area=float(m[:,0].sum()-bed_union.area),file=str(target.relative_to(out)),sha256=meter.sha(target))
        summaries.append(summary)
        meter.dump(out/'models'/ (target.stem+'-water-face-contacts.json'),layer_records)
        meter.dump(out/'progress.json',dict(completed=len(summaries),models=201,last=model['model'],measurement=meter.memory()))
    for p,digest in pins.items():require(meter.sha(p)==digest,'input_changed_after_census:'+p)
    meter.dump(out/'models.json',summaries);meter.dump(out/'extrema.json',all_extrema)
    return dict(status='SOURCE_RELATIVE_VISUAL_EXPOSURE_DIAGNOSTIC',models=len(summaries),
        faces=sum(m['faces'] for m in summaries),native_parts=sum(m['native_parts'] for m in summaries),
        limits=['Source terrain and nominal water, not full compiled terrain or render/transparency.',
                'Actual pilot water retained separately. Under water can remain visible.',
                'Reference corridor +/-4m, not measured pavement. Rectangles exact; circular joints/endpoints bounded inside/outside64gons. Uncertain ring never accepted as clear.',
                'Face sums can count stacked layers. Unions/components cover all categories per model, not global topology; additive area metrics separate BODY/CAP.',
                'No repaired candidate evaluated and no geometry changed. Fixed-constraint feasibility still pending.'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('worktree',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--preflight',action='store_true');a=ap.parse_args()
    a.root=a.root.resolve();a.worktree=a.worktree.resolve();a.output.mkdir(exist_ok=False)
    meter=module('meter',HERE/'water_constraint_diagnostic_ev112.py');meter.STARTED=STARTED;meter.MAX_SECONDS=120 if a.preflight else 600
    stop=meter.bounded(a.output)
    try:
        report=run(a.root,a.worktree,a.output,meter,a.preflight);m=meter.memory()
        require(m['seconds']<=meter.MAX_SECONDS and max(m['peak_resident_bytes'],m['peak_commit_bytes'])<=meter.MAX_BYTES,'resource_budget')
        report['measurement']=m;meter.dump(a.output/'report.json',report);print(json.dumps(report))
    except Exception as e:meter.dump(a.output/'failure.json',dict(reason=str(e),type=type(e).__name__,measurement=meter.memory()));raise
    finally:stop.set()
