# EV21 — control nativo del renderizador verificado

Una sesión con terreno EV16 intacto. La API DiagMenu.Get/SetEngineValue está definida en P:/scripts/1_core/proto/endebug.c:334–341. Los IDs se obtuvieron del registro del cliente diagnóstico mediante lectura de memoria: dirección del objeto, enlace del registro y etiqueta exacta coinciden. El ejecutable está fijado por SHA256. No se escriben direcciones ni se inyecta código.

La primera referencia queda intacta. Render debug mode=1 dibuja la malla; Water=1 elimina toda la familia de agua y devolverlo a0 la restaura. El mismo control funciona cerca de las charcas. Esto establece consumo real, pero no identifica por separado océano, charca y espuma, ni demuestra que todo triángulo de espuma visible en wireframe sea inundación física. El centro seco calibrado no reprodujo de forma estable el parche fuerte original. BALTIC-016 sigue abierto.

Tras restaurar ambos valores se revisaron el borde rectangular histórico, R3 a distancia media y la reserva. Las texturas cargaron sin intervención manual. No se aprecia un escalón rectangular en la primera vista; las panorámicas más lejanas tienen bruma y no permiten aceptar todo el contorno. R3 y el río de la reserva son continuos en estas vistas, sin extender esto a todas las distancias.

Cliente y servidor cierran normalmente, lease liberado, owner nulo y cero runs. El addon diagnóstico no pertenece a la base. Los scripts de inspección estática conservan varias salidas parciales; el contrato operativo usado es api-value-access.json y la prueba en vivo live-ids.json. No convertir las direcciones particulares de este ejecutable en API portable.

Documentación oficial del modo wire y la familia Water: https://community.bistudio.com/wiki/DayZ%3ADiag_Menu
