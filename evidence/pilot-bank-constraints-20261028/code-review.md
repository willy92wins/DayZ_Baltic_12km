**Veredicto: SOUND-with-fixes.** Los cortes u/v/v‑u, la triangulación NW‑SE, los segmentos positivos sin epsilon, el montaje de 64 CAP reales y 201 modelos, el reparto de caras por clase/dominio y los pines están correctos y el consumidor GEOS es aritméticamente independiente. Tres hallazgos concretos, ninguno produce hoy un número falso conocido, pero dos pueden dar diagnósticos engañosos y uno deja un hueco de independencia.

**Lo verificado (sin hallazgo)**

- Cortes: `cuts()` en `pilot_bank_profiles_ev112.py:21-29` corta en u, v y v‑u enteros con extremos excluidos; coincide con el split `f>=g` de `native()` (:19), con `tri_h` de streambed_kit_v31.py:277 y con `bary_samples` del consumidor (líneas 14‑22, pesos 1‑max, |f‑z|, min). Diagonal NW‑SE en ambos.
- Positivos/alcance: `positive_interval` conserva longitud positiva pequeña; `dry = exposed ∩ (B‑Wreal>0)`; alcance evaluado en extremos del intervalo seco. El consumidor usa signo en punto medio y extremos de subintervalos; equivalente en afines. Orden de los 9 campos coincide (FIELDS ↔ índices 0‑8).
- Montaje: `start = npz_start + 8 − cap_before` (census:71) es correcto para cap_before∈{0,8}; `seen.all()`, `body_changed`, `discordant_shared_rows` cubren 4×16 CAP y juntas. `face_classes` indexa `ravel()` fila‑mayor igual que `source_triangles` (a=r·39+c).
- Máscara del ensayo seco: reproduce exactamente pilot_dry_bank_visual_floor.py:31‑56 (REQUIRED+OPTIONAL, s3_road_guard, `c2v(isfinite(plane))` ≡ desplazamiento 4 vecinos, disco 60 m, cap `min(st, L−st)≤6`, piso H+.02 / Wreal+.025, cuantización 1/512). `OR(interp(mask_i)>0)` ≡ `interp(OR mask)>0` por pesos no negativos. Estación del cuerpo empieza en 0 (continuous_stream_pilot_v31.py:184‑187), así que `station[-9]-station` del consumidor (:109) coincide con `station−lo` del productor.
- Candidato: `candidate_guard` exige claves iguales, no‑bed byte‑exactos y XZ del bed intactos; `candidate_changes_excluded_points` (:106) detecta máscara reproducida incorrectamente por defecto.
- Áreas: suma por cara conserva total con 1e‑10; cobertura global 185744; dominios WET/DRY_INNER/DRY_OUTER/BOUNDARY por columna nominal (2.25 vs 4), separados de la clase.
- Consumidor: no importa `cuts`/`native`/`dry_contract`; sólo meter de recursos y `s3_road_guard` declarado en limits. Cobertura GEOS por `union_all` = longitud. Triángulos (0,1,3)/(0,2,3) = NW‑NE‑SE / NW‑SW‑SE ✓.
- 14 fixtures presentes y coherentes con el plan.

**Fix 1 (diagnóstico engañoso): residuo transversal y anchura de sección calculados y descartados.**
`row_profile` devuelve `maximum_row_offaxis_residual` y `section_water_width` (profiles:88‑89) pero `pilot_bank_constraint_census_ev112.py:112-117` sólo guarda `metrics` y `crossings`. El plan (líneas 50‑52) exige conservar el residuo como diagnóstico. Importa porque el generador estrecha el agua en los primeros/últimos 6 m del cuerpo: `half=2.25*max(cap,.015)` (continuous_stream_pilot_v31.py:322), luego redondea a 1/512. Con anchura mínima ≈0.0675 m y bordes cuantizados a ≈2 mm, la dirección `normal` derivada de esos dos bordes puede desviarse varios grados; proyectar columnas a |q|≈18 m sobre esa normal altera `outer_reach` en el orden de centímetros y produce residuos transversales grandes que nadie verá. Además `edges=±width/2` se traslada al centro de la fila en vez de proyectar los bordes reales (profiles:55), y el consumidor replica la misma traslación (:71), así que no lo detecta. Fix: guardar por fila `section_water_width`, `maximum_row_offaxis_residual` y el desplazamiento del punto medio del agua respecto a la columna 19; resumir min/mediana/max en sites.json y etiquetar filas con width<4.5 (cuerpo) como dirección derivada de agua estrechada. Repro: en kit‑7, fila 8 (station 0) y fila 13, calcular `np.linalg.norm(water[1]-water[0])` y comparar `normal` con `N` del eje; el residuo off‑axis máximo de columnas ±18 excederá la cuantización.

**Fix 2 (procedencia): solver del candidato cableado sin pin.**
`census:88` escribe `candidate_solver=dict(success=False,iterations=500,bounds_satisfied=True)` como constantes. Hoy coinciden con `R/dry-bank-visual-water-pilot-20261027/author-report.json` (success false, 500, bounds_satisfied true), pero ese fichero no está en `pins`. La adjudicación Fix3 pide registrar el estado del solver; copiarlo a mano sin hash es una afirmación no verificable por el consumidor. Fix: `pin(author-report.json)` y leer `solver` de ahí; `require` de que `candidate_sha256` del informe == `CANDIDATE_SHA`.

**Fix 3 (independencia): el consumidor no re‑verifica el montaje.**
`verify_pilot_bank_profiles_geos_20261028.py:125-128` usa `offset` sólo para cortar `excluded`; nunca comprueba que `grid[offset:offset+n] == mf['source_grid']` ni que `grid[8:-8]` sea el `bed` sellado de `meta.ARRAYS`. Si el montaje del productor fallara de forma silenciosa (no hay vía conocida, pero el consumidor debe cubrirlo), los perfiles se reproducirían sobre una rejilla errónea y PASS. Fix: añadir ambas igualdades exactas en ese bucle y la equivalencia `water` cuerpo vs NPZ. Coste despreciable.

**Observaciones menores (sin cambio obligado)**

- `reasons` por motivo no son disjuntos: `floor_above_original`/`no_quantized_value` se evalúan en todos los puntos, incluidos húmedos y CAP (profiles:116‑117), así que los conteos de sites.json:142 sobre‑representan esos motivos. La exclusión total es correcta; conviene decirlo en `limits` o añadir conteos marginales.
- `inputs.json` del consumidor sólo lista sus 4+ ficheros; los pines upstream quedan cubiertos transitivamente por el hash de `I/inputs.json`. Aceptable.
- Tolerancias 1e‑9/1e‑7: el error de los puntos GEOS es ~1e‑12·|coord|, muy por debajo; cualquier fallo debe seguir siendo INCONCLUSO, no relajación.
- Presupuesto: productor con preflight estratificado y watchdog 600 s; consumidor sin preflight pero acotado por el mismo watchdog. Suficiente.

Ningún hallazgo contradice la adjudicación (máscara del ensayo seco, no v31 original; restricciones técnicas no equiparadas a decisiones humanas; candidato sólo kit‑7, otros SIN_CANDIDATO). Sin producción lanzada; sin escrituras por mi parte.

FIN_REVISION
