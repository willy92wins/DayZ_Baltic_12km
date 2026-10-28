**Veredicto: SOUND-with-fixes.** La cadena preparar → capturar → consumir es fail-closed y no preselecciona el resultado del Roadway enterrado. Encontré cuatro correcciones mínimas, ninguna cambia tolerancias ni criterios.

**Lo que verifiqué y está bien**

- **Semántica del discriminador.** `observe` clasifica enterrados como GROUND/BED/INCONCLUSIVE con la misma banda de 0.03 m y exige separación mayor que 0.08 m entre predicciones. Sólo los expuestos tienen criterio de fallo, y ese criterio sí tiene evidencia previa. El test que acepta tanto GROUND como BED para enterrados confirma que no hay PASS preasignado.
- **Selección en prepare.** La remapeo de `kind` (0→1, 2→2, 1→255) está justificado: en el inventario A, kind 0 es Roadway, 1 agua visual, 2 proxy condicional. Así `local_water` enumera Roadway de todas las instancias y la condición `refs[:,0]==19394363 and flags==0` implementa “sin Roadway ajeno ni flags ambiguos”. Recalcula B y H con el mismo código que el script r2 y reconstruye la posición float32 igual que la línea 38 de ese script. El guard `[:21]` coincide con el dominio.
- **Productor y misión.** Las misiones previas en `C:/temp/.../mpmissions` sólo contienen `init.c` y `points.csv`, y el mod Kit7Overlap sólo `Addons`, así que el directorio nuevo es suficiente. El CSV `id;x 0 z` coincide con el formato previo y con el parse de `init.c` (dos campos). El log se trunca en OnInit, y la captura exige `LastWriteTimeUtc >= inicio`, cabecera y `END;16`, con lo que un log viejo del perfil compartido no cuela.
- **Binding.** `package_hashes` del host del run kit7 tenía exactamente 4 PBOs, consistente con `$a.Count -ne 4` en finish.js y con `verify_package_set`. El nombre `baltic_stream_pilot\cs_kit_118_0000.p3d` existe en el paquete. La condición `grant.adopted_run.ok===true && run_id===runid` coincide con loopback.py:5935-5944, que sólo marca ok con un único run idle sin dueño. `s.box.runs` existe en session_status.
- **Formatos de tiempo.** El host escribe 7 decimales (`…3082847Z`), MCP 6 (`…308285Z`). `fromisoformat` acepta esto sólo con Python 3.11 o superior, truncando a microsegundos, y la tolerancia de 1 µs se cumple en el borde. Hay que ejecutar consume con el mismo intérprete 3.11+ que el consumidor kit7.

**Correcciones mínimas antes de preparar**

1. **prepare línea 34, agua real.** `boundary_distance>1` mide la distancia al borde de la unión de agua, no la ausencia de agua. Un punto dentro de un polígono de agua cuya superficie queda bajo el terreno sigue siendo `dry_interior` con distancia grande. Añadir `and not row['water_face_ids']` a la selección. Es la única manera de garantizar “agua a más de 1 m” tal como lo enuncia el plan, y evita un `dry_control_has_water` nativo que se leería como fallo del mapa.

2. **finish.js finally, fuga de lifecycle.** El cierre del run propio sólo ocurre si `checked()` pasa. Si el servidor murió o el proceso cambió, se lanza antes de `dayz_test_close` y el run adoptado queda sin retirar. Con `adopted===true` el run_id es nuestro y el cierre es legítimo. Registrar el error de `checked()` en `cleanup.json` y cerrar de todos modos. No es un falso PASS, pero deja el box ocupado contra la regla de cierre exacto y liberación.

3. **prepare línea 4, rutas.** `R=Path(__file__).parent` produce rutas relativas si se invoca con ruta relativa, y la búsqueda `domain['inputs'][str(R/...)]` da KeyError frente a claves absolutas. Usar `Path(__file__).resolve().parent`. Fallo cerrado, pero evitable.

4. **Gate de revisión antes del FIFO.** `accepted.json` con `REVIEWED_DIAGNOSTIC_READY` sólo lo exige consume, a posteriori. Ningún script lo escribe ni lo comprueba antes de `dayz_test_run`. El paso de lanzamiento, que no está en los archivos revisados, debe exigir su existencia y que sus `inputs` incluyan `deployment.json`. Si no, el plan de “revisión antes de la entrada FIFO” no está codificado.

**Observaciones sin corrección obligatoria**

- Si `session_acquire_wait` falla tras el lanzamiento, el run propio queda vivo por diseño de no-takeover. La recuperación es un segundo acquire que lo adopte como único idle, no una intervención manual. Conviene anotarlo en el plan.
- Cualquier edición del plan, de las dos herramientas de W o de los scripts de R después de ejecutar prepare rompe `Frozen input drift`. Aplicar las correcciones 1-3 primero, luego preparar, luego aceptar.
- `cmd` en finish.js pasa PowerShell multilínea a `exec_command`. Asume el mismo shell que el run kit7. No pude verificarlo en estos archivos.

**Lo que no se aprueba con esto**

Resultado máximo `SEMANTICS_OBSERVED_AT_SAMPLES` en 16 posiciones. Nada sobre las otras 2642 posiciones, los 15 puntos frontera, los 5 testigos fuera de malla, el `max(H,B)` del consumidor ni visual, RAM o mapa. Bullet queda descriptivo, correcto.

FIN_REVISION