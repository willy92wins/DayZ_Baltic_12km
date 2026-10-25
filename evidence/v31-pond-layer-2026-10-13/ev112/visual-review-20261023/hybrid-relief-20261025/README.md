# EV112 — continuación híbrida E

**Compilado y comprobado: 4.401 puntos de servidor PASS, cero fallos; 159 tests PASS.**

E conserva exactamente D y añade cinco grupos corregidos: un pico y cuatro
depresiones, con 99 vértices nuevos. Desde la base T: 71 grupos y 1.446 vértices,
radio de 24 m y delta máximo de 0,75 m. Quedan 268 picos, 1.144 depresiones y
cinco transiciones rectangulares señaladas por el censo; el mapa sigue abierto.
El experimento aislado de seis grupos no es E: el grupo del clúster 39 queda
pendiente porque su contexto contiene alturas de D. Diez grupos objetivo,
incluido ese, no están aceptados. Los fallos de SLSQP no prueban imposibilidad.

Huella de agua exacta y bury sin cambios; 135 extremos protegidos afectados,
sin excesos nuevos. P11: 77.559 secciones y 130.534 intervalos, cero fallos.
Fuente y compilado: 2.578.725 objetos y 62 poses del piloto contrastados;
1.632 ajustes Y de bosque verificados con consumidor independiente, resto exacto.
Bosque: 2.560.872 instancias, cero fallos medidos; 3.727 discos de borde INCONCLUSOS.

Fable 5.1: SOUND-with-fixes. Sus tres ajustes están aplicados; el autor corregido
reproduce terreno y dominios byte a byte. Cada ejecución conserva su fuente/hash.
El fixture real de regresión contrasta los dos modos con consumidores de formas
y aristas. Dos tests de integración adicionales conservan una solución real y
rechazan máscaras incoherentes aun con hashes de archivo coincidentes. No cubren
toda combinación de clústeres; el negativo numérico sigue dependiendo de SciPy.

Mundo desplegado: `3a285df12e565373d678997aedb9b51f65f11cdbb0f24939da3b8ce77712231a`.
Piloto U2 y agua permanecen exactos. La sonda contiene los controles anteriores,
todos los vértices cambiados y los triángulos de los objetivos aceptados.
El servidor continúa reservado solo para generar la navegación; no se declara
cerrado en este checkpoint. La vista personal está preparada y no se ha lanzado.

Vista humana, contacto cliente, carreteras físicas, navegación, comparación de
rendimiento con Chernarus y aceptación global siguen pendientes. Las secciones
[D → E](candidate-e/sections-d-e.png) son gráficos numéricos, no imágenes del juego.
