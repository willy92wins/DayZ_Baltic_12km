**Veredicto: SOUND.** La adaptación del postprocess 8m es una sustitución mecánica correcta de rutas, hashes y grid; no encontré aceptación de NM viejo, retarget accidental ni regresión introducida. No hay fixes obligatorios antes de crear `accepted.json`.

**Comparación verificada**

- `package_and_deploy_kit7_nav8.py` vs `nav9`: cambian solo L7 (dirs 8m), L11 (BASE `Kit7Nav8Input`, DEST `Kit7Nav8`), L21-22 (review/consumer 8m), L32-35, L59, L61-62, L65, L73-77. Resto byte-idéntico en lógica.
- `finish_kit7_nav8_probe.py` vs original: solo L9 (consumer dir) y L27 (mcp-after de la preparación 8m). Idéntico en todo lo demás.
- `orchestrate_kit7_nav8_probe.js` vs original: solo L3 (dir, misión `BalticKit7Nav8`, log con UUID `8adc6fd2…`), L8 (review 8m), L9 (`@DayZ_Baltic_EV112_Kit7Nav8`), L11/L14/L16 (claves store), L48 (finish 8m). Sin restos de `20261026`, `NavV9`, `Kit7Overlap`, `983`, `12.5`, `eb0f…`, `10e09…`, `57c47974` en los tres archivos ni en los tests cjs.

**Puntos de riesgo pedidos, cada uno cerrado**

- **Paquete de entrada correcto**: L59 y L65 pinean `narva_trial.pbo`=`9fbc…`; `package-kit7-nav8-input-20261027/verification.json` confirma que ese PBO contiene NM `13e1ab…` (el kit7 12.5m, igual a `navmesh-kit7-v9-20261026/generation.json:33`), WRP `0da63d…`, solo `config.bin` cambiado, 6826 entradas conservadas. `attach_navmesh.py:85` rechaza si el NM existente no es exactamente `13e1ab…`; L64 exige 6826 inalteradas y `replaced_entry`.
- **No acepta NM viejo**: L60 y L65 atan el NM empaquetado a `gen['navmesh_sha256']` de la generación 8m; inspector L61 exige grid 1536×1536 y tile 8.0 (`inspect_navmesh_v9_ev112.py:23,26` fallan con 983/12.5).
- **UUID desconocido**: L33 valida formato UUID canónico; L34 exige igualdad gen/host/completion/close; L46 y L51 vuelven a atar observer, timeline y mcp-before/after al mismo run_id. Equivalente al pin fijo de nav9 sin hardcode.
- **Identidad de generador y stack**: L58 pinea el exe `66935…` (es lo que `generate_navmesh_console.py:50` escribe); el wrapper modificado queda pineado vía `launch-inputs.json` inputs (`701446…`), re-hasheado en L56. L56-57 re-hashean los PBO de `Kit7Nav8Input` antes de copiarlos en L68-71, así que pilot/water copiados están verificados.
- **Freeze y cierre**: L21 impide reutilizar O/DEST/deployment; L22-25 exigen `accepted.json` con el propio script y `verify_c_orderly_close.py` (ambos en `source-hashes.json`). `orchestrate…probe.js:8` re-verifica todos los inputs del accepted y del deployment antes de lanzar.
- **Fallo de altura preservado**: `verify_kit7_nav_ev112.py:85,108,110` escribe `FAIL_KIT7_NATIVE_GRAPH` y sale 1; `finish:45` eleva `SystemExit`; `orchestrate:50` lanza error. Ningún camino convierte FAIL/INCONCLUSIVE en PASS. Tolerancia `.801` sigue exigida en L36 del verificador.
- **Contrato 607**: `contract-parity.json` y `frozen.json` muestran `queries.csv` idéntico (`305e80…`) y solo `probe_id/header/log_name` cambiados; `finish:25-26` exige 607 y nombre de log congelado.

**Observaciones no bloqueantes**

1. `kit7-nav8-postprocess-review-20261027/source-hashes.json` no incluye `nav-kit7-8m-preparation-20261027/launch-inputs.json`. El paquete lo valida por contenido (L35, L56-59), así que no es hueco real; añadir su hash a `accepted.json` costaría una línea y cerraría edición posterior del receipt.
2. Los archivos del worktree pineados (`inspect_navmesh_v9_ev112.py` `200a9a…`, `observe_owned_server_exit.ps1` `8b1707…`, `generate_navmesh_console.py` `701446…`) están sin commitear. El push validado debe commitear exactamente esos bytes; cualquier retoque posterior invalidará accepted/frozen y bloqueará paquete y probe, que es el comportamiento deseado.
3. `test_kit7_nav8_consumer.py` y los controles de coordinador son sintéticos; coincido con que no son evidencia nativa y no deben entrar en ninguna afirmación de aceptación.

**Estado**: listo para crear `accepted.json` con los 13 hashes listados (opcionalmente más `launch-inputs.json`). Paquete y probe siguen esperando la generación 8m en FIFO; nada aquí autoriza reclamar actores, FPS, RAM ni verdicto global.
