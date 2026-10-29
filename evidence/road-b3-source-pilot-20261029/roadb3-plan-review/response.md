Veredicto: **SOUND-with-fixes**. La unidad es coherente como plan de fuente aislada y no autoriza build ni motor; las correcciones son de contrato, no de enfoque.

**Verificaciones que cuadran**

- **Fuente**: el SHA b108352f del report coincide con el pin `reference_inputs` de recipe.json para el WRP de tb. Prefijo 17.307.629 bytes es consistente con cabecera 24 + alturas 2048·2048·4 + materiales 256·256·2 más tabla de nombres. Terminador 56 bytes coincide con 12f32+u32+u32 de wrp0wzd.py y con el `read(56)` de prune. Dimensiones 256/2048/48.0 dan 12.288 m, coherente con celda 6.0.
- **IDs**: máximo 19.394.563 y propuestos +1/+2/+3 están muy lejos del límite uint32. El plan exige releer todos los IDs y segundo censo count+3 en el consumidor. Correcto.
- **Preservación**: copiar bytes hasta el terminador, insertar 3 registros, mantener terminador y exigir EOF replica las invariantes de `wrp0wzd.read:49` y `prune.objects:30`. Evitar `write()` de wrp0wzd evita el round trip por numpy de alturas. Bien.
- **Consumidor independiente**: lectura desde archivo, sin importar autor, igualdad por streaming salvo 56 bytes finales, más pruebas negativas por invariante. Correcto.
- **Matrices**: las tres rotaciones de la receta son propias (det=1), valores exactos en f32, y la AABB/ventana de grid del report (94..106 × 287,5..312,5, celdas 15..18 × 47..53) y la holgura 196,427 = 200 − 3,573 son consistentes. La afirmación de que escribir 12 floats no elige hipótesis nativa es aceptable: fija bytes, no interpretación.
- **Límite 200000**: correctamente atribuido a la tabla de modelos de `compiled_arrays:34`, no a objetos.
- **Pins cruzados**: CAT_SHA en road_consumer_discovery coincide con el pin del catálogo en recipe.json.

**Defectos con evidencia y corrección mínima**

1. **Convención de bytes del nombre no especificada.** `wrp0wzd.read:47` hace `rstrip('\0')` y `prune.objects:32` hace `.lower()`, lo que indica que los nombres del WRP pueden llevar NUL final y casing variable. El plan dice "prefijo literal PBO + entrada exacta local con slash normalizado" pero no fija si el registro incluye NUL ni el casing resultante. Si el autor escribe sin NUL y el motor espera NUL, o viceversa, el consumidor lo aceptaría igual porque compara contra el mismo literal. Corrección: en el descubrimiento, censar los registros existentes cuyo nombre empiece por `DZ\structures\roads` sin distinguir mayúsculas, registrar su casing exacto y si terminan en NUL, y pinear en el contrato los bytes crudos completos de cada nombre. El consumidor compara bytes crudos, nunca tras `norm` ni `lower`.

2. **Mapeo instancia→modelo no pineado.** recipe.json ata cada instancia a `local-faces-N.json` por SHA, no al p3d. SELECTED tiene tres entradas, y dos rectas (300/225 m²) deben corresponder a asf1_25/asf2_25, pero el plan no dice cuál es cuál. Corrección: el manifiesto del contrato lleva una tabla instancia / clave SELECTED / SHA p3d / nombre crudo / ID, y el consumidor verifica que los tres registros terminales coinciden con esa tabla en ese orden.

3. **ID del terminador no registrado.** El terminador contiene u32 id (wrp0wzd.py:9). El report da su SHA pero no su valor; si ese id fuera max+1 u otro de los propuestos, habría ambigüedad semántica aunque la unicidad del censo pase. Corrección: añadir `terminator_id` al recibo de descubrimiento, asegurar que no está en los propuestos y documentar que el censo lo excluye deliberadamente.

4. **Helpers de lectura reutilizados decodifican ASCII.** `prune.objects:32` falla con bytes no ASCII y además normaliza. Para el consumidor es aceptable usar `prefix()`, pero el recorrido de registros debe trabajar sobre bytes crudos. Corrección: el consumidor usa su propio bucle `struct` de 56+longitud sin decode, y añade la comprobación de tamaño total: candidato = fuente + Σlen(registros).

5. **Evidencia de IDs en el report.** El plan afirma "IDs únicos positivos" pero el fragmento del report no muestra campos `min_id` ni `ids_unique`. Corrección: incluirlos explícitamente en report.json para que la afirmación de la línea 41 sea trazable.

**Observaciones menores**

- La línea 54 escribe `DZ\\structures\\roads`; es el literal Python de `check_prefix:21`, equivalente a `DZ\structures\roads`. Conviene escribir en el contrato la forma sin escape para no inducir un doble backslash en el nombre.
- Los presupuestos (120 s/2 GiB por proceso) son holgados: el descubrimiento en streaming tardó 5,859 s para 2,58 M registros.
- Nada en esta unidad promueve el candidato a build, binarización ni DayZ; el estado CANDIDATE_SOURCE_OFFLINE es el correcto.

Con las correcciones 1 a 3 aplicadas al contrato antes de escribir código, el plan puede pasar a autoría.