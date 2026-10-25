# Narva: cruce humano registrado en servidor

Repetición sobre baseline regional ebc60f4f y nueva navegación0fc26281:
run36fa7ea9-11e1-4dc6-bc1f-7d4eaf7e2150, `regional-verification.json` PASS.
354 muestras servidor,68 por sentido sobre el puente, pies1.99993..2.025m,
salud100, sin nado/teletransporte y error lateral máximo0.081992m. El motor
ejecutó el mismo fixture; no extrapolar el resultado anterior tras cambiar
geometría. Cierre normal, sonda retirada por hash y caja libre antes del ensayo
de IA independiente. Los párrafos siguientes describen el primer baseline.

PASS acotado al recorrido oeste→este→oeste en el eje del puente. Run
39139a4a-8d2d-49f2-b6cf-78121d4af3e0, terreno5030cb74, sonda f0573d42.
359 muestras del servidor hasta el regreso;68 por cada sentido sobre el vano.
Error lateral máximo0.081894m; mayor paso entre muestras0.415933m; pies sobre
el tablero1.99993..2.025m; salud mínima100; ningún comando de nado.
El cliente marca COMPLETE_BOTH_DIRECTIONS a90.6063s. No se usa SetPosition
durante el recorrido. Ver v3-verification.json y los dos CSV por hash.

El control se aplica en cliente y servidor. Solo en cliente producía predicción
local oscilante mientras el servidor no avanzaba: v2-* conserva ese negativo.
GetHealth cliente era0 con salud servidor100; no sirve como guard inicial.
La prueba verifica locomoción humana scriptada, no transporte de teclado real,
vehículos, IA/pathfinding, loot o capacidad80–100. El verificador rechaza caídas,
muerte, nado, teletransporte y ausencia de final/avance servidor;7 controles.

Primera compilación de misión falló por concatenación float+string sin cadena
inicial. Corregida, sin tocar mapa. No fue un crash del mapa. Último cierre MCP
normal cliente/servidor, exit_metrics_valid=true. Avisó de jugador no guardado;
la misión de ensayo no usa estado productivo. Sonda retirada por SHA; caja y
lease libres. Las misiones/scripts de ensayo permanecen para reproducirlo.
