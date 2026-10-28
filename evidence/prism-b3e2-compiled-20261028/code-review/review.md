**Recibo:** Claude Fable 5.1 (model id claude-fable-5-1), lane nativa CLI 2.1.310, revisión read-only del diff B3E2 frente al plan adjudicado 28-10. Sin tools, hijos, escrituras ni git.

**Veredicto: SOUND-with-fixes.** El diff respeta el plan: aprobación nueva con esquema propio y postimágenes, preflight en hijo stdlib aislado con recibo PID, pins transitivos comprobados antes de cada fase, orden control-gate-candidato, enlace de fallo sin reinterpretar, consumidor sellado sin cambios. Los hallazgos son correcciones acotadas antes de ejecutar; ninguno exige rediseño ni toca fuentes selladas.

**Hallazgos (orden de prioridad)**

1. **Resultados oficiales descartados** `preflight_b3e2_ev112.py:29-30`. Solo check_p_drive pasa por require. Los cuatro restantes se invocan con el retorno ignorado. Si alguno señala fallo devolviendo False en lugar de levantar, el preflight certifica FRESH con un requisito de build ausente. Fix: capturar el retorno y exigir truthy para check_dayz_tools, check_vanilla_data y check_workshop_deploy. Para check_dayz_diag registrar el retorno en el reporte sin exigirlo. Si la skill fija documenta que estas funciones siempre levantan, anotarlo en el reporte en lugar de asumirlo.

2. **Candidato pinneado por observación** `build_prism_b3e2_ev112.py:51`. candidate.p3d entra en extra con sha observado. Si el contrato B3D no lo pinnea ya, el conflicto de la línea 52 no se activa y el pin histórico f2b7 queda sustituido por lo que haya en disco. El plan prohíbe exactamente eso. Fix: `gate.bind(sha(candidate)==gate.CANDIDATE,'candidate_pin')` antes de insertarlo, igual que ya se hace para OFFLINE, PROOF y PRIOR en la línea 46.

3. **Packer sin binding a pin** `build_prism_b3e2_ev112.py:79`. El script ps1 se ejecuta por ruta literal. check_pins verifica lo que hay en pins, pero nada ata esa ruta concreta a los pins heredados. Un desajuste de clave dejaría el packer sin verificar. Fix: en stable o al inicio de build, `gate.bind(str(W/'tools/water/pack_continuous_stream_pilot_v31.ps1') in c['pins'],'packer_pin')`.

4. **Importación del preflight bajo -I -S no probada** `build_prism_b3e2_ev112.py:67`. El hijo real de la suite solo ejecuta `-c`. Nadie prueba que preflight_b3e2 importe water_constraint_diagnostic y sus dependencias con site deshabilitado en la imagen PythonGIS. Si meter necesita psutil, el hijo muere en import, rc 2, INCONCLUSIVE_PREFLIGHT. No es falso PASS, pero bloquearía la ejecución y consumiría el intento. Fix: añadir un test que lance la imagen con `-I -S -c "import sys;sys.path.insert(0,HERE);import preflight_b3e2_ev112"` y exija rc 0.

5. **Módulos cargados exigidos tras importar solo odol_reader** `consume_prism_b3e2_ev112.py:12-15`. Si READER_PINS incluye lzo o lzss y odol_reader los importa de forma perezosa, el bind loaded_reader_path falla con módulo None y el gate de control queda inconcluso. Verificar que READER_PINS y la estrategia de import de odol_reader coinciden. Si no, importar explícitamente cada stem de READER_PINS antes del bucle.

6. **Recibo running tras éxito** `build_prism_b3e2_ev112.py:69`. Se lee preflight-driver.running.json después de un hijo que terminó bien. La suite solo observa el receipt tras timeout. Confirmar que run_tree conserva running.json en salida normal. Si lo retira, leer el pid desde el receipt. Fallo sería FileNotFoundError, no falso PASS.

7. **Fallo de aprobación sin recibo en disco** `build_prism_b3e2_ev112.py:63`. checked_approval corre antes de mkdir, por lo que un rechazo de aprobación no deja execution-failure.json. Es coherente con no crear la carpeta si la aprobación es ajena. Aceptable; anotar en el handoff que estos rechazos solo quedan en stderr del orquestador.

**Observaciones menores**

- `build_prism_b3e2_ev112.py:17` usa `Path(__file__)` sin resolve. En main es absoluto; añadir resolve evita un desajuste de clave si se importa desde otra ruta.
- `consume_prism_b3e2_ev112.py:19` fija MAX_SECONDS pero no MAX_BYTES. El preflight sí fija ambos. Igualar a 2 GiB.
- `preflight_b3e2_ev112.py:26` ejecuta el módulo de la skill fija antes de la redirección de stdout. Cualquier salida de import no queda en official-checks.log.
- La suite no ejercita helper_changed porque HELPERS se parchea vacío. Añadir un subtest con un helper mutado es barato.

**Lo que está bien y no requiere cambio**

- Orden de verificación hash antes de parsear en pinned_json y en los recibos externos.
- Recheck de aprobación tras el preflight y stable antes y después de cada fase.
- Gate real positivo y negativo sobre fixture independiente, con prueba de que no se crea carpeta candidata.
- Descendiente observado vivo impide cierre y se retira por PID/create_time, sin promesa sobre hijos no observados.
- Retorno 0 tardío rechazado por pared y por seconds del recibo.
- Comparación de config.bin entre control y candidato.
- Sin cambios en igualdad, tolerancias ni grosor local. Sin 201, nativo ni DayZ.

**Adjudicación sugerida para Codex:** aplicar fixes 1, 2 y 3 obligatoriamente, añadir el test de 4, verificar 5 y 6 contra las fuentes selladas antes de lanzar. Re-correr la suite y refrescar postimágenes en la aprobación. Presupuesto de preflight se mantiene en 60 s.

FIN_REVISION