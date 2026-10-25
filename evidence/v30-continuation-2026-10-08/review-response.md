# Contraste de la revisión de Claude

Claude Opus 5.5 revisó 71131f5 en solo lectura, con 21 fuentes de la lista autorizada, sin herramientas ni red de búsqueda. Veredicto recibido: SOUND-with-fixes, sin ejecución de tests. La revisión no alcanza las nuevas reparaciones de este directorio. El contraste siguiente usa archivos reales, consumidores separados y ensayos en motor.

| Hallazgo | Contraste y acción |
|---|---|
| P2-1 reserva | Confirmado con precisión de dominio: 483 vértices de reserva vial, 0 de reserva natural. El precedente que elevaba fondos no autorizaba rebajarlos. Generador y gate corregidos; la solución con reserva vial fija es INFEASIBLE. La propuesta anterior deja de ser aceptable con una decisión de fondo solamente. |
| P2-2 positivo alto seco | Confirmado: 693 pierde su valor como positivo y el lector anterior no lo exigía. El nuevo gate rechaza aquella serie. V3 conserva sus coordenadas como control seco explícito y añade 2001 antes del lanzamiento, sobre un plano real de 4,70 m. Los 18 puntos pasan y cuatro negativos se rechazan. |
| P2-3 planos declarados retirados | No reproducido en el paquete: 0 centros retirados cubiertos por pond. Se añade contraste de matrices emitidas, prueba de caras retenidas y control de tierra seca. Reinsertar un modelo real sobre una celda declarada retirada es rechazado. |
| P2-4 mezcla con corredores | Descartado para los 19 corredores congelados: 0 celdas compartidas con removed_cells. No justifica generalizar a otros corredores. |
| P2-5 huecos entre vértices | Confirmado: 698 caras mojadas contienen un hueco de 1,813 m². Dos coordenadas dan pond=0/62 en motor. R1 cubre la interior pero no la diagonal. R2 añade solape, conserva el mismo observador y se contrasta en gap-verification-r2.json. |
| P3-1 tormenta | Límite aceptado: se acreditan ajustes meteorológicos y el intervalo observado; no una envolvente máxima de oleaje ni que tormenta sea siempre peor. |
| P3-2 cuentas y redondeo | Los 88 vértices cruzan por primera vez el fondo de 1 m; ninguno estaba ya bajo él. No hay cambios de una ULP: rebajes entre 0,000101 y 0,079369 m. «Agua alta» significa nivel de vértice ≥2 m en este certificado. La reserva vial ahora añade una restricción independiente. |
| P3-3 independencia parcial | Se conserva el límite: la enumeración de caras y planos se comparte, aunque el muestreador es distinto. No se transforma en un PASS del consumidor nativo ni de navegación completa. |
| P3-4 composición | No se ha compuesto la propuesta de calado no aceptada. Si se elige esa vía, comprobar caras compartidas y repetir consumidores afectados, no solo disjunción de clases de vértice. |

Fuentes ejecutables: review-reproductions.json, old-controls-recheck.json, controls-verification.json, channels-recheck.json, channels-fixed-r2.json, compiled-face-verification-r2.json y gap-verification-r2.json. Los veredictos mantienen su ámbito local. No es un cierre de los veinte fallos ni de la base 1.0.
