**Veredicto: SOUND-with-fixes.** No encontré ningún camino reproducible hacia un certificado falso con los datos pinned. Los hallazgos son de presupuesto, frontera, metadata y carrera; ninguno convierte un INCONCLUSO en PASS.

**Verificado como correcto**

- `ownership` (`water_constraint_diagnostic_ev112.py:85-91`): los 7 offsets coinciden con S6 de `shore_ramp_v31.py:92` (simétrico por punto, sin reflexión); fuera de rejilla se descarta, igual que `binary_dilation` con border 0 en `small_native_water_pilot_ev112.py:98`. Centinelas int32 max / -1 y `np.minimum.at`/`maximum.at` acumulan dos cadenas por celda.
- `foreign` (`:95-96`): exacto para cualquier número de propietarios distintos (≥2 ⇒ `low!=high`; 1 ⇒ compara con C). Excluye siempre la propia C. Test de conjuntos explícitos `test_...:19-33` cubre 0..7 incluidos ID ausente.
- Reconstrucción `fixed_769` (`:172`): `(bits!=0)|foreign(...,769)` contra `saved['fixed']` completo. Ventana `crossing60` (`:162-166`) es conservadora (floor−/+2) y la igualdad de rejilla completa detectaría cualquier desvío.
- Caras: mapeo `tri` (`:173`) coincide con `TRIS/COFF` de `shore_ramp_v31.py:167-168` (A: NW,NE,SE; B: NW,SW,SE). Decodificación de claves `keys//(n*n)`, `keys%(n*n)` (`:183`) coincide con `shore_ramp_v31.py:199-200`. `pin` replica `small_native_water_pilot_ev112.py:100`; fracción por aristas, no por vértices.
- `classify` (`:99-109`): orden closed→sea→full_fixed→degree2→≤512→screen; `len(points)-1` cuenta segmentos; screen es `closed_screen` real (.25/45/60). Grado 2 se exige globalmente sobre el censo (`:177,186`), por lo que ninguna cara ajena puede re-ensamblar el anillo.
- `support_at` (`:112-128`): formas y anillos idénticos a `despike_v31.py:62-71`; `np.clip` equivale a `pad(mode='edge')`; aritmética float32 igual a `:81`. Igualdad exacta con los 9 valores guardados (`:213`), y los 9 puntos son interiores (filas 1647-1654, columnas 1957-1969).
- Control negativo real (`:220-221`), cobertura 1030/9 (`:219`), re-hash de entradas al final (`:222`), `mkdir(exist_ok=False)` (`:237`), sin escrituras fuera de `output`.
- Watchdog (`:24-59`): layout de `PROCESS_MEMORY_COUNTERS` correcto (2×DWORD + 8×SIZE_T), `GetCurrentProcess` pseudo-handle, `os.getpid` publicado, `os._exit(3)` sólo tras volcar `resource-stop.json`, fallo de medición también cierra.

**Hallazgos (ordenados por impacto)**

1. **Presupuesto global ausente** (`:104-105`). El tope 512 acota cada cadena, pero no la suma. `closed_screen` hace n rotaciones con `simplify` por anillo; con 1030 cadenas y centenares potencialmente fijas por `pond_envelope`/`crossing60`, el peor caso roza o supera 120 s y el watchdog mataría la única ejecución autorizada a mitad de `savez`. No es certificado falso, pero desperdicia la ronda. Arreglo mínimo: contador `pairs_left` como en `native_shore_census_ev112.py:75,84-88`; al agotarse, `NOT_EVALUATED_COST`. Opcional: procesar cadenas elegibles en orden creciente de tamaño.

2. **Frontera en soporte de testigos** (`:215-217`). `witness['shape']+witness['ring']` llegan sin recortar; `h[r, c]` y `saved['side'][r, c]` con índice negativo envuelven silenciosamente al lado opuesto, mientras `support_at` sí recorta (`:124`). No reproducible con los 9 puntos actuales; latente si se reutiliza. Arreglo: `r, c = np.clip(...)` idéntico a `:124`, o `require(0<=r<n and 0<=c<n)`.

3. **Metadata de código no pinned** (`:141-145,159,207`). `expected` no incluye el propio script, `small_native_water_pilot_ev112.py`, `verify_small_native_water_pilot_ev112.py` ni `shore_ramp_v31.py`, que sí ejecuta. El inventario se hashea en caliente, no contra el valor del `context.json` del piloto (`74e4677a…`). Arreglo: añadir esos paths a `expected` antes del bucle `:146` y comparar el hash del inventario con `context.json`.

4. **Carrera informe/watchdog** (`:240-244`). `report.json` se escribe antes de `stop.set()`; si el umbral de 120 s se cruza en ese intervalo quedan `report.json` + `resource-stop.json` y exit 3. Arreglo: `stop.set()` inmediatamente después del `require('resource_budget')` y antes de `dump`.

5. **Sin `failure.json`** en excepción: el directorio queda con archivos parciales y sin estado. Arreglo: `try/except` como `native_shore_census_ev112.py:259-263`.

6. **Tests**: falta contraste de `support_at` con `despike_v31.prominence` sobre un campo aleatorio 2048² (valida semántica, no sólo los 9 valores) y un caso `INCONCLUSIVE_DEGENERATE`. Nota: `pilot_fixed_mask_exact=True` (`:228`) es literal, pero lo garantiza el `require` de `:172`.

**Ninguno de los seis puntos** altera umbrales, añade candidato de altura ni relaja protecciones. Con 1, 3 y 4 aplicados la ejecución única sobre el mapa es defendible.

FIN_REVISION
