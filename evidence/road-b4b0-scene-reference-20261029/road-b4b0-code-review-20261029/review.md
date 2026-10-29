Revisión estática de los cuatro archivos, sin ejecutar ni editar.

**Identidad:** Claude Fable 5.1 (`claude-fable-5-1`), revisor read-only.

**Veredicto: NEEDS-WORK.** El camino positivo de la suite no puede pasar tal como está escrito, el consumidor es una copia del productor y varios campos del contrato externo son opcionales en la práctica. El fixture literal existe pero no se usa.

## Bugs concretos

**1. El test positivo no puede pasar: las claves de pines B4A3 no casan con el parser.**
Productor `road_scene_reference_index_ev112.py:285` y consumidor `verify_road_scene_reference_index_ev112.py:255` detectan pines de activo buscando la subcadena `/assets/` en las claves de `sources`. El fixture (`tests/test_road_scene_reference_index_ev112.py:54`) usa claves `previous:assets/dz/c.p3d`, que no contienen esa subcadena. Resultado: `asset_pins` queda vacío, `dz/c.p3d` cae a `PROVIDER_RESOLVED`, se emite `NEW_REFERENCE_STATE`, el productor devuelve 2 y `test_positive_producer_then_consumer` falla en la línea 67. Impacto: o la suite está roja, o el formato de clave real del contrato 178c difiere del fixture y nadie lo verificó. Fix: no inferir pines por subcadena; leer el esquema real de B4A3 con nombre de campo explícito y añadir un test negativo que compruebe el código `NEW_REFERENCE_WITH_B4A3_PIN` por nombre.

**2. Las pruebas negativas son vacuas.**
Línea 72 sólo exige `returncode==2` y `status!=OK`. Con el bug 1, todas las variantes fallarían por la misma causa ajena y el test seguiría en verde. Fix: afirmar el código de issue o el detalle FATAL esperado por variante (por ejemplo `duplicate object id`, `objects cap`, `CATALOG_COUNTS`).

**3. El fixture literal no se consume.**
`tests/fixtures/road_b4b0/literal.json` es correcto (header 46 bytes, 3 registros de 64, terminador 56, 294 y 486 bytes), pero ningún test lo carga. Los fixtures se generan con `_prefix()`/`_rec()` (líneas 11 a 12), es decir, con código propio, y las expectativas del candidato salen del mismo generador. El plan línea 46 pide consumidor negativo contra referente literal. Fix: construir source/candidate a partir de los hex del literal y comprobar `counts`, `expected_candidate_counts` y bytes contra ese JSON.

**4. El consumidor no es independiente, es un clon.**
Líneas 117 a 200 del consumidor reproducen `_Cur`, `_objects_begin`, `valid_name`, `norm`, `scan_source` y `scan_candidate` del productor casi byte a byte. No hay import, pero cualquier error compartido (offset 48 de id/nlen, salto de alturas, regla de nombre) pasa ambos. La línea 329 compara dos salidas de la misma lógica. Además las copias ya divergen en detalle: el productor emite `B2A_PACKAGE_DUPLICATE` (253), `CATALOG_NAME` (266) y `B2A_PACKAGE_MISSING` (313); el consumidor no. Si se dispara alguno, la comparación semántica falla con FATAL en vez de `VERIFIED_MISMATCH_DIAGNOSTIC`. Fix mínimo: igualar los conjuntos de issues y documentar que la independencia es de proceso, no de implementación. Fix real: que el consumidor use una estrategia distinta (por ejemplo recorrido por offsets absolutos derivados del literal y comparación de nombres contra el catálogo sin pasar por `valid_name`).

**5. Campos del B3 report y B2A report son opcionales.**
Productor 245 y consumidor 225: `if field in b3r and ...`. Un `b3_report` igual a `{}` pasa todas las comprobaciones. Lo mismo en 274 y 275 para `scene_instances` y `scene_models`, que el plan fija en 2578398 y 5509. Y `pin_map` (257 a 260) sólo verifica paquetes presentes en ambos lados; un paquete B2A sin pin en config pasa. Impacto: el consumidor "verifica todos pins" (F2) sólo nominalmente. Fix: definir la lista de campos obligatorios según el esquema real de cada artefacto y emitir issue por ausencia, no sólo por discrepancia. Para paquetes, exigir pin en config para todo paquete usado por un proveedor.

**6. Semántica incoherente para un nombre histórico con instancia añadida.**
Líneas 330 a 332: si un nombre está en `counts` y en `added_names`, sólo evita `NEW_REFERENCE_STATE` si se etiqueta `NEW_REFERENCE_WITH_B4A3_PIN`. El plan (F3) reserva esa etiqueta a referencias fuera de B2A. Fix: decidir estado por `v in counts`; para históricos con delta, `PROVIDER_RESOLVED` más campo de delta explícito.

**7. Join de proveedores O(N·M) y presupuesto del consumidor.**
`b2a_provider` (310) recorre todos los modelos por cada nombre: unos 5512 × 5509 llamadas a `norm`, más de 30 millones. El consumidor repite además el escaneo completo (hash, recorrido, hash de dos ficheros de 286 MB). No está medido, pero el presupuesto de 60 s para el consumidor es dudoso con este diseño. Fix: indexar `models` por nombre normalizado una sola vez; detectar colisiones de nombre normalizado con bytes raw distintos en ese paso.

**8. Lectura sin cap en el consumidor.**
`_validate_report` línea 304 a 305 abre `tool['path']` tomado del reporte y hace `tf.read()` completo sin límite de tamaño ni comprobación de que el path esté bajo el repositorio. Fix: cap antes de leer y comparar con una ruta esperada.

**9. Código muerto y comprobación de tamaño eliminada.**
Productor 149: `if exp_size ... : pass`. El tamaño del WRP frente al pin sólo se comprueba tras el escaneo completo (229). Productor 353 a 354: bucle vacío. Fix: rechazar o al menos registrar antes del escaneo; borrar el bucle.

**10. Splitlines en JSONL.**
Productor 217 y consumidor 207 usan `splitlines()`, que corta también en U+2028, U+0085 y otros. Fix: `split('\n')`.

## Lo que sí está bien

- Caps antes de alloc: nombre (171), objetos (170), referencias (173), material count (139), JSON total (211), reporte (343). El consumidor inserta antes de comprobar referencias (171) pero sin efecto práctico.
- Snapshots: identidad de handle incluye ctime, identidad de path la excluye; coherente con el test de unidades (línea 84). El consumidor no cruza su propio stat con el del productor, sólo coherencia interna; el SHA cubre contenido.
- Escritura exclusiva `xb`, rechazo de BOM, claves duplicadas y no finitos.
- `norm` copia literal la definición B2A; se rechazan slash exterior, drive, traversal y no ASCII. Es más estricto que el plan F1 y debería documentarse.
- Alcance de unicidad de IDs declarado en `CLAIMS` tal como pide F2.

## Siguiente paso

Corregir 1, 2, 3 y 5 antes de cualquier captura; 4 y 7 condicionan si el consumidor puede llamarse independiente dentro de 60 s. No evalué precedencia, materiales ni geometría, fuera de alcance.