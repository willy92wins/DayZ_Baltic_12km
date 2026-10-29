# Q02B2 — medición certificada en contornos reales

VERIFIED_REAL_NUMERIC_PILOT_ONLY. Cuatro cadenas reales fijadas por hash y offsets;
54 consultas: UNDEFINED_ZERO_CHORD: 9, INSUFFICIENT_SUPPORT: 32, DEFINED: 13. Se verificaron 18943 aristas. La cadena85
con dos segmentos cero se conserva como degenerada, sin generar ventanas.
No es el censo completo de1030cadenas ni un detector calibrado de naturalidad.

Productor1.000s/70.72MB RSS; consumidor independiente2.484s/97.98MB. 14pruebas
privadas2.890s PASS sin skips. El productor suma extremos enteros p48 en prefijos;
el consumidor verifica cada raíz y suma aristas directamente desde el ancla.
Coinciden soporte, estaciones e intervalos de rasgos de las54consultas sin
tolerancia añadida. El contrato externo84534d48, entradas, umbralbinario1e-8,
caps4096bits/100000ops porconsulta y4M porcadena se conservan.

El autorMuse172.063s y corrección119.860s entregaron. FableR0 agotó180.047s sin
dictamen; recuperación117.718s SOUND-with-fixes adjudicada. Codex integró los
fixes y sus negativos con contexto compartido, sin presentarlo como lane ciega.
Los fallosR0/R1 de tests permanecen archivados: h0 se esperaba incorrectamente
DEFINED y el guard del productor confundía core cerrado con punto final repetido.
R2 y final son ejecuciones posteriores a deltas concretos, no reintentos iguales.
El fixturehistórico literal30consultas ahora se lee porhash; no se regenera.

Se corrigió además comparación bool/int que Python considera igual, con negativos
de header, punto y consulta. El revisor había descrito erróneamente cacheexact como
byte a byte y la cadena13421 como cerrada; ambas precisiones están adjudicadas.
Los contadores del productor están acotados, no son transcript independiente de
operaciones ni prueba de que el consumidor hace el mismo número de cálculos.

Reporte detallado guardado privado, SHA f6d4f44cf5f8ca874d7ea3185b134902036d2e0d80d24a472e9470e332915325,
3768836 bytes. Se publica resumen ligado, consumidor,
contrato, herramientas propias y recibos; no geometría o textos vanilla completos.
Nueve rechazos humanos continúan GEOMETRY_UNBOUND/0resueltos, C1NOT_REVIEWED,
natural_positive_count0/calibration_readyfalse. Atan2/sumas de giro pendientes.
No reparación, pavimentado, build, DayZ, run ni lease. Todas las operaciones de
este piloto están consumidas; no repetirlo para simular un censo global.
