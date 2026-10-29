**Veredicto: CONTRATO_REQUIERE_FIXES antes de código.** El alcance y la clave de comparación son correctos. El defecto bloqueante está en `method_binding`: con los recibos listados no se puede afirmar RAW_ENTRY_BYTES para B2A, y para el catálogo sólo se alcanza método declarado, no ligado a la ejecución. Fixes concretos:

1. **B2A: método no verificable con estos recibos.** La adjudicación registra `correction_budget_used: 1` y `final_code_sha256` 394a99…, mientras `models.json` e31abb… figura como artefacto *unchanged* a través de esa corrección. Eso prueba que el código final no lo reescribió, no que lo produjo. El SHA del código previo a la corrección no está pinado en ningún archivo del contrato. Si no existe un recibo guardado del run r1 con su propio pin de código, B2A queda **METHOD_UNVERIFIED** obligatorio. No sustituirlo con el hecho de que la rutina de hash parezca igual leyendo el código actual: eso sería inventar identidad retrospectiva.

2. **Catálogo roads: método declarado, no ligado.** La aprobación pina el código y el reporte pina el PBO, pero ningún recibo registra qué código cargó el pid 73364. Introducir un estado de tres valores por fuente y exigirlo sin default: METHOD_BOUND (recibo del run nombra el SHA del código), METHOD_DECLARED (fuente sellada + aprobación, sin ligadura de run), METHOD_UNVERIFIED. Con los datos actuales el catálogo es DECLARED como máximo.

3. **Resolver la pregunta abierta del borrador.** INDEPENDENT_PIN_MATCH es inalcanzable con estos recibos y el contrato debe decirlo ahora, no dejarlo al autor. Toda coincidencia cruzada B2A/catálogo se etiqueta DECLARED_PIN_MATCH. Resultado global: SAVED_CONTENT_IDENTITY_VERIFIED_ONLY sólo si ninguna fuente usada en una comparación está en UNVERIFIED y el resultado lleva campo obligatorio `method_binding_global` con el peor valor por fuente. Si alguna fuente comparada queda UNVERIFIED, el global es INCONCLUSIVE_METHOD_BINDING aunque todas las filas sean SAME_PINNED_CONTENT. Dado el punto 1, el desenlace realista es INCONCLUSIVE_METHOD_BINDING salvo que se localice un recibo r1 ya guardado. Preregistrarlo así evita que una suite "verde" se lea como PASS.

4. **Origen de la clave.** Fijar que los grupos se construyen desde los SHA PBO/modelo contenidos en las filas del reporte B4B0 (es lo que :244-245 guarda), y que B2A/catálogo actúan sólo como contraste de pins. Para B2A el SHA de paquete llega por lookup del locator crudo en `report.packages`/`config.package_pins`: declarar comparación de cadena exacta, sin normpath ni basename; locator no encontrado → UNRESOLVED. Hoy el contrato dice "report packages == config pins" pero no cómo se une fila de modelo con pin de paquete.

5. **Ligadura del contrato B4B0.** `b4b0_contract` apunta a una copia en `tests/fixtures/road_b4b0`, no al origen. Exigir que el reporte 88589882 o result.json declaren el SHA b14834… del contrato consumido; si ningún recibo lo nombra, la ligadura queda UNRESOLVED y se dice.

6. **Qué es consumer.json.** 3558093 bytes frente a 3558090 del reporte y `child_executable_independently_recorded: false`. Es casi seguro una salida, no un script. El contrato debe declarar su naturaleza a partir del contenido observado, y no describir 53bd9540 como "consumidor" en sentido de ejecutable.

7. **Entradas excluidas explícitas.** Añadir `excluded_inputs` con saved-provider-comparison.json y toda ruta WRP/PBO/P3D/material citada por los JSON. Su ausencia en `files` no basta para impedir que el autor lo lea como oráculo.

8. **Denominadores preregistrados.** `expected` debe incluir `single_pinned_content_references: 5508` y `multi_provider_references: 4`, además de la regla de que todos los conteos se recomputan desde la tabla y se cotejan con `expected`, nunca al revés. Falta también explicar que la diferencia 2578401 frente a 2578398 son los tres candidatos nuevos, no las 28 instancias históricas; dejarlo escrito para que no se reconcilie a mano.

9. **Oráculos incompletos y contradictorios.**
   - Faltan fixtures literales de SINGLE_PINNED_CONTENT, UNRESOLVED, MALFORMED y METHOD_UNVERIFIED; el borrador exige estos estados sin defaults pero sólo da SAME/DISTINCT/BLOCKED.
   - Faltan oráculos de join: ("DZ/X/", "/A.P3D") → "dz/x/a.p3d"; ("dz", "x//a.p3d") → rechazo; prefix vacío → rechazo o estado definido.
   - `sha64_invalid` aparece sólo como nombre; añadir literales: hex en mayúsculas, 63 caracteres, carácter no hex.
   - En `conflicting_model_same_virtual`, `groups: 2` con mismo SHA PBO es una inconsistencia de metadatos, no dos identidades. Definir que BLOCKED no aporta grupos al conteo de identidades y reporta `observed_keys: 2`.
   - Rechazados: añadir nombre vacío, componente "..", y longitud > `name_bytes`.
   - Tras corregir, repinar `oracles-draft.json`; el SHA actual 73c970… queda obsoleto.

10. **Esquema del reporte nuevo.** Cerrar ahora los campos por fila: estado, `physical_precedence_unknown: true`, lista de procedencias con `source_file_sha`, pointer, `package_locator`, `prefix_raw`, `entry_raw`, y `method_binding` por fuente. Sin esto el consumidor independiente no tiene contra qué validar y la "co-mutación productor+reporte" no es testeable.

11. **Presupuesto.** El consumidor B4B0 tardó 22 s con JSON de tamaño similar; 30 s por derivación es techo plausible pero ajustado. Mantenerlo como medición, no como garantía, y registrar que la saturación es INCONCLUSIVE sin reintento, como ya dice el plan.

Lo que no cambia: cero apertura de WRP/PBO, B4B0 sigue VERIFIED_MISMATCH_DIAGNOSTIC histórico, `build_ready` false, `loaded_extractor_image_identity` NOT_CERTIFIED correcto. Siguiente paso: aplicar los fixes 1-10 al JSON del contrato y a los oráculos, repinar ambos, y sólo entonces autoría.
