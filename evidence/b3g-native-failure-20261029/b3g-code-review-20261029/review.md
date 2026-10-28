**Veredicto: SOUND-with-fixes.** No encuentro falsos PASS en el consumidor ni en el binding; los tres fixes del plan (F1 contrato íntegro, F2 adaptador con hashes y W exactas, F3 reloj de agua tras t1) están implementados y son consistentes con init.c. Hay cuatro defectos concretos con repro y tres huecos de sellado que conviene cerrar antes de la suite final.

**Bugs con repro**

1. **Hash "raw" del adaptador no es el del archivo** (`contact_pair_b3g_ev112.py:51`, `contact_pair_b3g_binding_ev112.py:75`). El texto llega vía `read_text(encoding='utf-8-sig')`, que elimina BOM y traduce CRLF a LF. `raw_sha256` se calcula sobre ese texto normalizado, mientras `log_binding` (binding:65) y `inputs` usan el SHA de bytes del archivo. Repro: escribir el fixture con `newline='\r\n'`, leerlo igual que consume_bound, y comparar `adapter.raw_sha256` con `sha(native.log)`: difieren. El recibo afirma "raw" pero no permite reproducir el hash del log capturado. Fix: calcular `raw_sha256` sobre bytes, o renombrar a `normalized_text_sha256` y registrar el SHA de bytes junto a él.

2. **El contrato no liga x/z del original al punto fijado** (`contact_pair_b3g_ev112.py:18-31`, 86). `contract()` exige `e['id']==p['id']` pero no `f32(e['x'])==p['x']`. `origins()` valida posición contra `p`; el canal RV valida XZ contra `e`. Repro: en `test_contact_pair_b3g_ev112.py` copiar el original, hacer `o['rows'][349]['expected']['x']+=5`, consumir: el contrato pasa, `ground` PASS, `rv_low` cae a FAIL por `RV_height_identity_or_ray_position`. Es un falso FAIL imputado a geometría cuando la causa es un contrato incoherente. Fix: añadir `require(f32(e['x'])==p['x'] and f32(e['z'])==p['z'],'expectation_position')` y test.

3. **test_miss_payload_not_contact es vacuo** (`test_contact_pair_b3g_ev112.py:66-67`). `test_complete_is_not_acceptance` fija `rv_high={'FAIL':30}` en baseline; mutar `R;…;RH` a `false` y afirmar `rv_high=='FAIL'` no distingue miss de la FAIL preexistente. Repro: quitar la mutación y la aserción sigue pasando. Fix: mutar la fila `RL` (baseline PASS) y afirmar FAIL, además de `contact_height is None`.

4. **Presupuesto de captura inconsistente** (`capture_contact_b3g_log.ps1:15,35`). El script rechaza cualquier `DeadlineUtc` más allá de 180 s, el plan dice 180 s y el brief operativo dice captura 300 s. Si el coordinador pasa 300 s, el script lanza `Capture budget above180s` y el brazo de control muere antes de medir, sin segundo brazo por diseño. Fix: fijar un único valor en plan, brief y script (y en `launch.json`).

**Consistencia reloj/snapshot**

Correcta. init.c:165-186,214 produce t0≤t1≤waterStart≤waterEnd≤t2 en ese orden; `parse` (49) lo exige y `consume` (102-104) convierte cualquier cambio en confusor, nunca en prueba. `round_snapshot_drift` y `pair_snapshot_drift` conservan objetos completos. `test_water_clock_does_not_change_ray_clock` cubre F3. El único punto suelto es la tolerancia de creación de proceso: PowerShell acepta 2 ms (identity.ps1:13, log.ps1:18) y Python 1 ms (binding:48). Un drift de 1,5 ms produce recibos válidos que el binding rechaza; unificar a 1 ms en ambos lados.

**Aceptación y hashes**

- `files()`/`identity()`/`pair_bound` ligan motor, scripts, mod efectivo por ruta de paquete, vanilla, misión y CSV; la intervención única se verifica en binding:88. Bien.
- Hueco de sellado: `prepare_contact_b3g_ev112.py:23` no incluye `capture_contact_b3g_identity.ps1` ni `capture_contact_b3g_log.ps1` en `required`, y `deployment.inputs` tampoco los pina. Los scripts que generan los recibos quedan fuera del SHA de aprobación. Fix: añadirlos a `required` y a `input_pins`.
- `launch.json` sólo se valida por `status` y `run_id` (binding:39-42,72). Ninguna comprobación de `takeover:false`, `on_busy:queue`, modo server o misión solicitada. El plan los exige; o se pinan aquí o se documenta que el recibo MCP los cubre.
- `log-capture.count` es constante 270 (log.ps1:27), no contado; inocuo porque `parse` recuenta, pero el recibo no debería afirmar lo que no midió.

**Preparación**

- `prepare` llama a `b.gate` tras crear ROOT, MISSION y los dos `@DayZ_Baltic_B3G_*`. Si `gate` falla (por ejemplo `unlisted_pbo` por la carpeta heredada de `dayz_mcp.pbo`, línea 41 conserva la ruta B2 sin verificar que esa carpeta contenga sólo el bridge), el reintento muere en `fresh_destinations`. Documentar limpieza manual o validar `files()` sobre un dict en memoria antes de escribir.
- El filtro `vanilla` (36) depende de que `static_packages` de B2 tenga los cinco nombres; si falta uno, falla más tarde en `vanilla_names`. Aceptable, pero el error llega tras haber copiado paquetes.

**No verificable aquí**

Formato de booleanos en Enforce (`"" + bool`) y la aceptación de líneas `BEGIN`/`LINK` por `wire.parse` dependen del helper B2 no adjunto; asumo paridad con la captura nativa B2 documentada.

**Resumen de fixes antes de suite final:** (1) SHA de bytes en adaptador, (2) ligar x/z del original, (3) test de miss sobre RL, (4) unificar 180/300 s, (5) pinar los dos .ps1 en aprobación y deployment, (6) tolerancia 1 ms unificada, (7) validar flags de `launch.json` o documentar quién los cubre. Ninguno exige recompilar, modificar helpers sellados ni repetir B2.

FIN_REVISION