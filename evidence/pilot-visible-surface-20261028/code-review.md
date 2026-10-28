**Veredicto: SOUND-with-fixes.** La extracción es fiel a las APIs reales, la cobertura 201/4 sitios está blindada y no veo vía de PASS falso. Hay un pin ausente y dos huecos de proveniencia menores que conviene cerrar antes de la única producción.

**Verificado contra fuentes reales (no sólo fixtures)**

- **APIs ODOL/py3d correctas.** `lod.vertices[].x/y/z`, `f.vertex_indices`, `lod_errors`, `lod_end_ok`, `proxies` existen en `odol_reader.py:622-768,935-1214`. En py3d, `Vertex.point` es propiedad real (`__init__.py:1822`), `Face.material/texture` (`:1855`), `P3D(f)` acepta fichero abierto (`:3002`). `LOD.resolution` se lee en `:2815`.
- **Topología de tira exacta.** `strip_faces` (`continuous_stream_pilot_v31.py:150-153`) genera exactamente `(a,a+m,a+m+1)` y `(a,a+m+1,a+1)`; coincide con `expected` de `strip_mapping` (`pilot_visible_surface_ev112.py:73-76`). `add_mesh` (`:110-122`) añade puntos en orden y sin soldar, con lecho antes que agua, luego `bed_point_layout` y `wp.reshape(-1,2,3)` son válidos. El volteo de winding de `add_mesh:99-101` no afecta porque la comparación de tira usa claves ordenadas.
- **CAP 8 filas.** `:345-362` de v31 añade 8 filas sólo si `start==0` / `stop==len(s)-1`, con tangente `(N_z,-N_x)` y distancias 1..8; `strip_mapping:68,87-93` reproduce signo y conteo. El redondeo doble a 1/512 (`:329` y `:363`) es idempotente para el cuerpo, así que la igualdad exacta cuerpo/agua NPZ es alcanzable.
- **Material/textura.** Las cadenas reales del ODOL desplegado (model-sections.json:108895-108950) coinciden tras `norm` con `BED_MAT/BED_TEX/WATER_MAT/WATER_TEX/BED_ROAD`. Las constantes de v31 (`:29-34`) son las mismas con barras invertidas.
- **Recentrado ODOL.** El centro registrado por A es múltiplo de 1/1024 (p. ej. -4.0107421875), y el consumidor de linaje consumido midió distancia máxima de marco 0.0 m sobre los 201. La equivalencia exacta sin tolerancia es factible; si falla, se reporta, no se bloquea ni se aprueba.
- **Pinning.** `HELPER_SHA` coincide con `script_sha256` de A. author-report.json y los 201 MLOD están en current-source-pins.json, así que sí quedan hasheados y rechequeados al final.
- **Cobertura.** author-report tiene 201 instancias (205 "site" = 201 + 4 informes de sitio). `coverage_guard` exige biyección autor↔catálogo `custom_pilot`↔poses, una pose por modelo, sin ids duplicados.
- **Presupuesto.** El consumidor de linaje parseó los 201 MLOD con py3d en 44 s; A parseó 5443 ODOL en 39 s. 600 s sobran.

**Bugs y fixes mínimos**

1. **Lector ODOL sin pin** (`pilot_visible_surface_ev112.py:167,179`). Se importa `odol_reader` desde `C:/temp/...` sin verificar hash; `discovery['reader']` (inputs.json de discovery:75) ya trae los digests y se ignora. Fix tras la línea 153:
   ```python
   for p,d in discovery['reader'].items():
       require(meter.sha(p)==d,'reader_changed:'+p); pins[p]=d
   ```
2. **Secciones Roadway no-lecho descartadas en silencio** (`:115-116`). `water_ext.paa` y cualquier textura inesperada caen en `continue` sin contarse; el plan pide "confirmar qué quedó fuera". Fix: `elif s['texture']==norm(WATER_ROAD): role='road_water'` y `else: role='road_unknown'`, inicializando ambos en `groups` y exigiendo `road_unknown` vacío o reportado en `faces`. Hoy sólo se infiere desde `sections`.
3. **Mapeo de filas incompleto para el consumidor** (`:217-218`). El payload guarda `body_row_*` en índices de `grid` (con CAP) pero no `start`, `before`, `after`; el consumidor tendría que reconstruirlos desde `station` del report. Fix: `strip_mapping` devuelve `start,before,after` y se añaden al payload como escalares (`npz_start, cap_before, cap_after`).
4. **Fallo sin contexto de modelo** (`:202`). `npz_body_not_source` aborta los 201 sin decir sitio/modelo. Fix: envolver con `try/except ValueError as e: raise ValueError(f'{e}:{name}')`.

**Notas (no bloqueantes)**

- La semántica CAP asigna a CAP_START el triángulo entre la fila 7 y la fila frontera 8 (y simétrico al final). Es coherente con `boundary_row` en el report; documentarlo en `limits`.
- Las claves de `prior` dependen de `str(Path)`; pasar `root` igual que en A. Si difiere, falla cerrado (`source_pin_missing_or_changed`), no abre.
- `oriented` entre ODOL y MLOD es informativo; `add_mesh` ya invierte winding por triángulo, así que una diferencia de orientación no implica geometría distinta.
- Tests: los 22 cubren sólo funciones puras. Añadir una fixture mínima de `odol_faces` con una sección Roadway de textura desconocida (para el fix 2) sería barato.

**Qué sigue:** aplicar fixes 1-4, un preflight ≤120 s, una producción ≤600 s con hash/PID, y recién entonces los consumidores H/W y corredor sobre `models/*.npz`.

FIN_REVISION
