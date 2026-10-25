# Recuperar casos interrumpidos sin variar el experimento

El delta8 aisladoV4 supera física/eventos y12negativos. Delta10 quedó
ABORTED_MISSION_FINISH: el motor terminó12:45:39UTC; expiración del lease registrada
12:45:34 tras últimoheartbeat12:42:48. Coincidencia temporal, no causa raíz aislada.
Narva6 de V3 también quedó incompleto por cierre del motor. Los FAIL se conservan.

[DESIGN] Una nueva misión por caso,10 y6, con una sola embarcación. Misma geometría,
controlador y criterios V3. Sin otro barco en el extremo común. No repetir8 que
ya terminó. Heartbeat acotado a cada run para cubrir cálculos y recuperación de
contexto; parar la renovación al cerrar ese run. No cambiar infraestructura MCP.

Presupuesto: una ejecución válida por caso,4200s límite de misión. Una interrupción
sin conjunto completo no es aceptación. Guardar logs cerrados, identidad desplegada,
física/eventos, negativos, RPT exacto y cierre lifecycle antes de otra misión.
PASS se refiere solo al caso completado; no convertir dos runs en prueba simultánea.
Sin Computer Use.
