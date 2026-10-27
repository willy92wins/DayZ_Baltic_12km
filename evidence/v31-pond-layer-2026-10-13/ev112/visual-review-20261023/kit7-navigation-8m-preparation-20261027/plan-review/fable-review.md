**Veredicto: SOUND-with-fixes.** El plan no inventa API, no evade el criterio y las cifras cuadran con las fuentes selladas. Hay una ambigüedad material sobre el timeout y dos ajustes menores.

**Verificado contra fuentes**

- Config: `tileWidth=12.5`, `cellSize1=0.25`, `cellSize2/3=0.1` en `config.cpp:64-67` del diagnóstico sellado. 8 es múltiplo de 0,25 y 0,1 y divide 12288 exactamente, luego la rejilla 1536×1536 no depende de floor/ceil del generador.
- Screen offline: 12,5→1,165 m; 10→0,868 (falla); 8→0,779; 7,5→0,812 (falla); 6,25→0,378. El plan cita bien y lo califica como orientación. La no monotonía (7,5 peor que 8) confirma que es ruido de diagonal, no predicción. Es incertidumbre del generador, no bloqueo.
- Reconstrucción: residuo máximo 4,82e-7 m coincide. Las alturas de vértices están cuantizadas a 0,1 m en esquinas de tesela, lo que hace plausible la hipótesis de interpolación por cuadrilátero.
- Ratio de teselas 2359296/966289 = 2,44×. Correcto.
- Referencia congelada: `prepare_patch_nav_probe_ev112.py:86-91` sella solo previous_reference, local_routes, source_mission y terrain. No incluye el paquete NM, así que reutilizar la misma referencia con nuevo UUID es válido en `verify_kit7_nav_ev112.py:99-101`.
- Tolerancia 0,801 fijada en `verify_kit7_nav_ev112.py:36`; el plan no la toca.
- Inspector: `inspect_navmesh_v9_ev112.py:16` y `:88` rechazan 8,0 hoy. La extensión del plan es necesaria y real. 8,0 es exacto en float32 y los límites `x*8` son enteros, sin riesgo en la comparación de `:62-66`. Referencia de tesela `(1<<48)|(index<<20)` no colisiona para índices < 2^28.
- Wrapper: `generate_navmesh_console.py:48` limita a 7200 s. Cambio necesario.

**Hallazgo 1 (material): el presupuesto 14400 s tiene ~1 % de margen y el plan no define qué ocurre ante TIMEOUT**

Fuente: plan líneas 41-43 y 67-69. 97 min 22 s = 5842 s × 2,44 = 14264 s. Quedan 136 s si el escalado es lineal. El plan dice "no repetir generación idéntica" ante fallo y presupuesta "una generación 8m". Un TIMEOUT con config idéntica y más presupuesto es, literalmente, una generación idéntica. Impacto: Codex podría quedar bloqueado tras 4 h sin regla para decidir, o reintentar sin autorización. Fix: añadir una frase que distinga TIMEOUT (resultado de infraestructura, conserva evidencia y replantea presupuesto con Guillermo) de FAIL por alturas (resultado del experimento, no reintentar idéntico). No cambia el máximo autorizado.

**Hallazgo 2 (menor): el test duplica el límite del wrapper**

Fuente: `tests/test_navmesh_generator_identity.py:39` reimplementa `10<=timeout_s<=7200` dentro del harness y `:79-81` prueba 7200/7201. Si solo se cambia el wrapper, el test predice mal y fallará por motivo equivocado. Fix: actualizar ambos sitios a 14400/14401 en el mismo cambio, como ya exige el plan en líneas 59-61, pero nombrando explícitamente esa línea 39.

**Hallazgo 3 (menor): procedencia del config citada con nombre distinto**

Fuente: plan línea 17 cita `checkpoint/diagnosis/deployed-config.cpp:64-67`; el hash sellado es `kit7-nav-layer-diagnostic-20261026-v2/config.cpp`. Las líneas coinciden. Fix: citar la ruta sellada o anotar que son el mismo contenido.

**Riesgo de tamaño, ya absorbido por el plan**

Cada tesela ocupa >116 bytes aunque esté vacía (`inspect_navmesh_v9_ev112.py:45`). Solo las cabeceras añaden unos 160 MB al archivo y RAM proporcional. Baltic 8 m tendrá ~25× más teselas que Chernarus. El paso 6 ya trata un exceso de RAM como no bloqueante para el éxito funcional, lo cual es correcto. El inspector valida que los offsets u32 no desborden.

**Sin contradicciones materiales** entre plan y autorización: FIFO directo sin pre-lease, sin cliente, física por paridad de entradas, UUID nuevo, PASS solo por 607 nativo, histórico FAIL conservado. No se declara PASS por predicción.

Resumen: aprobar con las tres correcciones textuales anteriores antes de implementar. El experimento 8 m está autorizado y su resultado es incierto por diseño, no por defecto del plan.
