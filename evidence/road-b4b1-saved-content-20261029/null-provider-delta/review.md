**Identidad:** Claude Fable 5.1 (claude-fable-5-1), revisión nativa sólo lectura.

**Veredicto: SOUND-with-fixes.** La premisa refutada se confirma y el delta es correcto en dirección; hay cinco ajustes de contrato antes de la versión final.

**Premisa refutada: confirmada.** La línea 358 de `road_scene_reference_index_ev112.py` asigna provider=None cuando hay más de un proveedor canónico distinto. Sólo sobrevive el issue PROVIDER_CONFLICT con el nombre virtual, no la lista. Las cuatro filas reales de puentes (15, 8, 4 y 1 instancias) tienen provider null y estado UNRESOLVED, lo que es consistente. Por tanto el contrato R1 y el punto 4 de la revisión anterior partían de un dato que no existe en la tabla B4B0. La decisión de no implementar R1 ni relanzar B4B0 es correcta.

**Delta: aritmética y alcance verificados.**
- 15+8+4+1 = 28 instancias en conflicto histórico, coincide con historical_conflict_instances.
- 5508 + 4 = 5512 referencias, y 2578398 + 3 = 2578401 con las tres referencias nuevas de source_instances==0. El +3 queda bien separado de las 28.
- Las tres filas nuevas no pueden tener proveedor B2A porque is_new exige ausencia en counts y el conjunto B2A es igual al catálogo. Siempre serán single. Correcto.
- Claims, geometría, fuentes y método global intactos. Correcto.

**Fixes requeridos antes del contrato final:**

1. **Prefijo B2A sólo desde report.** El código usa el prefix de b2ar.packages (línea 302); config.package_pins sólo confirma el SHA y admite valor string o dict con sha256 (línea 285). El contrato dice "prefix from report/config", que es ambiguo. Fijar: prefix de b2a_report, SHA de ambos con igualdad obligatoria, y documentar la forma str o dict del pin.

2. **Replicar las puertas del proveedor vial.** El contrato menciona READ_STRICT pero no mime==0, unicidad de entrada y modelo, igualdad model sha == entry sha ni acuerdo con previous:assets/ (líneas 341 a 345). Sin esas puertas la reconstrucción puede producir un candidato vial que B4B0 excluyó por ROAD_PROVIDER, inflando una fila null a tres registros o contradiciendo una fila no-null. Exigir las mismas puertas y registrar la razón de exclusión como provenance no aceptada.

3. **Regla para no-null con más de una tupla reconstruida.** El contrato exige que el registro histórico exista, pero no dice qué pasa si la reconstrucción añade una segunda tupla distinta a una fila que la historia marcó PROVIDER_RESOLVED. Eso es contradicción con la historia, no DISTINCT_CONTENT. Añadir estado MALFORMED con issue HISTORY_PROVIDER_MISMATCH, global inconcluso, y negativo correspondiente.

4. **Pointer al issue histórico y "distintos" explícito.** Para filas null el contrato pide "al menos dos registros crudos", pero el código dedup por _canon antes de contar (línea 305 y 353). Debe decir dos tuplas canónicas distintas, y la fila debe apuntar al issue PROVIDER_CONFLICT exacto dentro de b4b0_report.issues por string literal "multiple distinct providers for <name>". Hoy el row schema sólo tiene historical_state y historical_provider.

5. **Oráculo y pointer JSONL.** El contrato sigue pinneando oracles-r1.json, que codifica la semántica refutada. Debe regenerarse como oracles-r2 y re-pinnearse, lo que cambia el hash del contrato. Además models.jsonl no es JSON y "pointers resolve in pinned exact source bytes" no define cómo: fijar índice de línea cero-based sobre división por \n, cada línea parseada sola, línea vacía final rechazada o ignorada de forma declarada.

**Observaciones menores, no bloqueantes:**
- preregistered_method_outcome es orden ortogonal; si una fila sale DISTINCT_CONTENT o BLOCKED, status será INCONCLUSIVE_SAVED_CONTENT_IDENTITY y method_binding_global seguirá METHOD_UNVERIFIED. Conviene decirlo en una frase para que nadie lo lea como predicción de status.
- El negativo "quitar un proveedor de fila null" debe redactarse como mutación de fixture de reconstrucción, no de la tabla histórica, que ya es null.
- Los cuatro puentes caen bajo el prefijo vial, así que el conflicto más probable es B2A package versus PBO vial con SHA de paquete distinto. Eso daría SAME o DISTINCT, no BLOCKED. No prejuzgar en el oráculo.

**Siguiente paso:** aplicar los cinco fixes al contract-r2-draft, regenerar oráculo r2, re-pinnear y recién entonces autoría dentro de los 240s. Esta revisión no autoriza código.
