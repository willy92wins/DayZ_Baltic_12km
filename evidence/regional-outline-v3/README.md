# Región V3 — relieve, outline y navegación

30-09-2026. Plan: `plans/regional-outline-execution.md`; distribución:
`plans/outline-regional-v3.md`. Base0.2 fd2c7023 preservada. El estado de procesos
vive en HANDOFF.md; no se deduce de las fechas de estos resultados.

## Terreno persistido y outline

- Máximo109.5685m,1.672.627 vértices modificados,0 protegidos. Pendientes de
  triángulos afectados<=34.1696°. Verificador positivo y negativos baseline/reserva.
- La primera exportación conservó las alturas antiguas: `native-export-first.json`
  mantiene ese FAIL. Mapframe Rebuild, sin Generate Layers, seguido de guardar,
  cerrar, reabrir y exportar produjo4194304 alturas exactas, materiales y3 objetos.
- WRP nativo9bf50853, compilado0a993128. SAT1M conservado. Estas identidades son
  comunes a las tres variantes de navegación; no se modificó el relieve entre ellas.
- `outline.png` y `derived/outline-v3`:6 áreas y11229 segmentos principales,
  exportados y releídos. SHP en metros TB, GeoJSON geográfico, hashes en manifest.
- Reserva6.04km² de juego protegida: OSM principal+norte y envolvente de diseño.
  No es límite legal ni bosque ya colocado. Capa de biomas prevista en checkpoint.

## Comparación de navmesh

Misma referencia congelada5314d141, mismo WRP,279 puntos,6 rutas cortas, radio3D
 de2m y control negativo sin flags. `prepare_nav_tile25.py` cambia solo tileWidth;
primero recompila la configuración original y exige identidad binaria. Cada
navmesh se generó de nuevo y se empaquetó conservando las6826 entradas restantes.

| Tesela | Bytes NM | Teselas | Puntos válidos | Rutas válidas | Resultado |
|---|---:|---:|---:|---:|---|
|50m|31.310.232|60.025|253/279|2/6|FAIL conservado|
|25m|111.656.712|241.081|276/279|4/6|FAIL conservado|
|12.5m|439.493.936|966.289|279/279|6/6|PASS de muestras y rutas|

Todas las alturas del motor coinciden con el relieve previsto (error máximo
4.996e-7m). Todas las consultas de las tres variantes encuentran navmesh; los
fallos50/25 son de distancia vertical/extremos, no consultas ausentes. No se
eliminaron puntos ni se amplió la tolerancia para obtener el PASS.

Resultado12.5: NM eb0f131e, PBO55d7163c,542.360.979bytes. Generación propia
16d8c4ae; prueba servidor3981e526. Log28e99b1e y
`runtime-nav-tile12p5-v1.json`. El lector empírico comprobó cada cabecera/límite
de tesela y rechazó la dimensión25 incorrecta; no es un decodificador completo
de topología. El mecanismo interno de simplificación sigue sin aislar.

**Alcance del PASS geométrico:** consultas y seis rutas del grafo en puntos
fijados antes del ensayo. La locomoción se comprueba aparte a continuación.
No acredita conectividad de toda la superficie ni capacidad de jugadores.
El candidato permanece separado de0.2.

## Consumidor físico y vistas

En NM50, `runtime-chase-v1.log` tuvo deriva del objetivo humano. V2 corrigió
esa deriva, pero agotó90s durante la subida: `runtime-chase-v2.json` FAIL.
No atribuirlo automáticamente a navmesh o percepción. La primera compilación
V2 falló por GetInputController sobre Man; se conserva fuente fallida y el run
posterior usó Human.Cast. V2 repetido sobre NM12.5 también tuvo TIMEOUT.

V3 aisló el estímulo1→4, mismo resto funcional: completó control/ida/vuelta
pero falló el corredor lateral4m heredado del puente. FAIL retenido en
`runtime-chase-tile12p5-v3.json`. No hay carretera de8m en esta colina: el
contrato estaba midiendo una restricción ajena a locomoción en terreno abierto.

V4 se planificó y congeló antes de ejecutarlo (ref bc4108f8). Exige meta<=4m
en3D, trayectoria<=3×distancia directa, contacto -0.2..0.5m sobre terreno,
salud positiva, continuidad<=1s, objetivo estable y90s por etapa. Es un nuevo
ensayo; no reclasifica V3. Registra lateral, sin imponer un eje de carretera.

**PASS V4 en juego**, run2a66c02b/log0d0481e2: control+ida+vuelta,746 registros
activos, salud100, objetivo sin deriva. Ida135.08m/84.06s y vuelta115.07m/44.41s,
distancias finales3.71/3.78m. Contacto sobre superficie1.3–43.7mm, mayor hueco
0.207s. No overrides ni teletransporte del infectado después de crearlo.
Se usa ruido de diagnóstico4×; no demuestra percepción normal a larga distancia.
Prueba de una colina, un actor a la vez y un cliente; no navegación regional total.

Ocho controles negativos del verificador pasan en `consumer-v4-controls.json`.
Incluyen objetivo desplazado, actor flotante, llegada falsa, recorrido excesivo
y estado mental inválido. El motor devolvió valores fuera del rango al crear
actores: V4 no los acredita como respuesta y exige lecturas válidas tras1s.

Carga cliente/servidor confirmada con NM50 y NM12.5. Vistas de colina y
reserva observadas en `engine-view-0.png` y `engine-view-2.png`. El log guarda
cuatro poses de cámara, pero no acredita revisión visual de las cuatro.

## Rendimiento y alcance pendiente

La medición inicial `server-perf-with-data-server.json` duró120s sin jugadores,
CE ni IA y no tuvo timeslices>50ms. Tenía data-server y conexión NMG activos:
no usarla como comparación causal con0.2. GetAvgFPS permaneció14.2857; no se
interpreta como rendimiento real del servidor.

Comparación25/12.5 completada: misma misión BalticTerrainPerf,30s de
calentamiento y120s medidos, sin data-server ni cliente. `nav-cost-comparison.json`
y logs originales ligan cada medida a su PID, instante de inicio y paquete.

| Variante | Mediana residente | Mediana privada | CPU/fracción de un núcleo | Máxima timeslice |
|---|---:|---:|---:|---:|
|25m|1444.47MiB|1766.02MiB|0.0477|13ms|
|12.5m|2185.09MiB|2532.24MiB|0.0938|10ms|

Ambas tuvieron0timeslices>50ms. Residente adicional observado740.62MiB; no
atribuir toda esa memoria exclusivamente a navmesh. Son una pareja descriptiva
en escritorio compartido, con actividad de fondo sin controlar. No demostrar
causalidad de CPU ni capacidad80–100. Se conserva12.5 como candidato de precisión,
sin promoverlo a la base; habrá que valorar optimización con IA/carga real.

Agua elevada, secciones navegables regionales, rasantes y conducción continúan
pendientes. Edificios/vegetación van después y exigirán regenerar navegación.
No etiquetar esta fase como1.0 del mapa.

## Uso del escritorio y archivo

Regla de Guillermo30-09: preparar todo fuera de Computer Use; bloques breves
anunciados para iniciar/guardar, y reset del kernel al acabar cada bloque. No
mantener control durante generación, cálculos, empaquetado o logs. La API sky
leída no expone stop/dispose: reset está confirmado, liberación del bloqueo
percibido por el usuario no se midió independientemente.

Checkpoint `packages/baltic-regional-v0.3-candidate`: proyecto editable, ASC,
outline, biomas, configuración recompilada exacta, PBO y misión limpia. ZIP
14556324,630359048bytes,8974 miembros releídos por SHA256. Manifest y
`checkpoint.json` ligan todos los archivos. Dependencias absolutas locales;
no es instalador portable ni versión1.0.

Todos los runs propios cerrados normalmente, lease liberado, caja libre,
0 comandos pendientes y cleanup_degraded vacío. Addon de sonda retirado por
hash, copia conservada. TB/NMG abiertos y guardados, sin Computer Use activo.
RPT mantiene avisos de cfgenvironment ausente en la misión aislada y materiales
de personajes de prueba; `final-rpt-matches.json`. No proclamar arranque sin avisos.
`diagnostics/` preexistente queda fuera de los cambios de esta sesión.
