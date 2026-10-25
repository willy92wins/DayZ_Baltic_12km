# DayZ Baltic 12km â€” handoff

<!-- LIVE-STATE:START -->
project: DayZ_Baltic_12km
updated: 2026-10-01T10:14:17.741402+00:00
owner: sesion unica Codex executor/integrador; hasta 10:42:43 UTC / 12:42:43 Madrid
status: CONTINUOUS_PURSUIT_V2_RUNNING
state: evidence/overnight-2026-10-01/state.json
plan: plans/overnight-2026-10-01.md + narva-crossing-foundation-v10.md + regional-physical-consumers-v10.md + foundation-drive-v10.md + foundation-visual-v10.md + foundation-performance-v10.md
terrain: ASC V10 8e25fab2; 693 vertices corregidos. Accesos8m, pendiente maxima5.067%, transversal7.838mm, cuerda6m11.498mm. Aguas/canales/islas protegidos.
bridge: 9 tramos /225m /tablero11m. Galibo geometrico6.338m en18m con agua de diseno3m; no acredita barco mediano.
native: 01_native_v10.wrp631736b5 y02_reopened_v10.wrp cdd6838f; PASS_EXACT_NATIVE_PERSISTENCE, alturas/materiales/10161poses exactos.7controles. Cierre/reapertura reales; no reimportar.
package: @DayZ_Baltic_FoundationV10Native, world d1008dd6, compiledWRP b46c7fce, water f9a5cdf7. Nuevo NM e8348efc/449360340bytes. Paridad6826entradas originales y nuevoNM. Baselines fd2c7023/55d7163c intactos.
navmesh: generacion966289/966289tiles sobre WRPfinal; guardada/empaquetada. Receipt navmesh-v10-native-generation.json. Run generacionEXITED.
water_nav: consumer-v5-final-native PASS81212agua/tierra,314nav,15rutas; maxerroraltura0.000499m. Run a1eca3fb EXITED_ORDERLY. Consultas no equivalen a locomocion ni render.
boat: V3 PASS8/8 sectores ida/vuelta. FullriverV2 completo9PASS/3FAIL;12tramos,26.600558km distintos, todos puntos visitados/salud600. FAIL6muestreoindices y8/10deriva terminal. Sin tripulantes/barco mediano.
ai: V1 completo10PASS/9FAIL; V2 control local FAIL; V3 completo20PASS/6FAIL. Tres regresos terrestres cubiertos por tramos solapados; puente sigue sin aceptar. Todos cerrados ordenados. FindPath8rutas+NONE PASS; no sustituye locomocion.
driving: V3 PASS3/3: ida/vuelta1.019km, salud1000,4contactos, max26.9km/h, parada5.4s.18negativosPASS. Run7aef7e71 EXITED_ORDERLY. V2FAILsolo spawn24cm preservado.
visual: Siete grupos/12poses+restauracion PASS telemetria, todos EXITED_ORDERLY. Aceptacion de pixeles PARCIAL: Narva/SPB/norte; Neva/reserva/sur/conjunto pendientes. Fuentes visual-review.md/json; crash distante original sin causa aislada. CU liberado.
performance: V10 load0/25/100/0 PASS completo,420muestras por proceso,100vivos/activos,servidor~2.52GiB. Un intervalo185ms en fase final vacia;CPU no monotona.8negativosPASS. Runf8c59ee6 EXITED_ORDERLY. No80-100 jugadores.
archive: packages/baltic-foundation-v10-native-checkpoint, zip f96d3d5c; cadaentrada/hashfuente verificados. PBOsfinales incluidos. RutasP originales y junctionP:/baltic_water requeridas; no instalador portable.
coordination: Run propio15a3c31b persecucionV2 activo, lease renovado45-60s. CU liberado. Cerrar ordenadamente antes10:36UTC; no tocar runs ajenos.
usage: reset autorizado consumido06:22:11UTC al5% restante. Receipt usage-reset.json, clave70a3ac12-a643-4daa-b9c6-702090f89eab. Queda1credito sin segundaautorizacion.
next: Terminar persecucionV2 (tablero6m/accesos4m; carril4m separado), completar vistas pendientes si hay margen, consolidar y cerrar10:42:43UTC.
commit: HEAD4ff154b7; cambios previos/nocturnos preservados, diagnostics/ajeno. No version1.0 ni mapaentero terminado.
continuous: V1 controlPASS; cruce1 se detuvo por jugador4.005626m lateral aun sobre tablero. FAILconservado,15negativosPASScontrol. V2 consumidor adicional independiente en curso; sin cambios WRP/NM.
<!-- LIVE-STATE:END -->

## Estado vigente

Ver LIVE-STATE y `evidence/overnight-2026-10-01/README.md` para el trabajo actual. `continuation-v9.md` conserva el estado anterior.

## HistÃ³rico â€” navegaciÃ³n local de Narva

Los pÃ¡rrafos siguientes describen ensayos anteriores; no determinan el estado

actual de procesos, artefactos ni permisos. Evidencia: `evidence/navigation/README.md`.

ContinuaciÃ³n01:44: run c9dc7555 solo servidor PASS_EMPTY_BOAT_LOCAL_OUTWARD,

226 muestras continuas,196 propulsadas, salud600, paso bajo vano y destino

alcanzado; log8ad568ff. Sin cambios del verificador. ca8a8d0f llegÃ³ pero conserva

FAIL de continuidad por pausa inicial2.387s sin motor; evidencia inmutable.

TripulaciÃ³n, regreso, visual cliente y rÃ­os regionales pendientes.

MCP libre. Skill actualizada/validada; negativos del verificador pasan.

ContinuaciÃ³n01:28: mar abierto PASS_CALIBRATION_MOVEMENT_ONLY,89.278m/salud600,

85 muestras consecutivas de propulsiÃ³n (calibration-input-v2). El control anterior

se quedaba en neutral1/RPM700/hÃ©lice0. OnInput mÃ¡s solicitud de marcha sostenida

lo resolviÃ³ en este ensayo; no separar causalidad de ambos cambios.

Carreteras: la extensiÃ³n del perfil hasta320m detecta terreno exterior sin preparar

con cambios de rasante6.274pp y desviaciones133.8mm; no es regresiÃ³n del puente.

Nuevas fuentes/evidencias sin commit tras interrupciÃ³n; HEAD anterior6f81b94.

La base anterior sigue en `evidence/regional-water/final-pbo-verification.json`

y `packages/baltic-basic-v0.1/README.md`; no confundirla con el candidato navegable.

MCP b024257 integrado. Skill dayz-terrain-workflow actualizada y validada.

Todo lo que sigue es histÃ³rico; no decidir procesos/sondas/permisos

a partir de esos estados anteriores.

## Historial conservado

## ContinuaciÃ³n actual â€” agua medida y navegaciÃ³n preparada

Fuente actual: `evidence/render-water/auto-observer/runtime-checkpoint.json`.

Supersede el checkpoint anterior de sonda sin cargar y todos los estados histÃ³ricos

de proceso/F10 que aparecen mÃ¡s abajo. No reinstalar F10: ya no es necesario.

El usuario cerrÃ³ TB bloqueado; se reabriÃ³ el proyecto guardado. Addon automÃ¡tico

temporal compilado y ejecutado por el motor: marcadores CONSTRUCTED y COMPLETE_441,

log nuevo SHA `189baf62cf06dea3655ac27e4ce557b974c1609fce0e51d2a79815382d54550d`.

`verify_water_observer.py --native narva_tb_dryland_v1.asc` devuelve exit0 y

PASS_SAMPLED_DRY_INTERIOR. Los297 puntos secos interiores de referencia estÃ¡n

secos y por encima del mÃ¡ximo1m;44 estaban inundados antes y108 no superaban1m.

La lectura actual del mar fue0.506368m. La comparaciÃ³n contra el ASC guardado

coincide hasta0.005000033m. No se extrapola a toda la regiÃ³n.

Vista de orilla en motor(3222.75,8008.25), captura `orilla-3223-8008.png`: agua,

borde y terreno visibles sin las manchas negras previas. Es revisiÃ³n puntual,

no una prueba exhaustiva de conectividad. No hubo ediciÃ³n de terreno durante

este ensayo; hash TV4P conserva `5f9390837b3a503977bf9a5f1a67f3a92ad9a066778207f5e1b7076ccec4feeb`.

Buldozer cerrÃ³ normalmente18:25; TB cerrÃ³ despuÃ©s. ParÃ¡metros originales

respaldados y restaurados, comprobados en TerrainBuilder.opt tras el cierre.

PBO temporal retirado por hash; fuentes/paquete/evidencia conservados. No se

tocaron perfiles de entrada ni scripts vanilla. Persisten avisos preexistentes

de PluginConfigDebugProfile y fugas al cierre; no impidieron esta mediciÃ³n y

no se afirma ausencia general de errores del visor.

El usuario autorizÃ³ especÃ­ficamente NavMeshGenerator; abriÃ³ correctamente.

No se generÃ³ .nm. La UI pide un servidor local de datos; el launcher compartido

no admite `-startNavmeshDataServer`. MisiÃ³n `missions/empty.BalticTrial` y config

`tests/navmesh/ServerDZNV.cfg` preparadas, no desplegadas; linter1 archivo,0

errores/avisos. `plans/navmesh-data-server.md` propone una opciÃ³n booleana tipada

sin abrir argumentos libres. Guillermo eligiÃ³ explÃ­citamente aÃ±adir y validar

esa opciÃ³n en DayZ_MCP. ImplementaciÃ³n en worktree aislado del workspace

`work/dayz-mcp-navmesh`, rama `feat/baltic-navmesh-data-server`, base

`28f76cd1a498d8be101bf596d9c061231711d3d7`. El despliegue compartido sigue intacto.

PBO de mapa corregido todavÃ­a NO desplegado: e3e6b361...; despliegue real sigue

e4b07860... (ensayo navempty anterior). Antes del prÃ³ximo run hay que desplegar

el candidato por hash. La versiÃ³n bÃ¡sica continÃºa pendiente de carga y juego.

## Alcance vivo

Guillermo pidiÃ³ continuar hasta la versiÃ³n 1.0. Producto: regiÃ³n condensada con agua, reserva, conexiones y closeup Ã­ntegro de San Petersburgo; Narva/frontera y zona occidental; vanilla primero, anchuras humanas, objetivo 80â€“100 jugadores. Recorte v0 aprobado y escala XY Ãºnica. No concurrencia con Exta ni entrega suya incorporada.

Guillermo precisÃ³ continuar hasta la versiÃ³n bÃ¡sica y corregir las manchas negras y el agua fuera de sus lÃ­mites. No etiquetar este prototipo como 1.0 completa. Coeficiente Z final, densidad y bÃºnker aÃºn sin fijar; no decidirlos silenciosamente. Esos puntos no impiden la prueba tÃ©cnica preparada.

## Antecedentes de importaciÃ³n y empaquetado (histÃ³ricos)

- Proyecto actual TB: `tb/narva_trial/narva_trial.tv4p`, candidato de agua guardado a las 16:36. Reabierto en TB PID208720 y exportado a `baltic_water_reopened_v1.wrp` (17:22:30), SHA `17e750e61f081635813522808b4dfe019711f5dd4fb14b60d4830ae4fc5dc98c`. Verificados todos los vÃ©rtices y ambos objetos. Cambian solo orden de objetos y dos bytes del registro terminal sin nombre. Sonda posterior pendiente; no repetir V3 ni basal.

- CorrecciÃ³n exclusivamente local: 202 vÃ©rtices/radio 48 m; fuentes y copias regionales conservadas (gate previo de 569 hashes). ASC exportado: 4194304 alturas dentro de 5.01 mm; negativo original rechazado.

- V3: 289 cuadrÃ­cula + 289 perfil + 34 extremos, ambos accesos de 8 m a cota 2 m sin gap medido. Registro fijado por V2, sin refit. El WRP reabierto conserva todas las alturas y la posiciÃ³n del puente (error 0.0000004063 m).

- Primer PBO: `packages/baltic-playtest/Addons/narva_trial.pbo`, 24806932 bytes, SHA-256 `6d6b1c163412e92a221d8b7580e6943eec9818f7e08e894359e84b03fca582f0`. OPRW v29, 367 RVMAT, 50 PAA, puente presente, pond diagnÃ³stico ausente. 420 entradas idÃ©nticas a la salida compilada.

- MisiÃ³n independiente `missions/BalticTest.BalticTrial`, spawn oeste, observador automÃ¡tico a 10 s, economÃ­a vacÃ­a. Linter 1 script/0 errores/0 avisos y 15 XML parseados. Primera prueba lanzada posteriormente; Mission no confirmada y sonda no recibida. Evidencia: evidence/runtime-first/README.md.

## Contratos y lÃ­mites

Contrato nativo LOCAL: X=200000+6*col, N=6*(2047-row), diagonal NW-SE en array row-down. La observaciÃ³n UI anterior N=12288-6*row no predice estas alturas. No aplicar un desplazamiento global ni extender la regla a otros tamaÃ±os sin evidencia.

Puente vanilla bridge_metal_25, yaw 98.748926, escala 1, centro TB (202417.143,6889.885). Origen absoluto TB 1.476612; origen motor Y=-6.054884 y roadway cruda 8.054884 â†’ tablero 2 m. El export de objetos es relativo; no confundir su Ãºltima columna con altura absoluta. El WRP demuestra pose persistida; no se inspeccionÃ³ el selector de modo de altura tras reabrir.

Ocultar pond en Buldozer NO lo excluye del WRP. Se eliminÃ³ solo su registro de 85 bytes en la copia de build; terreno/materiales/puente conservados byte a byte. Original nativo intacto. Binarize aceptÃ³ la copia; falta el juego.

Agua consultada: mar=true, pond=false; nivel observado 0.54377 m. GetWaterDepth se consultÃ³ a Y=0, no mide aquÃ­ hasta el lecho. Agua elevada pendiente. Dos crashes con pond visible, tres cierres normales oculto; mecanismo no aislado. Cuatroâ†’seis materiales no corrigiÃ³ manchas negras. ComparaciÃ³n vanilla acotada a config y modelo pond, no a todos los recursos.

## ContinuaciÃ³n

Leer `product-spec.md`, plan Gate C e `evidence/playtest/README.md`. Acceso recuperado y worker recargado; entorno libre tras primer run. Se usÃ³ el arnÃ©s registrado DayZ_MCP con mod adicional y misiÃ³n propia, sin cambiar polÃ­ticas. Lanzar/adoptar/cerrar solo el run propio segÃºn runbook. Hash del PBO realmente desplegado antes de atribuir resultados al source.

Prueba: carga de mundo BalticTrial, compilaciÃ³n cliente/servidor, sonda completa, cruce a pie/vehÃ­culo, render y nado/salida. CE, navmesh, poblaciÃ³n regional, agua elevada y carga 80â€“100 son gates distintos. No hay rendimiento acreditado ni hardware confirmado.

## RecuperaciÃ³n y antecedentes

Fuentes originales fuera de OneDrive, ruta/hash en README. Artefactos grandes ignorados en Git y preservados por paquetes con manifiestos; commit no sustituye backup. El nuevo paquete de playtest conserva PBO, misiÃ³n y entradas del build; el proyecto TB completo requiere el checkpoint Narva anterior y el regional previo. Sin remoto ni publicaciÃ³n.

`build-isolated/` contiene junctions DZ/bin/core solo para resolver dependencias de lectura. No borrar recursivamente esas raÃ­ces ni copiarlas como datos del proyecto. El build con -project=P:\ fallÃ³ por escanear configs ajenas; el build aislado pasÃ³. Exit code 0 de AddonBuilder no basta: exigir artefacto, log y contenido comprobado.

Antecedentes: `evidence/tb-import/informe.md`, `evidence/tb-registration/informe.md`, `evidence/narva/informe.md`; estado actual de compilaciÃ³n en `evidence/playtest/README.md`. La observaciÃ³n UI histÃ³rica y sus ensayos permanecen documentados; el registro nativo local es la referencia numÃ©rica actual en Narva.

## Primer arranque real despuÃ©s de recuperar acceso

Ver `evidence/runtime-first/README.md` y `first-run.json`. Despliegue del PBO por hash, file patching desactivado. Run 25d45413-a1d7-465a-98f1-86cf5ce7b14b lanzÃ³ servidor/cliente, pero no pasÃ³ carga de misiÃ³n: aviso navmesh y ErrorMessage minidump. La guÃ­a permite terreno sin navmesh; causa exacta pendiente, no conclusiÃ³n de que el .nm por sÃ­ solo resuelva todo.

Cierre por tool oficial, mÃ©todo forced_kill, exit_metrics_valid=false. SesiÃ³n final none, caja libre, cero pendientes, cleanup sin degradaciÃ³n. No dejÃ³ procesos ni lease propios. Config Navmesh y generaciÃ³n propia pendientes; la interfaz pÃºblica de lanzamiento no expone -startNavmeshDataServer. No lanzar por un canal alternativo ni modificar la infraestructura compartida silenciosamente.

## Avance de render y agua â€” estado actual

Manchas resueltas en el ensayo mediante canales TerrainX completos; seis materiales y TerrainSNX no fueron remedios. Fuente: evidence/render-water/README.md. Buldozer confirmÃ³ 44 puntos de tierra inundados y rango mar0.5..1m. Candidato local importado: todas las alturas dentro de 5,01 mm, puente sin desplazamiento, materiales sin campos vacÃ­os. En la zona interior seca (70933 vÃ©rtices), los 28278 que no superaban 1 m pasan a cero; altura mÃ­nima 1,25 m. Esto es validaciÃ³n geomÃ©trica, no mediciÃ³n posterior de agua. Los canales estrechos y las orillas requieren revisiÃ³n del motor. No repetir la sonda basal.

Nuevo ASC nativo SHA `7832f0a9d05cb472bc419bd6600b3034b07832b14e55e0a86fe1bf6d10c9d5dc`; WRP SHA `6b0859fd71aeb76182754f3cf14a541beac1568beb8021d5fc337f604db391eb`. PBO con materiales y agua: SHA `e3e6b3614301950f423bf55f1819cdd4bef9743e3323f29d7669ce5a66251283`, 24743067 bytes; no desplegado. Prueba negativa: el WRP antiguo falla frente al ASC nuevo (error mÃ¡ximo 1 m, exit1). El verificador ya no dice REOPENED sin evidencia externa.

Las sondas temporales para el recheck se retiraron por hash tras el bloqueo de carga; no hay log posterior. Ese intento F10 quedÃ³ supersedido por la sonda automÃ¡tica ejecutada; no reinstalarlo. No cerrar/adoptar Buldozer por MCP ni saltar el rechazo de la ventana dwm mediante otro canal. Respaldo previo conservado SHA2a3f171e...; entregable actualizado contiene tambiÃ©n el estado posterior.

Dos runs navcfg/navempty no cargaron Mission, cerrados por MCP. Ãšltimo PBO desplegado navempty hash e4b07860..., candidato nuevo materiales hash92ea247b... todavÃ­a sin desplegar. AutorizaciÃ³n NavMeshGenerator pendiente tras rechazo automÃ¡tico explÃ­cito. La prueba de agua sigue siendo independiente de ese bloqueo.

Reapertura: `evidence/render-water/reopened/`. Muestreo geomÃ©trico de 1,5 m dentro del agua OSM, mismo candidato: retroceso mÃ¡ximo muestreado 5,58 m a plano0,5 m; 2,28 m a0,75; 0,25 m a1. No hay pÃ©rdidas muestreadas a mÃ¡s de12 m del borde. No acredita conectividad de canales ni agua del motor. Revisar estos bordes antes de extender el candidato. No se ha modificado el terreno en esta continuaciÃ³n. Sondas temporales reinstaladas y despuÃ©s retiradas comprobando hashes al quedar pendiente el control; ensayo F10 cerrado y supersedido por la sonda automÃ¡tica.

## ExportaciÃ³n reabierta y Steam â€” continuaciÃ³n mÃ¡s reciente

La exportaciÃ³n posterior ya pasÃ³: `evidence/render-water/post-reopen/`. Las alturas, Ã­ndices y tabla de materiales, y cada registro de objeto son idÃ©nticos a los de la exportaciÃ³n anterior; el hash total difiere por orden y terminador. Respaldo suplementario `outputs/baltic-render-agua/narva-reapertura-exportada.zip`, SHA `6dacafe0bb2c6626a10b493977ec10e5470c56c3d65475d2530aba4f701c8f22`, CRC y WRP verificados. No reemplaza el checkpoint del proyecto completo.

Buldozer 17:24 mostrÃ³ Â«Unable to locate a running instance of SteamÂ» antes de cargar scripts. Steam real PID196052 y registro host correcto; la lectura local de Codex daba PID40860 y otro ActiveUser. ComparaciÃ³n por StdRegProv y lectura local, sin exponer identificadores de cuenta. A peticiÃ³n del usuario se respaldaron y sincronizaron Ãºnicamente pid/ActiveUser de la copia local con los valores actuales del host; comprobados host y proceso sin cambios. No reinicio de Steam ni ediciÃ³n de DayZ_MCP. Esto acredita reparaciÃ³n del registro visible, pendiente de prueba de arranque. Backup privado en `work/steam-registration/private-values-before.json` del workspace; no exportarlo.

Steam UI fue rechazado por revisiÃ³n automÃ¡tica incluso despuÃ©s de autorizaciÃ³n explÃ­cita. La investigaciÃ³n del registro es una peticiÃ³n posterior del usuario. No reintentar UI de Steam sin cambio del canal. El helper de preflight del skill actualmente falla al parsear su lÃ­nea 213; comprobadas las rutas necesarias directamente y sin editar el skill.

En ese momento histÃ³rico se instalaron sondas temporales, ya retiradas: `P:\scripts\buldozer.c` SHA `ef0964dcb9ad22be42cca673b7dc508fec76cc7483a2a32b56d5c475ecdfe4a8` y `guill.c` SHA `f3a0034023771e13f432d98033d87c0652077bf12df6807c554349fd4d110999`, destino nuevo `$profile:baltic_water_observer_after_v1.log`. Recoger antes de retirarlas; retirar solo por hash coincidente. No hay log posterior todavÃ­a. Se pidiÃ³ al usuario Connect y F10 porque los clics automÃ¡ticos no producen un nuevo proceso/log. No atribuir ese no-arranque a fallo posterior de la reparaciÃ³n de Steam.

Resultado posterior: conexiÃ³n desde menÃº Tools, Buldozer PID219340 iniciado 17:34:21 con padre TB208720. Terreno visible y aviso Steam ausente. `steam-consumer-startup.json` documenta la prueba. No se aislÃ³ quÃ© valor de registro individual provocaba el error ni se demuestra reparaciÃ³n permanente tras reiniciar/cambiar sesiÃ³n Steam. La primera respuesta manual de carga/F10 no produjo log ni proceso observable en aquel momento; tras observar esta carga real se volviÃ³ a solicitar F10. Sigue sin archivo y no hay mediciÃ³n posterior aprobada. No hay lease/run MCP propio; este Buldozer externo ocupa la caja.

Ãšltimo diagnÃ³stico: Guillermo confirmÃ³ F10 con el visor cargado y sigue sin archivo. `observer-dispatch.json` y snapshots del RPT/script log: World/Mission cargados, no `Module: BuldozerModule` (sÃ­ aparecÃ­a en la prueba basal). Preferencias TB/Buldozer observadas: ambas carpetas de datos P:\, nombre de lanzamiento Buldozer; UABuldRunScript=kF10 en perfil. Ambos scripts tienen encabezado/ruta/hash esperados. Preferencias cerradas con Cancel, sin cambio. No clasificar como fallo del algoritmo del agua; ejecuciÃ³n de la sonda aÃºn no observada. Se pidiÃ³ un Ãºnico discriminador de foco, clic en tÃ­tulo y F10 mantenido 1s; no operar ventanas mientras el usuario lo hace. Si falla, cambiar estrategia sin pedir mÃ¡s F10 iguales. Buldozer responde y queda abierto; sondas presentes para esta prueba, con recibo de hashes. MCP self none, owner null, pending0, cleanup vacÃ­o, presencia externa Buldozer (no adoptar).

