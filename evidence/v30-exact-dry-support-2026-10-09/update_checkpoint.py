from pathlib import Path
import json,shutil,hashlib
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
p=W/'HANDOFF.md';text=p.read_text();start=text.index('<!-- LIVE-STATE:START -->');end=text.index('<!-- LIVE-STATE:END -->');live=text[start:end];assert end-start<10000
changes={
'status':'BASE_1_0_NO_ACEPTADA. EV61 es la ultima geometria comprobada en motor. EV67 superficie, EV68 Volkhov y EV70 bajos secos estan desplegados para prueba; fuente/compilado PASS, motor pendiente. No promocionar aun.',
'smoothing':'EV55/57 Msta/Volkhov y EV61 15dominios conservados. EV70 repara el cierre rectangular que bloqueaba vertices completamente secos: 2197objetivos a1.8m,23257vertices modificados,+0.4m max; energia angular incidente-16.10%, pliegues>30:163->92. p99banco16.71823->16.70260. 49/104sectores con aumento local inventariados. No aceptacion artistica.',
'global_detection':'EV70 censo8380418caras:413zonas>=1m2/731109.38m2 frente428/795569.19EV61; indice geometrico, no defectos confirmados. 92349caras analiticas+320GEOS+428puntos PASS. 2197objetivosEV60 restantes resueltos en fuente;309del dominioEV59 aun bajos, CSV exacto. EV70sinmotor.',
'remaining':'EV70 lectura nativa/vistas y309bajos secosEV59;007/020contornos y aspectoMsta/Volkhov;010texturas finales/TB;016shader sin causa cerrada;018propuestaEV68 pendiente motor/excepcion647/651 y grupos protegidos;01545cruces de reserva;017grandeslagos reservados;019streaming;014TB->navmesh/IA.',
'git':'Branch claude/codex-handoff-review-74f290. Checkpoint anterior1053910; este lote preservaEV67-70. Sin push ni subagentes.',
'next':'Recuperar tools MCP en un turno nuevo: este chat no las recibe aunque la UI dice conectado. Rehash y probar primero EV70 ExactDrySupportV1 mundo1853ff49; misionBalticExactDrySupportFullWaterV1,4194304vertices/1212puntos/1205planos. Despues vistasEV67 y comparacionEV68Volkhov(554db04d,2173puntos/2166planos). No promocionarEV68 sin excepcion647/651. FuenteEV70: evidence/v30-exact-dry-support-2026-10-09/README.md.',
'handoff':'EV67-70, manifest101archivos antes de este actualizador en evidence/v30-volkhov-float-consistent-2026-10-09/evidence-manifest.json. EV70capa terrain-delta replaybyte-exacto desdeEV61; P/F/objetos exactos, exposicioncompilada342objetos sin cambio y cobertura404484celdasPASS. Misionlista,noejecutada. Baseincompleta;seguir objetivoentero.'
}
for key,val in changes.items():
    lines=[s for s in live.splitlines() if s.startswith(key+':')];assert len(lines)==1;live=live.replace(lines[0],key+': '+val)
new=text[:start]+live+text[end:];assert len(new)>=len(text)*.9 and new.split('<!-- LIVE-STATE:END -->',1)[1]==text.split('<!-- LIVE-STATE:END -->',1)[1];p.write_text(new)
p=W/'bugs.md'
with p.open(newline='') as f:text=f.read()
head='> Actualización EV70 (09-10): candidato ExactDrySupportV1 resuelve2197 objetivos secos y reduce16,1% la energía angular incidente. Fuente y cobertura/exposición compiladas PASS; motor pendiente porque el chat no recibe tools MCP.309 bajos elegibles anteriores quedan inventariados. No cierre del shader ni base1.0. Evidencia: `evidence/v30-exact-dry-support-2026-10-09/README.md`.\n\n'
with p.open('w',newline='') as f:f.write(head+text)
p=W/'evidence/v30-global-water-risk-2026-10-09/bug-status-current.md';text=p.read_text().replace('vigente hasta EV69','vigente hasta EV70');lines=text.splitlines()
for i,line in enumerate(lines):
    if line.startswith('| 016 |'):lines[i]='| 016 | EV54 mejora local puente; EV61 resuelve96objetivos. EV70 resuelve2197objetivos mas en fuente y pasa geometria/compilado; energia angular incidente-16.1%, agua compilada exacta. | MotorEV70 pendiente;309bajos del dominioEV59 restantes. Indice413zonas/731109m2, no413defectos. Shader sin identificar. |'
    if line.startswith('| 007 |'):lines[i]='| 007 | EV53/55/57 orillas locales y EV61 comprobados. EV70 23257vertices secos: p99banco16.71823->16.70260,pliegues>30incidentes163->92;fuente/compiladoPASS. | EV70sinmotor;49sectores con aumento local inventariados. Contornosglobales ygrandeslagos abiertos; no aceptacion artistica. |'
text='\n'.join(lines)+'\n';text+='\nEV70: `../v30-exact-dry-support-2026-10-09/README.md`. Preparado ExactDrySupportV1 mundo1853ff49; mantieneP/F/objetosEV61. Prioridad: lectura nativa y vistas con catalogo MCP restablecido. Ningun nuevo run propio.\n';p.write_text(text)
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md')
addition='\n\n## EV70 — avance posterior al diagnósticoEV69\n\nEl cierre rectangular protegia18 vecinos secos entre27 de nueve aristas. Sustituido por cierre exacto de todos los triangulos mojados, manteniendo otras protecciones, una ejecucion60barridos.2197objetivos a1.8m,23257vertices;energiaangular-16.1%,p99banco16.71823->16.70260;49sectores con aumento local inventariados.342objetos compilados sin cambio de huella expuesta;auditoria404484celdas completaPASS. Indice413zonas/731109m2, nofallosconfirmados.309objetivosEV59 siguen bajos y listados.\n\nDesplegado ExactDrySupportV1 mundo1853ff49,terreno682d5553,agua3946db8b;P/F/objetosEV61exactos. MisionBalticExactDrySupportFullWaterV1 validada1212puntos/1205planos y4194304vertices, noejecutada. Sin toolsMCP publicadas aun, sinrun/lease nuevos. EV61 mantiene validacion nativa vigente; EV67/68/70 preparados, ninguna base1.0 aceptada. Continuar primeroEV70motor, luegoEV67vistas yEV68Volkhov/excepcion,309bajos restantes,lagos/cruces/TB/navmesh. Evidencia W/evidence/v30-exact-dry-support-2026-10-09/README.md.\n'
assert '## EV70 —' not in session.read_text()
with session.open('a') as f:f.write(addition)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dest=W/'evidence/v30-exact-dry-support-2026-10-09/update_checkpoint.py';shutil.copyfile(Path(__file__),dest)
mp=W/'evidence/v30-volkhov-float-consistent-2026-10-09/evidence-manifest.json';m=json.loads(mp.read_text());m.append(dict(evidence=70,path=dest.relative_to(W).as_posix(),sha256=sha(dest),bytes=dest.stat().st_size));mp.write_text(json.dumps(m,indent=2)+'\n');assert all(sha(W/v['path'])==v['sha256'] for v in m)
print(json.dumps(dict(status='UPDATED_EV70_NOT_COMPLETE',manifest_files=len(m)),indent=2))
