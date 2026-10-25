from pathlib import Path
import hashlib
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-water-cause-investigation-2026-10-10'
overview='''# EV75/76 — investigación localizada de los rectángulos de agua

Las dos revisiones Luna pedidas por Guillermo localizan el defecto y eliminan comparaciones inválidas; no reparan todavía el render. La base sigue EV72/73, mundo a08b96a1, agua3946db8b, terreno b54963eb. No se promueve EV68 ni ningún terreno rechazado.

## Hechos contrastados

- Dos transiciones visibles de la captura EV73 `233431_541` coinciden con bordes de objetos globalvis: par16812770/71,145px de solape con0.44–0.46px de offset; par16812805/15,45.28px de46 con1.75–1.79px. Son trazas visuales aproximadas, no límites de cajas ROI.
- Los cuatro ODOL comparten material CalmWater, normalmap y flags de alpha/visibilidad. Geometría y radios difieren. Lectura `scan_fallback`, sin errores de LOD: no convertir metadatos interpretados en prueba del mecanismo de render.
- EV76 lee proyección nativa en EV72 sin alterar mapa: focal654.545476px,8puntos retenidos con error máximo0.000073px. ROI gris345/345rayos atraviesan P/F por delante del terreno; terreno bajoF −4.445…−1.699m. El control ondulado378/378 también está bajo el mar. Por tanto, el lecho profundo es un factor compartido, no una clasificación del gris.
- La ROI gris toca reserva vial en20.3% de caras muestreadas. El eje óptico no era una localización válida del parche: está fuera de la ROI gris seleccionada.
- EV73 nativo confirma SeaMin0.65/SeaMax0.85. El censo global localiza120componentes interiores candidatos y548195.87m² de coincidencia a nivel máximo. Es índice geométrico, no120fallos gráficos; los gates secos EV72 no autorizan ni prohíben por sí solos reparar agua.
- El control histórico Peipus05-10 mejoró al elevar fondo manteniendo agua/material; no prueba universal ni mecanismo del Narva actual.

## Rechazos y límites

EV75 directo14c6b0b2 falló calado/pendientes; correcciónc0e0c206 conserva huella y mínimo0.952835m en4872caras afectadas, pero falla corte estricto de pendiente y objetivo del eje. Ambos permanecen fuera del juego; no se relajó el consumidor ni se redefinió retrospectivamente PASS.52caras tocaban reserva aunque sus vértices cambiados no. Ver rejected-narva/README.md.

El primer análisis DDA de EV76 con cero hits era incorrecto y queda invalidado. `projection/roi-world.json` final usa paso4 y `visible-field.npy` real; roundtrip nativo y celda óptica pasan. La captura EV76 es magenta y no sirve para aceptación visual: la calibración se transfiere a EV73 por pose/FOV/viewport iguales, con ese límite explícito.

Se rechaza el swap de modelos propuesto inicialmente por Luna: huellas distintas cambiarían P/F y exposición. La siguiente unidad EV77 observa una sola pose en wireframe para distinguir categorías visibles Water/Ocean/OceanShore; no vuelve a barrer opciones ni cambia el mapa. Ausencia de arista no prueba ausencia de capa, y presencia no atribuye composición del pixel normal.

## Evidencia y estado

`preservation.json` registra55archivos copiados con hash/bytes: scripts, informes, capturas y dos notas Luna. Terrenos NPZ rechazados permanecen en E:/DayZ-Baltic-Build, identificados por hash; no se empaquetaron. EV76 run3b4a4a81 cerrado orderly y lease liberado. EV77 está en preparación/ejecución en E:/DayZ-Baltic-Build/v30-water-wire-classification-20261010; consultar LIVE-STATE antes de usar DayZ. La base completa sigue abierta.
'''
(E/'README.md').write_text(overview,encoding='utf-8');assert (E/'README.md').read_text(encoding='utf-8')==overview
p=W/'HANDOFF.md'
with p.open(encoding='utf-8',newline='') as f:s=f.read()
a=s.index('<!-- LIVE-STATE:START -->');b=s.index('<!-- LIVE-STATE:END -->')
block=s[a:b];lines=block.splitlines(keepends=True)
updates={
'updated':'2026-10-10',
'render':'EV73/74 reproduce rectángulos; medio/extremo/medio no los elimina. Dos Luna localizan dos cortes en bordes globalvis16812770/71 y16812805/15, mismos materiales/flags. EV76 ROI gris345/345 y controlondulado378/378 bajo mar: factor compartido, no causa suficiente. Proyección nativa focal654.545476px, error retenido0.000073px. EV75 dos terrenos rechazados sin despliegue. Swap de modelos rechazado por cambiar huellas. EV77 un diagnóstico wire en curso, mapa intacto; no barrido gráfico.',
'runtime_lock':'EV76 run3b4a4a81 cerrado orderly y lease liberado. EV77 run16638541-9244-485c-81fe-67aa6fe4a143 ACTIVO, cliente94292/servidor163944, lease owner de esta sesión. Cámara [2417,65,6745], nativaFOV1.1/1920x1080. ProbeV2 READY131/276 y fase0, mapa exacto. Primera vista magenta y sin materiales: foco manual solicitado, comparación wire aún NO ejecutada. Mantener heartbeat; no lanzar otro run.',
'git':'Branch claude/codex-handoff-review-74f290. HEAD0f0c0e8. EV73/74, MCP y EV75/76+dos Luna preservados; checkpoint pendiente. Sin push.',
'next':'EV77 esperando foco manual para referencia normal válida; luego wire1/wire-only2/restauración0, máximo un run. PBOprobe48e28ceb, mapaEV72 intacto. Comparar aristas Water/Ocean con proyección real. No inferir causa por ausencia. Después cierre orderly+release+session_status y continuar reparación concreta y resto del plan; no promover EV68.',
'handoff':'Nueva evidencia evidence/v30-water-cause-investigation-2026-10-10, v30-base-surface-runtime-2026-10-09, v30-water-rectangles-detail-2026-10-09 y mcp-codex-provenance-2026-10-09. EV77 en E:/DayZ-Baltic-Build/v30-water-wire-classification-20261010; comparación pendiente. Revisiones Luna completadas; no corrigen el render. Objetivo completo abierto.'}
for i,line in enumerate(lines):
    key=line.split(':',1)[0]
    if key in updates:lines[i]=key+': '+updates[key]+('\r\n' if line.endswith('\r\n') else '\n')
new=s[:a]+''.join(lines)+s[b:]
with p.open('w',encoding='utf-8',newline='') as f:f.write(new)
with p.open(encoding='utf-8',newline='') as f:assert f.read()==new
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md')
with session.open('a',encoding='utf-8') as f:f.write('\n\n## EV75/76 — localización y revisión Luna\n\nDos propuestasEV75 rechazadas antes de empaquetar: no bajaron los gates. EV76 proyección nativa focal654.545476px, error retenido0.000073px; imagen magenta inválida para render, lectura numérica válida y run cerrado orderly. Dos Luna sitúan las transiciones en pares globalvis16812770/71 y16812805/15, materiales/flags iguales. ROIgris345/345bajo mar, controlondulado378/378también: factor compartido, no causa suficiente. Swap sugerido descartado por huellas distintas. Evidencia55archivos copiados conhash a W/evidence/v30-water-cause-investigation-2026-10-10. EV77 diagnóstico único wire iniciado16638541, mapa intacto; primera vista inválida, foco manual pendiente, lease activo. Ver HANDOFF antes de gestionar juego. No arreglo ni cierre base1.0 ni push.\n')
print('Updated overview, LIVE-STATE and session note. No product geometry changed.')
