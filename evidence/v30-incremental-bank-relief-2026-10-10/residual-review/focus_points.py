"""Read-only diagnostic for three vertices read from the EV80->EV82-B cuts."""
from pathlib import Path
import sys, json, hashlib, importlib.util
import numpy as np

B=Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010')
EV79=Path(r'E:/DayZ-Baltic-Build/v30-narva-dry-bank-relief-20261010')
EV80=Path(r'E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010')
SRC=EV79/'candidate/terrain.npz'; REF=EV80/'candidate/terrain.npz'; CAND=B/'candidate/terrain.npz'
EXPECTED='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(CAND)==EXPECTED
assert sha(REF)=='0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
spec=importlib.util.spec_from_file_location('ev82_author',B/'author.py')
author=importlib.util.module_from_spec(spec); spec.loader.exec_module(author)
source,ev80,cand=np.load(SRC),np.load(REF),np.load(CAND)
h79=source['heights'].astype(np.float64); h80=ev80['heights'].astype(np.float64); hB=cand['heights'].astype(np.float64)
con=np.load(EV79/'constraints.npz')
auth=json.loads((B/'authoring.json').read_text(encoding='utf-8'))
decision={(int(v['row']),int(v['col'])):v for v in auth['node_decisions']}
points=[
 {'name':'pico_1140_mas_x6','x_m':1146,'z_m':1002,'profile_context':'a +6m del anchor (1140,1002)'},
 {'name':'escalon_2196_z_menos12','x_m':2196,'z_m':1566,'profile_context':'z -12m del anchor (2196,1578)'},
 {'name':'escalon_2196_z_menos6','x_m':2196,'z_m':1572,'profile_context':'z -6m del anchor (2196,1578)'},
]
def point_geometry(h,r,c):
    patch=np.asarray(h[r-2:r+3,c-2:c+3],dtype=np.float64)
    normals=[]
    for tri in author.TRIANGLES:
        xyz=np.asarray([(dc*6.0,patch[dr+2,dc+2],-dr*6.0) for dr,dc in tri],dtype=np.float64)
        n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0])
        if n[1]<0: n=-n
        normals.append(n)
    slopes={i:float(np.degrees(np.arctan2(np.hypot(normals[i][0],normals[i][2]),abs(normals[i][1])))) for i in author.INCIDENT}
    hinges=[]
    for edge,(ta,tb) in author.HINGES:
        cosine=np.clip(float(np.dot(normals[ta],normals[tb])/(np.linalg.norm(normals[ta])*np.linalg.norm(normals[tb]))),-1.0,1.0)
        hinges.append(float(np.degrees(np.arccos(cosine))))
    return {'six_incident_face_slopes_deg':[slopes[i] for i in author.INCIDENT],
            'twelve_incident_hinge_angles_deg':hinges,
            'faces_over_30':sum(v>30 for v in slopes.values()),
            'hinges_over_30':sum(v>30 for v in hinges),
            'max_face_slope_deg':max(slopes.values()),'max_hinge_angle_deg':max(hinges)}

results=[]
for p in points:
    r=int(round((12282-p['z_m'])/6)); c=int(round(p['x_m']/6)); assert 6*c==p['x_m'] and 12282-6*r==p['z_m']
    in_selector=(r,c) in decision
    flags={k:bool(con[k][r,c]) for k in ('fixed','allowed','wet_support','engineering_halo','narva','other_fixed','bank_domain')}
    for k in ('water','beach','reserve','platform'):
        flags[k]=bool(source[k][r,c])
    flags['class0']=bool(source['cls'][r,c]==0)
    values={'ev79_m':float(h79[r,c]),'ev80_m':float(h80[r,c]),'ev82b_m':float(hB[r,c]),
      'ev80_minus_ev79_m':float(h80[r,c]-h79[r,c]),'ev82b_minus_ev80_m':float(hB[r,c]-h80[r,c]),
      'ev82b_minus_ev79_m':float(hB[r,c]-h79[r,c])}
    rec={**p,'row':r,'col':c,'world_xz_exact':True,'flags':flags,'selector_vertex':in_selector,
      'ev82_author_decision':decision[(r,c)] if in_selector else None,'heights':values,
      'geometry_ev80':point_geometry(h80,r,c),'geometry_ev82b':point_geometry(hB,r,c),
      'measurement':'direct cross-product normals on the six incident native NW-SE triangles and normal-pair angles on the 12 local hinges; no writes'}
    results.append(rec)
report={'status':'THREE_POINT_OFFLINE_DIAGNOSTIC','candidate_sha256':EXPECTED,'ev79_source_sha256':sha(SRC),
 'ev80_reference_sha256':sha(REF),'points':results,
 'limits':['Only the three vertices called out from the plotted profiles were sampled.','This local geometry/mask inspection does not establish a rendering cause or survey nearby faces.']}
out=B/'residual-review'/'focus-points.json'
out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# Tres vértices de los perfiles EV80→B','','Solo lectura; son los tres puntos observados en los cortes 1:1. Ángulos calculados con producto vectorial sobre las seis caras incidentes y doce bisagras locales.','']
for q in results:
    lines += [f"## {q['name']} · ({q['x_m']}, {q['z_m']}) m · fila/columna ({q['row']},{q['col']})",'',
      f"EV79/EV80/B: {q['heights']['ev79_m']:.6f}/{q['heights']['ev80_m']:.6f}/{q['heights']['ev82b_m']:.6f} m; Δ B−EV80 {q['heights']['ev82b_minus_ev80_m']:+.6f} m; B−EV79 {q['heights']['ev82b_minus_ev79_m']:+.6f} m.",
      f"Selector={q['selector_vertex']}; máscara: `{json.dumps(q['flags'],ensure_ascii=False)}`.",
      f"EV82-B: 6 caras >30° = {q['geometry_ev82b']['faces_over_30']}, max pendiente {q['geometry_ev82b']['max_face_slope_deg']:.4f}°; 12 bisagras >30° = {q['geometry_ev82b']['hinges_over_30']}, max diedro {q['geometry_ev82b']['max_hinge_angle_deg']:.4f}°.",
      f"Pendientes de las 6 caras (EV80→B): `{[round(x,4) for x in q['geometry_ev80']['six_incident_face_slopes_deg']]}` → `{[round(x,4) for x in q['geometry_ev82b']['six_incident_face_slopes_deg']]}`°.",
      f"Diedros de las 12 bisagras (EV80→B): `{[round(x,4) for x in q['geometry_ev80']['twelve_incident_hinge_angles_deg']]}` → `{[round(x,4) for x in q['geometry_ev82b']['twelve_incident_hinge_angles_deg']]}`°.",
      f"Conclusión local: {'seleccionado para EV82; decisión '+q['ev82_author_decision']['decision_reason'] if q['selector_vertex'] else 'fuera del selector EV82'}; no inferir que las caras circundantes tengan la misma clasificación.",'']
lines += ['Estos son exactamente tres puntos; no se amplió el dominio ni se modificó candidato, masks, agua o motor.']
(B/'residual-review'/'focus-points.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'points':[{'name':q['name'],'row':q['row'],'col':q['col'],'selector':q['selector_vertex'],'flags':q['flags'],'height_B':q['heights']['ev82b_m'],'faces_gt30':q['geometry_ev82b']['faces_over_30'],'max_face':q['geometry_ev82b']['max_face_slope_deg'],'hinges_gt30':q['geometry_ev82b']['hinges_over_30'],'max_hinge':q['geometry_ev82b']['max_hinge_angle_deg']} for q in results]},indent=2))
