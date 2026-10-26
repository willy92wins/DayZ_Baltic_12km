# Kit7:607 consultas preparadas y revisadas

Este checkpoint guarda el nuevo consumidor, su misión y el contrato geométrico.
No contiene un PASS de navegación nativa: la NM propia está en generación.

45regresiones conservadas (solo dos Y actualizadas al cauce actual) y562rutas
locales fijadas antes de consultar el motor. Cubren139piezas,138juntas, extremos
naturales y transiciones al terreno por ambas orillas. Los corredores se han
contrastado con Roadway extraído del PBO y poses leídas del WRP compilado.
No invaden agua; las piezas contiguas permitidas se distinguen de las piezas
obligatorias. El consumidor comprueba la polilínea completa y recalcula el
corredor, su zona exterior y su cobertura con los binarios congelados.

11fixtures geométricos y19controles sintéticos del consumidor;11escenarios del
lifecycle y8del wrapper. ValidadorEnforce:1archivo,0errores,0avisos.
Plan y código revisados por Fable5.1 y correcciones verificadas. Los resultados
sintéticos solo prueban el verificador; nunca se usan como evidencia del juego.

El MCP concede el turno mediante FIFO nativo de dayz_test_run, sin sondeo previo
del banco ni takeover. La automatización periódica anterior quedó pausada.
Tras terminar generación, inspección y empaquetado exclusivo deNM, se ejecutará
la sonda en un servidor normal propio y se registrará su cierre oficial.

Quedan pendientes el grafo nativo607, locomoción, revisión visual, rendimiento
del paquete actual y los defectos globales del mapa. Los binarios grandes no se
publican en este repositorio; se conservan identidades y evidencia reproducible.
