# Preparación de navegación de 12 m

Estado: preparación offline validada; generación y aceptación nativa pendientes.
Plan revisado por Fable 5.1 SOUND-with-fixes, reconciliado; implementación SOUND.
Configuración: 3 tests; prefijos de navegación: 6 tests; coordinación: 26 casos
y 9 mutantes rechazados. La mejora posterior a la revisión afecta solo al
harness: retrasa 30 segundos su reloj y detecta un inicio de presupuesto nuevo.
El coordinador revisado conserva exactamente sus bytes.

El input cambia únicamente tileWidth de 12,5 a 12. Las otras 6826 entradas
siguen idénticas; todavía contiene el NM previo y no es una malla nueva válida.
La generación comprobará 1024 x 1024 teselas de 12 m. El consumidor mantiene
las 607 consultas y límites 0,801 / 0,011 / 2,1 m. Solo si pasa se medirán seis
pasadas RAM nuevas, con ratio 1,10 y dispersión 5%. Nav8 conserva su 607 PASS
y su FAIL de RAM publicados; este checkpoint no los sustituye.

Las copias intermedias retiradas de C: se conservan byte por byte en E:, con
manifiestos de restauración. No se incluyen binarios, credenciales o logs de
otras sesiones. Las pruebas de coordinación usan mocks; no prueban el motor.
