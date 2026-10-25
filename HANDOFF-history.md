# DayZ Baltic 12km — historial del handoff

## Relevo de Astra: HANDOFF.md íntegro en 65df91f (10-10-2026)

Copia literal del HANDOFF vigente hasta el 11-10. Solo informa; el estado actual está en HANDOFF.md.


<!-- LIVE-STATE:START -->
project: DayZ_Baltic_12km
updated: 2026-10-10
owner: Codex, ejecutor/integrador por petición viva; seguir autónomamente. Tres revisores Luna reutilizados por autorización de Guillermo. Sin push.
status: BASE_1_0_NO_ACEPTADA. EV95 preview aislada compilada y empaquetada; identidad OPRW, 996PAA/7968mips y lectura nativa completa PASS. Agua dinámica, render gris y relieve de toda la superficie siguen abiertos.
plan: plans/v30-rumbo-agua-1.0.md; planes EV9/10/12/13/14. Fondo 1 m, calado nominal 0,95 m; Narva local autorizado. TB antes de navmesh. Petición viva: toda la superficie, fallos y comprobaciones, no parar al completar una unidad parcial.
candidate: Referencia operativa EV82-B f9fb23de. Nueva preview @DayZ_Baltic_EV95_WideBankPreviewV1: terreno 40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a, mundo f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d, OPRW 03dfa1c3e50b37e966eaebe26a0aec737505e1a5c9b01acbede9716556fca3ba. Agua 3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14 exacta. 66.058 alturas modificadas frente a B; EV93/94 preservadas, sin promoción de la nueva preview.
smoothing: EV93 original 37e6d4bd preservado FAIL global. Selección run-02 3b22dcc3 retiene 499 unidades (332 legacy + 167 crestas), candidato 6e275573 con 30.066 alturas cambiadas. Consumidor global6e661b07 attempt-03 PASS22/22, reporte656e676e, readset16.480 exacto. Cobertura física/visible1,4913e-8/1,5072e-8m². Preview @DayZ_Baltic_EV93_SelectedBankPreviewV1 worldcb4ffc6b/OPRW63d94759, agua3946db8b exacta. Superficie524teselas/975PAA/7.800mips PASS; readback nativo completo PASS. No aceptación artística/dinámica ni BASE1.0.
wide_relief: EV95 composición40c174e3: 66.058 alturas cambiadas frente B, consumidor b0b7c872 PASS17/17. Worldf1a148ca/OPRW03dfa1c3,996PAA/7968mipsPASS. Readback nativo f01f9076 PASS4.194.304vértices/1212puntos/1205planos, maxerror1.52588e-5m,8negativos. 0agua sobrecls0 a fase muestreada;24ausencias frenteclase y349consultassinflags por clasificar. Sin aceptación dinámica/gráfica ni de toda superficie.
water: EV12 global: 6.419 LOD visibles modificados; 10.493 instancias conservadas (incluidas 538 piloto), 18 esquinas obsoletas retiradas y 1.014 piezas mínimas de junta con centros XZ exactos. 830 masas preservadas, sin nuevas conexiones ni agua en caras secas. 765.290 contactos mojados continuos en fuente. Cobertura compilada de 404.484 celdas: cero hueco físico, residuo visible 3,8464e-12 m2. Límites visibles originales/candidatos 0,292958/0,268750 m. No es aceptación gráfica.
land_artifacts: EV49 B sin cuatrocharcas reproduce2853muestras anomalas comunesA/B/A; vientoB no identico, limita amplitud causal. EV54 traslada conjuntamente29grupos/41masas,122objetos y11062vertices, fondo minimo1.005m;3grupos/4masas excluidos por politica/protecciones. Comparacion fresca puente6frames:alertas6.285%->0.173%, control0.1%; mejora local, no cierre global del shader.
rejected_land_repairs: D1 no alcanza 1,80 m en el punto. D2 sí, pero 68 de 840 cuerpos significativos fallan conservación de área/componente y 169 vértices quedan revertidos por pendiente. El residual toca una charca afectada. D1/D2 NO empaquetar; no crear D3 variando cotas o protecciones.
global_detection: EV71 censo8380418 caras:408 zonas>=1m2/726892.25m2 frente428/795569.19EV61; índice geométrico, no defectos confirmados. Consumidor91937 caras analíticas+320GEOS+423puntos PASS. ListaEV59 completa:2615/2760 a cota,145 protegidos (59lagos/91borde/5comunes),0 editables pendientes. CSV y replay exactos.
render: Referencia A underlay run0013bf35 reproduce recuadros con terreno cargado; tres frames alineados, control de pan/restauración y 1.225 alturas nativas coinciden con B (máx. 5,24e-6 m). Diagnóstico desechable world28a7509f/terrain3e12ced7 baja 1.089 vértices 6,1 m; agua3946db8b exacta y 6.826 entradas intactas. B/A-prime pendientes por banco ajeno. La causa sigue sin aislar; render_frozen_signal es aviso, no veredicto ni prueba del LOD seleccionado.
runtime_lock: 21:12 UTC: banco ocupado por LFSkateboard, sesión Claude b230dc6f-1e2, run1c53bb8f-3def-4439-87f7-626419ada6b4 con actividad reciente. Sin lease propia; lanzamiento/adopción no disponibles. Nuestro run0013bf35 ya cerrado ordenadamente. RAM libre 2,598 GiB; no lanzar consumidor global hasta ≥9 GiB. Pregunta de prioridad pendiente; no cerrar ni adoptar prueba ajena.
surface: EV93 seleccionado: 524 teselas seleccionadas,975 PAA+WRP cambiados,5.851 entradas intactas,7.800mipsPASS. Lectura nativa4.194.304vértices/1.212puntos/1.205planosPASS; maxerror1,52588e-5m. Snapshotd8c610f3 ligado a run1ed16d48 por procedencia/ctime/RPT/cierreordenado;8negativosPASS. Agua nominalencls0=0,dinámica3(playa),23presenciasausentes frenteclases,371consultasescalarespositivassinflags; diagnósticos no cierredeagua.
editor: E:/DayZ-Baltic-Build/editor-v30-delta/native-asc/base_v30_shorefinish.tv4p sigue con terreno 40d8, aguas antiguas y nueve puentes. No reimportar CSV duplicado. Máscara/Generate Layers tras congelar geometría; después navmesh/IA.
crossings_recheck: EV95/P/F: 45 cohortes, 4.592 estaciones centrales siguen secas, 2.426 sin plano fuente; cuatro controles y readset estable PASS. Diagnóstico central; no prueba de todo el ancho, ODOL, causa del render gris ni nuevo viaje de coche. BALTIC-015 continúa abierto.
remaining: 007/020 contornos y aspecto Msta/Volkhov;016shader seco;018 fondos interiores bajo mar, propuestaEV68/excepción647/651 y grupos protegidos;017grandeslagos y145bajos protegidos;01545cruces de reserva;019streaming y rectángulos actuales sin causa local aislada;014TerrainBuilder->navmesh/IA. No aceptar base por gates offline.
load: 008 pospuesto al sector mapeado; capacidad 80-100 no verificada.
env: GIS Python C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env. B9/B10 y B12 E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009. No Python global; P:/DZ inmutable; junctions en builds, no borrar recursivamente.
git: Branch claude/codex-handoff-review-74f290; diagnostic-integration-checkpoint conserva 76 copias con SHA, intentos fallidos y recuperación del archivador. Consultar HEAD para commit actual. Sin push.
wet_bank: Diagnóstico2209df75 NO aceptado. Consumidor recovery-v5 d31a2306 terminó: reporte b2ae1ed9, 17/19 gates PASS; fallan topología local y energía. Arista focal47,9525→37,1978°, sin nuevas >30°. Cruces/D8/conos/cobertura compilada pasan. El fallo anterior de protección era del comprobador: 16 cambios cls5/agua liberados por el plan, cero cambios efectivos/P9/carretera. Topología elimina 0,0283188364 m² de agua; energía supera allowance sin relajarlo. No empaquetar ni afirmar validez física completa. Recovery242/242 sin solución de un vecino, no inviabilidad global. Cota dual preparada con REAL_LP_ENABLED=False, sin LP real.
global_shape: Censo frescoB→EV95 de12.566.533bisagras: >30°13967→11890,0nuevas; p9912.87553→12.32726. No es aceptación artística. Clasificaciónnominal:9085cruceconocido,621sumergidas,1288aguaP/Fdesconocido,53emergidasconlámina,843contextoseco; sinODOLnoequivalevisibilidad. Civilglobal:100215vértices protegidos exactos. Checkpointwet-bank-pilot-checkpoint conserva39fuentes/recibos y4refsgrandes.
global_operator: Recovery1bd6b67d:2.502.853 alturas secas,27rollbacks,objetivo69217.203→68784.240,NOaceptado. Consumidororiginal timeout600s. V2instrumentado8ab83e18:16fixtures,14.212hashes/1.16GB en8.586s;attempt02 rechaza RAM tras23.869s, sin gatesgeométricos. Reintentar idéntico solo cuando DayZ libere RAM≥9GiB, mantener6GiBreserva/3GiBpico.
next: Completar underlay B/A-prime cuando el banco esté disponible, mismo motor/cámara/probe; verificar 1.225 alturas, control de pan y ROI. Repetir consumidor global V2 idéntico solo con ≥9 GiB libres; build-global-dry-preview-v1 está revisado y preparado, sin stage/build, exige ocho gates PASS y pines REC/EV95. No promover diagnóstico local. Cruces y demás superficie/TB/navmesh siguen abiertos.
handoff: evidence/v30-global-bank-extension-2026-10-10/diagnostic-integration-checkpoint/README.md y manifest.json son el último checkpoint. Incluye resultado local completo, recheck de cruces, análisis A y preparación global. Estado operativo E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/WORKING_STATE.md. B sigue referencia; BASE1.0 abierta.
<!-- LIVE-STATE:END -->

## Rumbo heredado del 07-10 (histórico)

Guillermo pidió el relevo el 07-10: «haz handoff completo y compactamos. Deja el rumbo muy claro para que lo vea astra y
pueda seguir». Se conserva abajo el encargo original. Para continuar manda el LIVE-STATE actualizado y la evidencia del 08-10; los pasos ya comprobados no se repiten por este texto histórico.

### Dónde estamos

- **Orillas:** la base aceptada es la v10b (Guillermo, 06-10, con su lista de niveles). La v11 (finales de río
  redondeados y más calado en ríos, arroyos y orillas de lagos) está vista en motor y **sin aceptar**. Desde el aire no
  se distingue de la v10b, y los finales de río siguen cuadrados.
- **Agua navegable (BALTIC-018):** Guillermo decidió el 07-10 subir su fondo a 1,0 m. La **v12** lo aplica sobre la
  v11: `E:/DayZ-Baltic-Build/v30-v12`, evidencia `evidence/v30-v12-candidate-2026-10-07`. Construida y desplegada como `@DayZ_Baltic_V12Candidate`; sin ver en motor.
- **Teselas oscuras (BALTIC-019):** no son del mapa. Es la carga de texturas del cliente de pruebas tras cada
  teletransporte, igual en Chernarus vanilla. Una vista de motor solo vale si `tools/playtest/dark_tiles_v30.py` da
  menos de 0,2.

### Pasos, en orden

1. **Comprobar que la v12 está completa**, en `E:/DayZ-Baltic-Build/v30-v12`. Hecho cuando:
   - `chain.log` acaba en «done v12»;
   - `check-v12-vs-v11.json` da PASS;
   - el despliegue existe: `deploy-receipt.json` en esa carpeta y `P:/Mods/@DayZ_Baltic_V12Candidate/Addons`. Si falta,
     ejecutar `evidence/v30-v12-candidate-2026-10-07/scripts/deploy_v12.py` con el Python GIS. Exige que la carpeta
     del mod no exista y comprueba los hashes.

   Si la cadena falló, leer el log del paso que falló y repetir desde ese paso en una carpeta nueva (`v30-v12b`). No
   borrar carpetas de construcción: el paquete deja uniones dentro (LL-393).
2. **Ver la v12 en motor y compararla con la v11.**
   - **Lanzar:** `dayz_test_run` con `project=DayZ_MCP`, `mode=all`,
     `mission=C:\Program Files (x86)\Steam\steamapps\common\DayZServer\mpmissions\BalticTideProbeV2.BalticTrial`,
     `extra_mods=["P:\\Mods\\@DayZ_Baltic_V12Candidate"]`, `no_base_mods`, `no_file_patching`, 1920×1080. Después,
     `session_acquire_wait` y `wait_for players_at_least 1`.
   - **Antes de lanzar:** avisar a Guillermo («abro el cliente; no lo cierres hasta que te avise»). La ventana sale
     en su monitor principal.
   - **Poses**, con `camera_set lookat` y la altura absoluta del suelo + la altura de cámara:
     - el río del punto de aparición: SPAWN_12_SSE, cámara [1185, 12, 5392] → [1250, 1, 5100], y SPAWN_40_S, cámara
       [1185, 40, 5392] → [1185, 2, 5134]. Las de la v11 para comparar están en
       `E:/DayZ-Baltic-Build/v30-v11/views-water-report`;
     - el navegable grande (77 ha, centro (6081, 4966));
     - la zona de Narva (centro (2417, 6890), radio 620 m, `tools/terrain/profile_coast_v30.py:49`), que la pasada
       no toca: su tramo navegable de 22 ha, en torno a (2314, 6711), sigue con el mar debajo;
     - un tramo bajo hacia el mar, para ver el paso entre el fondo de 1,0 m y el que sigue bajo el mar: está en
       x 2052–10752, z 5196–10266 (`navigable-below-sea.log` de la v12).
   - **Validez:** tras cada teletransporte, capturar cada 30–60 s hasta que `dark_tiles_v30.py` dé menos de 0,2
     (hasta 6 min).
   - **Hecho cuando:** en los navegables altos ya no se ven el oleaje ni la espuma del mar, ni el borde recto junto a
     la orilla, y el agua se ve como la de los ríos.
3. **Probar la lancha vanilla en los navegables.** Es el contrato de navegación (P9): calado de 1,0 a 2,17 m.
   - El procedimiento es el del piloto de cauces del 04-10, `evidence/v30-vanilla-channel-pilot-2026-10-04`:
     - la preparación, con `tools/navigation/prepare_vanilla_channel_boat.py`;
     - la misión `BalticVanillaChannelBoatV1.BalticTrial`;
     - el resultado, `boat/verification.json`: PASS en el tramo R1 en los dos sentidos, run e5ccbe6a.

     Hay que adaptarlo a los navegables de la v12.
   - **Hecho cuando:** la lancha recorre sin encallar el tramo de aparición y un trecho del navegable grande, en los
     tramos altos y en uno bajo (1,0 m de agua).
   - **Si encalla:** anotar dónde y con qué calado. La alternativa, subir agua y terreno, es decisión de Guillermo.
4. **Presentar a Guillermo**, con las vistas válidas y el resultado de la lancha, y pedirle tres decisiones:
   - **la v12:** si la acepta;
   - **los tramos bajos y Narva**, que siguen con el mar debajo (14.594 vértices navegables, unas 52 ha). Opciones:
     - dejarlos: cerca del mar es coherente;
     - llevar también su fondo a 1,0 m con 0,3 m de agua como mínimo, y no serían navegables;
     - subir agua y terreno;
   - **los finales de río:** siguen cuadrados en motor. Para que se vean redondos habría que estrechar el río a lo
     largo de varias celdas antes del corte.
5. **Después**, en este orden si Guillermo no dice otra cosa:
   - BALTIC-019: prueba de foco. Hacen falta 20 s con la ventana de DayZ delante (hace falta Guillermo: desde un
     script no se puede mantener el foco) y `evidence/baltic-019-teselas-oscuras-2026-10-07/scripts/focus_probe.ps1`
     grabando.
   - El agua baja del RIVER_80 (1,0–1,4 m), que sigue plana.
   - Los pasos 4–9 de `plans/v30-rumbo-agua-1.0.md` y los lagos 269 y 170 (BALTIC-017).
   - Revisar BALTIC-012/013 (canal del Luga con dientes, Neva) con el contrato nuevo.

### Cómo trabajar aquí

Lo que más cuesta recordar:

- **Python:** solo el GIS, `C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe`, con
  `PYTHONUTF8=1`.
- **Escribir en OneDrive:** una sola escritura y relectura. Los `.py` se escriben en el scratchpad y se copian
  comprobando el hash. JSON nunca con PowerShell.
- **DayZ MCP:**
  - lease antes de mutar; el lease caduca a los 120 s sin llamadas (`session_heartbeat`);
  - no matar procesos de DayZ: cerrar con `dayz_test_close`;
  - el cliente puede abrir solo el menú de pausa: `ui_click continuebtn`.
- **No dar el foco a DayZ por script:** Windows se lo devuelve a la ventana del usuario y le molesta.
- **Al parar una cadena en segundo plano:** `TaskStop` no mata sus hijos (Python y workers). Buscarlos por la línea
  de comandos y pararlos por PID.
- **Git:** commits solo de lo propio, con rutas exactas, en la rama `claude/codex-handoff-review-74f290`; sin push.
  Nunca tocar `v29-base`.
- **Delegar:** GX10, máximo 4 lanes en total. Leer `gx10_occupancy.py` antes de lanzar y lanzar GLM con
  `GX10_EFFORT=medium`. Revisa otra familia.
- **Herramientas de medida de este tramo:**
  - `tools/playtest/dark_tiles_v30.py`: validez de una vista;
  - `evidence/baltic-018-navegables-2026-10-07/scripts/navigable_below_sea.py`: agua con el fondo bajo el mar;
  - `evidence/v30-v12-candidate-2026-10-07/scripts/check_v12_vs_v11.py`: que solo cambie lo previsto.

## Leer primero

Sesión más reciente: [v11, teselas oscuras, navegables y v12, 07-10](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-07-dayz-baltic-v11-finales-y-profundidad.md>). Lo que sigue es anterior.
Continuación vigente: [piloto de cauces vanilla, 04-10](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-04-dayz-baltic-piloto-cauces-vanilla.md>).
Antes: [integración de orillas y agua vanilla, 03-10, noche](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-integracion-orillas-y-agua-vanilla.md>).
Revisión y decisiones vigentes: [revisión de Claude, 03-10](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-revision-claude-relevo-y-herramientas.md>): TB aplazado hasta congelar la base; siguiente bloque, paquete con d5dadae8.
Continuación vigente: [orillas, editable y consumidores, 03-10](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-orillas-editor-y-consumidores.md>).
Antecedente: [navmesh, pruebas y reinicio](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-navmesh-y-reinicio.md>).
Antecedente autónomo: [sesión de ocho horas](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-sesion-ocho-horas.md>).
Antecedente: [editor, Luga y piloto FTT](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-v30-editor-luga-ftt.md>).
Referencia completa previa: [V30, base y navegacion, 02-10](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-02-dayz-baltic-handoff-completo-v30-base.md>).
La continuacion actualiza esas identidades y resultados; el resto conserva su alcance anterior.

1. Este LIVE-STATE y el [plan de agua y suelo](plans/water-ground-rebuild-v1.md).
2. [product-spec.md](product-spec.md) (P1–P15) y [bugs.md](bugs.md).
3. La [auditoría de agua y suelo](evidence/v29-water-color-audit-2026-10-02/summary.json),
   con sus mapas y recortes en la misma carpeta.
4. Para un resultado anterior concreto, su recibo en la tabla de validación del
   [handoff completo V29 de Codex](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md>).
   La historia está en [HANDOFF-history.md](HANDOFF-history.md) y no decide procesos,
   permisos ni el estado actual.

## Decisiones vigentes que no se reabren

- Recorte aprobado el 29-09 y una única escala XY; no agrandar San Petersburgo.
- Terreno, agua y navegación antes del mapeado (P10). Assets vanilla primero y
  anchuras a escala humana.
- Relieve selectivo por jugabilidad (P12), ríos para lancha vanilla con puentes
  elevados (P9) y carreteras lisas (P11).
- Agua, 02-10: ríos navegables con forma natural y ancho variable (30–60 m, con el
  canal libre de 24 m dentro); ríos con nombre de 8–20 m y arroyos largos de 3–6 m;
  delta del Neva con brazos e islas; lagunas desde ~300 m².
- Relieve, 02-10: conservar las zonas altas, dejar zonas de llanos y ajustar el resto a
  algo más natural, sin el ×5 general.
- Objetivo de 80–100 jugadores; el hardware del servidor sigue sin concretar.
- Orillas, 06-10: la v10b es la base aceptada, con su lista de niveles.
- Navegables, decisión08-10: conservar el fondo a 1,0 m y aceptar 0,95 m de calado geométrico mínimo; embarcación de referencia, lancha vanilla. Bajos/Narva conservan las excepciones anteriores. decision.json del contrato actual contiene la respuesta del usuario.
- Teselas oscuras: causa no aislada. dark_tiles_v30.py es una heurística de color, no un gate suficiente de carga. No usar la atribución histórica al cliente/foco como hecho demostrado.

## Revisión del 02-10 (Claude sobre el trabajo de Codex)

- El 01-10 se iteraron unos 25 candidatos de terreno con un sistema de
  restricciones duras: bastaba una fila imposible para abrir otra versión.
- Los 670 «residuos» de agua (2,98e-8 a 9,537e-7 m) son exactamente el ULP de
  float32: redondeo numérico, no un defecto.
- La prueba de carga sobre un terreno vacío no informa sobre 80–100 jugadores.
- La auditoría de agua y suelo confirmó lo que Guillermo veía: agua que falta, un
  canal uniforme, satélite desalineado y bordes rectos en el relieve. Detalle en
  bugs.md (BALTIC-009 a 011) y en el plan.
- El relieve es ×5 de base fuera de las zonas protegidas, y hasta ×20–24 en dos
  zonas. Guillermo pidió conservar las zonas altas, dejar llanos y el resto más natural.

## Entorno y precauciones

- `P:\` es un `subst` de `C:\Users\guill\OneDrive\Documentos\DayZ Projects`. En
  OneDrive, las escrituras grandes o que encogen un fichero se hacen con un solo
  write de Python y relectura.
- `P:\Mods` es una junction a `C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop`.
  `P:\baltic_water` apunta a `build-temp\regional_water_assets_v2\baltic_water`:
  `build-temp/` no es desechable.
- `build-isolated/` contiene junctions a los datos vanilla: nunca borrarlas ni
  copiarlas siguiéndolas.
- DayZ MCP: lease y lifecycle guard del runbook. Las misiones se pasan con ruta
  Windows (`\`). `camera_set` derribó el cliente en el run db477cf8: hasta aislar
  BALTIC-001, capturar desde la vista del jugador.
- E: es el destino de los archivos grandes. Consultar el espacio libre actual de
  C: antes de cualquier salida grande; la estimación anterior de21GB está obsoleta.

## Ejecución autónoma — 02-10, de las 04:00 a las 12:00 locales

Guillermo pidió, antes de compactar, no parar hasta tener la base del mapa (superficie,
terreno, ríos y demás) o hasta que pasen 8 horas. `/goal` solo lo puede lanzar él; la
condición propuesta, para pegar tras compactar:

```text
/goal Base del mapa Baltic V30 terminada y verificada, o son más de las 12:00 hora local del 2026-10-02. Terminada significa: (1) ASC V30 en tests/terrain_v30 con puertas offline PASS: carreteras con la definición de Codex (tools/terrain/verify_roads_v30.py), calado y orillas del agua, pendientes de tierra ≤35° y Narva idéntico a V29; (2) piezas de agua V3 para navegables, delta, ríos, arroyos ≥2,5 km y lagunas; (3) satélite a 1 m/px y máscara nuevos derivados del agua final; (4) importado en Terrain Builder, WRP exportado y paquete @DayZ_Baltic_V30 con navmesh nueva; (5) prueba en el juego por MCP con capturas desde la vista del jugador. En cualquier caso, HANDOFF.md y el handoff de sesión actualizados con lo hecho, lo pendiente y los fallos.
```

Reglas de la ejecución:

- Orden: fase 2 → 3 → 4 → 5. Cada fase termina con su puerta y un commit en `v29-base`.
  V10, V33 y V29 no se tocan; todo va a carpetas y mods nuevos.
- Computer Use solo en bloques agrupados (Terrain Builder, NavMeshGenerator) y soltado
  al acabar cada bloque. DayZ MCP: `session_status`, lease, cierre ordenado y release. Sin
  `camera_set` mientras BALTIC-001 siga abierto.
- Nada destructivo: no borrar variantes de C: (el archivo de E: lo permitiría, pero falta
  la confirmación de Guillermo) ni reescribir evidencia.
- Si una fase no cierra en dos intentos con estrategias distintas, documentar el bloqueo y
  pasar a la siguiente que no dependa de ella (DZ-R5).

### Resultado de la ejecución autónoma (02-10, 04:00–06:00)

`/goal` no llegó a lanzarse: el contexto se compactó solo. Se trabajó con la misma condición de parada.

| Punto de la condición | Estado |
|---|---|
| 1. ASC V30 con puertas offline | **Hecho.** `tests/terrain_v30/baltic_terrain_v30.asc` (`362550d1…`), determinista. Carreteras con la definición de Codex: 76.536 estaciones, 0 fallos. Calado, orillas, coherencia con las piezas (416.633 celdas), suelos, lecho, pendientes ≤35° y Narva idéntico: PASS. Evidencia en `evidence/terrain-v30-2026-10-02/`. |
| 2. Piezas de agua V3 | **Hecho:** 17.622 planos pond en losetas de 48 m y bandas de 25 mm (`baltic_water_v30`). El delta y el mar son el mar del motor. Los arroyos son planos propios con surcos de vértices. |
| 3. Satélite a 1 m/px y máscara | **Hecho** con los 4 materiales de V29; los 215 materiales incompletos de V29 se rehicieron completos. Evidencia en `evidence/surface-v30-2026-10-02/`. Las vistas de esa carpeta son offline, **no** capturas del motor. |
| 4. Terrain Builder, WRP y paquete con navmesh nueva | **Parcial.** Sin Terrain Builder: el WRP se deriva del de V29 con alturas y objetos V30, y se empaqueta con AddonBuilder. `@DayZ_Baltic_V30` desplegado: mundo `93c50593…`, agua `e9b52b8c…`. **Falta la navmesh nueva:** sigue la de V29, caducada. |
| 5. Prueba en el juego desde la vista del jugador | **Parcial.** Cuatro runs funcionales cerrados en orden: `1c716882` (preview 1), `0dce0a73` (preview 2), `da0137cc` (preview 4) y `86963791` (preview 6, con calzadas sobre agua). el mundo carga en 13–16 s, el agua está a su cota y las superficies son correctas. **Sin capturas:** la pantalla se apaga a los 5 min sin actividad. |

Revisión de otra familia: Codex revisó la cadena (solo lectura) y encontró 2 fallos P1 y 3 P2.
Todos se comprobaron y corrigieron; el detalle está en `evidence/terrain-v30-2026-10-02/codex-review.md`.

Después de la revisión salió un fallo más, en el run b0d7f161: el agua nueva tapaba calzadas que V29 tenía en
seco, como el terraplén al oeste de San Petersburgo. Ahora las carreteras conservan su terreno; las calzadas
sobre el agua pasan a 1,5 m y la carretera se apoya entera sobre el terraplén.

Cambios respecto al plan:

- Sin Terrain Builder: el mundo se deriva del de V29.
- Sin el prototipo de arroyo en el juego: sin pantalla no había juicio visual.
- Cuatro superficies, las de V29.
- Satélite procedural: el recorte está a escala 1:37 y no hay imagen real que encaje.

#### Reconstruir

En la raíz del repo, con el Python de `env`:

1. Rásteres de agua y terreno:
   `tools/terrain/build_v30_water.py tests/water_v3 tests/terrain_v30`
   y después `tools/terrain/build_v30.py tests/terrain_v30 tests/terrain_v30`.
2. Puertas:
   `tools/terrain/verify_roads_v30.py "tests/terrain_v30/terrain_v30.npz::heights" "tests/terrain_v30/terrain_v30.npz::water"`
   y `tools/terrain/verify_terrain_v30.py tests/terrain_v30/terrain_v30.npz`.
3. Superficie: `tools/terrain/build_surface_v30.py tests/terrain_v30/terrain_v30.npz <carpeta>`.
4. Paquete: `tools/terrain/build_v30_package.ps1 -Build <carpeta nueva> -Terrain tests\terrain_v30\terrain_v30.npz -Layers <carpeta de superficie>`.
   La salida queda en `<Build>\out\Addons`; se despliega en `P:\Mods\@DayZ_Baltic_V30\Addons`
   comprobando el hash.
5. Vistas offline: `tools/terrain/render_view_v30.py`.

Las builds están en `E:\DayZ-Baltic-Build`, fuera de OneDrive, porque C: tiene unos 20 GB libres.
Los previews 1 a 3 siguen allí para volver atrás.

#### Pendientes al cierre de Claude (06:40; ver LIVE-STATE para avances posteriores)

1. **Navmesh V30.** Necesita que Guillermo autorice Computer Use para NavMeshGenerator o que lo haga a mano.
   A las 06:40 se intentó pedir el acceso, pero `request_access` no encuentra la aplicación: ni
   «NavMeshGenerator», ni «NavMeshGenerator_x64», ni «DayZ Tools», aunque estaba abierta. No está en el
   menú Inicio y la petición nunca se mostró. Para usar Computer Use hace falta un acceso directo de
   `DayZ Tools\Bin\NavMeshGenerator\NavMeshGenerator_x64.exe` en el menú Inicio; crearlo es decisión de
   Guillermo. Si no, lo hace él a mano con los mismos pasos.
   - Lease y `dayz_test_run(project=DayZ_MCP, mode=server, navmesh_data_server=true, mission=…\mpmissions\empty.BalticTrial, extra_mods=[P:\Mods\@DayZ_Baltic_V30])`.
   - En NavMeshGenerator: conectar, recibir los parámetros del mundo, generar todo y guardar el `.nm`
     (V29 tardó 382 s con 966.289 teselas).
   - `dayz_test_close` y release.
   - Reempaquetar con `tools/terrain/attach_navmesh_v30.ps1 -Build E:\DayZ-Baltic-Build\v30-preview6 -Navmesh <nm> -Out <carpeta nueva>`.
     Se probó en vacío con la navmesh actual: funciona y no toca la build de origen.
   - Prueba de IA.
2. **Revisión visual en el juego**, con la pantalla encendida: capturas desde la vista del jugador en el
   delta, el Neva navegable, un arroyo, una laguna, la costa, las colinas y el puente de Narva.
   `camera_set` sigue vetado (BALTIC-001).
3. **Decisiones de Guillermo:**
   - La zona de Narva (480 m idénticos a V29) conserva el agua cuadrada de V29. ¿Se mantiene el
     requisito o se rehace con orillas suaves?
   - ¿Más superficies vanilla? Exigen materiales nuevos y comprobarlas en el juego.
   - Arroyos: ¿planos propios, como ahora, o piezas vanilla `stream_14_*`?
   - Borrar las variantes de C: sobre una lista concreta (sigue pendiente).
4. Terrain Builder para el mapeado: importar el ASC V30 en un clon del proyecto V29 y la capa de agua desde
   `pieces.json`.

## EV35–43 — exact census and conditional render detector

EV36 measures101602 design stations across77 built courses; exact triangle sections withdraw4 of49 coarse alarms. The45 remaining intervals intersect road/platform reserves; attribution and longitudinal continuity remain separate. Stream0431 is tier1500, excluded like0452/0456. EV37 seven-vertex repair withdrawn.

EV38 cap reprofiling, EV39 exterior lake smoothing, EV40 coupled bank smoothing and EV42 inverse contour fit are rejected, not packaged. EV40 slope gains do not override shoreline regression; wet-vertex preservation is correctly named. EV42 also demonstrates why a6m turn counter alone mistakes smooth tight curvature for angularity; actual corners still reject its candidate.

EV41 diagnostic omission of four pond instances is built but not run. EV43 projected water-marker calibration generalizes to a held-out image half, but native screen confirmation is pending. Read-only native projection addon built. The corrected ray consumer passes500 independent rays plus a no-water-sidewall negative. Archived A2/Bstable sequences yield16106/323 variable dry samples at common threshold11.8096 with9095 identical reference pixels; this does not prove shader cause or map-wide completion.

MCP remains disconnected; no game runs launched in this block. Prior free-bank state is historical, not a current claim. EV28 production hashes freshly unchanged. Evidence directories EV35–43 contain adjudications, source deltas and consumers. Continue the full map; do not promote failed trials or declare base1.0 accepted.

## EV44–47 — whole-map dry risk, crossings and retained shape failures

EV44 reproduces all ten original v11 water arrays exactly before attribution. The687 road-cut vertices directly affect4547/4592 exact dry stations:32 fully attributed crossings and13 partly. Not all removed vertices were V29 dry: the carriageway expansion reaches neighbours. This is source mechanism evidence, not acceptance of dry stream crossings.

EV45 considers every8380418 native triangle and clips actual P/F/sea planes.453 dry-low components(437>=1m2),81.9064ha; includes legitimate coastal transitions. CSV gives a proven dry point inside each component, not a centroid possibly inside a pond. Independent analytic/GEOS/point consumers pass.99.9441% ofEV43 conditional A2alerts lies in this band. It is a risk index, not437 confirmed render errors.

EV46 continuous shallow profile rejects area/shape. EV47 equality on actual native water area fixes contraction and improves slope/one-metre energy, but creates a72.391-degree tip over metre-scale segments. Both retained and rejected; no packaging. No more parameter sweeps.

Current external block: both exposed DayZ MCP connectors returnedTransport closed, latest direct status also fails. No new runs, no bypass. The reconnect request is pending. Native projection and isolated pond A/B/A are prepared. The map is still incomplete; no base acceptance or promise that a source census verifies the graphical shader.

---

# DayZ Baltic 12km — historia del handoff (29-09 a 01-10)

Retirado de `HANDOFF.md` el 02-10-2026 para dejar allí solo el estado vivo. Describe
ensayos anteriores: no decide procesos, permisos ni el estado actual. Los bytes
originales están en git: `git show 9d8a5dc:HANDOFF.md`. Aquí se han normalizado los
saltos de línea, que el original tenía cuadruplicados.

## LIVE-STATE de Codex al cierre del 01-10 (literal)

```text
project: DayZ_Baltic_12km
updated: 2026-10-01T21:36:25.602572+00:00
owner: Codex executor/integrador, continuacion autorizada por Guillermo; sin agentes adicionales
status: HANDOFF_V29_PARTIAL_ACCEPTANCE_NO_OWN_RUNTIME
state: evidence/foundation-followup-2026-10-01/state.json
plan: plans/outline-water-smoothing-v1.md; plans/road-network-v25-continuous-coverage.md
terrain: ACTUAL V29 ed6cdaa5; 2048x2048 a6m/12.288km. Seis gates offlinePASS,239126secciones viales,621260extremos de orilla;0infracciones. Agua/fairways/islas/reserva/Narva protegidos. Delta max5.079304m contraV33; compuesto<=6m contraV10.
bridge: 9 tramos /225m /tablero11m. Galibo geometrico6.338m en18m con agua de diseno3m; no acredita barco mediano.
native: ACTUAL road_v29.tv4p; r2 1763facc/r3 9cd94334 con cierre/reapertura reales. Alturas/materiales/10161poses iguales semanticamente. Literales FAILestrictoV10 por670residuosY heredados<=0.954micrometros; solo derivados explicitos restaurados. Provenance y negativos en road-v29-native.
package: ACTUAL @DayZ_Baltic_RoadV29: world b3418f92, compiledWRP2c95ab7d, waterf9a5cdf7, NMfacaf1e3/445971256bytes. Otras6826entradas exactas. V10d1008dd6 yV3338ebe847 rehasheados intactos al cierre. RoadV29Data es intermedio conNMheredada: no entrega jugable.
navmesh: ACTUAL V29966289/966289teselas,12.5m; guardada/empaquetada desdeWRP2c95ab7d. Decoder estructuralTESM6,1091979poligonos. ConsumidorV7 separado; regenerar tras mapeado. Recibo road-v29-native/nav-generation-saved.json.
water_nav: V29 consumerV7 PASS81212water/dry,314nav,15routes; maxgrounderror0.00046262m. Runfe6af12e EXITED_ORDERLY. Exact final PBO b3418f92. Queries are not physical traversal.
boat: HEREDADO V10:12segmentos seleccionados/26.600558km aceptados entre runs aislados; V29 conserva fairways/modelos protegidos, sin repetir lancha en PBO final. No viaje continuo unico,flotilla,tripulantes ni barco mediano. Fallos anteriores preservados.
ai: HEREDADO V10 cruce continuoV4 control+ambos sentidosPASS/18negativos. ACTUAL V29 queries314/15PASS y carga100vivos/despiertos; load INCONCLUSIVEpor deriva objetivo2.06473m. No locomocion fisica regional completa ni100jugadores.
driving: ACTUAL V29 seis rutas costa/colinas/sur ida/vueltaPASS entre DriveV3 casos0..3 yV4 casos0..1;5282.735m acumulados/2641.368m unicos,salud1000/4contactos,18negativos. DriveV3 5PASS/1FAILterminal conservado. No toda red ni piezas colocadas.
visual: V29 PENDIENTE: grupo agua con foco ajeno/entrada humana; CU reseteado sin insistir. Neva/reserva/surV29 referencias preparadas, no ejecutadas. V33 tiene capturas historicas; texturaWorldCover provisional. Crash transicion lejana BALTIC001 abierto.
performance: V29 INCONCLUSIVE_ACTIVE_LOAD:0/25/100/0 completo,60muestras/fase,420host/proceso. Objetivo deriva2.06473m>2m fases2/3. Sitios101/rutasWALK100PASS;servidor~2.50-2.52GiB. Escritorio no aislado; noFPS ni capacidad80-100. HistorialV10PASS no sustituye esta prueba.
archive: Checkpoint ZIP anterior V10 f96d3d5c, no V29. Manifest/snapshots documentales V29 en handoff-complete-v29; fuentes editables yPBO actuales en workspace. Falta checkpoint V29 completo tras aceptar base. DependenciasP/vanilla/junction no portables.
coordination: CIERRE: load ebffaa12 EXITED_ORDERLY cliente/servidor;420muestras cada sampler;4logs archivados. Lease propio liberado; selfnone. Box quedo vacio al cierre; relectura posterior: otro run @LFPowerGrid 7e4d808b activo, no tocar/adoptar. Sin procesos Baltic propios niTB/NavMeshGenerator/AddonBuilder. CU reset/OFF.
usage: 20:59UTC:5%remaining; reset individual solicitado, sin respuesta ni consumo nuevo.
next: Ante nueva peticion: revisar handoff completo; visual Neva/reserva/sur con escritorio disponible yrefs congeladas; aislar deriva del fixtureload sin relajar2m; repetir carga en reposo. No reactivar automaticamente noche8h. Base aun sin aceptacion1.0.
commit: HEAD4ff154b7; cambios previos/nocturnos preservados, diagnostics/ajeno. No version1.0 ni mapaentero terminado.
continuous: V4 PASS control y ambos sentidos,2188registros activos, actor lateral<=0.954m/humano<=0.357m, contacto/salud/metasPASS,18negativos. BALTIC002 aceptado para cruce continuo; ruido estacionario conserva FAIL. Rumbo corregido y tasas sobre SAMPLE200ms, sin cambiar limites4/12m/s. Sonda31c74cf3.
river_followup: Delta8V4,delta10V5,Narva6V5 aisladosPASS, cadauno12negativos+4relojes,salud600. Narva6:1757.178s/3951muestras/549transiciones, extremo1.966m, paso bajo puente. BALTIC003/004 aceptados para esos casos. river-accepted-segment-coverage.json consolida12tramos/26.600558km entre diferentes runs; no viaje unico ni flotilla/barco mediano. FAIL antiguos intactos.
visual_followup: V33 sur/reserva/Neva capturados y protocolos de camara completos. Neva repeat333442bf EXITED_ORDERLY, original neva.png. Textura provisional/aspecto global pendientes.
outline_water: V33 final world38ebe847 WRP2ccb8dc4 freshNM425b8488; all966289tiles,6826other entries unchanged. Regional consumer PASS; local dynamic water664epochs/15936samples PASS with0.28706m dry margin. Explicit derived670waterY corrections; not literal export.
regional_driving: V29 seis viajes PASS entre V3/V4,5.282735km totales/2.641368unicos,18negativos. Todos salud1000/cuatro contactos. V3 regreso sur FAILterminal conservado; V4 solo acelerador terminal.
skills: dayz-terrain-workflow/references/regional-relief.md actualizado: persistencia observada,residuos heredados y especificidad aguaV7. SHA61e52ae3; SKILL.md intacto. Recibos skill-persistence-update/skill-consumer-specificity-update. No skill nueva redundante.
closure: Peticion viva: handoff completo. Pruebas y procesos cerrados. Ventana nocturna02:42:43-10:42:43UTC previa completada/heartbeatPAUSED;unreset anterior;ningunreset nuevo consumido. Cuota individual pendiente no es accion de continuacion.
evidence_archive: packages/baltic-foundation-v10-night-evidence/manifest.json; autoridad del resultado del archivo complementario.
candidate_navmesh: V29 facaf1e3/445971256bytes;966289tiles completos; finalPBO b3418f92, WRP2c95ab7d. V7 regional PASS. V10/V33 anteriores intactos.
road_network: V29 ed6cdaa5 seis gates offlinePASS. r2 1763facc/r3 9cd94334 persistencia nativaPASS; dos laminas exactas;670residuos heredados restaurados solo en derivados explicitos. FinalPBO b3418f92/WRP2c95ab7d/nuevaNMfacaf1e3.
checkpoint: evidence/foundation-followup-2026-10-01/outline-v33-checkpoint.md
bugs: 8 registros;5aceptados con alcance,1abierto,1parcial abierto,1inconcluso. BUGS.md autoridad.
handoff_complete: C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md
```

## Historia anterior al 01-10

### Estado vigente

Leer primero el [handoff completo V29](<C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-01-dayz-baltic-handoff-base-v29.md>), LIVE-STATE y `evidence/foundation-followup-2026-10-01/state.json`. El checkpoint y los apartados siguientes conservan historia; no son una instruccion de retomar pruebas ni describen procesos activos.

### Histórico — navegación local de Narva

Los párrafos siguientes describen ensayos anteriores; no determinan el estado
actual de procesos, artefactos ni permisos. Evidencia: `evidence/navigation/README.md`.
Continuación01:44: run c9dc7555 solo servidor PASS_EMPTY_BOAT_LOCAL_OUTWARD,
226 muestras continuas,196 propulsadas, salud600, paso bajo vano y destino
alcanzado; log8ad568ff. Sin cambios del verificador. ca8a8d0f llegó pero conserva
FAIL de continuidad por pausa inicial2.387s sin motor; evidencia inmutable.
Tripulación, regreso, visual cliente y ríos regionales pendientes.
MCP libre. Skill actualizada/validada; negativos del verificador pasan.
Continuación01:28: mar abierto PASS_CALIBRATION_MOVEMENT_ONLY,89.278m/salud600,
85 muestras consecutivas de propulsión (calibration-input-v2). El control anterior
se quedaba en neutral1/RPM700/hélice0. OnInput más solicitud de marcha sostenida
lo resolvió en este ensayo; no separar causalidad de ambos cambios.
Carreteras: la extensión del perfil hasta320m detecta terreno exterior sin preparar
con cambios de rasante6.274pp y desviaciones133.8mm; no es regresión del puente.
Nuevas fuentes/evidencias sin commit tras interrupción; HEAD anterior6f81b94.
La base anterior sigue en `evidence/regional-water/final-pbo-verification.json`
y `packages/baltic-basic-v0.1/README.md`; no confundirla con el candidato navegable.
MCP b024257 integrado. Skill dayz-terrain-workflow actualizada y validada.
Todo lo que sigue es histórico; no decidir procesos/sondas/permisos
a partir de esos estados anteriores.

### Historial conservado

### Continuación actual — agua medida y navegación preparada

Fuente actual: `evidence/render-water/auto-observer/runtime-checkpoint.json`.
Supersede el checkpoint anterior de sonda sin cargar y todos los estados históricos
de proceso/F10 que aparecen más abajo. No reinstalar F10: ya no es necesario.
El usuario cerró TB bloqueado; se reabrió el proyecto guardado. Addon automático
temporal compilado y ejecutado por el motor: marcadores CONSTRUCTED y COMPLETE_441,
log nuevo SHA `189baf62cf06dea3655ac27e4ce557b974c1609fce0e51d2a79815382d54550d`.
`verify_water_observer.py --native narva_tb_dryland_v1.asc` devuelve exit0 y
PASS_SAMPLED_DRY_INTERIOR. Los297 puntos secos interiores de referencia están
secos y por encima del máximo1m;44 estaban inundados antes y108 no superaban1m.
La lectura actual del mar fue0.506368m. La comparación contra el ASC guardado
coincide hasta0.005000033m. No se extrapola a toda la región.
Vista de orilla en motor(3222.75,8008.25), captura `orilla-3223-8008.png`: agua,
borde y terreno visibles sin las manchas negras previas. Es revisión puntual,
no una prueba exhaustiva de conectividad. No hubo edición de terreno durante
este ensayo; hash TV4P conserva `5f9390837b3a503977bf9a5f1a67f3a92ad9a066778207f5e1b7076ccec4feeb`.
Buldozer cerró normalmente18:25; TB cerró después. Parámetros originales
respaldados y restaurados, comprobados en TerrainBuilder.opt tras el cierre.
PBO temporal retirado por hash; fuentes/paquete/evidencia conservados. No se
tocaron perfiles de entrada ni scripts vanilla. Persisten avisos preexistentes
de PluginConfigDebugProfile y fugas al cierre; no impidieron esta medición y
no se afirma ausencia general de errores del visor.
El usuario autorizó específicamente NavMeshGenerator; abrió correctamente.
No se generó .nm. La UI pide un servidor local de datos; el launcher compartido
no admite `-startNavmeshDataServer`. Misión `missions/empty.BalticTrial` y config
`tests/navmesh/ServerDZNV.cfg` preparadas, no desplegadas; linter1 archivo,0
errores/avisos. `plans/navmesh-data-server.md` propone una opción booleana tipada
sin abrir argumentos libres. Guillermo eligió explícitamente añadir y validar
esa opción en DayZ_MCP. Implementación en worktree aislado del workspace
`work/dayz-mcp-navmesh`, rama `feat/baltic-navmesh-data-server`, base
`28f76cd1a498d8be101bf596d9c061231711d3d7`. El despliegue compartido sigue intacto.
PBO de mapa corregido todavía NO desplegado: e3e6b361...; despliegue real sigue
e4b07860... (ensayo navempty anterior). Antes del próximo run hay que desplegar
el candidato por hash. La versión básica continúa pendiente de carga y juego.

### Alcance vivo

Guillermo pidió continuar hasta la versión 1.0. Producto: región condensada con agua, reserva, conexiones y closeup íntegro de San Petersburgo; Narva/frontera y zona occidental; vanilla primero, anchuras humanas, objetivo 80–100 jugadores. Recorte v0 aprobado y escala XY única. No concurrencia con Exta ni entrega suya incorporada.
Guillermo precisó continuar hasta la versión básica y corregir las manchas negras y el agua fuera de sus límites. No etiquetar este prototipo como 1.0 completa. Coeficiente Z final, densidad y búnker aún sin fijar; no decidirlos silenciosamente. Esos puntos no impiden la prueba técnica preparada.

### Antecedentes de importación y empaquetado (históricos)

- Proyecto actual TB: `tb/narva_trial/narva_trial.tv4p`, candidato de agua guardado a las 16:36. Reabierto en TB PID208720 y exportado a `baltic_water_reopened_v1.wrp` (17:22:30), SHA `17e750e61f081635813522808b4dfe019711f5dd4fb14b60d4830ae4fc5dc98c`. Verificados todos los vértices y ambos objetos. Cambian solo orden de objetos y dos bytes del registro terminal sin nombre. Sonda posterior pendiente; no repetir V3 ni basal.
- Corrección exclusivamente local: 202 vértices/radio 48 m; fuentes y copias regionales conservadas (gate previo de 569 hashes). ASC exportado: 4194304 alturas dentro de 5.01 mm; negativo original rechazado.
- V3: 289 cuadrícula + 289 perfil + 34 extremos, ambos accesos de 8 m a cota 2 m sin gap medido. Registro fijado por V2, sin refit. El WRP reabierto conserva todas las alturas y la posición del puente (error 0.0000004063 m).
- Primer PBO: `packages/baltic-playtest/Addons/narva_trial.pbo`, 24806932 bytes, SHA-256 `6d6b1c163412e92a221d8b7580e6943eec9818f7e08e894359e84b03fca582f0`. OPRW v29, 367 RVMAT, 50 PAA, puente presente, pond diagnóstico ausente. 420 entradas idénticas a la salida compilada.
- Misión independiente `missions/BalticTest.BalticTrial`, spawn oeste, observador automático a 10 s, economía vacía. Linter 1 script/0 errores/0 avisos y 15 XML parseados. Primera prueba lanzada posteriormente; Mission no confirmada y sonda no recibida. Evidencia: evidence/runtime-first/README.md.

### Contratos y límites

Contrato nativo LOCAL: X=200000+6*col, N=6*(2047-row), diagonal NW-SE en array row-down. La observación UI anterior N=12288-6*row no predice estas alturas. No aplicar un desplazamiento global ni extender la regla a otros tamaños sin evidencia.
Puente vanilla bridge_metal_25, yaw 98.748926, escala 1, centro TB (202417.143,6889.885). Origen absoluto TB 1.476612; origen motor Y=-6.054884 y roadway cruda 8.054884 → tablero 2 m. El export de objetos es relativo; no confundir su última columna con altura absoluta. El WRP demuestra pose persistida; no se inspeccionó el selector de modo de altura tras reabrir.
Ocultar pond en Buldozer NO lo excluye del WRP. Se eliminó solo su registro de 85 bytes en la copia de build; terreno/materiales/puente conservados byte a byte. Original nativo intacto. Binarize aceptó la copia; falta el juego.
Agua consultada: mar=true, pond=false; nivel observado 0.54377 m. GetWaterDepth se consultó a Y=0, no mide aquí hasta el lecho. Agua elevada pendiente. Dos crashes con pond visible, tres cierres normales oculto; mecanismo no aislado. Cuatro→seis materiales no corrigió manchas negras. Comparación vanilla acotada a config y modelo pond, no a todos los recursos.

### Continuación

Leer `product-spec.md`, plan Gate C e `evidence/playtest/README.md`. Acceso recuperado y worker recargado; entorno libre tras primer run. Se usó el arnés registrado DayZ_MCP con mod adicional y misión propia, sin cambiar políticas. Lanzar/adoptar/cerrar solo el run propio según runbook. Hash del PBO realmente desplegado antes de atribuir resultados al source.
Prueba: carga de mundo BalticTrial, compilación cliente/servidor, sonda completa, cruce a pie/vehículo, render y nado/salida. CE, navmesh, población regional, agua elevada y carga 80–100 son gates distintos. No hay rendimiento acreditado ni hardware confirmado.

### Recuperación y antecedentes

Fuentes originales fuera de OneDrive, ruta/hash en README. Artefactos grandes ignorados en Git y preservados por paquetes con manifiestos; commit no sustituye backup. El nuevo paquete de playtest conserva PBO, misión y entradas del build; el proyecto TB completo requiere el checkpoint Narva anterior y el regional previo. Sin remoto ni publicación.
`build-isolated/` contiene junctions DZ/bin/core solo para resolver dependencias de lectura. No borrar recursivamente esas raíces ni copiarlas como datos del proyecto. El build con -project=P:\ falló por escanear configs ajenas; el build aislado pasó. Exit code 0 de AddonBuilder no basta: exigir artefacto, log y contenido comprobado.
Antecedentes: `evidence/tb-import/informe.md`, `evidence/tb-registration/informe.md`, `evidence/narva/informe.md`; estado actual de compilación en `evidence/playtest/README.md`. La observación UI histórica y sus ensayos permanecen documentados; el registro nativo local es la referencia numérica actual en Narva.

### Primer arranque real después de recuperar acceso

Ver `evidence/runtime-first/README.md` y `first-run.json`. Despliegue del PBO por hash, file patching desactivado. Run 25d45413-a1d7-465a-98f1-86cf5ce7b14b lanzó servidor/cliente, pero no pasó carga de misión: aviso navmesh y ErrorMessage minidump. La guía permite terreno sin navmesh; causa exacta pendiente, no conclusión de que el .nm por sí solo resuelva todo.
Cierre por tool oficial, método forced_kill, exit_metrics_valid=false. Sesión final none, caja libre, cero pendientes, cleanup sin degradación. No dejó procesos ni lease propios. Config Navmesh y generación propia pendientes; la interfaz pública de lanzamiento no expone -startNavmeshDataServer. No lanzar por un canal alternativo ni modificar la infraestructura compartida silenciosamente.

### Avance de render y agua — estado actual

Manchas resueltas en el ensayo mediante canales TerrainX completos; seis materiales y TerrainSNX no fueron remedios. Fuente: evidence/render-water/README.md. Buldozer confirmó 44 puntos de tierra inundados y rango mar0.5..1m. Candidato local importado: todas las alturas dentro de 5,01 mm, puente sin desplazamiento, materiales sin campos vacíos. En la zona interior seca (70933 vértices), los 28278 que no superaban 1 m pasan a cero; altura mínima 1,25 m. Esto es validación geométrica, no medición posterior de agua. Los canales estrechos y las orillas requieren revisión del motor. No repetir la sonda basal.
Nuevo ASC nativo SHA `7832f0a9d05cb472bc419bd6600b3034b07832b14e55e0a86fe1bf6d10c9d5dc`; WRP SHA `6b0859fd71aeb76182754f3cf14a541beac1568beb8021d5fc337f604db391eb`. PBO con materiales y agua: SHA `e3e6b3614301950f423bf55f1819cdd4bef9743e3323f29d7669ce5a66251283`, 24743067 bytes; no desplegado. Prueba negativa: el WRP antiguo falla frente al ASC nuevo (error máximo 1 m, exit1). El verificador ya no dice REOPENED sin evidencia externa.
Las sondas temporales para el recheck se retiraron por hash tras el bloqueo de carga; no hay log posterior. Ese intento F10 quedó supersedido por la sonda automática ejecutada; no reinstalarlo. No cerrar/adoptar Buldozer por MCP ni saltar el rechazo de la ventana dwm mediante otro canal. Respaldo previo conservado SHA2a3f171e...; entregable actualizado contiene también el estado posterior.
Dos runs navcfg/navempty no cargaron Mission, cerrados por MCP. Último PBO desplegado navempty hash e4b07860..., candidato nuevo materiales hash92ea247b... todavía sin desplegar. Autorización NavMeshGenerator pendiente tras rechazo automático explícito. La prueba de agua sigue siendo independiente de ese bloqueo.
Reapertura: `evidence/render-water/reopened/`. Muestreo geométrico de 1,5 m dentro del agua OSM, mismo candidato: retroceso máximo muestreado 5,58 m a plano0,5 m; 2,28 m a0,75; 0,25 m a1. No hay pérdidas muestreadas a más de12 m del borde. No acredita conectividad de canales ni agua del motor. Revisar estos bordes antes de extender el candidato. No se ha modificado el terreno en esta continuación. Sondas temporales reinstaladas y después retiradas comprobando hashes al quedar pendiente el control; ensayo F10 cerrado y supersedido por la sonda automática.

### Exportación reabierta y Steam — continuación más reciente

La exportación posterior ya pasó: `evidence/render-water/post-reopen/`. Las alturas, índices y tabla de materiales, y cada registro de objeto son idénticos a los de la exportación anterior; el hash total difiere por orden y terminador. Respaldo suplementario `outputs/baltic-render-agua/narva-reapertura-exportada.zip`, SHA `6dacafe0bb2c6626a10b493977ec10e5470c56c3d65475d2530aba4f701c8f22`, CRC y WRP verificados. No reemplaza el checkpoint del proyecto completo.
Buldozer 17:24 mostró «Unable to locate a running instance of Steam» antes de cargar scripts. Steam real PID196052 y registro host correcto; la lectura local de Codex daba PID40860 y otro ActiveUser. Comparación por StdRegProv y lectura local, sin exponer identificadores de cuenta. A petición del usuario se respaldaron y sincronizaron únicamente pid/ActiveUser de la copia local con los valores actuales del host; comprobados host y proceso sin cambios. No reinicio de Steam ni edición de DayZ_MCP. Esto acredita reparación del registro visible, pendiente de prueba de arranque. Backup privado en `work/steam-registration/private-values-before.json` del workspace; no exportarlo.
Steam UI fue rechazado por revisión automática incluso después de autorización explícita. La investigación del registro es una petición posterior del usuario. No reintentar UI de Steam sin cambio del canal. El helper de preflight del skill actualmente falla al parsear su línea 213; comprobadas las rutas necesarias directamente y sin editar el skill.
En ese momento histórico se instalaron sondas temporales, ya retiradas: `P:\scripts\buldozer.c` SHA `ef0964dcb9ad22be42cca673b7dc508fec76cc7483a2a32b56d5c475ecdfe4a8` y `guill.c` SHA `f3a0034023771e13f432d98033d87c0652077bf12df6807c554349fd4d110999`, destino nuevo `$profile:baltic_water_observer_after_v1.log`. Recoger antes de retirarlas; retirar solo por hash coincidente. No hay log posterior todavía. Se pidió al usuario Connect y F10 porque los clics automáticos no producen un nuevo proceso/log. No atribuir ese no-arranque a fallo posterior de la reparación de Steam.
Resultado posterior: conexión desde menú Tools, Buldozer PID219340 iniciado 17:34:21 con padre TB208720. Terreno visible y aviso Steam ausente. `steam-consumer-startup.json` documenta la prueba. No se aisló qué valor de registro individual provocaba el error ni se demuestra reparación permanente tras reiniciar/cambiar sesión Steam. La primera respuesta manual de carga/F10 no produjo log ni proceso observable en aquel momento; tras observar esta carga real se volvió a solicitar F10. Sigue sin archivo y no hay medición posterior aprobada. No hay lease/run MCP propio; este Buldozer externo ocupa la caja.
Último diagnóstico: Guillermo confirmó F10 con el visor cargado y sigue sin archivo. `observer-dispatch.json` y snapshots del RPT/script log: World/Mission cargados, no `Module: BuldozerModule` (sí aparecía en la prueba basal). Preferencias TB/Buldozer observadas: ambas carpetas de datos P:\, nombre de lanzamiento Buldozer; UABuldRunScript=kF10 en perfil. Ambos scripts tienen encabezado/ruta/hash esperados. Preferencias cerradas con Cancel, sin cambio. No clasificar como fallo del algoritmo del agua; ejecución de la sonda aún no observada. Se pidió un único discriminador de foco, clic en título y F10 mantenido 1s; no operar ventanas mientras el usuario lo hace. Si falla, cambiar estrategia sin pedir más F10 iguales. Buldozer responde y queda abierto; sondas presentes para esta prueba, con recibo de hashes. MCP self none, owner null, pending0, cleanup vacío, presencia externa Buldozer (no adoptar).


## Estado archivado: cierre previo a reinicio, sustituido por orillas y consumidores (03-10)

```text
<!-- LIVE-STATE:START -->
project: DayZ_Baltic_12km
updated: 2026-10-03
owner: Codex ejecutor/integrador. Guillermo pide terminar el bloque en curso y dejar handoff completo para reiniciar el PC. La ventana autónoma anterior de ocho horas terminó; no arrancar otro bloque ni reactivar el recordatorio. No equivale a mapa completo.
status: V30_CONTINUITY_NAV_GENERATED_ENGINE_GATES_FAIL_NATIVE_SAVED; 03-10, cierre previo a reinicio. NM propia generada, empaquetada y cargada. 37 controles del grafo PASS pero cinco alturas fuera de tolerancia. 1332 lecturas completas,13 mojados con profundidad no positiva. Base1.0 todavía NO aceptada.
plan: plans/v30-continuity-native-runtime-resume.md actualizado con lo ya ejecutado y pendientes; deriva del plan water-ground-rebuild-v1 aprobado02-10. Terminar bloques y verificar al final. Ahora cierre/handoff por petición viva; retomar solo después del reinicio y nueva indicación.
candidate: NPZ40d8cfd9 / ASCdacc8e55 en E:/DayZ-Baltic-Build/v30-watercourse-continuity. NUEVO v30-continuity-nav-package: mundo302b000b, agua339fa17f, WRP0255d007 intacto, NM43916629 propia. Mod aislado @DayZ_Baltic_ContinuityV30_Nav. Original dedup e556f576 con NMV29eb0f131e conservado; otras6826entradas byte-identicas. No promover sobre @DayZ_Baltic_DeltaV30_Nav 916948ec/NMeece8e5e ni canónico69140d41/NM24baf069; paquetes anteriores572d4124/371ece8a tambien conservados.
terrain: Acabado73b01bb4, 49.717 vértices de orillas; lagunas2f954ad5, 75 alturas; continuidad40d8, 22.468 alturas adicionales. Incrementos pueden solaparse. Cero caras >35 grados nuevas/empeoradas; inventario mixto4149→4000. 23 canales, ingeniería y naturaleza seca fijos; 712 fondos ya mojados de naturaleza ajustados. 76.536 estaciones viales históricas/100cadenas PASS. Gate legado de Narva FAIL explícito por cuatro lagunas; ámbito local comprobado.
water: 17.637 instancias/8.775 modelos tras retirar4.659 duplicados exactos MLOD y ODOL; PBO34.254.192→24.715.347bytes. Poses, geometría, UV y nueve puentes idénticos; sin medición de FPS/RAM. Recuperadas cuatro lagunas aprobadas omitidas por el círculo de Narva. En ejes no reservados quedan30m secos de río y399,5m de arroyo; profundidad<5cm42/511m; laterales y halo de cruces reportados aparte. Autoconsistencia, no prueba del motor.22cortes >=6m localizados; intento conjunto en9grupos sin solución admisible, cero cambios, no repetir solver.
surface: Superficie40d8 regenerada a1m/px,1024tiles/2048PAA/4775materiales; PBO6827entradas. Fuentes12288² en editor-v30-delta/world/native_sources_continuity,3968solapes exactos. TB guardado14:00:26Madrid, TV4P2fa6d30b/raster0243ca028c7; biblioteca dedup copiada05c00add. Instancias, rebuild, fuentes finales y doble export/reapertura pendientes. WRP1a9cf270 solo referencia esperada. V4 headless ejecutada; siete vistas no ejecutadas.
decisions: 02-10 agua natural y relieve mezcla aprobados. 03-10 P15: red ferroviaria alrededor del mapa, radiales/bifurcaciones, tramo real por San Petersburgo para su estacion emblematica; solo alcance futuro, NO ejecutar ahora. Nuevo ritmo: completar cada bloque y validar al final, sin rechecks ni cierres documentales repetitivos; regla en CLAUDE.md.
runtime_current: 3d93327f genero43916629 en8m16s;453413960bytes;966289teselas/1138559poligonos/4087160vertices; estructura PASS.944442f7:37controlesgrafoPASS,FAILvertical5puntos0.851715–1.153181m frente0.801m.7971ec26:1332alturas maxerror0.000571102m,463secosPASS,13mojadosFAILsoloGetWaterDepth<=0; todosSurfaceIsPondtrue/planoesperado. Sonda Formula too complex corregida y compilada; no acepta visual,actor ni80–100jugadores.
runtime_previous: 45e5b57c:1682lecturas/3vistas PASS; d115461b:NM966289teselas/8m55s; 5c1e4734:13consultas PASS; 16fe4ad8:4viajes Neva PASS/2269muestras. Luga d0f7811a6/8; único discriminador0428d12b4PASS/5FAIL solo reloj0.929s. Todos los criterios físicos PASS, presupuesto temporal consumido. Es evidencia del paquete anterior, no del candidato40d8. Run propio posterior649d61b4 terminado ordenadamente tras interrupcion, sin resultados aceptados.
visual: Laguna y Narva sur observadas sin menú en A 90806e21 y B d4e404f6; ambos END2 y orderly_close. B es @DayZ_Baltic_ShorePilot: mejora talud pero deja franja somera oscura, NO PROMOVIDO. Cámara con diferente inclinación, comparación cualitativa. @BalticVisualUIProbe compiló/ejecutó END_NO_PAUSE_MENU; no demostró activar Continue. BALTIC-001/007/009/010/011 abiertos. camera_set no usado.
load: BALTIC-008 POSPUESTO a un sector mapeado (Guillermo, 02-10). El run ebffaa12 queda INCONCLUSO.
backup: E:\DayZ-Baltic-Archive\checkpoint-v29-2026-10-02 (115.770 ficheros, 16,0 GiB, PASS) y workspace-variants-2026-10-02 (356.538 ficheros, 41,8 GiB, PASS). SHA-256 comprobado en origen y destino. Nada borrado de C:.
git: Rama v29-base, arranque c93e77f2. Implementación/evidencia en edea2e7; plano legible en77f208a. Cierre documental posterior: consultar HEAD real y recibo en la sesión del vault. Conservar no seguidos anteriores y grandes artefactos en E:. Sin remoto, master4ff154b intacto.
env: Python GIS en C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env. Entorno DayZ verificado manualmente al retomar; helper generico preflight.py falla al parsear por unicodeescape en linea213, sin ejecutar comprobaciones. Preflight del launcher y linter de mision PASS por separado. Espacio C: fluctua; salidas grandes en E:. No limpiar build-temp/junctions ni archivos no seguidos.
runtime_lock: Todos los runs propios cerrados orderly_close:3d93327f generacion,944442f7 caminos,7971ec26 lecturas. Session_status final ownernull/selfnone/pending0/queuevacía/boxoccupiedfalse/runs[]/foreign[]. TB guardado y cierre normal solicitado; cierre de proceso comprobado al finalizar. No dejar generador, lease ni ensayo de fondo. El600s de takeover solo aplica a runs registrados abandonados, no a LFH2R manual; ver takeover-diagnosis.md. No culpar a permisos: CU funcionó pero TB respondió con grandes retardos y No responde transitorio.
next: Tras reinicio, reanclar WorkDrive/junctions y leer nuevo handoff. Reabrir base_v30_shorefinish.tv4p guardado, revisar raster/biblioteca sin duplicarlos; importar sonda única de origen, verificar matriz antes de17636instancias, sustituir agua vieja conservando9puentes, reconstruir marco/superficies, guardar/reabrir/exportar y comparar. En paralelo sin UI: discriminador acotado de13 puntos de profundidad y consumidor físico para5 alturas NM. No regenerar NM ni relajar gates por el FAIL numérico solo.
ftt: E:/DayZ-Baltic-Build/ftt-pilot-v1; P:/baltic_ftt_pilot junction a project. Ejecutable1.0.5 SHA b15f532f; export ca1776da, 16asf1_25+1asf1_0 2000, height0 por validar relativo en TB. Fuentes intactas; ajuste de terreno OFF. Bibliotecas requieren seleccionar carpeta explicita; XML con bbox placeholder. Evidencia evidence/ftt-pilot-2026-10-03. Sin prueba de curvas, conduccion, suavizado, vegetacion o NM. No dependencia productiva.
offline_candidate: E:/DayZ-Baltic-Build/v30-watercourse-continuity/terrain_v30.npz SHA40d8cfd9874e9260464f9e3c38c07d81a15c8aed374083a52c98f042c0161c2e. Toda evidencia del bloque en evidence/v30-shore-continuity-2026-10-03. Las variantes f27/73b/2f quedan preservadas; no retomar la primera por mtime.
handoff: C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-navmesh-y-reinicio.md es el relevo vigente. Evidencia evidence/v30-continuity-nav-2026-10-03. Antecedentes takeover-y-reanudacion, sesion-ocho-horas y handoff completoV30 conservan decisiones e historia. Skill navmesh-bootstrap actualizada con CLI completa y limite de concatenacion. Recordatorio anterior pausado;0resets usados en este bloque.
<!-- LIVE-STATE:END -->
```
