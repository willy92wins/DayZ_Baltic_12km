# EV77 — clasificación visual nativa, diagnóstico único

La auditoría Luna encontró dos límites entre gris/ondas alineados con bordes de cuatro P3D, sin diferencia de material/flags explícita. El fondo bajo el mar es común a ambas zonas. El swap sugerido inicialmente NO conserva superficie porque las geometrías son distintas y se descarta.

Un run con EV72 original, cámara EV73 [2417,65,6745] hacia [2417,0,6950], FOV1.1,1920x1080. World/agua por hash; terreno, P/F, satélites, materiales y perfil intactos. ProbeV2 cambia solo nombres de archivos respecto al V1 ya utilizado; usa API DiagMenu Get/SetEngineValue (P:/scripts/1_Core/proto/endebug.c:334,336), índices comprobados de nuevo contra etiqueta/registro del ejecutable con SHA exigido. Lectura de memoria exclusivamente, nunca escritura/hook/inyección. Fases normal0, wire1, wire-only2 y restauración0/9; no usar Water-off.

Fuente primaria: https://community.bistudio.com/wiki/DayZ%3ADiag_Menu, sección Render debug mode. Water RGB51,51,255; Ocean51,128,255; Ocean Shore30,193,177. La documentación no garantiza exactitud de RGB tras capturar/antialiasing ni equivalencia de visibilidad con render normal.

Presupuesto: un run, una pose, tres capturas por fase; máximo10min de comparación tras referencia normal válida. No cambios de mapa ni barrido de parámetros. Referencia normal debe mostrar tierra/cielo cargados y defecto; si arranca inválida, pedir foco una vez y mantener pendiente, no llamar PASS a capturas magenta. Durante espera humana liberar lease conservando el run; readoptar antes de mutar. El probe se restaura solo a los1200s: no ejecutar fases fuera de ese plazo ni declarar comparación completa. Restaurar antes de cierre orderly, liberar lease y comprobar ocupación.

PASS de observación: pose/viewport nativos estables; reproducción normal válida antes/después; readback de fases y Water0; aristas diagnosticadas con clase distinguible y alineadas con modelo proyectado o plano de mar. Resultado puede apoyar que una región incluye Water/Ocean. No equivale a causa raíz ni a mapa reparado.

FAIL de ejecución: hash/pose distintos, API/etiqueta inválida, control no restaura. INCONCLUSO: no reproduce defecto, carga inválida, colores ambiguos, malla no identificable o visibilidad wire distinta sin contraste interpretable. Ausencia de línea sola no demuestra culling. Si ambas familias aparecen, no afirmar qué draw-call ganó en imagen normal ni explicar el mecanismo sin discriminación posterior.
