Tengo todo lo necesario; redacto el dictamen.

**Dictamen: SOUND-with-fixes. El bloque diagnóstico puede comenzar** una vez creado accepted.json con las condiciones indicadas abajo. No encontré bypass de aceptación ni referencia antigua a Nav12 en la cadena operativa.

**Diferencia lógica real frente a los corredores Nav12 (verificada línea a línea)**

- `prepare_navv9diag_ram_pass.py:15-19` sustituye las tres comprobaciones de PASS nativo de `prepare_nav12_ram_pass.py:15-18` por `validate_diagnostic` sobre el result.json original y el deployment.json diagnóstico. Las pruebas de proofs pasan a incluir el gate y el deployment propio. Estado `BOUND_DIAGNOSTIC_ONLY_HEIGHT_FAIL` exigido simétricamente en `finish_navv9diag_ram_pass.py:14`.
- `orchestrate_navv9diag_ram.js` solo cambia nombres, regex de misión y el mod `@DayZ_Baltic_EV112_Kit7NavV9` (línea 12). Las fronteras se conservan idénticas a Nav12: on_busy queue, 600 s, takeover false, navmesh_data_server false, sin session_status antes del lanzamiento, lease propio tras run propio (línea 19), espera BOUND (línea 21), sampler antes del hash pesado (líneas 24 y 33), close propio y release en finally (líneas 40-42), rechazo de adopción forzada en beat (línea 17).
- `finalize_navv9diag_ram_ab.py:42-44` añade acceptance_eligible=False, scope diagnóstico y el hash histórico. El resto es idéntico.
- Sin generación, cliente ni cambio de consultas. Nav12 sellado no se toca: el setup solo escribe archivos con prefijo navv9diag y restaura PBO en la carpeta NavV9 con `open('xb')` y rechazo de destino distinto (`setup_navv9diag_ram.py:38-42`).

**Gate navv9diag_gate.py comprobado contra los datos reales**

- result.json original: status FAIL_KIT7_NATIVE_GRAPH (línea 2), height_issues con exactamente los cuatro nombres esperados (líneas 10935-10940), local_failures vacío (línea 21940). El hash e086af… coincide en gate, deployment.json y finalize.
- deployment.json: cuatro paquetes con los mismos hashes que `kit7-nav-consumer-20261026/deployment.json`, rutas P:\Mods, acceptance_eligible false. La forma P:\Mods coincide con la que el servidor reporta en host-identity de Nav8, así que la comparación por GetFullPath del coordinador (línea 34) funcionará.
- Los diez controles de `test_navv9diag_gate.py` ejercen validate_fields real, no un stub; la deriva de un byte se rechaza por hash.

**Fixture y rutas**

- `test_navv9diag_ram_flow.cjs:22` espera `@DayZ_Baltic_EV112_Kit7NavV9`; el coordinador usa el mismo. Los tres JSON de controles y source-hashes.json llevan el mismo coordinator_sha256 21a9ff…, así que el coordinador no cambió tras la corrección del fixture.
- El fixture de misión cumple el regex del coordinador al mismo nivel que las seis misiones reales de missions.json (`C:\temp\DayZ_MCP_130_dev\mpmissions\BalticNavV9DiagAB0n_hex12.World`). Los controles de condiciones leen los init.c reales y verifican su hash. Nada que influya.

**Retención sin reintento favorable**

- `prepare_navv9diag_ram_pass.py:24-27`: una pasada n solo se prepara si no existe su carpeta y la anterior terminó con PASS_COMPLETE y cleanup limpio. Una pasada inválida bloquea las siguientes y no puede repetirse sin intervención manual visible. Correcto.

**Fixes (ninguno bloquea, decidir antes de sellar)**

1. `finalize_navv9diag_ram_ab.py:44` escribe el hash histórico como literal sin reverificarlo, y no lee benchmark-gate.json de cada pasada. Recomiendo añadir, antes del bucle, la llamada a `validate_diagnostic(R/'kit7-nav-consumer-20261026/result.json', D/'deployment.json')` y comprobar por pasada que benchmark-gate.json tenga status BOUND_DIAGNOSTIC_ONLY_HEIGHT_FAIL. Si se cambia, hacerlo ahora, porque accepted.json sellará el hash de finalize y una edición posterior rompería las pasadas 2 a 6. Si no se cambia, el riesgo residual es bajo porque finish lo exige por pasada.
2. source-hashes.json revisado hoy no incluye las herramientas heredadas que sí selló el accepted.json de Nav12: capture_server_baseline_ev112.ps1, bind/read/compare_server_baseline_ev112.py, observe_owned_server_exit.ps1, verify_terrain_perf.py, capture_owned_server_identity.ps1, copy_owned_server_rpt.ps1, record_nav_c_event.ps1 y verify_c_orderly_close.py. accepted.json debe sellarlas con su hash actual, como se anuncia.
3. accepted.json debe repetir la condición de Nav12: navv9diagRamConfig cargada directamente desde D/missions.json congelado, nunca reconstruida. El coordinador no puede verificar esto por sí mismo.

**Límites del resultado, conformes al plan**

El agregado produce PASS_EMPTY_SERVER_RAM_BUDGET o FAIL con acceptance_eligible=False y scope diagnóstico. Ningún script puede convertir una RAM favorable en aceptación funcional, y un FAIL no atribuye la causa al kit en exclusiva. No se ha ejecutado nada ni se declara RAM medida.
