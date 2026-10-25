from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
import numpy as np

Q=Path(r'E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010')
OUT=Q/'ev91-descent'
BPATH=Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')
PRE=Q/'next-method-preflight/preflight.json'
PREP=OUT/'prepared.json'
REPORT=Q/'next-method-consumer/runs/attempt-02/ev90-review.json'
EV88=Q/'review-independent/verify_ev88q.py'
EV87=Path(r'E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py')
SOURCES={
 'B':(BPATH,'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'),
 'preflight':(PRE,'8c8ec80cbb7029f510c832adf90a8871e385fbd8ec52ee5043d5ea24e1099d63'),
 'EV90_preflight_script':(Q/'next-method-preflight/ev90_preflight.py','5892e917335ca2d8caa427f04f48ba8acbd8e16a5e1b400be596d5dd636afb7f'),
 'EV91_plan':(OUT/'plan.md','28db80ef21dcd8df59927556830e8cc663c6db7195819ab65e2ff1bccc127586'),
 'EV91_author_source':(OUT/'author_ev91.py','be0c7c72463d5b41544837aa232f678147e21e735e41b8bee1bc5c9639a7ff89'),
 'EV91_prepared':(PREP,'e172719641897ce41a92e7574aab7850d0a6c8298648f26ed2e2fc547d236c4f'),
 'EV90_report':(REPORT,'52c1ac1bb76658529899309af7b7fae1160469f8c940f079fff99753f9259c5a'),
 'EV90_consumer':(Q/'next-method-consumer/verify_ev90.py','ef4056bf186255389a899c193e92bfcB062664d317672bdee634656d89ad0b46'.lower()),
 'EV88_helper':(EV88,'82a988790e6bdfc0289bcb7c32cb0afd1210e07b264d92731aba266bc5980f78'),
 'EV87_helper':(EV87,'964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27'),
 'shape_contract':(Q/'next-method-consumer/shape_contract.py','8cd9d0fbea03c05e5ae53a31676d79ec2364be83c055213446f6c8599245d533'),
}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()

def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None:raise RuntimeError(f'cannot import {path}')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

for name,(path,want) in SOURCES.items():
 got=sha(path)
 if got.lower()!=want.lower():raise AssertionError(f'{name} pin mismatch {got} != {want}')
pre=json.loads(PRE.read_text(encoding='utf-8'))
prep=json.loads(PREP.read_text(encoding='utf-8'))
report=json.loads(REPORT.read_text(encoding='utf-8'))
assert pre['status']=='PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW'
assert prep['status']=='PREPARED_NO_SOLVE' and prep['baseline_feasible'] is True
assert report['status']=='FAIL_EV90_OFFLINE_CONSUMER'
assert report['information']['mutable_vertices']==85

ev88=load_module('ev88_collar_guard',EV88);ev87=load_module('ev87_collar_guard',EV87)
variables=[tuple(map(int,x)) for x in prep['variables_rc']]
varset=set(variables)
expected=[tuple(map(int,x)) for x in pre['domain_and_bound_analysis']['eligible_after_face_freeze_nodes']]
assert variables==expected and len(variables)==85
records=ev88.stencil_records(variables=variables)
assert len(records)==350
assert [x['key'] for x in records]==prep['stencils']
collar_records=[x for x in records if x['collar']]
stencil_guard=set().union(*(set(x['nodes']) & varset for x in collar_records)) if collar_records else set()

# Rebuild the exact WINDOW/CORE masks used by the EV90 consumer.
r0,r1,c0,c1=tuple(ev88.WINDOW);cr0,cr1,cc0,cc1=tuple(ev88.CORE)
collar={(r,c) for r in range(r0,r1) for c in range(c0,c1)
        if r<r0+2 or r>=r1-2 or c<c0+2 or c>=c1-2}
collar_mask=np.zeros((r1-r0,c1-c0),dtype=bool)
for r,c in collar:collar_mask[r-r0,c-c0]=True

# The four nodes are the union of the two triangles whose normal angle the
# EV90 consumer measures. A hinge enters the existing collar population if
# any of these four nodes is in the two-node collar (edge_vertex_slices).
hinge_nodes={'diag':[],'vertical':[],'horizontal':[]}
edge_touch_counts={'diag':0,'vertical':0,'horizontal':0}
edge_touch_hinges={'diag':[],'vertical':[],'horizontal':[]}
for r in range(r0,r1-1):
 for c in range(c0,c1-1):
  ns=((r,c),(r,c+1),(r+1,c),(r+1,c+1))
  edge=(ns[0],ns[3])
  if any(q in collar for q in ns):hinge_nodes['diag'].append(ns)
  if any(q in collar for q in edge):
   edge_touch_counts['diag']+=1;edge_touch_hinges['diag'].append(ns)
for r in range(r0,r1-1):
 for c in range(c0,c1-2):
  ns=((r,c),(r,c+1),(r+1,c+1),(r+1,c+2))
  edge=(ns[1],ns[2])
  if any(q in collar for q in ns):hinge_nodes['vertical'].append(ns)
  if any(q in collar for q in edge):
   edge_touch_counts['vertical']+=1;edge_touch_hinges['vertical'].append(ns)
for r in range(r0,r1-2):
 for c in range(c0,c1-1):
  ns=((r,c),(r+1,c),(r+1,c+1),(r+2,c+1))
  edge=(ns[1],ns[2])
  if any(q in collar for q in ns):hinge_nodes['horizontal'].append(ns)
  if any(q in collar for q in edge):
   edge_touch_counts['horizontal']+=1;edge_touch_hinges['horizontal'].append(ns)

expected_counts={k:int(report['information']['collar_hinges'][k]['count']) for k in hinge_nodes}
actual_counts={k:len(v) for k,v in hinge_nodes.items()}
assert actual_counts==expected_counts=={'diag':112,'vertical':108,'horizontal':108},(actual_counts,expected_counts)
# Cross-check population masks against the independent EV87 helper, for every
# measured hinge, not merely each reported maximum.
angle_counts={};mask_counts={}
for kind,angles in dict(ev87.edge_angles(np.asarray(np.load(BPATH,allow_pickle=False)['heights'][r0:r1,c0:c1],dtype=np.float32))).items():
 mask=ev87.incident_any(collar_mask,kind)
 angle_counts[kind]=int(np.count_nonzero(mask));mask_counts[kind]=list(mask.shape)
assert angle_counts==actual_counts,(angle_counts,actual_counts)
hinge_guard={q for groups in hinge_nodes.values() for ns in groups for q in ns if q in varset}
edge_touch_guard={q for groups in edge_touch_hinges.values() for ns in groups for q in ns if q in varset}
# The consumer population intentionally tests any 4-node hinge incidence;
# report actual shared-edge-only count to expose the broader footprint.
all_guard=stencil_guard|hinge_guard
remaining=varset-all_guard
assert all_guard.isdisjoint(remaining) and all_guard|remaining==varset
assert stencil_guard==hinge_guard
assert edge_touch_guard<=stencil_guard

# Verify the structural guard with a diagnostic perturbation outside the guard.
# This is an algebraic fixture, not a candidate or an in-bounds terrain.
with np.load(BPATH,allow_pickle=False) as z:b=z['heights'].copy()
test=b.copy()
for r,c in sorted(remaining):test[r,c]=np.float32(float(test[r,c])+0.03125)
energy_b=ev88.stencil_energy(b,collar_records)[0]
energy_t=ev88.stencil_energy(test,collar_records)[0]
angle_arrays_b=dict(ev87.edge_angles(np.asarray(b[r0:r1,c0:c1],dtype=np.float64)))
angle_arrays_t=dict(ev87.edge_angles(np.asarray(test[r0:r1,c0:c1],dtype=np.float64)))
angle_equal={}
for kind in hinge_nodes:
 mask=ev87.incident_any(collar_mask,kind)
 angle_equal[kind]=bool(np.array_equal(angle_arrays_b[kind][mask],angle_arrays_t[kind][mask]))
assert energy_b==energy_t and all(angle_equal.values()),(energy_b,energy_t,angle_equal)

# Re-anchor the prepared float32-inward bounds to the independent EV90 preflight.
bounds={tuple(map(int,node)):tuple(map(float,iv)) for node,iv in zip(prep['variables_rc'],prep['bounds_float32_inward'])}
pre_bounds={tuple(map(int,x['node_rc'])):tuple(map(float,x['interval_float32_inward_m']))
            for x in pre['domain_and_bound_analysis']['final_float32_intervals_for_eligible_nodes']}
assert bounds==pre_bounds and len(bounds)==85
B={node:float(b[node]) for node in set(variables)|{(int(ev88.ROW),int(ev88.COL))}}
def interval(node):
 if node not in varset:return (B.get(node,float(b[node])),B.get(node,float(b[node])))
 if node in all_guard:return (B[node],B[node])
 return bounds[node]
focus=(int(ev88.ROW),int(ev88.COL))
focus_free=focus in remaining
focus_interval=interval(focus)
cardinal={'east_west':((focus[0],focus[1]-1),(focus[0],focus[1]+1)),
          'north_south':((focus[0]-1,focus[1]),(focus[0]+1,focus[1]))}
axis={};limits=[]
for name,nodes in cardinal.items():
 prom=float(b[focus])-max(float(b[nodes[0]]),float(b[nodes[1]]))
 target=max(float(b[nodes[0]]),float(b[nodes[1]]))+0.75*prom
 nints=[interval(n) for n in nodes]
 axis[name]={'neighbors_rc':[list(n) for n in nodes],
             'B_neighbor_heights_m':[float(b[n]) for n in nodes],
             'neighbor_intervals_after_guard_m':[list(x) for x in nints],
             'B_prominence_m':prom,'max_focus_height_for_25pct_m':target,
             'box_feasible':bool(prom>0 and focus_interval[0]<=target)}
 limits.append(target)
# EV91 prepared descent witness for the focus. Keeping every other node at B
# and moving only the focus preserves all rows where focus is a witness; its
# own row remains feasible exactly when Hfocus >= H_witness.
witness_rows=[x for x in prep['witnesses'] if tuple(x['center'])==focus]
assert len(witness_rows)==1
witness=tuple(map(int,witness_rows[0]['witness']))
# Independently verify EV91's deterministic lowest-(height,row,col) witness.
neighbors8=[(focus[0]+dr,focus[1]+dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc]
expected_witness=min(neighbors8,key=lambda node:(float(b[node]),node[0],node[1]))
assert witness==expected_witness,(witness,expected_witness)
witness_h=float(b[witness]);
required_lower=max(focus_interval[0],witness_h)
target_upper=min(focus_interval[1],*limits)
raw_goal=target_upper
f32_goal=float(np.float32(raw_goal))
if f32_goal>raw_goal:f32_goal=float(np.nextafter(np.float32(f32_goal),np.float32(-np.inf)))
focus_only_feasible=(focus_free and required_lower<=f32_goal<=focus_interval[1]
                     and f32_goal>=witness_h and all(x['box_feasible'] for x in axis.values()))
# Construct a one-node scalar witness at float32; all remaining nodes stay at B.
test_h=b.copy();test_h[focus]=np.float32(f32_goal)
base_bounds_pass=all(lo<=B[node]<=hi for node,(lo,hi) in bounds.items())
witness_rows_pass=all(float(test_h[tuple(x['center'])])>=float(test_h[tuple(x['witness'])])
                        for x in prep['witnesses'] if x['linear_row'] is not None)
assert base_bounds_pass and focus_interval[0]<=float(test_h[focus])<=focus_interval[1]
assert witness_rows_pass, 'focus-only scalar witness violates an EV91 descent row'
shape_mod=load_module('ev90_shape_for_ev91_preflight',Q/'next-method-consumer/shape_contract.py')
shape_witness=shape_mod.evaluate_shape(np.asarray(b,dtype=np.float32),np.asarray(test_h,dtype=np.float32),ev88.WINDOW,focus)
focus_angle_b=ev88.local_mesh_angles(np.asarray(b,dtype=np.float64),center=focus,radius=2)['max_incident_hinge_deg']
focus_angle_test=ev88.local_mesh_angles(np.asarray(test_h,dtype=np.float64),center=focus,radius=2)['max_incident_hinge_deg']
focus_angle_delta=focus_angle_b-focus_angle_test
result={
 'status':'PASS_PREFLIGHT_GUARD_AND_FOCUS_BOX_WITNESS' if focus_only_feasible else 'INFEASIBLE_OR_INCONCLUSIVE',
 'scope':'Read-only EV91 descent preflight. No author, optimizer, solver, candidate, package, or engine run.',
 'source_hashes':{name:{'path':str(path),'sha256':sha(path)} for name,(path,_want) in SOURCES.items()},
 'geometry':{'window_vertices':[r0,r1,c0,c1],'core_vertices':[cr0,cr1,cc0,cc1],
             'collar_definition':'WINDOW minus CORE; two-node ring; exact EV90 consumer population'},
 'population':{'domain_variables':len(variables),'stencils_total':len(records),
               'collar_stencils':len(collar_records),'collar_hinges_by_kind':actual_counts,
               'collar_angle_masks_crosschecked_against_EV87':angle_counts},
 'guard':{'stencil_guard_count':len(stencil_guard),'hinge_guard_count':len(hinge_guard),
          'overlap_count':len(stencil_guard&hinge_guard),'union_count':len(all_guard),
          'remaining_free_count':len(remaining),'guard_rc':sorted(map(list,all_guard)),
          'remaining_rc':sorted(map(list,remaining)),
          'remaining_bounds_rc':[min(r for r,c in remaining),max(r for r,c in remaining),
                                 min(c for r,c in remaining),max(c for r,c in remaining)] if remaining else None,
          'actual_shared_edge_collar_touch_counts':edge_touch_counts,
          'edge_endpoint_touch_dependency_guard_count':len(edge_touch_guard),
          'consumer_mask_extra_dependency_guard_count':len(hinge_guard-edge_touch_guard),
          'all_edge_touch_dependencies_already_in_stencil_guard':edge_touch_guard<=stencil_guard,
          'conservatism_note':'The guard follows the existing EV90 gate mask: a hinge is measured if any of its four triangle vertices is in collar, then all four vertices are frozen if mutable. This can exceed literal shared-edge endpoint contact, but preserves every measured normal, not only the maximum.'},
 'core9_utility':{'definition':'9x9 centered on (840,370): rows 836..844 and cols 366..374 inclusive',
                  'variable_count':sum(836<=r<=844 and 366<=c<=374 for r,c in varset),
                  'guard_count':sum(836<=r<=844 and 366<=c<=374 for r,c in all_guard),
                  'remaining_free_count':sum(836<=r<=844 and 366<=c<=374 for r,c in remaining),
                  'remaining_free_rc':sorted([list(x) for x in remaining if 836<=x[0]<=844 and 366<=x[1]<=374])},
 'structural_invariance_fixture':{'kind':'diagnostic perturbation of every remaining variable by +0.03125m, no bounds/product claim',
                                 'collar_energy_B':energy_b,'collar_energy_test':energy_t,
                                 'energy_bitwise_equal':energy_b==energy_t,
                                 'collar_hinge_arrays_bitwise_equal_by_kind':angle_equal,
                                 'all_measured_hinges_included':sum(actual_counts.values())},
 'focus_feasibility':{'focus_rc':list(focus),'focus_free_after_guard':focus_free,
                      'B_height_m':float(b[focus]),'float32_inward_interval_after_guard_m':list(focus_interval),
                      'axes':axis,'focus_descent_witness_rc':list(witness),
                      'focus_descent_witness_B_m':witness_h,
                      'required_lower_from_focus_bound_and_witness_m':required_lower,
                      'common_upper_for_both_25pct_targets_m':target_upper,
                      'focus_only_float32_witness_m':f32_goal,
                      'focus_only_box_witness_feasible':focus_only_feasible,
                      'all_EV91_linear_descent_witness_rows_pass':witness_rows_pass,
                      'baseline_variables_within_float32_bounds':base_bounds_pass,
                      'focus_only_shape_contract_gates':shape_witness['gates'],
                      'focus_incident_max_hinge_deg_B':focus_angle_b,
                      'focus_incident_max_hinge_deg_focus_only':focus_angle_test,
                      'focus_hinge_reduction_deg_focus_only':focus_angle_delta,
                      'focus_hinge_reduction_2deg_gate_focus_only':focus_angle_delta>=2.0,
                      'interpretation':'With every other vertex at B and only focus changed to this float32 value, the two cardinal prominences meet the 25% target and the existing selected descent witness remains satisfied. This is a local box/testigo witness. The focus angle is measured only with the EV90 radius-2 metric; this is not the full EV91 optimization or full consumer evaluation.'},
 'limitations':['No SLSQP/BVLS/LP was called; no terrain or candidate was written.',
                'The focus-only scalar witness checks all EV91 linear descent rows, all WINDOW shape predicates, and the radius-2 focus hinge gate; it does not solve the EV91 energy objective or evaluate global sectors, p99, corridor, or compiled representation as a candidate.',
                'The guard proves unchanged values only for the fixed EV90 collar stencil and hinge populations; it does not guarantee all other EV90 gates.',
                'The scalar witness reports local focus-angle and WINDOW shape predicates, but does not evaluate global sectors, p99, corridor, or compiled representation as a candidate.',
                'Existing gate population is preserved in full (350 stencils and all 328 collar hinges); no post-hoc population shrink.']}
result['script_sha256']=sha(Path(__file__))
(OUT/'collar-guard-preflight.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
md=f'''# EV91 preflight: guard del collar

**{result['status']}**. Auditoría estática solamente: no se modificaron EV90, EV91 author, alturas, candidato ni geometría.

- Reconstrucción anclada a B `{SOURCES['B'][1]}`, preflight EV90 y lista exacta de 85 variables. La lista EV91 coincide con `eligible_after_face_freeze_nodes`; las 85 cotas float32 interiores coinciden nodo a nodo con el preflight EV90.
- El guard congela `{len(all_guard)}/85` variables: `{len(stencil_guard)}` participan en alguna de las `{len(collar_records)}` stencils de collar y `{len(hinge_guard)}` en las bisagras medidas; ambos conjuntos coinciden. Quedan `{len(remaining)}` variables libres, todas dentro del núcleo9 centrado (filas836–844, columnas368–374): `{sum(836<=r<=844 and 366<=c<=374 for r,c in remaining)}/{sum(836<=r<=844 and 366<=c<=374 for r,c in varset)}` elegibles.
- Se conservó la población completa: `{len(records)}` stencils y collar de `{actual_counts}` bisagras; los conteos concuerdan con el reporte EV90 y la máscara `incident_any` del helper EV87. Una perturbación sintética de todos los grados libres deja idénticos la energía de stencils y todos los ángulos collar, componente por componente; esto verifica la suficiencia estructural del guard.
- Foco `{focus}`: libre `{focus_free}`, B `{float(b[focus]):.9f} m`, intervalo tras guard `{focus_interval}`. El testigo EV91 es `{witness}` a `{witness_h:.9f} m`. Con los demás nodos en B hay testigo float32 `{f32_goal:.9f} m` que cumple los objetivos cardinales de reducción ≥25% en ambos ejes y mantiene la desigualdad foco≥testigo. Resultado: **{focus_only_feasible}** para esta prueba de caja local, sin solver.

## Conservadurismo y alcance

El guard replica la población efectiva EV90: `incident_any` incluye una bisagra si cualquiera de los cuatro vértices de sus dos triángulos toca el collar, y se congelan las variables entre esos cuatro nodos. La intersección por extremos del edge compartido sería menor (112/84/84 hinges diag/vertical/horizontal; 24 dependencias mutables), pero las 19 dependencias adicionales ya pertenecen al guard de stencils. Por eso la unión final sigue siendo 43; la definición amplia de normales no reduce más el núcleo que la energía de collar ya exige. Se compararon las 328 normales de collar, no solo sus máximos.

Para una prueba local, se deja todo en B salvo el foco en `{f32_goal:.9f} m`. Ese testigo satisface todas las filas de descenso EV91 (incluido el testigo del foco), las cinco puertas del shape contract sobre WINDOW y reduce la bisagra incidente máxima `{focus_angle_delta:.6f}°` (puerta 2°: `{focus_angle_delta>=2.0}`). Es evidencia de que la libertad central existe y de que el objetivo del foco no queda bloqueado por cotas/testigos; no es solución del objetivo energético EV91 ni chequeo completo de sectores, p99 o cobertura.

El detalle reproducible está en `collar-guard-preflight.json`; script `collar_guard_preflight.py`.
'''
(OUT/'collar-guard-preflight.md').write_text(md,encoding='utf-8')
print(result['status'])
print(json.dumps({'variables':len(variables),'stencils':len(records),'collar_stencils':len(collar_records),'collar_hinges':actual_counts,'guard':len(all_guard),'remaining':len(remaining),'core9_free':result['core9_utility']['remaining_free_count'],'focus_free':focus_free,'focus_witness':f32_goal,'focus_box_feasible':focus_only_feasible,'witness_rows_pass':witness_rows_pass,'shape_gates':shape_witness['gates'],'focus_hinge_delta_deg':focus_angle_delta,'focus_hinge_2deg':focus_angle_delta>=2.0,'angle_population':angle_counts},separators=(',',':')))






