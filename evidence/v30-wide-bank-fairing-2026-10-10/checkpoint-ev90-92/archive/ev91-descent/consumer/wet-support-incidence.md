# Diagnóstico de incidencia de `wet_support` — EV91

**Estado: diagnóstico independiente, no aceptación ni prueba de render.** No se cambió `verify_ev91.py`, ningún gate ni terreno; no hubo full run ni motor. Fuente B: EV82-B `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`. H es el candidato EV91 congelado `865901ab24aa3736da57847f9112d3c73181085213f89b48ef2e3e7a9f6ee702`.

El filtro previo solo midió bisagras cuyos **cuatro** vértices están en `eligible ∩ wet_support`: 65.955 nodos producen 775 bisagras (318 diagonales, 240 verticales, 217 horizontales). Su unión de nodos medidos contiene 1.680 nodos wet-support, el **2,55 %** de esa población; B y H son idénticos dentro de ese subconjunto. Por tanto, ese resultado solo habla de una parte muy pequeña del soporte, y omite casi toda la banda y sus interfaces.

Con incidencia **ANY** —una bisagra se incluye cuando cualquiera de sus cuatro vértices pertenece a `eligible ∩ wet_support`— hay 453.263 bisagras: 144.925 diagonales, 154.612 verticales y 153.726 horizontales. La unión toca los 65.955 nodos de soporte y 254.253 nodos en total. De esos nodos medidos, 82.606 pertenecen a la población bank y 35.455 a interior. Son intersecciones de las bisagras con las poblaciones EV87, no nodos `wet_support` reclasificados: las máscaras bank/interior excluyen `wet_support`; una bisagra ANY puede cruzar entre esas poblaciones.

En ANY agregado, B→H da p99 **36,287959→36,287087°**, máximo **83,047165°** sin cambio, conteos `>30°` **11.041→11.037**, y **0** nuevas bisagras que cruzan de `≤30°+ANG_TOL` a `>30°+ANG_TOL`. En all-four, p99 **37,267179°**, máximo **50,387703°**, `>30°` **25** en B y H, cero nuevas; H coincide con B. Son métricas angulares de la geometría de bisagra existente, no métricas de superficie de agua, exposición ni calidad visual. El agregado ANY mezcla interfaces mojado-soporte con banco e interior; no debe presentarse como medición exclusiva del agua.

La fixture discreta pasa en las tres familias: un único nodo marcado selecciona exactamente las cuatro bisagras que lo contienen y ninguna all-four; marcar los cuatro vértices de una bisagra selecciona exactamente esa bisagra en all-four y ANY. Esto valida el desplazamiento de índices/soporte de 4 vértices usado en el censo. La fixture no valida semántica del motor ni topología de agua.

La lectura reutilizó las definiciones EV87 (`edge_vertex_slices`, `incident_any`, `edge_angles`, `summaries`, `_ev87_eligible`, `_ev87_populations`) y el mismo `ANG_TOL`; no añadió umbrales. Hash del verificador EV87 `964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27`; EV91 `5e726b93642f5db531193a8f1d85afabd139c7b9ac3afca4479df793afd53668`. Hash del script diagnóstico `688bf121b1abb813d14d88eeadefeddaf45552ce3cf021c1d90080c40ef00037` (hex continuo en el JSON); reporte JSON `4c55098419467662409f5ed4a597f25f7183a760276a91f48e0458673acfbe02`.

La salida sigue siendo un diagnóstico de incidencia, no un cierre absoluto: ANY responde mejor a “qué bisagras de cuatro vértices tocan cualquier nodo de soporte” que all-four, pero no demuestra por sí sola qué caras son agua o visibles, ni que el conjunto ANY cubra toda interfaz relevante. Reproducible con GIS Python usando `analyze_wet_support_incidence.py`; datos completos y hashes en `wet-support-incidence.json`.


