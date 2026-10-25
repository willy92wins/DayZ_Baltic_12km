# EV93 fairing-layer1 — revisión independiente v1

**Veredicto:** NEEDS WORK antes de autorizar `--prepare`/`--execute`. Esta revisión se ancla al `author.py` SHA256 `8d4a6cd00a38e8cd042742d5afd0275b8467a8731b81fc61fc7af939ba015076`, `test_author.py` `e2145db7caa8fc7ba11fd2f801429029993f219f339e7bd5186373cd21916c2e`, README `f3f0ee315ccadd756a3a57b33a3bed5cc098d34b68e3955bf7888bbfe96b084d` y plan `author-stage-plan.md` SHA256 `2bc641c0ec88954e83a2d10f5a2542357ac8cdc6533456b466e4e71f90df504c`.

## Hallazgos bloqueantes

1. **La reanudación no reconcilia los resultados persistidos con el ledger.** En `author.py:367-372`, un resultado JSON existente se acepta verificando sus identificadores/estado y, si es `accepted`, el hash del delta; no se coteja con `result_sha256` de `ledger.jsonl`. La escritura ocurre primero en `atomic_json(result_path, ...)` y luego en `append_jsonl(...)` (`:407`). Una interrupción entre ambas deja un resultado sin evento; la siguiente ejecución lo omite y puede componerlo. También una edición del resultado tras un evento no se detecta. **Corrección:** antes de reanudar, reconstruir y verificar la correspondencia bidireccional de cada resultado con exactamente un evento ledger cuyo SHA, qid y estado coincidan; ante fila huérfana o discrepante, fallar cerrado sin componer.

2. **Una invocación después de finalizar puede volver a publicar y sobrescribir la salida.** Si los 703 resultados ya existen, `execute()` los omite y vuelve a componer/escribir `candidate-terrain.npz`, `authoring.json` y un evento final (`:409-430`). No exige que no haya un recibo terminal ni preserva por hash el candidato final anterior. Esto permite que una repetición accidental reemplace artefactos terminales; aunque las alturas sean iguales, la serialización NPZ puede cambiar sus bytes. **Corrección:** hacer terminal el estado final: detectar un final/recibo/candidato ya publicado y rechazar la segunda ejecución sin escrituras, o verificar y devolverlo sin reemplazar nada.

3. **Los JSON de ventana y el read-set no se revalidan al ejecutar.** `prepared_manifest()` almacena `detail_sha256` por entrada y valida el read-set al preparar (`:162-180`), pero `execute()` valida el ledger, base y `PINS` (`:355-363`) sin revalidar las entradas de `preflight_header.read_set_sha256`. Luego `reconstruct()` lee `detail_path` directamente (`:230-238`) sin comparar sus bytes con `entry.detail_sha256`. Por tanto, cambiar un detalle después de crear el manifiesto aprobado cambia las cotas/dominio consumidos, sin cambiar el SHA del ledger ni del manifiesto. **Corrección:** verificar el SHA exacto de cada detalle antes de reconstruirlo y revalidar el read-set fijado por el header antes del primer solve y antes de publicar el compuesto; si cambia, dejar ejecución incompleta y no componer.

## Lo que sí quedó comprobado

- Hashes actuales coincidieron con los cuatro anclajes anteriores.
- GIS Python `py_compile` implícito por import y `python -m unittest -v test_author.py`: **11/11 PASS** en 4.776 s. Incluyen reconstrucción de q0000, ledger reanudado 703, normalización de coordenadas, serialización de stencils, composición con propietario único/solape negativo, cast float64→float32 y un test de la ruta real `EV91.solve_once` bajo `multiprocessing spawn` de Windows con el módulo canónico fijado.
- El código revisado usa el centro de cada ventana para `scalar_rule`, vuelve a validar cotas/guard/D8 después del cast final, conserva collar y clasifica rechazo geométrico separado de error/timeout. No vi uso accidental de los gates legacy no-raise/half-sign de EV87.
- No ejecuté `--prepare`, `--execute` ni solver de producción; el fixture de spawn fue el único solve y usa una matriz analítica de dos variables.

Las pruebas actuales no ejercitan las tres condiciones de integridad anteriores. La aprobación de la fuente corregida requiere revisar solo esos cambios y sus fixtures de mutación/interrupción, manteniendo los gates geométricos y el plan intactos.
## Revalidación focal del freeze final

**Veredicto actual:** SOUND para autorizar `--prepare` y el segmento de `--execute`, limitado a la autoría offline bajo el plan fijado. Esta revalidación sustituye el veredicto NEEDS WORK de v1 solo para los tres hallazgos de integridad enumerados arriba; conserva v1 como historial. No implica aceptación geométrica/global ni ejecución productiva.

Anclajes actuales: `author.py` SHA256 `4b25ced7b853b29d7fbfe902954a07a661f4722367a2ce67fff249d035a3a0ef`; `test_author.py` `17c628c71fb4a383631a405818b81a2bee7b5b780d3c8caa863cd5943eb2c367`; README `e5952eb7b83bc5d7ff77ba14ce266bcd4986e40942631a0a71ff70d5547d1e29`.

- El lock exclusivo se adquiere antes de la recuperación/reconciliación (`author.py:480-483`); la comprobación terminal se repite dentro del lock y la recuperación corre bajo ese mismo lock. Así, dos ejecuciones no pueden reparar/escribir simultáneamente.
- `assert_not_terminal` rechaza recibos y eventos finales terminales. La ruta de ejecución comprueba antes de entrar y de nuevo dentro del lock (`:478-483`); también rechaza sobrescribir un candidato preexistente sin recibo terminal (`:550-551`).
- El read-set preparado se valida al comienzo y antes de composición; cada detalle de ventana se verifica contra su SHA antes de reconstrucción y de solve (`:479`, `:498-507`, `:550`). No hay rehash del read-set completo por ventana.
- La reconciliación de reanudación exige correspondencia uno-a-uno de JSON de resultado y evento ledger, con qid/estado/ruta/SHA, y valida los artefactos de solución/delta (`:367-433`).

Verificación actual con GIS Python: `py_compile author.py test_author.py` PASS; `python -m unittest -q test_author` **16/16 PASS** (5.350 s). Incluye mutaciones de ledger/artefactos/read-set/detalle, terminalidad y lock ocupado. El test de lock comprueba que la recuperación no deja escrituras mientras el lock está ocupado; la garantía de orden en la ruta real se confirma además por `execute()` en `:480-483`.

No se ejecutaron `--prepare`, `--execute` ni solver productivo en esta revisión. El siguiente paso autorizado puede iniciar preparación y el segmento conforme al manifiesto; su resultado seguirá pendiente del consumidor geométrico global.
