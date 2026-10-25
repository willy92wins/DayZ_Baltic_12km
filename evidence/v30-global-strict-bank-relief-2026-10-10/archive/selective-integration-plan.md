# EV87-S — integración conservadora de una pasada ya calculada

Estado: diseño revisado por Luna en selective-integration-design-review.md y adoptado por root. Autorización viva: avanzar suavizado y corregir fallos reportados. No añade solve, nueva ronda de parámetros ni modifica el agua. B sigue siendo el único baseline desplegado. EV87 original a7146c27 y sus dos FAIL se conservan.

## Distinción necesaria

El contrato absoluto de representación FALLA también en B por caras físicas a distintas cotas del P por celda y residuo fuera de banda. No se acepta ese defecto ni se amplían tolerancias. La salida nueva solo puede ser PASS_INCREMENTAL_NONREGRESSION: garantiza la intervención del terreno, con discrepancias heredadas inventariadas y abiertas. No equivale a PASS de toda la base, ni a cierre del render.

## Inventario y composición [DESIGN]

1. Una enumeración completa y reproducible B/H sobre las 41008 celdas originales y frontera, usando lectores/clipper congelados214f y9642. Guardar todas las violaciones above-P/above-F, todos los residuos por celda y huecos de soporte a cota nominal; no usar listas truncadas. Su status es informativo, no aceptación.
2. Marcar toda celda con cara física/visible expuesta por encima de campo+tolerancia, hueco H >1e-10m², o déficit/exceso físico fuera de banda >1e-12m² (umbral numérico ya usado para registrar caras). Esto es un filtro conservador, no un permiso para omitir déficits menores: consumidor final aplica los límites originales agregados. No se necesita calificar como correcto el solape heredado para dejarlo inalterado.
3. Rechazar cada parche aceptado cuyo stencil de TODOS los nodos mutables toca una celda marcada. Añadir q79/398/470/565/575/848. Cada celda marcada conservará sus cuatro alturas B bit a bit.
4. Componer NPZ nuevo desde B; en los parches retenidos reconstruir exactamente el punto medio float32 B/dirección almacenada. Registrar nodos, celdas, motivos y hashes de cada decisión. Nunca restar del candidato global ni modificar el original. P/F, máscaras/metadatos/objetos y modelos permanecen idénticos. Probar que la diferencia respecto a EV87 original solo es la restauración completa de los parches descartados.

## Consumidor independiente [DESIGN]

- Verificar el filtro contra el inventario completo, sin importar autor ni integrador. Todos los inputs fijados y rehash al final.
- Recalcular orden, extremos, pendiente, bisagras, p99/sectores completos, máscaras/componentes P/F/mar, cruces <=1m, cotas EV79, protecciones y metadatos sobre el nuevo mapa. No heredar estadísticas de los718 parches originales.
- Recalcular cobertura real ODOL en toda la huella modificada y su frontera. En celdas alteradas exigir gates absolutos de soporte (<1e-7m² agregado), altura P1e-5/F2e-5, residuos fuera de banda <=.002m² agregado y por celda; F parcial con cambios falla/inconcluso; F desconocido solo si sin caras o todas enterradas con margen >2e-5m en todos vértices de intersección.
- En TODAS celdas marcadas/excepcionadas, probar las cuatro alturas B exactas y modelos/transformaciones inalterados. Su exposición real es por ello idéntica; comprobar también métricas locales donde entren en la frontera del nuevo mapa. Inventariar fallos heredados como ABIERTOS, no ignorarlos ni transformarlos en PASS absoluto.
- Cero fallos nuevos frente a B. Probar casos negativos: parche conflictivo retenido, vértice restaurado incorrectamente, vecino fuera de footprint alterado, nueva grieta, plano a altura errónea. No usar solo igualdad de la transformación como verificador del terreno.

Presupuesto: un inventario completo, una composición y una validación del candidato compuesto. No nuevo solve. FAIL detiene empaquetado y conserva evidencia para diagnóstico concreto, no otra búsqueda de parámetros. Solo con PASS incremental explícito se adapta la cadena de build a este tipo de aceptación y se ejecuta surface/package/readback; los pendientes de B siguen abiertos.

Límite de forma: esta unidad rebaja crestas existentes, no demuestra que todas las elevaciones se vuelvan redondeadas. El piloto posterior de perfil ancho se diseñará sobre B o sobre la integración verificada, sin apilar sobre EV87 rechazado.
