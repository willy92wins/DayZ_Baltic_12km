# Ensayo acotado de carga IA sobre el terreno nativo

Extensión de P7/P10 y `terrain-load-performance.md`, por la petición viva de probar
carga. No altera mapa, parámetros físicos ni densidad final de población.

Escenario congelado antes de ejecutarlo: mismo PBO fd2c7023, un cliente real,
cuatro fases 0/25/100/0 infectados vanilla.25s de asentamiento y60 ventanas de1s
por fase. Prey fijo(2120,6920), invulnerable; cuadrícula10×10 desde(2050,6900),
paso4.5m. Terreno nativo muestreado:1.4567–1.8267m, seco respecto al máximo1m.
Estímulo cada3s con ruido vanilla de rifle. No cambiar posición/velocidad del
infectado después de crearlo, ni cambiar sus parámetros de IA/física.

| Dato | Servidor | Cliente | Mecanismo |
|---|---|---|---|
| Fases, actores, salud, movimiento, estado mental | autoridad y registro | representación vanilla | replicación del motor |
| Prey | posición inicial e invulnerabilidad temporal | un jugador de prueba | replicación vanilla |
| CPU/memoria | proceso identificado | proceso identificado separado | observador host de solo lectura |

PASS de medición:4×60 muestras nuevas, misma misión/mundo, fases ordenadas,
conteo vivo exacto, prey a≤2m, al menos80% de la población con mind>=1 durante
30 muestras de cada fase cargada. Registrar movimiento, salud y huecos de reloj.
Si no se activa la población, declarar INCONCLUSO para carga activa, conservar
sus costes observados. Fin tras4 fases, máximo8min o error de sonda, y limpieza
exclusiva de actores propios. No repetir sin un fallo o pregunta causal nueva.

CPU medido por deltas de tiempo del proceso y reloj host, porcentaje de un núcleo
lógico; memoria residente/privada. OnUpdate y timeslice son contadores de simulación,
no FPS de render ni duración CPU del callback. Vincular fases por reloj de misión
y registros, manteniendo explícita la incertidumbre si no hay reloj común exacto.

No es benchmark multijugador, ni sustituye CE, loot, persistencia, red o carga
gráfica de ciudades. La secuencia0/25/100/0 detecta retención gruesa, no demuestra
una fuga. Diferencias entre fases incluyen población, colisiones e instrumentación.

APIs leídas: `P:/scripts/3_game/global/game.c:702,705,913,947,1510`,
`P:/scripts/3_game/entities/object.c:293,1192`,
`P:/scripts/1_core/proto/enconvert.c:196`; el patrón de ruido, controlador y
spawn ya compiló y ejecutó en BalticNativeChaseV2. No RPC/SyncVar añadido.
