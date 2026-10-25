# OT3 Narva — revisión Codex y cierre offline, 18-10-2026

**SOUND offline, listo para integrar.** Sin críticos ni mayores abiertos en los nueve archivos entregados de la ronda 3. La aceptación en el motor y la medida sobre la cadena final EV112 siguen pendientes de OT7/OT8.

Evidencia completa: `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-ot3-20261018/`.

- `regate-a/steps.json`: los 12 pasos terminaron con el código esperado. G1–G4 PASS; 18 negativos geométricos y seis grupos auxiliares detectados. El control sin wrapper falla como se esperaba.
- `regate-a/dam/bury-report.json`: cero vértices modificados y ningún borde expuesto nuevo (29 preexistentes).
- `regate-a/verify-exact.json`: PASS, 13498 registros, 8098 modelos y 759954 medias celdas; ninguna LOD visual/roadway ausente, múltiple o fuera de sitio. Error máximo roadway 7.6294e-7 m.
- `independent-a.json`: las 14 comprobaciones independientes pasan. Contrato exacto de 21 vértices, ninguna bajada ni cambio de máscaras, 33 celdas retiradas tanto de cover como de envelope, ninguna añadida, alturas retenidas idénticas.
- Los 178 puntos de sonda (20 de cresta) concuerdan con terreno y roadway ODOL transformada mediante la pose float32 que consume WRP: error máximo 4.8312e-5 m y 3.5129e-5 m respectivamente; cero discrepancias de clasificación.
- Comparación independiente con siete presas reales de Livonia: exposición máxima de referencia 0.38960641 m frente a 0.37000008 m en Narva, holgura real 0.01960633 m (nominal 2 cm). El kit OT1 aceptado, run-l, conserva exactamente el terreno EV110 en el entorno de 110 m de la presa.
- Los nueve hashes fuente coinciden con `handoff-20261018/wip/ev112-dam-r3-top/deliver-manifest-9.json`.

La revisión leyó el contrato y su aplicación en dam_v31, las comparaciones independientes G3/G4, las resoluciones LOD requeridas por verify_pond_exact, el generador/evaluador de sonda y el wrapper ODOL56. Los negativos incluyen agua nueva fuera del área, máscara Narva retirada, bajada submilimétrica, vértice congelado fuera de lista, contrato alterado, cota nueva incorrecta, plano retenido modificado y LOD roadway errónea. El wrapper rechaza bytes adicionales no nulos y solo se valida aquí para este inventario.

`check_independent.py` no importa productor, puertas ni generador de sonda: mide los artefactos, los triángulos nativos y las roadway con resolución baricéntrica propia. Comparte únicamente el lector binario ODOL existente. Los ensayos margin/composite/kitv9 del runner usan prototipos antiguos: no se presentan como verificación de la cadena final. El estrés ±1 m es diagnóstico aislado; no amplía los 21 vértices autorizados.

Pendiente obligatorio en OT7: aplicar la presa después de kit/puentes, repetir G1–G4, bury, comprobación exacta y medir la holgura sobre ese terreno real. En OT8: sonda empaquetada y desplegada. Sin despliegue ni prueba de motor en este cierre.
