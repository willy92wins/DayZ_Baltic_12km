# EV25 — suavizado de taludes sobre caras nativas

Preview `@DayZ_Baltic_HingeSmoothV1`. Modifica 665.041 vértices secos de EV16 y conserva las máscaras corregidas de EV23. Minimiza el salto de gradiente entre caras, con intervalos de pendiente factibles antes de cada cambio. No es otra variante de sigma ni de niveles. Ejecuta una sola construcción de 60 barridos; no alcanza el umbral de convergencia de 0,1 mm, por lo que no se afirma óptimo matemático.

El consumidor independiente pasa: cero caras nuevas sobre el límite, carreteras PASS en 77.387 muestras, toda la ingeniería y las 447.030 alturas que soportan celdas de agua exactas. Los quiebros >30 grados en tierra natural bajan de 8.341 a 1.770; p99 de 12,8814 a 6,6784 grados. En bancos secos, 7.698 a 1.644 y p99 de 24,8442 a 16,7226. En aristas incidentes al dominio editable, la media de ángulo cuadrado baja un 68,88 %. Máximo cambio serializado 2,000000954 m; el exceso submicrométrico corresponde al redondeo float32 del límite de 2 m.

Se inventarían 772 sectores. En 46 aumenta la energía angular al distribuir curvatura hacia partes previamente planas; el máximo posterior en esos sectores es 3,9875 grados. Los registros permanecen en `sectors.json` y `verification.json`; no se recortan para mejorar el promedio. Los bancos de los dos grandes lagos, Narva y las caras del agua están protegidos.

El paquete real solo cambia `baltic_trial.wrp` respecto a EV23: otras 6.826 entradas idénticas. Mundo `9eb9f4006c55e3ed3f73461816bed0272e8ab5fdc2f0ca58e214687ef0b82ee5`, agua `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`, terreno `fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6`. Fuente WRP `a845bee973c2db1c94acf39758358dfcfb5967770e3879263ecf1a1bc4f66fd2`, compilado `cfcbbd0c70b75a8e82824343905b16c4d43431ecca32b4fe9b722ac802c38fab`.

Run `c99d9eb4-cf18-480b-95ad-a7c1a1554280`: lectura de los 4.194.304 vértices, error máximo 0,0000152588 m, cero anomalías secas; 18 faltas de flags de presencia y 339 escalares positivos sin flags inventariados. Pasan seis negativos del consumidor. Esto no es un nuevo temporal de tormenta ni cierre del reflejo sobre tierra.

Vistas de R3 cercana/elevada, primer talud, puente y charcas con texturas cargadas y cuatro frames distintos cada una. R3 muestra taludes continuos; no es A/B de iluminación idéntica ni aceptación de todas las formas. La vista de las charcas conserva formas angulosas y brillos locales: no se ocultan como corregidas. Cliente y servidor cerrados normalmente, sesión sin owner/runs.

No promoción a Terrain Builder ni navmesh nueva. Siguen abiertos el contorno/remates restantes, lagos reservados, efecto gráfico del mar y otros pendientes del HANDOFF. La evidencia EV18 de viajes conserva su ámbito anterior; no se simula una repetición de los viajes en EV25.
