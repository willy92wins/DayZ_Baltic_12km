# RoadC1 — recursos del laboratorio y puertas para la pareja compilada

Estado: BORRADOR_PENDIENTE_DE_REVISION. Fecha: 29-10-2026.
Codex planner/orchestrator/integrator; revisión externa Muse nativo. No council nuevo.

## Objetivo y cambio de diseño explícito

P5/P6/P8/P11: calibrar la transformación de tres piezas instaladas antes de extender
su colocación. P10 sigue vigente: esto no pavimenta la escena poblada. RoadC0 produjo
fuentes aisladas 0/3, no un WRP compilado. La pareja conserva el mismo terreno fuente;
no asumir que el control vacío es compilable ni que el compilador preserva alturas.

Hay dos bloqueos reales para autorizar la pareja: referencias del terreno aún no
ligadas y ningún lector localizado que valide terreno/materiales y objetos 0/3 del
OPRW DayZ. No ocultarlos con un PASS de magic/hash o un escáner de modelos.
Por eso esta revisión autoriza solamente C1A, investigación concreta de recursos y
superficie de herramientas. C1B (stage/config/compilador/consumidor) necesita cerrar
las anclas y su contrato antes de código o build. No se sustituye por otra fuente
sintética ni se añaden objetos al control para hacerlo aceptable.

## Hechos anclados

- RoadC0 control f00c3f57..., 17307685 B; candidato 2fb3686b..., 17307968 B.
  Prefijo terreno/materiales 17307629 B/d16b5139..., terminador56 B. Contrato9296cef4.
- `tools/quality/road_calibration_source_c0.py:66-78`: material count y cadenas
  se recorren por longitud; sin interpretación semántica. No ejecutar su CLI otra vez.
- `tools/terrain/compile_visual_pilot_ev112.ps1:9-29`: el wrapper histórico usa
  AddonBuilder, junctions DZ/bin/core/agua/piloto y config del mundo. Es evidencia,
  no entrypoint nuevo; no reusar sus directorios ni sus logs compartidos.
- Config exacta `stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/config.cpp`:
  requiredAddons DZ_Data/DZ_Surfaces/Baltic_Water_V30/Baltic_Stream_Pilot (8-12),
  clase BalticTrial:CAWorld (19), worldName (37), OutsideTerrain (24-36),
  midDetailTexture (48), cuatro UsedTerrainMaterials (49-55), navmesh (56-212).
  Quitar objetos NO elimina esos requisitos. No copiarla como configuración aislada.
- `tools/terrain/package_visual_forest_ev112.py:29-65` busca ancla baltic_water_v30,
  tabla por heurística y matriz de un objeto. No demuestra control0 ni alturas;
  tampoco es writer. Los lectores históricos localizados comparten ese límite.
- B4A3 liga doce recursos de tres modelos, no toda la escena ni el terreno.
  B0/B2 ya guardan caras, máscaras y24hipótesis de huella: no reextraer ni recalcular.

## Investigación C1A — único corte autorizado aquí

Hipótesis: un stage de laboratorio puede resolverse desde el prefijo/materiales de
RoadC0 y recursos guardados, sin importar la población original; configuración y
formato compilado siguen siendo puertas independientes.

La lectura exploratoria R0 del 29-10 se detuvo al comparar material_count con4096,
antes de abrir materiales. Un discriminador de56 B (24header+32enoffset16908312)
observó4776filas. No indica4776materiales únicos, corrupción ni capacidad del build.
Se conserva R0. El cap4096era un límite de investigación arbitrario sobre filas;
la siguiente lectura tiene otro contrato explícito: exactamente4776filas, dentro
de los399313 B restantes del prefijo, y como máximo16384rutas distintas. No amplía
límites geométricos ni convierte R0 en éxito.

Asiento EXECUTOR de investigación asignado explícitamente a Codex local: una
entrega240s; ejecución read-only60s/256MiB. 64MiB de contenido leído total,
1MiB por texto (config principal excepcional8MiB),32768referencias,16384rutas únicas.
No generar un CLI de producción, sólo recibo/script inerte de investigación.
Revisión externa del plan incluye el algoritmo de lectura; no tests geométricos.

1. Leer el control RoadC0 por hash, saltar alturas/índices por offsets verificados.
   Recorrer las4776filas con preguard de longitud<=4096 y final exacto17307629;
   conservar ordinal de fila, cadenas crudas y nombre normalizado de forma explícita.
   Validar formato de rutas sin fallback de basename. No abrir fuente poblada.
2. Deduplicar referencias sólo para lectura, conservando las filas originales.
   Leer RVMAT propios del stage histórico a las rutas literales encontradas.
   Conservar SHA/tamaño. Extraer cadenas citadas como observación léxica; NO afirmar
   cierre transitivo, shader válido ni parser semántico. Límites antes de leer.
3. Para rutas de textura/material observadas, registrar fuente candidata exacta,
   tamaño y estado LOCATED_NOT_READ/MISSING. Raíz propia y P: sólo lectura; un
   resultado por ruta no prueba precedencia actual ni identidad del proveedor.
   Ninguna lectura PBO/P3D, ni nueva copia de los doce recursos ya guardados.
4. Leer únicamente config histórico, Binarize/bin/config.cpp, P:/bin/config.cpp y
   P:/core/config.cpp si existen, con hashes e includes literales. Si una raíz es
   reparse, registrar identidad/link observado; no asumir symlink/cloud ni mutarla.
   No cerrar transitivamente includes de bin/core aquí ni atribuirlos al hijo.
5. Enumerar herramientas instaladas por nombre, sin ejecutar help desconocido que
   pueda lanzar una UI. ConvertWrp/DeWrp no aparecen en el bin Mikero observado;
   pboProject sí. Esto no prueba ausencia en todo el host. Las fuentes web son pistas
   de compatibilidad, no certifican el binario instalado ni DayZ32.
6. Reporte <=4MiB con inventario/lecturas/errores/estado; parcial persistido antes de
   fase. Un límite o I/O produce INCONCLUSIVE, sin reintentos ni prometer informe
   final tras kill. Causa de fallos históricos no establecida. No modificar mapas.

Criterio de término C1A: lista completa de filas de material fuente y observaciones
de rutas dentro de límites, o rechazo explícito. `build_ready=false`,
`dependency_closure=NOT_EVALUATED`, `compiled_terrain_decoder=NOT_VERIFIED` siempre.
Reconciliar conteos y muestras con recorrido independiente sobre bytes guardados;
esto sólo valida el inventario observado, no el formato OPRW ni la compilación.

## Diseño C1B pendiente, no ejecutable en este plan

[DESIGN] Stage exclusivo en E:, sin junction a todo P:/DZ ni configs ajenos. Config
de laboratorio explícita con clase/prefijo propios y lista cerrada de dependencias:
conservar mundo/escala/agua fuente, decidir y documentar referencias a navmesh y
clutter para calibración elevada; no heredarlas accidentalmente. No cambios de
producto ni mar/Narva/P9/P10/P11. Resolver recursos de terreno y bin/core observados,
además de los tres modelos instalados por sus SHA y materiales completos.

[DESIGN] Antes del build: contrato externo, oráculos0/3 y negativos; código nuevo
de preparador y consumidor, revisión/suite. Preflight oficial fresco, copia archivada
con diff literal si persiste SyntaxError conocido, nunca editar skill gobernada.
Una pareja, control primero; no candidato si control falla. Carpetas/sellos nuevos,
presupuestos a fijar con cierre de recursos, sin reintentos internos. Herramientas
instaladas pinadas no equivalen a hijos observados: guardar PID/birth/argv/streams.

Bloqueo del consumidor: localizar o definir lector capaz de establecer offsets y
cuentas0/3 y representación de alturas/materiales de la versión real. Necesita
oráculos y evidencia de versión, no sólo patrón de texto/ID. Si para descubrir el
formato hace falta una compilación exploratoria previa, proponer otra autorización
técnica explícita con estado COMPILE_PROBE_ONLY: sin empaquetado aceptado, despliegue,
motor ni afirmación de preservación semántica. No asumir aquí dicha autorización.

[DESIGN] RoadC2 posterior: paquete/mundo/modelos exactos; sondas que distingan las
cuatro hipótesis B2, control sin objetos y detección de oclusores. Ni personaje ni
proximidad eligen pivote. ColaFIFO600, heartbeat10s, adopciónrunpropio y cierre/release
oficiales. camera_set vetado. Sólo tras esto diseñar huella útil y ambos accesos.

## Referencias y límites de investigación externa

- https://community.bistudio.com/wiki/Binarize (consultado29-10): documenta Arma3,
  no certifica interfaz DayZ instalada. Sirve para preguntas sobre cwd/recursos.
- https://github.com/Braini01/bis-file-formats/issues/24 (consultado29-10): reporte
  primario de incompatibilidadv29, no reproducción local ni evidencia sobrev32.
- https://mikero.bytex.digital/ (consultado29-10): catálogo de herramientas, no
  presencia ni licencia local. No instalar ni comprar herramientas en esta unidad.

Nueve rechazos humanos0resueltos/C1NOT_REVIEWED; RoadC0/C1A no son reparaciones.
Q03C/Q05 pueden seguir midiendo la época histórica sin esperar identidad nativa;
ángulos/referentes/Q08/Q17 conservan sus pendientes. No publicar vanilla completo.
