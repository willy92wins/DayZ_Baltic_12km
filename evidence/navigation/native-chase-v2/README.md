# Cruce físico del puente elevado

PASS_NATIVE_AI_LOCAL_AND_BOTH_CROSSINGS. Misión congelada e27ae2bd, PBO nativo
fd2c7023, navmesh68450401. Runfcd183c5-c918-4633-842c-14920054f740, un cliente.
Log9f8b1e68. Verificación completa en verification.json y ocho negativos en
negative-controls.json; fuente tools/navigation/verify_native_chase.py.

Tres infectados sucesivos, cada uno creado una sola vez y borrado al terminar
su etapa. Posición/orientación de spawn y estímulo humano/ruido; ningún control
de posición, velocidad o input de IA después del spawn. Prey invulnerable,
20s de asentamiento previo por etapa y registro de posición real estable.

| Etapa | Duración | Registros de actor | Salud mínima |
|---|---:|---:|---:|
| Control local |8.845s|48|100|
| Oeste→este |49.822s|266|100|
| Este→oeste |55.789s|299|100|

No había puente ni agua directamente en la vista cliente al final, que miraba
hacia el oeste desde el destino. La prueba de cruce se basa en telemetría del
servidor y comparación con la geometría nativa, no en esa captura.

Límite: un actor a la vez, corredor Narva, sin capacidad multijugador ni red
regional acreditada. Gate de consultas navmesh0.8m sigue FAIL separado. V1
conservada con FAIL por deriva del prey en su control inicial. Cierre por MCP,
forced_kill/exit_metrics_valid=false; el registro acabó antes del cierre.
