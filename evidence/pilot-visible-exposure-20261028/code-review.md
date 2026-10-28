**Veredicto: SOUND-with-fixes.** El censo mide lo que el plan pide y las APIs reales cuadran; hay tres guardas ausentes y huecos de fixtures que conviene cerrar antes de producción. No hay falsos PASS en la matemática revisada.

**Verificado contra APIs/datos reales**

- Kernel: `refine`/`sign_regions`/`clip`/`plane`/`evaluate`/`triangle_intersection` existen con esas firmas en `pilot_surface_refinement_ev112.py`. `plane` falla cerrado con condición ≤1e-12; `clip` sin epsilon; área de refinamiento verificada por `require`.
- Meter: `bounded`, `dump(allow_nan=False)`, `sha`, `memory` (PID real), `MAX_SECONDS/MAX_BYTES` leídos como globales en tiempo de ejecución, así que sobreescribirlos tras importar funciona.
- Productor Visual201 escribe `bed`, `water` (n,4,3), `bed_n`, `water_n`, `bed_flags`, `water_flags`, `bed_source_face`, `source_category` con valores `BODY/CAP_START/CAP_END` (`pilot_visible_surface_ev112.py:83-86,221-226`). Report sellado: 201 modelos, 0 ambiguos, 0 no mapeados, 185744/4760 caras.
- Road reference: `edges` de 3 columnas (a,b,longitud) y `xy` en marco mundo (x,z) con fila = (top−z)/6, igual que `tri[:,(0,2)]` del lecho (`road_water_contacts_ev112.py:47-52,113`). Hash 94ecbca6 coincide.
- Manifest `artifact-hashes.json` usa claves relativas a root en posix con `sha256`; `p.relative_to(root).as_posix()` las resuelve bien.
- Índices NAMES: 11=min_B_H, 12=max_B_H; `NAMES[:11]` son exactamente las áreas. Correcto.
- NaN en deltas de agua sólo van al NPZ, nunca a JSON (allow_nan=False no se dispara).
- `union_all([])` → colección vacía; intersección/diferencia con ella da área 0 sin excepción.

**Matemática comprobada**

- Rectángulo ±4m exacto; 48 m² analíticos del test correctos (∫₂¹⁰(12−z)dz).
- Disco: inscrito r=4, circunscrito r/cos(π/64); exceso radial 0.004824 m, coincide con el plan. Anillo = (outer−road)−(inner−road), nunca sumado como libre.
- Capas de agua: `under` y `actual_footprints` se unen por parte antes de sumar; las partes son disjuntas, así que no hay doble conteo. Deltas 1.25/2.25 correctos frente a nominal 0.75 marino.
- Sumergido ≠ invisible: `above_H_area` no se reduce por agua; sólo se desglosa.
- Contacto: diff==0 en vértices ⇒ planos idénticos en la parte (dos planos que coinciden en 3 puntos no colineales coinciden en todo). `contact_area` no se solapa con above/below.
- Cortes de rectángulo/disco: como el resultado se interseca con `eg ⊂ foot`, consultar sólo rects/discos cuyo bbox toca `foot` no pierde área.

**Bugs/fixes mínimos (SOUND-with-fixes)**

1. `pilot_visible_exposure_ev112.py:29` — `rect` divide por `norm(d)`; una arista de longitud 0 produce NaN silencioso en Shapely. Fix: `require(np.linalg.norm(d)>0,'zero_length_road_edge')`.
2. `pilot_visible_exposure_ev112.py:120-121` — el grafo vial no se valida (este script no usa `graph_guard`). Fix mínimo: `require(edges.ndim==2 and edges.shape[1]==3 and xy.shape==(36428,2) and len(edges)==36467 and np.isfinite(xy).all() and (edges[:,:2]>=0).all() and (edges[:,:2]<len(xy)).all(),'road_universe')`, mismo universo que B (124/36428/36467).
3. `pilot_visible_exposure_ev112.py:154,166-167` — `exposed_union_area`/`exposed_components` mezclan BODY y CAP, contra "CAP separados del cuerpo" (aggregates sí los separan). Fix: construir `exposed` por categoría y emitir `exposed_components` por categoría, o etiquetar explícitamente el campo como `all_categories` en el summary y en `limits`.
4. Costo (`:140`) — preflight no mide tiempo por cara. Estimo 1.5–3 ms/cara (refine en Python puro + ~15 llamadas Shapely por cara) ⇒ 280–560 s para 185744 caras: muy ajustado a 600 s. Fix mínimo sin censo: en preflight cronometrar `regions_for_face` sobre las primeras 100 caras del primer modelo (descartando resultado) y escribir `estimated_seconds` en cost.json; si supera 600 s, parar en preflight como INCONCLUSO en vez de quemar producción.

**Comportamientos aceptados pero que hay que dejar escritos**

- Fallo cerrado global: una sola cara de lecho con proyección casi degenerada (p. ej. un CAP vertical) aborta toda la producción vía `plane` en `refine:68`. Coherente con el plan; `models/*.npz` y `progress.json` ya escritos se conservan, `models.json` no. Debe constar en el plan como salida INCONCLUSO esperada.
- `exposed_components` por redondeo de cortes en aristas compartidas puede fragmentar la unión; el plan ya lo dice.
- El árbol de agua es global a los 201 modelos (agua de un modelo vecino puede cubrir el lecho de otro). Es correcto para exposición, pero `intersecting_visual_water_faces` referencia índices globales en `water_refs`; el consumidor debe usar esa tabla, no el índice local.
- La ruta del road reference está hardcodeada al checkout primario (`:116`), no al worktree. Aceptable por hash, pero documentarlo.

**Fixtures que faltan (añadir a `test_pilot_visible_exposure_ev112.py`)**

- Junta/extremo dentro de la cara: carretera (3,3)→(6,3) con triángulo grande; asertar `corridor_disc_inner_above_H_area>0`, `corridor_disc_uncertain_above_H_area>0`, y `rect+inner+uncertain ≤ above_H_area`; cota analítica: inner ≤ 2·(semicírculo inscrito 64-gono = 32·sin(2π/64)·4²/2 … ) y uncertain ≤ outer−inner analíticos.
- Agua Visual bajo el lecho (y=0.5 bajo lecho y=1): `above_H_at_or_below_visual_W_area==0`, `intersecting_visual_water_faces==1`, `above_H_without_visual_W_footprint_area==0`.
- Cobertura parcial de agua: cara de agua que cubre la mitad del triángulo; asertar 36/36 entre at_or_below y without_footprint.
- Lecho casi degenerado propagando `NEAR_DEGENERATE` a través de `regions_for_face`; cara de agua casi degenerada con corte no nulo también.
- Arista vial de longitud cero rechazada (tras fix 1).
- Agregación por categoría en `run`: hoy `run` está sin test; un fixture mínimo con `source_category` mezclado verificando que `aggregates` separa CAP y que `min_B_H/max_B_H` usan columnas 11/12.

**Alcance/excepciones**

- Status `SOURCE_RELATIVE_VISUAL_EXPOSURE_DIAGNOSTIC` y `limits` no reclaman reparación, viabilidad ni render; correcto.
- No se pide cliente ni motor; el diagnóstico queda relativo a terreno fuente 815ef8b7 y agua nominal 084171b0.
- Candidato seco y viabilidad de restricciones siguen fuera, como exige el plan.

FIN_REVISION
