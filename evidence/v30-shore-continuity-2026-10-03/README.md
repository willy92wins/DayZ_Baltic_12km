# Orillas, lagunas y continuidad V30 — sesión autónoma del 03-10

**Estado del bloque:** candidato geométrico y paquete preparados; importación
nativa, prueba del motor y navmesh propia pendientes. La ventana de ocho horas
terminó con el entorno bloqueado: [recibo de cierre](session-window.json).
La parte posterior fue espera por disponibilidad, no implementación efectiva.
No es una entrega 1.0 ni sustituye el mod aceptado anterior.

## Cadena del candidato

| Paso | Identidad / resultado |
|---|---|
| Fuente aceptada del delta | a84dfff0, desplegada antes de esta sesión |
| Acabado de orillas corregido | 73b01bb4; 49.717 vértices retocados; 23 corredores conservados |
| Cuatro lagunas recuperadas | 2f954ad5; 75 alturas, 72 vértices nuevos de agua, 166 celdas de plano |
| Continuidad de cauces pequeños | **40d8cfd9**; 22.468 alturas adicionales, 712 de fondo ya mojado en la reserva |
| ASC para importar | dacc8e55, 2048², celda 6 m, origen de ingeniería 200000/0 |
| Paquete vigente, deduplicado | mundo **e556f576**, agua **339fa17f**, copiado en mod aislado; sin ejecutar |
| WRP compilado vigente | 0255d007d173efbd88832a0193725af843a3ba930ea360112b4f98737d650dd2 |
| Paquete anterior, conservado | mundo572d4124 / agua371ece8a; geometría equivalente |

Artefactos grandes en `E:/DayZ-Baltic-Build/v30-watercourse-continuity`, paquete
en `v30-continuity-dedup-package`. [sources.json](sources.json) identifica las fuentes
de los recibos copiados o resumidos. Los incrementos de vértices pueden solaparse;
no sumar las tres cifras como total de vértices distintos.

## Qué se ha comprobado

- [Revisión geométrica](continuity-review.json): ámbito, límites, metadatos,
  reserva seca, ingeniería, 23 canales y ASC. Cero caras >35° nuevas o empeoradas.
  El acabado de orillas redujo el inventario de caras mixtas >35° de 4.149 a 4.000;
  ese recuento no equivale a defectos visuales confirmados.
- [Carreteras históricas](road-gates-historical.json): 100 cadenas y **76.536
  estaciones**, cero fallos. Se conserva la máscara original de elegibilidad;
  los recibos intermedios de 76.513 estaciones no son la cobertura final.
- [Terreno legado](legacy-terrain-gates.json): **FAIL** exclusivamente en la
  igualdad del antiguo círculo de Narva, por las cuatro lagunas documentadas.
  No se ha ocultado ni relajado; [pond-review.json](pond-review.json) acredita
  el ámbito exacto de la excepción.
- [Paquete](package-contents.json): 6.827 entradas, 4.775 materiales y 2.048 PAA,
  con paridad de bytes frente al árbol compilado.
- [Reutilización del agua](water-reuse.json): planos exactos. La apertura previa
  del delta cambió 358 celdas de clase seca a mar, sin cambiar piezas pond.

## Continuidad parcial, sin falsear el resultado

En el eje de 40 ríos y 37 arroyos, fuera de plataformas y su halo triangular:

| Medición | Ríos | Arroyos |
|---|---:|---:|
| Seco antes | 381 m | 12.045,5 m |
| Seco después | 30 m | 399,5 m |
| Por debajo de 5 cm después | 42 m | 511 m |
| Cortes secos de al menos 6 m | 1 | 21 |

Los ejes también los usa el constructor: **autoconsistencia**, no consumidor
independiente. [Resumen completo](continuity-after-summary.json) incluye dos
líneas laterales, plataformas y halo por separado. Cuatro ríos sin perfil
longitudinal quedan fuera de este muestreo. No acredita navegabilidad de arroyos.

[22 casos localizados](residual-cases.json): diez con vértices protegidos, uno
en el borde, uno limitado por cotas de fondo/banco, diez tras restaurar taludes.
La causa se clasifica en el punto medio, no en cada punto del corte. Un intento
conjunto de pendiente/profundidad, en nueve grupos, no dio ninguna solución
admisible: [resultado](joint-slope-attempt.json). El terreno se conservó íntegro.
No demuestra imposibilidad matemática ni autoriza relajar las restricciones.

## Preparado para el consumidor

- [Siete vistas](atlas/sites.json), con perfiles y línea de agua geométrica.
- Misiones V4 normal y sin cliente: **1.332 puntos**, de ellos 1.076 distinguen
  alturas antiguas/nuevas. Incluyen las cuatro lagunas y los casos residuales.
  Linter de cada misión PASS, un archivo examinado; ejecución pendiente.
- Fuentes nativas 12.288²: satélite/máscara exactos, 3.968 solapes comprobados.
  Biblioteca de agua preparada, importación nativa todavía pendiente.
- NavMeshGenerator instalado: ayuda CLI y rechazo sin ruta observados. Wrapper
  preparado en `tools/navigation/generate_navmesh_console.py`; generación real
  aún no probada. El paquete contiene **NM V29 provisional eb0f131e**, no válida
  como aceptación de la geometría nueva.

Computer Use perdió el transporte; recuperación pendiente del cliente Codex.
La caja DayZ sigue ocupada por un run ajeno @LFRider/@LFH2R. No hay run ni lease
propios. Continuar por HANDOFF y el plan de esta sesión, sin tocar esos procesos.

El [consumidor de navegación nuevo](nav-consumer/reference.json) conserva13casos
históricos y añade24trayectos en orillas secas retocadas. No se ejecutó ni está
copiado a mpmissions. [Controles offline](nav-consumer/offline-controls.json):
dos positivos, quince negativos y linter de un archivo PASS. Las comprobaciones
de terreno y proximidad a superficie física no sustituyen la prueba de actores.

## Deduplicación exacta y preparación nativa

La copia deduplicada usa **8.775 modelos en vez de13.434**, con las mismas17.637
instancias. Cada sustitución coincide en bytes MLOD y ODOL; el mundo conserva
altura, materiales, poses, IDs y los nueve puentes. Solo cambia el nombre del
recurso de4.659 instancias. PBO de agua:34.254.192→24.715.347bytes. No se ha medido
mejora de FPS, memoria o carga. Recibos en [dedup](dedup/sources.json).

El mod nuevo y misionesV4 están copiados y comprobados. Un lease breve protegió
la copia y se liberó. El intento de arranque06:10UTC fue rechazado por ocupación
externa del puerto; no se creó ningún run y no quedó petición en cola.

La biblioteca nativa de8.775 plantillas incluye una pieza asimétrica separada
para comprobar altura absoluta y autocentrado antes de importar el lote.
La referencia WRP de prefijo local **1a9cf270** es una referencia esperada,
**no una exportación del editor**. Instrucciones exactas:
[continuación nativa y motor](../../plans/v30-continuity-native-runtime-resume.md).

[Vista general](overview/overview.png) y [PDF](overview/overview.pdf): ilustración
geométrica offline, con carreteras reservadas, ámbito de naturaleza y22cortes
residuales. No es una captura del juego ni una medición de superficie inundada.
