from __future__ import annotations
import hashlib, importlib.util, json, csv, time
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
from scipy.ndimage import distance_transform_edt, label

OUT=Path(__file__).resolve().parent
ROOT=Path(r'E:/DayZ-Baltic-Build')
EV87=ROOT/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
H=ROOT/'v30-global-bank-extension-20261010/global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz'
C=ROOT/'v30-narva-dry-bank-relief-20261010/constraints.npz'
P=ROOT/'v30-global-bank-extension-20261010/build-focal/candidate/plane.npy'
F=ROOT/'v30-global-bank-extension-20261010/build-focal/candidate/visible-field.npy'
SEA_LOG=ROOT/'v30-global-bank-extension-20261010/build-selected/native-snapshot.log'
SEA_CLASS_SOURCE=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain/build_v30_water.py')
ROAD=Path(r'P:/DayZ_Baltic_12km_dev/tests/regional_foundation_roads_v6/reference.npz')
CENSUS=ROOT/'v30-global-bank-extension-20261010/ev95-global-shape-census/report.json'
CENSUS_SCRIPT=ROOT/'v30-global-bank-extension-20261010/ev95-global-shape-census/census_ev95.py'
SCRIPT=Path(__file__).resolve()
EXPECTED={
 'EV87':'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
 'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 'EV95':'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
 'constraints':'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
 'P':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 'F':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
 'sea_class_source':'3897e05e2cd5789a42f66825c650589a7c04509a6f5736811f4999cc89730b94',
}
N=2048; CELL=6.; Z0=12282.; CLEARANCE_LABEL_TOL=1e-4
FAMILIES=('diag','vertical','horizontal')
TRIS=((0,1,3),(0,2,3)); OFFSETS=((0,0),(0,1),(1,0),(1,1))

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def load_module(path,name):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def js(v):
 if isinstance(v,(np.integer,)):return int(v)
 if isinstance(v,(np.floating,)):return float(v)
 if isinstance(v,(np.bool_,)):return bool(v)
 raise TypeError(type(v).__name__)
def hinge_vertices(kind,r,c):
 if kind=='diag':return ((r,c),(r,c+1),(r+1,c),(r+1,c+1))
 if kind=='vertical':return ((r,c),(r,c+1),(r+1,c+1),(r+1,c+2))
 return ((r,c),(r+1,c),(r+1,c+1),(r+2,c+1))
def adjacent_triangles(kind,r,c):
 if kind=='diag':return [((r,c),TRIS[0]),((r,c),TRIS[1])]
 if kind=='vertical':return [((r,c),TRIS[0]),((r,c+1),TRIS[1])]
 return [((r,c),TRIS[1]),((r+1,c),TRIS[0])]
def water_eval(levels,hs):
 if levels is None:return {'known':False,'status':'unknown','under':False,'emergent':False,'crossing':False,'contact':False,'near_1e-4':False,'clearance_min_m':None,'clearance_max_m':None}
 d=np.asarray(levels,dtype=np.float64)-np.asarray(hs,dtype=np.float64)
 crossing=any(d[i]*d[j]<0.0 for i,j in ((0,1),(1,2),(2,0)))
 contact=bool(np.any(d==0.0)); under=bool(np.all(d>0.0)); emergent=bool(np.any(d<0.0))
 status='under' if under else ('crossing' if crossing else ('contact' if contact else ('emerged' if np.all(d<0.0) else 'mixed')))
 return {'known':True,'status':status,'under':under,'emergent':emergent,'crossing':bool(crossing),'contact':contact,
         'near_1e-4':bool(np.min(np.abs(d))<=CLEARANCE_LABEL_TOL),
         'clearance_min_m':float(d.min()),'clearance_max_m':float(d.max())}
def fixtures():
 assert water_eval([2.,2.,2.],[1.,0.,1.])['under']
 assert water_eval([0.,2.,0.],[1.,1.,1.])['crossing']
 assert water_eval([0.,0.,0.],[1.,1.,1.])['status']=='emerged'
 assert water_eval([1.,1.,1.],[1.,0.,1.])['contact']
 assert not water_eval(None,[0.,0.,0.])['known']
 # P is cell-constant while F remains the exact per-corner triangle field.
 assert water_eval([2.,2.,2.],[1.,1.,1.])['under']
 assert water_eval([2.,0.,2.],[1.,1.,1.])['crossing']
 return {'uniform_under_positive':True,'triangle_crossing_positive':True,'emerged_positive':True,
         'zero_contact_positive':True,'missing_data_unknown_positive':True,'P_constant_vs_F_per_corner_not_averaged':True}

def sea_values(sea_log):
 line=next((x.strip() for x in sea_log.read_text(encoding='utf-8').splitlines() if x.startswith('SEA;')),None)
 if line is None:raise AssertionError('native SEA record absent')
 vals=[float(x) for x in line.split(';')[1:]]
 if len(vals)!=4:raise AssertionError('unexpected SEA record shape')
 # min,max,current,waveMax as emitted by mission init.c
 return {'min_m':vals[0],'max_m':vals[1],'current_m':vals[2],'wave_max_m':vals[3],'record':line}
def classify_triangle(kind,cell,tri,h,p,f,cls,sea):
 r,c=cell; coords=[(r+OFFSETS[i][0],c+OFFSETS[i][1]) for i in tri]
 hv=np.asarray([h[rr,cc] for rr,cc in coords],dtype=np.float64)
 out={}
 pv=float(p[r,c]); out['P']=water_eval([pv]*3,hv) if np.isfinite(pv) else water_eval(None,hv)
 fv=np.asarray([f[r,c,i] for i in tri],dtype=np.float64)
 out['F']=water_eval(fv,hv) if np.isfinite(fv).all() else water_eval(None,hv)
 cls_v=np.asarray([cls[rr,cc] for rr,cc in coords],dtype=np.uint8)
 all_sea=bool(np.all(cls_v==1)); any_sea=bool(np.any(cls_v==1))
 out['SEA']={
  'all_ocean_class':all_sea,'partial_ocean_class':bool(any_sea and not all_sea),
  'current':water_eval([sea['current_m']]*3,hv) if all_sea else water_eval(None,hv),
  'minimum':water_eval([sea['min_m']]*3,hv) if all_sea else water_eval(None,hv),
  'maximum':water_eval([sea['max_m']]*3,hv) if all_sea else water_eval(None,hv),
 }
 out['coords_rc']=[list(x) for x in coords]
 out['h_m']=[float(x) for x in hv]
 out['P_level_m']=pv if np.isfinite(pv) else None
 out['F_levels_m']=[float(v) if np.isfinite(v) else None for v in fv]
 out['P_signed_clearance_m']=[float(pv-x) for x in hv] if np.isfinite(pv) else None
 out['F_signed_clearance_m']=[float(v-x) if np.isfinite(v) else None for v,x in zip(fv,hv)]
 out['known_field_count']=int(out['P']['known']+out['F']['known']+out['SEA']['current']['known'])
 out['water_context']=bool(np.any(cls_v!=0))
 return out

def classify_hinge(kind,r,c,h,p,f,cls,water):
 tris=[classify_triangle(kind,cell,tri,h,p,f,cls,SEA) for cell,tri in adjacent_triangles(kind,r,c)]
 layer_pairs={}
 for name in ('P','F'):
  a,b=(t[name] for t in tris)
  layer_pairs[name]={'both_under':bool(a['known'] and b['known'] and a['under'] and b['under']),
    'any_emergent_vertex':bool((a['known'] and a['emergent']) or (b['known'] and b['emergent'])),
    'any_crossing':bool((a['known'] and a['crossing']) or (b['known'] and b['crossing'])),
    'any_contact':bool((a['known'] and a['contact']) or (b['known'] and b['contact'])),
    'known_triangles':int(a['known'])+int(b['known'])}
 for name,levelkey in [('SEA_current','current'),('SEA_minimum','minimum'),('SEA_maximum','maximum')]:
  a,b=(t['SEA'][levelkey] for t in tris)
  layer_pairs[name]={'both_under':bool(a['known'] and b['known'] and a['under'] and b['under']),
    'any_emergent_vertex':bool((a['known'] and a['emergent']) or (b['known'] and b['emergent'])),
    'any_crossing':bool((a['known'] and a['crossing']) or (b['known'] and b['crossing'])),
    'any_contact':bool((a['known'] and a['contact']) or (b['known'] and b['contact'])),
    'known_triangles':int(a['known'])+int(b['known'])}
 full_cover=any(v['both_under'] for v in layer_pairs.values())
 pf_missing=any((not t['P']['known']) or (not t['F']['known']) for t in tris)
 water_context=any(t['water_context'] for t in tris)
 unknown_water=bool(pf_missing and water_context and not all(t['SEA']['current']['known'] for t in tris))
 crossing_pf=layer_pairs['P']['any_crossing'] or layer_pairs['F']['any_crossing']
 crossing_sea=any(layer_pairs[k]['any_crossing'] for k in ('SEA_current','SEA_minimum','SEA_maximum'))
 emergent=any(v['any_emergent_vertex'] for v in layer_pairs.values())
 both_faces_some_known=all(t['known_field_count']>0 for t in tris)
 if full_cover: primary='fully_under_one_known_layer'
 elif unknown_water: primary='P_F_unknown_on_water_context'
 elif crossing_pf or crossing_sea: primary='known_waterline_crossing'
 elif emergent: primary='emerged_above_known_sheet'
 elif both_faces_some_known: primary='known_mixed_or_contact'
 else: primary='no_active_water_sheet_on_dry_context'
 return {'primary':primary,'fully_under_one_known_layer':bool(full_cover),'pf_unknown_on_water_context':unknown_water,
   'pf_sample_missing':bool(pf_missing),'known_waterline_crossing_PF':bool(crossing_pf),
   'known_waterline_crossing_SEA':bool(crossing_sea),'any_known_sheet_emergence':bool(emergent),
   'both_faces_have_some_known_sheet':bool(both_faces_some_known),'layer_pairs':layer_pairs,'triangles':tris}

def main():
 t0=time.perf_counter(); paths={'EV87':EV87,'B':B,'EV95':H,'constraints':C,'P':P,'F':F,'sea_snapshot':SEA_LOG,'sea_class_source':SEA_CLASS_SOURCE,'roads_reference':ROAD,'census_report':CENSUS,'census_script':CENSUS_SCRIPT,'classifier_script':SCRIPT}
 start={k:sha(v) for k,v in paths.items()}
 for key,val in EXPECTED.items():
  if start[key]!=val:raise AssertionError(f'{key} pin mismatch {start[key]}')
 ev=load_module(EV87,'ev87_exposure_census')
 with np.load(B,allow_pickle=False) as z:
  base={k:z[k] for k in z.files}; hb=base['heights']; cls=base['cls']; water=base['water']
 with np.load(H,allow_pickle=False) as z: hh=z['heights']
 if hb.shape!=(N,N) or hh.shape!=hb.shape or hb.dtype!=np.float32 or hh.dtype!=np.float32:raise AssertionError('terrain grid mismatch')
 with np.load(C,allow_pickle=False) as zc: cons={k:zc[k] for k in zc.files}
 p=np.load(P,allow_pickle=False); f=np.load(F,allow_pickle=False)
 if p.shape!=(N-1,N-1) or f.shape!=(N-1,N-1,4) or p.dtype!=np.float64 or f.dtype!=np.float64:raise AssertionError('P/F must retain native float64 arrays')
 if np.isinf(p).any() or np.isinf(f).any():raise AssertionError('P/F contains infinity')
 SEA=sea_values(SEA_LOG)
 with np.load(ROAD,allow_pickle=False) as zr: roads=zr['corridor'].astype(bool)
 if roads.shape!=(N,N):raise AssertionError('road mask shape mismatch')
 pop=ev._ev87_populations({'cls':cls,'reserve':base['reserve'],'platform':base['platform']},{'wet_support':cons['wet_support']})
 masks={'dry':pop['bank']|pop['interior'],'bank':pop['bank'],'interior':pop['interior'],'wet_support':cons['wet_support'].astype(bool),
   'civil_guard':(cons['other_fixed']|cons['engineering_halo']|cons['narva']|base['reserve']|base['platform']|roads),
   'other_fixed':cons['other_fixed'].astype(bool),'engineering_halo':cons['engineering_halo'].astype(bool),
   'road_corridor':roads,'reserve':base['reserve'].astype(bool),'platform':base['platform'].astype(bool),
   'narva':cons['narva'].astype(bool),'water_nodes':water.astype(bool)}
 for name,m in masks.items():
  if m.shape!=(N,N):raise AssertionError(f'mask shape mismatch {name}')
 # The census itself supplies the pinned count and source-family identities. Recompute EV95 angles to recover every residual hinge.
 census=json.loads(CENSUS.read_text(encoding='utf-8'))
 if census.get('status')!='COMPLETE_OFFLINE_CENSUS' or census['terrain']['EV95_sha256']!=start['EV95']:raise AssertionError('census report identity/status mismatch')
 b_ang=dict(ev.edge_angles(hb.astype(np.float64))); h_ang=dict(ev.edge_angles(hh.astype(np.float64)))
 if sum(int(np.count_nonzero(a>30.0)) for a in h_ang.values())!=11890:raise AssertionError('residual >30° count drift from requested 11890')
 family_rows={}; records=[]; mask_hits={k:Counter() for k in masks}; groups=Counter(); exposure_counts=Counter(); exposure_by_family=defaultdict(Counter)
 shoreline_masks={}; cluster_reports={}; emitted=[]
 cellwater=np.isfinite(p)|np.any(np.isfinite(f),axis=2)
 water_dist=distance_transform_edt(cellwater)*CELL
 for kind in FAMILIES:
  arr=h_ang[kind]; old=b_ang[kind]; rr,cc=np.where(arr>30.0); shoreline_mask=np.zeros(arr.shape,dtype=bool)
  for r,c in zip(rr.tolist(),cc.tolist()):
   verts=hinge_vertices(kind,r,c)
   # Reconcile exact four-vertex convention with EV87's incidence slices.
   if any(not (0<=vr<N and 0<=vc<N) for vr,vc in verts):raise AssertionError('hinge vertex out of grid')
   angmask={name:bool(any(m[vr,vc] for vr,vc in verts)) for name,m in masks.items()}
   result=classify_hinge(kind,r,c,hh,p,f,cls,water)
   oldres=classify_hinge(kind,r,c,hb,p,f,cls,water)
   class_cross=False
   for tri_rec in result['triangles']:
    qcoords=[tuple(v) for v in tri_rec['coords_rc']]
    for i,j in ((0,1),(1,2),(2,0)):
     if bool(water[qcoords[i]])!=bool(water[qcoords[j]]):class_cross=True
   crossing=bool(result['known_waterline_crossing_PF'] or result['known_waterline_crossing_SEA'])
   shoreline=bool(crossing or class_cross)
   if shoreline:shoreline_mask[r,c]=True
   for name,hit in angmask.items():
    if hit:mask_hits[name][result['primary']]+=1
   exposure_counts[result['primary']]+=1;exposure_by_family[kind][result['primary']]+=1
   cells=[cell for cell,_ in adjacent_triangles(kind,r,c)]
   covered_cells=[(cr,cc0) for cr,cc0 in cells if cellwater[cr,cc0]]
   widthpx=max([float(water_dist[cr,cc0]) for cr,cc0 in covered_cells],default=0.)
   rec={'family':kind,'anchor_rc':[r,c],'anchor_xz_m':[float(c*CELL),float(Z0-r*CELL)],
    'angle_EV95_deg':float(arr[r,c]),'angle_B_deg':float(old[r,c]),'delta_EV95_minus_B_deg':float(arr[r,c]-old[r,c]),
    'mask_any4':angmask,'exposure':result,'exposure_B':oldres,
    'touches_PF_or_SEA_waterline':crossing,'touches_water_class_boundary':class_cross,
    'touches_design_shoreline':shoreline,'water_design_cell_edge_distance_proxy_m':widthpx}
   records.append(rec)
   if result['any_known_sheet_emergence'] and shoreline:emitted.append(rec)
  shoreline_masks[kind]=shoreline_mask
  lab,ncomp=label(shoreline_mask,structure=np.ones((3,3),dtype=np.uint8))
  sizes=np.bincount(lab.ravel())[1:]
  components=[]
  if ncomp:
   for compid in np.argsort(sizes)[-10:][::-1]+1:
    cr,cc0=np.where(lab==compid)
    components.append({'hinges':int(len(cr)),'anchor_bounds_rc':[int(cr.min()),int(cr.max()),int(cc0.min()),int(cc0.max())],
     'world_bounds_xz_m':[float(cc0.min()*CELL),float((Z0-cr.max()*CELL)),float(cc0.max()*CELL),float((Z0-cr.min()*CELL))]})
  cluster_reports[kind]={'shoreline_crossing_or_water_class_boundary_residual_hinges':int(shoreline_mask.sum()),'eight_connected_component_count':int(ncomp),'largest_components':components}
  family_rows[kind]={'residual_over30':int(len(rr)),'primary_categories':dict(exposure_by_family[kind]),'design_shoreline_residual_hinges':int(shoreline_mask.sum())}
 # Compute overlapping populations for all residuals, by category, and save full machine-readable rows.
 pop_counts={}
 for name in masks:
  vals=[x for x in records if x['mask_any4'][name]]
  pop_counts[name]={'residual_hinges':len(vals),'primary_categories':dict(Counter(x['exposure']['primary'] for x in vals)),
   'fully_under_one_layer':sum(x['exposure']['fully_under_one_known_layer'] for x in vals),
   'has_PF_unknown_on_water':sum(x['exposure']['pf_unknown_on_water_context'] for x in vals),
   'has_emergent_vertex':sum(x['exposure']['any_known_sheet_emergence'] for x in vals),
   'known_waterline_crossing':sum(x['touches_PF_or_SEA_waterline'] for x in vals),
   'design_shoreline_boundary':sum(x['touches_design_shoreline'] for x in vals)}
 def top_key(x):return x['angle_EV95_deg']
 emerged_shore=sorted(emitted,key=top_key,reverse=True)
 overall_exposure={
  'residual_over30':len(records),'fully_under_one_known_layer':sum(x['exposure']['fully_under_one_known_layer'] for x in records),
  'has_PF_unknown_on_water':sum(x['exposure']['pf_unknown_on_water_context'] for x in records),
  'has_any_PF_sample_missing':sum(x['exposure']['pf_sample_missing'] for x in records),
  'has_emergent_vertex_relative_to_known_sheet':sum(x['exposure']['any_known_sheet_emergence'] for x in records),
  'touches_known_PF_or_SEA_waterline':sum(x['touches_PF_or_SEA_waterline'] for x in records),
  'touches_water_class_boundary':sum(x['touches_water_class_boundary'] for x in records),
  'touches_design_shoreline':sum(x['touches_design_shoreline'] for x in records),
  'primary_categories':dict(exposure_counts),
  'layer_summary':{}
 }
 for layer in ('P','F','SEA_current','SEA_minimum','SEA_maximum'):
  under=sum(x['exposure']['layer_pairs'][layer]['both_under'] for x in records)
  emergence=sum(x['exposure']['layer_pairs'][layer]['any_emergent_vertex'] for x in records)
  crossing=sum(x['exposure']['layer_pairs'][layer]['any_crossing'] for x in records)
  known_triangles=sum(x['exposure']['layer_pairs'][layer]['known_triangles'] for x in records)
  overall_exposure['layer_summary'][layer]={'both_triangles_under':int(under),'any_emergent_vertex':int(emergence),'crossing':int(crossing),'known_triangle_count':int(known_triangles)}
 # Top 20 current emerged shorelines, plus controls showing highest residuals with no exposure crossing.
 top20=[]
 for x in emerged_shore[:20]:
  exp=x['exposure']; top20.append({k:x[k] for k in ('family','anchor_rc','anchor_xz_m','angle_EV95_deg','angle_B_deg','delta_EV95_minus_B_deg','mask_any4','touches_PF_or_SEA_waterline','touches_water_class_boundary','touches_design_shoreline','water_design_cell_edge_distance_proxy_m')}|
   {'primary':exp['primary'],'fully_under_one_known_layer':exp['fully_under_one_known_layer'],'pf_unknown_on_water_context':exp['pf_unknown_on_water_context'],'triangles':exp['triangles']})
 tops_dry=[x for x in records if not x['touches_PF_or_SEA_waterline'] and not x['exposure']['fully_under_one_known_layer']]
 tops_dry=sorted(tops_dry,key=top_key,reverse=True)[:20]
 top_dry=[{k:x[k] for k in ('family','anchor_rc','anchor_xz_m','angle_EV95_deg','angle_B_deg','mask_any4','water_design_cell_edge_distance_proxy_m')}|
  {'primary':x['exposure']['primary'],'pf_unknown_on_water_context':x['exposure']['pf_unknown_on_water_context'],'triangles':x['exposure']['triangles']} for x in tops_dry]
 pins_end={k:sha(v) for k,v in paths.items()}
 if start!=pins_end:raise AssertionError('input readset drift')
 # Verify selected incidence ANY against EV87 helper for each family using all masks.
 incidence_checks={}
 for kind in FAMILIES:
  for name,m in masks.items():
   expected=np.logical_or.reduce(ev.edge_vertex_slices(m,kind))
   got=np.zeros(expected.shape,dtype=bool)
   for rec in records:
    if rec['family']==kind and rec['mask_any4'][name]:
     r,c=rec['anchor_rc'];got[r,c]=True
   if not np.array_equal(got & (h_ang[kind]>30.0),expected & (h_ang[kind]>30.0)):
    raise AssertionError(f'incidence ANY mismatch {kind}/{name}')
   incidence_checks[f'{kind}/{name}']=int(np.count_nonzero(got))
 # CSV keeps one row per residual hinge; detailed 2-triangle payload stays in JSON for compactness.
 csv_path=OUT/'residual-hinges.csv'
 with csv_path.open('w',newline='',encoding='utf-8') as fcsv:
  w=csv.writer(fcsv);w.writerow(['family','row','col','x_m','z_m','angle_EV95_deg','angle_B_deg','delta_deg','primary','fully_under_one_layer','pf_unknown_on_water','PF_crossing','SEA_crossing','water_class_boundary','emergent_known_sheet','dry','bank','interior','wet_support','civil_guard','water_design_cell_edge_distance_proxy_m'])
  for x in records:
   e=x['exposure'];m=x['mask_any4'];w.writerow([x['family'],*x['anchor_rc'],*x['anchor_xz_m'],format(x['angle_EV95_deg'],'.12g'),format(x['angle_B_deg'],'.12g'),format(x['delta_EV95_minus_B_deg'],'.12g'),e['primary'],int(e['fully_under_one_known_layer']),int(e['pf_unknown_on_water_context']),int(e['known_waterline_crossing_PF']),int(e['known_waterline_crossing_SEA']),int(e['any_known_sheet_emergence']),int(m['dry']),int(m['bank']),int(m['interior']),int(m['wet_support']),int(m['civil_guard']),format(x['water_design_cell_edge_distance_proxy_m'],'.8g')])
 pins={k:{'path':str(v),'sha256':start[k]} for k,v in paths.items()}
 report={'schema':'ev95.residual_hinge_exposure.v1','status':'COMPLETE_DIAGNOSTIC_ONLY','claim_limit':'P/F/SEA design-field exposure of raster terrain triangles; does not query compiled ODOL clipping or prove rendered visibility/artistic defect. Primary categories are diagnostic; layer flags overlap. The 1e-4m value only labels near-contact.',
  'inputs':pins,'source_readset_start':start,'source_readset_end':pins_end,
  'sea_source':{'class_mask_source_path':str(SEA_CLASS_SOURCE),'class_mask_source_sha256':start['sea_class_source'],'snapshot_path':str(SEA_LOG),'record':SEA['record'],'min_m':SEA['min_m'],'max_m':SEA['max_m'],'current_m':SEA['current_m'],'wave_max_m':SEA['wave_max_m'],'scope':'SEA levels come from the pinned native snapshot. SEA is applied as a continuous face only when all three triangle vertices have cls==1; cls==1 sea-mask derivation is anchored to build_v30_water.py:293-314. Mixed ocean-class triangles are not treated as fully covered.'},
  'method':{'residual_selector':'EV87.edge_angles(EV95 heights promoted float32→float64), strict angle>30.0°; exact residual count reconciles the pinned census report.',
   'families':'diag, vertical, horizontal with exact two native NW-SE terrain triangles per hinge; P is its cell float64 scalar, F is the actual three per-corner float64 samples for that triangle; no averaging across cells/faces.',
   'triangle_rule':'signed clearance = water_level - H at its three actual raster vertices; affine field means all three positive => fully below that sheet; mixed signs => edge crossing; negative => an emerged vertex. Exact zero is contact.',
   'near_tolerance_m':CLEARANCE_LABEL_TOL,'masks':'ANY of exact 4 hinge vertices. dry/bank/interior use EV87._ev87_populations; wet_support is EV79 constraints; civil_guard is union of EV79 other_fixed, engineering_halo, narva, B reserve/platform, and road reference corridor.',
   'water_width_proxy':'distance transform to nearest cell without finite P or any finite F, sampled at adjacent triangle cells; approximate cell-center radius only, not source river polygon width.',
   'not_loaded':'compiled ODOL face index; this is a design-field/terrain comparison, not native mesh intersection. A water-class boundary is not itself proof of an actual rendered shoreline.'},
  'fixtures':fixtures(),'reconciliation':{'requested_EV95_over30':11890,'recomputed_EV95_over30':len(records),'residual_csv_rows':len(records),'incidence_ANY_matches_EV87_for_masks':True,'incidence_checked_counts_on_residuals':incidence_checks},
  'overall':overall_exposure,'by_family':family_rows,'by_overlapping_population':pop_counts,'shoreline_clusters_by_family':cluster_reports,
  'water_design_support_radius_proxy':{'n_positive':int(sum(x['water_design_cell_edge_distance_proxy_m']>0 for x in records)),
    'percentiles_m':{str(q):float(np.percentile([x['water_design_cell_edge_distance_proxy_m'] for x in records if x['water_design_cell_edge_distance_proxy_m']>0],q)) for q in (0,50,90,99,100)},
    'bins_m':{'le_6':int(sum(0<x['water_design_cell_edge_distance_proxy_m']<=6 for x in records)),
      'gt_6_le_12':int(sum(6<x['water_design_cell_edge_distance_proxy_m']<=12 for x in records)),
      'gt_12':int(sum(x['water_design_cell_edge_distance_proxy_m']>12 for x in records))}},
  'top20_emerged_shoreline':top20,'top20_not_covered_no_field_crossing':top_dry,
  'timing_seconds':round(time.perf_counter()-t0,3),'csv_path':str(csv_path)}
 out=OUT/'report.json';out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({'status':report['status'],'residual_count':len(records),'overall':overall_exposure,'by_family':family_rows,'by_population':pop_counts,'clusters':cluster_reports,'top20_count':len(top20),'report':str(out),'csv':str(csv_path),'timing_s':report['timing_seconds']},indent=2,allow_nan=False))
if __name__=='__main__':
 # initialize SEA at module level for classifier after validating source log at run start
 SEA=sea_values(SEA_LOG)
 main()


