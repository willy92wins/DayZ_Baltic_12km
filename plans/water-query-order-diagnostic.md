# Discriminador de consultas de agua — 01-10-2026

Alcance: diagnóstico autorizado de los 551 FAIL del consumidor V3 sobre el
primer export V9. No cambia terreno, agua, WRP, referencias ni tolerancias.
No acredita reapertura nativa, navegación ni barco. Dos ensayos como máximo
antes de reevaluar el mecanismo; se preservan todos los registros.

Hechos: 122 fallos son primera muestra de lote; 225 son primera muestra de
lago. En 154 muestras bajo Narva, SurfaceIsPond=false pero nivel y profundidad
coinciden. Hipótesis: orden/estado de consultas y clasificación tapada por el
puente; no causa raíz confirmada.

Procedimiento: misión nueva dedicada BalticTrial; todos los puntos fallidos,
controles húmedos y secos congelados. Repite dos pasadas sin cambiar XY ni Y
de consulta. A: dos lecturas de superficie, clasificación, tercera lectura,
SurfaceGetType3D limitado a la Y de consulta, cuarta lectura y profundidad al
terreno. B: añade SurfaceIsPond antes de esas mismas lecturas. Registra cada
resultado sin elegir el favorable. Un punto por tick de 30ms, final explícito.

Criterios: entrada/hash/XY intactos y ambas pasadas completas; evidencia de
dependencia de orden si cambia nivel >0.05m dentro del mismo punto/tick. Un
resultado estable incorrecto mantiene el problema de geometría/consumidor
abierto. Dry controls deben seguir sin agua real. No sustituir el gate V3
por este diagnóstico. Si demuestra defecto de sonda, diseñar su versión
corregida manteniendo los 81.212 puntos y rechazar el mapa viejo como negativo.

Datos: solo servidor (CSV, consultas, logs), sin cliente/RPC/actores. Fuentes
verificadas: P:/scripts/3_game/global/game.c:1162-1187 (consultas, comentario
nearest water or object surface), :1127, :933, :1525 (guard/world/queue);
P:/scripts/1_core/proto/ensystem.c:417,443,481,501 (archivos);
P:/scripts/1_core/proto/enstring.c:59,396 (vector/split). Patrón de misión y
CallLater/Remove comprobado en BalticFoundationConsumerV3 que terminó en motor.

## Resultado y corrección propuesta V4

Ensayo terminado, log SHA9ef60ac3: ambas pasadas627 puntos; dos llamadas
consecutivas de nivel no arreglan el síntoma. Después de clasificar,0 errores
de nivel; la pasada con SurfaceIsPond al principio tiene0 errores desde la
primera lectura.154 puntos bajo el puente conservan SurfaceIsPond=false y
SurfaceGetType3D=fresh_water_ext bajo el tablero.60 controles secos sin agua.
Se demuestra dependencia de orden; no se afirma implementación nativa concreta.

V4 mantiene los CSV originales byte a byte, ASC, profundidad, umbrales, muestras
y rutas. Cambia el orden (clasificar antes de nivel) y registra además tipo/Y
3D/IsLiquid/GetLiquidType. Si un estanque elevado devuelve pond=false, solo
admite clasificación alternativa con líquido del grupo de agua instalado,
superficie 3D a<=0.25m del nivel sin onda y profundidad positiva al terreno.
No basta el nombre ni sea=true. Los controles secos rechazan también líquido3D.
Fuentes: surfaceinfo.c:14-44 y actionfillbottlebase.c:103-126 usan el mismo
SurfaceGetType3D -> SurfaceInfo.GetByName -> GetLiquidType; constants.c:544-560
fija LIQUID_GROUP_WATER=8259072. Validar controles positivos/negativos relevantes;
después mismo mapa y baseline viejo como consumidor negativo. El FAIL V3 queda.

Esto corrige la semántica de observación del gate de agua, no las expectativas
geográficas. No acredita flotación, propulsión ni paso bajo el puente.
