# Adjudicación B3F de código — 28-10-2026

Fable 5.1 nativo entregó SOUND-with-fixes en 116.000 s; entradas intactas,
sin denegaciones. Codex adjudica los hallazgos contra fuentes y contraejemplos.
No autoriza DayZ ni despliegue. La composición única conserva sus presupuestos.

1. Trailer: aceptado y corregido. Guard independiente exige cero o 21 bytes;
   en el segundo caso, cero inicial y SHA1 del prefijo anterior al trailer.
   Dos PBO reales sellados confirman esta forma en
   b3f-review-claims-20261028/report.json. Fixtures válido/corrupto/anexado pasan.
2. Identidad del consumidor: aceptado el problema. La igualdad directa con PID
   del launcher sugerida se rechaza: GIS usa launcher y proceso Python hijo.
   consumer_identity liga el PID del reporte a exactamente una identidad
   pid@birth del árbol propio observado, imagen resuelta y hash fijado.
   Positivo con PID hijo y negativos de PID/hash incorrectos pasan.
3. Sustituir sys.executable por imagen directa: no se aplica. Ambos importan
   numpy, pero desde site-packages distintos, medidos en el reporte de claims.
   Se conserva el entorno GIS probado y se liga la imagen real observada como
   en el punto 2. No se atribuye ausencia de numpy ni causalidad histórica.
4. Cabecera truncada: se conserva INCONCLUSIVE_PACKAGE para excepciones de
   lectura/parseo; ningún caso produce PASS. No certifica rechazo geométrico.
5. Wrapper externo: se incluye su hash en la aprobación antes de ejecutarlo.
6. Fixtures añadidos: compresión, Vers ausente/tardío/doble, terminador, trailer,
   original distinto de size. En entrada sin compresión, size manda, conforme
   al lector real; se documenta, no se interpreta original como cuerpo.

Suite final: 29 tests PASS, 5.203 s, en b3f-tests-final-20261028/report.json.
Las tres postimágenes finales están fijadas allí y en la aprobación específica.
La suite inicial de 22 tests y las postimágenes revisadas originales se conservan.
Límites: lector de cuerpos compartido, inventario instalado no DLL cargadas,
fixtures no certifican motor. 47 FAIL y 21 inciertos originales permanecen.

Estado: REVISIÓN_ADJUDICADA; código apto para la composición experimental B3F,
tras aprobación ligada a estas postimágenes y preflight fresco.
