**Hechos verificados**

1. **Contrato de anchura realmente autorizado.** El único texto aprobado es plans/ev112-visual-rework-20261023.md:29: “conservar anchos/clases, extremos y receptores”, sin cifra ni distinción visual/física. La cifra 4.5 m sólo existe en el código del autor: continuous_stream_pilot_v31.py:289 (“the approved stream width stays 4.5m”) y :321-322 (`half=2.25*cap`). El plan de orilla seca (ev112-dry-bank-domain-pilot-20261027.md:26) la hereda como invariante del ensayo, no la aprueba como producto. product-spec.md:15 (P9) fija 24 m/0.95 m sólo para corredores navegables; P2 (:8) y P14 (:20) exigen agua funcional y bajos sin agua indeseada, sin anchura. Conclusión: existe autorización de **conservar** anchos, no de qué anchura (lámina visual o agua física) es el contrato.

2. **El modelo genera por diseño lecho por encima del agua física en |q|=2.** Perfil continuous_stream_pilot_v31.py:300: `cross` interpola (1,−.6)→(2.25,0), luego bed(q=2)=W−0.12. El agua física es la lámina menos 0.25 (:384, `wflat-[0,.25,0]`). Diferencia: 0.13 m, exactamente los 0.127–0.131 de las filas vértice (report.json:53,100,147…); los centroides (q entre 2 y 2.25) dan 0.163–0.211. report.json:22-27 lo confirma analíticamente: línea de agua física en |q|=83/48=1.73 m, anchura física 3.46 m, visual 4.5 m. Es el **modelo autorizado comportándose como está escrito**, no una deriva de cuantización.

3. **El oráculo etiquetó wet con W_phys>H ignorando B** (plans/ev112-dry-road-native-discriminators-20261028.md:33-34). Las filas lo ratifican: 524/528 (dry) tienen H>W_phys por 1.1–1.7 cm; las 41 wet tienen H<W_phys. Ningún punto de los 43 tiene B cambiado ni cara protegida (`height_changed:false`, `protected_faces:[]`).

4. **El juez es insatisfacible por construcción para wet con B>W_phys.** eval_visual_probe_v31.py:90 exige depth>0 y :92 exige road≈max(bed,water_ext,ground); dry_road_native_consumer_ev112.py:43 exige pond∧depth>0 y :49 roadway esperado=max(ground,bed). La profundidad se muestrea en H+0.01 (discriminators:29), bajo el lecho. Con B≥W_phys+0.03, si el motor dice “agua” falla roadway/depth y si dice “seco” falla water: **los 41 wet fallan con cualquier comportamiento del motor** y por tanto no discriminan API frente a modelo. Esto no es reclasificar: la etiqueta se conserva, sólo se constata que etiqueta y modelo son incompatibles.

5. **Los 2 dry (524/528) son el único subconjunto que interroga al motor**: H+0.01 queda 2–3 cm por encima de W_phys y aun así el servidor devolvió agua. Están a 1.1–1.7 cm del umbral de 5 cm del juez; no afirmo causa.

6. **Referentes anteriores independientes y sus límites:**
   - Pre-kit (stream_reference_v31.py:8-10 PINS; :35 `wet=H<vp` en malla de 6 m): recupera extremos/componentes (:27-48), resolución 6 m. No puede adjudicar 0.13 m en |q|=2 (trace-addendum:4-6).
   - Kit: streambed_kit_v31.py:187-188 `SEAT0=-0.33, HW=1.8`; HW es la semianchura donde terreno=roadway+0.25 (línea visible); la física (terreno=roadway) cae en 0.33/0.322≈1.02 m. Constante del generador, no medición (trace-addendum:7-9).
   - Vanilla Chernarus: REPORT.md:65 roadway 2/3/3.5 m, visible 3/4/5.5 m (inferido); stream_sections.json:263-265 asiento mediano −0.33/−0.03/+0.33 a 0/1/2 m. En vanilla, a 2 m del eje el terreno está 0.33 sobre el roadway y 0.08 sobre la lámina visible. Son medianas de otro mapa: informan la decisión, no adjudican puntos.
   - W>max(H,B): candidato autorreferente, sólo columna EXPECT2 (discriminators:125-127; trace-addendum:18).

**Hipótesis (sin cerrar historia)**

- H-O (oráculo): los 41 wet son incompatibles con el perfil autorizado; su fallo es información sobre el contrato, no sobre motor ni geometría.
- H-A (API/numérico): 524/528 reflejan lectura de profundidad/superficie en frontera de 1–3 cm (oleaje falso, muestreo H+0.01 o cuantización WRP 1/1024), indeterminado.
- H-M (modelo): la pregunta de producto real es si un lecho visible 1.73<|q|<2.25 bajo lámina pero seco para el motor es “orilla saliente” (KIT118-VIS-01/CONT65-VIS-01, visual-rework:62-64) o comportamiento vanilla aceptable (stream_sections:265). Ninguna métrica actual lo decide.

**Propuesta única: partición mecánica oráculo/API/modelo, offline, sin motor**

Entradas (hash fijado): selected-points.json de discriminators-a, result.json de dry-road-full-native (2658), *-surfaces.npz del piloto, códigos del juez (eval_visual_probe_v31.py, dry_road_native_consumer_ev112.py), stream_sections.json, constantes kit.

Cálculo por cada uno de los 43 (y, sin coste, por los 2658): q, H, B, W_vis, W_phys ya disponibles en report.json; asignar exactamente una clase:
- **ORACLE_UNSAT**: expect=wet ∧ B ≥ W_phys+0.03. Prueba mecánica: ejecutar `evaluate`/`judge` sobre dos filas sintéticas (motor dice agua con road=B; motor dice seco con road=B) y comprobar que ambas devuelven FAIL. Mutante que debe pasar a satisfacible: B’=W_phys−0.01 con fila sintética “agua”. Se usa el juez existente, no una reimplementación.
- **BOUNDARY_NUMERIC**: |H+0.01−W_phys|≤0.05 o |B−W_phys|≤0.03, no cubierto por ORACLE_UNSAT. Candidatos API; aquí caen 524/528. Sin nueva consulta al servidor.
- **DISCRIMINATING**: resto. Si queda algún FAIL aquí, es el único sitio donde cabe hablar de modelo o motor.

Controles: positivo = punto centro (q=0, kind `centre`) PASS original con B<W_phys: fila sintética “agua” pasa, “seco” falla. Negativo = punto `dry_bank` (|q|≈6) PASS original: inverso. Ambos se evalúan con los mismos juzgadores.

Observables adicionales descriptivos (no PASS): por sitio, anchura física real tras cuantización y taper (intersección bed/W_phys por estación, min/p50/max), comparada con 3.46 analítico, con HW-kit 2×1.02/2×1.8 y con vanilla 2/3/3.5 y 3/4/5.5. Esto da al usuario el dato para decidir sin medir en juego.

Criterio de terminación: los 43 quedan en una clase y sólo una; ORACLE_UNSAT demostrada por ejecución del juez; dos controles con resultado esperado. Cualquier fila que no encaje → NEEDS-WORK de la unidad, no del mapa. Salida: nuevo directorio en R con CSV de 43 filas + 2658 anotadas, hashes, script. Presupuesto: un script, <15 min CPU, sin build, sin servidor, sin tocar etiquetas, tolerancias, protecciones ni superficies.

Límites: no demuestra que el motor lea bien el agua bajo el lecho; no repara nada; no valida naturalidad visual; no cubre los 4 FAIL restantes (47−43) ni los 20/21 inconclusos de roadway.

**¿Camino autónomo o decisión nueva?**

La unidad anterior es autónoma y cabe en el encargo. Lo que **no** resuelven las autorizaciones previas y requiere decisión de producto NUEVA antes de tocar el núcleo:

“¿Qué anchura se conserva: la lámina visual (4.5 m, código del autor) o la anchura física para el motor (3.46 m), y es aceptable que entre 1.73 y 2.25 m del eje haya lecho bajo la lámina pero seco para el motor?”

Razones: visual-rework:29 sólo dice “conservar anchos”; P9 habla de 24 m; P2/P14 no cuantifican; el piloto seco congela el perfil |q|≤2.25 (dry-bank:26) justo donde está la contradicción. Las opciones excluyentes son: (a) bajar el lecho a ≤W_phys−ε hasta |q|=2.25 (cambia el núcleo congelado, el perfil y potencialmente la protección de agua); (b) definir el oráculo wet como W_phys>max(H,B)+margen (hoy prohibido como reclasificación); (c) encoger la lámina visual a la anchura física. Elegir una es producto, no medición. La partición propuesta entrega los números para esa elección sin asumirla.

**Riesgo residual**

El juez agrupa en la clase BOUNDARY_NUMERIC usando sus propios umbrales (0.03/0.05); si el mecanismo nativo de muestreo bajo lecho (H2 de discriminators:47) fuese distinto, parte de DISCRIMINATING podría ser ruido de API y no de modelo. Las comparaciones con vanilla son de otro mapa y por medianas. Nada aquí acredita naturalidad de orillas ni cierra KIT118/CONT65.

**Veredicto de viabilidad de la siguiente unidad: SOUND-with-fixes.** Las correcciones: usar los juzgadores existentes en vez de fórmulas nuevas, fijar hashes de entradas antes de ejecutar, y registrar la decisión de producto pendiente como bloqueo explícito de cualquier edición del núcleo.

FIN_RESEARCH