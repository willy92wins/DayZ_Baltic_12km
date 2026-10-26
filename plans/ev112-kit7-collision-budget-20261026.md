# EV112 — reducir la colisión de kit-7 sin cambiar sus superficies

Continuación del plan de ríos y optimización autorizado. El candidato kit-7 ya supera la revisión MLOD de extremos/agua/pliegues/cierre y las guardas de terreno; no está integrado. Original `river-kit7-a-on-f-20261026/author-report.json` SHA256 `5bca325f35bfc1ddabfdc9368eb06ad5898ea8a2d3e4867f174e1e6aab5d152f`, terreno815ef8b7…;139modelos y127.528prismas triangulares. C/F desplegado y la generación C en curso permanecen inmutables.

## Descubrimiento y propuesta

La relectura de los27MLOD C ligados al checkpoint público da1.449componentes,45.470caras,25.633vértices, máximo72vértices/140caras por componente. Es una referencia operativa con contacto nativo muestreado, **no** una equivalencia de rendimiento. La relectura de kit-7 fijará los cinco costes por modelo antes de autoría.

[EXACT] `midpoint_stream_collision_v31.partition_midpoint` ya acepta límites explícitos de complejidad, tiempo y estados; `compact_stream_collision_v31.fit_grid` prueba la desviación local de la cubierta. [DESIGN] Reutilizar ambas funciones sin editarlas para una única partición nueva de cada modelo kit-7, caps72/140 fijados antes de medir el resultado. Mantener presupuestos0,03m vertical local y0,01m lateral, centrar la colisión por el error de cubierta cuantizado a1/512m y exigir al consumidor global±0,02m. Guardar solo Geometry nuevo, los otros tresLOD como bytes originales. Copiar terreno/envelope/cover/superficies exactos a carpeta nueva `river-kit7-midpoint-a-20261026`; orígenes y transformaciones lógicas originales exactos.

El máximo individual aumenta respecto a los prismas originales de6vértices/8caras: se informa expresamente y se limita por la referencia C. La puerta exige componentes, caras y vértices **totales y por modelo** no crecientes frente a kit-7 original, reducción estricta de componentes globales y cumplimiento72/140 por componente. No declarar mejora en las cinco dimensiones ni FPS por ese recuento.

Kit-7 nunca se colocó en un WRP: no se hereda la pose compilada de un modelo131. Cambiar Geometry puede mover el centro ODOL. Antes de integrar habrá que calcular las poses desde el centro realmente compilado y probar en coordenadas globales que el LOD visible/agua/roadway continúa en su posición original. No aplicar por copia los diezvértices del arreglo131 ni alterar el WRP C en ejecución.

## Presupuesto, aceptación y parada

Un autor, una búsqueda por modelo,20.000estados y60s por modelo; timeout externo1.800s, prioridad baja y un hilo numérico. Cualquier límite produceINCONCLUSO, sin aceptar resultados parciales. No variar caps/tolerancias para conseguirPASS. Revisión Fable de plan y adaptación del autor antes de ejecutarlo.

Si termina: consumidor independiente `review_compact_collision_v31.py`, sobre todos139modelos y juntas, máximo1.800s; cierre, convexidad, selección completa, LODbyteexactos, orígenes y overlay planar global±0,02m/0,01m. Fuente y hashes del lector fijados. Los controles negativos vigentes de cobertura/altura/estado se conservan; no se cambia el verificador. Un fallo se localiza con su contraejemplo antes de otra propuesta; no regeneración automática.

PASS offline solo significa coste explícito y contacto matemático en MLOD. Quedan compilación/centros/poses, huella/bury del agua nueva, bosque y física nativa completa incluyendo juntas, después navegación correspondiente y vista. El candidato permanece separado hasta pasar todas las puertas. Ningún PASS heredado de río131 ni de la navegaciónC en curso.
