# EV79 — revisión de stage y paquete

**Veredicto: PASS para staging, regeneración selectiva y composición/integridad del PBO.** No acepta la geometría OPRW en motor: la lectura nativa `SurfaceY` continúa pendiente.

## Revisión

- `stage.py` fija el hash del WRP 0WZD fuente, compara sus alturas con EV71, escribe solo alturas EV79 y vuelve a leer el resultado. Comprueba igualdad del header, materiales, terminador y los 18.033 registros de objetos. La nueva salida conserva estos bytes; el hash de WRP staged es `7d49ba19…`.
- `build_changed_surface.py` calcula celdas tocadas por cualquier vértice modificado y prueba su intersección con la caja de cada tesela, incluidos los 64 m de solape y los 8 px del padding del filtro. Recalculé independientemente la selección: coincide exactamente con la lista del informe, 18 teselas y 13.926 celdas tocadas. El archivo actual también fija hashes del generador, fuente EV71, candidato y plano P. Esas guardas de hash se añadieron después de generarse `surface-verification.json`; no atribuyo esos checks a aquella ejecución. Los hashes y la selección sí se verificaron independientemente en esta revisión antes de aceptar el uso del reporte.
- La verificación de superficie de esas 18 teselas pasó los gates: agua de origen en grava, interiores compilados en grava, alfa, paleta y solapes. Revisé 90 comparaciones de solape; hubo 0 diferencias. Los 8.840 cambios de máscara coinciden con los 8.840 píxeles de cambio de clase de orilla del análisis EV79. Hay 17 controles negativos aplicables PASS y 1 tesela sin interior aplicable (`null`); no hay controles negativos fallidos. El PAA decodificado conserva 237 píxeles húmedos no-grava en bordes, pero el interior compilado no-grava es 0; queda limitado al borde, no se presenta como continuidad perfecta de máscara.
- `package.py` comprueba las 2.048 identidades PNG y 2.048 PAA del paquete base antes de sustituir, preserva propiedades y rutas del PBO y compara cada entrada empaquetada con su reemplazo previsto o con el byte original. Releí el PBO base y el desplegado con `attach_navmesh.read_pbo`: 6.827 entradas y propiedades iguales; 6.804 entradas intactas; los únicos cambios son el WRP y 22 PAA seleccionados. Los 36 PAA seleccionados están en el reemplazo previsto; los otros 14 quedaron idénticos byte a byte. El PBO de agua mantiene SHA `3946db8b…`.

## Límite de aceptación

El OPRW resultante es v29, 16.664.545 bytes, SHA `fee7cad7…`, y difiere del WRP base. Eso demuestra identidad e integridad del artefacto, no que las alturas compiladas correspondan al candidato. No hay lector OPRW local verificado; debe cerrarse con la sonda nativa `SurfaceY` server-only. Render y navegación también siguen pendientes.

Fuentes revisadas: `stage.py`, `build_changed_surface.py`, `package.py`, `stage.json`, `surface-verification.json` y `deploy.json`, todos bajo EV79. Sin cambios a scripts, candidato, WRP o PBO durante esta revisión.