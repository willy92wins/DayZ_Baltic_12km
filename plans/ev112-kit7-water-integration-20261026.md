# EV112 — comprobar el agua antes de integrar kit-7

Unidad derivada del plan de validación de kit-7 y de P9/P10. El terreno candidato cambia3.430vértices, pero la revisión independiente conserva exactamente las esquinas de las charcas actuales, su clasificación, el mar, protecciones, carreteras y reparaciones F. La envolvente retira36celdas inactivas; cover no cambia. No hay permiso nuevo de topología.

[EXACT] `tools/water/bury_edges_v31.py:20` acepta terreno, referencia, cover, envolvente, informe de huella base y tres salidas nuevas. Recalcula `pond_footprint_v31.py` antes de cada pase y puede corregir bordes: esas correcciones todavía no están autorizadas por esta unidad. Ejecutar una vez en carpeta aislada, presupuesto900s, sin PBO/WRP/juego.

Aceptación de esta unidad: cero cambios de bury, cero bordes recién expuestos, terreno de salida byteexacto al candidato aprobado, última huella vinculada al mismo terreno; plane,field,visible exactos a F. `env_plane` debe corresponder exactamente a la envolvente candidata ya revisada; no exigir igualdad de ese campo con F porque las36retiradas inactivas son intencionadas. No modificar ninguna tolerancia. Si cualquiera falla, guardar salida y diagnóstico, sin integrarla ni repetir automáticamente.

Esta comprobación solo permite conservar la geometría de charcas anterior si sus tres campos siguen exactos. No demuestra que las piezas del kit antiguo se hayan retirado del WRP, que el bosque despeje el nuevo cauce ni que las piezas nuevas funcionen en el motor. Después: composición de registros, bosque, WRP compilado, física/agua/navegación propias y vista. La generación C/F actualmente activa permanece inmutable.
