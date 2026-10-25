# EV21 — identificar la capa nativa que dibuja el residual

Diagnóstico reversible; no modifica terreno, agua ni materiales de producción.

La documentación oficial DayZ Diag Menu distingue agua, océano y espuma en wireframe y permite desactivar la familia Water. La API local `P:/scripts/1_core/proto/endebug.c:334-341` expone Get/SetEngineValue, pero no enumera sus IDs. No se adivinan IDs ni se barre el motor con escrituras.

Presupuesto: una inspección estática acotada del ejecutable diagnóstico, máximo 20 minutos, buscando únicamente el registro de Render debug mode, Terrain y Materials/Water. Si no hay correspondencia inequívoca entre etiqueta, registro e ID, no se ejecuta ninguna escritura. Un resultado estático no confirma consumo.

Si se obtiene un ID verificable: addon de prueba aislado, lecturas iniciales conservadas, cambio de una sola opción, comprobación positiva visible, readback, restauración y cierre normal. Máximo una sesión y una reparación de instrumentación. Sin repetición de cotas, colores, amplitudes o radios ya descartados. La geometría EV16 y sus PBO permanecen idénticos. Se conserva la diferencia entre capa identificada y causa corregida.

Fuente oficial: https://community.bistudio.com/wiki/DayZ%3ADiag_Menu

Herramientas auxiliares de análisis binario, si hacen falta, solo en esta carpeta externa; no son dependencias de producción ni del pipeline GIS.
