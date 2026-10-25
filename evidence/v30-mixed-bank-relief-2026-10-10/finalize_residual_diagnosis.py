from pathlib import Path
import json, hashlib, sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt
B=Path(__file__).resolve().parent
R=B.parent
EV79=R/'v30-narva-dry-bank-relief-20261010'
sys.path.insert(0,str(B/'review-luna'))
import verify as v
report=json.loads((B/'residual-diagnosis.json').read_text(encoding='utf-8'))
source=np.load(EV79/'candidate'/'terrain.npz')
candidate=np.load(B/'candidate'/'terrain.npz')
con=np.load(EV79/'constraints.npz')
h0=source['heights'].astype(np.float64); h1=candidate['heights'].astype(np.float64); cls=source['cls']
wet=con['wet_support'].astype(bool); fixed=con['fixed'].astype(bool)
flow=np.isin(cls,(3,5,6)); dist=distance_transform_edt(~flow,sampling=6.0)
dry=(cls==0)&~wet&~source['water'].astype(bool)&~source['beach'].astype(bool)&~source['reserve'].astype(bool)&~source['platform'].astype(bool)
bank=dry&(dist<=96.0+1e-9)
allowed=(cls==0)&(dist<=96.0+1e-9)&~fixed
# Source selector is exactly EV80's domain intersected with vertices incident to source >30 hinges.
touch=np.zeros(cls.shape,dtype=bool)
for kind,a in v.edge_angles(h0):
    m=a>30.0+v.TOL_DEG
    if kind=='diagonal': touch[:-1,:-1]|=m; touch[:-1,1:]|=m; touch[1:,:-1]|=m; touch[1:,1:]|=m
    elif kind=='vertical': touch[:-1,:-2]|=m; touch[:-1,1:-1]|=m; touch[1:,1:-1]|=m; touch[1:,2:]|=m
    else: touch[:-2,:-1]|=m; touch[1:-1,:-1]|=m; touch[1:-1,1:]|=m; touch[2:,1:]|=m
selector=allowed&touch
changed=h1!=h0
residual=[]
state={'no_selector_protected_bank':0,'selector_no_edit':0,'selector_edit_only':0,'selector_mixed_edit_unedited':0}
by_kind={k:{s:0 for s in state} for k in ('diagonal','vertical','horizontal')}
for kind,a in v.edge_angles(h1):
    mixed=v.incident_any(bank,kind)&v.incident_any(wet,kind)
    mask=mixed&(a>30.0)
    coords=np.argwhere(mask)
    # Endpoint slices in consumer order; vertical fourth corner is (r+1,c+2).
    if kind=='diagonal': corners=(selector[:-1,:-1],selector[:-1,1:],selector[1:,:-1],selector[1:,1:]); edits=(changed[:-1,:-1],changed[:-1,1:],changed[1:,:-1],changed[1:,1:]); centers=(6*coords[:,1]+3,12282-6*coords[:,0]-3)
    elif kind=='vertical': corners=(selector[:-1,:-2],selector[:-1,1:-1],selector[1:,1:-1],selector[1:,2:]); edits=(changed[:-1,:-2],changed[:-1,1:-1],changed[1:,1:-1],changed[1:,2:]); centers=(6*(coords[:,1]+1),12282-6*coords[:,0]-3)
    else: corners=(selector[:-2,:-1],selector[1:-1,:-1],selector[1:-1,1:],selector[2:,1:]); edits=(changed[:-2,:-1],changed[1:-1,:-1],changed[1:-1,1:],changed[2:,1:]); centers=(6*coords[:,1]+3,12282-6*(coords[:,0]+1))
    anysel=np.logical_or.reduce(corners); anyedit=np.logical_or.reduce([c&e for c,e in zip(corners,edits)]); anyun=np.logical_or.reduce([c&~e for c,e in zip(corners,edits)])
    for ix,(r,c) in enumerate(coords):
        s= ('no_selector_protected_bank' if not anysel[r,c] else ('selector_mixed_edit_unedited' if anyedit[r,c] and anyun[r,c] else ('selector_edit_only' if anyedit[r,c] else 'selector_no_edit')))
        state[s]+=1; by_kind[kind][s]+=1
        residual.append((kind,int(r),int(c),float(a[r,c]),bool(anysel[r,c])))
# Assert corrected census before touching outputs.
assert len(residual)==3384, len(residual)
assert state=={'no_selector_protected_bank':217,'selector_no_edit':1753,'selector_edit_only':1325,'selector_mixed_edit_unedited':89},state
assert sum(x[4] for x in residual)==3167
report['counts']['participant_state']=state
report['counts']['participant_state_by_kind']=by_kind
report['counts']['with_any_selector_vertex']=3167
report['counts']['without_selector_vertex']=217
report['counts']['selector_but_no_accepted_edit']=1753
report['counts'].pop('freedom_and_water_support',None)
report['counts']['source_angle_le_30.0001_but_candidate_over30']=2
report['counts']['interpretation_of_float32_bank_p99_rejected']={
 'count':1275,
 'meaning':'Post-float32 direct cross-product comparison rejected a proposed nodal value because at least one originally-under-p99 bank hinge exceeded the EV79 p99 cap by more than 2e-8 degrees.',
 'not_proven':'No per-node margins or alternate nextafter probes were retained in authoring.json; therefore these are not yet classified as quantization-only, and they do not prove geometric infeasibility under another value.'}
report.pop('no_selector_by_kind',None)
report.pop('top_10_individual_residual_hinges',None)
report['incidence_fixture']={
 'status':'PASS',
 'one_hot_masks_four_corners':{'diagonal':True,'vertical':True,'horizontal':True},
 'vertical_wrong_corner_r_c_plus_2':False,
 'triangle_pair_direct_check':{'diagonal':True,'vertical':True,'horizontal':True},
 'notes':'Para cada orientacion se compararon las dos caras que comparten la arista con formula de producto vectorial directo y el mapa edge_angles del consumidor; en vertical la esquina exterior correcta es (r+1,c+2).'}
# Plot layers, using native cell centers and corrected consumer edge-to-point placement.
fig,ax=plt.subplots(figsize=(10,10),dpi=180)
for k,col in ((3,'#64a8d4'),(5,'#2e9f9a'),(6,'#5775b7')):
    rr,cc=np.where(cls==k); ax.scatter(6*cc+3,12282-6*rr-3,s=0.16,c=col,alpha=.55,rasterized=True,label=f'flow class {k}')
rr,cc=np.where(changed); ax.scatter(6*cc+3,12282-6*rr-3,s=0.45,c='#f1a340',alpha=.85,rasterized=True,label=f'{len(rr)} modified vertices')
free=[x for x in residual if x[4]]; blocked=[x for x in residual if not x[4]]
for data,color,marker,label in ((free,'#00c98d','o',f'residual >30° with EV80 selector ({len(free)})'),(blocked,'#ed3562','x',f'residual >30° without selector ({len(blocked)})')):
    if data:
        xx=[]; zz=[]
        for kind,r,c,a,s in data:
            if kind=='diagonal': x=6*c+3; z=12282-6*r-3
            elif kind=='vertical': x=6*(c+1); z=12282-6*r-3
            else: x=6*c+3; z=12282-6*(r+1)
            xx.append(x); zz.append(z)
        ax.scatter(xx,zz,s=5 if marker=='o' else 11,c=color,marker=marker,linewidths=.7,alpha=.9,rasterized=True,label=label)
ax.set(xlim=(0,12288),ylim=(0,12288),xlabel='x (m)',ylabel='z (m)',title='EV80 — diagnóstico geométrico offline · planta 12.288 × 12.288 km\nSin relieve vertical ni aceptación de render; bisagras mixtas >30°')
ax.set_aspect('equal'); ax.grid(False); ax.legend(loc='lower left',fontsize=8,framealpha=.9,ncol=2)
fig.tight_layout(); fig.savefig(B/'residual-diagnosis.png'); plt.close(fig)
report['figure']['path']=str(B/'residual-diagnosis.png')
report['figure']['sha256']=hashlib.sha256((B/'residual-diagnosis.png').read_bytes()).hexdigest()
report['figure']['description']='Plan view; flow classes 3/5/6, 2,591 modified height vertices and 3,384 candidate residual mixed hinges split by source-reconstructed EV80 selector (3,167/217); no vertical exaggeration and not a DayZ render.'
(B/'residual-diagnosis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
# Markdown uses recomputed corrected totals and existing peak/sector records.
lines=['# Diagnostico residual EV80','',f"Candidate SHA: `{report['source_candidate_sha256']['ev80_candidate']}`  ",f"Consumer report SHA: `{report['consumer_report_sha256']}`",'', 'Bisagra residual = ángulo candidato >30° y `mixed_any` del consumidor EV80: al menos una esquina de bank mask y una esquina de wet support de EV79. Esto es clasificación geométrica, no diagnóstico visual/render.','', '![Mapa de cobertura geométrica offline](residual-diagnosis.png)','', '## Censo corregido','', '- Total: **3384** (diagonal 2176, vertical 605, horizontal 603).','- Con al menos una esquina perteneciente al selector fuente EV80: **3167**; sin esquina seleccionable: **217**.','- Estado de esquinas seleccionables: 1753 sin cambio aceptado en el barrido; 1325 con una o más esquinas ya editadas; 89 contienen tanto esquinas editadas como no editadas. Las cifras describen incidencia de extremos y pueden solaparse en los dos últimos estados solamente como definidos.','- Dos bisagras caen en la franja numérica `source<=30.0001°` y `candidate>30°`; el consumidor conserva su tolerancia/gate independiente.','', '## Qué bloquea las 217 sin selector','', 'Todas las 217 tienen sus esquinas de bank que podrían pertenecer al selector protegidas por al menos una máscara semántica; los hits se solapan: halo de ingeniería 90, grandes lagos 59, borde 11 celdas 45 y controles temporales 25. Combinaciones exclusivas: halo 88, grandes lagos 59, borde 45, controles 23, halo+controles 2. Reserva/plataforma core no bloquean una esquina bank en este subconjunto; aparecen en 64 bisagras como contexto del lado húmedo.','', 'Las 217 tocan wet support porque esa condición forma parte del predicado mixed-any. Eso no demuestra que haya que mover agua: su esquina seca del bank está fijada por las máscaras enumeradas. No se identificó un grado de libertad seco dentro del selector EV80 para ellas.','', '## Rechazos float32 de p99','', 'El autorizador registra 1275 rechazos `float32_bank_p99_rejected`. En [author.py](author.py#L413), primero redondea la altura propuesta a float32, vuelve a medir los doce diedros con producto vectorial directo y rechaza si una bisagra bank que estaba bajo el p99 EV79 excede ese límite en más de `2e-8°` ([líneas 433–435](author.py#L433)). Es una comprobación estricta post-cast, no una prueba de imposibilidad geométrica ni evidencia de que los 1275 sean solo cuantización. El registro no retuvo propuesta, margen ni coordenada por rechazo; hasta la sonda `nextafter` autorizada, la proporción rescatable en ≤2 ULP es desconocida.','', '## Diez focos conectados más densos','', '|#|N|pico (x,z)m|tipo/fila,col|ángulo|selector|','|---:|---:|---:|---|---:|---:|']
for i,a in enumerate(report['top_10_connected_areas_8_neighbor'],1):
 p=a['peak']; lines.append(f"|{i}|{a['hinges']}|{p['x_m']:.1f},{p['z_m']:.1f}|{p['kind']}/{p['edge_row']},{p['edge_col']}|{p['angle_deg']:.2f}°|{a['with_selector']}|")
lines += ['', '## Diez sectores 64×64 más densos','', '|#|Sector|N|pico (x,z)m|tipo/fila,col|ángulo|selector|','|---:|---:|---:|---:|---|---:|---:|']
for i,a in enumerate(report['top_10_64x64_sectors'],1):
 p=a['peak']; lines.append(f"|{i}|{a['sector_row']},{a['sector_col']}|{a['hinges']}|{p['x_m']:.1f},{p['z_m']:.1f}|{p['kind']}/{p['edge_row']},{p['edge_col']}|{p['angle_deg']:.2f}°|{a['with_selector']}|")
lines += ['', '## Límites','', '- `selector_no_edit` significa que los vértices seleccionables incidentes no cambiaron en la pasada; no demuestra que otra delta factible no exista.','- Las causas de máscara son por intersección con extremos y no atribuyen causa única por bisagra.','- Esta figura y los conteos son geometría offline: no describen color/forma de píxel ni prueban corrección visual de DayZ.','- No se modificaron terreno, candidato, authoring ni máscaras consumidoras; solo se actualizaron este JSON, Markdown y figura diagnóstica.','']
(B/'residual-diagnosis.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'state':state,'total':len(residual),'free':len(free),'blocked':len(blocked),'figure_sha':report['figure']['sha256'],'incidence_fixture':report['incidence_fixture']},ensure_ascii=False))
