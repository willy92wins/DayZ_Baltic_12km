# Revisión acotada del bloque de orillas

Guillermo autorizó consultar Opus 5.5 y trabajar esta sesión de ocho horas. Tu
asiento es reviewer, solo lectura. No implementes, no delegues, no uses UI,
procesos, red ni escritura. Lee únicamente los archivos indicados y referencias
directas necesarias. Codex sigue como executor/integrador.

Objetivo: buscar fallos concretos en el bloque ya terminado, no otra auditoría
general ni otra especificación. Máximo 900 palabras. Devuelve solo hallazgos
accionables con archivo:línea, mecanismo y consecuencia, y límites de la revisión.
No supongas que lectura, un contador o un gate offline prueban el motor.

Implementaciones nuevas:
- tools/terrain/finish_shores_v30.py
- tools/terrain/review_shores_v30.py
- tools/terrain/prepare_water_templates_v30.py
- tools/terrain/prepare_shorefinish_runtime.py
- tools/playtest/verify_shorefinish_v30.py
- tools/terrain/render_view_v30.py (cambio de nearest-water por cell_planes)

Contrato real de agua/triángulos: tools/terrain/v30_common.py y
tools/terrain/build_surface_v30.py. Plantillas/poses: consulta solo si lo
necesitas tools/terrain/derive_world_v30.py y el verificador regional anterior.

Recibos, no evidencia de ejecución nativa:
- E:/DayZ-Baltic-Build/v30-shore-finish-tidal/build.json
- E:/DayZ-Baltic-Build/v30-shore-finish-tidal/review/review.json
- E:/DayZ-Baltic-Build/v30-shore-finish-tidal/runtime-fixture/reference.json
- E:/DayZ-Baltic-Build/v30-shore-finish-tidal/runtime-fixture/verifier-controls.json
- E:/DayZ-Baltic-Build/editor-v30-delta/water-import-v30/preparation.json
  (muy grande: leer cabecera o secciones concretas; no volcar los 13.419 modelos)

La salida f27aacd3 ajusta 50.072 vértices, protege corredores útiles, carreteras,
Narva y reserva. Bajar tierra hasta 3 m y elevar fondo hasta 1,5 m fuera del
canal fue el diseño. Revisión final conserva cero nuevas exposiciones a la cota
marina baja 0,5 m. Se mantienen 17.622 piezas/13.419 modelos pond.

Biblioteca nueva con nombres v30_: hash de nombre SDBM 65599 firmado32 y radios
basados en mitad de Z, comparados con los 6.187 templates nativos anteriores.
CSV conserva traslaciones float32 del WRP; el consumidor nativo todavía NO está
probado. No marcar como bug confirmado una diferencia de origen/centro sin
leer el contrato anterior o aislar el consumidor.

Misión preparada, no desplegada: 961 consultas, 730 distinguen las alturas del
baseline, siete sitios. El verificador tiene un control positivo sintético y
ocho negativos; solo prueban el verificador. DayZ está ocupado por otra sesión
y Computer Use se ha desconectado. No existe aún navmesh ni prueba del motor
para este candidato, y no lo presentamos como base terminada.

Prioriza pérdida geométrica, pruebas que dan falso PASS, agua fuera de piezas,
transformaciones equivocadas o condiciones de terminación de la misión.
No pedir repetición de gates intactos por costumbre. Si no encuentras defectos
concretos, dilo y separa los riesgos que solo resuelve el consumidor.
