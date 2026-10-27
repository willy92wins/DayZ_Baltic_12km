Ya tengo todas las fuentes leídas; redacto el veredicto.

**Veredicto: SOUND-with-fixes.** La cadena preparador → orquestador → finalizador → agregador exige realmente las tres condiciones nativas y conserva FAIL/INCONCLUSIVE, pero hay tres huecos que permiten un PASS fabricado o no rastreable. Ninguno requiere cambiar consumidores ni tocar DayZ.

**Lo que está bien verificado**

- **Admisión nativa en ambos extremos.** `prepare_nav8load1_ram_pass.py:16-20` y `finalize_nav8load1_ram_ab.py:15-17` exigen config PASS, 607 PASS, joint PASS, identidad y deployment. Hoy el directorio consumidor no contiene result.json, config-result.json, joint-result.json ni identity-verification.json, así que el preparador falla ahora mismo, que es lo correcto mientras la sonda sigue en curso.
- **El joint no puede ser un 607 antiguo por construcción.** `finish_kit7_nav8load1_probe.py:90` solo escribe PASS_LOAD1_CONFIG_AND_NATIVE607 cuando ambos consumidores devuelven código 0 y estado PASS en la misma ejecución, y guarda run_id y paquetes.
- **Gate por pasada.** benchmark-gate.json rehashea las pruebas nativas, accepted.json, missions.json y el propio preparador; finish y finalize vuelven a comprobar todos esos hashes.
- **Orden de medida.** Sampler arranca antes del observer y del hash; hash de paquetes solo tras cerrar la ventana; deadline 630 sobre captura 600; observer 900; arranque 60×5 s. Los tres mutantes del flow test cubren exactamente esos puntos.
- **Identidad del proceso.** PID más creación con tolerancia 2 ms en host-identity, observer, RPT y run.json; modo sin navmesh server; cero clientes; un solo CLOSE_INTENT y salida observada en 30 s.
- **Asimetría de carga respetada.** Chernarus espera 1 paquete (DayZ_MCP.pbo), Baltic 4; el host cuenta y compara solo lo que aparece en -mod. Ningún archivo afirma que Baltic se cargue en ambos mundos.
- **Comparador intacto.** Ratio 1.10, dispersión 5 %, INCONCLUSIVE_DISPERSION e INCONCLUSIVE_PAIRED_EXCESS se preservan; finalize sale con 1 en todo lo que no sea PASS pero escribe comparison.json igual.
- **Misiones.** Seis init.c con un solo guard de mundo y nombre de log repetido dos veces; prepare_files comprueba reversibilidad al template; validator Enforce 1 archivo por misión.

**Fixes necesarios antes de ejecutar**

1. **Joint no está atado a su sonda.** El preparador acepta joint-result.json solo por status. Un archivo escrito a mano con ese status y un result.json/config-result.json cualesquiera pasan. Fix: en prepare y finalize exigir joint.run_id == identity-verification.run_id == host-identity.run_id del consumidor, joint.packages == deployment.packages y joint.config_status/native_status == los status de sus archivos. test_nav8load1_joint_gate.py debe ganar fixtures para run_id y paquetes discordantes.
2. **accepted.json sin contenido mínimo.** `prepare_nav8load1_ram_pass.py:13-14` comprueba que lo que haya en inputs coincida, pero no que inputs incluya orchestrate, finish, finalize, los scripts PowerShell y los consumidores. Un accepted.json con inputs vacío pasa. Fix: assert de que inputs cubre la lista completa de source-hashes.json y que esos hashes son los revisados aquí.
3. **measurement_repeats hardcodeado.** `finalize_nav8load1_ram_ab.py:47` escribe 0 sin evidencia. Borrar pass-NN y relanzar prepare es indetectable. Fix: que finalize exija unicidad de run_id entre las seis pasadas y, si hay timeline global del box, que no existan run_ids del kit fuera de los seis; registrar el valor como "no verificado" si no se puede probar.

**Observaciones menores, no bloqueantes**

- Inventario de carpeta de misión no congelado: solo se hashea init.c. Un archivo añadido en la carpeta (cfggameplay.json, storage) alteraría la carga sin romper ningún gate. Conviene que prepare exija que la carpeta contenga exactamente init.c.
- Vanilla Addons se comparan solo por nombre tras la medida; los hashes vanilla vienen de before.json pre‑lanzamiento. Aceptable porque el ejecutable sí se rehashea y los PBO vanilla no se escriben, pero conviene documentarlo.
- En el orquestador `cmd` referencia `beat` antes de su declaración; solo funciona porque token es null hasta la línea 19. Es frágil pero no incorrecto.
- Caso wrong_server_identity deja el run sin cerrar por diseño. Hay que asegurar que el sellador lo trata como INCONCLUSIVE con intervención manual, no como repetible.
- El gate de calidad del preparador no comprueba el estado del pase anterior cuando n == 1, correcto, pero si pass‑01 falla y se quiere continuar hay que decidir explícitamente que la serie entera se descarta: el orden A‑B‑B‑A‑A‑B no admite huecos y compare exige exactamente seis.

**Lo que no se puede afirmar con este paquete**

- Nada sobre causa de RAM ni promoción global; el comparador ya lo limita y finalize no lo amplía.
- Nada sobre rendimiento demostrado: no hay ninguna pasada, ni accepted.json, ni joint-result.json.
- La fidelidad del contrato de dayz_test_run (status 'succeeded', on_busy 'queue') se da por buena desde los finales Nav12 revisados; no la he reverificado contra el servidor MCP.

**Para el sellador**

Antes de escribir accepted.json: aplicar los fixes 1 y 2, re‑ejecutar test_nav8load1_joint_gate.py con los fixtures nuevos, regenerar joint-gate-controls.json, y comprobar que la lista completa de source-hashes.json sigue coincidiendo salvo prepare y finalize, cuyos nuevos hashes deben quedar registrados. No se acepta RAM hasta que joint-result.json real exista con run_id atado y los seis pass‑NN tengan reference.json PASS.

FIN_REVISION