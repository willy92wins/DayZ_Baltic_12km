# Adjudicación del instrumento de lectura

Fable5.1 nativo157.171s entregó NEEDS-WORK, identidad y postimágenes intactas.
Se aceptó el contraejemplo de clave seconds duplicada: Events ahora separa elapsed
de duración por lectura; un test usa el consumidor real Events en discover completo.
No se ejecutó la sonda real antes de corregirlo. Se aceptó stat para conservar
PermissionError como IO y lifecycle INCONCLUSIVE_CLEANUP si no se acredita retirada.
La carrera en el borde temporal se conserva como inconclusa, nunca falso PASS.

El riesgo de barras de pins no afecta al contrato sellado actual: sus claves
exactas se usaron también en B3E. Se mantiene la identidad textual del recibo
fijado, sin normalizar un contrato histórico ni aceptar variantes no autorizadas.

Primer intento de suite agotó30s y quedó incompleto. La suite tras correcciones
dio15tests funcionales OK pero49.985s de proceso (49.816s unittest): se registra
FUNCTIONAL_PASS_RESOURCE_FAIL, no aceptación. Esto produjo un contraejemplo
adicional verificable: que wait devuelva éxito no demuestra presupuesto monotónico.
Se añadió comprobación final elapsed contra límite y test con wait exitoso/reloj
fuera de presupuesto. No se amplió el límite ni se atribuye causa al host.

La suite R2, postimágenes definitivas, pasa16tests en2.558s, proceso2.734s <30s.
Incluye PID real igual al handle, timeout, limpieza fallida, lectura íntegra con
eventos fsync, cambios de recibos y errores de E/S. El hijo stdlib usa la misma
imagen CPython que ejecuta GIS (GetModuleFileNameW), sin launcher intermedio,
paquetes ni Python global por PATH. Revisión original y recibos fallidos intactos.

Código adjudicado para UNA lectura real de60s, sin build/DayZ/edición de skills.
No segunda opinión sobre el mismo dictamen; correcciones ligadas a contraejemplos.
