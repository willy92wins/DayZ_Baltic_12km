Modelo servido al retorno: `muse-wonder-1.0` — Muse Wonder 1.0, CLI nativo.

## Dictamen: SOUND-with-fixes

La partición exacta está justificada para este snapshot y conserva el objetivo sin inflarlo. No requiere tocar `e967`, reclasificar Q03B4 ni crear infraestructura genérica. Las correcciones siguientes deben entrar al congelar el contrato, antes de código.

### Lo que sostiene el plan

- El hueco está medido, no inferido: 539009 filas, `model` 5434/5437 y `source_model` 5440/5443, faltando exactamente 216/226/238 y sin inesperados, con reporte `13e24bf8…19247c11b`.
- Las metadata pinadas son compatibles con selección guardada vacía bajo el escritor citado: sin LOD `ROADWAY=3000000028082176.0`, sin secciones de agua en Visual 0 y `proxy_count=0`. El ancla [writer 131-170](/tools/quality/deployed_surface_inventory_ev112.py:131) explica el mecanismo —selección Roadway/Visual-agua sobre metadata completa conservada— sin certificar causalidad histórica ni motor. El plan respeta ese límite: `cause=NOT_ESTABLISHED`, `kind_semantics=SAVED_CLASSIFIER_ONLY`.
- La partición es exhaustiva y disjunta por construcción, con excepciones preregistradas y no derivables de la ausencia en META. Eso cierra el falso supuesto de Q03B4 sin convertirlo en ignore-list.
- El techo de resultado es honesto: `VERIFIED_SAVED_SELECTED_SURFACE_INDEX_ONLY`, con las 969 instancias (702+158+109) conservadas en catálogo y poses, cero runs, y la geometría Visual ordinaria como deuda `NOT_SAVED` explícita que bloquea aceptación global en Q03C/Q05.

### Fallos a corregir

1. **El predicado vacío no certifica por sí solo el rol `source_model`.** Un modelo con selección propia vacía y proxies propios vacíos podría aun así aparecer como fuente si otro modelo lo invoca como hijo proxy con agua descendiente ([writer 173-198](/tools/quality/deployed_surface_inventory_ev112.py:173)). El plan se salva porque el consumidor recorre META de forma independiente y contrasta ambos conjuntos completos, pero la redacción «cada excepción sólo es válida si las metadata satisfacen el predicado» sobredeclara. Fix: el certificado de fuente vacía = predicado propio **y** ausencia de rutas proxy entrantes en `proxy-paths` pinado **y** conteo cero en el recorrido META independiente. Añadir el negativo correspondiente: vacío propio alcanzado como fuente vía proxy ajeno.
2. **Identidad de excepción ambigua entre espacios de índice.** La metadata distingue `catalog.index` 216/226/238 de `sections_index` 5293/5283/5271. El contrato debe pinar la excepción como tripleta (nombre, índice de catálogo, índice en secciones); un «ID» desnudo permite que un rol valide contra el espacio equivocado. El negativo «ID/name cambiados conservando cantidades» debe aplicarse a cada componente de la tripleta.
3. **Alcance del predicado sin fijar contra el escritor.** «Cero secciones de materiales de agua» debe limitarse al LOD Visual elegido, que es lo único que el clasificador selecciona ([writer 154-155](/tools/quality/deployed_surface_inventory_ev112.py:154)); exigirlo en todos los LOD sería más estricto que la semántica guardada. Simétricamente, «ningún Roadway con caras» debe definirse como: sin LOD con resolución exactamente igual a `ROADWAY`, o con ese LOD en cero caras —la igualdad es exacta en [writer 136](/tools/quality/deployed_surface_inventory_ev112.py:136), sin tolerancia. Añadir dos oráculos frontera: Roadway presente con cero caras (vacío válido) y material de agua sólo en LOD no-Visual (no invalida).
4. **Unicidad del Visual no enumerada como guarda.** El predicado invoca «regla histórica única», pero los negativos no cubren resolución Visual duplicada en el mínimo, que el escritor rechaza ([writer 135](/tools/quality/deployed_surface_inventory_ev112.py:135)). Añadir ese negativo explícito; «elegir Visual incorrecto» no lo subsume.

### Límites

Nada en esta cápsula prueba ausencia física: las metadata muestran caras Visual ordinarias abundantes (p. ej. 4226 en el LOD 0 de 216) que simplemente no están guardadas en el NPZ. El índice resultante certifica superficies seleccionadas guardadas, no geometría de escena. Carreteras, ángulos, referentes independientes, 9 humanos sin resolver y C1 `NOT_REVIEWED` quedan abiertos, correctamente fuera de esta unidad.

## Cierre: CONVERGE

Con los cuatro fixes incorporados en el contrato congelado —sin nueva lane ni reapertura—, Q03B6 puede pasar a implementación acotada en carpeta nueva sobre los snapshots R1, con producción y consumidor sólo tras las puertas presupuestadas.
