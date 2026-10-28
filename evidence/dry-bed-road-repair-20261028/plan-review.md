**Veredicto: SOUND-with-fixes.** Una corrección es bloqueante (contraejemplo ejecutable abajo); el resto va al backlog. El mecanismo (LP sobre descensos con restricciones lineales en vértices del refinamiento) es correcto; el conjunto fijo tal como está escrito hace INFEASIBLE el único objetivo conocido.

**Verificado contra fuente**

- `continuous_stream_pilot_v31.py:313-319`: piso `ground+.02` para `4<|q|<18` sin excluir corredor; techo `ground+.02` sólo sobre `protected`; `fair_support` congela filas `[0,-1]` y columnas `[0,-1]` del cuerpo. `:349/:358`: CAP a `ground-.03` sólo en distancia 8; distancias 1..7 interpolan desde la fila 0 sin piso ni techo. `:403` conserva H protegido. Todo coincide con §1.
- La transición 12 m está en `:259` (`blend`) y comentario `:261`, no en `:269` (ese es el `burrow`). Corregir cita.
- `pilot_surface_refinement_ev112.py`: B, H y W son lineales en cada polígono de refinamiento, luego comprobar `sum(bary·d) >= B-H+margen` en los vértices del polígono es exacto. La formulación LP de §2 es sólida. Rebajar B sólo reduce B−H: la afirmación "no crea solapes nuevos" es cierta.
- `report.json` del discriminador: 23.9567 m², 0 agua A, 0 nativa nominal, 4.825 m a las 27 caras próximas, 5 instancias broadphase. Coincide con §1.

**BLOQUEO 1: fijar "primera fila del cuerpo" y "primera fila CAP" vuelve INFEASIBLE el objetivo kit118.**

De `geometry.json` (footprint de `cs_kit_118_0000`): la fila s=0 es el segmento A=(8269.355,8919.863)→B=(8246.867,8938.996); tangente t=(0.648,0.762); el CAP se extiende hacia −t. Distancia firmada de vértices del polígono `exposed_conflict` respecto a esa recta: (8262.50,8922.00)→−2.81 m (lado CAP, filas distancia 1–3); (8268.79,8924.88)→+3.46 m (cuerpo, filas 0–4); (8268.59,8920.51)→0.00; (8269.02,8920.15)→0.00. Para x=8266 la recta de fila 0 pasa por z≈8922.72, que está dentro del polígono (que ahí abarca z 8921.9–8925.1). Es decir, B>H sobre la propia arista de la fila 0, donde B depende sólo de vértices de fila 0. Con fila 0 fija (y más aún con fila CAP distancia 1 fija), ninguna d≥0 satisface B−H≤1e-9: el plan devuelve INFEASIBLE con testigo y no hay candidato, que es lo que no queremos.

Contraejemplo ejecutable: cargar `exposed_conflict` de `R/road-bed-water-discovery-20261028/geometry.json`; cargar `source_grid` de `R/pilot-visible-surface-extraction-20261028/<kit_118_0000>.npz` (fila `body_row_min`, xz); `LineString(fila0).intersection(Polygon(exposed)).length > 0` ⇒ con la regla §2 "fijar primera fila del cuerpo + primera fila CAP" el sistema de restricciones es inconsistente. Si da 0 me retracto.

Corrección: redefinir "extremos" como (a) vértices de toda cara que toque agua propia, incluido el ápice en s=0 (ya cubierto por la regla de agua), (b) fila CAP distancia 8 (única fila a `ground-.03` por construcción), (c) columna exterior ±18 (nominal; física es `apron`). No fijar fila 0/última del cuerpo ni CAP distancia 1 por sí mismas. XZ, agua y P[0] siguen intactos, que es lo que la petición original pide conservar. Para sitios cuyo solape no toque extremos, la regla no cambia nada.

**Fixes no bloqueantes (una sola ronda)**

1. **Congelar también `|q|<=4`**, como `bed_free` del generador. Las columnas 3–4 son banco húmedo a W+0…0.4; el LP de gradiente puede rebajarlas bajo W junto a la orilla fija y dejar agua "flotante". El solape está en |q|≈6–14.5 (eje P[0]=(8258.1,8929.4)), así que no estorba.
2. **Acotar la puerta "corredor afectado B−H≤1e-9"** a caras semilla ∪ modificadas. `source_conflict_area` 112.79 vs expuesta 23.96 indica ~89 m² de corredor con B>H bajo W nominal (H≤W por el `burrow` a W−.95). Esas caras quedan congeladas por la regla nativa y seguirán con B>H; si la puerta las incluye, falla siempre. Reportarlas aparte como "no en alcance, bajo agua nominal".
3. **Preflight de factibilidad antes del LP**: listar caras semilla que caen en el conjunto fijo (agua A, nativa H≤W, 015, extremos) y vértices de refinamiento con soporte totalmente fijo y B−H>0. Si no está vacío, INFEASIBLE inmediato con testigo. Riesgo concreto: el borde del polígono expuesto hacia el eje (d≈−2.8) probablemente coincide con la línea H=W; una cara que la cruce y además esté expuesta es testigo seguro. Si ocurre, la siguiente decisión (política sobre agua nominal no desplegada) es del usuario, no se afloja en esta ronda.
4. **"Toca agua"**: definir como intersección XZ de área positiva o contacto de borde entre la proyección de la cara y la huella de agua, y para nativa como algún vértice del refinamiento con H−W≤0 (incluidos vértices de corte). Sin esto el productor y el consumidor pueden discrepar.
5. **Métrica de terreno que atraviesa el lecho**: el descenso crea cruces B<H nuevos en la transición (lo que `:309-311` quería evitar). Reportar área y localización de B<H nuevo dentro del dominio, sin umbral.
6. **LP lexicográfico**: fijar tolerancia explícita para "manteniendo ese óptimo" (p. ej. g* ·(1+1e-9)+1e-12). Cuantización hacia abajo preserva todas las restricciones (monótonas en d); confirmar que el consumidor lo comprueba tras redondeo, no sobre d real.
7. Citas: `:269`→`:259`; "q=±18" → "columna exterior (qactual=apron)".

**Backlog**: mutante "vértice de fila 0 fijo" como control negativo del fix bloqueante; parte del dominio 12 m cae en `_0012`, el plan ya exige unión de filas por sitio, el test de junta debe usar ese caso real.

FIN_REVISION
