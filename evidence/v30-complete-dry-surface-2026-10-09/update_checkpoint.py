from pathlib import Path
import hashlib, json, shutil

B = Path(__file__).parent
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
deploy = json.loads((B / 'deploy.json').read_text())
gate = json.loads((B / 'offline-gate.json').read_text())
mips = json.loads((B / 'changed-mips.json').read_text())
assert gate['status'] == 'OFFLINE_PASS_NATIVE_PENDING'
world = deploy['files']['narva_trial.pbo']
p = W / 'HANDOFF.md'
text = p.read_text()
start, end = text.index('<!-- LIVE-STATE:START -->'), text.index('<!-- LIVE-STATE:END -->')
live = text[start:end]
changes = {
    'status': 'BASE_1_0_NO_ACEPTADA. EV61 es la última geometría comprobada en motor. EV72 reúne terreno EV70/71 y superficie completa actualizada; fuente/compilado PASS, motor pendiente. EV68 sigue propuesta separada, sin promoción.',
    'smoothing': 'EV70/71 elevan y suavizan 27996 vértices respecto de EV61, +0.4 m acumulado máximo. EV71 completa164 objetivos restantes, energía angular incidente -15.98%, pliegues >30:89->50. p99 banco global16.70260->16.69000. EV70 conserva49 sectores con aumentos locales yEV71 cuatro. No aceptación artística ni cierre de contornos mojados.',
    'global_detection': 'EV71 censo8380418 caras:408 zonas>=1m2/726892.25m2 frente428/795569.19EV61; índice geométrico, no defectos confirmados. Consumidor91937 caras analíticas+320GEOS+423puntos PASS. ListaEV59 completa:2615/2760 a cota,145 protegidos (59lagos/91borde/5comunes),0 editables pendientes. CSV y replay exactos.',
    'runtime_lock': 'Sin run ni lease propios nuevos trasEV64 cerrado orderly. A2026-10-09 19:33:23UTC el catálogo628tools incluye0dayz-mcp aunque la UI dice conectado. Ocupación actual desconocida. Sin bypass, reinicio de daemon ni CUA.',
    'surface': f'EV72:1024teselas sobreEV71,150847524px/3968solapesPASS. Cambian{deploy["changed_satellites"]}satélites+{deploy["changed_masks"]}máscaras frenteEV67;{mips["changed_mips"]}mips nuevosPASS. Agua y objetos exactosEV61,WRPd3924a80. Mod@DayZ_Baltic_BaseSurfacePreviewV1 mundo{world}. Runtime pendiente.',
    'remaining': 'EV72 lectura nativa/vistas;007/020 contornos y aspectoMsta/Volkhov;016shader sin causa cerrada;018propuestaEV68 motor/excepción647/651 y grupos protegidos;017grandeslagos y145bajos protegidos;01545cruces de reserva;019streaming;014TerrainBuilder->navmesh/IA. No aceptar toda la base por gates offline.',
    'git': 'Branch claude/codex-handoff-review-74f290. Checkpoint anteriorc688ebc; loteEV71/72 preservado. Sin push ni subagentes.',
    'next': f'Recuperar catálogoMCP en un turno nuevo; no repetir reinicios externos. Rehash y probar primero@DayZ_Baltic_BaseSurfacePreviewV1 mundo{world[:8]}, misiónBalticBaseSurfaceFullWaterV1.BalticTrial,4194304vértices/1212puntos/1205planos. Después vistas cargadas puente/Msta/Volkhov/distancias yEV68separado. No promociónEV68 sin excepción647/651. Mantenerlease/lifecycle del runbook.',
    'handoff': 'EvidenciaEV71/72 ymanifest propio en evidence/v30-complete-dry-surface-2026-10-09/README.md. Manifest previoEV67-70 exacto enlazado. EV71 capa replay byte-exacta desdeEV70; P/F/objetos exactos,500objetos compilados sin cambio de exposición,404484celdas cubiertas. Misión instalada/lint1archivo sin errores,NOejecutada. Seguir objetivo completo.'
}
for key, value in changes.items():
    rows = [line for line in live.splitlines() if line.startswith(key + ':')]
    assert len(rows) == 1, key
    live = live.replace(rows[0], key + ': ' + value)
new = text[:start] + live + text[end:]
assert new.split('<!-- LIVE-STATE:END -->', 1)[1] == text.split('<!-- LIVE-STATE:END -->', 1)[1]
p.write_text(new)

p = W / 'bugs.md'
with p.open(newline='') as f:
    text = f.read()
header = '> Actualización EV71/72 (09-10): preparada superficie completa sobre terreno corregido; 2615/2760 puntos de la lista de bajos a cota,145 protegidos y0 editables pendientes.1024teselas/3968solapes y mipmaps nuevos PASS. Motor pendiente: Codex no publica herramientasdayz-mcp. No cierre del residual ni base1.0. Evidencia: `evidence/v30-complete-dry-surface-2026-10-09/README.md`.\n\n'
assert not text.startswith(header)
with p.open('w', newline='') as f:
    f.write(header + text)

p = W / 'evidence/v30-global-water-risk-2026-10-09/bug-status-current.md'
text = p.read_text().replace('vigente hasta EV70', 'vigente hasta EV72')
rows = text.splitlines()
updates = {
    '007': '| 007 | EV70/71:27996 vértices secos ajustados respecto deEV61; fuente y compiladoPASS. Última pasada p99banco16.70260->16.69000, pliegues incidentes>30:89->50. | EV72sinmotor. Regresiones localesEV70/71 inventariadas. Contornos mojados, grandes lagos y aceptación artística abiertos. |',
    '009': '| 009 | EV71 cobertura compilada completa404484celdas:0hueco físico, residuo visible3.8464e-12m2.500objetos afectados sin cambio de exposición. | Lectura nativaEV72pendiente. EV64atribuyó cinco flags ausentes a objetos de puente; controles fluviales exactos. No cierre de oleaje/render por geometría. |',
    '010': f'| 010 | EV72:1024teselas sobreEV71,150847524px y3968solapesPASS;{deploy["changed_satellites"]}satélites+{deploy["changed_masks"]}máscaras cambiados y{mips["changed_mips"]}mips nuevosPASS. | Vistas sobreEV72, aceptación final yTerrainBuilder pendientes.4323mezclasDXT de borde inventariadas. |',
    '016': '| 016 | EV54mejora local puente. EV70/71 completan bajos editables:2615/2760puntos a1.8m,145protegidos y0editables pendientes. Censo completo408zonas/726892m2. | MotorEV72pendiente; índice geométrico no equivale a408fallos. Shader sin identificar. No elevar automáticamente145protegidos. |',
    '019': f'| 019 | EV30 audita todos16384mips por paqueteEV25/28; EV67yEV72 verifican cambios posteriores. EV72decodifica{mips["changed_mips"]}mips nuevos con controles nativos y negativo de truncación. | Streaming sin mecanismo cerrado. Ticket de foco existente fb-20261008-233507-8b1c. La UI MCP conectada sin tools es un bloqueo de entorno distinto. |'
}
for key, value in updates.items():
    indices = [i for i, row in enumerate(rows) if row.startswith('| ' + key + ' |')]
    assert len(indices) == 1, key
    rows[indices[0]] = value
p.write_text('\n'.join(rows) + '\n\nEV71/72: `../v30-complete-dry-surface-2026-10-09/README.md`. Primera prueba pendiente: BaseSurfacePreviewV1, mundo' + world[:8] + '. SustituyeEV70como siguiente candidato de prueba; EV61conserva la última validación nativa. Ningún nuevo run ni cierre global de20IDs.\n')

session = Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md')
heading = '## EV71/72 — terreno seco y superficie completa preparados'
assert heading not in session.read_text()
with session.open('a') as f:
    f.write('\n\n' + heading + '\n\nEV71completa164objetivos,5202vértices adicionales;27996respectoEV61con+0.4m acumulado máximo. ListaEV59:2615a cota,145protegidos,0editables pendientes. Replay byte-exacto;500objetos compilados sin cambio de exposición;404484celdas de coberturaPASS. Índice408zonas/726892m2, no defectos confirmados.\n\nEV72regenera1024teselas/150847524px,3968solapesPASS. ' + str(deploy['changed_satellites']) + 'satélites+' + str(deploy['changed_masks']) + 'máscaras y' + str(mips['changed_mips']) + 'mips nuevosPASS. BaseSurfacePreviewV1 mundo' + world + ',terrenob54963eb,agua3946db8b. MisiónBalticBaseSurfaceFullWaterV1instalada1212puntos/1205planos,4194304vértices,lint1archivo0errores,NOejecutada.\n\nCatálogo de628tools sin dayz-mcp aunque UI conectada; no run/lease nuevo,bypass,CUA,subagentes ni push. EV61último nativo;EV68sigue propuesta separada con excepción647/651pendiente. Reflejos,contornos,grandeslagos,45cruces,streaming,TB->navmesh/IA abiertos. Estado/fuente: W/evidence/v30-complete-dry-surface-2026-10-09/README.md yHANDOFF. Objetivo completo incompleto; no base1.0 aceptada.\n')

dest = W / 'evidence/v30-complete-dry-surface-2026-10-09'
out = dest / Path(__file__).name
shutil.copyfile(Path(__file__), out)
mp = dest / 'evidence-manifest.json'
manifest = json.loads(mp.read_text())
manifest['files'] = [row for row in manifest['files'] if row['path'] != out.relative_to(W).as_posix()]
manifest['files'].append(dict(evidence=72, path=out.relative_to(W).as_posix(), sha256=sha(out), bytes=out.stat().st_size))
assert all(sha(W / row['path']) == row['sha256'] for row in manifest['files'])
mp.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(dict(status='CHECKPOINT_UPDATED_NOT_COMPLETE', manifest_files=len(manifest['files'])), indent=2))
