# Consumidor físico del navmesh de continuidad

Diagnóstico acotado dentro del plan de continuación V30. No modifica terreno,
agua, navmesh ni tolerancias de los resultados anteriores.

## Trabajo

- Usar el paquete `@DayZ_Baltic_ContinuityV30_Nav` (mundo302b000b, NM43916629).
- Recorrer `hills`, `changed_bank_01`, `02`, `03`, `05` en ambos sentidos y
  `lagoon` como control de ruta cuya consulta de grafo pasó. Son12 casos.
- Conservar XZ de las consultas congeladas. Apoyar las posiciones de spawn y
  objetivo en el ASC40d8/dacc, sin desplazar la IA durante el recorrido.
- Un cliente inmóvil como estímulo, un infectado por caso,20s de asentamiento,
  muestras cada0,2s, ruido cada3s y límite90s por caso. Presupuesto total1800s.
- Heredar los criterios físicos del consumidor regional: llegada, reacción,
  continuidad temporal, objetivo estable, salud y posición sobre suelo nativo.
  El control de laguna permite detectar problemas comunes de estímulo/ejecución.

## Interpretación y parada

Una ejecución completa. Una segunda solo si se identifica y corrige un fallo de
compilación/instrumentación. No repetir por no haber alcanzado el objetivo.
PASS aplica únicamente a las12 rutas físicas; no cierra por sí solo los cinco
FAIL de separación entre grafo y suelo ni certifica navegación de todo el mapa.
Si el control falla, investigar estímulo/ejecución antes de atribuirlo al navmesh.
Si las rutas afectadas fallan y el control pasa, localizar el tramo observado
antes de cambiar parámetros del generador o terreno. Evidencia incompleta es
INCONCLUSO, nunca PASS.

## APIs verificadas localmente

- `P:/scripts/3_Game/ai/aiworld.c:65,122`: filtro y muestreo de navmesh.
- `P:/scripts/3_Game/global/game.c:702,947`: CreateObjectEx y GetPlayers.
- `P:/scripts/3_Game/ce/centraleconomy.c:16,17,37`: flags de spawn de IA viva.
- `P:/scripts/3_Game/noise.c:7,24`: AddNoisePos y LoadFromPath.
- `P:/scripts/3_Game/entities/dayzinfectedinputcontroller.c:9`: estado mental.
- `P:/scripts/3_Game/human.c:234`: inmovilización del jugador de prueba.

Preparación en el repositorio. Copia a mpmissions y lifecycle mediante lease y
gestor de DayZ MCP; no intervenir en la prueba SecretRock de otra sesión.
