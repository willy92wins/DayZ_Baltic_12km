**Veredicto: SOUND-with-fixes.** El diseño del consumidor y del compositor respeta la adjudicación (allowlist semántica en lugar de unión de deltas, `+4` en `size_of_rest_data`, soporte ST por anillo de caras, `area_over_tex` marcado INCONCLUSO, codeword de 10 bits exacto, bits altos ST no interpretados pero preservados, estados nunca PASS de mapa). Encontré un falso FAIL casi seguro, dos fragilidades que convertirían una ejecución limpia en `wrong_rejection`/`gate_code_changed`, y dos literales que la adjudicación pidió derivar. Ninguno exige conocer Binarize.

**Contrato API verificado contra el código real**

- `ODOL.from_file(strict=True)`, `lod_end_ok`, `declared_end`, `vertex_raw`, `normal_raw`, `st_raw`, `uv_sets[].uv_raw/uv_data/default_fill`, `sections[].area_over_tex`, `model_info.bounding_center/center_of_mass/inv_inertia` existen en `odol_reader.py` fa0d74b6. LOD y ModelInfo usan `__dict__`, Section/UVSet/Polygon usan `__slots__`: `normalized` cubre ambos, así que la allowlist es exhaustiva y no hay campo decodificado que escape.
- La instrumentación (gate líneas 44-48) inserta una sola línea tras `lod.size_of_rest_data = reader.read_uint32()` (lector línea 698) en un módulo en memoria; el lector instalado queda intacto y pineado por hash.
- Regla `size_of_rest_data == declared_end − probe + 4` coincide con `dry-road-review-claims` (reported = actual + 4 en los 16 LOD).
- Allowlists de LOD0/1/3 y de model_info coinciden exactamente con `candidate_lods` y `candidate_modelinfo_changes` del análisis compilado.
- `read_pbo` devuelve `(data, props, entries)` con dict ordenado nombre→bytes, y la sintaxis FileBank `-property k=v … -dst dest source` es la ya verificada en `attach_navmesh.py:106`. FILEBANK_SHA coincide con `inputs.json`.
- `py3d` no está en el worktree; los atributos `facenormals/normal_index/point_index/material/texture` son los mismos que ya consumió `verify_dry_road_mlod_ev112.py`, así que no es un contrato nuevo.
- Las comprobaciones ST (anillo, `B[N&~ring]==D`, `B[ring&~N]==C`, 721 slots constantes en los 4 builds, quiralidad por signo del determinante, envolvente de control) reproducen los seis invariantes de `dry-road-st-neighborhood`. El bloqueo de bits altos (línea 77-78) es un requisito adicional: si fallara sería FAIL honesto, no falso PASS.

**F1. Falso FAIL seguro en LOD2 (Memory), gate líneas 135-137 y 50-52.** `rest_data_offset_probe` es una posición absoluta del archivo y queda en `vars(lod)` de los cuatro LOD, pero sólo se permite en 0, 1 y 3. El lector documenta (línea 839-846) que los LOD se almacenan con inicios decrecientes, es decir Roadway (LOD3) primero y Memory después. Como LOD3 cambia de tamaño (10111→10103) entre control y candidato/Y, el probe de LOD2 se desplaza y `known_fields` lanzará `candidate:LOD2:unknown_fields:rest_data_offset_probe` aunque el LOD sea idéntico (el análisis dice `changed_fields: []`). Corrección mínima: en `known_fields` descartar la clave antes de comparar, igual que hace `stripped`:

```python
a,b=normalized(control),normalized(other)
for d in (a,b):d.pop('rest_data_offset_probe',None)
```

y eliminar el bucle de la línea 137. El probe sigue usándose en la línea 144, que es su único propósito.

**F2. Mutante `water_face_height` frágil, test líneas 44-45.** Suma 0.25 en float64 al `Vector3P.y` y por separado en float32 al `vertex_raw`. Si la Y del vértice de agua tiene ulp menor que la del resultado, ambos redondeos difieren y el gate rechaza antes por `decoded_vertex_raw_mismatch` (gate línea 101), que `reject` registra como `wrong_rejection` y aborta toda la batería. Corrección: calcular una sola vez en float32 y asignar el mismo valor a ambos:

```python
raw[i,1]=np.float32(raw[i,1]+np.float32(.25));m.lods[0].vertices[i].y=float(raw[i,1])
```

**F3. Clave de identidad del gate no normalizada, gate línea 167, package línea 14, test línea 14.** Se usa `str(Path(__file__))` mientras `HERE` usa `.resolve()`. Si el gate se ejecuta con ruta relativa o distinto case/forma 8.3 y luego el compositor lo importa con ruta resuelta, `pins.get(...)` devuelve None y salta `gate_code_changed` sin que nada haya cambiado. Corrección: `Path(__file__).resolve()` en los tres sitios.

**F4. Literales que la adjudicación pidió derivar.** `geometry_preserves_numeric_certificate=True` (gate línea 184) sólo está respaldado por la cadena de 21 filas de la línea 177; conviene sustituirlo por el conteo real (`numeric_to_MLOD_rows_checked=grid.shape[0]`) o renombrarlo como condicional. `measured_control_envelope_preserved=True` (línea 84) sí está derivado por excepción en `check_frames`, aceptable. `dependency='Y_ONLY'` está respaldado por la línea 91. `water_section_exact=True` por la línea 88.

**F5. Menores, no bloqueantes.**
- Test línea 38: muta el word 0 sin comprobar que algún triángulo referencie el vértice 0. Si no lo hace, el test termina en `false_PASS` ruidoso, no silencioso. Más robusto: `idx=int(b.lods[0].faces[0].vertex_indices[0]); raw[4*idx+3]^=0x80`.
- Gate línea 118: `lookup[...]` lanza `KeyError`, no `ValueError`; `reject` no lo captura y la batería caería con traza. Cambiar por `require(k in lookup,'source_corner_xz')`.
- Test línea 36 prueba quiralidad llamando directamente a `check_frames`; es necesario porque `ST_separated_dependency` lo interceptaría antes en `verify_models`. Correcto, pero conviene anotarlo en el reporte como prueba de función, no de consumidor completo.

**Comprobaciones de falso PASS que no encontré rotas.** Composición: pre-check y post-check con la misma `package_identity`, `changed==[NAME]` estricto, orden y props exactos, universo 201 + config, payload igual byte a byte al ODOL 351424ab; FileBank ya demostró paridad byte a byte con este mismo `read_pbo`. Geometría: cada esquina compilada se resuelve por (rol, XZ) con unicidad exigida, winding invertido, multiplicidad por Counter, contacto 0 con tolerancias ±0.02/0.01 sin alterar, pose WRP por `instances.npz` y centro float32. Normales: codeword 10 bits exacto por esquina, consistente con `dry-road-normal-codec` (4632 esquinas). Nada escribe P3D, nada compila, nada despliega; el test sólo muta objetos deep-copiados.

**Resultado aceptable tal y como está escrito:** `COMPILED_GEOMETRY_GATE_PASS_METADATA_CONDITIONAL` y `EXPERIMENTAL_PACKAGE_IDENTITY_PASS_METADATA_CONDITIONAL` separan geometría/identidad de paquete (verificables) de ST/`area_over_tex` (INCONCLUSO semántico) y de visual/motor/RAM (pendientes). Con F1 corregido, F2 y F3 aplicados, puede ejecutarse; F4 y F5 antes de publicar el informe final.

FIN_REVISION
