**Veredicto: SOUND-with-fixes** para la unidad A offline. La unidad B no queda autorizada. Las correcciones son adiciones de lectura dentro del alcance de A; ninguna cambia umbrales, IDs ni veredictos.

**Comprobaciones que resisten refutación**

- Los conteos del plan (51 canales/47 puntos, 46/21, Ground 2658, Roadway 2638/20, agua 43, RV 5, Bullet 3) coinciden con `probe/result.json:2-29` y el diagnóstico.
- `discover_dry_road_effective_domain_20261028.py:57` etiqueta wet con W>H ignorando B, y `:50` sí usa B en Roadway. Cita exacta.
- `game.c:1197-1200` sólo declara nativos. `GetWaterSurfaceHeightNoFakeWave` devuelve "water or object surface". Nada define depth ni pond.
- Calibración: `CALIBRATION_PASS`, margen 0.03999, 289 vacíos. El consumidor exige .038–.042 (`dry_road_native_consumer_ev112.py:18`).
- Los FAIL de RV en 349/350/1425 son correctos: rama `rvshapes<=shapes` con haya ajena. 700/723: B>H+0.03, rama exige shapes no vacías, RV devolvió terreno con shapes vacías. No hay error del consumidor.
- Los dos secos 524/528 fallan sólo por `depth<=0` (`:44`); pond y sea son false.

**Hallazgos**

1. **[Alta] A no contiene el discriminador decisivo: ¿las caras de los 43 fallos de agua eran modificables por el generador?** `dry_bed_road_candidate_ev112.py:128-130` congela |q|<=4 y toda cara que toca agua, y `:146` aborta si una cara mojada cambió. Las filas 524, 525 y 723 tienen una cara de agua en `roadway_faces` (1850/1860), por tanto están congeladas por construcción. Además todos los IDs vértice fallidos tienen residuo 17 o 21 módulo 39 (524, 563, …, 801, 528, 567, …, 723), que con 39 columnas corresponde a q=±2, dentro de la franja fija. Si el mapeo id→índice de rejilla se confirma, B candidato = B anterior en todos los fallos de agua, luego "lecho que invade agua" no es regresión del candidato sino relación original kit/lámina o etiqueta. Esto es exactamente lo que el usuario pide distinguir y A hoy sólo dice "identificar qué caras cambiaron".
   Corrección mínima: en A punto 1 exigir, por ID fallido/incierto, la máscara `free`/`wet_faces`/`protected_faces` de `kit-118-inputs.npz` y `modified` del candidato, con verificación explícita del mapeo id↔(fila,columna,q); registrar para cada punto "congelado/modificable, B anterior, B candidato, W".

2. **[Alta] H2 y el gate seco presuponen que depth es relativa a la altura de consulta; 524 lo refuta.** H=6.8354, surface medida=6.8242 (igual a W, delta 1e-6), consulta en H+0.01 está 2.1 cm sobre la lámina y devuelve depth=+0.101 (`result.json:47362-47398`). En 525 (wet PASS) depth=0.317 no iguala W−H−0.01=0.165 ni W−B=0.299. La semántica es opaca y el plan lo admite, pero A punto 4 debe tabular el residuo depth − (surface − (H+0.01)) para las 2658 filas, positivos incluidos, como hecho offline. Además 524 (W−H=−0.0112) y 528 (−0.0172) caen 1 mm y 7 mm fuera de la banda `water_depth_numeric` [−0.01,+0.02] de `prepare_dry_road_full_native_20261028.py:39`. Registrar el dato; no ampliar la banda ni reetiquetar.

3. **[Media] El "segundo referente" de H1 no está nombrado.** El plan habla de "huella mojada del estado anterior y contrato de producto" sin artefacto ni hash. El estado anterior es la misma fuente defectuosa; las caras water_ext son producto; las protecciones del generador se derivan de ese mismo producto. Si el referente no es independiente (p. ej. corredor hidrológico de `local_corridor`, polígono fuente del río o marcado humano fijado antes de leer resultados), A debe declarar el referente INCONCLUSO en lugar de "contrastar etiquetas". Corrección: fijar en el plan el archivo y hash del referente antes de ejecutar A, o escribir que no existe.

4. **[Media] rv_normal nunca se analiza.** En 524 el impacto RV sobre lecho devuelve contactDir (0, −0.1156, 0), no unitario y descendente; los impactos sobre terreno (525, 700, 723) devuelven (0,0,0). El consumidor sólo valida bullet_normal. A punto 2 debe tabular rv_normal de todos los impactos RV con shapes del kit frente a terreno, incluidos los vecinos PASS de 700/723, como señal de winding/cara posterior. Sin afirmar mecanismo.

5. **[Media] Tautología max(H,B).** Reetiquetar wet := W>max(H,B) convertiría los 41 fallos y 14 inciertos mojados en secos, y el gate seco los volvería a fallar por depth>0 (0.19–0.96). No hay vía de PASS gratuito, pero la etiqueta quedaría definida por la misma B que se audita. Cualquier relectura con max(H,B) debe ser columna adicional EXPECT2 junto a la original, nunca sustitución. Añadir esta frase al plan.

6. **[Baja] Concentración espacial no registrada.** Los 43 fallos de agua y 700/723 están en x 8256–8267, z 8931–8942, un tramo de cs_kit_118_0000; los tres árboles en x≈8247. El plan debe constatar el tramo y la cara de agua compartida (1850/1860) para que A compare contra positivos del mismo tramo, no sólo contra los 96 PASS globales.

7. **[Baja] Diseño B: el rayo bajo de H3 debe aplicarse también a `GetWaterSurfaceHeightNoFakeWave`**, que parte de H+100 y devuelve "water or object surface" (`game.c:1199-1200`, `init.c:142`). Hoy no se detecta porque los tres puntos del haya son secos sin cauce.

8. **[Baja] Redacción línea 28.** El productor carga objetos en `init.c:104-111`, espera 100 ms y vuelve a cargar en `:114-116` en el frame de consulta. "Carga WRP en el mismo frame" es correcto sólo para la segunda carga.

**Respuestas a las preguntas del alcance**

- ¿A distingue consumidor equivocado de lecho que invade agua? Con el hallazgo 1 incorporado, sí distingue "regresión del candidato" de "estado original o etiqueta". No distingue "etiqueta errónea" de "defecto visual del kit original": eso requiere el referente del hallazgo 3 y, para pond, experimento nativo (B).
- Datos faltantes: B anterior por punto no está en las filas (sólo candidate_bed = effective_bed); mapeo id↔rejilla no verificado; referente independiente ausente; rv_normal sin tabular.
- Positivos: 525 es positivo natural adyacente a 524 con la misma lámina 6.8242; A debe emparejar así por columna/fila.
- Identidad: hashes de entrada presentes en diagnóstico y resultado; A debe pinear además `kit-118-inputs.npz`, el candidato y la extracción fuente.
- Rechazos confirmados: no podar árboles, no desplazar 700/723, no reetiquetar 524/528, no tocar tolerancias.

FIN_REVISION