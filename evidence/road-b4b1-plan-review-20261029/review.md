**Modelo:** Claude Fable 5.1, revisión solo lectura, sin herramientas. No pude abrir `road_scene_reference_index_ev112.py` ni los JSON fijados; las líneas citadas y los SHA se toman como declarados.

**Veredicto: SOUND-with-fixes.**

El núcleo es correcto: separar representación de filesystem de contenido virtual, key de contenido sin locator, locators distintos como SAME_PINNED_CONTENT y no SAME_PHYSICAL_PROVIDER, claims físicos NOT_EVALUATED, y no usar el booleano guardado como oráculo. Los presupuestos son holgados para 5512 referencias y 28 instancias afectadas. Los negativos cubren traversal, procedencia, co-mutación y reapertura centinela.

**Riesgos de falso PASS**

- **Igualdad de SHA tautológica.** Si B4A3 o road_catalog heredaron package_sha256 y model_sha256 del índice B2A en lugar de recalcularlos, la igualdad confirma copia, no contenido. Fix: por cada pin, registrar el recibo que lo produjo y clasificar la igualdad como INDEPENDENT_PIN_MATCH o INHERITED_PIN_MATCH. Ambas valen SAME_PINNED_CONTENT, pero el reporte debe distinguirlas.
- **Método de hash no verificado.** Los dos índices deben declarar en su esquema que model_sha256 es SHA-256 de los bytes extraídos de la entry. Si una fuente no lo declara, su pin no es comparable y la fila queda UNRESOLVED, no equivalente.
- **Hex sin validar.** Validar 64 caracteres hex antes de comparar; comparar en minúsculas sólo tras validar. Vacío, truncado o no hex rechaza. Añadir fixture.
- **Strip exterior.** Recortar espacios puede fusionar dos entries distintas de la fuente. Como el SHA modelo gobierna la key, el riesgo de contenido es bajo, pero registrar que hubo strip como procedencia y añadir fixture con espacio final.

**Riesgos de falso FAIL y cobertura**

- **Join exacto ambiguo.** El name del reporte ya está en minúsculas; el join crudo "dz/structures/roads"+"Bridges/Bridge_Metal_25.p3d" no coincidirá literalmente. Especificar: join normalizado debe igualar el name del reporte; join crudo se conserva como observación. Si no, las 28 instancias fallan por construcción.
- **Resultado global binario oculta el progreso.** Una referencia sin proveedor en ninguna fuente convierte todo en INCONCLUSIVE sin decir cuántas filas sí resolvieron. Fix: clasificación por fila (SAME_PINNED_CONTENT, DISTINCT_CONTENT, BLOCKED_SHA_CONFLICT, UNRESOLVED, MALFORMED) con conteos y de instancias, y el veredicto global derivado de esos conteos.
- **Prefijo con slash final.** Añadir fixture donde prefix "dz/structures/roads/" y entry sin slash inicial normalizan al mismo name; debe agrupar, no rechazar como componente interior vacío.

**Separación de identidad física**

Correcta. Dos observaciones: la fila guardada de B4B0 no debe reclasificarse aunque las cuatro equivalgan, y eso está declarado. Añadir al reporte el campo `physical_precedence_unknown: true` por grupo para que un consumidor posterior no infiera precedencia del orden de procedencias.

**Presupuestos y negativos**

Suficientes. Falta un negativo explícito: recibo de fuente con SHA que no coincide con el archivo leído produce INCONCLUSIVE con evidencia conservada y sin retry. Falta otro: entries no ASCII en origen rechazan sin excepción no controlada. Mantener la doble lectura rawstat/hash y el cap de 32 MiB como está.

**Fixes concretos antes de autoría**

1. Añadir clasificación de procedencia de pins (independiente/heredado) al contrato.
2. Exigir declaración del método de hash en el esquema de cada fuente.
3. Definir join normalizado como criterio de coincidencia con el name del reporte.
4. Reportar conteos por categoría de fila además del veredicto global.
5. Fixtures: hex inválido, espacio final, prefix con slash final, recibo que no coincide, no ASCII.

Nada de esto cambia build_ready ni la lectura histórica de B4B0.
