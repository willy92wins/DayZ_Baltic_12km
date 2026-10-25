# Observación agrupada: Neva, reserva y sur

NevaV2 pidió captura nativa con aplicación activa pero no produjo DDS. NevaV3
restauró la cámara correctamente, pero estaba inactivo al llegar al guard y no
llamó a MakeScreenshot: no acredita un fallo del nombre de archivo absoluto.

[EXACT] `proto.c:136-142` admite ruta completa si empieza por `$`.
`prepare_native_visual_fullpath.py` preserva posiciones/foco/restauración de V1.
Las tres referencias originales contienen el mundoV10 y poses congeladas.

[DESIGN] V4 conserva posiciones, óptica, clima, jugador y mapa. Amplía cada pose
de45 a90s para observarla sin movimientos manuales y solicita una sola captura
nativa a los60s de fase, bajo el mismo guard IsAppActive. Métricas10..70s.
Neva y sur terminan108s después de comenzar la sonda; reserva198s.

Preparar y verificar los tres paquetes antes de Computer Use. Un bloque de
observación, con una carga local por región para evitar el salto distante ya
reproducido. Seleccionar la ventana real, observar sin input si basta; activar
DayZ solo si la captura nativa necesita foco. Guardar píxeles originales y
proveniencia cuando estén disponibles. No aceptar por telemetría sola, ni
atribuir a la escena un crash exclusivo de la sonda distante.

Terminar el bloque al acabar las tomas. Sin UI durante cálculo, empaquetado,
logs o NavmeshGenerator hasta que haya un nuevo terreno aceptado. La API Sky
leída no documenta método explícito de liberación; no inventar uno.
