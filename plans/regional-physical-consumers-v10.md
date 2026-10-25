# Consumidores físicos regionales V10

Continuación de la sesión nocturna: P3/P5/P9/P11. No modifica el mundo.
La NM nueva supera consultas y rutas; todavía faltan actores y conducción.

## Narva

V1/V2 se conservan: su eje atraviesa geometría proyectada de pilas. El nuevo
ensayo V3 usa un recorrido continuo desde las estaciones35 a300 del mismo
sector, evitando pilas dentro del cauce profundo. Se congela antes del motor;
no reclasifica los fallos anteriores. Diseño offline: eje124.18m, separación
mínima5.81m de la geometría proyectada,8466 muestras de profundidad en discos
de6m, mínimo3.08165m. No cambia terreno/objetos/física ni los criterios de
movimiento, daño, continuidad y precisión. Dos viajes con spawns independientes.
No prueba tripulación, viraje completo ni barcos medianos reales.

## Infectados

Extender el mecanismo de OutlineChaseV4 que ya produjo locomoción real:
un humano de prueba inmóvil, veinte segundos de asentamiento, un infectado
independiente por caso, ruido diagnóstico4x y seguimiento continuo. Una prueba
local25m y ambos sentidos de seis recorridos regionales existentes, más tres
segmentos solapados del puente/accesos. Total19 casos; timeout90s por actor,
pausa6s entre casos; los fallos de un caso no impiden registrar los siguientes.

PASS por caso: spawn en coordenada congelada; objetivo estable<=2m; salud
positiva; meta3D<=4m; recorrido<=3 veces distancia directa; continuidad<=1s;
estados mentales0..4 tras1s y alguna respuesta1..4; contacto sobre geometría
-0.2..+0.5m. Muestrear también SurfaceY y compararlo contra ASC con2mm, usando
vectores con seis decimales. En puente, contacto esperado con tablero11m dentro
de su huella; registrar desviación lateral y exigir corredor4m allí.

FAIL: incumplimiento medido. INCONCLUSO: falta de cliente/actor/nav-anchor,
log incompleto o fallo de arranque. Conservar terminales e identidades de caso.
Validar el verificador con registros reales y negativos de llegada falsa,
flotación, objetivo movido, hueco temporal, salud, esquema y truncación.
No atribuir un timeout a navmesh sin aislar percepción/obstáculos/movimiento.

## Autoridad y APIs leídas

Estado de infectado y objetivo: servidor; réplica del humano: motor vanilla.
Cliente: override temporal de velocidad0 para estabilizar exclusivamente el
humano local, con liberación al finalizar y límite3600s. Sin RPC ni persistencia.
El infectado no recibe overrides, SetPosition ni velocidad después de crearlo.

Fuentes locales verificadas: P:/scripts/3_game/ai/aiworld.c:65,108,141;
entities/dayzinfectedinputcontroller.c:9; noise.c:7; human.c:234;
global/game.c:702,1163. Harness operativo:
missions/BalticOutlineChaseV4.BalticTrial/init.c y
evidence/regional-outline-v3/runtime-chase-tile12p5-v4.json.

La carga de jugadores, percepción normal y navegación de toda la región no
quedan acreditadas por estos casos. El paquete continúa diagnóstico hasta
cerrar la comparación real tras reapertura del editor.
