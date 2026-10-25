# EV84 - reperfilado local sin invertir el orden de alturas

Estado final de esta propuesta aislada: NO AUTORÍA. `order-bounds.json` demuestra antes de optimizar que el segundo foco puede bajar como máximo 0,0350475 m conservando el orden de sus vecinos fijos; no alcanza el criterio de 0,1 m. El primer foco admite como máximo 0,2003584 m. No se creó terreno ni se relajó el criterio. Se estudia por separado un movimiento conjunto de los vecinos secos sin protección, manteniendo la restricción de forma.

Diseño revisado por root sobre el contraejemplo EV83 y los perfiles completos; ejecución dentro del encargo vivo de suavizar orillas y taludes. No hay cambio de niveles, protecciones ni alcance de lagos. Fuente desplegada sigue siendo EV82-B, no el piloto EV83.

## Por qué cambia el diseño

EV83 baja los dos focos y su energía angular, pero la segunda altura queda por debajo de ambos vecinos este-oeste. El pico se convierte en una V nueva. El primer foco también desplaza un máximo al vecino sur. Los perfiles completos de 36 m a escala 1:1 lo muestran; los gráficos de una sola arista no podían detectarlo. EV83 no se promueve, aunque pase sus antiguos gates geométricos/cobertura.

## Contrato [DESIGN]

Se conservan íntegramente el alcance, identidades, gates angulares, cruce <=1 m, topología, presupuesto total EV79 <=2 m, no-raise, suelos y cobertura ODOL del plan EV83. Los únicos puntos mutables siguen siendo (1146,1002) y (2196,1572). Todo otro dato permanece exacto.

Se añade un invariante de forma para las aristas entre cada punto modificado y sus ocho vecinos de rejilla:

- Si en B h_i > h_j, la nueva h_i debe seguir siendo >= h_j.
- Si en B h_i < h_j, la nueva h_i debe seguir siendo <= h_j.
- Si en B h_i == h_j, se conserva la igualdad.

Esto permite aplanar un pico hacia el vecino pero prohíbe invertir pendientes y trasladar/crear extremos al bajar un único nodo. Como los dos puntos están separados y todos sus vecinos fijos, el límite inferior para descenso es el máximo de las alturas vecinas <=h_i; si existe un vecino igual, no puede bajar. Los ocho vecinos incluyen ambos ejes y diagonales; es un criterio conservador de forma, no una afirmación sobre resolución LOD del motor.

La restricción se intersecta con el intervalo factible ANTES de optimizar. La decisión float32 final se verifica con comparaciones directas contra B, sin tolerancia que permita invertir el orden. No se cambia el objetivo ni se corrige una altura a mano después de aceptar.

## Salida

Una propuesta, más una corrección solo si hay error de implementación. Descenso >=0,1 m y energía incidente reducida >=1% en cada punto, ningún gate anterior relajado. El consumidor independiente agrega la comprobación del orden de todos los pares afectados y un control negativo con la V real de EV83; conserva fixtures de cruce/signo/ángulo/hueco.

Perfiles completos de 36 m a escala 1:1 en ambos ejes y comparación B/EV83/EV84. Explicar máximos, mínimos y mesetas resultantes. No basta con la energía ni con dos puntos sobre una arista.

Sin empaquetar, desplegar ni iniciar motor. La extensión al mapa requiere plan de dominio propio y consumer sobre interacciones entre nodos; el criterio local no prueba esa generalización.

Anclajes: EV83 author_pilot.py:45-93 intervalo de cruces; función piloto de intersección 159-175; EV82-B author.py:419-545 solucionador angular y float32. Contraejemplo reproducible: EV83 candidate SHA f0e977d8bc2e11529aedc3851bb1d456b45ffee0e2b974af89db6a26fab087f9; B f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0; perfiles EV83 profiles-full-1to1.png.
