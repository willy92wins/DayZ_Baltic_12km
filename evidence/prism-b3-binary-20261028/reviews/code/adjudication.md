# Adjudicación de código B3B
Fable5.1 nativo,396.844s,SOLOLECTURA,identidad confirmada; SOUND-with-fixes.
Una corrección agrupada, sin nuevo build ni nueva revisión y sin cambiar tolerancias.
H1 aceptado: identidades, bindings, estructura/pose y campos imprevistos -> INCONCLUSIVE_BINARY; geometría -> REJECTED_BINARY. La condición de rechazo no cambia.
H2 aceptado: control_surface comprueba MLOD d130 contra ODOL fresco antes de compilar candidato; se repite como condición del consumidor separado. Sus contactos se informan sin exigir que el control ya repare el defecto. Fallo del instrumento/control es inconcluso.
H3 aceptado: residuos/predicción, caras exclusivas y ULP en details; se conservan al rechazar. No se amplió exactitud ni tolerancia.
H4 aceptado: fixture analítico de dos prismas/cuatroLOD recorre verify_pair y overlay reales; constantes de coste parcheadas sólo con unittest.mock en tests. Producción conserva9120/12160/1520 y72.
H5 aceptado: informe identifica ambos marcos, cuya igualdad de caras mundiales es condición mecánica.
H6 aceptado: dependenciapsutil al final de sys.path y origen real comprobado; lista de fuentes y hash actuales conservados.
H7 informativo, sin cambio de lifecycle.
Hallazgo adicional Codex reproducido: unchanged({'mass':1},{'mass':1,'new_field':None},set()) devolvía[]. Se comprueba presencia de clave separada del valor; test primitivo y mutante Geometry integrado lo rechazan.
Refuerzo de binding: contrato offline447d y su source/original/targets/componentes se releen; config.bin de pareja comparado también en consumidor.
Primer fallo de fixture .01float64 frente a rawfloat32 corregido a .125 exacto. Fixture de dos prismas corregido por alias entre lista de puntos y selección y reubicación de dos líneas de test; no cambios de producción para hacerlos pasar.
33tests incluyen ruta completa, cambiosVisual/Memory/Roadway/UV/agua, Geometry desconocido, no seleccionados, dominio incompleto y winding erróneo del control. Cualquier futura geometría roja para esta pareja detiene el presupuesto; no segunda pareja ni replay oportunista.
