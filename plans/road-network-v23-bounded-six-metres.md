# V23: comprobar la matriz local corregida con cota6m

V22 terminó sin ASC. El ajuste avanzó nueve soluciones parciales, pero otro
certificado exige>=5.030710m en(4992,6396). Sus116filas físicas significativas
(85carretera,27talud,4cuerda) abarcan x[4986,5202],z[6342,6420], distinto de la
ladera cuya transición se amplió. No atribuir el nuevo conflicto al borde viejo.
La última solución parcial tenía mediana de cambio0.141m,p90=1.452m,p99=2.813m;
no era aceptable, conserva1790filas incumplidas y nunca se exportó.

[DESIGN] Una comprobación con cota6m, ya contemplada antes en V21 pero ahora
sobre la matrizV22 con transición local corregida. Se reutilizan las403368filas
activas, además de todas las infracciones originales. Sin ampliar otra franja
ni cambiar suavidad, suelo seco, islas, reserva o agua. Cada solución parcial
vuelve a comprobarse contra las6535300filas de la matriz congelada completa.

600s solver/650s worker,un hilo,guardia2GiB. No siguiente incremento automático.
Si es inviable, reconstruir su conflicto físico antes de elegir más cambios.
Si produce ASC: lector independiente denso con cota6m y envolventeV22 explícitas,
hidrografía/reserva y negativos. Revisar distribución/visual de los movimientos,
importar solo tras esos gates y regenerar navmesh para el terreno final.
