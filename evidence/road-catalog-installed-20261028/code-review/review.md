Revisión en modo sólo lectura del catálogo A, sin herramientas ni ejecución; los repros son analíticos y el receptor debe confirmarlos.

**Veredicto: SOUND-with-fixes.** El contrato A se respeta en lo esencial: denominador completo (línea 44 y 83), doble parseo de tabla (41-48), pin antes/después (105, 117), lector estricto sin CLI (111-115), cruce raw/decoded (61-65), ningún array exportado, `usable_width` fijo (78, 85), trailer sólo forma (51). Los fallos son de clasificación de errores e integridad de salida, no de producto.

**Bugs concretos**

1. **Serialización fuera del `try` rompe la clasificación por entrada.** Líneas 93-97 y 114. El `try` cubre decode y `model_metadata`, pero `emit` corre fuera. Repro: un modelo cuyo `named_properties`, `textures`, `sections` de selección o `material_name` contenga bytes, objetos del lector o un float no finito. `json.dumps(allow_nan=False)` lanza, la excepción sale de `collect`, `execute` aborta y `models.jsonl` queda parcial sin que esa entrada figure como INCONCLUSIVE_PARSE. Consecuencia: un campo no serializable convierte un fallo local en caída global y pierde el denominador en el jsonl. Fix: dentro del `try`, tras `model_metadata`, hacer `row['measurement']=json.loads(json.dumps(measurement,allow_nan=False))` o coaccionar strings con `str()`; mover `emit` también a una ruta que nunca lance por el contenido.

2. **No hay guardia propia de duplicados normalizados.** Líneas 44-49 confían en que `read_pbo` o `pbo_table` rechacen `parts/A.p3d` frente a `parts/a.p3d`. Si ambos helpers sólo rechazan duplicados exactos, la lista lowercase de la línea 44 coincide, los payloads cuadran y el catálogo emite dos filas con el mismo `normalized_name`. Consecuencia: la prueba `test_duplicate_case` depende del texto `Duplicate` de un helper y el catálogo acepta una colisión de nombres que en NTFS extrae al mismo archivo. Fix: en `check_table` añadir `require(len({e['name'] for e in table})==len(table),'duplicate_normalized_name')` y que el test acepte ese mensaje o el del helper.

3. **Sólo `odol_reader` se verifica como módulo cargado.** Línea 112. Los pins de `bis_reader.py` y `math_types.py` se comprueban por hash de archivo, pero no que los módulos importados por el backend procedan de esas rutas. Con `HERE` y `playtest` al frente de `sys.path` desde la línea 8, un `bis_reader.py` homónimo en esas carpetas no es imposible. Fix: tras importar, `require(Path(sys.modules['bis_reader'].__file__).resolve()==READER/'bis_reader.py')` y lo mismo para `math_types`.

4. **`lod_errors` y tipo de `resolution` se usan sin revalidar la definición.** Línea 56 usa `not od.lod_errors`. Si el lector real guarda una lista por LOD como `[None, None]`, es verdadera y todos los modelos caen a INCONCLUSIVE_PARSE con `incomplete_model`, dando un INCONCLUSIVE_CATALOG falso. Igual riesgo si `l.resolution` llega como `numpy.float32` o double: la comparación `resolution==od.resolutions[i]` y la clave de `ROLES` pueden fallar. Fix: leer la definición de `lod_errors` y `resolution` en `odol_reader.py` antes de la lectura de 120s y normalizar con `any(x for x in lod_errors)` o la forma real.

5. **Tests acoplados a interfaz y mensajes de helpers no mostrados.** Líneas 10, 37, 42, 68 del test. El fixture `section` expone `get_face_indices`, y los asserts exigen `Duplicate`, `Compressed` y `unassigned`. Si `sections()` usa `face_index_start`/`face_count` u otro atributo, el fixture no ejerce la ruta real y `test_bad_face_or_section_not_green` o el test analítico fallan o pasan por motivo equivocado. Fix: alinear el fixture con la firma real de `sections` y usar regex sobre los mensajes reales; no presumir PASS de la suite.

6. **LOD sin vértices se acepta en silencio.** Línea 30 devuelve `None` para listas vacías; `raw_box==decoded_box` es `None==None`. Un LOD vacío queda READ_STRICT con `bbox: null`. Consecuencia: un modelo degenerado parece completo. Fix: `require(vertices or not l.faces,'empty_lod')` y registrar `empty_lod=True` en el metadato.

**Observaciones menores**

- Línea 125: `mkdir(exist_ok=False)` sin `parents` y fuera del `try`; si falta el padre no hay `report.json`. Aceptable si el receptor lo documenta.
- Líneas 10-11 importan helpers antes de `check_pins` (105). El orden no es invertible sin reestructurar; basta documentar que el pin aborta antes de cualquier lectura del PBO.
- `verify_coverage` no exige `error` en INCONCLUSIVE_PARSE ni `measurement` en READ_STRICT. Añadir dos `require` baratos cierra el falso completo por fila malformada.
- Línea 130: si la excepción nace en `meter.dump(report.json)`, el segundo `dump` del `except` puede volver a fallar. Riesgo bajo.

**Lo que está bien y no hay que tocar**

Trailer sin semántica SHA1 (51-52), rechazo de MLOD y bytes no ODOL como INCONCLUSIVE_PARSE (94), `del data` y `del entries` para presupuesto (110, 116), `open('x')` con `fsync` por fila (113-114), roles como etiquetas de resolución (68, 79), y la negativa a reabrir B3E o producto. Presupuesto de memoria plausible: imagen de 318MB más payloads sin copiar la BytesIO, dentro de 2GiB.

Orden sugerido para el receptor: aplicar 1, 2, 3 y 6; confirmar 4 y 5 leyendo las definiciones pinned; correr la suite en paralelo; sólo entonces la lectura de 120s/2GiB.

FIN_REVISION