# V17: resolver la cota insuficiente identificada

Descubrimiento verificado: el certificado dualV16 contiene14 restricciones y
10 coeficientes de vértice (dos dominantes), alrededor de x1602..1626,z4062..4074.
Su combinación contrastada con la matriz original exige un cambio máximo de al
menos2.455156m; con2.05m queda una contradicción de0.450710. No es una medida de
la cota mínima global. `dual-ray-diagnostic.json/.npz` conserva el certificado.
El minimax global anterior terminó por tiempo sin solución; no borrar ese estado.

[DESIGN] Una varianteV17 con la misma matriz, mismas fuentes, máscaras, pisos,
geometría, pendiente/transversal/cuerda y controles. Cambiar únicamente el límite
de movimiento vertical local a3.0m. Es graduación autorizada para carreteras,
no relajación de suavidad ni edición de cauces. Minimizar L1 de movimientos.

Presupuesto: un solve de600s/un hilo y límite del proceso650s, guardia de RAM.
Si al agotarse el tiempo existe un primal factible, se podrá conservar como
candidato NO ÓPTIMO solo tras comprobar independientemente todas las filas,
cotas y finitud; la optimalidad deL1 no es un requisito jugable. Si no hay
primal válido, no producir terreno. No aumentar otra vez3m dentro de esta variante.

Después: lectura independiente ASC en toda la red seca(0.37m/0.25m), exactamente
las mismas tolerancias; agua/costa/283polígonos y reserva; negativos. No importar
ni generar NM hasta pasar esos gates. Guardar V10 y el pilotoV14 como referencias.
La persistencia nativa, navmesh, conducción y vistas deV17 serán aceptación nueva.

[EXACT] HighsSolution.value_valid y col_value comprobados en la API instalada.
El dato del solver nunca sustituye los consumidores geométricos independientes.
