## 0. Crítica del encuadre

El encuadre mezcla tres problemas de naturaleza distinta y los presenta como un solo «rumbo del agua»:

1. **Confunde decisión de diseño con arreglo técnico.** BALTIC-017 (agua colgada) es una decisión de niveles, explícitamente abierta: «No confundir ese candidato con una decisión de cerrar todos los niveles de agua» (`product-spec.md:23`); el propio README del pulido dice que derivar niveles del terreno natural «es una decisión de diseño pendiente» (`evidence/v30-polish-candidate-2026-10-04/README.md:84-85`). BALTIC-015 y la escalera de BALTIC-007, en cambio, son problemas de colocación y de malla con remedio técnico conocidos. Meterlas en la misma decisión «rumbo» hace que parezca que todo se decide a la vez, y no es así.

2. **La evidencia es casi toda visual u offline, pero los criterios de aceptación de la spec son funcionales.** P9 exige «paso real de embarcación por cauce y puente» y P10 exige navmesh y navegación antes del mapeado (`product-spec.md:15-16`). Nada de lo citado mide cómo el agua colgada o las costuras afectan a lancha, navmesh o IA; el censo mide geometría (`evidence/v30-polish-candidate-2026-10-04/census/census.json`, `params`: anillo 12–36 m, umbrales 0,3/0,5 m). Falta el eslabón «esto rompe el juego», y sin él se corre el riesgo de pulir visualmente cosas que no bloquean la base 1.0 mientras navmesh e IA quedan para el final (`HANDOFF.md:20`, pasos 4–5).

3. **El hecho H2 se usa con una métrica desplazada.** El «26–30 % de la mejora» con calado ≥ 0,25 m es la mejora del *desvío de línea de agua* (`bugs.md:19`), no una medida de calidad visual; usarlo para descartar calados intermedios mezcla unidades. Lo que sí está medido en motor es solo los dos extremos (escalera del candidato frente a transparencia del surco libre, `evidence/v30-shore-crossing-candidate-2026-10-04/README.md:165-171`).

4. **I1 está bien planteada como supuesto, y el mecanismo está verificado aunque la comparación lago a lago no.** Los niveles de lago y banda salen tal cual de las superficies V29 `contour-v2` (`tools/terrain/build_v30_water.py:44-51`), así que la causa estructural de I1 es cierta; lo no verificado es la magnitud lago a lago.

5. **Falta un dato que cambiaría la decisión:** el histograma del censo muestra 520 de 631 masas por debajo de 0,3 m de perched (`census.json`, `perched_m_histogram`). Es decir, el 82 % del agua estancada está *bien*. Cualquier rumbo que «rederive todos los niveles» trabaja innecesariamente sobre la mayoría sana.

## 1. Agua colgada

**Recomendación: mezcla con criterio por masa, sesgada a bajar el agua (no a levantar diques), pero solo donde haga falta.**

- **Criterio por masa.** Usar el censo tal cual (`census.json`, `totals`): 111 lagos colgados (7,0 km²), 190 masas con dique > 0,5 m. Propongo tres clases:
  - **Rebajar el agua** (nivel := mediana del anillo + margen pequeño) en las masas *colgadas* con dique > ~1,0 m o adyacentes a cauces navegables (P9): en el top-12 del censo los diques van de 1,15 a 1,57 m (`census.json`, `top_12`: `dike_m` 0,797–1,498 en las colgadas), y el caso típico de la cabecera del Luga es agua a ~4,15 m sobre terreno a ~3,0 m con diques de ~1,4 m (`evidence/v30-polish-candidate-2026-10-04/README.md:18-20`). Los diques de +0,35 m del constructor (`build_v30.py:40,449-450`, citado en el brief; [SUPUESTO]: no pude abrir el fichero) son la consecuencia, no la causa.
  - **Aceptar** las masas con perched < 0,6 m y dique < 1,0 m fuera de vista de corredores: son 49–101 masas del histograma en la banda 0,3–1,0 m (`census.json`, `perched_m_histogram`) y el coste visual de tocarlas no está justificado para 1.0.
  - **Los dos lagos grandes colgados** (id 269: 4,6 km², perched 0,333 m; id 170: 2,0 km², perched 0,547 m; `census.json`, `top_12`) merecen decisión separada por superficie: bajarlos mueve orillas que el ajuste de orillas H1 acaba de calzar (91.857 vértices cambiados, `evidence/v30-shore-crossing-candidate-2026-10-04/README.md:56`).

- **Riesgos que hay que gestionar explícitamente:**
  - **Separación de masas.** El constructor da la arista a la tierra cuando agua estancada supera a un vecino en > 0,30 m (`tools/terrain/build_v30_water.py:221-223`). Bajar un lago sin revisar sus vecinos puede borrar planos en la frontera y fragmentar el agua. La re-derivación debe hacerse por cuenca/localidad, no lago a lago independiente.
  - **Arrastre en escalera hacia ríos.** El tope de 0,25 m por 6 m solo baja el agua que fluye, no la estancada (`tools/terrain/build_v30_water.py:209-211,224-235`), pero si el río conectado queda por encima del lago rebajado, la separación actúa al revés. Revisar bandas V29 en las junciones (mismo origen V29, `build_v30_water.py:45-48`).
  - **Puertas.** Tras rebajar hay que re-correr `verify_terrain_v30` (calado ≥ 0,10 m, tierra ≥ 1,40 m, pendientes ≤ 35°, esquinas contra plano; `tools/terrain/verify_terrain_v30.py:31` [SUPUESTO], citado del brief) y re-correr el censo: salida exigible, 0 masas colgadas > 0,3 m salvo excepciones firmadas por Guillermo.

## 2. Cauces y piezas

**Recomendación: sí a piezas vanilla solo en cauces anchos, con encadenado canto con canto como Chernarus, y con un umbral operativo, no «anchura» a ojo.**

- El diagnóstico es sólido: Chernarus tiene 0,33 % (ríos) y 0,49 % (arroyos) de huella con dos láminas o más, con juntas a −0,044 m de mediana (canto con canto) y desvío de rumbo p50 0,44°; nosotros 58/73/75 % en R1/R2/R3, con solapes p50 de 0,54 m en R2 y giros en junta de 8,8–11,4° (`evidence/v30-polish-candidate-2026-10-04/joints/joints.json`, bloque `groups`; `evidence/v30-polish-candidate-2026-10-04/README.md:61-74`). La causa está en el código: `--overlap-all` y `overlap_from=None` solapan un par de faldones (`tools/water/fit_channel_pieces_v30.py:263` y definición de reaches en `:50-58`), y el avance con solape resta 6·escala por pieza (`:278`).
- **Umbral operativo:** colocar piezas solo donde el cauce tiene *vértices mojados interiores* (≥ 3 vértices de ancho). Hoy R2 y R3 no tienen ninguno: «todos tocan tierra, porque los cauces miden 1–2 vértices de ancho» (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md:189-190`). Es medible, automático y coincide con donde las piezas aportan algo.
- **Curvas sin solapes ni huecos:** imitar lo medido en Chernarus: encadenar canto con canto (along p50 −0,044 m, `joints.json`), girar *dentro* de las piezas curvas de 10/30° (la biblioteca ya las tiene: `fit_channel_pieces_v30.py:9-10`) y permitir desplazamiento lateral de hasta ±3,5 m (across p10/p90 ±3,48 m en Chernarus, `joints.json`). Con `overlap_from=None` eliminado y `--overlap-all` fuera, el bucle ya sabe avanzar sin solape (`fit_channel_pieces_v30.py:261-279`); hay que añadir el giro intra-pieza y la deriva lateral, que hoy no hace.
- **R1:** sus 58 % de doble lámina vienen del solape total (unos 22 m, por encima del umbral de 12 m de la regla de juntas, `evidence/v30-polish-candidate-2026-10-04/README.md:69`), no de la anchura. Con encadenado canto con canto, R1 debería quedarse con piezas.

## 3. Arroyos estrechos

**Recomendación: discrepo de I3; sí hay al menos una tercera vía, no probada pero barata, y una segunda que toca diseño.**

1. **Surco libre + fondo oscuro del lecho.** El problema del surco libre es que con 0,10 m de lámina el agua «se ve casi transparente y en primer plano parece seco» (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md:168-169`). Pero la transparencia es un problema de *lectura*, no de geometría: la superficie del candidato v2 ya demuestra que el tono del fondo es configurable (`build_surface_v30.py --bed-tone land --shore-ring flowing`, `evidence/v30-polish-candidate-2026-10-04/README.md:30,52`). Pintar el lecho de los arroyos con surco del tono oscuro del agua convertiría la lámina fina en un arroyo oscuro legible, sin escalera y sin tocar la orilla. **[SUPUESTO]: el efecto visual no está probado en motor**; es un experimento de una sesión. La mancha oscura de BALTIC-016 demuestra además que un fondo oscuro *se* ve cuando la lámina no se dibuja (`bugs.md:28`) — justo el mecanismo opuesto al que necesitaríamos controlar, y razón para probarlo antes de asumir.
2. **Enschar el contorno de diseño de los arroyos importantes a ≥ 3 vértices** solo en los tramos que Guillermo quiera protagonistas: da vértices mojados interiores, permite calado sin mover la orilla y reduce las isolíneas de profundidad. Toca water_v3 (decisión de producto, P2/P14: `product-spec.md:8,20`), así que es de Guillermo, pero es la única vía que resuelve la causa estructural y no el síntoma.
3. **Lo que descartaría para 1.0:** piezas vanilla en R2/R3. Con 1–2 vértices de ancho, encadenar canto con canto no arregla el zigzag aéreo de anchura uniforme (1.817 m² de agua visible frente a 552 m² de diseño en R3, `evidence/v30-shore-crossing-candidate-2026-10-04/README.md:209-211`), y el lecho constante que atenuaría las isolíneas «movería la orilla» (`:188-190`).

## 4. Rumbo fijo

1. **Ver el candidato v2 pulido en motor** (`@DayZ_Baltic_PolishCandidate`, vistas de `camera-poses.json`; `HANDOFF.md:20`). *Salida:* veredicto binario por vista (cabecera del Luga, rectángulos, lake_038, fosos, manchas, SHORE4) y confirmación de BALTIC-016 con la superficie nueva. *Congela:* la superficie (`--bed-tone land --shore-ring flowing`) si pasa.
2. **Decisión de política de niveles (BALTIC-017)** con Guillermo, usando el censo y el criterio del §1. *Salida:* lista firmada de masas a rebajar y excepciones aceptadas. *Congela:* la política; nadie toca niveles sin ella.
3. **Reconstrucción de niveles:** rebajar las masas seleccionadas al nivel del anillo, revisar bandas de río conectadas y separaciones, regenerar agua. *Salida:* censo nuevo con 0 masas colgadas > 0,3 m salvo excepciones, y `verify_terrain_v30` PASS. *Congela:* los niveles de agua (insumo de todo lo demás).
4. **Re-fit de orillas** (`fit_shore_crossings_v30.py`) sobre los niveles nuevos. *Salida:* desvío p50 ≤ 0,10 m / p90 ≤ 1,6 m global (las cifras del candidato H1: `evidence/v30-shore-crossing-candidate-2026-10-04/README.md:48`) y puertas PASS. *Congela:* la geometría del terreno.
5. **Cauces:** re-fit con encadenado canto con canto (sin `--overlap-all`, sin `overlap_from=None`), curvas con piezas curvas y deriva lateral; piezas solo en tramos con vértices mojados interiores; R2/R3 a planos o a la opción del §3 que se pruebe. *Salida:* `multi_share` < 5 % en tramos con piezas, heading p50 < 1°, lectura en motor 0 huecos (referencia: 100 % de concordancia y 0 huecos hoy, `evidence/v30-shore-crossing-candidate-2026-10-04/README.md:75-79`). *Congela:* piezas y tramos.
6. **Sesión única de decisión visual de arroyos** (surco + fondo oscuro frente a escalera del candidato), con capturas comparables. *Salida:* una opción elegida y archivada. *Congela:* agua, orillas y cauces juntos — este es el punto de no retorno.
7. **Navmesh + física + IA + lancha** sobre el mundo congelado (P9/P10; la NM anterior dejó 138 teselas cambiadas junto a orillas y la IA quedó parcial: `HANDOFF.md:11,17`). *Salida:* lancha PASS en navegables, IA/grafo sin fallos nuevos frente a línea base, casos `changed_bank` ejecutados (quedaron sin correr: `HANDOFF.md:11`). *Congela:* el mundo jugable.
8. **Terrain Builder** al congelar la base (`HANDOFF.md:14`, `product-spec.md:16`). *Salida:* importación TB sin diferencias de alturas, capas generadas, orientación confirmada (P1). *Congela:* base 1.0.

## 5. Fuera de 1.0

- **Perseguir la perfección visual de arroyos estrechos** más allá de una opción elegida: las tres vías del §3 son excluyentes; probar todas es dar vueltas.
- **Variante de calado 0,03 m:** exige rebajar una puerta y gana 5.212 m² poco visibles en todo el mapa (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md:159,205-207`).
- **Re-perfilado de costa de marea y delta:** ya está fuera de alcance esta noche (`:215`) y no bloquea P9 en cauces interiores.
- **Charcas pequeñas remotas del censo** (perched 0,3–0,6 m lejos de corredores): aceptar y registrar.
- **Ferroviario P15:** explícitamente «no ejecutar ahora» (`product-spec.md:21`).
- **Prueba de carga 80–100 jugadores (P7/BALTIC-008):** ya pospuesta a sector mapeado (`HANDOFF.md:18`).
- **Nuevas exageraciones de relieve P12** sobre zonas ya aceptadas: reabriría orillas y niveles.

## 6. Discrepancias con el orquestador

1. **Orden (I2c).** Estoy de acuerdo con «ver v2 primero», pero discrepo en agrupar las decisiones (a) y (b) tras una sola vista y una sola reconstrucción. Los niveles (b) *deben* ejecutarse antes del re-fit final de orillas y cauces: si se rebajan lagos después de calzar las orillas (H1 cambia 91.857 vértices, `evidence/v30-shore-crossing-candidate-2026-10-04/README.md:56`), el ajuste queda invalidado y se repite. Mi secuencia separa niveles → orillas → cauces como pasos congelables.
2. **Alcance de (b).** «Derivar los niveles de lago del terreno natural» sin cualificar es demasiado: el 82 % de las masas está bajo 0,3 m de perched (`census.json`, `perched_m_histogram`). Propongo re-derivación selectiva por clases del §1, no global.
3. **I3.** La afirmación «no hay buena solución con planos» es cierta solo si el tono del lecho es fijo. El surco libre con lecho oscuro es una tercera vía concreta y barata de probar (§3.1), aunque [SUPUESTO] hasta verla en motor.
4. **Umbral de (a).** «Ríos anchos» no es operativo; propongo el criterio de vértices mojados interiores (§2), que además excluye R2/R3 de forma automática y explica por qué R1 puede quedarse con piezas pese a su 58 % actual.
5. **Peso de la explicación de las costuras.** El orquestador da por buena la lectura de Guillermo (solapes de colocación). La evidencia la apoya (`bugs.md:27`, corrección del 04-10), pero las isolíneas de profundidad quedan «como alternativa sin confirmar» (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md:194`): si el re-fit canto con canto no elimina del todo las costuras, hay que volver a esa hipótesis antes de tocar más colocación.

## LO_NO_VERIFICADO

- No pude abrir ficheros del repo: todo lo citado procede del anexo literal del brief. Las citas de `tools/terrain/v30_common.py:88`, `tools/terrain/verify_terrain_v30.py:31` y `tools/terrain/build_v30.py:40,449-450` vienen del texto del brief, no del anexo: trátalas como [SUPUESTO] hasta re-verificación.
- I1: no existe comparación lago a lago entre niveles V29 y el terreno V30 (el orquestador lo marca como supuesto y sigo sin poder verificarlo).
- El efecto visual del fondo oscuro bajo una lámina de 0,10 m en arroyos con surco (§3.1): no probado en motor.
- Dónde vio Guillermo el agua inundada de BALTIC-016 (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md:132`) y la confirmación de las manchas con la superficie nueva (`bugs.md:28`): pendientes.
- La causa de las costuras de R2 (solapes frente a isolíneas de profundidad): la lectura de solapes es «la más probable», no demostrada; la focal real de las capturas es desconocida (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md:186,194`).
- Las vistas en motor del candidato v2 pulido: desplegado y sin ver (`HANDOFF.md:7,15`).
- Que Chernarus use efectivamente esa estrategia de encadenado fuera de las métricas de juntas medidas (la inferencia «gira dentro de piezas curvas» viene de las medidas de `joints.json`, no de un análisis del colocador vanilla).

FIN-DICTAMEN