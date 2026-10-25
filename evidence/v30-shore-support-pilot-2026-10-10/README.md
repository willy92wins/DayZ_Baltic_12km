# Orillas: diagnóstico y piloto sin promoción

EV82-B (`6c98ab1`) sigue siendo la única preview desplegada. Esta unidad no cambia el paquete, no inicia DayZ ni cierra la base 1.0.

La conservación exacta del cruce de agua fijaba dos crestas secas a sus vecinos sumergidos inmutables. LP local y revisión explican la ecuación; no era falta de intensidad del filtro. P/F local coinciden; el calado de 0,95 m no aplica a esos puntos fuera del corredor.

EV83 permite mover la orilla <=1 m en dos puntos. Bajan 0,53847 y 1,10991 m; energía de las doce bisagras -23,077% y -25,858%; cruces máximos 0,09510 y 0,50952 m. Geometría y cobertura del consumidor independiente PASS, pero **NO PROMOVER**: el segundo pico se convierte en una V axial nueva. Los perfiles completos 1:1 muestran la regresión que una métrica agregada y la gráfica de una sola arista ocultan. El primero también invierte orden con dos vecinos en el entorno8.

Cobertura: ODOL compilados y transforms del 0WZD fuente hash-vinculado al OPRW/PBO; no transforms leídos del motor. Huella física/visible cubierta dentro de 3,77e-13 m2; gana 1,88276 m2 de orilla diseñada, sin pérdida ni nueva exposición en caras secas. P/F y metadatos exactos, protecciones y grandes lagos conservados. El consumidor detectó/corrigió sus propios errores de epsilon, resolución float32, extrapolación de terreno fuera de cada triángulo y conjunto incompleto de bisagras; fixture independiente de una cara ODOL grande sobre relieve quebrado exige 27 m2.

Propuesta aislada de orden (EV84): no se creó candidato. Preservar el orden de ocho vecinos fijos limita el segundo foco a bajar 0,03505 m, por debajo del mínimo material de 0,1 m. El siguiente diagnóstico examina movimientos conjuntos de los vecinos secos sin protección en dos ventanas7x7; aún no es un candidato ni una extensión al mapa. Root censó 48640 vértices fluviales secos de soporte mojado sin otras protecciones, 15173 incidentes a quiebros>30 en 53 sectores de1536m. Es un inventario de geometría, no confirmación visual de 15173 defectos.

Rectángulos grises: investigación de API no halló una sonda pasiva demostrada. GetLODS no devuelve LOD renderizado; SetFixedLOD está bajo ENF_DONE; EOnVisible puede intervenir en la decisión de render y su despacho sobre ponds estáticos es nativo no verificado. No se lanzó otro ensayo ciego ni se cambió material.

Revisión: pilot/review-independent/review.md. Perfiles: pilot/profiles-full-1to1.png. No aceptación gráfica, no push. Terreno completo/P/F externos fijados por hash; deltas explícitos en authoring-report.json permiten reproducir los dos cambios.
