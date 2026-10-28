# B3E2: código adjudicado para una pareja aislada

Fable5.1 nativo:109.734s, entrega completa, identidad modelUsage,
sin herramientas ni denegaciones; las cinco entradas permanecieron exactas.
No escrituras externas por el revisor: tools vacías/safe-mode, salida capturada
por el wrapper propio. No equivale a council ampliado.

1. F1 REFUTADO frente a preflight_syntax_repaired.py:219-254,311-341:
   los cuatro check_* retornan None tanto en éxito como en aviso. Exigir truthy
   rompería todos los casos válidos. Los requisitos de build ya se verifican
   directamente: check_p_drive, validate_p_mods, tools_root/hash y cuatro carpetas.
   La semántica queda explícita en el reporte. Diag no certifica entorno nativo.
2. F2 no era falso PASS: prism_b3e_compiled_ev112.py:158-165 ya exige CANDIDATE
   literal y se llama antes del build. Se añade guard temprano idéntico en
   make_contract para evitar materializar un contrato con identidad incorrecta.
3. F3 aceptado como binding explícito adicional: exigir que la ruta concreta del
   packer invocado esté en pins B3D. No sustituir el hash por una lectura actual.
4. F4 aceptado: nuevo test real importa el worker bajo imagen GIS -I -S, sin
   ejecutar preflight. Importación stdlib pasa, no presupuesto consumido de build.
5. F5 refutado por odol_reader.py:11-12 y bis_reader.py:16-17: imports inmediatos
   de los cinco módulos. Test real separado confirma rutas y hashes de los cinco.
6. F6 resuelto por lectura run_tree: running.json se escribe y nunca se retira;
   test positivo real comprueba PID del recibo conservado frente al árbol observado.
7. F7 intencional: aprobación rechazada antes de crear salida queda en stderr
   del wrapper exterior; no clobber ni recibo en carpeta ajena.

Menores: Path(__file__).resolve y MAX_BYTES explícitos aplicados. Test helper
mutado añadido. La carga del módulo oficial se conserva en driver.log y tiene
evento previo duradero; sus check_* escriben official-checks.log. Sin pérdida
de log global ni afirmación de causalidad del timeout histórico.

Suite final24tests PASS6.156s; recibo b3e2-tests-final-20261028/report.json.
Presupuesto120s sin ampliar. Suite inicial21PASS8.109s preservada. Fixtures
positivos/negativos contra consumidor real, PBO independiente e hijos reales.
No cambios en consumidor sellado ni tolerancias. Se autoriza una sola pareja
B3E2 conforme al plan: preflight60s, builds150s cada uno, gates180s cada uno,
2GiB, control antes de candidato. Nada de paquete201, despliegue o DayZ.
