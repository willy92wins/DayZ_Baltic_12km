**Veredicto: SOUND-with-fixes.** El plan es coherente con A y con el censo nativo; no encontré contradicciones de APIs ni un falso PASS reproducible a nivel de plan. Hay cuatro riesgos de falso FAIL/PASS que conviene cerrar antes de escribir código. Limitación de esta revisión: sin Bash no pude recomputar los SHA256 de inputs.json ni comprobar el commit 6c125cca; comparé contenidos, no hashes.

**Verificado correcto**

- Los 28 puentes existen como grupo `bridge` del catálogo sellado: bridge_metal_25 (15), bridge_wood_25 (8), bridge_wood_50 (4), bridge_wood_50_1 (1) en `evidence/deployed-geometry-discovery-20261028/model-catalog.json:5478,10998,29124,31302`. Presas: grupo `dam` (:5850).
- Prototipos: 539009 caras, 362554/176390/65, 43 ambiguas, 0 degeneradas, residuo máximo 0,3543688 m (`E:/.../deployed-surface-prototypes-20261028/report.json:5-11`). Consumidor independiente 201 pilotos, 0 m (`independent-consumer.json:9-10`).
- Las caras proxy ya están en el marco del modelo raíz (`deployed_surface_inventory_ev112.py:191-196`), así que una sola matriz de instancia basta para el bbox; el flag PROXY_CONDITIONAL se conserva por cara (:194).
- Transformación `v @ m[:9].reshape(3,3) + m[9:]` (:82-85) coincide con lo validado en A.
- El universo de aristas está guardado con `graph_guard` (`road_water_contacts_ev112.py:111-124`) y la aserción 124/36428/36467 (:189). El censo publicó 770 aristas con contacto, 92 raíces y 1313 partes mojadas sin raíz interior (`evidence/road-water-census-20261028/report.json:11-15`).
- Shapely/STRtree ya se usan en tests del repositorio (`tools/quality/test_road_water_contacts_ev112.py`, `native_shore_census_ev112.py`), así que el oráculo propuesto es ejecutable.
- La separación nativa/modelo, EXPOSED/BURIED y la prohibición de certificar sequedad bajo marco condicional (plan :46-57, :65-70) responden exactamente a la precisión pendiente del plan padre (`ev112-deployed-mesh-road-overlay-20261028.md:194-203`).

**Fixes mínimos (no bloqueantes del diseño, sí previos al código)**

1. **Micro-huecos entre triángulos vecinos del mismo tablero (falso FAIL).** El plan exige unión exacta sin cerrar huecos (:37-38). Si el parámetro t del cruce con la arista compartida entre dos caras se calcula dos veces desde vértices en distinto orden, los floats difieren en ULP y aparece un hueco de 1e-16 dentro de un tablero continuo, que se leería como "hueco entre piezas" o un sliver WET_AXIS_WITHOUT_BRIDGE_ROADWAY. El censo evitó esto porque `cuts()` calcula cada corte una sola vez (`road_water_contacts_ev112.py:32-43`) y etiqueta slivers como `numerical_incidence_ambiguity` (:94). Fix: calcular t por arista única de malla (clave = par de vértices ordenado) y derivar los intervalos de cara desde esos cruces, de modo que vecinos compartan el mismo bit; conservar y etiquetar lo que aun así quede como NUMERICAL_SLIVER, sin tolerancia. Añadirlo a los casos de prueba.

2. **Roadway bajo el agua suprime el hallazgo sin estado propio (falso PASS).** El plan mide Ytablero-W (:62-63) pero WET_AXIS_WITHOUT_BRIDGE_ROADWAY solo se emite si "falte superficie de puente" (:65-66). Un tablero cuya Roadway queda por debajo o al nivel de la lámina (caso "sumergido" de las pruebas, :82) silenciaría el hallazgo. Fix: definir estados explícitos por capa, por ejemplo ROADWAY_ABOVE_WATER, ROADWAY_AT_OR_BELOW_WATER y ROADWAY_WITHOUT_WATER, y que sólo el primero cuente como "superficie de puente presente" en la regla de :65. Sin umbral: el signo de Ytablero-W es dato, no tolerancia.

3. **Caras ambiguas de los propios tableros.** Tres de los cuatro modelos de puente tienen dos caras Roadway AMBIGUOUS con residuo ~3e-6 m (`evidence/deployed-surface-prototypes-20261028/ambiguities.json:11-32`); afectan a 13 de las 28 instancias. El plan sólo guarda la envolvente convexa XZ (:40-43). Si el eje cruza únicamente esas caras, el puente queda INCONCLUSIVE sin ninguna altura. Fix: calcular W o Ytablero para ambos fans (0-1-2/0-2-3 y 0-1-3/1-2-3) y guardar el intervalo [min,max] por t, manteniendo la etiqueta INCONCLUSIVE_TRIANGULATION. Esto es lo que el plan padre pide en :218 ("límites conservadores para ambos casos") y no eleva ni aplana vértices.

4. **Hnativo no está ligado al mundo visitado.** El plan compara Wmodelo con el terreno 815ef8b7 (:19, :49). Ese NPZ es el terreno de autoría del merge kit-7; el mundo desplegado es WRP 0da63d3f / editable b108352f (`ev112-deployed-mesh-road-overlay-20261028.md:10-11`). No hay en el plan ni en la evidencia leída una afirmación hasheada de que la malla de alturas del WRP sea idéntica a 815ef8b7. Si difieren, EXPOSED/BURIED serían falsos. Fix: pinear la equivalencia con una referencia existente, o si no la hay, declarar Hnativo como "terreno de autoría, no muestreado del WRP" en limitaciones y en el nombre de los estados.

5. **Hashes de salida del censo.** El plan cita "contactos guardados del 28-10" (:19) sin hash. Pinear contacts.json 3827291e… y chain-coverage e53011aa… (`evidence/road-water-census-20261028/publication-source.json:9,13`) y el hash externo de partitions.npz, igual que hace el censo con sus entradas (`road_water_contacts_ev112.py:174-181`).

6. **Caras verticales en XZ.** Se conservan (:36) pero la intersección por semiplanos degenera. Fix: para normal con componente Y nula usar intersección segmento-segmento en XZ, intervalo puntual o colineal, y altura como intervalo [Ymin,Ymax] de la cara, etiquetado VERTICAL_FACE.

7. **Reutilizar la partición de terreno del censo.** Para cortar por caras nativas, cargar `cuts`/`faces_at`/`bary` del módulo del censo con su hash, en vez de reimplementar la diagonal TRI (0,1,3)/(0,2,3) (:20). Así la triangulación asumida es la misma ya expresada como límite, no una segunda hipótesis.

8. **Etiqueta de capa sólo desde el grupo sellado.** El plan separa presa, lecho y piedras (:59-60) y a la vez prohíbe clasificar por nombre (:29). Hacer explícito que la etiqueta proviene del campo `group` del catálogo sellado por hash y que la geometría decide el contacto. Las 201 piezas piloto tienen Roadway propia (`pilot-source-frames.json`, kind 0), que así nunca contará como puente.

**Límites ya expresos, no bloqueantes:** triangulación del terreno asumida, agua nominal 0,75 por defecto en celdas sin plano (`road_water_contacts_ev112.py:86`), marco proxy condicional, sin anchura ni conducción. No se piden aquí.

**Presupuesto:** el censo nativo usó 4,6 s / 802 MB commit (`report.json:24-29`); A usó 39 s. El preflight de pares bbox (plan :94-96) es suficiente; sugiero fijar un tope de caras candidatas por arista en el preflight para detectar charcas gigantes antes de ejecutar.

FIN_REVISION
