**Veredicto: SOUND.** Los cuatro fixes obligatorios y el opcional están cerrados en el código congelado, los controles nuevos demuestran que cada puerta añadida está viva, y no encuentro ninguna regresión que abra un camino de PASS falso ni un FAIL falso. No hay hallazgos bloqueantes residuales.

**Cierre verificado**

1. **Readiness 60×5 s.** `orchestrate_kit7_nav_probe.js:18` pasa de 30 a 60 iteraciones. En `test_kit7_nav_probe_flow_v2.cjs:23` el caso `slow_readiness` devuelve WAITING en 35 lecturas y termina con cierre, liberación y consumo. `readiness_timeout` lanza el deadline sin consumir y cierra y libera el run. Ambos pasan en coordinator-controls-v2. Cerrado.
2. **SHA de referencia desde frozen.** `finish_kit7_nav_probe.py:55` pasa `frozen['inputs'][str(O/'reference.json')]`. La clave coincide carácter a carácter con la entrada de frozen.json en formato Windows con barras invertidas, y todo el manifiesto frozen y deployment se verifica en las líneas 14 y 15 antes de usarlo. Cerrado.
3. **Verify recalcula el corredor.** `verify_kit7_nav_ev112.py:36` exige 0.801 exacto. Las líneas 65 a 71 reconstruyen buffer 2.1 desde la centerline, el conjunto `allowed` por `intersects` con cada seco, el exterior solo para `cap_to_land` como diferencia contra la unión total, comparan ambos con diferencia simétrica menor que 1e-6 y reafirman agua nula y cobertura continua. Las cuatro reglas son idénticas a las de `freeze_kit7_nav_routes.py:35-40`, incluido el GeometryCollection vacío para rutas sin exterior. Los 19 controles sintéticos pasan, con el positivo real en PASS y `relaxed_tolerance`, `changed_centerline`, `fake_exterior` y `fake_corridor` rechazados con el mensaje esperado. Cerrado.
4. **Nombre de log ligado a la UUID.** `finish:26` compara el nombre de `binding['source']` con `frozen['log_name']`. El capturador escribe `source` con la ruta del EngineLog, y la constante del orquestador lleva la UUID 9953b36c que coincide con frozen.json. Cerrado.
5. **Versión exacta.** `finish:27` compara `mcp['version']` con el de mcp-after.json, cuyo SHA añade el empaquetador a `deployment.inputs` en `package_and_deploy_kit7_nav9.py:72` y se verifica en finish antes de leerlo. El generador activo escribe ese fichero con el campo `version` mediante su función snapshot. Cerrado.

**Regresiones buscadas y descartadas**

- Las 11 fixtures del worktree solo usan `check_route`, que no cambió, así que no se ven afectadas por la nueva comprobación de 0.801.
- Si mcp-after.json o frozen.json no están al día, finish falla antes de escribir nada, de modo que es reejecutable sin consumir evidencia.
- La mezcla de inputs en deployment.json no permite que un hash de accepted sobrescriba silenciosamente uno estancado en frozen, porque package y finish verifican frozen por separado.

**Notas no bloqueantes**

- No he podido recalcular hashes en modo solo lectura. Los SHA del coordinador en los dos ficheros de controles v2 coinciden entre sí, pero Codex debe rehashar orchestrate, finish, verify y package al sellar frozen.json y accepted.json, puesto que frozen.json todavía lleva los SHA de la versión previa de los tres scripts revisados.
- Acepto la aclaración de la nota 6 del plan: los cuatro excesos y las seis rutas con `allowed` extra son métricas distintas y no cambian criterios.
- Sigue sin existir evidencia de navegación nativa. Los controles demuestran que las puertas están vivas, no que el grafo navega.
