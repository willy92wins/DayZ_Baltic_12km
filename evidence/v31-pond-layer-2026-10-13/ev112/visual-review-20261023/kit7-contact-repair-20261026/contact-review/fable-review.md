**Veredicto: SOUND.** No encuentro bugs en el cambio `--contact-only`; las cuatro propiedades pedidas se cumplen en el código leído.

**Lo verificado**

- **Legacy por defecto.** `contact_only=False` en `tools/water/overlap_stream_collision_v31.py:43`. La condición de la línea 64 se parsea como `not contact_only and (anchors-if-minimal else (min==lo or max==hi))`, así que sin la bandera la selección es idéntica a la anterior. Sin targets sigue el camino `whole_model` con deltas ±1/512 esperados en 165-166. Test de regresión en `tests/test_overlap_stream_collision_v31.py:75-79`.
- **Excluye anclas.** Con `contact_only` nunca se añade `bbox_extremum` (línea 64) y la combinación con `minimal_bbox_anchors` lanza `ValueError` (49-50), cubierto por el test 80-83. En CLI, 102-103 rechaza la combinación antes de crear el directorio de salida.
- **Requiere targets.** `parser.error` en 102-103 si faltan. Además 105-106 exige que las claves coincidan exactamente con los modelos pedidos y que las coordenadas sean finitas, y la línea 72 aborta si algún modelo no tiene ningún componente de contacto. No hay no-op silencioso.
- **Rechazo si cambia alguna cota.** Líneas 165-166 comparan con `np.array_equal` exacto las seis cotas del LOD Geometry **releído desde disco**, no de la estructura en memoria. Fallo = excepción antes de escribir `overlap-report.json`, luego no hay PASS falso. Las aserciones están protegidas por el guard de `__debug__` (6-7).
- **Masa.** Total por componente conservado con tolerancia relativa 1e-6 (169-172) y total global (168); los componentes no elegidos deben ser byte-idénticos en coordenadas (173-175).
- **Otros LOD.** Reconstrucción `header + blobs[0] + geo + blobs[2] + blobs[3]` y verificación de igualdad binaria de los blobs 0,2,3 tras relectura (156-160). Código no modificado por este cambio.
- **Descubrimiento.** `discover_kit7_contact_only.py:13-14` selecciona con anclas mínimas y filtra a `contact_footprint`; es equivalente a `contact_only=True` porque la razón `contact_footprint` se calcula independientemente de las anclas. El JSON muestra 19 filas, todas `bbox_exact`, cero exceso horizontal y cero componentes sobre 72/140, con 2 o 4 componentes por modelo. La afirmación del plan ("las anclas eran innecesarias") es consistente con esos datos.

**Observaciones no bloqueantes**

- El operador no registra vértices/caras por componente ni comprueba el techo 72/140 ni la extensión 1cm; eso queda delegado al overlay externo, como prevé el plan. Conviene que la puerta de overlay sea la que lo certifique, no el reporte del autor.
- `kit7-contact-only-discovery.json` no incluye hashes del `author-report.json` ni de `targets.json` usados (el `hashlib` del script está sin usar). La trazabilidad del descubrimiento depende del manifiesto externo. En cambio, el operador sí registra `contact_targets_sha256` y `script_sha256`.
- El texto de ayuda de `--contact-targets` (línea 83) sigue diciendo "and bbox anchors", desactualizado en modo contact-only. Cosmético.
- `geometry_bbox_centre_exact=True` está fijo en el reporte (180); en contact-only es cierto por la aserción 165-166, pero no se deriva de ella.

**Condición para el motor**

El veredicto cubre el operador y la selección. La ejecución nativa debe mantener los 6801 puntos y umbrales existentes, y la puerta de overlay debe confirmar caps y extensión sobre el candidato real producido con los mismos targets cuyo hash quede en `overlap-report.json`.
