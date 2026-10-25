# DayZ Baltic 12km â€” handoff

<!-- LIVE-STATE:START -->
project: DayZ_Baltic_12km
updated: 2026-10-25 (candidato GuardedD:58 picos y8 depresiones corregidos offline;148 tests PASS; compilación y navmesh en curso)
owner: Codex, ejecutor e integrador por petición viva de Guillermo: continuar OT1 y EV112 hasta completar las pruebas autorizadas. Plan aprobado plans/ev112-plan-astra.md; decisiones del picker incorporadas en la sesión canónica.
status: EV112 abierto. U2 conserva2823controles y300rayos PASS. Candidato GuardedD separado:269picos/1148depresiones/5transiciones restantes; sin aceptación visual/global. Río131 sigue2245componentes y coste no medido.
plan: plans/ev112-guarded-relief-neighbours-20261025.md y plans/ev112-navmesh-v9-20261025.md, continuación de EV112 autorizada. Generación navmesh U2 no acepta el terreno nuevo D.
candidate: E:/DayZ-Baltic-Build/shape-repair-20261025. combined-merged terrenoSHAab96a8f6fb3da6ca02e566caa1cf5d61ad720d340ec611316c33bcbe2ce717ef; WRPfuentea23f446b32b48114b3bdbfebf9838ee7c515396feefdbc192f2f8b178702b830. package-combined verifica2578725objetos y62poses. Mod separado @DayZ_Baltic_EV112_ShapeRepairT: mundo06aae98a7763c131d97a55774da01b9af9db575c37216ebc9d13aaf082579bdb; piloto988354f4488c0a31c6ab57b3768b24447879aa815e0afdb056864dac2435423f; agua97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43.
pilots: EV111 V2 @DayZ_Baltic_EV111_ForestPilotV2 (mundo ee4bd96eâ€¦, E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev111/r2/BUILD-EV111-r2.md); EV111 V1; EV110 @DayZ_Baltic_EV110_LatticeShoresV1 mundo 226932e3â€¦, agua 46e63c70â€¦ (terreno ev110/terrain-ev110.npz d25e9428â€¦, cadena evidence/â€¦/ev110/BUILD-EV110.md); EV109 7ad4d6cfâ€¦; EV108 V7 389e27a6â€¦. Build E:/DayZ-Baltic-Build/v31-pond-layer-20261013; trabajo de EV112 en ev112-wip/; relevo en handoff-20261018/ (MANIFEST.json).
previous: EV103 441dfda9â€¦, EV102 4d572a76â€¦, EV101 470cceceâ€¦, EV100 21e7f71dâ€¦, EV99 fb8893a4â€¦, EV98 4330c9a2â€¦, EV97 546bdcfdâ€¦, EV96 b12fe58câ€¦, EV95 f1a148caâ€¦ (Astra), B b11c825bâ€¦ referencia.
water: agua de dos colores = charca sobre fondo bajo el mar del motor (EV96: fondos a 1,0 m, tramos bajos convertidos en mar). Capa v31: una pieza por tesela de 48 m y banda de 25 mm, verificaciÃ³n exacta por medias celdas. Kit: lÃ¡mina visible plana de 14 Ã— 24 m y cara `water_ext` de 14 m; solo la V del terreno la recorta (asiento de Chernarus âˆ’0,33/+0,70/+1,81 a 0/3/6 m); el motor da agua del kit con â‰¥0,10â€“0,15 m bajo su suelo.
relief: EV97: suavizado Ïƒ 12 m solo de tierra seca; reserva, plataformas y Narva fijas. Rejilla de 6 m con diagonal NO-SE (igual que Chernarus a 7,5 m).
focus: el cliente sin foco al cargar abre el menÃº de pausa (cielo morado, terreno sin texturas) hasta que Guillermo hace clic en la ventana y pulsa Â«ContinuarÂ».
blocker: Sin bloqueo de banco. T falla5rayos RV; U2 los corrige con expansión local de46componentes y+0,3783%caras, sin alterar terreno/agua/poses. Quedan ríos antiguos,98.0-2/67.0-0sin construir,48.0-0apoyo incompatible, contacto cliente/coste global131,3727discos de bosque y015-45/60m pendiente autorizado.
validation: U2:132tests PASS sin errores/skips;2823controles congelados PASS y300rayos RV/Bullet con modelo. Calibración vanilla fresca.62ODOL/poses/juntas exactos; certificado de unión superior±2cm/huella1cm. P11heredado77559secciones/130534intervalos,0fallos. Bosque2560872instancias:0fallos medidos,3727discos INCONCLUSOS. No cierre visual/global.
cleanup: Trabajo activo: run propio382bfb40-1db2-46b0-a8b9-eef201b93032 sirve datos navmesh U2; lease renovado, generador limitado3600s desde16:13UTC. Compilación GuardedD y revisión Fable en curso. No cerrar ni asumir libre el banco sin session_status.
performance: Auditoría5495 ODOL completa, PresentMon2.6 firmado y lector contrastado contra357 frames/10 grupos de traza oficial. Sin captura DayZ/A-B. Plan plans/ev112-performance-chernarus-20261024.md; evidencia evidence/performance/chernarus-audit-20261024-d/README.md.
bugs: bugs.md una fila por ID: 007 (orillas en escalera; kit EV108), 015 (puentes; EV109), 017, 018, 019, 020. Historia en bugs-history-hasta-2026-10-10.md.
next: Cerrar compilación/readback GuardedD; guardar resultado del generador U2, revisar TESM9 si existe y sondear37rutas con referenciaB (bridgeY preservada). Continuar sonda D y pendientes de ríos/relieve/bosque/carreteras físicas/A-B Chernarus. No usar la primera referencia nav-v9 (rechazada antes de ejecutarse).
git: GitHub público https://github.com/willy92wins/DayZ_Baltic_12km. Historial público saneado independiente en E:/DayZ-Baltic-Build/shape-repair-20261025/public-repo; historial local completo conservado. No publicar ramas locales ni usar --all/--mirror; ver PUBLICATION.md.
handoff: Checkpoint runtime-rv-contact-20261025 continúa compiled-shape-t-20261025. Sesión C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-25-dayz-baltic-shape-repair.md.
deployed: P:\Mods\@DayZ_Baltic_EV112_RuntimeMarginsV2 — mundo 751823ac65cd56c9093de9705ee30b08a448a69606690c1363ecf944a15ac838; agua 97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43. Carga del terreno corregido contrastada en motor.
visual_probe: U2 @DayZ_Baltic_EV112_RVOverlapU2:mundo06aae98a7763c131d97a55774da01b9af9db575c37216ebc9d13aaf082579bdb,pilotoc0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87,agua97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43. Sonda2823+rejilla300completadas. Candidato para vista humana; no CCT/FPS/AI. R,T,U1conservados.
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
