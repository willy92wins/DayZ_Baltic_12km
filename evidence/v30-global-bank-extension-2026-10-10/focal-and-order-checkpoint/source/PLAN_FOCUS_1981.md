# Unidad focal Narva: bajar una cima conservando el agua

Estado: propuesta concreta del integrador dentro del reperfilado Narva autorizado por Guillermo. Revisar antes de generar un candidato. No modifica el piloto seco PLAN_REAL_SECTOR.md ni amplía su dominio. Es una sola modificación analítica, sin solver ni búsqueda de variantes.

## Cambio propuesto y motivo

Base de salida: EV93 seleccionado, `compound-selection/run-02/candidate-terrain.npz`, SHA `6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d`. Conservar B `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0` para la trazabilidad. Deben coincidir bit por bit en `[832:849,362:379]` antes de transferir la cota local. P/F, metadatos, agua compilada, objetos, rutas y todas las otras alturas quedan exactos con la base EV93.

Una sola variable: fila840, columna370, mundo X2220/Z7242. Su altura B/EV93 es `3.73610520362854 m`. Derivar la altura máxima que reduce al menos25% ambas prominencias cardinales de EV92 con vecinos fijos y redondearla hacia abajo a float32: resultado esperado `3.278029680252075 m`, descenso `0.45807552337646484 m`. No escoger altura según el resultado de la validación. Si ese único valor falla una puerta, registrar FAIL y no buscar otro en esta unidad.

La cota conservadora inicial de0.29056m era suficiente, no necesaria. `derive_focus_univariable_bound.py` SHA `ffde2a49fbd5ae9106a68eae4dbbe27ac5565c05723c0795b6daca9b2dbafc39` y resultado `feccc8ebdb9b9ddbf0a5151e5aa49841ae980682a3c2fdd80287d48cf2eb444a` derivan mediante clearance/lambda la cota local estricta `d<2.61110520362854 m` en las dos celdas P/F desconocidas. Esto permite estudiar la altura propuesta sin liberar vecinos; aún no demuestra todas las puertas.

## Contrato de agua específico, sin cambiar el piloto seco

La propuesta anterior645b que congelaba los otros114nodos y limitaba d a0.29056 se conserva como descartada. Esta unidad mueve solo el foco. El plan seco original sigue congelando las huellas ODOL y exigiendo no ganancia total de exposición; esa política no se aplica implícitamente como veto universal a todo reperfilado de orilla.

Esta unidad usa el contrato de producto existente EV90/91, verificado en EV87 `exposure` líneas1428–1455 y CV254–325: cambios del área ya mojada pueden acompañar a un cruce de orilla dentro de1m, siempre que el agua tenga soporte P/F y no haya exposición nueva en caras nativas antes secas, ganancia sin diseño, residuos fuera de banda ni nuevas/empeoradas violaciones. Se registra por separado cualquier aumento/pérdida de área. No se cambia el agua para acomodar la propuesta.

Cuatro celdas incidentes:839369/840369 conocidas con cruce;839370/840370 P/F desconocidas y caras enterradas. No imputar NaN. En conocidas, comparar B/EV93/H con P y F por separado, sus signos, todos los cruces afectados≤1m, soporte nominal con hueco total físico/visible<1e−7m², residuos totales/máximos fuera de banda≤0.002m², ausencia de nueva cara nativa expuesta previamente seca y de ganancia sin diseño. Reaplicar el gate de violaciones de altura del consumidor existente.

En desconocidas, certificar B/H/L32 con las caras compiladas reales conforme a EV91; mantener el margen visible propio2e−5m y la regla física de su implementación. Incluir además contactos de área cero en el análisis de no contacto de esta excepción; el descenso debe ser estrictamente menor que cada clearance/lambda limitante. No trasladar la cota de una celda a otra ni usar bbox como prueba de cobertura. Verificar índice y readset antes/después.

## Forma, presupuesto y protecciones

Reconstruir elegibilidad EV87 del foco desde cls/protecciones/cotas reales. El antiguo `fixed`/`wet_support` de EV79 no sustituye la semántica actual; permitir el foco es una excepción explícita a la máscara de huella del piloto seco, no a reserva, plataforma, obra civil, P9 ni a los mínimos de terreno. Derivar presupuesto acumulado EV79±2m y pisos EV82; aplicar float32 interior. Verificar las cuatro celdas frente al inventario vial/puente y corredor, no solo la clase de su vértice. Si hay P9 desconocido o civil intersectado, mantener exacto y fallar esta propuesta. Mantener fondo1m/calado0.95m allí donde aplique el corredor real.

El consumidor compara primero contra EV93 y también informa la referencia B: una sola altura distinta, metadatos idénticos, nada fuera del foco. Todas las bisagras y triángulos afectados, incluido halo, deben pasar no nueva bisagra>30.0001°, máximos de sector no peores, pendiente≤max(35°,base)+1e−4; p99 por las poblaciones existentes no peor. Coste de curvatura/fidelidad de todos los stencils afectados debe bajar y ambas prominencias deben quedar≤75% de EV93. D8 y mínimos nuevos exactos enfloat32 según consumidores vigentes; sin redondeo adicional tras fijar la altura.

Alcance exacto de la reutilización: se heredan las puertas de agua descritas arriba, no la unidad completa EV90 de85variables. `verify_ev90.py:721-725` pide25% de reducción sobre sus `domain['stencils']` congelados; ese conjunto pertenece a otro dominio y no es la población de esta unidad de una altura. Aquí la puerta de energía es descenso estricto sobre TODAS las filas xx/zz/xz y fidelidad que toquen el foco, con coeficientes fijos de los vecinos y comparación idéntica B/EV93/H. El25% se exige en ambas prominencias cardinales, como ya está fijado. Registrar también el cambio de bisagra máxima incidente y el cambio de energía por familia. No etiquetar el resultado como PASS de las27puertas EV90/91: su nombre propio es `PASS_FOCAL_DELTA_OFFLINE` y cada puerta reutilizada debe quedar identificada.

Para la aceptación global incremental, partir del PASS EV93 global656e676e y demostrar que el delta está contenido en las cuatro celdas y soporte de forma ampliado exacto. Ninguna cara/triángulo ni variable fuera de ese soporte cambia. Reutilizar invariantes globales inalterados solo con hashes y prueba de soporte; si no se puede justificar una puerta global por ese delta, ejecutar su consumidor completo. Un PASS local por sí solo no es PASS global, ni BASE1.0.

## Secuencia y resultados

1. Revisar plan, fuentes/API y derivación f32. Cerrar lectura de agua hipotética y controles negativos antes de exportar terreno.
2. Crear como máximo un candidato aislado EV93+foco, sin sustituir despliegue. Autor y consumidor separados; preservar fuente y hashes.
3. Ejecutar todos los gates anteriores. FAIL/INCONCLUSIVE bloquean promoción. No segunda altura, cambio de agua ni ampliación del dominio en esta unidad.
4. Solo si pasan los gates incrementales, integrar como capa separada sobre EV93. Compilación, readback nativo y revisión visual son etapas posteriores. No afirmar que este punto arregla todos los taludes.

Presupuesto de esta unidad: una generación/consumo numérico, máximo120s para comprobaciones locales (hashes/lectura de índice aparte), sin cliente DayZ. El bloqueo gráfico sigue pendiente de cambio externo de escritorio. La revisión independiente de gates está en `focus-1981-water-exposure-review.md` SHA `c3eb476aff2ca7a97c86a392477b6d14188a9ff02c145bf4699740da9792481f`.
