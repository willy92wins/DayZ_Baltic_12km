**Veredicto: SOUND-with-fixes.** La unidad está acotada, no inventa umbrales físicos y mantiene los nueve rechazos abiertos. Hay cuatro puntos que deben corregirse en el contrato antes de escribir arrays o consumidor.

**Fixes obligatorios**

- **Arco regular no es representable con racionales exactos.** Un polígono equiangular con coordenadas racionales solo existe para el cuadrado. Redefinir "arco circular poligonal regular", "transición recta-arco" y "escalera con esquinas redondeadas" como vértices racionales sobre un círculo (puntos pitagóricos, radio² racional). La expectativa analítica exacta es `|p-c|² = r²` por vértice y el conteo; la regularidad angular no se afirma ni se mide. Las esquinas redondeadas pasan a chaflán o a puntos pitagóricos declarados. Si no, el consumidor acabaría necesitando una banda de tolerancia, que el plan prohíbe.
- **Cierre: una sola convención.** Fijar cerrado = flag explícito con primer vértice distinto del último. El consumidor rechaza primer==último en cualquier fixture, y rechaza flag abierto con endpoints coincidentes. Sin esto "convertir cerrado a abierto" y "soldar" son ambiguos.
- **Filas humanas sin coordenadas, sin excepción.** Las nueve tienen `UNCONFIRMED_CONTEXT_ONLY`. El consumidor debe exigir GEOMETRY_UNBOUND en toda fila cuyo location_status sea ese valor, y rechazar cualquier campo de geometría, vértice o testigo en la parte 1. Añadir negativo: fila humana con coordenadas inventadas.
- **Prohibir cobertura implícita.** Un fixture "L abierta" se leerá como cobertura de NARVA-VIS-01. Si se quiere una referencia, el campo debe llamarse `analogy_only` y el consumidor rechaza cualquier campo tipo `covers`, `resolves` o lista de IDs humanos dentro de fixtures sintéticos. Las métricas de sensibilidad declaran denominador sintético, nunca "defectos reales detectados".

**Self-oracle: aceptable con dos precisiones.** El manifiesto externo debe hashear los bytes literales del array tal como se escriben a mano, no una serialización del generador, y vivir fuera del directorio de salida. El consumidor recibe el hash del contrato anterior como argumento, no lo lee del corpus; así la co-mutación corpus+manifiesto falla contra el contrato pinado. Los metamórficos están bien limitados; documentar que inversión de orden cambia el signo de giro y que cambio de inicio solo aplica a cerrados.

**Calibración sintético/humano: correcta.** `natural_positive_count=0`, `calibration_ready=false`, la curva suave etiquetada como referencia sintética no aceptada. Añadir el enum de rol explícito (`SYNTHETIC_SMOOTH_REFERENCE`) para que ningún consumidor posterior lo confunda con NATURAL_GOOD. El par círculo DESIGNED/UNCLASSIFIED cumple su función: misma geometría, intención distinta, sin veredicto de producto.

**Alcance:** la frase "permite descubrir omisiones" es hipótesis, no resultado; dejarla como tal. El corpus habilita a Q02B, no detecta nada por sí mismo. Sin PASS de mapa, sin vínculo con 11921 testigos, sin cambio del ledger Q01: correcto.

**Sin aceptación accidental:** el consumidor debe reafirmar `resolved_count=0`, los nueve `OPEN_REJECTED` literal y C1 `NOT_REVIEWED`; cualquier desvío es REJECTED_CORPUS. Ningún estado de salida contiene la palabra ACCEPTED. Controles de alcance se conservan por dimensión sin préstamo (calzada49 ≠ río49).

**Presupuesto:** viable. ≤20 fixtures, ≤4096 vértices, aritmética racional con `fractions`, un productor y un consumidor en 30s/256MiB. No hay umbral físico inventado; los límites son de tamaño de artefacto.

**Condición de cierre de la unidad:** salida VERIFIED_CORPUS_INCOMPLETE_CALIBRATION con los cuatro fixes incorporados al contrato, hashes publicados antes del consumidor, y los negativos ampliados con los dos nuevos casos (coordenadas en fila humana; campo de cobertura en fixture sintético).
