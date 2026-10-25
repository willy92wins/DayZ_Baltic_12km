**Veredicto: SOUND-with-fixes.** El plan es coherente con los artefactos citados y las condiciones del usuario. Las correcciones son de precisión y de pre-registro; ninguna exige otra fase.

**Verificado contra fuentes**

- 4749 controles PASS, cero fallos: `runtime-rectangle-f/result.json:2-9`. El vínculo con el PBO 4e5f909 no está en ese archivo sino en identity.json y receipt.json del mismo directorio.
- Terreno F caa5398 y límites del parche X2892..2958/Z6804..6870: `f-nav-dry-corridors.json:3-9,284`.
- Las cuatro líneas del plan coinciden con las seleccionadas: `f-nav-dry-corridors.json:54-61,113-120,172-179,235-242`. Política 0.05 m, delta fuerte 0.1 m, muestreo 1 m: líneas 42-45. Las primeras líneas se rechazaron por margen negativo: `f-nav-route-discovery.json:15,38,61,84`.
- No existe navegación nativa de F y las 37 consultas de E no incluyen ninguna f_patch, así que la selección no pudo usar resultados del motor: `navmesh-guarded-e-v9-probe-c/result.json` solo lista los 37 casos heredados.
- Generador 66935ce, versión 9, cuadrícula 983x983 = 966289, duración 18:07 a 19:23 (76 min): `navmesh-guarded-e-v9/generation.json:4-6,29,34-40`.
- tileWidth 12.5 y cellSize 0.25/0.1/0.1: `package-rectangle-f/config.cpp:64-67`.
- Consumidor sin cambios: `init.c:41-44` conserva SampleNavmeshPosition radio 2 y FindPath. El verificador prueba terreno cargado contra el npz con 0.011 m: `verify_continuity_nav_v30.py:31,39`. Esto hace que un delta E/F ≥0.05 m en un waypoint sí discrimine F de E.

**Hallazgos y correcciones**

1. **Taxonomía de fallo no pre-registrada** (`plan:47-48,66`). Los corredores EW y NE/SW tienen margen seco 0.070 y 0.089 m (`f-nav-dry-corridors.json:63,181`). Es plausible que el muestreo falle en E y F por igual. Fijar antes del run de E: consulta nueva que falla igual en E y F = INCONCLUSO explicado y la unidad no PASA; consulta que pasa en E y falla en F = FAIL de regresión. No retirar ni mover.

2. **Criba de una sola banda por la rejilla** (`plan:38-39`). Con z=12282-6r y x=6c (`v30_common.py:21-22`), EW z=6828 es exactamente la fila de vértices 909, NS x=2934 la columna 489, y NO/SE corre sobre las diagonales de celda. La criba contó celdas solo por floor, un lado de la línea (`f-nav-dry-corridors.json:64-105,123-164`). El agente de 0.6 m y el radio de muestreo 2 m invaden el lado no comprobado. Corrección pre-run y numérica: exigir esquinas secas en ambas celdas adyacentes a cada línea, documentando el rescreen con el mismo script. No usa resultados del motor.

3. **Hash de E ausente en el plan** (`plan:6-8`). La puerta de cobertura compara tri_sample de E y F; el plan solo fija F. Añadir el npz de E 705196d (`f-nav-dry-corridors.json:283`) como entrada fijada de la puerta.

4. **Stack piloto/agua no fijado** (`plan:51`). E se generó con agua 97edcafe y piloto c0be9abc (`generation.json:18-19`). El plan debe exigir esos mismos SHA como --additional-pbo y agua para F.

5. **El preparador no produce 45 consultas** (`prepare_current_nav_probe_ev112.py:45-48`). Solo retarget de las antiguas, y el control de deriva usa zip, que no detecta añadidos. Se necesita un preparador o un modo explícito que tome las 37 heredadas más un JSON congelado de 8 consultas con expect=path, sin tocar las 37. El nombre de log y cabecera están fijos en `:51-52`, así que los runs E y F necesitan perfiles distintos o marcadores distintos para no sobreescribir.

6. **init.c sin fijar**. El plan lo da por definitivo (`plan:21-23`), pero está modificado sin commit en el worktree. Fijar SHA o commit antes de ambos runs, como ya exige el preparador en `:40`.

7. **Referencia de línea imprecisa** (`plan:16`). El límite ≤7200 s y la salida nueva están en `generate_navmesh_console.py:48`, la identidad por SHA en `:60`. El valor por defecto es 1800 (`:46`); pasar --timeout-s 7200 explícito.

8. **Identidad del PBO con NM de F en el paso 7** (`plan:57-60`). El delta de terreno demuestra el WRP de F, no el NM. Como NM y WRP van en el mismo PBO, basta registrar el SHA del PBO desplegado al lanzar, como hizo runtime-rectangle-f con identity.json. El plan debe exigirlo y además decir que el PASS 4749 se transfiere por WRP 0139cd1 y 6826 entradas exactas, no por SHA de PBO.

9. **config.bin "idéntico" frente a verification.json** (`plan:11`, `verification.json:70-73`). config.bin figura como entrada cambiada respecto al PBO compilado 1db792. No es contradicción si la base es la salida de Terrain Builder antes de inyectar la clase Navmesh, pero el plan debe nombrar la base de cada comparación.

10. **Especificación de la puerta** (`plan:58-62`). Definir: entrada = result.json del verificador con status PASS, el log, ambos npz con hash; por cada uno de los 8 casos existe una fila P cuyo XZ tiene |tri_sample(hE) − tri_sample(hF)| ≥ 0.05. Pruebas: punto fuera del parche, caso ausente, delta 0.03, y verificador en FAIL con deltas válidos (la puerta no debe PASAR).

**Supuestos a exponer**

- La regla "preferir el máximo delta" (`plan:42`) no considera pendiente; maxSlope=60 y maxStepHeight=0.45 (`config.cpp:76-77`). Si el muestreo falla en el punto de máximo delta, queda FAIL/INCONCLUSO conservado. Opcional: registrar la pendiente de F en el disco antes del run para que el fallo sea explicable, sin cambiar márgenes.
- El paso 1 (A/B de servidor vacío de E) es independiente de esta unidad y no debería bloquear F.
- 983 teselas asume la extensión 12282 m; coincide con la cabecera medida de E, no con un cálculo.

Para Codex: los puntos 1 a 4 son texto del plan antes de congelar; 5, 8 y 10 son el código nuevo con pruebas; 2 requiere un rescreen numérico pre-run con el script 568160 extendido a ambas bandas.