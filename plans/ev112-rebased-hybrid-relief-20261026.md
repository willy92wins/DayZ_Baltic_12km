# EV112: reintento híbrido sobre la base kit7

Continuación del suavizado de vecinos protegidos, en la base kit7 inmutable
`815ef8b7`. Solo pico fila1171,col190, antes omitido porque la retención de E
solapaba correcciones ya aceptadas. El reintento normal volvió a fallar con
0cambios. Un diagnóstico de disyunciones min/max aisló la incompatibilidad de
los testigos elegidos; eso no demostraba infactibilidad del terreno.

Una semilla MILP experimental superó37tests y el piloto14vértices, pero la
comparación directa posterior demostró una solución más simple: el modo
híbrido existente también resuelve el mismo caso, con prominencia0,299900055m
y energía pura164,129606→161,897188. El viejo lote de retención había OMITIDO
este grupo: no había probado ni rechazado su solución híbrida sobre kit7.

Por ello no se promueve el helper MILP ni se modifica el solver. Prototipo,
plan y pruebas quedan conservados en
`E:/DayZ-Baltic-Build/shape-repair-20261025/unpromoted-feasible-witnesses-20261026`.
La revisión inicial de Fable acertó el mecanismo matemático, pero su afirmación
de que no había alternativa más simple queda refutada por esa comparación.

Cambio mínimo: permitir `--hybrid-witnesses` también sin `--retain-candidate`.
La selección de pares ya está implementada en `repair_free_shapes_ev112.py:67`;
la rama de retención y todas sus comprobaciones permanecen iguales. El modo
predeterminado no cambia. Se conserva la identidad de solver y el consumidor
global independiente de picos, pozos, pendientes, aristas, agua y protecciones.

Último candidato de esta unidad: una ejecución híbrida fresca para ese grupo.
Mantener ápice fijo, vecinos libres a24m, delta<=0,75m, suelo/coronas exactos,
descenso de energía y todos los criterios anteriores. Si pasa, rederivar
máscaras, verificar todas las coronas, regenerar bury/huella sin diferencias,
consumir carreteras y censo global. Revisión Fable del diff mínimo y evidencia
antes de promover. Los demás hallazgos permanecen abiertos; sin nuevas rondas
arbitrarias ni cambios de umbral. La base y navegación activa no se alteran.

Este candidato es solo offline hasta su composición, compilación, bosque y
sonda propias. No hereda las607consultas de la navegación kit7 en generación.
