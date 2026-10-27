**Veredicto: SOUND-with-fixes.** El experimento de 12 m está suficientemente motivado, los gates son verificables sin falso PASS, y no encuentro defecto bloqueante en el plan. Hay cuatro correcciones mínimas de redacción/contrato y dos incertidumbres experimentales que el gate nativo ya cubre.

**Citas contrastadas (todas correctas)**

- Cifras de `comparison.json`, `height-comparison.json` y el resumen de planificación coinciden con el plan: 1,26591 / 1,24133, dispersión máxima 0,205 %, 0,711963 m, 0,715085 / 0,535467 / 0,778856 m, excesos 74 / 56 / 10 y calibración 125→4, 10→0.
- `config-input/config.cpp:64` tiene `tileWidth=8;` y el diagnóstico v2 `config.cpp:64` tiene `tileWidth=12.5;`. SHA base `a2919a80…`, 6826 entradas inalteradas y WRP `0da63d3f…` confirmados en `config-input/verification.json`.
- `package_nav8_config_ev112.py:27-31` exige exactamente una declaración 12.5 y `:34` compara tokens; `inspect_navmesh_v9_ev112.py:16` y `:88` enumeran (8, 12.5, 25, 50); `generate_navmesh_console.py:48` acota a 18000 s.
- `orchestrate_kit7_nav8_generation.js:6` llama al heartbeat directo dentro de `cmd` y `:35` registra `HEARTBEAT_ERROR` vía `cmd` antes de recuperar, lo que reproduce la recursión con token caducado. `resume_kit7_nav8_generation.js:6` usa `beat()` y `:14-21` adopta y verifica identidad antes de `event('LEASE_RECOVERED')`. `lease-recovery.json` documenta exactamente ese fallo. La descripción del plan es fiel.
- 12288 / 12 = 1024 exacto; 1024² = 1048576. Para 12,5 el generador produjo 983 (floor de 983,04), así que para 12 no hay ambigüedad de redondeo.
- No pude recalcular los SHA de `source-hashes.json` (sin procesos); contrasté contenidos, no hashes.

**Hallazgos**

1. **Motivación RAM incompleta pero verificable a favor del plan** (`plans/ev112-kit7-nav12-cost-20261027.md:26-31`). El plan omite el dato más fuerte: `evidence/performance/server-baseline-ab-20261025/comparison.json` registra PASS con 0,832 / 0,844 usando una navmesh de 12,5 m (966289 teselas, 704,67 MB). La de 8 m tiene 2359296 teselas y 1338 MB, y falla a 1,266. Entre ambos puntos la residente creció ~1455 MiB, más del doble del incremento de bytes de archivo (~633 MB), así que el coste sigue al número de teselas más que al tamaño en disco. 12 m añade solo 82287 teselas sobre el punto PASS conocido. Corrección mínima: citar ese PASS en §1 como motivación de proximidad, no como predicción. Consecuencia de no hacerlo: un lector no puede distinguir 12 m de una elección arbitraria entre los candidatos.

2. **Control faltante en el replanteo tras fallo** (`:109-111`). La línea base 25-10 cargó el paquete E (`navmesh-guarded-e-v9`), no el NavV9 de kit7 (`navmesh-kit7-v9-20261026`, 704,54 MB). El paquete kit7 de 12,5 m nunca se midió en RAM. Si 12 m falla RAM, "localizar el coste responsable" exige medir el kit7 12,5 m como control, pues de lo contrario se atribuiría a la anchura de tesela lo que podría ser geometría del kit7. Corrección: añadir esa medición como primer paso del replanteo, sin ejecutarla ahora.

3. **Expectativa funcional presentada de forma asimétrica** (`:19-22`). El plan cita el máximo en los ocho puntos (0,715 m) pero no el máximo en todos los waypoints: 1,2509 m para 12 m frente a 1,0111 m para 8 m. La regla de selección (`:28-29`) usa solo los ocho puntos, mientras que el único predictor calibrado es el exceso total (125→4, 10→0), donde 74 sugiere del orden de dos fallos. No es defecto: el gate 4 lo cubre y el presupuesto de una sola generación es correcto. Corrección: citar ambos máximos y declarar que la justificación de 12 m es la proximidad RAM al PASS conocido, no la estimación funcional.

4. **Plazo de recuperación no trasladable sin receipt** (`:68-69, :77`). `resume_kit7_nav8_generation.js:27` fija el deadline con la hora de inicio escrita a mano. El plan prohíbe trasladar PIDs, tokens y sesiones, pero el deadline sí debe sobrevivir a la recuperación. Corrección: el coordinador nuevo persiste `started_utc`/`deadline_utc` en un recibo y el runner de recuperación lo lee; test de que no se reinicia.

5. **Inspector: el recibo del wrapper no fija 1024** (`:56`, `generate_navmesh_console.py:108`). `header_ok` solo comprueba `count == nx*nz`. El plan ya exige inspección estricta con grid 1024×1024, lo que cierra el hueco; basta hacer explícito que se invoca con `--grid 1024 1024 --tile-width 12` y que `tests/test_navmesh_v9_prefixes_ev112.py` añade el caso 12 positivo y el rechazo de 12 contra un NM de 8 o 12,5.

**Presupuesto temporal**: la generación de 8 m duró de 01:59:33 a 05:39:12 UTC (~13180 s, 73 % de 18000). Con el 44 % de teselas, 18000 s es creíble; el wrapper marca `TIMEOUT` y sale 1, y el plan lo trata como INCONCLUSO. Coherente.

**Gates sin falso PASS**: el gate funcional exige las mismas 607 consultas, CSV idéntico, cero `height_issues`/`local_failures` y cierre limpio; el gate RAM reutiliza lectores y referencia con hashes y exige ambos estados del paquete exacto de 12 m. El preparador por pasada ya exige PASS nativo e identidad de paquetes. No veo ruta a un PASS no respaldado.

**Límites de esta revisión**: solo lectura; no verifiqué hashes ni ejecuté tests; no revisé el harness RAM ni los scripts de screening de anchura más allá de sus resultados; no afirmo nada sobre capacidad, cliente ni éxito geométrico de 12 m.
