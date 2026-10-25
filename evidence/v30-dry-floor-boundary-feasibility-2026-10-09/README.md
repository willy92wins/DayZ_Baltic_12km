# EV69 — límites locales al elevar bajos secos

Diagnóstico sin modificar terreno. De53 aristas de EV60,34 tienen un único vértice editable y19 más de uno. En nueve objetivos, elevar el único vértice al intervalo autorizado [1,8m,fuente+0,4m] obliga a superar el límite local max(ángulo original,p99 original). El exceso mínimo llega a1,45636grados. Todos los vecinos fijos que impiden esa corrección local son apoyos acuáticos; no es un error de precisión como EV66.

Las coordenadas y protecciones exactas están en `boundary-feasibility.json`. El diagnóstico compara normales con el consumidor independiente (error máximo7,11e-15grados), evalúa extremos, mínimo escalar, una rejilla de2049 alturas y valores float32 vecinos. No demuestra que el percentil global sea imposible: examina una condición suficiente por arista, más fuerte que ese percentil.

Consecuencia: conservar la selección segura EV61. Estos nueve puntos requieren autoría coordinada del talud y sus apoyos para cumplir este límite local, o una decisión explícita sobre su criterio; subir el vértice seco aislado no lo cumple. No se relaja el gate, no se elimina ningún objetivo de los2197 pendientes y no se genera otro terreno. El resto no queda validado por esta clasificación. Msta/Volkhov, niveles reservados, cruces y pruebas en motor continúan abiertos.

Discriminador posterior `exact-support-discriminator.json`:18 de27 vecinos estaban fijos por pertenecer a la caja de una celda de agua, aunque son secos en todos sus triángulos. Los otros9 sí soportan una cara mojada. La rigidez local era consecuencia de ese cierre rectangular, no prueba de que hubiera que mover agua real. EV70 prueba el cierre exacto de caras mojadas y conserva las demás protecciones; es una propuesta separada con su propio consumidor.
