# EV112 — verificar el mundo integrado de kit7 en el motor

Continuación de la integración autorizada. La fuente ya está contrastada contra F:2.578.398objetos,139piezas nuevas,62anteriores exactas,292árboles retirados y1623ajustesY. El registro del piloto corrige35clases antiguas ausentes y añade139nuevas:201clases para201ODOL. El paquete piloto aceptado es `46244e7f2abc6bd2d07be828097325ec9bba9c672b48bfcef177895b87380b2d`. El mundo debe leerse de `package-kit7-fc-world-20261026/verification.json` solo después de terminar su compilación y readback; no inferir éxito por existencia de un PBO.

## Lo preparado y lo pendiente

El helper existente `tools/water/prepare_visual_probe_v31.py` ha producido `R/probe-kit7-prepared-20261026`:2050puntos,2extremos originales,413centros,826controles laterales,414consultas alrededor de138juntas,364puntos de relieve,25frente aNarva,3referencias de mar y3apoyos. Sin diagnósticos de lecho sobre agua. La misión es una copia exacta del productor existente, sin nuevos métodos del motor. **Preparado no equivale a listo para lanzar:** el manifiesto todavía apunta al PBO aislado del kit7; debe vincularse al mundo/piloto combinado real y al run nuevo antes de obtener resultados.

[DESIGN] Congelar los paquetes finales y conservar los4749controlesC/F como regresión, recalculando únicamente la expectativa de terreno donde cambió H. Revisar aparte los puntos que caigan sobre geometría nueva: no conservar una expectativa de vacío si ahora hay un lecho. Añadir los3430vértices modificados y muestras de sus caras nativas adyacentes para validar las alturas compiladas; presupuestar según los100ms de espera por consulta de esta misión, o separar una sonda de altura sin raycast. No afirmar readback completo de alturas a partir del lector OPRW de objetos.

[DESIGN] Verificar la cobertura de todas las139piezas y sus138juntas contra los intervalos del author-report, ambos extremos y los dos extremos globales del certificado de contacto. Los controles secos se contrastan contra toda el agua del mundo, incluyendo confluencias, conforme a la decisión previa de Guillermo. No cambiar tolerancias ni reclasificar por el resultado del motor.

## Ejecución y aceptación

1. Leer el runbook MCP y pedir lease solo cuando el candidato y las sondas estén verificados. Si el banco está ocupado, no cerrar ni adoptar sesiones ajenas. No abrir cliente sin la revisión conjunta. Copiar a un mod/mission propios nuevos, verificar SHA del desplegado y usar ciclo oficial de DayZ MCP.
2. Calibrar en un run propio con el control vanilla y el espacio vacío; ejecutar las sondas nuevas y las regresiones. Exigir identidad completa, log nuevo, BEGIN/END y cobertura exacta. Consumidor existente `eval_visual_probe_v31.py`; pasar sus positivos/negativos relevantes si cambia el adaptador.
3. Repreparar los3727objetos de borde contra el WRP nuevo y repetir la sonda de soporte/agua. El PASS deF en269968puntos no se hereda. Los controles interiores y de densidad/contexto ya pasan en fuente; el borde sigue INCONCLUSIVE.
4. Solo con el paquete físico aceptado, generar navegación propia. La NM6 conservada por el paquete técnico y la NM9 deC/F no aceptan este mundo. Incluir rutas que recorran el kit7, ambos extremos y las regresiones existentes; después locomoción/vista con Guillermo.
5. Cerrar solo runs propios mediante MCP, liberar lease y comprobar session_status. Guardar rechazos y recetas/inputs; commit/push desde el checkout público saneado de las unidades verificadas.

Los GatesG2/G3 de densidad/composición comparan el conjunto con bandas Livonia:PASS agregado admite ventanas fuera de banda según la regla calibrada; no significa cero ventanas imperfectas. Los47humedalesG7 y475ventanas forestalesG8 no presentan fallos. Nada de ello prueba FPS, capacidad para80–100jugadores, conducción ni aceptación visual de las orillas.
