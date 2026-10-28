# Sonda completa de lecho y carretera: FAIL nativo registrado

La medición completa conserva **FAIL**. No es una reparación aceptada ni un
cierre de calidad. Se midieron los 2658 puntos originales con una calibración
vanilla nueva; ambos runs propios se cerraron oficialmente y liberaron el lease.
La identidad de proceso, misión, ejecutable, cuatro PBO y logs quedó vinculada.

| Canal | PASS | FAIL | INCONCLUSO |
|---|---:|---:|---:|
| Terreno | 2658 | 0 | 0 |
| Roadway | 2638 | 0 | 20 |
| Agua | 2599 | 43 | 16 |
| RaycastRV | 2648 | 5 | 5 |
| Bullet BUILDING | 2650 | 3 | 5 |

Son 51 fallos de canal en 47 puntos únicos, y 46 canales inconclusos en los
21 puntos ya declarados inciertos antes de ejecutar. No se eliminaron IDs,
reclasificaron fallos ni cambiaron tolerancias.

Calibración: margen 0,03999144638858333 m; rango
0,039988754257876985–0,0399953942907385 m. Dos rejillas completas de 289
posiciones; cinco impactos sobre la referencia vanilla y 289 controles de
espacio vacío. No se sustituyó por la calibración histórica de los tests offline.

La clasificación posterior conserva estos hechos y sus límites:

- Los 41 controles esperados mojados que fallan tienen lecho por encima de
  water_ext. Los 96 mojados decisivos con agua sobre el lecho dan pond=true.
  La correlación no demuestra por sí sola cómo decide el motor.
- Dos controles secos dan pond=false pero profundidad positiva consultada en
  terreno +0,01 m; no se ha descartado ese criterio para hacerlos pasar.
- En 349, 350 y 1425 los rayos altos golpean una copa de haya, entre 17 y 19 m
  sobre el lecho. Esto no prueba que su tronco invada la carretera o el cauce.
- En 700 y 723 RaycastRV devuelve terreno mientras Bullet alcanza el lecho.
  La causa todavía no está aislada; no se han desplazado estos puntos para ocultarla.

Hace falta discriminar las expectativas del consumidor frente al mapa real
antes de diseñar la siguiente corrección procedural. Se mantendrán referencias
independientes del agua que debe conservarse y de los corredores jugables.
C1, nueve regresiones visuales, RAM, calidad global y council ampliado siguen abiertos.

Una admisión anterior fue rechazada porque el caller transformó las barras
Windows de la ruta sellada. El predicado real del MCP reprodujo el rechazo;
usar el campo mission exacto del gate resolvió la llamada sin cambiar política,
preparación, paquete o misión. No es un fallo de generación del mapa.

Los archivos raw son evidencia de ejecuciones consumidas. No relanzar misiones,
coordinadores ni consumidores sobre esas salidas. El código usado está publicado
en la unidad dry-road-full-offline-20261028; los modelos vanilla y PBO permanecen
fuera del repositorio público.

## Contraste offline A, revisado independientemente

Fable 5.1 revisó el plan en 314,156 s. Se incorporaron sus ocho observaciones;
la revisión sólo permite diagnóstico offline, no lanzar la microsonda B ni
alterar el mapa. La copia exacta del plan revisado se conserva por hash.

Se analizaron los 47 puntos fallidos y 21 inciertos, más 47 controles positivos
locales elegidos antes del cálculo: 115 puntos en total. Se usaron PBO/ODOL
reales, poses WRP, caras Geometry/Roadway y máscaras originales del generador.
Cuatro fixtures analíticas/de rechazo comprobaron proyección, pose y hashes.
Tiempo: 15,094 s; pico de memoria comprometida 151891968 bytes.

Los 43 fallos de agua tienen B anterior = B candidato exactamente en el
soporte proyectado; sus 16 vértices y 27 centroides quedaron trazados al
dominio y las protecciones. Los vértices 700/723 conservan seis caras de
soporte Geometry cada uno. Esto acota la investigación, pero no prueba que
la respuesta nativa anterior fuera idéntica ni explica la semántica opaca.

La profundidad consultada no coincide simplemente con surface−(H+0,01):
el residuo también varía en controles positivos. Las normales RV no son
unitarias en estos registros; no se han usado como una normal física asumida.

**INCONCLUSIVE_PRODUCT_REFERENCE**: todavía falta fijar un referente independiente
de qué agua debe quedar accesible en esos puntos. Conservar una fuente anterior
defectuosa no valida su estética ni autoriza a convertir sus fallos en secos.
El resultado nativo original sigue FAIL. La siguiente unidad necesita productor,
consumidor, controles y revisión propios antes de una nueva admisión oficial.
