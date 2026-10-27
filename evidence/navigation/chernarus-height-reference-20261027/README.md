# Referencia nativa de altura: arroyos de Chernarus

**REFERENCE_HEIGHT_EXCEEDANCES**. 48/48 rutas comparables; 17 puntos superan0,801 m; máximo 5.595824 m.

Un único run de servidor, 24 piezas elegidas antes de conocer resultados,
48 rutas y control NONE. Selección sin sustituciones. Capturas completas y
rutas no comparables conservadas. Tolerancias 0,801 / 0,011 / 2,1 m intactas.
Ejecutable, 118 paquetes stock, bridge, misión y anclas fijados por hash.
Cierre oficial observado y lease liberado. No cliente ni actores añadidos.

Es un diagnóstico del mismo observable, no una aceptación de Baltic. Los
extremos usan SurfaceRoadY actual+.2, distinto del max(roof,ground)+.2 offline
de Baltic. Los datos no prueban comportamiento de actores ni una causa única.
Una desviación vanilla no borra fallos de Baltic ni autoriza bajar tolerancias.

Nav8 conserva607 PASS de altura con máximo0,711963 m, pero falla RAM con ratios
1,265913/1,241333. Nav12 conserva tres alturas FAIL y no tiene medida RAM.
El original12,5 pasa RAM0,832329/0,844646 y conserva los cuatro fallos de altura.
No hay todavía una variante que reúna aceptación funcional y de memoria.

Revisión independiente Fable5.1 conciliada; 18 controles del lector,
13 escenarios de coordinación con dos mutantes y ocho de comandos pasan.
El validador estático revisó una misión sin errores ni avisos. El log nativo
y el resultado indican por separado la cobertura real de esta ejecución.
