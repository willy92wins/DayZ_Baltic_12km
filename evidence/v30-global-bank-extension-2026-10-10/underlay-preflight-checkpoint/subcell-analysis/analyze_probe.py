import csv, json, hashlib, importlib.util, math, sys, time
from pathlib import Path
import numpy as np
BASE=Path(r'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010')
RUN=BASE/'build-wide-slope'/'subcell-flag-probe'/'runtime-v2'
POINTS=RUN/'BalticEV95SubcellFlagsV2.BalticTrial'/'points.csv'
LOG=RUN/'native-snapshot.log'
SELECTION=BASE/'build-wide-slope'/'subcell-flag-probe'/'selection.json'
CLASS=BASE/'build-wide-slope'/'anomaly-classification'/'classification.json'
INDEX_RUN=BASE/'ev93-face-index'/'runs'/'20261010T092417Z-63d4cec3'
INDEX_SRC=BASE/'ev93-face-index'/'build_face_index.py'
OUT=RUN/'analysis'/'runtime-v2-analysis.json'
PREP=RUN/'preparation.json'
STAGE=RUN/'stage.json'
RECEIPT=RUN/'runtime-receipt.json'
MISSION_INIT=RUN/'BalticEV95SubcellFlagsV2.BalticTrial'/'init.c'
WIDE_STAGE=BASE/'build-wide-slope'/'stage.json'
INDEX_MANIFEST=INDEX_RUN/'manifest.json'

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def loadcsv(p, delimiter=';'):
    with open(p,encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f,delimiter=delimiter))
def cross2(a,b): return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def point_face(p, xyz):
    # Coordinates (X,Z); positive-area compiled triangle. Returns inside, edge distance, outside distance, barycentric.
    v=xyz[:,:,[0,2]]
    a,b,c=v[:,0,:],v[:,1,:],v[:,2,:]
    den=cross2(b-a,c-a)
    good=np.abs(den)>0
    den_safe=np.where(good,den,1.0)
    w1=cross2(p-a,c-a)/den_safe
    w2=cross2(b-a,p-a)/den_safe
    w0=1.0-w1-w2
    tol=1e-10
    inside=good&(w0>=-tol)&(w1>=-tol)&(w2>=-tol)
    # Distance to each edge; for inside this is distance to polygon boundary, outside is nearest edge.
    dists=[]
    for u,vv in ((a,b),(b,c),(c,a)):
        dv=vv-u; den2=np.sum(dv*dv,axis=1)
        t=np.divide(np.sum((p-u)*dv,axis=1),den2,out=np.zeros_like(den2),where=den2>0)
        t=np.clip(t,0.0,1.0)
        q=u+t[:,None]*dv
        dists.append(np.sqrt(np.sum((p-q)**2,axis=1)))
    edge=np.min(np.stack(dists,axis=1),axis=1)
    return inside,edge,np.stack([w0,w1,w2],axis=1)

start=time.perf_counter()
manifest_doc=json.loads(INDEX_MANIFEST.read_text(encoding='utf-8'))
WRP_SOURCE=Path(next(p for p in manifest_doc['input_hashes'] if p.lower().endswith('baltic_trial.wrp')))
WORLD_PBO=Path(r'P:\\Mods\\@DayZ_Baltic_EV95_WideBankPreviewV1\\Addons\\narva_trial.pbo')
WATER_PBO=Path(r'P:\\Mods\\@DayZ_Baltic_EV95_WideBankPreviewV1\\Addons\\baltic_water_v30.pbo')
readset_paths=[LOG,POINTS,SELECTION,CLASS,PREP,STAGE,RECEIPT,MISSION_INIT,WIDE_STAGE,INDEX_SRC,INDEX_MANIFEST,WRP_SOURCE,WORLD_PBO,WATER_PBO]
readset_paths += [INDEX_RUN/sh['path'] for sh in manifest_doc['shards']]
pins_start={str(p):sha(p) for p in readset_paths}
selection_doc=json.loads(SELECTION.read_text(encoding='utf-8'))
classification_doc=json.loads(CLASS.read_text(encoding='utf-8'))
preparation_doc=json.loads(PREP.read_text(encoding='utf-8'))
stage_doc=json.loads(STAGE.read_text(encoding='utf-8'))
wide_stage_doc=json.loads(WIDE_STAGE.read_text(encoding='utf-8'))
receipt_doc=json.loads(RECEIPT.read_text(encoding='utf-8'))
with open(LOG,encoding='utf-8-sig') as f: log_header=f.readline().strip().split(';')
if log_header != ['BALTIC_EV95_SUBCELL_FLAGS_V2','BalticTrial','40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a','3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14','279','7']: raise ValueError(f'unexpected runtime header {log_header}')
if len(classification_doc['rows']) != 24 or selection_doc['index']['manifest_sha256'] != pins_start[str(INDEX_MANIFEST)]: raise ValueError('classification/index anchors mismatch')
if sha(POINTS) != selection_doc['points_sha256'] or sha(POINTS) != preparation_doc['points_sha256'] or sha(MISSION_INIT) != preparation_doc['source_v2_sha256'] or selection_doc['mission_source_sha256'] != preparation_doc['source_v1_sha256']: raise ValueError('mission/point source pin mismatch')
if stage_doc['world_sha'].lower() != sha(WORLD_PBO) or stage_doc['water_sha'].lower() != sha(WATER_PBO) or stage_doc['water_sha'].lower() != manifest_doc['base_identity']['water_pbo_sha256'] or sha(WRP_SOURCE) != manifest_doc['base_identity']['wrp_source_sha256'] or wide_stage_doc['source_wrp_sha256'] != manifest_doc['base_identity']['wrp_source_sha256'] or wide_stage_doc['baseline_water_pbo_sha256'] != manifest_doc['base_identity']['water_pbo_sha256']: raise ValueError('runtime stage/index water identity mismatch')
if receipt_doc['End']['satisfied'] is not True or receipt_doc['End']['observed'] != 'END;7;1953;30012' or receipt_doc['Close']['graceful'] is not True or receipt_doc['Close']['stop_method'] != 'orderly_close' or receipt_doc['Final']['cleanup_degraded']: raise ValueError('runtime receipt is not a clean complete run')
point_rows=loadcsv(POINTS)
log_rows=[]; phase_meta={}; end_record=None
with open(LOG,encoding='utf-8-sig') as f:
    for line in f:
        parts=line.rstrip(chr(13)+chr(10)).split(';')
        if not parts: continue
        if parts[0]=='S':
            if len(parts)!=25: raise ValueError(f'bad S width {len(parts)}')
            names=['record','phase','index','sample_id','role','group_id','class','row','col','ring_m','dx_m','dz_m','x','z','ground','sea_flag','pond_flag','no_fake','with_fake','depth','elapsed_ms','sea_level','wave_current','wave_max','wind']
            row=dict(zip(names,parts));
            for k in ('phase','index','class','row','col','elapsed_ms'): row[k]=int(row[k])
            for k in ('ring_m','dx_m','dz_m','x','z','ground','no_fake','with_fake','depth','sea_level','wave_current','wave_max','wind'): row[k]=float(row[k])
            for k in ('sea_flag','pond_flag'): row[k]=row[k].lower()=='true'
            log_rows.append(row)
        elif parts[0]=='PHASE_BEGIN':
            phase=int(parts[1]); phase_meta[phase]={'start_ms':int(parts[2]),'offset_ms':int(parts[3]),'sea_level':float(parts[4]),'wave_current':float(parts[5]),'wave_max':float(parts[6]),'wind':float(parts[7])}
        elif parts[0]=='PHASE_END':
            phase=int(parts[1]); phase_meta.setdefault(phase,{})['end']={'elapsed_ms':int(parts[2]),'run_elapsed_ms':int(parts[3]),'rows':int(parts[4]),'sea_level':float(parts[5]),'wave_current':float(parts[6]),'wave_max':float(parts[7]),'wind':float(parts[8])}
        elif parts[0]=='END': end_record=parts

if len(point_rows)!=279 or len(log_rows)!=1953 or len(phase_meta)!=7: raise ValueError((len(point_rows),len(log_rows),phase_meta.keys()))
point_by={p['sample_id']:p for p in point_rows}
if len(point_by)!=len(point_rows): raise ValueError('duplicate sample ids')
# Verify emitted coordinates against point CSV; mission numeric formatting is rounded to 0.01 m.
max_log_coord_delta_m=0.0
for phase in range(7):
    rows=sorted((r for r in log_rows if r['phase']==phase),key=lambda x:x['index'])
    if len(rows)!=279 or [r['sample_id'] for r in rows] != [p['sample_id'] for p in point_rows]: raise ValueError(f'phase {phase} sample order mismatch')
    for r,p in zip(rows,point_rows):
        max_log_coord_delta_m=max(max_log_coord_delta_m,abs(r['x']-float(p['x'])),abs(r['z']-float(p['z'])))
        if r['index']<0 or r['x']!=float(p['x']) or r['z']!=float(p['z']):
            # mission emits coordinates rounded to 6 decimals. Verify exact emitted numeric matches expected within formatter precision.
            if abs(r['x']-float(p['x']))>5.1e-3 or abs(r['z']-float(p['z']))>5.1e-3: raise ValueError(f'coordinate mismatch {phase}:{p["sample_id"]}')

# Load pinned complete range index; query one small neighborhood per point group to bound exact clipping.
spec=importlib.util.spec_from_file_location('face_index',INDEX_SRC); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
index=mod.FaceRangeIndex(INDEX_RUN)
manifest_sha=sha(INDEX_MANIFEST)
groups={}
for p in point_rows: groups.setdefault(p['group_id'],[]).append(p)
static={}
for gi,(gid,pts) in enumerate(sorted(groups.items())):
    # A sample lies in cell col=floor(x/6), row=2047-floor(z/6). pad one closed cell around range.
    cols=[int(math.floor(float(p['x'])/6.0)) for p in pts]
    rows=[2047-int(math.floor(float(p['z'])/6.0)) for p in pts]
    r0=max(0,min(rows)-1); r1=min(2046,max(rows)+1); c0=max(0,min(cols)-1); c1=min(2046,max(cols)+1)
    cand=index.query_window(r0,r1,c0,c1)
    # Preserve candidate faces and solve point inclusion for each sample.
    for p in pts:
        sid=p['sample_id']; xy=np.array([float(p['x']),float(p['z'])],dtype=np.float64); ground=next(r['ground'] for r in log_rows if r['sample_id']==sid and r['phase']==0)
        records=[]
        for kind in (0,1):
            ix=np.flatnonzero(cand['kind']==kind)
            if not len(ix): records.append({'kind':'physical' if kind==0 else 'visible','candidate_count':0,'inside':[],'nearest_candidate_in_query_window':None}); continue
            xyz=cand['xyz'][ix]
            ins,edge,bary=point_face(xy,xyz)
            inside=np.flatnonzero(ins)
            rel=np.arange(len(ix))
            nearest_i=int(np.argmin(edge))
            nearidx=int(ix[nearest_i]); near_y=float(np.dot(cand['plane_y_xz'][nearidx,:2],[xy[0],xy[1]])+cand['plane_y_xz'][nearidx,2])
            near={
                'object_id':int(cand['object_id'][nearidx]),'model':mod.model_name(index.manifest,int(cand['model_id'][nearidx])) if hasattr(mod,'model_name') else next(m['basename'] for m in index.manifest['models'] if m['model_id']==int(cand['model_id'][nearidx])),
                'face_id':int(cand['face_id'][nearidx]),'distance_m':float(edge[nearest_i]),'face_y_m':near_y,
                'ground_minus_face_y_m':float(ground)-near_y,'cell_range_rc':cand['cell_range_rc'][nearidx].astype(int).tolist()}
            inside_recs=[]
            for li in inside:
                idx=int(ix[li]); plane=cand['plane_y_xz'][idx]
                yy=float(plane[0]*xy[0]+plane[1]*xy[1]+plane[2])
                inside_recs.append({'object_id':int(cand['object_id'][idx]),'model':next(m['basename'] for m in index.manifest['models'] if m['model_id']==int(cand['model_id'][idx])),'face_id':int(cand['face_id'][idx]),'face_y_m':yy,'ground_minus_face_y_m':float(ground)-yy,'edge_distance_m':float(edge[li]),'barycentric':bary[li].tolist(),'cell_range_rc':cand['cell_range_rc'][idx].astype(int).tolist()})
            records.append({'kind':'physical' if kind==0 else 'visible','candidate_count':int(len(ix)),'inside':inside_recs,'nearest_candidate_in_query_window':near})
        static[sid]={'group_id':gid,'center_rc':[int(p['row']),int(p['col'])],'sample_xy':[float(p['x']),float(p['z'])],'static_faces':records}
    if gi%40==0: print(f'index_query_groups={gi+1}/{len(groups)} elapsed_s={time.perf_counter()-start:.2f}',flush=True)
if not index.reverify(): raise RuntimeError('index reverify failed')
# All source/index files that informed the result must be byte-stable across the analysis.
pins_end={str(p):sha(p) for p in readset_paths}
if pins_start != pins_end: raise AssertionError('analysis input readset changed during run')

# Group/phase comparisons.
byid={}
for r in log_rows: byid.setdefault(r['sample_id'],[]).append(r)
for sid,rr in byid.items(): rr.sort(key=lambda x:x['phase'])
false_samples=[]; false_group_summary=[]; phase_stats=[]
for phase in range(7):
    rr=[r for r in log_rows if r['phase']==phase]
    phase_stats.append({'phase':phase,'sea_level':phase_meta[phase]['sea_level'],'wave_current':phase_meta[phase]['wave_current'],'wave_max':phase_meta[phase]['wave_max'],'wind':phase_meta[phase]['wind'],'surface_is_sea_true':sum(r['sea_flag'] for r in rr),'surface_is_pond_true':sum(r['pond_flag'] for r in rr),'either_surface_flag_true':sum(r['sea_flag'] or r['pond_flag'] for r in rr),'ground_min_m':min(r['ground'] for r in rr),'ground_max_m':max(r['ground'] for r in rr),'depth_min_m':min(r['depth'] for r in rr),'depth_max_m':max(r['depth'] for r in rr),'withfake_minus_ground_min_m':min(r['with_fake']-r['ground'] for r in rr),'withfake_minus_ground_max_m':max(r['with_fake']-r['ground'] for r in rr),'depth_minus_withfake_minus_ground_min_m':min(r['depth']-(r['with_fake']-r['ground']) for r in rr),'depth_minus_withfake_minus_ground_max_m':max(r['depth']-(r['with_fake']-r['ground']) for r in rr)})
# Center diagnostics: keep SurfaceIsSea and SurfaceIsPond distinct.
centers=[p for p in point_rows if p['role']=='anomaly_center']
center_out=[]
for p in centers:
    rr=byid[p['sample_id']]
    face=static[p['sample_id']]['static_faces']
    center_out.append({'sample_id':p['sample_id'],'group_id':p['group_id'],'class':int(p['class']),'rc':[int(p['row']),int(p['col'])],'xy':[float(p['x']),float(p['z'])],'surface_is_sea_true_phases':[r['phase'] for r in rr if r['sea_flag']],'surface_is_pond_true_phases':[r['phase'] for r in rr if r['pond_flag']],'either_surface_flag_true_phases':[r['phase'] for r in rr if r['sea_flag'] or r['pond_flag']],'no_fake_range_m':[min(r['no_fake'] for r in rr),max(r['no_fake'] for r in rr)],'with_fake_range_m':[min(r['with_fake'] for r in rr),max(r['with_fake'] for r in rr)],'depth_range_m':[min(r['depth'] for r in rr),max(r['depth'] for r in rr)],'ground_m':rr[0]['ground'],'static_faces':face})# Label each runtime sample by exact face containment and phase stability.
sample_summary=[]
for p in point_rows:
    rr=byid[p['sample_id']]; sf=static[p['sample_id']]['static_faces']
    def krec(k):return next(x for x in sf if x['kind']==k)
    phys=krec('physical'); vis=krec('visible')
    stat=static[p['sample_id']]
    sample_summary.append({'sample_id':p['sample_id'],'role':p['role'],'group_id':p['group_id'],'class':int(p['class']),'rc':[int(p['row']),int(p['col'])],'ring_m':float(p['ring_m']),'offset_m':[float(p['dx_m']),float(p['dz_m'])],'xy':[float(p['x']),float(p['z'])],'surface_is_sea_true_phases':[r['phase'] for r in rr if r['sea_flag']],'surface_is_pond_true_phases':[r['phase'] for r in rr if r['pond_flag']],'either_surface_flag_true_phases':[r['phase'] for r in rr if r['sea_flag'] or r['pond_flag']],'no_fake_range_m':[min(r['no_fake'] for r in rr),max(r['no_fake'] for r in rr)],'with_fake_range_m':[min(r['with_fake'] for r in rr),max(r['with_fake'] for r in rr)],'depth_range_m':[min(r['depth'] for r in rr),max(r['depth'] for r in rr)],'ground_m':rr[0]['ground'],'depth_formula_max_abs_error_m':max(abs(r['depth']-(r['with_fake']-r['ground']-0.01)) for r in rr),'physical_containing_faces':phys['inside'],'visible_containing_faces':vis['inside'],'physical_nearest':phys['nearest_candidate_in_query_window'],'visible_nearest':vis['nearest_candidate_in_query_window']})

# Global flags and center anomaly partition.
center_absent=[r for r in center_out if not r['either_surface_flag_true_phases']]
center_present_ever=[r for r in center_out if r['either_surface_flag_true_phases']]
center_absent_static=[]
for r in center_absent:
    phys=r['static_faces'][0]; vis=r['static_faces'][1]
    center_absent_static.append({'sample_id':r['sample_id'],'group_id':r['group_id'],'rc':r['rc'],'class':r['class'],'surface_is_sea_true_phases':r['surface_is_sea_true_phases'],'surface_is_pond_true_phases':r['surface_is_pond_true_phases'],'physical_inside':phys['inside'],'visible_inside':vis['inside'],'physical_nearest':phys['nearest_candidate_in_query_window'],'visible_nearest':vis['nearest_candidate_in_query_window']})# Each absent center groups point offsets: count runtime positive by ring and static face coverage.
offset_by_ring={}
for r in sample_summary:
    if r['role']!='anomaly_offset':continue
    ring=f"{r['ring_m']:.2f}"
    acc=offset_by_ring.setdefault(ring,{'samples':0,'samples_with_either_flag_ever':0,'physical_contains':0,'visible_contains':0,'no_static_containment':0,'allphase_flags_false':0,'phase_variable':0})
    acc['samples']+=1
    acc['samples_with_either_flag_ever']+=bool(r['either_surface_flag_true_phases'])
    acc['physical_contains']+=bool(r['physical_containing_faces'])
    acc['visible_contains']+=bool(r['visible_containing_faces'])
    acc['no_static_containment']+=not (r['physical_containing_faces'] or r['visible_containing_faces'])
    acc['allphase_flags_false']+=not r['either_surface_flag_true_phases']
    acc['phase_variable']+=len(r['either_surface_flag_true_phases']) not in (0,7)
# controls
control_summary=[]
for p in point_rows:
    if p['role'].startswith('anomaly'): continue
    r=sample_summary[point_rows.index(p)]
    control_summary.append(r)
# Stats of all samples by flags and static geometry, clean listing of center classifications.
summary={
 'schema':'ev95.subcell-runtime-v2-analysis.v1','status':'COMPLETE','inputs':{},
 'method':{'index':'existing COMPLETE EV93 face-range index; one padded query window per point group; exact 2D triangle inclusion from compiled XYZ triangles; index remains broadphase only','nearest_distance_semantics':'nearest indexed triangle-edge candidate within the padded query window only; not a global nearest-face proof','sample_grid_mapping':'col=floor(X/6m); row=2047-floor(Z/6m); each per-group query window pads one cell around all sample cells','containment_tolerance_m2':1e-10,'not_a_water_visibility_inference':True},
 'integrity':{'runtime_header':log_header,'points':len(point_rows),'log_samples':len(log_rows),'phases':len(phase_meta),'groups':len(groups),'end_record':end_record,'complete_run_receipt':{'run_id':receipt_doc['Launch']['run_id'],'end_satisfied':receipt_doc['End']['satisfied'],'graceful_close':receipt_doc['Close']['graceful'],'stop_method':receipt_doc['Close']['stop_method'],'cleanup_degraded':receipt_doc['Final']['cleanup_degraded']},'phase_rows':{str(p):phase_meta[p]['end']['rows'] for p in sorted(phase_meta)},'sample_identity_phase_order_exact':True,'coords_match_points_csv_with_0.01m_log_formatter_tolerance':True,'max_log_coordinate_rounding_error_m':max_log_coord_delta_m,'index_reverify':True},
 'global':{'role_counts':{k:sum(p['role']==k for p in point_rows) for k in sorted({p['role'] for p in point_rows})},'groups_by_role':len(groups),'unique_classes':sorted(set(int(p['class']) for p in point_rows)),'runtime_surface_is_sea_true':sum(r['sea_flag'] for r in log_rows),'runtime_surface_is_pond_true':sum(r['pond_flag'] for r in log_rows),'runtime_either_surface_flag_true':sum(r['sea_flag'] or r['pond_flag'] for r in log_rows),'samples_ever_sea_flag_true':sum(any(r['sea_flag'] for r in byid[p['sample_id']]) for p in point_rows),'samples_ever_pond_flag_true':sum(any(r['pond_flag'] for r in byid[p['sample_id']]) for p in point_rows),'samples_ever_either_surface_flag_true':sum(any(r['sea_flag'] or r['pond_flag'] for r in byid[p['sample_id']]) for p in point_rows),'samples_never_either_surface_flag_true':sum(not any(r['sea_flag'] or r['pond_flag'] for r in byid[p['sample_id']]) for p in point_rows),'samples_phase_variable_either_surface_flags':sum(0<len([r for r in byid[p['sample_id']] if r['sea_flag'] or r['pond_flag']])<7 for p in point_rows),'water_formula_depth_vs_withfake_ground_minus_1cm_max_error_m':max(x['depth_formula_max_abs_error_m'] for x in sample_summary),'phase_stats':phase_stats,'offset_by_ring_m':offset_by_ring},
 'source_24_absence_crosswalk':{'source_classification_rows':len(classification_doc['rows']),'source_class_counts':{str(k):sum(int(x['class'])==k for x in classification_doc['rows']) for k in (1,3)},'source_rows_with_both_surface_flags_false':sum(x['runtime']['sea']=='False' and x['runtime']['pond']=='False' for x in classification_doc['rows']),'runtime_v2_class1_centers_tested':sum(int(p['class'])==1 for p in centers),'runtime_v2_class3_centers_tested':sum(int(p['class'])==3 for p in centers),'runtime_v2_class3_centers_unprobed':sum(int(x['class'])==3 for x in classification_doc['rows'])-sum(int(p['class'])==3 for p in centers),'runtime_v2_class1_center_ids':[{ 'sample_id':x['sample_id'],'rc':x['rc'],'sea_true_phases':x['surface_is_sea_true_phases'],'pond_true_phases':x['surface_is_pond_true_phases'],'physical_containment_count':len(x['static_faces'][0]['inside']),'visible_containment_count':len(x['static_faces'][1]['inside'])} for x in center_out if x['class']==1],'runtime_v2_class3_center_ids':[{'sample_id':x['sample_id'],'rc':x['rc'],'sea_true_phases':x['surface_is_sea_true_phases'],'pond_true_phases':x['surface_is_pond_true_phases'],'physical_containment_count':len(x['static_faces'][0]['inside']),'visible_containment_count':len(x['static_faces'][1]['inside']),'ground_m':x['ground_m'],'face_y_m':sorted({round(f['face_y_m'],9) for layer in x['static_faces'] for f in layer['inside']}),'depth_range_m':x['depth_range_m']} for x in center_out if x['class']==3]},'anomaly_centers':{'count':len(centers),'never_either_surface_flag_count':len(center_absent),'ever_either_surface_flag_count':len(center_present_ever),'never_present_static_face_partition':center_absent_static},
 'controls':control_summary,'samples':sample_summary,'center_runtime_detail':center_out,
 'pins':{'readset_start':pins_start,'readset_end':pins_end,'index_manifest_sha256':manifest_sha,'index_source_sha256':sha(INDEX_SRC),'index_base_identity':manifest_doc['base_identity'],'face_index_counts':manifest_doc['counts'],'face_index_object_count':manifest_doc['object_count'],'stage_world_sha':stage_doc['world_sha'],'stage_water_sha':stage_doc['water_sha'],'wrp_source_path':str(WRP_SOURCE),'world_pbo_path':str(WORLD_PBO),'water_pbo_path':str(WATER_PBO)}
}
OUT.write_text(json.dumps(summary,indent=2,ensure_ascii=False,allow_nan=False)+chr(10),encoding='utf-8')
print(json.dumps({'output':str(OUT),'output_sha256':sha(OUT),'elapsed_s':round(time.perf_counter()-start,3),'points':len(point_rows),'groups':len(groups),'face_index':summary['pins']['index_manifest_sha256'],'runtime':summary['global'],'center_absent':len(center_absent),'center_absent_static':[(r['sample_id'],len(r['physical_inside']),len(r['visible_inside'])) for r in center_absent_static]},indent=2,ensure_ascii=False),flush=True)













