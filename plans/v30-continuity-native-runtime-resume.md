# Continuación concreta del paquete de continuidad

Preparación del 03-10, dentro de la sesión de ocho horas. Estado y cualquier
avance posterior: HANDOFF. No usar una variante por ser la de fecha más reciente.

## Estado posterior — cierre de orillas y consumidores, 03-10

Esta actualización sustituye el estado anterior, que se conserva debajo como
antecedente. Relevo: `C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-orillas-editor-y-consumidores.md`.

- Consumidor físico de los cinco avisos de NM: **12 recorridos PASS**, ambos
  sentidos y control, run2f0c6b76; se conserva el FAIL numérico anterior.
- Serie temporal del agua:17puntos×151muestras/301s, run5b19c193. Pond presente
  en los13someros; oleaje expone el lecho. Orden de consulta afecta al plano sin
  ola. Mecanismo interno sin aislar; diagnóstico y primer ensayo rechazado guardados.
- Parche local `v30-wave-margin-constrained`, NPZd5dadae8/ASCed3b12f2:
  **PASS offline**,126vértices,463secos/23canales/76.536estaciones viales.
  No importado, empaquetado ni ejecutado. Requiere navmesh propia al integrarlo.
- El editable contiene40d8 y17.637aguas+9puentes. Rebuild antes de reimportar
  Absolute: corrige el desplazamiento de hasta25,86m; residuo máximo de agua
  0,000000476837m. No importar otra vez el CSV completo sobre este proyecto.
- Guardado y reapertura con export independiente: alturas, materiales y poses
  exactos respecto al export anterior; terminador distinto. Comparador estricto
  conservaFAIL. No equivale a aceptación de superficies ni del paquete nuevo.
- Estado final de la integración de superficies y proceso TB: handoff canónico.

La receta siguiente es histórica. Sonda de origen, importación completa,
Rebuild y save/reopen ya ejecutados: **no repetirlos por leer sus casillas antiguas**.

## Histórico: pruebas del 03-10 y cierre antes del reinicio

La generación por consola y el empaquetado ya terminaron. Estado vigente:

- `@DayZ_Baltic_ContinuityV30_Nav`: mundo302b000b, agua339fa17f,
  WRP0255d007 intacto y NM43916629 propia (453.413.960bytes,966.289teselas).
- Run944442f7:37 controles del grafo PASS, pero cinco puntos superan la
  distancia vertical local0,8m. Resultado global **FAIL_LOCAL_CONTINUITY_NAV_PATHS**.
- Run7971ec26:1332 alturas correctas (máximo0,0005711m de error),463 controles
  secos PASS;13 puntos mojados dan GetWaterDepth<=0. Todas esas piezas sí devuelven
  SurfaceIsPond=true y el plano sin ola esperado. **FAIL_SHORE_ENGINE_READBACK**.
  Distinguir ola/profundidad instantánea de ausencia de pieza; causa no aislada.
- La concatenación V4 fue corregida tras `Formula too complex`; headless compiló
  y completó END_READBACK;1332. No cambiar referencias o tolerancias retrospectivamente.
- TB guardado14:00:26Madrid: ASC añadido como raster y biblioteca deduplicada
  copiada. Rebuild del mapframe, importación de instancias, superficies y export
  siguen pendientes. La referencia WRP esperada NO es un export nativo.
- Runs propios cerrados orderly_close y lease liberado. No arrancar nada para
  el reinicio; al retomar observar estado nuevo, no reutilizar PID/lease.

Evidencia: `evidence/v30-continuity-nav-2026-10-03/`; handoff canónico:
`C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-navmesh-y-reinicio.md`.
Las secciones siguientes conservan la receta y el estado de preparación original;
esta actualización determina cuáles de sus pasos ya se ejecutaron.

## Identidades preparadas

- Terreno: `E:/DayZ-Baltic-Build/v30-watercourse-continuity/terrain_v30.npz`,
  **40d8cfd9874e9260464f9e3c38c07d81a15c8aed374083a52c98f042c0161c2e**.
- ASC al lado: `baltic_terrain_v30.asc`,
  **dacc8e553ed70d1828d7c6bcf755533953765c09f730601dae1a6557c1a01431**.
- Paquete `E:/DayZ-Baltic-Build/v30-continuity-dedup-package/out/Addons`:
  mundo **e556f5763c552a890975e57841edc88e1f76406a5840657232030eb16c97159a**;
  agua **339fa17f26c9ec7a47fca59f621447ef44dbc1212b7c654cc4f88e51dca24b13**.
- Copias comprobadas en `P:/Mods/@DayZ_Baltic_ContinuityV30/Addons`.
  WRP compilado **0255d007d173efbd88832a0193725af843a3ba930ea360112b4f98737d650dd2**.
  Este paquete original conserva NM V29 **eb0f131e** provisional. El nuevo
  `v30-continuity-nav-package/Addons` lo sustituye por43916629 sin rebinarizar.
- Misiones `BalticV30ShoreFinishV4.BalticTrial` y
  `BalticV30ShoreFinishV4Headless.BalticTrial` en la carpeta mpmissions de DayZServer.
  Referencias de 1.332 puntos en `v30-continuity-dedup-package/runtime-fixture*`.

## Bloque nativo al recuperar Computer Use

El archivo guardado es `editor-v30-delta/native-asc/base_v30_shorefinish.tv4p`;
contiene el raster nuevo, pero su mapframe final no se ha reconstruido/exportado.
Reabrir ese proyecto y observar el estado; no asumir diálogos pendientes.

1. Trabajar en esa copia. Comprobar el ASC ya cargado, conservar marco2048²/6m y
   origen de ingeniería200000/0. No modificar recorte, resolución ni escaladoZ.
2. Preparar el enlace `P:/baltic_water_v30` hacia
   `E:/DayZ-Baltic-Build/v30-water-deduplicated/source/baltic_water_v30`.
   **Ya apunta a ese destino deduplicado.** El enlace anterior está conservado
   como `P:/baltic_water_v30_pre_continuity_20261003`. Reanclar tras el reinicio;
   no sustituirlo otra vez ni borrar su contenido.
3. Biblioteca en `editor-v30-delta/water-import-continuity-dedup/Baltic_Water_V30Dedup.tml`:
   8.775 plantillas `v30d_*`, ya cargadas y copiadas en TemplateLibs del proyecto.
   No duplicar la biblioteca. En capa nueva, importar únicamente
   `origin-probe/01_water_probe_absolute.txt` con altura absoluta.
4. Exportar una prueba nueva y comprobar la matriz del único
   `baltic_water_v30/edge_00000.p3d` contra `origin-probe/probe.json`.
   Centro del modelo desplazado16,98m: discrimina un doble autocentrado.
   Si coincide, importar `02_water_remaining_absolute.txt`, 17.636 filas.
   No importar además el CSV completo. Reemplazar la capa de agua vieja sin
   retirar los nueve puentes; ocultar una capa no demuestra excluirla del WRP.
5. Fuentes en `P:/baltic_editor_v30_delta/native_sources_continuity/`:
   `satellite.png`, `mask.png`, `layers.cfg`, `legend.png`. Marco conserva
   1m/px, textura512px, solape128 y capa48m del contrato comprobado.
6. Guardar, exportar, reabrir y exportar otra vez. Referencia esperada de prefijo
   local: `editor-v30-delta/native-reference-continuity-dedup.wrp`.
   `tools/terrain/verify_v30_native_editor.py:13` compara alturas, materiales,
   todas las poses/modelos y terminación, y reporta IDs aparte. Si el editor
   genera nombres/materiales distintos, diagnosticar antes de cambiar ese gate.

Estado histórico: esos pasos estaban pendientes. Consultar la actualización al
principio antes de ejecutar la receta. No editar TV4P/TV4L como binarios.

## Lecturas y navmesh al quedar libre DayZ

La ocupación externa de LFH2R terminó y los tres runs de esta sesión pudieron
arrancar. El reloj600s no aplica a procesos fuera del gestor. Detalle y evidencia
en `evidence/v30-shore-continuity-2026-10-03/takeover-diagnosis.md`.

[EXACT] Petición que pasó preflight, cambiando `preflight` a false solo al poder
arrancar por el lifecycle normal: project `DayZ_MCP`, mode `server`, mission
`C:\Program Files (x86)\Steam\steamapps\common\DayZServer\mpmissions\BalticV30ShoreFinishV4Headless.BalticTrial`,
extra_mods `[@DayZ_Baltic_ContinuityV30]`, base_mods vacío, no_base_mods true,
no_file_patching true, build/clean/pack_only false, navmesh_data_server true,
server_wait_s60. La ruta de misión es absoluta: solo el nombre fue rechazado.
Contrato local: `DayZ_MCP_dev/tools/dayz_mcp/dayz_test_request.py:373`.

Después del run propio, adquirir lease para operar el generador y renovarlo
mientras dure. Wrapper `tools/navigation/generate_navmesh_console.py:32`,
exe y argumentos comprobados; run3d93327f ya generó la NM en8m16s sin Computer Use.
No repetirlo sin un cambio de terreno/objetos o un diagnóstico que lo justifique.
Leer `baltic_v30_shorefinish_v4_headless.log` y exigir `END_READBACK;1332`.
Consumidor: `tools/playtest/verify_shorefinish_v30.py:10`, con referencia V4 y
los hashes efectivamente desplegados. Un estanque oculto por mar puede quedar
INCONCLUSO; no convertirlo en PASS por una profundidad positiva.

Al generar NM: inspección TESM6 completa, y `tools/playtest/attach_navmesh.py:69`
con el **mismo PBO que alimentó el generador**, WRP0255d007 y reemplazo autorizado
NMeb0f131e. FileBank sin rebinarizar el mundo. Después carga/consultas útiles y
las vistas V4 con jugador próximo, sin `camera_set`.

Consumidor copiado a mpmissions y ejecutado en944442f7:
`missions/BalticV30ContinuityNavV1.BalticTrial`, referencia en
`v30-continuity-dedup-package/nav-fixture/reference.json`. Son37consultas:
13históricas que no necesitaron cambiar ninguna Y y24recorridos nuevos en bancos
secos modificados. Linter PASS(1archivo); lector:2positivos/15negativos aceptados
y rechazados respectivamente. `verify_continuity_nav_v30.py` conserva los
controles de completitud y separación del delta, compara el suelo leído contra
40d8 y reporta distancia vertical navmesh/superficie física. Umbral diagnóstico
local0,8m, sin aceptación global ni locomoción real. Copiar la misión bajo lease
al cambiar el código; registrar hashes del nuevo PBO/NM al arrancar.

Cerrar únicamente el run propio por run_id, liberar lease y consultar estado.
Lecturas, apariencia, navegación, locomoción y rendimiento son resultados separados.
