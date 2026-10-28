# Incidencia exacta del agua: corregir falso contacto sin relajar tolerancias

Estado: EJECUTADO_DIAGNOSTICO_VERIFICADO. Codex ejecutor/integrador; Fable revisor.
Continuación acotada del censo Visual/H/W revisado. No modifica mapas ni agua.
Censo anterior213.093s,201modelos/299567partes, CONSUMIDO, NO VALIDADO globalmente.
Su resumen es exploratorio: no publicar como unidad aceptada.

## Causas verificadas y reparaciones
1. Consumidor1 restaba alturas float32 antes de promover. Experimento pareado
   cs_65p0_0_0000/cara891 aisló6.519258e-9m; promover y primero deja0. Código
   *_float64 consume límites originales1e-7m²/1e-9m. No ampliar criterios.
2. Consumidor2float64 se detuvo en cs_65p0_0_0012/cara196 por NaNdiscordante.
   Productor incluyó agua global635(modelo65_0012/cara5) donde ambos triángulos
   sólo comparten arista. SATcon enteros exactos(grid1/512) devuelve solape0
   en dos ejes separadores; GEOS devuelve LineString/área0. Clippingfloat de
   la subdivisión nativa introdujo área espuria y membresía de agua falsa.
   Evidencia R/pilot-exposure-contact-discriminator-20261028.json.
   No inferir que todo desacuerdo futuro tenga esta causa.

## Implementación propuesta
- pilot_exact_incidence_ev112.py: SATestricto con enteros Python sin overflow
  cuando las coordenadas verifican exactamente grid1/512. Otros inputs pasan
  a intersección de triángulos con Fraction(float), conserva el valor binario
  exacto recibido. No redondear coordenadas para forzar el grid.
- Candidatos agua descartados por SATsólo si no hay área positiva matemática.
- Cortes comunes lecho/nativo/agua cerca del redondeo se recomputan con
  racionales sobre los TRES triángulos originales. El umbral numérico de
  despacho selecciona backend exacto; nunca significa descartar área pequeña.
  Una intersección diminuta positiva sigue presente. Sin epsilon de alturas.
- Refine conserva triángulo nativo para ese cálculo. Capas de agua siguen
  globales, no sustituir por agua nominal ni “sumergido=invisible”.
- Pareado del caso real corregido:0carasagua en ambos algoritmos, área residual
  7.62e-14m² y altura0. No es prueba del censo entero.
- 7fixtures exactas: arista real, punto, solape, lámina positiva diminuta,
  corte común nativo sólo en punto, winding inverso, traslación a10000m.
  15integración pasan;12kernel previas. Añadir las recomendadas por revisión.

## Presupuesto y cierre de esta ronda
Revisión nativa≤600s/1200palabras, después fixes/tests.
Un preflight NUEVO pilot-visible-exposure-preflight-r2-20261028≤120s/2GiB:
benchmark192caras estratificadas, estimación25%margen debe quedar≤600s.
Una producción NUEVA pilot-visible-exposure-census-r2-20261028≤600s/2GiB.
Un consumidor NUEVO-float64 referido a r2≤600s/2GiB, nunca importar SAT/clip
del productor en la comprobación independiente. Si difiere GEOS en contactos,
conservar fallo y resolver con oráculo exacto independiente, no añadir epsilon.
Controles originales sin ampliar1e-7m²/1e-9m. Hash/PID real y outputs únicos.

Producción/consumidores/repro previos CONSUMIDOS. No repetirlos ni borrar fallos.
Cualquier discrepancia nueva termina la ronda y exige mecanismo/hypótesis
revisados y presupuesto nuevo. No publicar censo por cantidad de tests.
Reparación física/candidato seco/viabilidad de protecciones todavía posterior.

Revisión Fable167.016s SOUND-with-fixes, inputs inmutables,0denegaciones.
Fix1: guarded_intersection devuelve bool exact_positive separado del polígono
float; membresía no se pierde si vértices racionales distintos redondean a un
solo punto. Área float puede0, membresía exacta se conserva (fixture a10000m).
Fix2: fixture corte espurio positivo1e-12m² en contacto triple trasladado10000m
demuestra despacho a racionales y área exacta0; sliver verdadero sigue presente.
Fix3: semilla racional degenerada falla igual que SATentero.10fixtures exactas,
15integración+12kernel. No cambia ningún límite ni ninguna geometría del mapa.



## Resultado verificado

R2 EJECUTADO_DIAGNOSTICO_VERIFICADO,201modelos/185744caras/299567partes;37fixtures.
Consumidor independiente GEOSglobal154s verifica todas18métricas; máximos
residuales3.22e-12m²/9.98e-13m. Producto/tolerancias/geometría intactos.
Fallos previos conservados,75contactos falsos eliminados en34modelos.
Evidencia evidence/pilot-visible-exposure-20261028. No relanzar scripts consumidos.
Candidato/viabilidad de protecciones/reparación física aún pendientes.
