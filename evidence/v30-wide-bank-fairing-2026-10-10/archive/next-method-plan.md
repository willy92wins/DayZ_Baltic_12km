# EV90 — revisión explícita del método de forma (propuesta antes de candidato)

EV88-Q permanece rechazado y sin desplegar. No se cambian sus informes ni se
recalibran sus umbrales. Este documento propone otro contrato local, todavía
sin solver autorizado, para el mismo foco y ventana sobre EV82-B.

## Problema del contrato anterior

La condición por cada fila/columna impide cualquier alpha positivo del camino
B→Q, aunque desaparezca la pirámide y disminuya la energía de quiebros. En el
alpha mínimo para mejorar el foco, el supuesto empeoramiento de una fila es
6.75 mm. La condición de ventanas casi planas usa el percentil de la propia
base defectuosa: confunde una pendiente suave nueva con una meseta producida
por recorte. Son heurísticas de método, no requisitos solicitados del mapa.
El análisis de intervalos queda en line-feasibility; no demuestra seguridad
del agua ni que Q deba aceptarse.

## Ámbito e invariantes que se conservan

Misma B, EV79, P/F, geometría compilada y ventana17/core13/collar2 de EV88;
protecciones, metadatos, objetos, fondo1m y calado0.95m intactos. Ningún cambio
de nivel, cauce mojado, modelos o agua se autoriza por este piloto.

Antes de autoría, inventariar en la ventana todas las celdas con una cara
compilada por encima de su campo nominal más la tolerancia ya fijada,
incluidas las caras enterradas. Congelar a B sus cuatro vértices. Esto elimina
la posibilidad de aumentar exposición en esas discrepancias heredadas. No
confundirlas con agua visible. Si el foco queda fijo o no hay libertad material,
parar como diseño inviable; no quitar esa protección para obtener resultado.

El consumidor comprobará no regresión local de cobertura, no nuevos huecos,
exposición o dominios F desconocidos afectados. Los fallos absolutos heredados
seguirán abiertos. Para corredores, toda cara afectada debe tener campo válido
y calado aprobado; la identidad exacta B/H de caras desconocidas conserva una
limitación heredada, no un PASS absoluto mundial.

## Autoría propuesta [DESIGN]

Misma energía cuadrática y BVLS de EV88, una sola llamada con deadline120s.
Reconstruir dominio y cruces tras las nuevas protecciones; no reutilizar98
variables ni397 stencils como constantes. Convertir ANTES del solve cada
cota inferior a la menor altura float32 >= cota, y cada superior a la mayor
float32 <= cota. Rechazar intervalos vacíos. El solve usa esos límites exactos;
una única conversión final float32, sin reparación posterior ni barrido.

## Forma propuesta [DESIGN]

- Foco: prominencia positiva reduce al menos25% en ambos ejes, sin mínimo
  estricto nuevo; ángulo máximo incidente reduce al menos2 grados.
- Energía fija de stencils reduce al menos25%; energía y máximos angulares
  del collar no empeoran. Se conservan pendientes, máximos por sector,
  ausencia de nuevas bisagras>30.0001 y p99/conteos globales anteriores.
- Medir prominencia cardinal positiva de TODOS los nodos del núcleo y halo.
  En cada eje, exigir que máximo y suma de cuadrados no aumenten. Informar
  cada nuevo extremo y su magnitud, sin exigir que caiga en la misma fila ni
  inventar un límite milimétrico ajustado a Q.
- Ningún nuevo mínimo estricto de ocho vecinos (hoyos); controles positivos
  rampa y negativos foso. Ninguna nueva ventana2x2 exactamente constante tras
  cuantizar cuando B no lo era (meseta por clipping). Las ventanas casi planas
  quedan como diagnóstico con el tau anterior, nunca ocultas ni renombradas.
- Inspección de cuatro perfiles cardinales/diagonales y malla a escala real:
  puede rechazar una deformación aun con métricas favorables. Esto no es
  aceptación gráfica en DayZ ni autorización de extensión global.

## Revisión y presupuesto

Revisión independiente del método y preflight de viabilidad antes de generar
un candidato. Fixtures de fórmula/recortes/float32/orientación/rampa-foso y
mesetas; no usar cantidades de checks como prueba del terreno. Si inviable,
conservar B y explicar la restricción. Si viable y aprobado por integrador,
una candidata local; consumidor completo una vez tras fixtures. Sin build
antes del resultado y sin presentar estática como envolvente de oleaje.
