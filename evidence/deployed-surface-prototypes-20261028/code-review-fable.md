**Veredicto: SOUND-with-fixes.** Las 17 fixtures no ejercitan `inventory()`; con las entradas selladas actuales, producción fallaría en el primer paso por un defecto de claves. No hay falso PASS reproducible. Dependencias reales verificadas: lector ODOL fa0d74b6 expone `from_bytes(data, strict=True)`, `lod_errors`, `lod_end_ok`, `Section.get_face_indices`, `mat_name`, `Matrix4P.orientation.aside/up/dir` y `model_info.bounding_center` tal como el código los usa. El meter `water_constraint_diagnostic_ev112.py` expone `sha`, `dump`, `bounded`, `memory`, `STARTED`.

**P1. Bloqueante reproducible: claves del manifiesto**

`deployed_surface_inventory_ev112.py:201` indexa `artifacts[p.relative_to(root).as_posix()]`. El manifiesto `evidence/deployed-geometry-discovery-20261028/artifact-hashes.json` usa claves con barra invertida (`geometry-payload-discovery-resolved-20261028\all-models.json`). Resultado: `KeyError` antes de hashear nada, capturado en `failure.json` como fallo genérico. Fix mínimo: normalizar ambas partes con `norm()` al construir un dict de búsqueda, o buscar `str(p.relative_to(root))`. Añadir fixture que cargue el manifiesto real y resuelva los cuatro nombres.

**P2. Sin recomprobación tras el primer hash**

Los JSON de descubrimiento se hashean en 201 y se leen en 202-203; `selected-instances.npz` se hashea en 201 pero se carga en 244, tras decodificar 5443 payloads (ventana de decenas de segundos). Los payloads sí están protegidos (SHA del contenido leído, 79). El diagnóstico hermano recomprueba al final (`input_changed_during_diagnostic`); este script no. Fix mínimo: leer bytes una vez y hashear esos bytes (JSON y NPZ vía `io.BytesIO`), o repetir `meter.sha` de discovery, manifiesto, paquetes y lector justo antes de escribir `report.json`, abortando con `input_changed_after_hash`.

**P3. Trazabilidad de proxies incompleta**

`META` no registra qué ranura de proxy del padre originó una cara. Si un padre instancia el mismo hijo dos veces con matrices distintas, los registros resultantes son indistinguibles (`model`, `source_model`, `face`, `lod` iguales). Fix mínimo: campo `proxy` (`<i2`, -1 en caras propias) en META, asignado en `expand_proxies:180-183`; conservar índice de ranura también en anidamiento (padre más cercano). `model-sections.json` ya lista los proxies por modelo con matriz y nombre, así que el consumidor podrá cruzar.

**P4. Pruebas que no distinguen omisiones**

- Todas las fixtures de `extract` tienen una sola cara. Una regresión que conserve solo la primera cara, o que omita degeneradas, pasaría. Añadir LOD Roadway con ≥3 caras (tri, quad convexo, quad degenerado) y afirmar `len(ids)==faces` y flags por cara.
- `expand_proxies` solo se prueba con hijo `kind=1`. El docstring promete no convertir Roadway hijo en soporte; añadir meta hijo con `kind=0` y afirmar que no aparece. Añadir nieto (jerarquía de dos niveles con centro no nulo) y verificar composición analítica.
- No hay test de `inventory()` con raíz sintética; es lo que habría atrapado P1. Basta un directorio temporal con manifiesto, catálogo de dos modelos, un PBO en memoria con dos ODOL mínimos... si construir ODOL es costoso, al menos test de resolución de claves y del bloque 244-248.

**P5. Coplanaridad con TOL=1e-9 absoluto sobre float32**

`face_flag:102` compara distancia al plano en metros contra 1e-9. Los vértices ODOL son float32; cualquier quad real con coordenadas de decenas de metros tendrá residuos ~1e-6 y será AMBIGUOUS. No es falso PASS, es conservador, pero puede volver INCONCLUSIVE casi toda la etapa B. Recomendación sin rediseño: conservar el bit y añadir la magnitud (distancia al plano) en metadatos o resumen, para que B decida con dato en lugar de umbral heredado del solver (que el plan fija para residuos, no para coplanaridad de datos).

**Verificado correcto (sin cambio)**

- Roadway por igualdad exacta `r == 3000000028082176.0`; visual = mínima en [0,1000); duplicados rechazados.
- Secciones: índices -1 tolerados, `mat_name` cuando `material_index==-1`, partición total exigida, raw y normalizado conservados. Agua solo por material exacto normalizado; textura no clasifica.
- Transformación raíz `v @ M[:9].reshape(3,3) + M[9:]` coincide con el layout `[aside, up, dir, pos]` del WRP (`discover_geometry_payloads_resolved_20261028.py:77`) y con `verify_compiled_stream_pilot_v31.py:54-84`. Proxy `(V + child.bc) @ R + T` marcado PROXY_CONDITIONAL siempre; el nombre de proxy se normaliza igual que en descubrimiento (`:58`).
- PBO: rutas inseguras, duplicados case-insensitive, compresión y truncamiento rechazados; sentinel validado.
- Identidad de mundo: WRP editable, compilado y `narva_trial.pbo` rehasheados (≈2.2 GB de lectura, dentro de 120 s a velocidad de disco normal). Paquetes y diez ficheros del lector por SHA.
- Cobertura de instancias: conteos por modelo contra catálogo, IDs únicos.
- Memoria: el bucle por cara en Python para todas las LOD de 5443 modelos es el coste principal; el descubrimiento previo hizo trabajo similar en 18 s y 278 MB. El meter aborta a 120 s/2 GiB.

**Observación menor**: `inputs.json` de salida no copia los SHA de paquetes ni del mundo; quedan cubiertos transitivamente por el manifiesto. Aceptable si se declara.

**Prioridades**: P1 (bloquea ejecución), P2 y P3 (procedencia/trazabilidad), P4 (pruebas), P5 (dato para B). Ninguno exige resolver la convención del motor; el marco de proxy sigue como hipótesis.

FIN_REVISION
