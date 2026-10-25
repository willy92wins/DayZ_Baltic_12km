# DayZ Baltic 12km — handoff

<!-- LIVE-STATE:START -->
project: DayZ_Baltic_12km
updated: 2026-10-01
owner: sesión única Codex, executor/integrator por petición viva; sesión autónoma 8h hasta 01-10 12:42:43 Madrid
status: V9_IMPORTED_SAVED / NATIVE_STRICT_GATE_FAIL / WATER_IMPORT_PENDING / FRESH_NAVMESH_PENDING / CANDIDATE_0.3_UNCHANGED
handoff: C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-01-dayz-baltic-handoff-terreno-v9.md; inventario vivo evidence/regional-foundation-v1/handoff-2026-10-01/state.json
plan: plans/overnight-2026-10-01.md + plans/regional-foundation-execution.md, P2/P3/P5/P9/P10/P11/P12/P13. Objetivo de producto pendiente: base completa de terreno/agua/navmesh antes del mapeado; no declarar versión1.0.
next: V9 YA importado/Rebuild/guardado en tb/regional_foundation_v1/narva_trial.tv4p SHA139d2423. Último WRP baltic_foundation_bridges_v9.wrp SHAfe02d6e0. Verificar reapertura y resolver explícitamente precisión; crear biblioteca Baltic_Water_V2 desde P:/baltic_water, importar water_absolute_v2.txt con cota absoluta, guardar/reabrir/exportar completo, paquete SAT1M y NM12.5 nueva, consumidorV3/lancha/IA/cliente/carga. No Generate Layers.
blocker: Petición nocturna renueva autorización de CU; editor y juego cerrados al inicio, reapertura V9 pendiente. Estado nocturno evidence/overnight-2026-10-01/state.json. Solo Narva_Vanilla.tml persiste y último WRP contiene3 puentes/0 aguas. Gate estricto FAIL por22 alturas de borde (max5.96e-8m) y dos cotas de puente (max7.16e-7m), sin cambio XY/rotación/modelos. No se relajó ni sustituyó la evidencia. Falta agua nativa, reapertura, NM nueva y runtimeV9.
validation: ASC335554a6 y copia idénticos; alturas/materiales comparados sobre todos los vértices:4194282 exactos,22 diferencias submicrométricas. Cabecera/materiales nativos exactos. Puente restaurado tras desplazamientos del Rebuild; comparación nueva documentada. V9 offline: pendientes34.16955grados,rasantes29772+1472,79420 muestras de corredor>=3m,239 lagos,283 islas. ConsumidorV3 completo en baseline:81212 agua/tierra+314nav+15rutas; FAIL esperado por cotas antiguas, no aceptaciónV9. Helpers de paquete solo negativos/preflight, sin build positivo.
cleanup: Último run propio3edbd6e3 cerrado y lease liberado previamente. Hoy session_status sin respuesta; coordinación actual NO confirmada. TB258320 responde; DayZDiag274188/287828 existen (propiedad desconocida, no tocados); NMG no detectado. No procesos gestionados ni CU en este cierre. Desplegados fd2c7023 y55d7163c, baseline WRP9bf50853/NMeb0f131e intactos. diagnostics/ ajeno intacto.
bugs: No bugs.md vivo (ausencia declarada). Fallos actuales en handoff canónico/state.json y native-bridges-v9-first.json; mantener negativos históricos. Baseline jugable no prueba nuevo terreno, navegación regional ni capacidad80–100. HEAD4ff154b7; cambios sin commit preservados; no commit nuevo.
<!-- LIVE-STATE:END -->

## Estado vigente

Ver LIVE-STATE y `evidence/regional-foundation-v1/continuation-v9.md` para el trabajo actual.

## Histórico — navegación local de Narva

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

## Historial conservado

## Continuación actual — agua medida y navegación preparada

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

## Alcance vivo

Guillermo pidió continuar hasta la versión 1.0. Producto: región condensada con agua, reserva, conexiones y closeup íntegro de San Petersburgo; Narva/frontera y zona occidental; vanilla primero, anchuras humanas, objetivo 80–100 jugadores. Recorte v0 aprobado y escala XY única. No concurrencia con Exta ni entrega suya incorporada.

Guillermo precisó continuar hasta la versión básica y corregir las manchas negras y el agua fuera de sus límites. No etiquetar este prototipo como 1.0 completa. Coeficiente Z final, densidad y búnker aún sin fijar; no decidirlos silenciosamente. Esos puntos no impiden la prueba técnica preparada.

## Antecedentes de importación y empaquetado (históricos)

- Proyecto actual TB: `tb/narva_trial/narva_trial.tv4p`, candidato de agua guardado a las 16:36. Reabierto en TB PID208720 y exportado a `baltic_water_reopened_v1.wrp` (17:22:30), SHA `17e750e61f081635813522808b4dfe019711f5dd4fb14b60d4830ae4fc5dc98c`. Verificados todos los vértices y ambos objetos. Cambian solo orden de objetos y dos bytes del registro terminal sin nombre. Sonda posterior pendiente; no repetir V3 ni basal.
- Corrección exclusivamente local: 202 vértices/radio 48 m; fuentes y copias regionales conservadas (gate previo de 569 hashes). ASC exportado: 4194304 alturas dentro de 5.01 mm; negativo original rechazado.
- V3: 289 cuadrícula + 289 perfil + 34 extremos, ambos accesos de 8 m a cota 2 m sin gap medido. Registro fijado por V2, sin refit. El WRP reabierto conserva todas las alturas y la posición del puente (error 0.0000004063 m).
- Primer PBO: `packages/baltic-playtest/Addons/narva_trial.pbo`, 24806932 bytes, SHA-256 `6d6b1c163412e92a221d8b7580e6943eec9818f7e08e894359e84b03fca582f0`. OPRW v29, 367 RVMAT, 50 PAA, puente presente, pond diagnóstico ausente. 420 entradas idénticas a la salida compilada.
- Misión independiente `missions/BalticTest.BalticTrial`, spawn oeste, observador automático a 10 s, economía vacía. Linter 1 script/0 errores/0 avisos y 15 XML parseados. Primera prueba lanzada posteriormente; Mission no confirmada y sonda no recibida. Evidencia: evidence/runtime-first/README.md.

## Contratos y límites

Contrato nativo LOCAL: X=200000+6*col, N=6*(2047-row), diagonal NW-SE en array row-down. La observación UI anterior N=12288-6*row no predice estas alturas. No aplicar un desplazamiento global ni extender la regla a otros tamaños sin evidencia.

Puente vanilla bridge_metal_25, yaw 98.748926, escala 1, centro TB (202417.143,6889.885). Origen absoluto TB 1.476612; origen motor Y=-6.054884 y roadway cruda 8.054884 → tablero 2 m. El export de objetos es relativo; no confundir su última columna con altura absoluta. El WRP demuestra pose persistida; no se inspeccionó el selector de modo de altura tras reabrir.

Ocultar pond en Buldozer NO lo excluye del WRP. Se eliminó solo su registro de 85 bytes en la copia de build; terreno/materiales/puente conservados byte a byte. Original nativo intacto. Binarize aceptó la copia; falta el juego.

Agua consultada: mar=true, pond=false; nivel observado 0.54377 m. GetWaterDepth se consultó a Y=0, no mide aquí hasta el lecho. Agua elevada pendiente. Dos crashes con pond visible, tres cierres normales oculto; mecanismo no aislado. Cuatro→seis materiales no corrigió manchas negras. Comparación vanilla acotada a config y modelo pond, no a todos los recursos.

## Continuación

Leer `product-spec.md`, plan Gate C e `evidence/playtest/README.md`. Acceso recuperado y worker recargado; entorno libre tras primer run. Se usó el arnés registrado DayZ_MCP con mod adicional y misión propia, sin cambiar políticas. Lanzar/adoptar/cerrar solo el run propio según runbook. Hash del PBO realmente desplegado antes de atribuir resultados al source.

Prueba: carga de mundo BalticTrial, compilación cliente/servidor, sonda completa, cruce a pie/vehículo, render y nado/salida. CE, navmesh, población regional, agua elevada y carga 80–100 son gates distintos. No hay rendimiento acreditado ni hardware confirmado.

## Recuperación y antecedentes

Fuentes originales fuera de OneDrive, ruta/hash en README. Artefactos grandes ignorados en Git y preservados por paquetes con manifiestos; commit no sustituye backup. El nuevo paquete de playtest conserva PBO, misión y entradas del build; el proyecto TB completo requiere el checkpoint Narva anterior y el regional previo. Sin remoto ni publicación.

`build-isolated/` contiene junctions DZ/bin/core solo para resolver dependencias de lectura. No borrar recursivamente esas raíces ni copiarlas como datos del proyecto. El build con -project=P:\ falló por escanear configs ajenas; el build aislado pasó. Exit code 0 de AddonBuilder no basta: exigir artefacto, log y contenido comprobado.

Antecedentes: `evidence/tb-import/informe.md`, `evidence/tb-registration/informe.md`, `evidence/narva/informe.md`; estado actual de compilación en `evidence/playtest/README.md`. La observación UI histórica y sus ensayos permanecen documentados; el registro nativo local es la referencia numérica actual en Narva.

## Primer arranque real después de recuperar acceso

Ver `evidence/runtime-first/README.md` y `first-run.json`. Despliegue del PBO por hash, file patching desactivado. Run 25d45413-a1d7-465a-98f1-86cf5ce7b14b lanzó servidor/cliente, pero no pasó carga de misión: aviso navmesh y ErrorMessage minidump. La guía permite terreno sin navmesh; causa exacta pendiente, no conclusión de que el .nm por sí solo resuelva todo.

Cierre por tool oficial, método forced_kill, exit_metrics_valid=false. Sesión final none, caja libre, cero pendientes, cleanup sin degradación. No dejó procesos ni lease propios. Config Navmesh y generación propia pendientes; la interfaz pública de lanzamiento no expone -startNavmeshDataServer. No lanzar por un canal alternativo ni modificar la infraestructura compartida silenciosamente.

## Avance de render y agua — estado actual

Manchas resueltas en el ensayo mediante canales TerrainX completos; seis materiales y TerrainSNX no fueron remedios. Fuente: evidence/render-water/README.md. Buldozer confirmó 44 puntos de tierra inundados y rango mar0.5..1m. Candidato local importado: todas las alturas dentro de 5,01 mm, puente sin desplazamiento, materiales sin campos vacíos. En la zona interior seca (70933 vértices), los 28278 que no superaban 1 m pasan a cero; altura mínima 1,25 m. Esto es validación geométrica, no medición posterior de agua. Los canales estrechos y las orillas requieren revisión del motor. No repetir la sonda basal.

Nuevo ASC nativo SHA `7832f0a9d05cb472bc419bd6600b3034b07832b14e55e0a86fe1bf6d10c9d5dc`; WRP SHA `6b0859fd71aeb76182754f3cf14a541beac1568beb8021d5fc337f604db391eb`. PBO con materiales y agua: SHA `e3e6b3614301950f423bf55f1819cdd4bef9743e3323f29d7669ce5a66251283`, 24743067 bytes; no desplegado. Prueba negativa: el WRP antiguo falla frente al ASC nuevo (error máximo 1 m, exit1). El verificador ya no dice REOPENED sin evidencia externa.

Las sondas temporales para el recheck se retiraron por hash tras el bloqueo de carga; no hay log posterior. Ese intento F10 quedó supersedido por la sonda automática ejecutada; no reinstalarlo. No cerrar/adoptar Buldozer por MCP ni saltar el rechazo de la ventana dwm mediante otro canal. Respaldo previo conservado SHA2a3f171e...; entregable actualizado contiene también el estado posterior.

Dos runs navcfg/navempty no cargaron Mission, cerrados por MCP. Último PBO desplegado navempty hash e4b07860..., candidato nuevo materiales hash92ea247b... todavía sin desplegar. Autorización NavMeshGenerator pendiente tras rechazo automático explícito. La prueba de agua sigue siendo independiente de ese bloqueo.

Reapertura: `evidence/render-water/reopened/`. Muestreo geométrico de 1,5 m dentro del agua OSM, mismo candidato: retroceso máximo muestreado 5,58 m a plano0,5 m; 2,28 m a0,75; 0,25 m a1. No hay pérdidas muestreadas a más de12 m del borde. No acredita conectividad de canales ni agua del motor. Revisar estos bordes antes de extender el candidato. No se ha modificado el terreno en esta continuación. Sondas temporales reinstaladas y después retiradas comprobando hashes al quedar pendiente el control; ensayo F10 cerrado y supersedido por la sonda automática.

## Exportación reabierta y Steam — continuación más reciente

La exportación posterior ya pasó: `evidence/render-water/post-reopen/`. Las alturas, índices y tabla de materiales, y cada registro de objeto son idénticos a los de la exportación anterior; el hash total difiere por orden y terminador. Respaldo suplementario `outputs/baltic-render-agua/narva-reapertura-exportada.zip`, SHA `6dacafe0bb2c6626a10b493977ec10e5470c56c3d65475d2530aba4f701c8f22`, CRC y WRP verificados. No reemplaza el checkpoint del proyecto completo.

Buldozer 17:24 mostró «Unable to locate a running instance of Steam» antes de cargar scripts. Steam real PID196052 y registro host correcto; la lectura local de Codex daba PID40860 y otro ActiveUser. Comparación por StdRegProv y lectura local, sin exponer identificadores de cuenta. A petición del usuario se respaldaron y sincronizaron únicamente pid/ActiveUser de la copia local con los valores actuales del host; comprobados host y proceso sin cambios. No reinicio de Steam ni edición de DayZ_MCP. Esto acredita reparación del registro visible, pendiente de prueba de arranque. Backup privado en `work/steam-registration/private-values-before.json` del workspace; no exportarlo.

Steam UI fue rechazado por revisión automática incluso después de autorización explícita. La investigación del registro es una petición posterior del usuario. No reintentar UI de Steam sin cambio del canal. El helper de preflight del skill actualmente falla al parsear su línea 213; comprobadas las rutas necesarias directamente y sin editar el skill.

En ese momento histórico se instalaron sondas temporales, ya retiradas: `P:\scripts\buldozer.c` SHA `ef0964dcb9ad22be42cca673b7dc508fec76cc7483a2a32b56d5c475ecdfe4a8` y `guill.c` SHA `f3a0034023771e13f432d98033d87c0652077bf12df6807c554349fd4d110999`, destino nuevo `$profile:baltic_water_observer_after_v1.log`. Recoger antes de retirarlas; retirar solo por hash coincidente. No hay log posterior todavía. Se pidió al usuario Connect y F10 porque los clics automáticos no producen un nuevo proceso/log. No atribuir ese no-arranque a fallo posterior de la reparación de Steam.

Resultado posterior: conexión desde menú Tools, Buldozer PID219340 iniciado 17:34:21 con padre TB208720. Terreno visible y aviso Steam ausente. `steam-consumer-startup.json` documenta la prueba. No se aisló qué valor de registro individual provocaba el error ni se demuestra reparación permanente tras reiniciar/cambiar sesión Steam. La primera respuesta manual de carga/F10 no produjo log ni proceso observable en aquel momento; tras observar esta carga real se volvió a solicitar F10. Sigue sin archivo y no hay medición posterior aprobada. No hay lease/run MCP propio; este Buldozer externo ocupa la caja.

Último diagnóstico: Guillermo confirmó F10 con el visor cargado y sigue sin archivo. `observer-dispatch.json` y snapshots del RPT/script log: World/Mission cargados, no `Module: BuldozerModule` (sí aparecía en la prueba basal). Preferencias TB/Buldozer observadas: ambas carpetas de datos P:\, nombre de lanzamiento Buldozer; UABuldRunScript=kF10 en perfil. Ambos scripts tienen encabezado/ruta/hash esperados. Preferencias cerradas con Cancel, sin cambio. No clasificar como fallo del algoritmo del agua; ejecución de la sonda aún no observada. Se pidió un único discriminador de foco, clic en título y F10 mantenido 1s; no operar ventanas mientras el usuario lo hace. Si falla, cambiar estrategia sin pedir más F10 iguales. Buldozer responde y queda abierto; sondas presentes para esta prueba, con recibo de hashes. MCP self none, owner null, pending0, cleanup vacío, presencia externa Buldozer (no adoptar).
