"""Archive a completed offline unit. Does not traverse generated packages/junctions."""
from pathlib import Path
import json,hashlib,shutil
R=Path('E:/DayZ-Baltic-Build'); B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-shore-support-pilot-2026-10-10'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not D.exists()
review=json.loads((B/'review-independent/ev83-review.json').read_text())
assert review['status']=='PASS_EV83_REVIEW' and all(review['gates'].values())
assert sha(B/'candidate/terrain.npz')=='f0e977d8bc2e11529aedc3851bb1d456b45ffee0e2b974af89db6a26fab087f9'
assert sha(B/'review-independent/verify_ev83.py')=='4af00546ba72dea411442d3f2464386778331e08c7fb745331d5989a280c0410'
D.mkdir(parents=True)
groups={'feasibility':R/'v30-bank-support-feasibility-20261010','pilot':B,'isolated-order-not-authored':R/'v30-shore-order-pilot-20261010','render-api-research':R/'v30-render-event-feasibility-20261010'}
for folder,source in groups.items():
 dst=D/folder;dst.mkdir()
 for p in source.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.md','.png'}:
   assert p.stat().st_size<3_000_000,p
   shutil.copy2(p,dst/p.name)
 if folder=='pilot':
  target=dst/'review-independent';target.mkdir()
  for p in (source/'review-independent').iterdir():
   if p.is_file() and p.suffix in {'.py','.json','.md'}:shutil.copy2(p,target/p.name)
text='''# Orillas: diagnóstico y piloto sin promoción

EV82-B (`6c98ab1`) sigue siendo la única preview desplegada. Esta unidad no cambia el paquete, no inicia DayZ ni cierra la base 1.0.

La conservación exacta del cruce de agua fijaba dos crestas secas a sus vecinos sumergidos inmutables. LP local y revisión explican la ecuación; no era falta de intensidad del filtro. P/F local coinciden; el calado de 0,95 m no aplica a esos puntos fuera del corredor.

EV83 permite mover la orilla <=1 m en dos puntos. Bajan 0,53847 y 1,10991 m; energía de las doce bisagras -23,077% y -25,858%; cruces máximos 0,09510 y 0,50952 m. Geometría y cobertura del consumidor independiente PASS, pero **NO PROMOVER**: el segundo pico se convierte en una V axial nueva. Los perfiles completos 1:1 muestran la regresión que una métrica agregada y la gráfica de una sola arista ocultan. El primero también invierte orden con dos vecinos en el entorno8.

Cobertura: ODOL compilados y transforms del 0WZD fuente hash-vinculado al OPRW/PBO; no transforms leídos del motor. Huella física/visible cubierta dentro de 3,77e-13 m2; gana 1,88276 m2 de orilla diseñada, sin pérdida ni nueva exposición en caras secas. P/F y metadatos exactos, protecciones y grandes lagos conservados. El consumidor detectó/corrigió sus propios errores de epsilon, resolución float32, extrapolación de terreno fuera de cada triángulo y conjunto incompleto de bisagras; fixture independiente de una cara ODOL grande sobre relieve quebrado exige 27 m2.

Propuesta aislada de orden (EV84): no se creó candidato. Preservar el orden de ocho vecinos fijos limita el segundo foco a bajar 0,03505 m, por debajo del mínimo material de 0,1 m. El siguiente diagnóstico examina movimientos conjuntos de los vecinos secos sin protección en dos ventanas7x7; aún no es un candidato ni una extensión al mapa. Root censó 48640 vértices fluviales secos de soporte mojado sin otras protecciones, 15173 incidentes a quiebros>30 en 53 sectores de1536m. Es un inventario de geometría, no confirmación visual de 15173 defectos.

Rectángulos grises: investigación de API no halló una sonda pasiva demostrada. GetLODS no devuelve LOD renderizado; SetFixedLOD está bajo ENF_DONE; EOnVisible puede intervenir en la decisión de render y su despacho sobre ponds estáticos es nativo no verificado. No se lanzó otro ensayo ciego ni se cambió material.

Revisión: pilot/review-independent/review.md. Perfiles: pilot/profiles-full-1to1.png. No aceptación gráfica, no push. Terreno completo/P/F externos fijados por hash; deltas explícitos en authoring-report.json permiten reproducir los dos cambios.
'''
(D/'README.md').write_text(text,encoding='utf-8',newline='\n')
external=[B/'candidate'/x for x in ['terrain.npz','plane.npy','visible-field.npy']]
(D/'external-artifacts.json').write_text(json.dumps({'files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in external]},indent=2)+'\n')
manifest=[{'path':p.relative_to(D).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(D.rglob('*')) if p.is_file()]
(D/'manifest.json').write_text(json.dumps({'decision':'NO_PROMOTION_PRODUCT_REGRESSION','files':manifest},indent=2)+'\n')
for row in manifest:assert sha(D/row['path'])==row['sha256']
h=W/'HANDOFF.md';s=h.read_text(encoding='utf-8');a=s.index('<!-- LIVE-STATE:START -->');b=s.index('<!-- LIVE-STATE:END -->');lines=s[a:b].splitlines()
updates={
 'status:':'status: BASE_1_0_NO_ACEPTADA. EV82-B validado y desplegado. EV83 offline PASS pero NO PROMOVER: crea V axial; propuesta aislada con orden inviable sin mover vecinos. Investigar suavizado conjunto local; render abierto.',
 'next:':'next: LP conjunto en E:/DayZ-Baltic-Build/v30-coupled-shore-feasibility-20261010, dos parches7x7 secos sin protección, orden8vecinos/cruces<=1m/suelo y presupuesto. No candidato global ni motor pendientes. EV83 descartado por forma; no repetir selector seco ni bajar nodos aislados. EV68 sin promover.',
 'git:':'git: Branch claude/codex-handoff-review-74f290; EV82-B commit6c98ab1. Nueva evidencia evidence/v30-shore-support-pilot-2026-10-10, consultar gitlog; sin push.',
 'handoff:':'handoff: evidence/v30-shore-support-pilot-2026-10-10/README.md + manifest: diagnóstico/piloto no promovido. EV82-B operativo en evidence/v30-incremental-bank-relief-2026-10-10. Conservar pruebas geométricas/render separadas.'}
for i,line in enumerate(lines):
 for key,value in updates.items():
  if line.startswith(key):lines[i]=value;break
h.write_text(s[:a]+'\n'.join(lines)+'\n'+s[b:],encoding='utf-8',newline='\n')
bug=W/'bugs.md';lines=bug.read_text(encoding='utf-8').splitlines()
for i,line in enumerate(lines):
 if line.startswith('| BALTIC-007 '):
  cells=line.split('|');cells[2]=' EV82-B DESPLEGADO; EV83 NO PROMOVER POR FORMA ';cells[4]=' EV83: cruce limitado/ODOL PASS, pero genera V axial; preservar orden requiere mover vecinos. Evidencia evidence/v30-shore-support-pilot-2026-10-10/README.md. '+cells[4].lstrip();lines[i]='|'.join(cells)
bug.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-10-dayz-baltic-bank-relief.md')
with session.open('a',encoding='utf-8') as f:f.write('\n## Diagnóstico de soporte mojado y EV83 no promovido\n\n'+text+'\nEvidencia: '+str(D)+'\n')
print(json.dumps({'archive':str(D),'files':len(manifest),'bytes':sum(x['bytes'] for x in manifest)}))
