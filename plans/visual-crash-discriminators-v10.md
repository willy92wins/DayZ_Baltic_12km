# Aislar el cierre del cliente al cargar la vista de SPB

Repro: `BalticFoundationVisualV3` con mundoV10 `d1008dd6`, cámara
Narva aérea -> SPB a150s. Cliente termina con ACCESS_VIOLATION; servidor sigue.
Evidencia: `foundation-visual-v3/crash-attempt01/`. El GetFPS no enlazado deV2
ya fue eliminado; no reaparece enV3. No atribuir la nueva excepción al terreno
sin separar instrumentación y carga visual.

Consumidor: siguiente run diagnóstico del cliente y revisión visual del mapa.
VERDE: carga estable de las doce poses, telemetría completa y revisión de sus
imágenes; los contadores por sí solos no acreditan render correcto.

Discriminadores cerrados, sin alterar mundo ni tolerancias:

1. V4 repite cámaras, tiempos, clima, perfil y mundo; elimina únicamente
   MakeScreenshot y cambia nombres de registros. Capturas por Computer Use.
   Si cruza150s no demuestra causalidad por una sola repetición; sí aporta
   un control sin esa instrumentación. Mantener el fallo original.
2. Si falla otra vez en el mismo punto, misión mínima con spawn directamente
   en SPB, sin addon de cámara/contadores. Observar durante180s.
3. Si también falla al cargar la región directamente, aislar datos de render
   (agua frente a terreno) en un paquete diagnóstico separado; planificar
   el cambio tras leer el formato/herramienta real. No tocar el paquete estable.

Presupuesto de esta ronda: dos ejecuciones del cliente más la decisión de
diagnóstico basada en los resultados; no repetir variaciones de parámetros
sin nueva evidencia. Antes09:00UTC iniciar la cobertura física fluvial larga.
Un cierre limitado/inconcluso de render no invalida ni asciende las pruebas
independientes de agua, navegación o conducción ya conservadas.

## Resultado y siguiente lote de observación — 07:50UTC

V4 volvió a terminar con ACCESS_VIOLATION al entrar en POSE3 a150.001s.
La captura nativa no es condición necesaria. El control SPB mínimo cargó
normalmente y permaneció observable213.029s; `spb-basic-v1/verification.json`.
Su cierre fue ordenado. No se ha aislado la causa interna del salto de cámara.

Para completar observaciones útiles sin modificar el mundo: siete sesiones
regionales, conservando las doce poses originales y colocando al jugador
cerca sobre un punto seco. `visual-groups-index.json` congela referencias,
misiones y addons. El generador comprueba separación de agua >10m y altura
>1.25m; cada sesión restablece cámara y distancia solicitada al terminar.
Narva/SPB tienen tres vistas; reserva dos; Neva/norte/sur/general una.
Esto es cobertura visual, no prueba causal ni solución declarada del crash.

Presupuesto: una ejecución por grupo; conservar cualquier fallo sin reinicios
idénticos. Observar/capturar píxeles después del asentamiento, guardar identidad
de ventana y telemetría del mismo momento. La cámara y los contadores solo se
aceptan con registros completos y controles negativos sobre una ejecución real.
Computer Use se libera entre bloques. Los renders aéreos con nearplane10m siguen
siendo diagnósticos; no acreditan la vista aérea con clipping original.
