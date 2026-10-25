# Discriminador del nivel del mar — EV15

Consumidor: comparación nativa/gráfica del residual del puente BALTIC-016. La prueba de colores de materiales R1/R2 no tuvo control positivo y su presupuesto está cerrado. No identifica ni excluye Shore/ShoreWet.

Una comparación A/B: referencia GlobalContourV1, misión estática viento 20 m/s, cámara R1 registrada en EV14; candidato diagnóstico con un único override `MaxTide=0` en CfgWorlds BalticTrial. `MaxWave=0.1`, terreno, estanques, materiales, hora, clima y cámara conservados. La predicción a comprobar es que cambia el nivel nativo del mar; no se presupone cómo lo usa el render. No se incorpora el añadido al mapa de distribución.

Puertas antes de ejecutar: hashes idénticos de los dos PBO del mapa, lectura cliente del valor de configuración y nivel nativo del mar, cliente vivo, texturas cargadas, misma cámara. Control visual del mar en EDGE1; ausencia de efecto allí deja la comparación de materiales/render inconclusa. Residual que persiste excluye solo este factor en las condiciones observadas; desaparición localiza una dependencia del nivel del mar, no prueba aún qué shader/malla la causa. Capturas no sustituyen la cobertura compilada ni el censo físico de todo el mapa.

Presupuesto: un valor diagnóstico y una reparación únicamente por defecto ejecutable de preparación. No variantes de cotas/oleaje ni aceptación permanente por una imagen. Tras el ensayo se cierra el run y se vuelve a los PBO normales. Siguen pendientes forma/taludes, finales, lagos y consumidores de base.

Fuentes verificadas: P:/scripts/3_game/global/game.c:1174-1180 (lectura nativa del mar); config.cpp de GlobalContourV1:22-23 (MaxTide/MaxWave actuales); lectura de MissionGameplay de EV10 usada en motor en EV14. `MaxTide=0` es un contraste experimental, no una recomendación de configuración final.
