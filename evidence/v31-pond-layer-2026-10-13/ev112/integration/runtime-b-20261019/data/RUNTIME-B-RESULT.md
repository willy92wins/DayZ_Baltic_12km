# EV112 — servidor completado; vista personal preparada

Cierre 2026-10-20T00:26:52.122007+02:00. Corregidos los cuatro controles nuevos detectados por la primera sonda. El paquete final supera los controles obligatorios del servidor y la comprobación temporal. **El AND estricto y G8 del kit permanecen FAIL por 271 labios/juntas de hormigón**, pendientes no bloqueantes según el plan §5. No se ha cambiado ningún umbral ni concedido una excepción nueva.

| Comprobación | Resultado |
|---|---|
| Sonda completa | 4114 filas válidas, capturadas antes de cerrar el servidor |
| Kit obligatorio | 2450/2450 PASS; 278 puntos adicionales son referencias sin expectativa juzgada |
| Hormigón vanilla | 271 pruebas secas pendientes; mismos IDs que en la primera sonda: True |
| Puentes | 10/10 PASS, sin regresión frente a EV110; 015-18 6/9→9/9 puntos mojados |
| Orillas | 50/50 mojadas, 50/50 secas; 10/10 parejas de islote |
| Presa | 178/178 puntos; consumidor independiente PASS |
| Temporal | 30 muestras de los mismos 8 puntos: cuatro corregidos y controles conformes en todas las muestras |
| Revisión independiente OT7 R2 | SOUND-with-fixes; cero críticos/mayores abiertos |
| Vista personal | 16 archivos instalados y comprobados por hash; ruta y solicitud de lanzamiento preparadas. Cliente no lanzado |

## Corrección física y prueba

La primera sonda y el diagnóstico temporal demostraron que cuatro controles cambiaban de signo con el oleaje. Se descartó sustituir la profundidad por flags/NoFakeWave: esa propuesta producía 190 rechazos adicionales. También se descartó el candidato A, que reducía el margen del control seco vecino del islote. No hubo permiso adicional ni waiver para estos controles.

La capa reproducible `tools/terrain/apply_engine_water_margins_v31.py` cambia exactamente cuatro vértices del terreno C: un eje del kit baja 0,15 m, dos restos de lecho suben 0,19 m y un vértice enteramente submarino baja 1,577194 m. La última corrección conserva la costa local y la altura del control seco vecino. Todas las máscaras, la huella de agua y el grafo de conectividad permanecen idénticos. Pendiente máxima incidente: 23,1373°; ninguna protección tocada. Los dominios completos de c2–c7 permanecen idénticos.

| Punto global / tipo | Profundidad primera sonda (m) | Profundidad final (m) | Rango temporal final (m) |
|---|---:|---:|---|
| 2733 / kit_axis | -0.03286190 | 0.11239600 | 0.11235900 .. 0.23989100 |
| 3807 / old_bed | 0.04220630 | -0.14779400 | -0.29355000 .. -0.11475800 |
| 3808 / old_bed | 0.04870670 | -0.14129300 | -0.31990400 .. -0.12899300 |
| 3836 / shore_wet | -0.00720781 | 0.15297600 | 0.15297600 .. 0.39596400 |

La discrepancia máxima suelo motor/NPZ entre las cuatro familias de la sonda es 0.00109759 m. Esto vincula la carga observada al terreno corregido en los puntos muestreados; no decodifica toda la matriz binarizada.

## Paquete y validación offline

Se conservan exactamente los 2.561.015 registros de bosque y los 2.578.916 objetos totales. El staging conserva los registros byte por byte; la lectura independiente del WRP compilado vuelve a verificar modelos, IDs y matrices. G1 y G4 del bosque se ejecutaron de nuevo sobre el terreno B; los cinco consumidores del bosque pintado usan el PBO final. Las seis puertas de superficie pasan contra las PAA empaquetadas. El agua se conserva por identidad de las cuatro arrays de huella y de su PBO.

Las 45 etapas conocidas, las 50 etapas de holdout y los seis positivos/25 negativos del bosque AE se heredan por identidad de fuente/registros y por la nueva ejecución de los consumidores afectados. No se reutilizan semillas como si fueran nuevas ni se declara un PASS global de todas las ventanas.

- Mod: `P:\Mods\@DayZ_Baltic_EV112_RuntimeMarginsV2`.
- Mundo SHA256: `751823ac65cd56c9093de9705ee30b08a448a69606690c1363ecf944a15ac838`.
- Agua SHA256: `97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43`.
- Terreno SHA256: `07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62`.
- Fuente de corrección: commit `eb77548bbfe7394db014b3000d9bd45add26a9c4`; sin push.

El paquete anterior permanece intacto. El lanzador público funcionó; no se renovó su bundle ni se modificó el registro de Steam.

## Pendientes y alcance

- **015-45:** disco protegido de 60 m pendiente, nunca PASS.
- **Hormigón:** las juntas/labios conservan su FAIL estricto. Su solución está fuera del cierre no bloqueante aprobado en §5; no se confirma aquí su comportamiento en Chernarus.
- **Calzadas:** p90≤0,03 m corresponde al dominio central aceptado. Los 1.491 vértices exteriores con agua (538 en tramos G2) conservan sus métricas, hasta 0,11791 m.
- **Fases:** G9/G11 del kit sobre el terreno final siguen FAIL, idénticos medida por medida a C. El G7 histórico de orillas conserva cuatro vértices C7 sustituidos por la fase posterior. Los intentos fallidos y sus logs se conservan.
- **Bosque:** G8 sin exenciones por ventana, con exclusiones estructurales de Narva/kit/puentes. Permanecen las limitaciones de 124 traslaciones fuera del recorte de mutaciones, tres filas diagnósticas de juncos G9 y el fallo regional G2/G3. La identidad G9 compara 243.157 objetos a 20 m del borde, no a 40 m.
- **Motor:** la prueba temporal abarca aproximadamente un minuto con clima fijo. No acredita todos los climas, humedad del jugador, aceptación visual, FPS ni capacidad para 80–100 jugadores.

## Continuidad y evidencia

Sonda final: `06e21c19-4c00-4119-88a8-297f7854e6bc`. Diagnóstico final: `07002c95-df79-4116-a993-57e46b457b85`. Ambos capturados antes del cierre ordenado, retirados y con lease liberado. Las dos ejecuciones originales también se cerraron. No queda run ni lease propio.

Para la vista: `personal-view-runtime-b/README.md`, `route.json` y `launch-request.json` en el build. Misión instalada `BalticBasicEV112.BalticTrial`, aparición en Narva. Comprobar disponibilidad del banco y adoptar la ejecución propia después del lanzamiento público; mantener heartbeat durante la visita.

Evidencia original y final en `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/`: `runtime-b-closure.json`, `deploy-runtime-b.json`, `build-review-closure-runtime-b.json`, `runtime-capture-runtime-b-20261019/`, `runtime-eval-runtime-b-20261019/`, `water-temporal-runtime-b/` y `water-fix-b/`. Los recibos anteriores `reviewed-ae-awaiting-runtime` y la primera sonda se conservan como historia, no como estado actual.

La documentación global del vault conserva fallos de enlace y un pin del generador ajenos a esta tarea. Este cierre no los convierte en PASS ni modifica gobernanza global; valida sus propios enlaces y conserva el contenido ajeno de la parada Baltic.
