# Render y agua — 29-09-2026

Estado, experimento y límites: [informe](<C:/Users/guill/Documents/Codex/2026-09-29/vamos/outputs/baltic-render-agua/README.md>).

Estado vigente: `auto-observer/runtime-checkpoint.json`, agua posterior medida y seca en las297 muestras interiores. Sonda automática retirada, F10 no requerido. Navegación propia cargada después; ver `../navmesh/checkpoint.json`. Los párrafos siguientes son históricos.

Materiales: A/B/A/B real PASS. Agua basal: 44/297 puntos secos inundados. Corrección local importada: 4194304 alturas PASS; puente conservado; PBO420 entradas verificado, sin desplegar. En el núcleo seco interior, 28278 vértices <=1m pasan a cero; esto no sustituye la nueva sonda del motor.

Pruebas posteriores en `water-import/`. Recuperación en `recovery/`: Buldozer ya cerrado; Terrain Builder sigue sin responder, cierre manual solicitado. Los logs finalizaron al cerrar Buldozer y llegan a Game, sin World/Mission. El aviso de Sakhal también aparece en la sesión correcta; causa interna del bloqueo no aislada. Sondas temporales retiradas; reinstalar antes del siguiente F10. Navmesh y autorización NavMeshGenerator pendientes. El verificador de agua ahora devuelve exit1 para FAIL; registro auténtico negativo y tres controles sintéticos verifican el contrato de salida sin acreditar el terreno corregido en el motor.

Actualización posterior: editor recuperado y proyecto reabierto, `reopened/reopening.json`. Exportación y visor en pausa por entrada simultánea; usuario preguntado, sin respuesta todavía. Sondas temporales retiradas por hash. `reopened/shore-subcell-analysis.json` mide el efecto geométrico de la interpolación en la costa: hasta5,58 m de retroceso muestreado a mar0,5 m, ninguno a más de12 m del borde; no prueba conectividad ni agua real. Terreno sin nuevos cambios.
