# Baltic — smoothing y pruebas del 07-10-2026

**Preview del relieve construida, desplegada y probada en DayZ frente a V12; aprobación visual pendiente.** Orillas y Luga siguen en piloto. La base 1.0 no está aceptada.

Continuación autorizada por Guillermo: orillas, cauces y relieve general; «adelante» y «continua, prueba». Trabajo en el árbol de Claude `codex-handoff-review-74f290`, sobre `4382029394f27f7e256fe410eee71285134b449b`. No se modifica `v29-base` ni se sustituyen V11/V12.

## Resultado utilizable

`P:/Mods/@DayZ_Baltic_SmoothingPreview` contiene solo el cambio de relieve seco. Se excluyen las variantes fallidas del Luga y los nuevos contornos vectoriales.

- Terreno NPZ: `E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007/dry-18-corrected/terrain_dry.npz`, SHA256 `164ad4ffbe4177c7615d18e95d12920d4d332612e596377963a54e0281fc608d`.
- Mundo desplegado: `c597062ed8c6b3f8f299c957a6b308c079f938e395e038a20290ebb29cc1ec5a`.
- Agua desplegada: `07c5295f112746d621e96324467b1d54fccc415a785c227feb245f59adff503f`, idéntica a V12.
- El PBO tiene 6.827 entradas; frente al PBO de V12 cambia **solo `baltic_trial.wrp`**. Config, 4.775 materiales, 2.048 texturas y navmesh conservados byte a byte. La navmesh sigue siendo la anterior y no acepta la geometría nueva.
- Verificador del PBO: `PASS_PACKED_CONTENT`, comparación completa con el árbol compilado aislado. Directorio de compilación nuevo, sin reutilizar temporales.

[Comparativa en DayZ](figures/relieve-en-dayz.png) · [Comparativa offline del relieve](figures/relieve-comparativa.png) · [Comparativa del Luga](figures/luga-comparativa.png) · [Recibo de despliegue](reports/deploy-receipt.json).

## Relieve seco: PASS offline y despliegue confirmado en motor

Se probaron sigma 18 y 24 m desde V12, sin aplicar una variante sobre otra. Las primeras variantes conservaban las protecciones pero excedían el límite regional de 10 cm y no reducían suficiente la curvatura en zonas altas. La única corrección de este piloto usa saturación suave y retira la componente regional después de aplicar las protecciones.

Variante 18 m corregida:

| Medida independiente | Resultado |
|---|---:|
| Reducción RMS de curvatura local, conjunto | 21,02 % |
| Zonas altas | 10,21 % |
| Llanos | 25,92 % |
| Cambio máximo a escala regional de 180 m | 0,066013 m |
| Cambio local máximo | 1 m, tolerancia float32 <0,00001 m |
| Vértices cambiados | 2.494.070 |
| Carreteras | 77.381 estaciones, PASS y resultado idéntico a V12 |
| Nuevas caras de tierra más inclinadas por encima de 35° | 0 |

Clases, niveles, agua, playa, plataformas, reservas viales y Narva idénticos. Máscara de reserva natural y 66 cimas regionales protegidas idénticas. Agua y banda de 36 m excluidas; transición de 60 m junto a protecciones. Controles negativos: edición de vértice protegido y cambio de clase rechazados.

El verificador general sigue dando **FAIL heredado**, con todos sus valores idénticos a V12: 1 vértice de calado, 21 esquinas de piezas y comparación histórica de Narva no idéntica. No se presentan esos fallos como resueltos ni se confunde exit 0 del script con PASS del informe.

Código: `tools/terrain/smooth_dry_relief_v30.py`. Consumidor: `scripts/check_dry.py`; [resultado](reports/dry-independent-18-corrected.json).

## Contornos de orillas: defecto previo confirmado; modo estricto validado en vectores

La función anterior limita cada punto antes de `make_valid` y de los dos buffers de recuperación de área. El contorno final no conserva necesariamente ese presupuesto ni las islas. Comparación contra el diseño original congelado, que incluye geometrías válidas:

| Sigma | Contornos finales con distancia muestreada >4 m | Cambios de número de islas |
|---|---:|---:|
| 12 m (actual) | 305 | 46 |
| 18 m | 313 | 55 |
| 24 m | 312 | 55 |

Ejemplo real: Oredezh (`water_v3` índice 87, `river_051`) pasa de 71 islas interiores a 31 en 12 m y a 23 en 18/24 m. La distancia máxima entre límites llega a 31,28 m por pérdida de límites interiores; no significa que toda la orilla exterior se traslade 31 m.

Añadido `--strict-outline-limits` a `smooth_water_outlines_v30.py`: conserva islas y zonas de contacto originales, prueba atenuaciones fijas 1 / 0,5 / 0,25 y conserva el original si no satisface simultáneamente validez, área ±2 % y envolvente continua de 4 m. La ruta histórica queda disponible para reproducir V11/V12.

La variante estricta 18 m cambia realmente 76 geometrías; no deben confundirse con las 659 **tentativas** del campo histórico `smoothed`. Distancia máxima muestreada 3,9383 m; comprobación continua dentro de 4 m; cero pérdidas de islas y cero separaciones de contactos dibujados >0,05 m. El auditor incluye arroyos tier>=2500 y excluye bandas `river_contour_*`, que solo transportan niveles y no son cuerpos dibujados. Dos falsos positivos del primer auditor correspondían precisamente a esas bandas; se conservan los resultados originales y se documenta la corrección del consumidor.

**No se integra:** esta variante conserva más geometría pero no mejora la suavidad frente a los 12 m actuales en todas las clases. Subir sigma con un desplazamiento acotado no garantiza menos esquinas. Los cuatro tests de regresión y el selftest histórico pasan. [Informe independiente](reports/outline-independent-18-strict.json).

## Luga: mejora prometedora, FAIL por dos regresiones locales

13.197 estaciones congeladas sobre el contorno original, separadas 2 m; agua de los triángulos nativos, búsqueda ±8 m con paso 0,25 m. Se excluyen puntos protegidos, borde/Narva y contactos con otros cuerpos. No se rellenan huecos para calcular curvatura. Oeste, centro y este se juzgan por separado.

| Variante | Zigzag RMS total | Estado |
|---|---:|---|
| V12 / 12 m | 0,6404 m | Referencia |
| Sigma 18 m sobre campo raster | 0,7079 m | FAIL |
| Sigma 24 m sobre campo raster | 0,7690 m | FAIL |
| 18 m, perfil sobre distancia al contorno vectorial | 0,4705 m | FAIL: este |

La última prueba conserva exactamente los vértices de todos los corredores, metadatos y terreno fuera de la máscara autorizada. Reduce el zigzag un 26,5 %, pero en el este los cruces no encontrados dentro de ±8 m pasan de 68 a 70. Un diagnóstico adicional amplió la búsqueda a 16 m **sin cambiar el gate**:

- X=10267,750; Z=3854,120: cruce de +7,875 m a +10,625 m.
- X=10320,139; Z=3991,598: cruce de −0,125 m a +8,625 m.

Por eso no se incorpora al paquete. Siguiente corrección requiere tratar esos vértices/triángulos y demostrar todas las puertas, no relajar la tolerancia ni aceptar por promedio. [Mediciones](reports/luga-independent.json) · [puntos](reports/luga-new-missing.json).

## Render y runtime

El primer lanzamiento de V12 (`b4d19d6e-5aa1-4adb-8f24-961deb92e82b`) llegó a servidor/cliente vivos y jugador conectado. No se obtuvo una comparación controlada: Codex mantenía el catálogo compacto y faltaban cámara/teletransporte. Tras reconectar perdió la identidad propietaria; el run quedó protegido y se dejó cerrar al gestor de inactividad. No hubo kill ni adopción forzada.

Configuración mínima, con respaldo local: `C:/Users/guill/.codex/config.toml`, argumentos del MCP normal, añadido `--no-progressive-disclosure`. Opción existente en `P:/DayZ_MCP_dev/tools/dayz_mcp/server_cli.py:554`; muestra el catálogo y conserva el gate de lease. Los procesos nuevos de las 21:12 ya llevan la opción y cámara, teletransporte y captura son ahora invocables.

El bloqueo temporal de puerto 2302 por LFSkateboard terminó por su propietario. Después de verificar que ambas instancias MCP veían el banco libre, se ejecutaron cuatro runs propios; no se intervino en el run ajeno.

### Teselas: síntoma reproducido y recuperación parcial registrada

Run V12 `f8d4e477-165d-4c38-b4cd-d64e13d0b11c`, DayZDiag 1.29.163709. Teletransporte desde aparición oeste a (6081,4966), cámara absoluta (6081,85,4966), mirada (6081,2,4700), FOV solicitado 1,1955505. A los 4 min 18 s la tierra seguía gris; a los 8 min 56 s aparecieron teselas texturizadas y a los 14 min 29 s se había recuperado gran parte de la vista. `surface_query(6081,4700)` devuelve tierra seca, `cp_conifer_common1`, Y=6,845251 m. No se juzga el agua con un índice global de oscuridad.

Dos registros de foco: 178 muestras de 21:29:23 a 21:32:22 y 593 de 21:34:21 a 21:44:20; todas `False`. **Existe un intervalo sin registro entre ambas sondas.** La segunda empieza todavía con la tierra gris y contiene la recuperación parcial sin foco registrado. No hubo el intervalo activo solicitado: prueba causal del foco **INCONCLUSA**. El reloj de esta misión original avanzaba (se leyó 12:10), aunque cámara y geometría permanecieron fijas. El aviso `render_frozen_signal` también apareció sobre vistas estáticas correctamente texturizadas: no equivale a proceso colgado ni prueba por sí solo congelación del render.

[Serie visual](figures/render-v12-unfocused.png), [medición diagnóstica de tierra](reports/render-v12-unfocused.json), [registro de foco continuo](reports/focus-v12-nav85.csv) y [metadatos originales](reports/runtime-v12-record.json). Fotogramas completos y sonda a 1 Hz conservados en E:.

Control de aparición directa, mismo paquete V12: run `b63e7661-ecd1-42ed-a72f-b1ce05ec99ae`, misión aislada `BalticRenderNavControlV1.BalticTrial`. `CreateCharacter` crea al jugador directamente en (6081,4966), sin teletransporte posterior; mediodía congelado. La primera captura con la misma matriz de cámara ya muestra tierra texturizada. También se obtuvo una vista del cauce real del Luga mirando a (5905,547;5184,845), un punto interior del polígono: el centro aproximado de 77 ha del handoff cae en tierra. Es un procedimiento práctico para vistas, **no una causa raíz aislada**: foco durante arranque no instrumentado y viewport distinto (1920×1080 frente a 2891×1648 del run anterior). [Registro](reports/runtime-direct-nav.json).

### Comparación V12 / preview del relieve

Runs `b1da273f-3771-4be8-912d-a48c36e6258c` y `5cb12f16-8adb-4f56-82ad-f27e436c7b90`, misma misión aislada `BalticRenderDryControlV1.BalticTrial`, aparición (6192,8466). Dos matrices de cámara idénticas, viewport real 1920×1080 y reloj leído a las 12:00 antes/después. Las dos vistas de cada paquete tienen tierra texturizada; el efecto visual del smoothing es moderado con el límite de 1 m.

| Punto X,Z | V12 leído en motor | Preview leída en motor | Cambio |
|---|---:|---:|---:|
| 6060,8346 | 59,361595 m | 58,361595 m | −1,000000 m |
| 6324,8190 | 16,663990 m | 17,653690 m | +0,989700 m |

Ambos valores coinciden exactamente con los NPZ independientes; usar V12 como si fuera la preview falla el control negativo de paquete obsoleto. **PASS_DEPLOYED_HEIGHT_AND_MATCHED_POSE_ONLY**, no aceptación del mapa entero. FOV solicitado igual; el getter MCP devuelve cero, de modo que no hay lectura nativa del FOV. [Comparación](reports/runtime-comparison.json), [imágenes](figures/relieve-en-dayz.png), [misiones y hashes](missions/receipt.json).

Los cuatro runs terminaron por cierre ordenado cliente→servidor. Lease liberado; `session_status`: owner=null, runs=[], box.occupied=false, pending_commands=0. [Lifecycle](reports/runtime-lifecycle.json).

BALTIC-019 sigue abierto: falta aislar foco, comprobar bandas cerca/media/lejos de forma completa y repetir el control Chernarus/retail si procede. No cambiar materiales para corregirlo sin ese discriminador. BALTIC-018, lancha V12, finales Volkhov/Grib/Msta, RIVER_80, lagos 269/170, Terrain Builder y nueva navmesh siguen pendientes. No hubo travesía de lancha ni aceptación del agua por estas capturas.

## Reproducibilidad y límites

Intérprete GIS existente: `C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe`, UTF8 y sin bytecode. Parámetros, presupuesto y gates anteriores a las variantes: `spec.json`. Salidas grandes, registros y variantes fallidas conservados en `E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007`.

Repetir generación siempre con destino nuevo. `scripts/build_dry_preview.ps1` documenta la cadena exacta ya ejecutada y rechaza destinos existentes. Se ha agotado la ronda de baseline + dos intensidades + una corrección por ámbito; no continuar probando sigmas sin revisar el mecanismo.
