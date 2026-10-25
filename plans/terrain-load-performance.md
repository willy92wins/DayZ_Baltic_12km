# Carga y rendimiento de la base de terreno

Petición viva30-09: avanzar terreno/navmesh y probar carga, priorizando rendimiento.
Extiende P7/P10; no altera recorte, arte SAT1M aceptado, física ni cotas regionales.

1. Cerrar exportación nativa del editable V3. Exigir lectura completa, alturas del
   delta congelado y tres poses; conservar cada export fallido.
2. Generar navegación completa sobre el WRP realmente desplegado y guardar su
   hash junto al NM. Empaquetar con identidad de todas las entradas restantes.
3. Probar arranque y consultas de caminos en esa pareja WRP/NM. Arranque por
   DayZ MCP; adoptar/release/stop por el protocolo registrado.
4. Medir una base reproducible: misión aislada, sin CE/población/clientes;
   30s de calentamiento y120s de muestras servidor. Registrar FPS nativos,
   número y duración de OnUpdate, tiempos de misión y memoria/CPU del proceso.
   Registrar hardware, versiones, paquete y contexto de otras aplicaciones.
5. Solo optimizar ante un coste medido y atribuible; comparación A/B con mismos
   datos y escenario. No degradar resolución SAT1M ni malla para ocultar cortes.
   La carga de IA y cliente son escenarios separados; NPC no equivale a jugador.

PASS de medición: mundo correcto, inicio/final nuevos,120 muestras después del
calentamiento, contadores y tiempos monotónicos, proceso vivo y ninguna excepción
de la sonda. FPS bajos son resultado, no motivo para descartar una medida válida.
FAIL de funcionamiento: export truncado, geometría cambiada sin autorización,
paquete distinto o errores de carga/compilación. INCONCLUSO: interrupción, huecos,
sesión ajena, navmesh sin guardar o falta de observación del consumidor.

Esta base solo mide coste fijo del mapa sin poblar.80–100 jugadores, red, loot,
persistencia y densidad futura siguen requiriendo sus pruebas específicas.

Fuentes locales verificadas30-09: scripts/3_game/global/game.c:878,885,892,902,
913 (FPS y reloj); scripts/5_mission/mission/missionserver.c:102 (OnUpdate).
Datos servidor únicamente; no RPC/SyncVar, archivos en el perfil temporal.

## Contrato congelado de la navegación nativa

La misión BalticNativeNav se preparó antes de cargar la nueva navegación:
cruce oeste/este y regreso desde60m a cada lado del centro; controles locales
50–60m y filtro negativo sin polígonos.121 muestras por sentido, aceptación
geométrica0.8m conservada; tablero físico9m y tres tramos/75m, conforme al
ledger V3. No heredar el gate del puente antiguo de2m.

Además se muestrean los751 puntos secos del reference-v1 regional anterior.
No se eligen según su resultado de navmesh. Se informa cada fallo al buscar
suelo caminable a2m y la región; una ausencia requiere discriminar pendiente,
filtro/isla, agua y datos, y no demuestra por sí sola un defecto del terreno.
Esto no valida locomoción de IA ni conectividad entre los751 puntos.

Durante el ensayo headless se observaron FPS nativos constantes14.2857 frente
a miles de llamadas OnUpdate por segundo. Conservar ambos sin equipararlos:
la semántica efectiva de esos FPS en servidor no está validada. CPU/memoria
vienen del proceso identificado por PID y fecha de creación, con reloj host.
