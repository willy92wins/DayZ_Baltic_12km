# Discriminador de configuración del mundo

La prueba explícita oceanold conserva arco blanco a1600 y franjas en Ládoga a6000.
OutsideTerrain y enableTerrainSynth=0 tampoco lo corrigieron. No seguir variando
parámetros de esos componentes sin evidencia nueva.

Prueba temporal: BalticTrial hereda ChernarusPlus en vez de CAWorld, declarando
DZ_Worlds_Chernarusplus_World como dependencia. Fuente instalada verificada:
P:/DZ/worlds/chernarusplus/world/config.cpp:3,36. Mantener todas las propiedades
explícitas del mapa, WRP, materiales y navegación byte a byte. Cambiar solo
config.bin. No entregar esta variante: hereda nombres, economía y ambiente ajenos.
Si corrige el síntoma, bisecar los componentes del config; no atribuir causa a una
propiedad concreta por este ensayo agregado. Registrar clima/cámara y limitación
de que valores heredados de agua/ambiente aún no están aislados.

Gate: dos vistas estables1600/6000 con la sonda congelada; FAIL si persiste el arco
o las franjas. INCONCLUSO si no carga o cambia pose/clima. Presupuesto: una prueba
de herencia; solo si mejora, hasta dos bisecciones de componentes. En todo caso,
cerrar run, restaurar baseline por hash y retirar sonda al abandonar experimento.
