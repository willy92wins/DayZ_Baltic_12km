# Material de mar: prueba explícita y acotada

Después del A/B/A/B de visibilidad, el arco depende de la distancia, pero quedan
franjas en agua lejana. OutsideTerrain con/sin síntesis no lo corrigió. No se ha
aislado todavía si esos píxeles los produce agua, relieve o su transición lejana.

Prueba siguiente: usar los tres campos de material de océano documentados por el
ejemplo oficial DayZ Test_Terrain/world/config.cpp:114–116, asignando explícitamente
los materiales instalados Graphics/materials/water/oceanold(.emat,_nice,_storm).
Las rutas y sus contenidos se han leído en P:/graphics/materials/water. No cambiar
WRP, navegación, texturas terrestres, distancia de cámara ni clima del fixture.
Es un discriminador del render del mar; no afirmar que corrige el defecto antes
del ensayo. El DeepMap vanilla pertenece a otro encuadre15384m; esta variante es
temporal y no se entrega como agua propia del mapa sin revisar esa dependencia.

Materiales leídos frente a otros supuestos: se verificaron rutas, tipoMatOceanOld,
DeepMapCoord y referencias de textura; no se conoce todavía el material efectivo
del fallback del motor. PBO solo config.bin diferente; cuatro fases SPB iguales.
PASS acotado si desaparecen franjas/arco con el override y vuelve el defecto al
retirarlo. FAIL si no cambia o degrada; retirarlo por hash. No variar coeficienteZ.
