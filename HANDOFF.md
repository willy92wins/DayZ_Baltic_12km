# DayZ Baltic 12km â€” handoff

<!-- LIVE-STATE:START -->
project: DayZ_Baltic_12km
updated: 2026-10-27 (Nav8 funcional publicado; Nav12 rechazado; control RAM12,5 completado)
owner: Codex, ejecutor e integrador por petición viva de Guillermo: continuar OT1 y EV112 hasta completar las pruebas autorizadas. Plan aprobado plans/ev112-plan-astra.md; decisiones del picker incorporadas en la sesión canónica.
status: EV112 abierto. F conserva 59 picos/12 depresiones corregidos y corrige una transición rectangular. Quedan268picos,1144depresiones,4transiciones. Colisión C, bosque muestreado y 11 secciones de carretera pasan motor; vista/cliente/global pendientes.
plan: plans/ev112-kit7-navv9-ram-diagnostic-20261027.md. Medir el control original12,5 antes de otra generación; diagnóstico separado, cuatro FAIL preservados. Sin rebajar tolerancias.
candidate_f: F mundo4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38; terreno33d6f2713800bd07f3e20ca80870423a8a41c16b7408492d6f705f3fbffe9049; mergedcaa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc. E exacto+94vértices,59árbolesY. 4749controles físicos PASS; F original NM6 conservado, CNav9 validada aparte. Bosque3727/269968 SAMPLED_BOUNDARY_CLEAR; no disco continuo.
candidate: E:/DayZ-Baltic-Build/shape-repair-20261025/guarded-relief-batch-e: terreno efbf0c18b1144ee401d983e4f64e2a35b489c69ae5f333524fdc66fbbf4714f9; merged705196d69646f2528aa5796d26e90bab36aebd07a5a0ddb861b31b7160f4a33e. StageE WRPfuente85b2d03dded38382d9deaa01cfc1a36b996087ce2d7e8cadeb8f07c135894887. PackageE verifica2578725objetos/62poses; mundo3a285df12e565373d678997aedb9b51f65f11cdbb0f24939da3b8ce77712231a. BaseT y candidatoD preservados.
pilots: EV111 V2 @DayZ_Baltic_EV111_ForestPilotV2 (mundo ee4bd96eâ€¦, E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev111/r2/BUILD-EV111-r2.md); EV111 V1; EV110 @DayZ_Baltic_EV110_LatticeShoresV1 mundo 226932e3â€¦, agua 46e63c70â€¦ (terreno ev110/terrain-ev110.npz d25e9428â€¦, cadena evidence/â€¦/ev110/BUILD-EV110.md); EV109 7ad4d6cfâ€¦; EV108 V7 389e27a6â€¦. Build E:/DayZ-Baltic-Build/v31-pond-layer-20261013; trabajo de EV112 en ev112-wip/; relevo en handoff-20261018/ (MANIFEST.json).
previous: EV103 441dfda9â€¦, EV102 4d572a76â€¦, EV101 470cceceâ€¦, EV100 21e7f71dâ€¦, EV99 fb8893a4â€¦, EV98 4330c9a2â€¦, EV97 546bdcfdâ€¦, EV96 b12fe58câ€¦, EV95 f1a148caâ€¦ (Astra), B b11c825bâ€¦ referencia.
water: agua de dos colores = charca sobre fondo bajo el mar del motor (EV96: fondos a 1,0 m, tramos bajos convertidos en mar). Capa v31: una pieza por tesela de 48 m y banda de 25 mm, verificaciÃ³n exacta por medias celdas. Kit: lÃ¡mina visible plana de 14 Ã— 24 m y cara `water_ext` de 14 m; solo la V del terreno la recorta (asiento de Chernarus âˆ’0,33/+0,70/+1,81 a 0/3/6 m); el motor da agua del kit con â‰¥0,10â€“0,15 m bajo su suelo.
relief: EV97: suavizado Ïƒ 12 m solo de tierra seca; reserva, plataformas y Narva fijas. Rejilla de 6 m con diagonal NO-SE (igual que Chernarus a 7,5 m).
focus: el cliente sin foco al cargar abre el menÃº de pausa (cielo morado, terreno sin texturas) hasta que Guillermo hace clic en la ventana y pulsa Â«ContinuarÂ».
blocker: Nav8 cierra los cuatro fallos y pasa607, pero falla RAM1.26591/1.24133. Nav12 introduce tres alturas nuevas0.856856/0.923148/0.818588 contra0.801 y queda rechazado. No se ejecutó RAM12. Visual,actores y global siguen pendientes.
validation: Kit7 fuente2578398objetos y201modelos; G2/G3/G7/G8 y carreteras offlinePASS. Motor propio11052alturas/0fallos (3430vértices+7622centroides, máximo0.0001861622m); frontera3727/269968 SAMPLED_BOUNDARY_CLEAR,3categorías0.19tests; Fable5.1 revisado y corregido. No aceptación visual/global.
cleanup: Los seis runs propios del control RAM12,5 cerrados oficialmente y leases liberados. Generación/sonda Nav12 y Nav8 también cerrados. Automatización anterior PAUSED; siguientes lanzamientos por FIFO.
performance: Control kit7original de 12,5 DIAGNOSTIC_ONLY: PASS_EMPTY_SERVER_RAM_BUDGET, seis ABBAAB nuevas,sin repeticiones. Residente 2787.18/3348.65MiB ratio0.832329; privada 3151.58/3731.24MiB ratio0.844646. Conserva4FAILaltura. Nav8funcional conservaFAILRAM1.265913/1.241333. SinFPS/capacidad.
bugs: bugs.md una fila por ID: 007 (orillas en escalera; kit EV108), 015 (puentes; EV109), 017, 018, 019, 020. Historia en bugs-history-hasta-2026-10-10.md.
next: Replantear una única variante funcional motivada con el control RAM12,5 ya medido; no generar otro ancho por el estimador de dos diagonales. Mantener607consultas y tolerancias0.801/0.011/2.1; nuevo paquete necesitará su propio RAMABBAAB. No aceptación global.
git: GitHub público https://github.com/willy92wins/DayZ_Baltic_12km. Historial público saneado independiente en E:/DayZ-Baltic-Build/shape-repair-20261025/public-repo; historial local completo conservado. No publicar ramas locales ni usar --all/--mirror; ver PUBLICATION.md.
handoff: evidence/performance/kit7-navigation-12p5m-diagnostic-ab-20261027/README.md; Nav12FAIL en evidence/navigation/kit7-nav12-rejected-20261027; Nav8funcional y RAMFAIL intactos.
deployed: Nav8 funcional conservado; Nav12 af12bfe3ed48c6d436ed2f22bf8057d28a8e96d2de402ef3c36ae09862bfc87d rechazado; NavV9 original a2919a80ae6da6fc90e75b0ac55d1e9dd4ba4a39f6700b9fec237c7e7683b16c restaurado por hash solo para diagnóstico.
visual_probe: C conserva4749+300físicaPASS; NMpropia CNav9 y45consultas/8rutasF PASS en servidor normal. Ninguna cobertura de actor ni tránsito por25modelosC. Sincliente/vista/CCT/FPS/capacidad. E+Nav9 anterior conservado.
council: Fable5.1, Grok4.7, Gemini4ArgonHigh, Muse Wonder1.0 CLI nativo, GLM5.3FlashEXL3 y Qwen3.8. Siete informes de seis familias; Glimmer suplementario. Opus sustituido por Fable por el usuario. Adjudicación y recibos en checkpoint actual.
<!-- LIVE-STATE:END -->

## Leer primero

0. **[plans/ev112-plan-astra.md](plans/ev112-plan-astra.md)**: plan dirigido de EV112 (relevo a Astra del 18-10). Empezar por aquÃ­.
1. Este LIVE-STATE, [la evidencia v31](evidence/v31-pond-layer-2026-10-13/README.md) (EV104â€“EV109R) y
   [los arroyos y el kit](evidence/v31-pond-layer-2026-10-13/streams/README.md); lo anterior en
   [la evidencia del 11-10](evidence/v30-claude-review-2026-10-11/README.md).
2. [bugs.md](bugs.md) (una fila por ID) y [product-spec.md](product-spec.md) (P1â€“P15).
3. Lo anterior a hoy, incluido el relevo de Astra completo, estÃ¡ en [HANDOFF-history.md](HANDOFF-history.md):
   solo informa; no decide procesos, permisos ni estado actual.

## Decisiones vigentes que no se reabren

- Recorte aprobado el 29-09 y una Ãºnica escala XY; no agrandar San Petersburgo.
- Terreno, agua y navegaciÃ³n antes del mapeado (P10). Assets vanilla primero y anchuras a escala humana.
- Relieve selectivo por jugabilidad (P12), rÃ­os para lancha vanilla con puentes elevados (P9), carreteras lisas (P11).
- Agua 02-10: navegables de forma natural y 30â€“60 m de ancho con canal libre de 24 m; rÃ­os con nombre de 8â€“20 m;
  arroyos de 3â€“6 m; delta del Neva con brazos e islas; lagunas desde ~300 mÂ².
- Relieve 02-10: conservar las zonas altas, dejar llanos y el resto mÃ¡s natural, sin el Ã—5 general.
- Orillas 06-10: la v10b es la base aceptada, con su lista de niveles.
- Navegables 08-10: fondo a 1,0 m y calado mÃ­nimo 0,95 m; embarcaciÃ³n de referencia, lancha vanilla.
- **11-10:** el agua no puede mezclar charca y mar. LÃ¡minas â‰¥1,95 m con fondo â‰¥1,0 m; tramos bajos de cauce con
  fondo submarino pasan a ser mar del motor (Guillermo eligiÃ³ Â«convertirlos en marÂ»). Lagos no se convierten.
- **11-10:** el relieve anguloso se trata con una pasada global de suavizado de la tierra seca, no con solvers locales.
- **11-10:** puentes vanilla segÃºn el ancho (metal_25 en rÃ­os, wood_25/50 en arroyos). **14-10:** dos tramos metÃ¡licos alineados
  y wood_50 donde la reserva de carretera no cabe bajo la parte plana del wood_25.
- **13-10:** arroyos estrechos con el kit `streambed` vanilla (lecho 3D, piedras y agua propia), no con la V fina de terreno (que
  escalona los tramos que ya eran lisos); piloto en kit-118 y kit-7.
- Objetivo de 80â€“100 jugadores; hardware del servidor sin concretar.

## Entorno y precauciones

- `P:\` es un `subst` de `C:\Users\guill\OneDrive\Documentos\DayZ Projects` y **se pierde al reiniciar**:
  `subst P: "C:\Users\guill\OneDrive\Documentos\DayZ Projects"`.
- `P:\Mods` = `!Workshop` de DayZ en C:. Solo previews vigentes; las archivadas estÃ¡n en
  `E:\DayZ-Baltic-Build\archived-mods-20261011` (devolverlas copiando la carpeta).
- Python: solo el GIS, `C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe`, con `-I`.
- OneDrive: escrituras grandes en una sola pasada y relectura. Builds en E:; contienen junctions (DZ, bin, core,
  baltic_water_v30): **nunca borrar recursivamente**.
- DayZ MCP: lease antes de mutar; caduca a los 120 s sin llamadas y el daemon retira el run unos minutos despuÃ©s.
  Cerrar con `dayz_test_close`. **Sin `camera_set`** (BALTIC-001). Para vistas: Guillermo delante para el foco.
- **No reejecutar** los `checkpoint_*.py` / `update_*.py` de `evidence/v30-global-bank-extension-2026-10-10/`:
  reescriben por regex este LIVE-STATE y la nota de Obsidian.
- Herramientas de terceros **por probar** (cÃ³digo clonado en `E:/DayZ-Tools-ThirdParty`, sin compilar ni ejecutar): ASCTerrainMixer
  (mezcla de ASC con mÃ¡scara pintada, exporta normales; Ãºtil para capas de retoque de Guillermo o un `terrainNormalTexture`) y
  DayZ Road Studio (fusiÃ³n y trazado de carreteras en `.tv4p`; Ãºtil en la fase de mapeado con Terrain Builder). Detalle, commits
  fijados y lÃ­mites: `C:/Users/guill/.codex/skills/dayz-terrain-workflow/references/third-party-terrain-tools.md`.
- Sondas de servidor sin jugadores: cargar los objetos con `GetGame().GetObjectsAtPosition` en el mismo fotograma antes de consultar
  el agua (si no, no ve las piezas del kit ni las de Chernarus); misiones `missions/BalticKitProbeV1` y `missions/BalticBridgeProbeV2`.
- Cadena de agua: tras cualquier cambio de terreno o envolvente, `bury_edges_v31.py` y usar la **Ãºltima** huella de su carpeta de
  trabajo (`fpN` mayor) para la autorÃ­a; un pase que entierra un borde cambia el terreno respecto a `fp0`.
- Los extremos y cruces del kit y de los puentes estÃ¡n en las cabeceras de `tools/water/streambed_kit_v31.py` y
  `tools/terrain/bridges_v31.py` (cada regla con el defecto que la motivÃ³).
- GPU: el equipo tiene una AMD integrada (512 MB, estado Â«ErrorÂ» en Windows) ademÃ¡s de la RTX 3090; Guillermo fijÃ³
  `DayZDiag_x64.exe` en Â«Alto rendimientoÂ» el 11-10.

## Reconstruir EV96 y EV97

Con el Python GIS, scripts en `tools/terrain/` y `evidence/v30-claude-review-2026-10-11/scripts/`:

1. `water_piece_bbox.py` â†’ `E:/DayZ-Baltic-Build/v30-water-two-colour-fix-20261011/water-piece-bbox.npz`.
2. `tools/terrain/fix_two_colour_water_v30.py` â†’ `terrain-ev96.npz`, WRP editable y `stage-report.json` (exige salida nueva).
3. `compile_world.ps1` de esa carpeta (AddonBuilder) y `package_ev96.py` (FileBank, solo cambia el WRP).
4. `tools/terrain/smooth_dry_land_ev97.py terrain-ev96.npz terrain-ev97.npz 2 --report smoothing-report.json`,
   despuÃ©s `stage_ev97.py`, `compile_world.ps1` de `v30-dry-relief-smoothing-20261011` y `package_ev97.py`.

## Reconstruir EV108 y EV109

Python GIS con `-I`; salidas en `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/`; scripts de empaquetado y compilado en
`evidence/v31-pond-layer-2026-10-13/scripts/ev108-ev109/` (usan `build_bisect.py` de la misma carpeta y la base EV95 de P:/Mods).

1. Kit: `tools/water/streambed_kit_v31.py bridges/terrain-ev107.npz bridges/fp-ev107/footprint.npz
   E:/DayZ-Baltic-Build/v30-shore-sdf-20261011/cover-level-ev98.npy bridges/envelope-ev107.npy ev108-kit/sites.json
   ev108-kit/terrain-kit.npz ev108-kit/cover-ev108.npy ev108-kit/envelope-ev108.npy ev108-kit/kit-records.json ev108-kit/kit-report.json`.
2. `tools/water/bury_edges_v31.py ev108-kit/terrain-kit.npz bridges/terrain-ev107.npz ev108-kit/cover-ev108.npy
   ev108-kit/envelope-ev108.npy bridges/fp-ev107/footprint-report.json ev108-kit/terrain-ev108.npz ev108-kit/bury-work
   ev108-kit/bury-report.json`; copiar la Ãºltima `bury-work/fpN` a `fp-ev108`.
3. `tools/water/pond_author_v31.py fp-ev108/footprint.npz author-ev108`, `tools/water/pack_water_v30.ps1 -Water author-ev108`,
   `tools/water/stage_pond_pilot_v31.py author-ev108 ev108-kit/terrain-ev108.npz
   E:/DayZ-Baltic-Build/v31-ev103-sills-cones-20261012/stage/root/dayz_baltic_12km_dev/tb/narva_trial ev108w --full`,
   `tools/water/verify_pond_exact_v31.py ev108w/stage-report.json fp-ev108/footprint.npz ev108w/water/temp/baltic_water_v30 â€¦`.
4. Registros = `bridges/records.json` + `ev108-kit/kit-records.json` â†’ `tools/terrain/stage_bridges_v31.py
   ev108w/stage/root/â€¦/narva_trial ev108-kit/terrain-ev108.npz ev108-kit/records-ev108.json ev108/stage/root/â€¦/narva_trial
   ev108/stage-report.json`; `compile_world_ev108.ps1`; `package_ev108.py`.
5. EV109: `tools/terrain/bridges_v31.py ev108-kit/terrain-ev108.npz ev108-kit/envelope-ev108.npy
   evidence/â€¦/bridges/ev109/sites-rollout.json ev109/terrain-br.npz ev109/envelope-br.npy ev109/bridge-records.json
   ev109/bridge-report.json`; despuÃ©s los pasos 2â€“4 con la cobertura `ev108-kit/cover-ev108.npy`, la envolvente `ev109/envelope-br.npy`,
   registros = `ev108-kit/records-ev108.json` + `ev109/bridge-records.json`, `compile_world_ev109.ps1` y `package_ev109.py`.
6. EV109R: `tools/terrain/global_normal_map.py ev109/terrain-ev109.npz baltic_global_nohq.png` â†’ `ImageToPAA` â†’ copiar el
   Ã¡rbol `ev109/stage/root/dayz_baltic_12km_dev` (solo esa carpeta: el resto son junctions) a `ev109r/stage/root/`, PAA en `data/`,
   `ev109r_config.py`, `compile_world_ev109r.ps1`, `package_ev109r.py`.
7. Sondas: puntos con `tools/water/probe_points_kit.py` y `tools/terrain/probe_points_bridges.py`, misiÃ³n
   `BalticBridgeProbeV2.BalticTrial` (solo servidor), y comparar con `bridges/ev109/probe-ev109-summary.json`.

## Candidato aislado: rebase híbrido1171,190 (26-10-2026)

Ver plans/ev112-rebased-hybrid-relief-20261026.md y evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-hybrid-rebase-20261026/README.md.
14vecinos corregidos;29tests,coronas,agua,carreteras y censo offlinePASS. Candidato
267picos/1144pozos/4rectángulos, sin aceptación global. NO desplegado ni integrado:
kit7 nativo sigue268picos y su generación/607 no se heredan. Candidato preparado
en E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-hybrid-pilot-merged-20261026.
Faltan bosque,stage,binario y sonda propias antes de integrar esta modificación.
