# Visual201: exposición continua y corredor de referencia

Estado: EJECUTADO_DIAGNOSTICO_VERIFICADO. Codex ejecutor/integrador, Fable revisor.
Implementa la siguiente unidad del plan revisado ev112-pilot-visible-bank-feasibility-20261028.md.
Visual201 ya publicado b61e233:201modelos/185744caras lecho/4760agua/4864CAP;
equivalencia NO orientada verificada. Vectores geométricos fuente/ODOL inversos,
sin atribuir causa ni render. No cambiar caras para resolver esa diferencia.

[EXACT] Inputs y APIs:
- terrain815ef8b7 / footprint084171b0, referidos por hashes completos en código.
- roads94ecbca6, geometría independiente de puentes. Matrices del WRP compilado.
- herramientas A/B publicadas inmutables; modelos Visual201 por manifest.
- triángulos nativos NW-SE (0,1,3)/(0,2,3),6m, row0norte,12282m.
- shapely2.1.2 local set_operations.py:41/114/465, Polygon,STRtree.query.
  intersection/difference/union_all sin grid_size ni set_precision: no snap.
- kernel pilot_surface_refinement_ev112.py: clip afín, subdivisión contra
  todos los triángulos nativos que intersecta cada cara y extremos de B-H/B-W.
  No decide por vértices originales ni reduce tolerancias de producto.

[DESIGN] Censo completo una vez. Por cara, guarda área proyectada, sobre/bajo/
contacto con H, máximos/mínimos en cortes, y agua nominal separada de las caras
Visual reales. El agua puede ser transparente; sumergido no equivale a invisible.
Los solapes con caras de agua conservan referencias a todas; la unión evita
duplicar área bajo capas superpuestas. Número de caras no equivale a capas físicas.

Corredor continuo: unión de rectángulos±4m por segmento. Todos los vértices de
carretera añaden discos conservadores de junta/extremo. Aproximación explícita:
64gono inscrito y circunscrito al radio4m; el anillo entre ambos es INCIERTO,
nunca se clasifica libre. Exceso radial máximo0.004824m; no tolerancia de altura.
Separar área rectangular, interior de disco fuera de rectángulos y anillo incierto.
El ancho es reserva del gate existente, no pavimento medido ni aprobación de paso.

Conservar sumas de caras y unión por modelo; diferencia indica solape proyectado
o ruido numérico, no borrar geometría. Componentes por modelo, nunca topología
global. CAPseparados del cuerpo; posiciones/H/W/agua/modelos NO modificados.
Outliers guardan cara, XZ y triángulo nativo. Mantener candidato seco/viabilidad
de restricciones y reparación como siguiente unidad, no inferirlos de exposición.

Fixtures:12núcleo+8integración iniciales PASS, incluyen saliente interior con
vértices enterrados, plano cubierto/contacto, agua real frente nominal, capas,
triángulo casi degenerado, corredor continuo48m² analíticos, punto cercano sin
solape, contactos y límites de disco. Faltan fixture específica de solape sólo
en junta/extremo y comprobación de datos reales en consumidor independiente.
Un falso positivo de componente por redondeo no autoriza reparación.

Presupuesto:
1. Revisión Fable600s/1200palabras; fixes+fixtures.
2. Preflight≤120s/2GiB:hashes/cobertura/índices de geometría/coste, sin censo.
3. Una producción≤600s/2GiB, particiones201, registro de progreso/PID real.
4. Consumidor independiente≤600s/2GiB, contra MLOD/WRP fuente y geometría
   analítica o Shapely independiente del clip del productor. Extremos/áreas y
   cobertura de todos los modelos; diferenciar subconjunto verificado.
Si falta cobertura, geometría ambigua, dato cambiado o presupuesto excedido:
INCONCLUSO, conservar evidencia y revisar hipótesis/plan antes de otro bucle.
No relanzar scripts consumidos. No DayZ,lease,compilación ni cambio de producto.

## Revisión y adjudicación antes de producción

Fable5.1nativo252.766s SOUND-with-fixes, inputs inmutables y0denegaciones.
Fixes1-2: aristas nulas/índices fraccionarios/no finitos/grafo incompleto fallan
cerrado antes de construir corredor. Fix3: campos de unión/componentes nombran
explícitamente all_categories; métricas aditivas permanecen BODY/CAP separadas.
Fix4: preflight cronometra192caras estratificadas (16por modelo, primero/medio/
último por sitio) y descarta resultados. Estima producción con25%de margen más
setup+15s; si >600s, INCONCLUSO sin producción. Watchdog600s sigue mandando.
Esto es presupuesto de coste, no tolerancia geométrica ni garantía worst-case.

Fixtures ampliadas:27(12kernel+15integración) incluyen agua bajo lecho, cobertura
parcial36/36m², CAPseparado, solape sólo en extremo y anillo incierto conservado.
Consumidor GEOS independiente preparado, sin importar productor: semiplanos
GEOS y buffers de líneas/puntos, contrasta18métricas de todas185744caras.
Cuatro controles analíticos del consumidor pasan. Comparación aritmética
≤1e-7m²/1e-9m; no cambia ningún umbral del producto ni acepta reparación.
Una cara casi degenerada abortará censo global con evidencia parcial INCONCLUSA;
no se descarta para seguir con un subconjunto que parezca PASS. Referencias de
agua en water_refs son globales. Carreteras se leen del checkout primario por
hash, y no de una lista de puentes. No volver a evaluar scripts consumidos.



## Resultado verificado

R2 EJECUTADO_DIAGNOSTICO_VERIFICADO,201modelos/185744caras/299567partes;37fixtures.
Consumidor independiente GEOSglobal154s verifica todas18métricas; máximos
residuales3.22e-12m²/9.98e-13m. Producto/tolerancias/geometría intactos.
Fallos previos conservados,75contactos falsos eliminados en34modelos.
Evidencia evidence/pilot-visible-exposure-20261028. No relanzar scripts consumidos.
Candidato/viabilidad de protecciones/reparación física aún pendientes.
