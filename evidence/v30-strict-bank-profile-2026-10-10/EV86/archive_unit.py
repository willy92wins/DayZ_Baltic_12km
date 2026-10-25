"""Preserve completed EV85/86 evidence; global EV87 remains a separate unit."""
from pathlib import Path
import hashlib,json,shutil,re
R=Path('E:/DayZ-Baltic-Build');O=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-strict-bank-profile-2026-10-10';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={'feasibility':R/'v30-coupled-shore-feasibility-20261010',
         'rejected-EV85':R/'v30-coupled-shore-pilot-20261010',
         'EV86':O,'global-inventory':R/'v30-global-relief-queue-20261010'}
manifest=[]
for label,root in sources.items():
 for p in sorted(root.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts or p.suffix not in ('.py','.md','.json','.png'):continue
  target=D/label/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(p,target);assert sha(p)==sha(target)
  manifest.append({'path':str(target.relative_to(D)).replace('\\','/'),'source':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
external=[]
for p in (sources['rejected-EV85']/'diagnostic-vector.npz',sources['rejected-EV85']/'quantized-repair/candidate-terrain.npz',O/'candidate-terrain.npz'):
 external.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
readme='''# EV86 — piloto de perfil estricto, verificado offline

EV86 pasa el consumidor independiente sobre dos parches de orilla:33 alturas,
220 signos estrictos de vecinos conservados, cero extremos axiales nuevos.
Los focos bajan0,858/0,780m y su energía angular baja43,31%/35,82%.
Pasan cotas, pendientes, sectores, p99/conteos, P/F, cruces, componentes y
cobertura física/visible ODOL. El candidato NPZ es85b09e55954811edfa3933d979db1513898ea9ea328421f68c87007ac79f6076.

La fuente/preview sigue EV82-B f9fb23de; EV86 no se empaquetó por separado.
La cobertura usa transforms0WZD fuente ligados por hash al OPRW/PBO desplegado;
no es readback del motor, prueba gráfica ni aceptación de base1.0.

## Por qué cambió el método

EV85 SLSQP dio estado8 y12 inversiones micrométricas. Su única corrección
numérica explícita EV85-R corrigió orden y cruces, pero dejó9 extremos débiles
por mesetas; ambos se mantienen RECHAZADOS. El diseño permitía igualar vecinos
pero su criterio de forma prohibía esos extremos: repetir tolerancias no lo resolvía.

EV86 fija el punto medio B/R y demuestra que conserva al menos la mitad de cada
pendiente original antes de redondear. Verifica signos estrictos después de
cuantizar, sin reparar ULP ni buscar factores. El consumidor conserva el gate
de extremos débiles, que ahora pasa. Corrigió además un flag informativo que el
harness anterior había situado por error entre los gates: los metadatos reales
se comprueban con terrain_metadata_exact; no cambia el rechazo geométrico deR.

## Cobertura del mapa y siguiente unidad

El inventario lee toda la malla2048²:18768 vértices secos editables incidentes a
quiebros>30°,15173 junto al agua,2358 en taludes secos de río y1237 interiores.
Son medidas geométricas, no ese número de defectos visuales confirmados.
Se prepara EV87, una pasada de parches disjuntos en todas las crestas editables,
con máscaras protegidas intactas y verificador global. Plan vivo externo:
E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/plan.md.

Los rectángulos de render, agua visual sobre tierra, grandes lagos, finales,
TerrainBuilder y navmesh continúan abiertos. No hubo DayZ ni lease en esta unidad.
'''
(D/'README.md').write_text(readme,encoding='utf8')
manifest.append({'path':'README.md','bytes':(D/'README.md').stat().st_size,'sha256':sha(D/'README.md')})
(D/'manifest.json').write_text(json.dumps({'files':manifest,'external_large_artifacts':external},indent=2)+'\n',encoding='utf8')
for q in manifest:assert sha(D/q['path'])==q['sha256']
h=W/'HANDOFF.md';text=h.read_text(encoding='utf8')
updates={
'status':'BASE_1_0_NO_ACEPTADA. EV82-B sigue desplegado. EV86 piloto estricto offline PASS; EV85 y R rechazados por mesetas. EV87 pasada global en preparación/autorizada tras review, ver su plan externo. Render abierto.',
'next':'EV87 en E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010. Una pasada global de crestas con parches disjuntos, pendientes estrictas midpoint1/2, p99 por cuentas de ranks y consumidor global. No empaquetar piloto separado. Consultar progreso vivo antes de ejecutar; autoría delegada Luna.',
'handoff':'evidence/v30-strict-bank-profile-2026-10-10/README.md + manifest. EV86 solo offline, fuenteB sigueoperativa; EV85/R rechazados. Mantener pruebas geométricas/render separadas.',
'git':'Branch claude/codex-handoff-review-74f290; EV82-B6c98ab1, soporte5c975ec, nueva unidadEV86 consultar gitlog. Sin push.'}
for key,value in updates.items():
 text,n=re.subn(r'^'+re.escape(key)+r':.*$',key+': '+value,text,count=1,flags=re.M);assert n==1
h.write_text(text,encoding='utf8',newline='\n')
b=W/'bugs.md';text=b.read_text(encoding='utf8');lines=text.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| BALTIC-007 |'):
  cols=line.split('|');cols[2]=' EV86 PILOTO ESTRICTO OFFLINE PASS; GLOBAL Y VISUAL ABIERTOS '
  cols[4]=' EV86:33 alturas,0 extremos axiales nuevos,220 signos estrictos; no paquete/motor. EV85/R rechazados por mesetas. Evidencia evidence/v30-strict-bank-profile-2026-10-10/README.md. '+cols[4].lstrip();lines[i]='|'.join(cols);break
b.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-10-dayz-baltic-bank-relief.md')
with session.open('a',encoding='utf8') as f:f.write('\n\n## EV86 perfil estricto y preparación global\n\n'+readme+'\nEvidencia durable: '+str(D)+'\n')
print(json.dumps({'archived_files':len(manifest),'bytes':sum(q['bytes'] for q in manifest),'destination':str(D)}))
