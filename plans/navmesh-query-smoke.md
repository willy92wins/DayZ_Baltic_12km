# Comprobación de rutas de navegación propias

Alcance: misión local separada, cinco consultas servidor, sin crear ni mover IA.
Cuatro positivos: tramo corto en cada orilla y puente oeste→este→oeste. Negativo:
mismo puente con filtro que excluye todos los polígonos. Archivo de resultados
acotado en el perfil del servidor. Se conserva la navegación0fc26281 del WRPd12ae049.

APIs [EXACT] leídas en la instalación: scripts/3_game/ai/aiworld.c:59–68 PGFilter
SetFlags/GetIncludeFlags/GetExcludeFlags; :98 FindPath(from,to,filter,out
TVectorArray); :122 SampleNavmeshPosition(position,radius,filter,out position).
scripts/3_game/global/world.c:119 GetAIWorld. Usar WALK y excluir SWIM/SWIM_SEA/
DISABLED; registrar flags efectivos. Puntos del cruce a pie ya medido, a30m a
cada lado del centro (2417.143,6889.885), eje(0.988364361,-0.152104866).

PASS: ambos extremos muestreados cerca del pedido, rutas completas con ambos
extremos a<=1m de los puntos muestreados, longitud finita razonable, cruces por
el corredor del puente y alturas compatibles con tablero. Negativo sin ruta.
FindPath=true por sí solo no es PASS. FAIL/INCONCLUSO si falta prueba del destino,
compilación, punto o final de registro. Esto no prueba comportamiento de infectados,
puertas, vehículos ni CE; su objetivo es comprobar que la navegación nueva puede
resolver el cruce que exige el lore de Narva, además de cargar.
