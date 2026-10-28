**Revisión independiente B3B (sólo lectura).** Leí el plan, la adjudicación, el consumidor, sus tests, el driver de compilación, el preflight archivado y las utilidades reutilizadas (gate antiguo, lector ODOL fa0d, normalizador canónico, overlay, read_pbo, contrato B3 r1 y proof offline).

## Plan (alcance, APIs, criterios, presupuesto)

El plan es coherente con la adjudicación y con las fuentes: lector estricto fijado por SHA e instrumentado sólo con el probe de offset (`compiled_dry_road_gate_ev112.py:42-48`), cabecera ODOL sin offsets físicos (atributos version…notes, `odol_reader.py:940-951`, `:1125-1130`), control fresco contra 3514 vía canonical_lod, LOD0/2/3 exactos, Geometry con lista blanca cerrada, caras orientadas float32 mundiales, overlay ±.02/.01 sin cero exacto, contains estricto 700/723, COM/inercia NO_CERTIFICADAS, campo imprevisto ⇒ INCONCLUSIVE. Presupuestos acotados; el paquete sólo tras consumidor verde. No encuentro cambios derivados sin cubrir. Única observación: el presupuesto de 180 s del consumidor es más estrecho que los 300 s del gate anterior (que leía 5 ODOL); con 3 ODOL y un overlay de 12160 caras es plausible, y un exceso termina en INCONCLUSIVE_RESOURCE por el watchdog, no en PASS.

## Código: ausencia de falsos PASS

No hallé una ruta a `COMPILED_B3_CONDITIONAL` sin cumplir las puertas:

- Binding: candidato c769 fijo, pines verificados antes y después, proof OFFLINE_CANDIDATE_ONLY ligado a contrato 447d y a candidato, targets/origen/componentes/original iguales, pose WRP releída del npz, ODOL histórico igual al payload del PBO ef229, ODOL de la pareja igual al payload del PBO recién compilado (`prism_b3_binary_ev112.py:140-157`).
- Estructura: `lod_value` exige fin exacto y `size_of_rest_data` contra el probe (`:31-33`); cabecera y model_info con `unchanged` sobre lista blanca cerrada; LOD 0/2/3 canónicos exactos (`:113-114`); conteos 9120/12160/1520; Geometry sólo vertex_raw/vertices/normal_raw/normals/size_of_rest_data; b_radius/b_center/face_area no permitidos y reportados por bits (`:117,135`).
- Localidad: bytes de vertex_raw/normal_raw idénticos fuera de los 72 vértices seleccionados (`:118-125`).
- Geometría: raw==decodificado, 6/8 únicos por componente, predicción local float32(MLOD−centro) como multiconjunto, error bidireccional <.001, multiconjunto cíclico de caras orientadas con winding invertido, cobertura única de todos los vértices/caras (`:73-103`). Una cara invertida cambia la clave cíclica y falla (test `:73-75`).
- Contactos: `Polygon.contains` excluye borde, punto float32, se reporta margen y ULP sin umbral inventado (`:60-71`); tests de borde/vértice/subULP correctos.
- Overlay: mismo filtro de lecho que el consumidor offline aprobado (`verify_prism_contact_b3_ev112.py:159`), techo por normal +y como en el gate histórico, límites por defecto .02/.01.
- Driver: control compilado antes que el candidato y `control_identity` falla antes de compilar el candidato (`build_prism_b3_pair_20261028.py:82-88`); misma config en ambos lados (`:91`); consumidor en proceso separado con `-I` y cwd=W; paquete sólo con status y contract_sha correctos; FileBank con propiedades reproducidas e identidad 200/201 reverificada sobre el PBO real (`:98-109`). Rutas explícitas, sin rglob.

## Hallazgos (con repro)

**H1 (medio) Taxonomía de fallos invertida para identidad/binding.** Todo `need()` lanza ValueError y el main lo mapea a `REJECTED_BINARY` (`prism_b3_binary_ev112.py:22-23,175`). El plan (líneas 88-89) exige INCONCLUSIVE_BINARY para identidad/control/campo imprevisto y REJECTED sólo para puertas geométricas. Afecta a wrong_candidate, unpinned_core, input_changed, candidate_payload_binding, offline_*, saved_WRP_pose_binding, original_controls_changed, historical_package_payload, pair_package_entries, saved_odol_not_pbo_payload, incomplete_odol, lod_boundary, compiled_cost_changed, vertex_raw_decode, component_names/counts/indices, selected_vertex_domain, nonselected_compiled_data_changed, invalid/rotated/pose_changed. Repro: alterar un byte de cualquier fichero pinado ⇒ exit 1 y report `REJECTED_BINARY:input_changed`, atribuyendo al candidato un rechazo geométrico. No es falso PASS, pero el registro histórico quedaría mal etiquetado. Arreglo: que esos `need` lancen `Inconclusive` (p. ej. helper `bind()`), dejando ValueError para compiled_vertex_error, compiled_face_counter, local_recentering_prediction, compiled_contact_*, compiled_overlay.

**H2 (medio) Inversión de winding no verificada sobre el control en esta unidad.** El plan (línea 78) la exige "verificada en el control"; `source_faces` sólo se ejecuta sobre el candidato (`:126`) y `c['source_control']` (d130, pinado) nunca se carga en el consumidor. Sin la corrida de control, un REJECTED del candidato no se distingue de un defecto del gate (riesgo de falso rechazo que consumiría la única corrección permitida). Arreglo: `source_faces(mlod_control[1], A, …)` con el MLOD d130 y exigir PASS; incluir también los contactos del control en el reporte.

**H3 (medio) Residuos/ULP no se guardan al fallar la puerta exacta.** La adjudicación F1 y el plan (105-106) piden "guardar residuo/ULP, no rebajar". Al fallar `local_recentering_prediction` o `compiled_face_counter` sólo se escribe el nombre del componente (`:90,99,175`). Arreglo: adjuntar a la excepción, o volcar en un `diagnostics.json`, el máximo |predicho−B| por componente, la diferencia multiconjunto de caras y los ULP; sin cambiar el criterio.

**H4 (medio) `verify_pair`/`verify_saved` sin cobertura de tests.** Los mutantes del plan "cambio Visual/Roadway/agua/UV", "campo desconocido en Geometry", "vértice no seleccionado alterado" y "cobertura 72" se exigen por `protected_lod_changed`, `geometry_metadata_changed`, `nonselected_compiled_data_changed` y `selected_vertex_domain` (`:113-125`) y ningún test los recorre; sólo se prueban primitivas. Los conteos fijos en `:116` impiden un fixture pequeño. Arreglo: constante de módulo para los conteos esperados que el test pueda parchear, y un fixture SimpleNamespace de 4 LOD que ejercite esas cuatro rutas más la ruta feliz.

**H5 (bajo) Un solo marco reportado.** El plan (109) pide reportar marco MLOD y marco ODOL; sólo se informa el ODOL. Como el gate exige igualdad exacta de caras float32 mundiales, ambos marcos coinciden por construcción; conviene decirlo en `limits` o duplicar el reporte, no afecta al veredicto.

**H6 (bajo) Directorio de dependencias primero en sys.path con pines parciales.** `build_prism_b3_pair_20261028.py:7,57-59` antepone `dry-road-build-dependencies-20261028` y pina sólo los ficheros psutil listados en inputs.json histórico; cualquier módulo extra no pinado allí sombrearía imports. Directorio privado, riesgo bajo; bastaría pinar un listado del directorio o ponerlo al final del path.

**H7 (info) Recursos del driver.** `execute` identifica descendientes por PID+create_time, mide RSS del árbol y mata en orden inverso; `child.wait(timeout=10)` puede lanzar TimeoutExpired, que acaba en failure.json (`:42,114-117`). Huérfanos tras salida del padre se esperan hasta el límite y se matan: acotado. Correcto. El watchdog del consumidor usa `MAX_SECONDS` global reasignado, válido porque se lee en tiempo de ejecución.

## Veredicto

**SOUND-with-fixes.** No se encontró ninguna vía a falso PASS ni relajación de criterios; H1-H4 son correcciones de etiquetado, verificación de control, diagnóstico de fallo y cobertura, implementables sin tocar fuentes publicadas ni relanzar B3 offline/B2. Recomiendo aplicar H1-H3 antes de la ejecución de la pareja (una sola corrección por repro según presupuesto, agrupables en un commit), y H4 antes de publicar.

Identidad: revisión realizada por Claude Fable 5.1 (claude-fable-5-1), sin ejecución de código ni escritura.

FIN_REVISION