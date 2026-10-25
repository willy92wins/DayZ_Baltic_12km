from pathlib import Path
import json,csv,numpy as np
from scipy.ndimage import distance_transform_edt,median_filter
O=Path(r'E:/DayZ-Baltic-Build/v30-bank-relief-review-20261010/luna-geometry');R=Path(r'E:/DayZ-Baltic-Build');C=R/'v30-remaining-exact-dry-support-20261009/candidate'
a=json.loads((O/'non4of4-fold-classification.json').read_text());records=a['records'];T=dict(np.load(C/'terrain.npz'));h=T['heights'].astype(float);cls=T['cls'];co=np.load(R/'v30-remaining-exact-dry-support-20261009/constraints.npz');support=co['water_support'].astype(bool);fixed=co['fixed'].astype(bool);flow=np.isin(cls,[3,5,6]);base=(distance_transform_edt(~flow,sampling=6)<=96)&(cls==0)&~support&~T['water']&~T['beach']&~T['reserve']&~T['platform'];med=median_filter(h,size=5,mode='nearest')
# Vertex-level grouping prevents an edge threshold from masquerading as a broad turning shoreline.
per_vertex={}
for q in records:
 if q['face_state']!='wet-dry':continue
 for r,c in q['vertices_rc']:
  if base[r,c] and not fixed[r,c]:
   per_vertex.setdefault((r,c),[]).append(q)
cands=[]
for (r,c),qs in per_vertex.items():
 prom=float(h[r,c]-med[r,c]);components=sorted(set(int(q['flow_component']) for q in qs))
 if len(qs)<2 or prom<.65 or len(components)!=1:continue
 x,z=c*6,12282-r*6
 if min(x,12282-x,z,12282-z)<96:continue
 cands.append((prom,len(qs),x,z,components[0],r,c,qs))
cands.sort(key=lambda q:(q[0],q[1]),reverse=True)
selected=[]
for q in cands:
 if all(q[4]!=s[4] and np.hypot(q[2]-s[2],q[3]-s[3])>=300 for s in selected):selected.append(q)
 if len(selected)==3:break
assert len(selected)==3
focus=[]
for rank,(prom,n,x,z,comp,r,c,qs) in enumerate(selected,1):
 assert base[r,c] and not support[r,c] and not fixed[r,c] and cls[r,c]==0
 incident=[]
 for q in qs:
  incident.append({'hinge':q['kind'],'row':q['row'],'col':q['col'],'dihedral_deg':q['angle_deg'],'face_state':q['face_state'],'wet_face_flags':q['face_wet'],'four_vertices_rc':q['vertices_rc'],'wet_support_vertices':q['wet_support_vertices'],'engineering_vertex_hits':q['hard_engineering_vertices']})
 neighbors=[]
 for rr in range(max(0,r-2),min(h.shape[0],r+3)):
  for cc in range(max(0,c-2),min(h.shape[1],c+3)):
   neighbors.append(float(h[rr,cc]))
 focus.append({'rank':rank,'x_m':x,'z_m':z,'height_m':float(h[r,c]),'height_minus_5x5_median_m':prom,'incident_wet_dry_high_hinges':n,'flow_component_8conn':comp,'flow_class_codes':'6' if np.any(cls[max(0,r-3):r+4,max(0,c-3):c+4]==6) else ','.join(map(str,sorted(set(int(cls[rr,cc]) for rr,cc in incident if False)))),'target_flags':{'cls':int(cls[r,c]),'within_96m_of_cls_3_5_6':True,'actual_wet_support':bool(support[r,c]),'EV71_fixed':bool(fixed[r,c]),'water':bool(T['water'][r,c]),'beach':bool(T['beach'][r,c]),'reserve':bool(T['reserve'][r,c]),'platform':bool(T['platform'][r,c])},'five_by_five_height_m':np.round(h[r-2:r+3,c-2:c+3],3).tolist(),'hinges':incident,'held_support_corner_count_per_hinge':[q['wet_support_vertices'] for q in qs]})
summary={'selection':'three spatially separated vertices with at least two >30° actual wet/dry hinges converging on the same eligible, nonsupport dry vertex; positive prominence >=0.65m over a 5x5 median; distinct 8-connected class 3/5/6 component labels; >=96m from raster edge; no reserve/platform/water/beach and not EV71 fixed. This is a diagnostic anchor selection, not acceptance or solver result.','focuses':focus,'limitations':['Component labels are 8-connected geographic buckets on combined cls 3/5/6, not named rivers and not proof of hydrological connectivity.','A wet/dry face XOR is a geometric shoreline discriminator under P/F source semantics; it is not proof of rendered LOD or appearance.','The target point is editable under current EV71 fixed mask; changing it alone is not proven to improve aesthetics or meet a slope gate. The wet support corner set is preserved only if no support vertex is changed.','Prominence is a local numeric screening metric; no visual pyramid recognition was performed.']}
(O/'focus-anchors.json').write_text(json.dumps(summary,indent=2)+'\n')
with (O/'focus-anchors.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['rank','x_m','z_m','height_m','height_minus_5x5_median_m','flow_component_8conn','incident_wet_dry_high_hinges','hinges']);w.writeheader()
 for q in focus:w.writerow({k:json.dumps(q[k],ensure_ascii=False) if isinstance(q[k],(list,dict)) else q[k] for k in w.fieldnames})
# Compact memo report for the requested subset.
s=json.loads((O/'non4of4-fold-classification.json').read_text())['summary']
lines=['# Bisagras >30° que tocan banco seco: revisión de las 4.768 no 4/4 secas','',f"Fuente: EV71 `terrain.npz` SHA-256 `{s['source']['terrain_sha256']}`; `plane.npy` `{s['source']['plane_sha256']}`; `visible-field.npy` `{s['source']['visible_field_sha256']}`; constraints `{s['source']['constraints_sha256']}`. Recalculé P/F por cara con el contrato de EV71 y exigí igualdad exacta con `constraints.npz:water_support`.",'', '## Qué significan las 4.768', '', 'El selector es el censo previo: bisagras nativas >30° con ≥1 de sus cuatro vértices en la banda de terreno seco elegible de 96 m y excluyendo las que tienen 4/4 vértices elegibles secos. No es un censo de agua profunda ni de todas las orillas.', '', '| Estado de las dos caras que comparten la bisagra | Bisagras | Interpretación |','|---|---:|---|']
for state,labeltxt in [('wet-dry','borde geométrico mojado-seco real según P/F'),('dry-dry','ambas caras secas; soporte de vértices viene de otras caras incidentes'),('wet-wet','dos caras mojadas (ninguna en este subconjunto)')]:lines.append(f"| {labeltxt} | {s['face_states'].get(state,0):,} | {'orilla en esta bisagra' if state=='wet-dry' else ('no confundir soporte de vértices con transición de orilla aquí' if state=='dry-dry' else 'sin evidencia de caras profundas dentro del subconjunto')} |")
lines += ['',f"De las 3.317 bisagras `wet-dry`, las caras mojadadas marcan 9.951 incidencias de vértice como soporte; 6.634 incidencias son vértices `cls=0` secos pero bloqueados por ese soporte. En las 1.451 `dry-dry`, hay 3.874 incidencias de vértices secos con soporte: dado que las dos caras de la bisagra están secas, el soporte proviene de otras caras P/F que comparten esos vértices. Es conteo de incidencias, no de vértices únicos.",'', 'Las clases agrupadas son componentes raster 8-conexos combinando `cls ∈ {3,5,6}`; sirven para agrupar por sector, no son nombres de ríos ni una conectividad hidrológica demostrada. Los mayores grupos son:', '', '| Componente espacial | Bisagras | wet-dry | dry-dry | Caja X/Z (m) | Códigos |','|---:|---:|---:|---:|---|---|']
for q in s['by_flow_component'][:12]:lines.append(f"| {q['component']} | {q['hinges']:,} | {q['wet_dry']:,} | {q['dry_dry']:,} | {q['bbox'][0]:.0f},{q['bbox'][1]:.0f}–{q['bbox'][2]:.0f},{q['bbox'][3]:.0f} | {q['component_class_codes']} |")
lines += ['', '## Tres focos de relieve local', '', 'Se agruparon las bisagras por vértice seco elegible y se eligieron puntos donde convergen al menos dos bisagras >30° de transición mojado-seco. El punto objetivo es un vértice `cls=0` seco, no parte del soporte P/F y no bloqueado por EV71; los demás vértices de esas caras incluyen 3 puntos de soporte y deben quedar intactos para conservar el contorno P/F. Esto discrimina un nudo local de cambio de pendiente de una larga faceta inclinada, aunque no demuestra que el render lo perciba como una pirámide.', '', '| Foco (X,Z) m | Componente | h local | h−mediana 5×5 | Diedros convergentes | Condición del vértice objetivo |','|---|---:|---:|---:|---|---|']
for q in focus:
    hs=', '.join('{} {:.1f}°'.format(v['hinge'],v['dihedral_deg']) for v in q['hinges'])
    lines.append(f"| ({q['x_m']:.0f}, {q['z_m']:.0f}) | {q['flow_component_8conn']} | {q['height_m']:.3f} m | +{q['height_minus_5x5_median_m']:.3f} m | {hs} | cls0, no soporte, no fixed, sin reserve/platform/water/beach |")
lines += ['', 'Una intervención futura acotada sería ajustar únicamente el vértice seco objetivo y su vecindad elegible dentro del mismo sector, dejando inmóviles todos los vértices del soporte P/F, reservas, plataformas y carretera. Este diagnóstico no calcula ni valida tal ajuste; el hecho de que cada objetivo esté editable no prueba que una modificación de un solo vértice suavice el terraplén sin efectos laterales.', '', '## Reproducibilidad y límites', '', 'El cálculo usa `classify_non4of4_folds.py`, que reproduce 4.768 y los estados de las dos caras con la topología de triángulos de `audit_native_surface.py`. `select_bank_focuses.py` agrupa por vértice y genera los tres anclajes. `non4of4-folds.csv` y `non4of4-fold-classification.json` contienen los registros completos. No se modificó terreno, P/F, constraints ni DayZ.', '', 'Las 1.451 bisagras `dry-dry` son soporte seco geométricamente cercano a agua, no una falsa clasificación de profundas. Para censar bajo agua profunda haría falta otro dominio que incluyera vértices sin banda seca; eso quedó fuera de esta petición. Las cifras no prueban una “pirámide visual” ni la factibilidad del solver.']
(O/'non4of4-review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('wrote',len(focus),'focus anchors; report and csv')
