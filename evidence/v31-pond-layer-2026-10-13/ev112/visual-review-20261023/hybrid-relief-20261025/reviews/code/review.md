**Veredicto: SOUND-with-fixes.** No encuentro ningún defecto que produzca una falsa aceptación. Los tres ajustes siguientes son de fidelidad de evidencia y procedencia, no bloquean la integración del código, pero conviene aplicarlos antes de declarar E candidato formal.

**Lo verificado**

- **Suficiencia del testigo.** Para cualquier a∈P, b∈R vale min(P)−max(R) ≤ h[a]−h[b], así que el par conservado en `tools/terrain/repair_free_shapes_ev112.py:42-44` sigue acotando la prominencia real. La condición usa la base exacta sin tolerancia nueva. Si el par conservado es fijo en ambos extremos, la rama de la línea 46 no lanza porque la forma ya cumple. Camino predeterminado y modo bounds sin cambios respecto a la copia D archivada en evidence.
- **Conservación exacta de D.** Identidad por hashes de terreno, dominios y reporte (líneas 70-72 del autor), deriva de metadatos (73-74), máscara de cambios (76), dominios (77-78), aceptación dentro de objetivo (80), unión de la capa de retoque (81), cobertura de clústeres (83) y coherencia máscaras-estados (85). Los parches nuevos no pueden pisar alturas D porque `use` cae dentro de un slice sin cambios D (95). Puerta global `retained_changes_exact` (145). Todas las puertas globales comparan compuesto contra h0 original, no contra D.
- **Procedencia.** D retenido b0c7caaa coincide con el output de candidate-d; el fixture referencia la base ab96a8f6 y el autor D cef5392, cuyo código de recorte es idéntico al actual (97-112). Aritmética de E consistente: 1347+65+19+15=1446; 66+3+1+1=71; 10 grupos pendientes = clústeres 15,16,28,35,39,44.
- **Float32.** Controles locales sobre el parche redondeado (117), globales sobre h float32 (134), test redondea antes de los consumidores (33).

**Fixes**

1. `repair_guarded_shapes_ev112.py:95`: el guardia solo mira cambios de D, no los de clústeres hermanos ya reintentados en esta misma pasada. Un segundo clúster reintentado cuyo slice contenga vértices cambiados por el primero haría sus controles locales contra un contexto obsoleto. Las puertas globales lo cubren, pero la regla del plan es contexto limpio. Sustituir por `(h!=h0)[sl].any()`. Por geometría de representantes, en E los clústeres 10, 11 y 38 no se solapan, así que el resultado no cambiaría; no lo he verificado contra `target_vertices`.
2. `repair_guarded_shapes_ev112.py:159`: `solver_sha256` se calcula al final del run, no en el momento de importar. Una edición accidental durante la ejecución atestaría un texto distinto del ejecutado. Mover el hash junto a la comprobación de la línea 48.
3. `repair_guarded_shapes_ev112.py:115-116` y `96`: los reintentos fallidos (15,16,28,44) no registran que fueron reintentados ni con qué modo; solo el campo global `witness_mode` lo dice. El clúster 39 arrastra el `error` antiguo de D junto a la nueva razón. Añadir `retried`/modo al ítem y renombrar el error heredado.

**Límites**

- La lógica de composición y procedencia (líneas 68-96, 145) no tiene test unitario. La única evidencia es que el run E pasa sus propios controles. No pido refactor de `main`, pero debe constar.
- La prueba negativa depende de que SLSQP falle con ese fixture; es una regresión real pero sensible a la versión de scipy.
- El hash del fixture es autorreferencial dentro del repo; no se verifica contra el terreno real.
- Los 153 tests PASS son los del log; huella, bordes, forest, build y runtime siguen sin declararse.
