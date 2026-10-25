from pathlib import Path
import json,hashlib,shutil
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
R=Path('E:/DayZ-Baltic-Build')
p=W/'HANDOFF.md';text=p.read_text()
start=text.index('<!-- LIVE-STATE:START -->');end=text.index('<!-- LIVE-STATE:END -->');live=text[start:end]
updates={
'status':'BASE_1_0_NO_ACEPTADA. EV61 geometria vigente; EV67 superficie completa PASS offline/desplegada, vistas pendientes. EV68 propuesta Volkhov PASS geometria/compilado, pendiente motor y excepcion647/651. Continuar objetivo completo.',
'runtime_lock':'Sin run ni lease propios nuevos tras EV64 cerrado orderly. MCP: Transport closed; despues de reabrir en Codex, ninguna herramienta dayz-mcp publicada aunque la UI informa conectado. Ocupacion actual no verificada; no bypass, no daemon restart ni CUA.',
'git':'Branch claude/codex-handoff-review-74f290. Checkpoint anterior1053910 EV62-66; este lote incorpora EV67/68 y diagnosticoEV69. Sin push ni subagentes.',
'next':'Recuperar publicacion de tools MCP de este chat. EV67 SurfaceAlignedV2 mundo37f42c8e: vistas Nazia/Msta/Volkhov. EV68 VolkhovBedProposalV1 mundo554db04d: misionBalticVolkhovBedFullWaterV1,4194304vertices/2173puntos,2166planos. Hashes antes de lanzar; no promocionar sin motor/excepcion647/651. Despues contornos/bajos/cruces/lagos/TB.',
'handoff':'EV67/68 en evidence/v30-volkhov-float-consistent-2026-10-09/README.md y manifest. EV68 corrige precision numerica deEV66 sin cambiar consumidor:6gruposconvergen,5.32894e-5gradosresidual<1e-4. Cobertura global yexposicion deagua compiladaPASS. Capa replaybyte-exacta desdeEV61. Base incompleta;seguirautonomamente.',
}
for key,value in updates.items():
    old=[line for line in live.splitlines() if line.startswith(key+':')];assert len(old)==1,key
    live=live.replace(old[0],key+': '+value)
surface='surface: EV67 regenera1024teselas sobreEV61:150847524px/3968solapesPASS,14satelites+11mascarasPAAcambian,200mipsnuevosPASS. GeometriaEV61exacta,6802otrasentradasPBOexactas; runtimependiente. E:/DayZ-Baltic-Build/v30-surface-aligned-20261009.\n'
assert 'surface:' not in live;live=live.replace('editor:',surface+'editor:')
p.write_text(text[:start]+live+text[end:]);assert '<!-- LIVE-STATE:END -->' in p.read_text()

p=W/'bugs.md'
with p.open(newline='') as f:text=f.read()
prefix='> Actualización EV67–68 (09-10): superficie completa verificada y desplegada para prueba; propuesta Volkhov pasa geometría y compilado. Lectura nativa y vistas pendientes por falta de herramientas MCP publicadas; no cierre gráfico ni promoción de la excepción647/651. Evidencia: `evidence/v30-volkhov-float-consistent-2026-10-09/README.md`.\n\n'
with p.open('w',newline='') as f:f.write(prefix+text)
p=W/'evidence/v30-global-water-risk-2026-10-09/bug-status-current.md';text=p.read_text().replace('vigente hasta EV66','vigente hasta EV69')
lines=text.splitlines()
for i,line in enumerate(lines):
    if line.startswith('| 010 |'):lines[i]='| 010 | EV67 actualiza las1024teselas sobreEV61:150847524px y3968solapesPASS;25PAA cambiados y200mips completosPASS;6802entradas restantes exactas. | Vistas sobreEV67 y aceptación final/TB pendientes.4323mezclas DXT de borde inventariadas. |'
    if line.startswith('| 018 |'):lines[i]='| 018 | EV54 corrige41de70masas bajas, lectura1205planosPASS. EV68 Volkhov: fondo1.01042m y profundidades/huellas conservadas; fuente y compiladoPASS,109objetos trasladados42.5cm. | EV68 pendiente lectura nativa/vistas y excepción647/651; no promovido. Msta comparte gran lago reservado. Bajos/Narva no cerrados globalmente. |'
text='\n'.join(lines)+'\n'
text=text.replace('EV67 regenera la superficie completa sobre EV61; en curso, sin nueva aceptación.','EV67 completa superficie offline; EV68 geometría/compilado PASS y listo para motor. Ver `../v30-volkhov-float-consistent-2026-10-09/README.md`. La UI MCP dice conectado pero el catálogo del chat no publica tools; no se ha lanzado el runtime nuevo.')
text=text.replace('Banco libre trascierreorderly.','EV64 cerró orderly; ocupación actual desconocida con MCP no disponible.')
p.write_text(text)

session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md')
addition='\n\n## Continuación EV67–69\n\nEV67 superficie completa sobreEV61:1024teselas/150847524px/3968solapesPASS;25PAA nuevos/200mipsPASS; mundo37f42c8e. EV68 Volkhov corrige incompatibilidad de precisión deEV66, consumidor idéntico:6grupos convergen26iteraciones; fondo1.01042m, profundidad/huella conservadas, cobertura404484celdas y exposición115objetos compiladosPASS. Mundo554db04d; terreno1fc4fe26; agua3946db8b. Propuesta preparada, no promovida; excepción647/651 y motor pendientes. Capa replay byte-exacta desdeEV61. Misión4194304vertices/2173puntos(2166planos) validada y no ejecutada.\n\nTras reinicio externo y reapertura de MCP en Codex, el catálogo de este chat pierde sus herramientas DayZ aunque la UI informa conectado. No run ni lease nuevos; no afirmar banco libre actual. Sin bypass/daemon restart/CUA/subagentes/push. Objetivo completo sigue activo e incompleto. EV69 diagnóstico de restricciones de bajos secos, sin nuevo terreno. Fuente vigente: W/evidence/v30-volkhov-float-consistent-2026-10-09/README.md.\n'
assert '## Continuación EV67–69' not in session.read_text()
with session.open('a') as f:f.write(addition)

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest_path=W/'evidence/v30-volkhov-float-consistent-2026-10-09/evidence-manifest.json'
manifest=json.loads(manifest_path.read_text());owned={v['path'] for v in manifest}
for ev,folder in [(67,'v30-surface-aligned-2026-10-09'),(68,'v30-volkhov-float-consistent-2026-10-09')]:
    p=W/'evidence'/folder/'README.md';rel=p.relative_to(W).as_posix();assert rel not in owned
    manifest.append(dict(evidence=ev,path=rel,sha256=sha(p),bytes=p.stat().st_size))
src=Path(__file__);dest=W/'evidence/v30-volkhov-float-consistent-2026-10-09'/src.name;shutil.copyfile(src,dest)
manifest.append(dict(evidence=68,path=dest.relative_to(W).as_posix(),sha256=sha(dest),bytes=dest.stat().st_size))
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
assert all(sha(W/v['path'])==v['sha256'] for v in manifest)
print(json.dumps(dict(status='LIVE_STATE_UPDATED_NOT_COMPLETE',manifest_files=len(manifest)),indent=2))
