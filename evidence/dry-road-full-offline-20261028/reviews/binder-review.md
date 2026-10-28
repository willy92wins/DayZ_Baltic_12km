Ya tengo todo lo necesario; redacto el veredicto.

**Veredicto: SOUND-with-fixes.** La capa de preparación, binder, gate y lifecycle reproduce el ciclo que funcionó nativamente en el run 1bb6c4f6 y falla cerrada en lo decisivo. No encontré ningún camino que produzca un PASS falso. Hay tres correcciones menores, ninguna cambia tolerancias ni elimina IDs.

**Lo que verifiqué y está bien**

- **Binder idéntico al probado.** `consume_dry_road_full_native_20261028.py:17-28` repite línea a línea las comprobaciones de `consume_buried_roadway_semantics_20261028.py:14-25`, que sí cerró el run 1bb6c4f6. La tolerancia de 1 µs entre `created_utc` de host y captura ya se demostró con datos reales de 7 decimales (`09:46:49.1686482Z` frente a `.1686480Z`, truncados a microsegundo por `fromisoformat`), así que no es un FAIL falso nuevo.
- **Separación de runs.** La fase probe exige calibración con `run_id` distinto, creación anterior, mismo engine y mismo conjunto de cuatro paquetes (`consume…:33-35`). El gate exige el hash de ese `result.json` como argumento (`check…:16-17`). El conjunto esperado se construye de forma idéntica en gate, consume y en el PowerShell de `finish…js:27` (3 PBO del mod nuevo + bridge, `$a.Count -ne 4`).
- **Identidad de misión y productor.** Copia de `init.c` fuente a misión nueva, `producer_sha256` de la fuente, y el host hashea `mission/init.c` (`capture_owned_server_identity.ps1:36`); coinciden. El CSV se regenera en consume y se compara byte a byte con el desplegado (`consume…:36-37`). El formato `id;x 0 z` es el que parsea `init.c:55,101`.
- **Captura.** Cabeceras y marcas de fin coinciden con los productores: `BALTIC_COLLISION_DIAGNOSTIC_V3`/`END;289` (`calibration/init.c:28,101`) y `BALTIC_VISUAL_PROBE_V3;BalticTrial`/`END;2658` (`init.c:46,171`). Nombres de log y `$profile` coinciden. Sólo proceso propio, StartTime ±2 ms, log posterior al arranque, `FAIL;*` aborta.
- **Presupuesto.** La cadencia nativa real fue ~104 ms/punto (result.json 1bb6c4f6, `time_ms`), lo que da ~280 s para 2658 puntos más 10 s de arranque: dentro de los 900 s. El lease caduca a 120 s sin llamadas (HANDOFF.md:69) y `finish…js:10` late antes de cada comando y cada 10 s dentro de `write_stdin`.
- **Preparador.** Exige adjudicación con pins antes de crear nada (`prepare…:21-23`), rechaza destinos existentes, verifica 1866 caras triangulares y contacto Roadway/Geometry error 0 desde el report sellado (`:28-30`), `bed_shapes` derivados de `face-info` excluyendo agua con el mismo formato `baltic_stream_pilot/…` que luego normaliza el consumidor (`dry_road_native_consumer_ev112.py:49`), y `foreign_dry_support` acotado al único modelo demostrado. Verifiqué que en points.json ese campo tiene exactamente ese literal (línea 26139).
- **5 puntos fuera de malla.** Id 2373 porta `outside_changed_model_after_roundtrip` y el consumidor lo hace INCONCLUSO en roadway, rv y bullet (`:33,46`), agua decisiva. Coherente con mi adjudicación anterior.
- **Gate y pruebas.** Los 8 controles del gate cubren drift de engine, log, deployment, hash de calibración ausente/erróneo y relanzamiento. Los 6 controles de lifecycle cubren adopción ajena, run ajeno visible, fallo de captura, fallo de cierre y proceso desaparecido, con exactamente un release y cero comandos cuando la adopción no es propia.

**Sobre la banda water_depth_numeric [-0.01, +0.02] en W−H**

Fundamento verificado: el productor mide profundidad en `ground+0.01` (`init.c:143`) y ground nativo se acepta en H±0.01. Para un punto wet con W−H ∈ (0, 0.02], la muestra cae en [H, H+0.02] y puede quedar por encima de W, dando depth ≤ 0 y FAIL falso aunque el lecho esté bien. El lado +0.02 está correctamente derivado. El lado −0.01 es conservador: para dry con W<H la muestra siempre queda ≥ H > W, así que no hay FAIL falso por aritmética; incluirlo sólo resta cobertura, no crea PASS. Acepto la clasificación como INCONCLUSA previa al motor. Correcto también que no toque el canal Roadway (`:33`). Nota honesta: en id 1769 Roadway no discrimina (W−H = 2.5 mm < 3 cm), pasará devuelva H o W; es cobertura no informativa, no evidencia.

**Fixes mínimos antes de preparar**

1. **Conteo exacto no registrado.** El plan (línea 84) exige registrar al preparar cuántos IDs reciben `water_depth_numeric` y el total de inciertos. `prepare…:61` no incluye ningún conteo en `deployment.json`; sólo quedan embebidos en points.json. Añadir al `doc` un contador por etiqueta de `uncertain` y el total de IDs con alguna etiqueta. Sin esto la cifra "21" del contrato queda sin sello.
2. **Clave de lanzamiento compartida entre fases.** `finish…js:6` lee `dryRoadFullLaunch` y `:13` escribe `launch.json` antes de verificar la adopción. Si el store conserva el run de calibración cuando se ejecuta la fase probe, se escribe `probe/launch.json` con el run_id ajeno; la adopción fallaría y consume lo rechazaría (`run_binding`, `calibration_order`), así que no hay PASS falso, pero el gate quedaría bloqueado por `unit_already_launched` y habría que intervenir a mano. Usar clave por fase (`'dryRoadFullLaunch_'+mode`) y limpiarla al terminar.
3. **Restos tras fallo del preparador.** Si falla después de `prepare…:51` o `:56`, quedan el mod, las misiones y `failure.json` dentro de O; el siguiente intento muere en `fresh_targets_required` (`:12`). Es fail-closed, pero debe constar en el procedimiento que el operador retira esos restos antes de reintentar, sin reutilizar nada de ellos.

**Observaciones que no bloquean**

- `accepted.json` y el JSON de adjudicación son documentos manuales; el preparador y el gate exigen que pinen deployment/prelaunch/points y, en el caso de la adjudicación, los hashes de las entradas. La adjudicación debería pinar también esta revisión y sus `completion.json`, como se hizo en el run de 16.
- El gate sólo detecta relanzamiento si `finish` llegó a escribir `launch.json`. Un lanzamiento MCP sin `finish` posterior no deja rastro en O. Acepto el riesgo porque el binder posterior exige misión, paquetes y run propio, pero conviene decirlo.
- Sigue sin evidencia nativa de puntos wet (152) ni de `SurfaceIsPond` sobre caras water_ext; un FAIL ahí será FAIL honesto, no reinterpretable. Ya consta en la revisión anterior.
- Fixture 16 + 7 negativos con calibración histórica: sólo regresión de código. Correcto que ningún script la acepte como calibración fresca (`consume…:33-35` exige run propio).

**Lo que no apruebo:** lanzamiento, Global, piloto entero, tolerancias nuevas, visual, RAM, c1/7970ae67. Esta revisión cubre únicamente preparación, binder, gate y lifecycle.

FIN_REVISION