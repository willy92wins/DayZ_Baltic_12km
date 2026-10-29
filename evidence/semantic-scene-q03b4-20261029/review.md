Identidad servida: Claude Fable 5.1 (`claude-fable-5-1`). Revisión de sólo lectura sobre los bytes congelados; no ejecuté nada ni abrí NPZ.

**Dictamen: NEEDS-WORK.** Bloquear la captura de los 204 NPZ históricos hasta suite verde por delta. La implementación es en gran parte correcta y el consumidor relee de verdad las fuentes, pero hay un crash que invalida todo PASS del consumidor, una discrepancia oráculo/test en códigos, y tres huecos de completitud del conjunto cerrado.

## Hallazgos bloqueantes

**H1. Crash del consumidor por sombra de variable.** `saved_scene_consumer_q03b4.py:133` asigna `cat='CAP_START' ...` dentro del bucle de triángulos. Esa variable es el catálogo dict creado en la línea 78. Al salir del bucle de pilotos, la línea 137 llama `cat.items()` sobre un `str` y la 139 `cat.get(mi)`. Consecuencia: todo consumo con al menos un piloto termina en INTERNAL_ERROR, nunca en VERIFIED. Esto explica los 2 FAIL y 1 ERROR (test literal CLI, N18 positivo). Corrección acotada: renombrar la variable local de la línea 133 (por ejemplo `label_cat`) y la lista `cats`. Tras leer el resto del recorrido no veo otro impedimento para que el test literal y N18 pasen, pero esa afirmación es de lectura, no de ejecución: la suite por delta debe confirmarlo.

**H2. Correspondencia oráculo/test rota en N11.** `oracle.json:395` fija N11 = `SCHEMA`. El test `test_saved_scene_q03b4.py:103` exige `MEMBER_SCHEMA` para miembro extra, que es lo que realmente emite `_central` sellado (archive:160) a través de `Reader.open` (io:89). El código producido es correcto; el oráculo nombra un predicado distinto. Corrección: cambiar el literal N11 del oráculo a `MEMBER_SCHEMA` para el miembro extra y conservar `SCHEMA` para el descriptor META (ese sub-caso se cubre sólo implícitamente por la comparación de `meta` con `M`/`META`, sin test negativo propio). Esto obliga a repinar `oracle_sha256` en contract.json; es un cambio de oráculo, no de código, y debe registrarse como tal.

## Hallazgos de completitud del contrato (no bloquean individualmente, sí en conjunto)

**H3. Categorías con caps nunca ejercidas.** Todas las fixtures usan `cap_before=cap_after=0` y `cap_rows=[]`. Las fórmulas de CAP_START/CAP_END en productor:90-91 y consumidor:133 son idénticas e inferidas; ningún oráculo literal las fija. N09 (test:112-115) rechaza por "cualquier etiqueta no BODY", no por permutación conservando cuentas. Si la convención histórica de caps difiere (por ejemplo `<= before-1` o `>= n-after`), la captura real rechazaría con CATEGORY a los 201 pilotos o, peor, aceptaría un corte incorrecto si ambas implementaciones comparten el mismo error. Corrección: añadir un oráculo literal con `cap_before=8` en grilla 10xM y categorías escritas a mano, más un negativo que intercambie dos filas BODY/CAP conservando `source_regions`.

**H4. Alternativa mixta selected/instances sin negativo.** F4 exige que selected e instances usen la misma alternativa exacta. La guarda existe (productor:136 por descriptor, consumidor:116 por digest), pero N18 sólo cubre combinaciones positivas y liga `ttype` a `ftype`, así que `<i4` con `<f8` y `<i8` con `<f4` nunca se prueban, ni `<i4` ids en selected contra `<i8` en instances. Corrección: una fixture con `mutate` que recodifique `selected.ids` a otra alternativa, esperando POSE en ambos caminantes, y desacoplar `ttype`.

**H5. N01 es un mock, no una mutación de bytes.** `test:75-80` parchea `Session._prepare` para devolver otro SHA. Verifica la guarda io:100, pero no que una sustitución real del archivo entre la fase de cabeceras y `session.open` produzca SOURCE_CHANGED con la Session sellada. Corrección: invocar `predicate` con una función que reescriba el NPZ en disco (mismo nombre, bytes distintos) y comprobar SOURCE_CHANGED. Tal como está, es un rechazo anterior que no prueba la guarda objetivo con bytes.

**H6. N05 y N15 cubren casos más débiles que su enunciado.** N05 cambia `lod` a un índice inexistente (FACE por ausencia), no "LOD/section confundido con posición"; N15 duplica un spec de array, no omite un pin. Ambos pasan por caminos reales, pero no por el predicado nombrado. Corrección mínima: N05 con `section` existente en otro LOD del mismo modelo, N15 eliminando una entrada de `pilot_manifest` (espera EPOCH en productor:104 y consumidor:74).

## Verificado como correcto (sin cambio)

- Adaptador: `io:57-73` lee sólo magic/versión/longitud/cabecera con cap 16384 antes del diccionario, rechaza objeto/subarray/Fortran, comprueba extensión contra longitud declarada, y `inspect_header` sellado confirma después del predicado (io:97). Orden F1/F2 respetado: probe Session sólo para `_snapshot`, comprobación de remanente por lectura de campos (io:91) sin escribir en la Session autoritativa, buffer liberado antes de `session.open` (io:98), SHA de inspección igual al pin y al de carga (io:100). Pilot con exactamente 35 miembros toca el cap `members` sin excederlo.
- Runs: productor:125-127 produce runs máximos; consumidor:98-107 verifica fila a fila, clave por fila, cobertura exhaustiva y disjunta, y maximalidad por `key!=last`. Esto cubre N08 real.
- Consumidor independiente: no importa productor, recorre catálogo/secciones/rutas con sus propios validadores, compara `pose_rows`, `layers`, `arraydigestmap`, `sources` y `coverage` por igualdad exacta con `IO.exact` (bool != int, claves desconocidas rechazadas). N12/N13 cubiertos.
- N14: TOTAL_CAP se lanza en io:91 antes de ZipFile y de cualquier `read_array`; el parche de `read_array` no se alcanza.
- Rutas proxy: ambos caminantes validan continuidad, profundidad <=16, ausencia de ciclos, hijo final y literal normalizado, sin basename.
- Poses: unicidad de IDs, cuentas por índice contra catálogo no vegetación, un piloto a una fila exacta, sin atribución por proximidad. Referencia temporal de `ids/indices` copiada y explicitada (consumidor:111).
- Salida y fallo: `mkdir(exist_ok=False)`, `failure.json` con código distinto de INTERNAL_ERROR para rechazos y re-raise.

## Observación menor, sin corrección exigida

`coverage` del informe (productor:157) es `dict(e, ...)`: copia las expectativas del contrato más dos cuentas observadas. Todos los valores numéricos están gateados por R antes, pero `human_resolved` y `C1` son eco, no observación. Aceptable como literal de contrato; conviene declararlo en `limitations`.

## Resumen operativo

- NEEDS-WORK. No autorizar lectura de NPZ históricos.
- La única corrección de 240s debe cubrir H1 (rename) y H2 (oráculo + repin). Son dos archivos, cambio trivial.
- H3 a H6 son completitud del conjunto cerrado; sin ellos un verde posterior sigue sin probar caps ni alternativa mixta, que son precisamente las clases variables que motivaron Q03B4. Si el presupuesto no admite añadirlos, el estado debe quedar explícitamente como "índice no apto para captura" en lugar de reducir el contrato.
- No asumir que H1 arreglado produce aceptación: ejecutar la suite completa por delta y confirmar los 11 métodos verdes antes de reconsiderar.
