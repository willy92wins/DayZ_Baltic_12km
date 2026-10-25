# Replay de frontera float32 EV80

**Resultado: REPLAY_EXACT.** Se ejecutó una sola reproducción determinista de `author-executed.py` desde EV79, con instrumentación de los retornos `float32_*`; no se invocó `main()` ni se escribió ningún NPZ.

- Selector: **4329/4329**; aceptados: **2591**; duración: **89.844 s**.
- SHA256 del array de alturas float32 contiguo: replay `80432d3751cea4a339c5b4df960a1aa1ebd6cdc83ca5cbc0e06fa637f6ae0ee1`; EV80 `80432d3751cea4a339c5b4df960a1aa1ebd6cdc83ca5cbc0e06fa637f6ae0ee1`; igualdad byte a byte. Candidato de referencia `0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b`.
- De **1275** rechazos `float32_bank_p99_rejected`, los **1275** pasan todas las comprobaciones directas al tomar la altura float32 propuesta y aplicar un solo `np.nextafter` en dirección a la altura previa. A dos ULP también pasan los 1275.
- Se conservaron sin relajar: seis pendientes de cara, doce bisagras, p99 banco EV79 **5.004892938026179°**, límite por sector, nueva bisagra >30°, suelo, presupuesto ±2 m y beneficio local mínimo `1e-4`. El menor beneficio entre los 1275 valores a un ULP fue **0.00020994215**, aún por encima del mínimo. La violación p99 original se juzga con el umbral estricto `direct > p99 + 2e-8°`.

Tres ejemplos reproducibles por índice (row,col):

| row,col | propuesta float32 rechazada | a 1 ULP hacia altura previa | beneficio local |
|---:|---:|---:|---:|
| 12,1306 | 6.956103801727295 | 6.956103324890137 | 0.26337816 |
| 15,1304 | 6.696689128875732 | 6.696688652038574 | 0.30301901 |
| 30,1393 | 7.779608249664307 | 7.779607772827148 | 0.06687845 |

Conclusión acotada: los 1275 rechazos eran **rescatables por cuantización local** en el estado secuencial de cada visita; el reporte de EV80 no debe tratarlos como falta de libertad geométrica. Esto no prueba que la aplicación simultánea de los 1275 ajustes sobreviva a cambios de vecinos: no se construyó ni evaluó otro terreno. Tampoco se guardó el margen angular exacto original por nodo; el reporte conserva propuesta, coordenada y resultados de 1/2 ULP, pero esa instrumentación se serializó sin el contexto completo del p99 que falló. No se repitió el replay.

Detalle completo: [numeric-boundary-replay.json](numeric-boundary-replay.json).
