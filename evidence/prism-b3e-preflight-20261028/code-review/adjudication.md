# B3E: adjudicación de la revisión de código

28-10-2026. Fable 5.1 nativo entregó SOUND-with-fixes en 271.875 s.
Identidad, entrega completa y postimágenes intactas en completion.json. Revisión
consumida; una corrección agrupada, sin segunda opinión ni cambio de tolerancias.

1. Aceptado: un ValueError interno no implica rechazo geométrico. El consumidor
   sólo clasifica como REJECTED_BINARY el ValueError exacto con details que emite
   need; errores de lectura, buffer o serialización son INCONCLUSIVE_BINARY.
   Los negativos reproducen normal_raw de 13 bytes y JSON no finito. Se refuta
   la conjetura de que el NaN diagnóstico heredado rompe por sí mismo el informe:
   compare_non_geometry_lods_v31.normalized codifica floats en bits float64 y
   el positivo completo se serializa correctamente.
2. Aceptado parcialmente: exe/hash son telemetría opcional y su AccessDenied
   queda registrado, sin matar una compilación sana. La denegación de memoria
   o identidad sigue deteniendo sólo el árbol propio; continuar sin medida
   permitiría eludir el presupuesto. Ambos comportamientos tienen repro.
3. Refutado: meter.memory no importa psutil; usa ctypes/kernel32/psapi. No hay
   un segundo psutil sin binding en el proceso consumidor.
4. Aceptado: los descendientes observados actualizan create_time si reutilizan
   PID; las observaciones se indexan por PID y nacimiento. No se adopta un
   proceso ajeno por nombre ni un PID sin procedencia del árbol lanzado.
5. Limitación aceptada: B3D no registró versiones de GEOS/numpy/shapely. No se
   inventan retrospectivamente. Antes de juzgar el ODOL se reproduce la medida
   sobre el MLOD sellado con la primitiva original; si no coincide exactamente
   con B3D, INCONCLUSIVE. Se registran las versiones actuales. El test altera
   un ULP float64 del referente y comprueba el cierre. No se relaja el margen.
6. El desempate margen/componente coincide con B3D; índice físico sólo identifica
   la cara actual. Se corrigió además el dominio: los contactos usan las mismas
   12 selecciones del proof, mientras el censo y overlay cubren las 1520. Un
   techo superpuesto no seleccionado no cambia ese referente; tiene regresión.
7. La comprobación transitiva de pins de baseline/PBO/poses se conserva antes
   de cualquier build. Si faltan, el preparador para sin compilar.
8. Identidad de objetos: coincide con las primitivas ya usadas por el lector
   MLOD y B3D. Se conserva el gate real de control antes del candidato, que
   comprobará el archivo completo; fixtures no se presentan como prueba ODOL.

Resultado de la suite final privada: 41 tests PASS, 31.872 s de unittest,
44.484 s del proceso, límite 120 s; hashes de las tres postimágenes intactos.
Recibos en prism-b3e-final-tests-20261028. Código adjudicado para la única pareja
aislada del plan, después de preflight fresco. Sin paquete 201 ni DayZ.
