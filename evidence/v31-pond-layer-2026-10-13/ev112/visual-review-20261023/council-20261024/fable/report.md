# Council de COBERTURA — Controles de calidad EV112 (candidato R)

**Veredicto sobre LOS CONTROLES: SOUND-with-fixes.** Los oráculos leídos son en general fail-closed y honestos en su alcance. Pero la cadena de evidencia para R tiene tres huecos que impiden afirmar hoy que los controles juzgan al candidato correcto: no hay gate de contrato extremo a extremo sobre el terreno R, el revisor P11 del paquete apunta a otro terreno, y el consumidor de sonda no pinea el hash del terreno medido. Además, los oráculos geométricos no ven las tres patologías visuales reales (escuadras en planta, bancales de clamp, pirámides de menos de 20 grados).

## Tabla de hallazgos

| ID | Sev | archivo:línea | Defecto | Consecuencia | Fix |
|---|---|---|---|---|---|
| C1 | ALTA (vacío) | `review_continuous_stream_pilot_v31.py:92`; sin gate sobre R | Cada herramienta valida su paso contra `water-fix-b`, nunca el merge `road-merged-20261024-h`. El revisor del piloto congela solo reserve/platform/narva; omite bridge_cut/fill, dam, causeway, shore_ramp y el disco 015-45, que solo asegura el propio autor (`continuous_stream_pilot_v31.py:383`). | El contrato (XY, islas, disco 60 m, esquinas de estanque, relleno C2 de 11 vértices) no tiene oráculo independiente sobre el SHA d3d41a… | Gate `verify_candidate_contract`: diff R−B ⊂ (v31_relief_general ∪ v31_continuous_pilot ∪ máscara vial); diff ∩ (frozen ∪ disco ∪ esquinas pond ∪ shoreline) = los 11 vértices C2 exactos; `H<.75` idéntico; componentes secos idénticos; emite SHA de ambos. |
| C2 | ALTA (HIPÓTESIS hash) | `review_visual_roads_ev112.py:28-29` | Terreno fijado a `visual-merged-20261024-b/terrain-buried.npz` y hash de `forest-visual-consumers-20261024-a/inputs.json`, no a R. | Si "102 cadenas / 77559 estaciones" salió de este script sin editar, la evidencia P11 pertenece a otro terreno. | Parametrizar `merged`; exigir `terrain_sha256 == d3d41a…` en `review.json`; el verificador debe comprobar ese campo en el informe existente. |
| C3 | ALTA (hash sonda) | `eval_visual_probe_v31.py:105-108`; `eval_visual_road_probe_ev112.py:29-33` | `points.json` lleva hash del terreno (`prepare_visual_probe_v31.py:79`) pero el juez nunca lo compara con nada ni con el log. | Un log de Q (786/786) puede juzgarse como PASS para R; exactamente el riesgo "sonda histórica que no pertenece a R". | CLI `--terrain-sha256` obligatorio; `assert doc['inputs'][...terrain-buried.npz]==arg`; incluir el hash en la cabecera del log del init.c y verificarlo en `parse`. |
| C4 | MEDIA (cobertura retirada) | `verify_roads_v30.py:50,61,118` | Cadenas con <4 puntos o sin estación válida se descartan sin contar; no se emiten estaciones excluidas por motivo (agua/Narva/extremos). El margen de 18 m se aplica también a extremos libres sin cruce ni junction. | Las exclusiones pendientes no son visibles numéricamente; puntas de carretera muerta quedan sin oráculo sin razón de diseño. | Reportar `excluded={water,narva,ends,short_chains}` con estaciones y metros; clasificar extremos (libre / junction a <10 m de otra cadena / húmedo) y evaluar los libres; puentes y junctions como gates separados (ver D1). |
| C5 | MEDIA (vacío oráculo) | `review_visual_roads_ev112.py:20` | Máscara 1 m → vértices correcta solo si `water1m.npy` tiene fila 0 = norte, columna 0 = oeste; nada lo comprueba. | Espejo N-S silencioso desplazaría las exclusiones de 48 m: estaciones falsamente válidas junto al agua en una mitad del mapa. | `assert v[H<.75].all()` (todo vértice bajo mar engine es húmedo) y cobertura ≥99 % de `ref['wet']|ref['ocean']` de v33. |
| C6 | BAJA (bug legible) | `verify_roads_v30.py:77`; `smooth_free_relief_ev112.py:55,64`; `census_creases_v31.py:87` | Comparaciones `>lim` con NaN son False: un NaN en altura pasa como verde; en el relief un vértice NaN libre se propaga a la salida con OFFLINE_PASS. | Falso verde improbable (inputs pineados) pero gratuito de cerrar. | `assert np.isfinite(h).all()` en `load`/`evaluate` y en `checks`. |
| C7 | MEDIA (geometría no detectada) | `smooth_free_relief_ev112.py:53`; `despike_v31.py:238` | `np.maximum(…, floor)` crea bancales planos a nivel agua+0.30 / plano+0.35 siguiendo la curva de nivel. Crease de ángulo = pendiente local (<20°) invisible al diedro; no se reporta cuántos vértices quedaron recortados. | Terraza artificial contorneando orillas, justo donde el usuario ve el defecto "a altura media". | Reportar `floor_clamped_vertices` y longitud de su contorno; DESIGN D2 (suavizado con cotas). |
| C8 | MEDIA (backlog oculto) | `smooth_free_relief_ev112.py:80`; `census_creases_v31.py:88-90` | El collar retirado solo se cuenta; el census agrupa por dominio solo >20° y no mide prominencia. Una pirámide de 1 m sobre malla 6 m tiene diedro ≈19° y pasa. | El backlog protegido (lo que el usuario llama pirámides) no se enumera con coordenadas. | Volcar `rejected` y, por dominio y para `other`, prominencia >0.3/0.5/1.0 (`despike.prominence`) con x,z y ángulos >10°. Diagnóstico, no aceptación. |
| C9 | MEDIA (vacío ríos) | `inventory_visual_endpoints_v31.py:31,41`; `streambed_kit_v31.py:245-250,627-628` | Extremos = diámetro BFS del componente húmedo: 2 por sitio; brazos de confluencia no inventariados. Umbral `ph>g` sin margen frente a +0.10 m en las otras cláusulas. | "Extremos ausentes" en tributarios no entran en el inventario; una lámina de 1 mm cuenta como OFFLINE_COVERED. | Enumerar todos los tips de grado 1 del esqueleto; margen uniforme ≥0.10 m más profundidad mínima. Mutante: plano = g+0.001 → debe ser LOSS. |
| C10 | MEDIA (vacío ríos) | `review_continuous_stream_pilot_v31.py:87-91` | Solo se exige terreno intacto en esquinas de estanque; no se compara el plano nativo retenido bajo la franja del piloto con W(s). Anchura 4.5 m y `max_turn_per_m_deg` del autor no se consumen. | Doble superficie de agua (nativa + piloto) con escalón o z-fighting pasaría OFFLINE_PASS. | Para cada celda con plano finito que intersecte el polígono de agua: `|plane−W(s)|≤0.02` o celda retirada; leer y acotar el giro máximo del autor. |
| C11 | BAJA-MEDIA (bosque) | `review_visual_forest_support_v31.py:55,74`; `run_visual_forest_gate_v31.py` (g2g3/g7 en build, no leídos) | Escala por norma de la columna 0 solamente; sin ortonormalidad, escala uniforme ni rango; sin detección de instancias coincidentes; nombres solo contra JSON, no contra existencia del p3d. | Transformaciones defectuosas (cizalla, escala anisótropa, árboles dobles) pasan el gate de soporte. | `|det A|≈scale³`, columnas ortogonales, scale ∈ rango por modelo, pares a <0.3 m misma familia = fallo; existencia de `P:/<model>`. DESIGN D3 para distribución. |
| C12 | BAJA (binario) | `verify_compiled_stream_pilot_v31.py:50,60-62` | Solo cuenta caras de agua; caras de lecho no comparadas; KD-tree unidireccional ODOL→fuente no detecta vértices ausentes. | Lecho binarizado incompleto pasaría BINARY_PASS. | Contar caras de lecho igual que agua; consulta inversa fuente→ODOL con el mismo umbral. |

## Repros para los bloqueantes (sin ejecutar)

**C1.** Mutante: en una copia de R, sumar 0.01 m a un vértice dentro del disco `hypot(6c−10397.4, 12282−6r−9421.9)≤60`. Ninguna herramienta del paquete consume R con ese check: `smooth_free_relief` lo comprueba solo sobre su propia salida, el revisor del piloto no lo mira. Resultado esperado del gate nuevo: FAIL con la coordenada. Negativo: R sin tocar → PASS y diff ⊂ máscaras autorizadas.

**C2.** Leer `review.json` del informe P11 usado para R. Si `terrain_sha256 ≠ d3d41a8b…` o la ruta contiene `visual-merged-20261024-b`, la evidencia P11 no es de R. El script del paquete no puede producir otra cosa sin edición.

**C3.** Test: tomar el fixture de `tests/test_visual_probe_v31.py`, añadir `inputs={'…terrain-buried.npz':'aaaa'}` al doc y pasar `--terrain-sha256 bbbb`. Hoy devuelve SERVER_PROBE_PASS; debe devolver FAIL_INVALID_EVIDENCE.

## Propuestas DESIGN

**D1. Gates separados de puente y junction (P11).** Criterio: en el tramo 18–48 m hacia cada estribo (máscara `v31_bridge_fill`/registros de puente a 30 m), aplicar el mismo chord 3 cm/6 m sobre el perfil terreno→tablero usando la cota del registro, y en cada junction (extremos a <10 m de otra cadena) ptp del disco de 12 m ≤ 3 cm. Fuente de tolerancia: P11 vigente, sin relajar. Positivo: quiebro sintético de 1 % en el estribo → FAIL. Negativo: rampa plana con la misma pendiente del tablero → PASS. Coste bajo; limitación: no hay piezas físicas, solo reserva de plataforma.

**D2. Suavizado con cotas en vez de clamp.** Reutilizar `fair_support` (L-BFGS-B con bounds, ya probado en `test_continuous_support_v31.py`) por componente conexo de `eligible`, con `floor` como cota inferior. Criterio: cero vértices con `H==floor & H!=H0` formando líneas >3 celdas. Positivo: valle sintético con floor plano → sin bancal. Negativo: plano inclinado inalterado (ya testado). Coste: minutos por región; limitación: convergencia no es aceptación visual.

**D3. Distribución y textura de bosque.** Histograma de distancia al vecino más próximo y de rumbo del vecino por familia, comparado con Livonia leída con el mismo `wrp0wzd.read`. Criterio: picos de rumbo en 0/90° > 2× la media señalan rejilla; CV de distancia fuera del rango Livonia ±20 %. Positivo: colocación en malla 6 m → FAIL. Negativo: muestreo Poisson → PASS. Coste moderado (2.56 M instancias, cKDTree); limitación: no juzga apariencia ni rendimiento.

**D4. Censo de angularidad en planta de cauces no pilotados.** Desde el `lattice` de `kit-report.json` por sitio: giros de 90° por 100 m, radio mínimo, banda de cota W. Referencia: el eje spline del piloto. Diagnóstico de backlog, no aceptación. Coste muy bajo.

## Clasificación

- **Bug comprobable por lectura:** C3, C6, C9 (margen), C12.
- **HIPÓTESIS:** C2 (depende del informe real), C5 (convención del raster), semántica NaN de `geom.disc_min` para `sea_band` (C11).
- **Vacío de cobertura:** C1, C4, C7, C8, C10, C11, D1–D4.
- **Mera forma:** `review_visible_pilot_relief_v31.py:100` revienta con cero filas en vez de emitir DIAGNOSTIC vacío; `eval_visual_probe_v31.py:41` exige reloj estrictamente creciente en ms (falso inválido, no falso PASS); `verify_roads_v30.py` carece de test unitario propio, a diferencia del consumidor de sondas.
- **No reclasifico como falso PASS global:** `review_visual_roads_ev112` status PASS con scope explícito, `inventory` INVENTORY_NOT_ACCEPTANCE, `read_presentmon` DESCRIPTIVE_ONLY: ningún consumidor del paquete infiere aceptación de ellos.

## Empaquetado, navmesh, runtime

No existe en el paquete evidencia motor, render ni benchmark para R; la sonda 786/786 es de Q y C3 impide hoy distinguirlas por hash. Navmesh antigua y MCP inaccesibles: coincide con el checkpoint, nada que declarar. `forest_arrays` sí vincula el WRP al terreno R por igualdad de alturas (`review_visual_forest_support_v31.py:21`), lo que es correcto.

## LO_NO_VERIFICADO

- Orientación de `water1m.npy` (fila 0 norte) y de `wsea1m/bog1m/slot1m`.
- Semántica NaN de `geom.disc_min` y `geom.h_at` (`forest-final-tools/r2/gates`, fuera de tools/tests).
- Contenido de `g2g3_map`, `g7_map`, `g8_agreement`, `recio` (directorio de build).
- Que el informe P11 de R provenga de `review_visual_roads_ev112.py` y su `terrain_sha256`.
- `kit.site_axis` para sitios con `mode` distinto de component; `sites-d.json`.
- Si `visual-merged-20261024-b` y `road-merged-20261024-h` comparten terreno por hash.
- Contenido de `tests/test_presentmon_evidence.py`, `test_water_probe_controls.py` y resto de tests no incluidos.

END_COUNCIL