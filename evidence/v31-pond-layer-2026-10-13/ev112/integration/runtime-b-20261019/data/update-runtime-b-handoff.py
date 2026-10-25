"""Update only this task's live state; preserve shared files with checked backups."""
from pathlib import Path
import hashlib,json,datetime,subprocess
O=Path(__file__).parent;W=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
V=Path('C:/Users/guill/ObsidianVault/AI');A=W/'evidence/v31-pond-layer-2026-10-13/ev112/integration/runtime-b-20261019'
C=json.loads((O/'runtime-b-closure.json').read_text());R=json.loads((O/'build-review-closure-runtime-b.json').read_text())
assert C['status']=='AUTHORIZED_SERVER_SCOPE_COMPLETED_WITH_EXPLICIT_PENDING' and all(C['checks'].values()) and (A/'README.md').exists()
now=datetime.datetime.now().astimezone();date=now.date().isoformat();stamp=now.isoformat()
B=O/'handoff-runtime-b-backups';B.mkdir(exist_ok=False);changes=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(path,transform):
 raw=path.read_bytes();s=raw.decode('utf-8').replace('\r\n','\n');new=transform(s);assert new!=s,path
 print('Document characters',str(path),len(s),'->',len(new));assert len(new)>=.9*len(s),'unexpected document shrink'
 nl='\r\n' if b'\r\n' in raw else '\n';data=new.replace('\n',nl).encode('utf-8')
 backup=B/f'{len(changes):02}-{path.name}';backup.write_bytes(raw);assert path.read_bytes()==raw,'concurrent edit'
 path.write_bytes(data);assert path.read_bytes()==data
 changes.append(dict(path=str(path),before=sha(raw),after=sha(data),backup=str(backup)))
link='evidence/v31-pond-layer-2026-10-13/ev112/integration/runtime-b-20261019/README.md'
url='<'+str(A/'README.md').replace('\\','/')+'>'
br=f"{C['bridge_passed']}/{C['bridge_sites']}";sh=f"{C['shores']['wet_ok']+C['shores']['dry_ok']}/{C['shores']['n']}";kp=C['kit_required']['passed'];kt=C['kit_required']['total'];pc=C['concrete_pending_count'];refs=C['kit_unclassified_reference_points'];pr=C['probe_rows'];tr=C['temporal_rows']
b18=C['bridge_01518']['baseline'];n18=C['bridge_01518']['current'];w18=f"{b18['wet']}/{b18['under']}→{n18['wet']}/{n18['under']}"
summary=f"EV112: correcciones e integración verificadas; sonda de servidor completada ({pr} puntos). Puentes {br}, orillas {sh}, presa y {kp} controles obligatorios del kit PASS. G8 estricto conserva FAIL por {C['concrete_pending_count']} labios/juntas de hormigón pendientes según plan §5. Vista personal instalada y preparada, sin lanzar."
limits='015-45/disco60m PENDIENTE, nunca PASS. Juntas de hormigón pendientes. OT4<=0,03m solo en el dominio central. Límites forestales/regionales y de fase conservados. Sin aceptación visual, FPS ni capacidad80–100jugadores.'
def live(s,root=False):
 a=s.index('<!-- LIVE-STATE:START -->');b=s.index('<!-- LIVE-STATE:END -->',a);old=s[a:b]
 print('LIVE span',len(old));assert len(old)<20000,'unexpectedly long live block; preserve history'
 assert ('Correccion fisica aislada de4vertices en validacion' in old or 'EV112 runtime B desplegado; OT7 R2' in old)
 repl={'updated':stamp,'status':summary,'blocker':'Sin bloqueo del banco ni trabajo de servidor pendiente en el alcance autorizado. '+limits,
 'worktree':'P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c — rama claude/handoff-astra-map-review-6d301c; capa correctora '+R['source_commit']+'. Generador AE de845295f conservado. Checkout raíz v29-base no integrado.',
 'deployed':C['mod']+' — mundo '+C['world_sha256']+'; agua '+C['water_sha256']+'. Carga del terreno corregido contrastada en motor.',
 'validation':f"OT7 R1 y R2 {R['verdict']}, cero críticos/mayores abiertos. Cuatro vértices corregidos, huella y objetos idénticos; G1/G4 bosque y cinco consumidores pintados nuevos PASS. Sonda completa y diagnóstico30x8 capturados. G8kit sigue FAIL solo por hormigón conocido; no se cambió ningún gate.",
 'cleanup':f"Runs {C['probe_run_id']} y {C['temporal_run_id']} cerrados ordenadamente, retirados y leases liberados. También cerradas las dos ejecuciones anteriores. Cliente nunca lanzado. Paquete anterior preservado.",
 'next':'Cuando Guillermo esté delante: vista preparada personal-view-runtime-b/README.md y launch-request.json en el build. Revisar terreno, bosque y FPS. No reabrir los cuatro controles corregidos ni declarar resueltos los pendientes pactados.',
 'git':'Fuente de corrección en '+R['source_commit']+'; rama claude/handoff-astra-map-review-6d301c, sin push. Evidencia/documentación en este worktree; cambios ajenos de parada Baltic preservados.',
 'handoff':('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/HANDOFF.md' if root else 'Plan plans/ev112-plan-astra.md; cierre '+link+'; sesión canónica C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-18-dayz-baltic-ev112-ot1-execution.md.'),
 'evidence':str(A/'README.md').replace('\\','/'),'limits':limits,
 'plan':('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/plans/ev112-plan-astra.md' if root else 'plans/ev112-plan-astra.md: OT1–OT7 y sonda OT8 completadas con pendientes explícitos de §5; vista personal preparada según picker.')}
 lines=[];present=set()
 for line in old.splitlines():
  key=line.split(':',1)[0]
  if key in repl:lines.append(key+': '+repl[key]);present.add(key)
  else:lines.append(line)
 if 'deployed' not in present:lines.append('deployed: '+repl['deployed'])
 return s[:a]+'\n'.join(lines)+'\n'+s[b:]
write(W/'HANDOFF.md',lambda s:live(s))
write(Path('P:/DayZ_Baltic_12km_dev/HANDOFF.md'),lambda s:live(s,True))
def plan(s):
 a=s.index('## Estado de ejecución');b=s.index('## 0. Dónde está todo',a)
 return s[:a]+f"## Estado de ejecución — {date}\n\n{summary}\n\nOT7 R2 {R['verdict']}, sin críticos ni mayores abiertos. La primera sonda detectó cuatro controles afectados por oleaje; se corrigieron cuatro vértices sin alterar huella, topología ni objetos. La nueva sonda y el diagnóstico temporal pasan esos controles. Se conserva el FAIL original y el FAIL estricto de las juntas. No renovación del lanzador ni cambios de umbrales. {limits}\n\n[Evidencia y cierre](../{link}). Fuentes de corrección: {R['source_commit']}; sin push.\n\n"+s[b:]
write(W/'plans/ev112-plan-astra.md',plan)
def bugs(s):
 s=s.replace('Actualización EV11219-10-2026;',f'Actualización EV112 {date};')
 s=s.replace('**EV112 desplegado19-10, sin cierre visual:**','**EV112 con sonda servidor completada, sin cierre visual:**')
 s=s.replace('Kit v9 en49/51sitios y orillas centrales verificadas offline; falta sonda y vista.',f'Kit v9 en49/51sitios; {kp}/{kt} controles obligatorios del kit y{sh}orillas PASS en servidor.{pc}juntas/labios de hormigón siguen pendientes y G8 estricto FAIL; falta vista.')
 s=s.replace('Puentes v6 integrados y verificados offline; sonda/no-regresión EV110 pendientes;015-45/60m sigue pendiente.',f'Puentes v6:{br} PASS en servidor, sin regresión frente aEV110;015-18 {w18}mojados.015-45/60m sigue pendiente.')
 s=s.replace('[Build revisado](evidence/v31-pond-layer-2026-10-13/ev112/integration/reviewed-ae-awaiting-runtime/README.md). Sonda bloqueada por banco ajeno;',f'[Sonda y pendientes]({link}). Vista personal preparada;')
 return s
write(W/'bugs.md',bugs)
def projectmap(s):
 s=s.replace('Actualizado 2026-10-19 20:44.',f'Actualizado {now:%Y-%m-%d %H:%M}.')
 a='| Evidencia del build revisado | [README](evidence/v31-pond-layer-2026-10-13/ev112/integration/reviewed-ae-awaiting-runtime/README.md) |'
 assert a in s
 return s.replace(a,f'| Cierre de servidor y pendientes | [README]({link}) |\n| Revisión previa OT7 R1 | [README](evidence/v31-pond-layer-2026-10-13/ev112/integration/reviewed-ae-awaiting-runtime/README.md) |')
write(W/'PROJECT-MAP.md',projectmap)
session=V/'30_Sessions/2026-10-18-dayz-baltic-ev112-ot1-execution.md'
def ses(s):
 i=s.index('## Histórico de ejecución, conservado')
 return '# EV112 — servidor completado; vista personal preparada\n\n'+summary+'\n\n'+f"Cierre {stamp}. OT7 R2 {R['verdict']}; fuentes {R['source_commit']}, sin push. Cuatro vértices corrigen los fallos nuevos de la primera sonda, manteniendo huella, costa local del islote, topología y objetos. Verificación temporal30x8: cuatro controles y sus referencias estables en las30muestras; no prueba todos los climas.\n\n"+limits+'\n\n'+f"Run de sonda `{C['probe_run_id']}`; temporal `{C['temporal_run_id']}`. Capturados antes de cierre ordenado; runs retirados y leases liberados. Cliente no lanzado;16archivos de vista instalados y comprobados por hash. Paquete `{C['mod']}`. [Cierre completo]({url}).\n\nLa propuesta de cambiar gates por flags/NoFakeWave fue descartada. No hubo picker adicional ni waiver para los cuatro controles: se corrigió el terreno. Los candidatos fallidos y los FAIL de fase/regionales permanecen archivados con su alcance.\n\n"+s[i:]
write(session,ses)
index=V/'30_Sessions/index.md'
def idx(s):
 lines=s.splitlines();hits=[i for i,line in enumerate(lines) if '](./2026-10-18-dayz-baltic-ev112-ot1-execution.md)' in line];assert len(hits)==1
 lines[hits[0]]=f"- [DayZ Baltic — EV112: servidor completado, vista preparada](./2026-10-18-dayz-baltic-ev112-ot1-execution.md) — Sonda{pr} y temporal{tr};{br}puentes/{sh}orillas/presa/{kp}controleskit PASS. G8estricto conserva{pc}juntas pendientes porplan§5. OT7R2 {R['verdict']}, sin mayores; fuente {R['source_commit'][:7]}, sin push.015-45/60m yvista/FPS pendientes."
 return '\n'.join(lines)+'\n'
write(index,idx)
matrix=V/'10_Projects/DayZ_Baltic_12km/validation-matrix.md'
def mat(s):
 a=s.index('## Estado vigente');b=s.index('## Histórico',a)
 return s[:a]+f"## Estado vigente — EV112, {date}\n\n[Cierre y evidencia]({url}). {summary}\n\n| Puerta | Estado y alcance |\n|---|---|\n| Terreno y paquete | Cuatro vértices corregidos; huella/topología/objetos conservados. Superficie G1–G6, lectura de2.578.916objetos y consumidores forestales afectados PASS. |\n| OT7 R2 | {R['verdict']};0críticos/mayores abiertos. Fuente {R['source_commit']}. |\n| Servidor |{pr}filas;{br}puentes,{sh}orillas, presa y{kp}/{kt}controles obligatorios del kit PASS. Sin regresiónEV110. |\n| G8kit / AND estricto | FAIL por{pc}labios/juntas conocidos de hormigón, pendientes no bloqueantes según plan§5. Ningún umbral relajado.{refs}puntos del kit son referencias sin expect juzgado. |\n| Temporal |{tr}filas;30muestras de8puntos. Cuatro corregidos y controles cumplen en30/30; clima fijo, no prueba jugador ni todos los climas. |\n| Límites heredados |015-45/60m pendiente; OT4central solamente; G8bosque conserva exclusiones estructurales;124traslaciones fuera del recorte de mutaciones; G9juncos y G2/G3regional históricos conservados. |\n| Vista / rendimiento |16archivos instalados, ruta y solicitud de lanzamiento preparadas; cliente no lanzado. Sin vista/FPS/capacidad80–100jugadores. |\n\n"+s[b:]
write(matrix,mat)
inbox=V/'10_Projects/DayZ_Baltic_12km/reviews/codex-review-inbox.md'
write(inbox,lambda s:s+f"\n- {date}, EV112 OT7 R2 y OT8: {R['verdict']}, cero críticos/mayores abiertos. Paquete nuevo con4vértices corregidos; servidor{pr} y temporal{tr} capturados.{kp}controleskit/{sh}orillas/{br}puentes/presa PASS; G8estricto FAIL solo{pc}juntas/labios pendientes porplan§5. Vista instalada sin lanzar,015-45 yFPS pendientes. [Evidencia]({url}). Los estados de no ejecución anteriores son históricos.\n")
estate=V/'10_Projects/_estado-proyectos.md'
def es(s):
 a=s.index('## DayZ_Baltic_12km —');b=s.index('**Ampliación18-10',a)
 return s[:a]+f"## DayZ_Baltic_12km — EV112: servidor completado, vista preparada, {date}\n\n{summary} OT7 R2 {R['verdict']}; fuente {R['source_commit']}, sin push.015-45/60m yFPS pendientes. [Evidencia]({url}) · [sesión](../30_Sessions/2026-10-18-dayz-baltic-ev112-ot1-execution.md).\n\n"+s[b:]
write(estate,es)
(B/'manifest.json').write_text(json.dumps(dict(time=stamp,changes=changes),indent=2)+'\n');print('Updated',len(changes),'scoped files; preserved backups and foreign content.')
