## Veredicto: SOUND-with-fixes

**CONVERGE** — condicionado a incorporar los fixes F1–F6 en el texto antes de ejecutar C1A. Sin ellos: NO_CONVERGE para ejecutar.

El alcance es correcto en lo esencial: autoriza sólo C1A, bloquea compile real, no inventa cierre (`build_ready=false`, `dependency_closure=NOT_EVALUATED`, `compiled_terrain_decoder=NOT_VERIFIED` siempre), conserva R0 sin convertirlo en éxito, declara el cambio de cap como contrato nuevo de otra investigación (no reparación geométrica ni rerun del CLI de C0), no pide prueba nativa para la lectura histórica y no repite catálogos. La config histórica se trata como evidencia no copiable y el wrapper `compile_visual_pilot_ev112.ps1:9-29` como no-entrypoint. Eso está bien anclado.

### Fixes bloqueantes (cambio mínimo por punto)

**F1 — Gramática de las 4776 filas no está definida.** Ancla: C1A.1 dice «recorrer las 4776 filas con preguard de longitud<=4096 y final exacto 17307629», pero no define qué es una fila (nº de cadenas, terminador, codificación), dónde vive el count (el discriminador de 56 B lo observó en offset 16908312) ni desde qué offset empiezan las filas. Tal como está, «4776» es un número mágico y el final exacto sólo prueba consumo de bytes, no parseo. *Cambio mínimo:* fijar en el plan offset/tipo/endianness del count, offset de inicio de filas, gramática por fila y qué discrepancia (count≠4776, longitud, no-terminación) produce rechazo explícito vs INCONCLUSIVE.

**F2 — Resolución literal de rutas sin regla de namespace.** Ancla: C1A.2–3 («rutas literales», «sin fallback de basename», «raíz propia y P:»). Las rutas observadas serán del tipo `DZ\surfaces\...` (cf. config ancla líneas 26, 33, 48, 51–54); mapearlas a una raíz exige declarar qué prefijo se retira o se conserva. Sin esa regla, el executor puede «localizar» por heurística — exactamente el límite que el plan reprocha a `package_visual_forest_ev112.py:29-65`. *Cambio mínimo:* tabla cerrada raíz→transformación literal permitida (o `UNRESOLVED_NAMESPACE`), registrada por ruta en el recibo.

**F3 — Raíces de búsqueda no cerradas; riesgo de traversal por reparse.** Ancla: C1A.3. «Raíz propia y P:» no acota directorios, profundidad ni nº de entradas enumeradas; el control de reparse sólo aparece en C1A.4 para config. Seguir un junction tipo los de `compile_visual_pilot_ev112.ps1:18-22` escaparía del presupuesto 60s/64MiB. *Cambio mínimo:* lista cerrada de raíces, no seguir reparse en ninguna fase (registrar identidad/link, como ya pide C1A.4), y contador de entradas enumeradas dentro de los límites globales.

**F4 — Orden de fases deja fuera las rutas de config.** Ancla: C1A.3 precede a C1A.4, pero las referencias de terreno de la config histórica (OutsideTerrain líneas 24–36, `midDetailTexture` línea 48, UsedTerrainMaterials líneas 49–55) sólo se leen en el paso 4; sus rutas nunca entran al inventario del paso 3. El criterio de término («lista completa… y observaciones de rutas») quedaría incompleto respecto a uno de los dos bloqueos declarados. *Cambio mínimo:* reordenar (config antes que localización) o añadir paso 3b con los mismos límites; o declarar explícitamente esas rutas excluidas de C1A y trasladadas como abiertas a C1B.

**F5 — Contabilidad de límites ambigua.** Ancla: asiento EXECUTOR (64MiB total, 1MiB/texto, 8MiB excepcional, 32768 referencias, 16384 rutas). No se dice si el hash completo del control (17307685 B) cuenta contra los 64MiB, si «referencias» cuenta por cadena, por fila o por ruta distinta, ni si el preguard de longitud se aplica antes de copiar la cadena (4776×4096 con final exacto no protege la asignación intermedia). *Cambio mínimo:* definir unidad de conteo por límite, qué operaciones cargan (hash, lectura, enumeración), y preguard contra bytes restantes del prefijo (399313 B) antes de materializar cada cadena. Mantener INCONCLUSIVE sin reintento al exceder, como ya está.

**F6 — C1B puede auto-autorizarse.** Ancla: «C1B necesita cerrar las anclas y su contrato antes de código o build» y el bloque [DESIGN]. Quién juzga ese cierre no está dicho; el mismo executor podría declararlo. *Cambio mínimo:* una línea — C1B (y cualquier `COMPILE_PROBE_ONLY`, ya bien exigido como autorización separada) requiere autorización explícita nueva tras revisión del recibo C1A; el éxito de C1A no la habilita.

### No bloqueante

- Herramientas (C1A.5): la cautela «no prueba ausencia en todo el host» es correcta; basta fijar los directorios exactos enumerados para que «no aparece» tenga ancla.
- Reconciliación independiente: aceptable tal como está, porque el plan limita su alcance al inventario observado y no al formato OPRW. Conviene que el recibo nombre los offsets usados al «saltar alturas/índices» y su campo en el contrato 9296cef4.
- C1B [DESIGN]: navmesh/clutter «decidir y documentar» es deuda legítima de diseño, no autorización; con F6 queda suficientemente contenida.

Con F1–F6 escritos en el plan, C1A es ejecutable tal cual: acotada, falsable, sin cierre inventado y sin tocar geometría ni build.

END_ROADC1_REVIEW
