Provenance chain verified; writing the verdict now.

**Veredicto: SOUND-with-fixes.** El cambio mínimo es correcto y la evidencia del piloto es coherente. Hay un falso-PASS potencial en el test de integración que conviene cerrar antes del commit.

**Lo verificado**

- `tools/terrain/repair_guarded_shapes_ev112.py:44-47` solo valida la terna de retención. La rama `--retain-candidate` (70-88, 93-100, 149) no cambia. El modo por defecto sigue siendo `bounds`.
- El solver reportado en `report.json:69`, `receipt.json`, `inputs.json` y el intento fallido previo coinciden en `5f575db3…`. No hay versión nueva del solver.
- Cadena de dominios cerrada: `selected-discovery/domains.npz` tiene el mismo hash `5af81412…` que la inventario completa, y `audit_kit7_hybrid_all.py:21-23` rederiva free/shore/road contra ese fichero.
- El intento previo en modo `bounds` sobre el mismo grupo falló con `SOLVER_FAILED` (`kit7-guarded-rebase-1171-190-20261026/candidate/report.json:38-39`). El fixture reproduce ese fallo y el éxito híbrido con energías idénticas al piloto (`164.1296→161.8972`, solver `161.98782`), así que el fixture es el mismo slice que el piloto.
- Bury 0 cambios y huella exacta se afirman con `assert` en `merge_kit7_hybrid_relief.py:13-15`, no solo por JSON. Carreteras `current.status=PASS` con 0 fallos.
- El censo de formas no está: `validation.json` y los `*-shape-screen.json` no existen en el directorio del piloto. Coherente con lo declarado; no se da por pasado.

**Hallazgos**

1. **Falso-PASS posible en el test fresco.** `tests/test_guarded_retention_ev112.py:64` comprueba `witness_mode=='hybrid'`, pero ese campo se deriva directamente del flag en `repair_guarded_shapes_ev112.py:102,164`, no del solver. Si el paso `preserve_satisfied_witnesses=a.hybrid_witnesses` en la línea 118 se rompiera, el test seguiría pasando porque el caso sintético también resuelve en modo `bounds`. Fix: añadir `self.assertEqual(result['clusters'][0]['solve']['witnesses'],'hybrid')`.

2. **El fixture no asegura el recibo híbrido.** `tests/test_hybrid_witnesses_ev112.py:27` descarta el recibo. Fix: capturarlo y asertar `receipt['witnesses']=='hybrid'`, como ya hace la línea 57 para el otro fixture.

3. **Metadato huérfano.** `tests/fixtures/feasible-witness-1171-190.json:4` referencia `diagnostic_sha256` de un fichero fuera del repo (`diagnostic/linear-witness-only.npz`) que ningún test ni `source-hashes.json` verifica. Quitarlo o documentar la ruta en el JSON para que no parezca evidencia comprobada.

4. **Recibo de tests sin recuento.** `kit7-hybrid-rebase-tests-20261026/result.json` registra `returncode 0` y módulos, pero no el número de tests ni la salida. La cifra de 29 PASS no es verificable desde la evidencia. Fix: guardar stdout de unittest junto al recibo.

5. **Alcance del flag ampliado, sin guardia.** Con el flag fresco, el modo híbrido aplica a todos los clusters de la discovery, no solo al grupo omitido. Hoy está acotado porque la discovery seleccionada tiene un único grupo. No es regresión, pero conviene anotarlo en el plan: una futura ejecución sobre la inventario completa con `--hybrid-witnesses` cambiaría soluciones de clusters que ya pasaban en `bounds`.

**Criterios revisados y suficientes**

Guards locales (124-130) y globales (140-152) idénticos a los aceptados antes. La auditoría externa solo acota extremos protegidos con prominencia >0.3, pero `no_new_peak_failures` y `no_worsened_faults` cubren el resto en toda la rejilla.

**Límites de esta revisión**

- No pude ejecutar `git diff`; no confirmo que el único cambio sea la eliminación de la restricción. El hash anterior del autor era `f5bf8ac5…`, el actual `98311d57…`.
- No abrí los `.npz`; la equivalencia fixture-piloto se infiere por energías idénticas al float.
- El `baseline_sha256` del consumidor de carreteras (`07054c46…`) no es kit7 (`815ef8b7…`); sus 11 fallos cruzados son preexistentes y no atribuibles a esta unidad, pero el informe no identifica ese baseline.
- No reviso el prototipo MILP archivado, conforme a lo indicado.
- Esta unidad no acredita bosque, stage, binario, native, visual ni la navegación 607.

**Recomendación:** aplicar fixes 1 y 2 antes del commit; 3 y 4 son de higiene de evidencia. Esperar el censo antes de publicar la aceptación offline.
