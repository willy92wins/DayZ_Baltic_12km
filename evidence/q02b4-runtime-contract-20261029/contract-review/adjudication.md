# Adjudicación Q02B4, 66.985s nativo Fable5.1

SOUND-with-fixes adjudicado para autoría, no medición. Primerreview120.078s no entregó dictamen; no lo contamos como aprobación.

1. REFUTAR confusión entre cap N=16777216 y máximo observado N=16777106. La cifra16782349 era correcta para cap;16782237 corresponde al observado. Añadir sumandos de ambos, sin bajar ni ampliar límites.
2. ACEPTAR progreso explícito: consumed_input>0 O produced_output>0 O transición eof. La producción desde buffer interno también cuenta, no sólo los dos casos del revisor. Paso sin ninguno rechaza. Trailer sin salida puede avanzar input/eof. No decoder.flush/max_length0.
3. ACEPTAR encoded_sha/bytes sobre concatenación ordenada de todos los retornos compress y flush, cap acumulado y porpieza.
4. REFUTAR OneDrive para captura: E:/DayZ-Baltic-Build/shape-repair-20261025/q02b3-coverage-20261029. W en C: tiene OneDrive, pero no se lee el corpus de W. No afirmar hidratación ni causa de latencia. Preservar timeout parcial legítimo bajo120s. No añadir guarda sobre nube sin evidencia.
Observación fsync: coste incluido en120s, no garantizar que cabe; salida parcial permitida. Refutar exigencia de leer fichero completo a memoria: hash y encoder consumen el MISMO chunk de64KiB de una pasada; SHA incremental acredita bytes del mismo flujo, no necesita fichero entero ni segunda lectura. Revisión no demuestra procedencia upstream ni techo RSS por sí sola; reserva128MiB sigue derivación condicional y guardexterno512MiB.

No autoría, codec sobre captura ni producción numérica repetida. Contrato final y oráculos se fijan antes de código. Implementación futura requiere review120s y suite90s antes de medición única120s512MiB/consumidor metadata60s. No relanzar sondeos consumidos.
