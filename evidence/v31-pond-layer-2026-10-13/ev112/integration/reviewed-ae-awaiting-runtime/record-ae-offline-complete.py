"""Record observed holdout completion, exact promotion and deployed offline candidate."""
from pathlib import Path
from datetime import datetime
import hashlib,json
O=Path(__file__).parent
P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
read=lambda name:json.loads((O/name).read_text())
hold=read('forest-holdout-ae-steps.json')['steps']
assert len(hold)==50 and all(v['rc']==0 for v in hold)
assert {v['seed'] for v in hold}==set(range(181,191))
assert all(sum(v['seed']==s for v in hold)==5 for s in range(181,191))
closure=read('forest-review-closure-ae.json');deploy=read('deploy.json')
assert closure['verdict']=='MECHANICAL_PASS' and closure['independent_build_review']=='PENDING'
assert deploy['forest_tag']=='ae' and deploy['offline_status']=='PASS'
route=read('personal-view-ae/route.json')
assert route['package_binding']['world_sha256']==deploy['world_sha256']
assert (O/'review-build-ae-r1-binding.json').is_file()
h=P/'HANDOFF.md';old=h.read_bytes();s=old.decode()
a=s.index('<!-- LIVE-STATE:START -->');b=s.index('<!-- LIVE-STATE:END -->',a)
assert b-a<15000
print('Previous LIVE-STATE span:\n'+s[a:b])
lines=s[a:b].splitlines()
updates={
 'status:':'status: BASE 1.0 NO ACEPTADA. EV112 offline completo: AE45 etapas conocidas y50/50 nuevas(181–190) PASS. Fuentes exactas promovidas y dosPBO desplegados. OT7 independiente ronda1/2 lanzada; falta veredicto y sonda. Vista personal preparada, no aceptada.',
 'blocker:':'blocker: Esperar veredicto real OT7 sobre el paquete desplegado y el delta posterior a S. Luego instalar misiones con lease/caja libre y ejecutar sonda. Ultima lectura MCP encontro procesos ajenos; refrescar antes de mutar, sin tocarlos.015-45 protegido60m PENDIENTE.',
 'validation:':'validation: AE PBO '+deploy['world_sha256']+',2.561.015 registros y2.578.916 objetos compilados.45 etapas conocidas+50 nuevas PASS;6 positivos emparejados/25 mutaciones detectadas;7 planos inspeccionados. Lectura WRP y superficie final PASS. Dos fallos originales del arnes y alcance124 traslaciones fuera del recorte de controles preservados. Sin aprobacion visual/FPS.',
 'cleanup:':'cleanup: 94408 termino0, HOLDOUT PASS50(terminacion observada2d4301). Promocion/despliegue/vista/preparacionOT7 terminaron0.89990: run-review-build-ae-r1.py lanzado; revisar salida real. Sin lease/runDayZ propios ni cambios en misiones vivas.',
 'next:':'next: Esperar89990; leer review-build-ae-r1.json/run.json/binding.json y resolver hallazgos dentro de OT7 max2rondas. Solo con cierre independiente0mayores: MCPstatus fresco, lease con caja libre, install-ev112-missions.py ae, liberar, dayz_test_run servidor, adquirir, esperarEND4114, capturar antes de cerrar, cerrar/liberar/status y evaluar. Despues archivar/commit/handoff; no lanzarcliente.',
 'git:':'git: Worktree handoff-astra-map-review-6d301c, rama claude/handoff-astra-map-review-6d301c; ultimo commit234f8e8. Sin push. BosqueAE0fef87ee... y helper promovidos; clearings400m2 y patch_surface pendientes de commit con evidencia final. Cambios ajenos del checkout principal preservados.'}
for key,value in updates.items():
 ids=[i for i,line in enumerate(lines) if line.startswith(key)];assert len(ids)==1
 lines[ids[0]]=value
new=(s[:a]+'\n'.join(lines)+'\n'+s[b:]).encode();assert len(new)>=.9*len(old)
backup=O/'ae-offline-complete-handoff-before.md';assert not backup.exists();backup.write_bytes(old)
assert h.read_bytes()==old;h.write_bytes(new);assert h.read_bytes()==new
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-18-dayz-baltic-ev112-ot1-execution.md')
previous=session.read_bytes();backup=O/'ae-offline-complete-session-before.md';assert not backup.exists();backup.write_bytes(previous)
entry=f'''\n### Cierre offline AE {datetime.now().astimezone().isoformat(timespec='minutes')} y OT7 lanzada\n\nEl proceso94408 termino con exit0 (respuesta2d4301). `forest-holdout-ae.log` termina HOLDOUT PASS50; las semillas181–190 completaron sus50etapas originales, todasrc0. No hubo sustitucion ni cambio de fuentes, bandas o entradas.\n\n`close-forest-offline-ae.py ae`, `deploy-verified-ev112.py ae`, `bind-personal-view-final.py ae` y `prepare-final-build-review.py` terminaron0. Cierre mecanico y promocion exacta en `forest-review-closure-ae.json`; copia verificada de los dosPBO en `{deploy['mod']}`. MundoSHA{deploy['world_sha256']}; aguaSHA{deploy['water_sha256']}. Vista personal vinculada al paquete con16archivos, no instalada ni ejecutada.\n\nOT7 independiente ronda1de2 lanzada con `run-review-build-ae-r1.py`, proceso de herramienta89990. Leer el resultado real antes de aceptar; no equivale a una tercera ronda de la fuenteS. El prompt declara todo el delta S→AE, ambos fallos originales del arnes, controles16regionales/9globales,124traslaciones fuera del pool de mutaciones y3filas diagnosticas de juncos deG9.\n\nLa lectura previa de MCP encontro caja ocupada por procesos ajenos (@DayZ_MCP/@LFDeathRagdoll, perfiles130). No lease/run propios ni mutacion de mision. Refrescar disponibilidad despues de OT7, sin cerrar ni adoptar esos procesos. Faltan sonda real, archivo/commit y cierre documental.015-45/60m permanece pendiente; tampoco hay aprobacion visual oFPS.\n'''
assert session.read_bytes()==previous;session.write_bytes(previous+entry.encode());assert session.read_bytes()==previous+entry.encode()
print('Offline completion recorded; independent OT7 and runtime pending')
