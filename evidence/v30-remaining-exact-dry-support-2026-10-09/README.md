# EV71 — cierre de los bajos secos editables

Estado: fuente y modelos compilados PASS; sin ejecución nueva en DayZ.

Se completan los 164 objetivos editables que quedaban después de EV70. Esta pasada cambia 5.202 vértices; la composición EV70+71 cambia 27,996 respecto de EV61, con elevación acumulada máxima de 0.4000001 m. P/F, carreteras, plataformas y todos los apoyos de triángulos realmente mojados se conservan. Las 18.033 instancias del WRP permanecen exactas.

La lista EV59 queda contada completamente: 2.615 de 2.760 puntos alcanzan 1,80 m (tolerancia 1e-6); los 145 restantes están protegidos, 59 en bancos de grandes lagos y 91 en el borde, con 5 comunes. Ningún objetivo editable de esa lista queda pendiente. No equivale a eliminar todo defecto gráfico del mapa.

El consumidor independiente de normales mide reducción del 15,98 % de energía angular en las 22.689 aristas incidentes, y los pliegues >30 grados bajan de 89 a 50. En los bancos naturales completos, p99 pasa de 16,70260 a 16,69000 grados. Cuatro sectores empeoran localmente; `sectors.json` conserva su detalle. No hay aceptación artística.

La exposición de los 500 objetos compilados afectados se conserva exactamente: 11.197 caras físicas y 30.141 visibles sin área nueva u oculta. La cobertura completa de 404.484 celdas pasa, sin hueco físico; residuo visible 3,8464e-12 m². El control negativo de hueco de un centímetro falla como debe.

El índice global recorre 8.380.418 triángulos: 408 zonas >=1 m² y 726892.25 m² en la banda de riesgo. Su consumidor independiente pasa 91.937 caras analíticas, 320 comparaciones GEOS y 423 puntos secos. Es un índice geométrico, no 408 defectos de render confirmados.

`terrain-delta.npz` reconstruye byte a byte el candidato desde EV70; `layer-replay.json` verifica también los 145 protegidos. Terreno `b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36`. El paquete final con las texturas nuevas es EV72; no usar las texturas provisionales de ExactDrySupportV2 para aceptación gráfica.
