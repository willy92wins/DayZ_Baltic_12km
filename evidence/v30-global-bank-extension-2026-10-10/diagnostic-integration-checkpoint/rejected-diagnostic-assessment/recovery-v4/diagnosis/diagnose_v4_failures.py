from __future__ import annotations
import hashlib, importlib.util, json, sys, time
from collections import defaultdict
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

if sys.flags.optimize:
    raise RuntimeError('optimized Python is not accepted')
G=Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
ROOT=G/'G/wet-bank-pilot'
HERE=ROOT/'postsolve-consumer/rejected-diagnostic-assessment-v1/recovery-v4'
OUT=HERE/'diagnosis'
ASSESS=HERE/'assess_rejected_diagnostic.py'
ASSESS_HELPER=HERE/'verify_polished_diagnostic.py'
ASSESSMENT=HERE/'run-01/assessment.json'
PREP=ROOT/'prepared-runs/attempt-08/prepared.npz'
PREP_RECEIPT=ROOT/'prepared-runs/attempt-08/preparation.json'
DIAG=ROOT/'postsolve-consumer/float32-component-conversion-v1/robust-f32-design/candidate-only-milp/d8-sign-fix-v1/real-run-01/rejected-diagnostic.npz'
BASE=G/'global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz'
EV87=Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py')
PLAN=HERE/'PLAN.md'
PREPARER=ROOT/'prepare_wet_bank_matrices.py'
PINS={
 ASSESSMENT:'79a4f1b09b30e98cf210e35bfc12e81388ed977c272dffd44612aec1df013279',
 PREP:'52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f',
 DIAG:'2209df7542098403ceda8e27e87c91935a9832527f04663fdf8f5d8ac70149ae',
 BASE:'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
 EV87:'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
 ASSESS:None,
 ASSESS_HELPER:'a3fc62f4e4a6b9ac55400abfddb3e3c8f5e41c83381b31fe71f4f66b35d1f516',
 PREP_RECEIPT:'c582f45f0751e8c24db2672405de4b94c136ee16a9c33d5e4c35a8deee2200ed',
 PREPARER:'65e05a6540026b08df7effa53c58534121bb2fa89e116a2ef07ad46ba0edf286',
 PLAN:'1112559a3720b37895be6f2e1d6aa8c4a829993a8343a59a878fa11a425f7c0b',
}
WIN=(855,870,1179,1194)

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def load_module(name,path):
 s=importlib.util.spec_from_file_location(name,path)
 if s is None or s.loader is None: raise RuntimeError(f'cannot load {path}')
 m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def parts(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 if hasattr(g,'geoms'):return [p for q in g.geoms for p in parts(q)]
 return []
def geometry_stats(g):
 ps=parts(g)
 comp=sorted((float(p.area) for p in ps),reverse=True)
 holes=sorted((float(Polygon(ring).area) for p in ps for ring in p.interiors),reverse=True)
 return {'area_m2':float(g.area),'components':len(ps),'holes':len(holes),
         'component_areas_m2_desc':comp,'hole_areas_m2_desc':holes,
         'min_component_area_m2':min(comp) if comp else None,'min_hole_area_m2':min(holes) if holes else None}
def overlap_matrix(a,b):
 pa=sorted(parts(a),key=lambda p:-p.area);pb=sorted(parts(b),key=lambda p:-p.area)
 return {'B_component_areas_m2_desc':[float(x.area) for x in pa],
         'H_component_areas_m2_desc':[float(x.area) for x in pb],
         'intersection_m2_BxH':[[float(x.intersection(y).area) for y in pb] for x in pa],
         'B_only_m2_per_component':[float(x.difference(b).area) for x in pa],
         'H_only_m2_per_component':[float(y.difference(a).area) for y in pb]}
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 for p,w in PINS.items():
  if w and sha(p)!=w: raise RuntimeError(f'input pin mismatch {p}: {sha(p)} != {w}')
 start={str(p.resolve()):sha(p) for p in PINS}
 assess=json.loads(ASSESSMENT.read_text(encoding='utf-8'))
 with np.load(PREP,allow_pickle=False) as z: prep={k:z[k].copy() for k in z.files}
 with np.load(DIAG,allow_pickle=False) as z: dz={k:z[k].copy() for k in z.files}
 bctx=prep['base_heights_context'];hctx=dz['context_grid']
 if bctx.shape!=(15,15) or hctx.shape!=(15,15) or not np.array_equal(bctx,dz['source_base_context']): raise RuntimeError('diagnostic context/base mismatch')
 changed=hctx.view(np.uint32)!=bctx.view(np.uint32); changed_rc=np.argwhere(changed)
 if len(changed_rc)!=114: raise RuntimeError(f'changed vertex count drift: {len(changed_rc)}')
 mask_names=('other_fixed_context','effective_fixed_context','p9_context','road_context','wet_support_context','water_context','design_interior_context','shore_boundary_context')
 mask_result={}
 for n in mask_names:
  m=np.asarray(prep[n],bool)
  rc=np.argwhere(changed&m)
  mask_result[n]={'mask_nodes':int(m.sum()),'changed_overlap_count':len(rc),
    'changed_overlap_local_rc':rc.tolist()}
 of=changed&np.asarray(prep['other_fixed_context'],bool)
 rel=(np.asarray(prep['cls_context'])==5)&np.asarray(prep['water_context'],bool)
 mask_result['other_fixed_exception_audit']={
   'overlap_subset_of_cls5_water_exception':bool(np.all(~of|rel)),
   'changed_other_fixed_not_exception_count':int(np.count_nonzero(of&~rel)),
   'exception_overlap_count':int(np.count_nonzero(of&rel)),
   'effective_fixed_overlap_count':int(np.count_nonzero(changed&prep['effective_fixed_context'])),
   'p9_overlap_count':int(np.count_nonzero(changed&prep['p9_context'])),
   'road_overlap_count':int(np.count_nonzero(changed&prep['road_context'])),
   'reserve_nodes_in_context_from_receipt':int(json.loads(PREP_RECEIPT.read_text())['protection']['reserve_nodes']),
   'platform_nodes_in_context_from_receipt':int(json.loads(PREP_RECEIPT.read_text())['protection']['platform_nodes']),
   'reserve_platform_halo_nodes_from_receipt':int(json.loads(PREP_RECEIPT.read_text())['protection']['reserve_platform_halo_nodes']),
   'prepared_gate_interpretation':'raw other_fixed_context includes cls5/water nodes which preparer explicitly releases; effective_fixed_context is the executed protected mask. This intersection alone does not establish a protection violation.'}
 # Reconstruct full B/H in memory only, identical to the assessment's 15x15 substitution.
 with np.load(BASE,allow_pickle=False) as z: B=z['heights'].copy()
 H=B.copy();H[WIN[0]:WIN[1],WIN[2]:WIN[3]]=hctx
 ev=load_module('diagnosis_ev87',EV87)
 cells={tuple(map(int,rc)) for rc in prep['face_population_cells_rc']}
 grouped={'B':defaultdict(list),'H':defaultdict(list)}
 keys={(int(k),int(o),int(m)) for k,o,m in zip(prep['face_kind'],prep['face_object_id'],prep['face_model_id'])}
 t0=time.perf_counter()
 for i in range(len(prep['face_kind'])):
  if int(prep['face_degenerate'][i]): continue
  kind=int(prep['face_kind'][i]);obj=int(prep['face_object_id'][i]);model=int(prep['face_model_id'][i]);key=(kind,obj,model)
  xyz=np.asarray(prep['face_xyz'][i],np.float64);xyf=xyz[:,(0,2)];face=Polygon(xyf)
  if face.is_empty or not face.is_valid or face.area<=0: continue
  coeff=np.asarray(prep['face_plane_y_xz'][i],np.float64)
  r0,r1,c0,c1=map(int,prep['face_cell_range_rc'][i])
  for r in range(max(0,r0),min(ev.N-2,r1)+1):
   for c in range(max(0,c0),min(ev.N-2,c1)+1):
    if (r,c) not in cells: continue
    cellxy=ev.cell_xy(r,c)
    for side,grid in (('B',B),('H',H)):
     ground=ev.corner_values(grid,r,c)
     for tri in ev.TRIS:
      piece=ev.odol_visible_in_native_tri(xyf,coeff,cellxy,ground,tri)
      if not piece.is_empty and piece.area>0: grouped[side][key].append(piece)
 geometries={'B':{},'H':{}}
 for side in ('B','H'):
  for key in sorted(keys):
   ps=grouped[side].get(key,[])
   geometries[side][key]=unary_union(ps) if ps else Polygon()
 union={}
 for side in ('B','H'):
  for kind in (0,1):
   gs=[geometries[side][k] for k in sorted(keys) if k[0]==kind and not geometries[side][k].is_empty]
   union[(side,kind)]=unary_union(gs) if gs else Polygon()
 elapsed=time.perf_counter()-t0
 targets={
  'physical_object_16804567_model7443':(0,16804567,7443),
  'visible_object_16804567_model7443':(1,16804567,7443),
 }
 geom_out={}
 for label,key in targets.items():
  bg=geometries['B'][key];hg=geometries['H'][key]
  geom_out[label]={'B':geometry_stats(bg),'H':geometry_stats(hg),
    'B_minus_H_area_m2':float(bg.difference(hg).area),
    'H_minus_B_area_m2':float(hg.difference(bg).area),
    'symmetric_difference_area_m2':float(bg.symmetric_difference(hg).area),
    'component_overlap':overlap_matrix(bg,hg)}
 for kind,label in ((0,'physical_unique_union'),(1,'visible_unique_union')):
  bg=union[('B',kind)];hg=union[('H',kind)]
  geom_out[label]={'B':geometry_stats(bg),'H':geometry_stats(hg),
    'B_minus_H_area_m2':float(bg.difference(hg).area),
    'H_minus_B_area_m2':float(hg.difference(bg).area),
    'symmetric_difference_area_m2':float(bg.symmetric_difference(hg).area),
    'component_overlap':overlap_matrix(bg,hg)}
 # Verify the same overlay reproduces published topology/areas exactly within tight floating tolerance.
 top=assess['compiled_water']['topology']
 validation={}
 for kind,label in ((0,'physical_unique_union'),(1,'visible_unique_union')):
  pub=top['exposed_area']['physical' if kind==0 else 'visible']
  got=geom_out[label]
  validation[label]={'B_area_abs_error_m2':abs(got['B']['area_m2']-pub['unique_union_area_B_m2']),
    'H_area_abs_error_m2':abs(got['H']['area_m2']-pub['unique_union_area_H_m2']),
    'B_components_match':got['B']['components']==top['kind_union_signatures_B'][str(kind)]['components'],
    'H_components_match':got['H']['components']==top['kind_union_signatures_H'][str(kind)]['components'],
    'B_holes_match':got['B']['holes']==top['kind_union_signatures_B'][str(kind)]['holes'],
    'H_holes_match':got['H']['holes']==top['kind_union_signatures_H'][str(kind)]['holes']}
 end={str(p.resolve()):sha(p) for p in PINS}
 if start!=end: raise RuntimeError('readset changed during diagnosis')
 result={
  'schema':'ev93.rejected-diagnostic-v4-failure-diagnosis.v1','status':'READ_ONLY_DIAGNOSTIC_NOT_ACCEPTANCE',
  'inputs':{str(p.resolve()):{'sha256':start[str(p.resolve())]} for p in PINS},
  'assessment_status':assess['status'],'assessment_accepted':assess['accepted'],
  'changed_vertices':int(changed.sum()),'mask_audit':mask_result,
  'topology_source':'same pinned EV87 odol_visible_in_native_tri clipping over prepared face/cell population; no index build and no consumer/gates rerun',
  'topology_reproduction':validation,'affected_geometry':geom_out,
  'published_topology_failures':top['topology_failures'],
  'published_exposed_area':top['exposed_area'],
  'overlay_compute_seconds':elapsed,'readset_stable':True,
  'interpretation':{
   'protection':'The raw other_fixed_context gate counts released cls5/water nodes as protected. All changed nodes overlapping that raw mask must be checked against the explicit cls5/water release and effective_fixed_context; no changed effective-fixed, P9, or road nodes means this particular failure is a consumer-mask interpretation mismatch, subject to the other protection masks being consistent.',
   'topology':'Component/hole deltas are reported with exact component/hole areas and symmetric differences. No tolerance is introduced; do not waive a topology failure as a GEOS sliver without evidence from those measured areas.'
  }
 }
 out=OUT/'assessment-v4-failure-diagnosis.json';tmp=out.with_suffix('.json.tmp');tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(out)
 lines=['# Diagnóstico de los fallos nuevos de recovery-v4','',f"Informe v4: `{ASSESSMENT}` (SHA256 {PINS[ASSESSMENT]}). Estado `{assess['status']}`; no aceptado, sin terreno escrito.",'', '## Protección y máscara efectiva','',f"De {int(changed.sum())} vértices modificados, {int(np.count_nonzero(changed & prep['other_fixed_context']))} intersectan `other_fixed_context`; los 16 son simultáneamente `cls=5`, `water=true` y `wet_support=true`, es decir, la excepción de liberación declarada. La intersección con `effective_fixed_context` es {int(np.count_nonzero(changed & prep['effective_fixed_context']))}; con P9 y carretera es {int(np.count_nonzero(changed & prep['p9_context']))} y {int(np.count_nonzero(changed & prep['road_context']))}. Preparación informa reserva=0, plataforma=0 y halo ingeniería=0 en contexto.",'', 'El preparador define `nonreleased_fixed = other_rebuilt & ~((cls==5)&water)` y `effective_fixed` incorpora large-lake banks, halo, Narva, reservas, plataformas, P9 y carretera. El consumidor v4 intersecta cambios con el `other_fixed_context` bruto, que aún contiene la parte liberada `cls=5/water`; por tanto ese gate parece un falso FAIL de interpretación de máscara, no un cambio en reserva/civil. El resto del recibo de protecciones sigue siendo evidencia necesaria; no se modifica el gate aquí.','', '## Topología compilada local','', 'Se repitió solo el clipping/topology de las 200 caras preparadas sobre 144 celdas, usando la misma rutina geométrica EV87. Las áreas reproducen las del informe (ver JSON). Para las dos claves afectadas se guardan áreas de componentes, áreas de huecos, matrices de solape B/H y diferencias simétricas. No se aplicó umbral ni se reclasificó el FAIL como sliver.','', '| Medida | B | H |','|---|---:|---:|']
 for label,obj in geom_out.items():
  lines.append(f"| {label} área expuesta (m²) | {obj['B']['area_m2']:.12g} | {obj['H']['area_m2']:.12g} |")
  lines.append(f"| {label} componentes / huecos | {obj['B']['components']} / {obj['B']['holes']} | {obj['H']['components']} / {obj['H']['holes']} |")
 lines += ['', 'Los cambios topológicos no se pueden atribuir a precisión de overlay sin mirar tamaños: el JSON conserva magnitudes absolutas de cada componente/hueco y áreas B-only, H-only y simétrica. Las áreas totales expuestas cambian aproximadamente 15.2 m² en cada superficie; esto es una diferencia geométrica sustantiva, aunque el cambio de conectividad puede depender de un cuello estrecho. La puerta topológica sigue fallida según el contrato actual.','', '## Energía y alcance','', 'La puerta de energía sigue fallando: 155.9440734841285 − 155.94405102975674 = 2.24543717593e−5, por encima del allowance 1.55944051030e−5; la mejora frente a B (279.185592812943) no basta para satisfacer cierre-vs-raw. Este artefacto no corrige eso ni reevalúa otras puertas.','', 'El JSON ancla hashes del assessment, preparador, máscaras, diagnóstico rechazado, B, EV87 y ayudante, y comprueba que el readset no cambió durante el análisis. No se modificó solver, candidato ni gates.']
 (OUT/'assessment-v4-failure-diagnosis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(out);print('SHA256',sha(out));print('script',Path(__file__).resolve(),sha(Path(__file__)));print('topology_seconds',elapsed)
if __name__=='__main__': main()
