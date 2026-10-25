# EV16 — remates con contorno nativo

Preview `@DayZ_Baltic_TerminalContourV1`: 478 vértices cambiados sobre EV14. Diez de quince cajas integradas; cinco descartadas e intactas. Fuente y consumidor triangular global pasan los límites físicos, de forma y topología; las 830 masas permanecen. No se han añadido ni cambiado modelos/objetos de agua.

El p90 global baja de 38,9483 a 38,7828 grados. Entre los remates aceptados, river_074 pasa de 57,4646 a 38,5049 y stream_0131 de 54,7117 a 33,9000 grados. Msta no se aplica: su propuesta no superaba el consumidor. La comprobación independiente a 1 m/±3 m confirma geometría exactamente igual en su caja y halo: p90 28,1771 antes/después. No se declara cumplido el estrechamiento histórico ni terminados todos los finales.

Cobertura contra los modelos compilados: 404.484 celdas, cero hueco físico, residuo visible 3,8464e-12 m². La primera auditoría usa ya el terreno nuevo. La comprobación final reutiliza ese resultado con identidad exacta de todos los objetos del WRP y del PBO de agua; `coverage_reuse_proof` explica la equivalencia, sin simular una segunda auditoría.

El censo nativo del run `09600f6e-cb0a-4310-942d-1542d9912180` comprueba 4.194.304 vértices, error de suelo máximo 0,0000152588 m y cero anomalías secas. Se inventarían 19 faltas de presencia y 308 escalares positivos sin flags; no se confunden con huecos físicos ni se interpreta la diferencia entre fases de ola como una mejora. Pasan los seis negativos del verificador. No se ha ejecutado un nuevo temporal 674×62; sus soportes se preservan, al igual que toda el agua.

Vistas diurnas de river_074 y stream_0131 guardadas en `frames/`; los primeros intentos oscuros se descartan por falta de sincronización inicial de la hora. El segundo disparo tiene señal heurística `render_frozen_signal`, aunque registra cuatro frames diferentes; no se usa para aprobar dinamismo del agua. Solo son comprobaciones locales de forma y textura. Cliente y servidor cierran normalmente; lease liberado y sesión disponible.

Hashes desplegados: mundo `c06f9b52d0b31d5c6e5cd3ec6c8cb14055abbe3ae40163092403b5ac66ca88fe`; agua `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`; terreno `70f74c9334620c458880f728d3ff15cec7867ffe2bd8bd2e9d5135e1692b7ed5`. Delta, scripts, informes y logs preservados. No es promoción a TB ni aceptación de la base completa.
