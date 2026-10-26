# Kit7:607 rutas ejecutadas; altura de navegación todavía FAIL

**FAIL_KIT7_NATIVE_GRAPH**. Pasan607 consultas de conectividad y562 controles
locales de la polilínea XZ. Cuatro waypoints incumplen0,801m de distancia vertical
a Roadway. No hay aceptación global de navegación, actores, barcos ni vista.

| Caso | Error vertical | Exceso sobre0,801m |
|---|---:|---:|
| pieza124derecha/1 |0,852283m|0,051283m|
| junta124derecha/0 |0,875470m|0,074470m|
| pieza133derecha/1 |1,167696m|0,366696m|
| junta133derecha/0 |0,981493m|0,180493m|

La generación propia produjo704535052bytes,966289teselas TESMv9/VAND12 en97min22s.
NM SHA256:13e1ab1567740aca2ff94d6607b6f2c6423b9142674878562bf477994597f80b.
El paquete solo reemplaza NM;6826entradas restantes permanecen byteexactas.
Mundo SHA256:a2919a80ae6da6fc90e75b0ac55d1e9dd4ba4a39f6700b9fec237c7e7683b16c.
Los archivos grandes y los binarios de Bohemia quedan fuera de Git.

La sonda607 se ejecutó en servidor normal propio sin cliente. Cubre139piezas,
138juntas, extremos por ambas orillas y45regresiones anteriores. Conserva los
ocho testigosF y todos los umbrales fijados antes de consultar el motor.
Preparación, tests y revisión del consumidor:
[checkpoint previo](../kit7-navigation-consumer-preparation-20261026/README.md).

En ocho waypoints de las dos zonas, visual y Roadway coinciden; Geometry difiere
menos de0,008m. La altura guardada en los polígonos de tres teselas reproduce
las ocho alturas nativas con residual máximo4,82e-7m. Es evidencia local de una
aproximación vertical del navmesh; no una explicación completa del generador.
La lectura de polígonos es empírica y limitada a esas teselas. No se editó NM.

Ambos runs entraron por FIFO MCP sin preconsulta, terminaron con cierre oficial
propio y liberación de lease; pending0, cleanup[], selfnone. La automatización
periódica sigue pausada. Las comprobaciones estáticas no sustituyen locomoción.

Siguiente: aislar una corrección de generación que conserve cauce, transitabilidad
y tolerancias; repetir después las607consultas con identidad propia. No regenerar
igual ni deformar la orilla para hacer verde el contador. El piloto híbrido de
14vértices publicado aparte sigue sin integrar y no hereda esta navmesh.
