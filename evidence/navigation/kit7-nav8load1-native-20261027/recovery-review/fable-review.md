**Veredicto RECOVERY: SOUND-with-fixes.** **Veredicto RAM_FIXES: SOUND-with-fixes.** Ninguno de los problemas exige relanzar la sonda ni tocar las fuentes congeladas.

**RECOVERY**

Lo verificado contra los archivos reales:

- **Fallo original acotado.** config-consumer.stderr.log muestra solo ModuleNotFoundError del hermano verify_nav_config_types_ev112. identity-verification.json ya existía, result.json tiene PASS_KIT7_NATIVE_GRAPH con log_sha256 igual a log-binding.sha256 y reference_sha256 igual al hash congelado de reference.json. run_id f6f09de4 coincide en host, identity, close y los cinco eventos del timeline.
- **Captura cruda válida para el consumidor.** Las 9 filas de config-runtime.log cumplen exactamente verify_nav8_load1_config_ev112.py con el probe_id congelado 4b29679b: filas 0, 2, 3 tipo 0, texto 1, entero y flotante 1; fila 1 tipo 2 y texto true; controles positivos 8, 50, 12:00, Chernarus; negativo ausente. El resultado esperado es PASS, no está forzado.
- **Bloques congelados bien cortados.** Las tres marcas de corte aparecen una sola vez y la aserción de conteo lo exige. El primer bloque reejecuta stock, frozen, deployment, identidad MCP, cleanup, RPT y timeline; el segundo, observer y salida de generación. Se omite correctamente la aserción de ausencia de result.json porque ya existe, y la ventana temporal del config log se reimplementa igual que la original.
- **Bootstrap idéntico al probado.** test_nav8load1_isolated_wrapper.py extrae la línea bootstrap del propio script de recovery, así que lo ejecutado es lo testeado. Hashes del consumidor y de su módulo hermano están en frozen.inputs y en source-hashes.
- **Joint equivalente al original.** Mismos campos que exigen prepare y finalize, nav status asegurado por aserción previa, packages de deployment.

Problema concreto:

1. **No-clobber incompleto en los logs auxiliares.** recover_kit7_nav8load1_config_consumer.py:35 usa write_bytes. Si el consumidor muriese antes de escribir config-result.json, la línea 36 falla sin dejar joint ni config-recovery, y una segunda ejecución sobrescribiría los logs del primer intento sin rastro. Fix mínimo: abrir ambos con modo xb y añadir `not (D/'config-recovery.json').exists()` y los dos logs a la aserción de la línea 15.

Observación: el estado PASS del recovery depende de que el sellador genere completion.json y adjudication.json con ACCEPTED_AFTER_REVIEW; el script no verifica que response.json termine en FIN_REVISION ni su veredicto, eso queda en manos del sellador.

**RAM_FIXES**

- **Fix 1 confirmado.** prepare_nav8load1_ram_pass.py:28-32 y finalize_nav8load1_ram_ab.py:29-33 exigen run_id común en joint, identity y host, statuses espejo y cuatro paquetes idénticos por ruta normalizada entre joint, identity, host y deployment. test_nav8load1_joint_gate.py ejecuta la sección real con fixtures discordantes por run_id, status y paquete.
- **Fix 3 confirmado.** La reserva se abre con modo x fuera de pass-NN antes de crear la carpeta; finalize exige exactamente seis reservas, un LAUNCHED por pasada, seis run_id distintos y accepted_sha256 coincidente. measurement_repeats null y host_wide_history NOT_VERIFIED están etiquetados honestamente. Consecuencia a aceptar explícitamente: si prepare(spec) o el lanzamiento MCP fallan tras la reserva, la serie entera queda muerta sin medida, porque no hay reintento posible por diseño.
- **Fix 2 con hueco.** prepare_nav8load1_ram_pass.py:17-22 y finalize_nav8load1_ram_ab.py:18-23 comparan solo las claves de source-hashes revisado con adjudication; los valores revisados nunca se comparan. Hoy el source-hashes de la revisión RAM tiene hashes antiguos de prepare, finalize, test_nav8load1_joint_gate y joint-gate-controls, distintos de los actuales. Eso es legítimo, pero el código permitiría que adjudication registrase cualquier archivo con cualquier hash nuevo, no solo esos cuatro, y accepted.json pasaría. El fixture del test usa valores iguales en reviewed e inputs, así que no detecta la divergencia. Fix mínimo: en ambos scripts `assert all(reviewed[p]==required[p] for p in reviewed if p not in adjudication['post_review_changes'])`, exigir que post_review_changes sea exactamente ese conjunto de cuatro rutas y que sus valores coincidan con los de kit7-nav8load1-recovery-review-20261027/source-hashes.json, añadiendo ese archivo y su adjudication.json al bucle de pruebas de la línea 20 y 21. Añadir al test un caso con valor revisado distinto.

Menores, no bloqueantes:

- finalize_nav8load1_ram_ab.py:39 reutiliza el nombre gate para el benchmark-gate y oculta el accepted gate; no se usa después, pero conviene renombrar.
- prepare_nav8load1_ram_pass.py:36 exige carpeta con solo init.c; funciona porque cada pasada usa carpeta distinta y el servidor crea storage al arrancar, no antes.

**Condición de PASS global.** RAM solo arranca un bloque de seis si el joint real escribe PASS_LOAD1_CONFIG_AND_NATIVE607 con el run_id f6f09de4 y los hashes de este source-hashes siguen intactos en el momento de ejecutar recover. Si el sellador aplica el fix xb y el fix de valores revisados, nada más impide proceder.

FIN_REVISION