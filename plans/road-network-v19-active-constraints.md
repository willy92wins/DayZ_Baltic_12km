# V19: resolver las mismas restricciones con menos memoria

La geometría congelada V18 tiene 6.523.172 restricciones y 147.393 variables.
Con 3 m de movimiento vertical hay certificado de inviabilidad; dos puntos
secos necesitan al menos 3,877807 m. El ensayo diagnóstico a 4 m devolvió
Infeasible en 59,938 s y terminó a los 121,375 s sin conseguir el certificado.
Se conserva ese resultado; falta localizar la nueva contradicción.

[DESIGN] Producir un candidato a 4 m de cota máxima (revisión explícita de los
3 m anteriores, justificada por el certificado). Misma transición de 24 m,
misma banda de 8 m y todos los límites de suavidad/protección congelados V18.
No aumenta montañas ni modifica cauces. La necesidad real se medirá en el
resultado, por localización y cuantiles, antes de aceptar/importar.

Resolver L1 con generación de restricciones: comenzar por todas las filas
que incumple V10, resolver y evaluar el resultado frente a TODA la matriz
original. Añadir todas las filas violadas y repetir. Nunca descartar filas
activas. Parar con inviabilidad certificada, error, tiempo, falta de memoria
o de progreso; escribir candidato solo si los límites y todas las filas
originales verifican el primal. El resultado no sustituye al consumidor
independiente que lee las alturas reales.

Presupuesto: 600 s de cálculo, 650 s de proceso, un hilo; no operaciones de UI.
RAM disponible >= 2 GiB al empezar cada solve. Datos y matriz por SHA256.
Sin ampliar cota o soporte automáticamente. Si el solve parcial no termina,
solo aceptar su primal si verifica toda la matriz y los límites originales.

Después: consumidor denso independiente (0,37 m longitudinal/0,25 m lateral),
agua y 283 polígonos protegidos, reserva seca, negativos pertinentes. Solo si
pasa: lote de Terrain Builder, persistencia real y nueva navmesh del WRP final.
