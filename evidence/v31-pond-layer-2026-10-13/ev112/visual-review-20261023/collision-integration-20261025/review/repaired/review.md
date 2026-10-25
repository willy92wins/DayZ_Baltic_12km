**Veredicto: el contrato geométrico de la unión de sólidos está bien formulado y la prueba formal es correcta. No encuentro falsos verdes en el certificado.** La objeción de mi NO-GO anterior (extremo sin localizar, magnitud sin explicar) queda resuelta: el extremo está identificado y la cobertura exacta demuestra que es una cara interna. Lo que sigue sin prueba es el motor, no la geometría.

## Qué verifiqué de la prueba

**Semántica.** Para sólidos convexos cerrados con normales interiores, la superficie superior de cada componente es exactamente el conjunto de caras con normal interior apuntando hacia abajo. La superior de la unión es el máximo de esas caras. Si toda cara cumple ≤ fuente+2cm y en cada punto existe una cara ≥ fuente−2cm, el máximo queda dentro de la banda. Los fondos nunca forman la superior porque cada fondo está bajo el techo de su propio componente. El razonamiento es sólido.

**Exactitud del certificado.** La intersección de dos triángulos es convexa y el error es lineal sobre ella, así que el recorte por semiplano en `collision_contact_union_v31.py:13-27` es exacto. Las regiones se acumulan por triángulo fuente y se exige diferencia nula. Ningún muestreo interviene.

**Dirección de los fallos numéricos.** El búfer de 1e-7 m solo absorbe huecos de décimas de micra. Si GEOS devolviera un MultiPolygon por robustez, el par se descarta y el resultado tiende a falso rojo, no a falso verde. Un hueco real de 1 mm se detecta (test `narrow_gap`).

**Localización.** Las etiquetas de extremos mapean en el mismo orden en que se concatenan lecho y techos, así que modelo, componente y triángulo son correctos. El mínimo −0,203 m está en el componente 60 del chunk 0000, con área de intersección de 3,7e-7 m² según el diagnóstico, y la cobertura certificada lo cubre. Hipótesis B confirmada por prueba, no por muestra.

**Lecho univaluado.** La autocomparación con tolerancia 1e-6 y extensión lateral 0 detectaría cualquier pliegue con alturas distintas.

## Afirmaciones de fail-closed

- **Degeneración aborta:** correcto. Los `ValueError` de `fit_grid` y el `QhullError` del fallback 2×2 no se capturan y abortan. Solo el `QhullError` de un bloque grande subdivide, lo cual termina igualmente en abort si persiste. El consumidor lanza excepción ante polígonos o recortes inválidos.
- **Inferencia de grid validada por consumidor:** correcto. El lecho se toma de las caras visuales guardadas del original (`review_compact_collision_v31.py:79`), las LOD 0, 2 y 3 se comparan byte a byte, y la cobertura total descartaría un orden de columnas erróneo.
- **py3d fijado por hash:** **parcialmente falso.** El revisor registra el hash de `__init__.py` en la salida, pero no lo compara con ningún valor esperado. Ese hash solo aparece en ficheros de salida, no en código ni en provenance del autor. Es trazabilidad, no fijación.

## Defectos concretos

- **`review_compact_collision_v31.py:71,75-78,91` y `compact_stream_collision_v31.py:96,102`:** las comprobaciones de hash, byte-exactitud y volumen firmado son `assert`. Con `python -O` desaparecen en silencio. Deben ser `raise`. No bloqueante hoy, pero contradice el fail-closed declarado.
- **`tests-collision-final.json`:** 91 tests sin hash de los módulos probados ni commit. No se puede atar ese resultado a los hashes que figuran en el informe de contacto.
- **`contact-union-probe.json`:** sin hashes, script ni rutas. Sus números coinciden con el informe formal, pero no es evidencia independiente y no debe citarse como tal.
- **Franja lateral sin cota vertical:** las caras de techo fuera de la huella del lecho (hasta 1 cm) no se comparan en altura. Límite de diseño conocido, sin cambios.
- **Tests sin cubrir:** el mapeo de etiquetas de extremos y `main()` no tienen test. Tampoco hay test de una cara que supere +2cm solo en una esquina lateral.
- **Cosmético:** `lower_coverage` recibe `source_polygons` y no lo usa.

## Sin prueba, nombrado sin convertir

- **Modelo de contacto del motor.** La prueba asume que el motor consulta la unión de componentes convexos de la Geometry LOD. El binary review muestra una Roadway LOD con el mismo número de caras que la visual. En RV los personajes suelen apoyarse en Roadway cuando existe, y Geometry rige vehículos y proyectiles. Cuál de las dos gobierna el contacto de un jugador en este asset no está comprobado. Esto no invalida la geometría; delimita qué certifica.
- **Rendimiento con 2245 componentes.** Fuera de alcance de esta revisión, sin medir.
- **Lectura ODOL compilada en WRP.** El propio binary review lo declara pendiente.

No ejecuté nada: los hashes de `reviewer_sources` no los he recomputado contra los ficheros leídos.