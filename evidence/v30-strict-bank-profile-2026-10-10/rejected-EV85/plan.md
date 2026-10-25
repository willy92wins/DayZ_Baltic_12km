# EV85 - suavizado conjunto de dos parches de orilla

Propuesta concreta para revisión; ejecutar solo tras factibilidad LP corregida/congelada y revisión del diseño. Fuente: EV82-B f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0. EV83 no promovido; EV84 aislado no se llegó a escribir.

## Motivo y alcance

Mover una sola cima genera una depresión transversal; conservar el orden de vecinos inmóviles bloquea el descenso material del segundo foco. Se mueven conjuntamente únicamente vecinos secos sin protección de dos parches 7x7 VÉRTICES, centrados en (r1880,c191) y (r1785,c366). El anillo exterior está fijo; los interiores potenciales son 5x5. El diagnóstico LP enumera explícitamente cada variable, excluye agua en cualquier P/F/mar, other_fixed, engineering_halo y large_lake_banks. No se cambia ninguna otra altura ni metadato del mapa. El tercer punto húmedo queda fijo.

Presupuesto acumulado y suelo reconstruidos desde EV79 candidate dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c, como EV82-B: max(h79-2,min(h79,1.8),min(h79,max incidente(P/F/.85)+.0001)). Tope min(B,h79+2). No usar las cotas antiguas guardadas que ya incorporaban wet_support fijo.

## Invariantes [DESIGN]

- Todo nodo mutable solo baja. Ambos focos bajan >=0,1 m desde B.
- Conservar orden B en TODAS las aristas de 8 vecinos que toquen cualquier variable, incluidos vecinos fijos lexicográficamente anteriores. Signo positivo permite cero pero no negativo; signo negativo permite cero pero no positivo; igualdad B conserva igualdad. Sin mínimos ni máximos axiales nuevos en el parche completo.
- P/F byte-exactos y signos mojado/seco separados por superficie/celda/cara intactos. Todos los cruces se desplazan <=1 m desde B; componente/conexiones y frontera de cada parche P/F intactas, verificadas geométricamente. Los extremos mojados son fijos; si un cruce tiene ambos extremos variables, detener en lugar de usar una fórmula escalar incorrecta.
- Fondo/corredor, playas, carreteras/plataformas/halo, controles, grandes lagos y demás máscaras exactos. No modificar objetos, materiales ni niveles.
- Geometría angular respecto a B: 0 bisagras nuevas >30 grados con tolerancia de clasificación exacta del consumidor 1e-4; máximos por sector no peores (tolerancia 1e-4 grados); pendientes <=max(35,pendiente B); energía de las 12 bisagras de cada foco baja >=1%; energía de la unión deduplicada de bisagras afectadas baja. No sumar varias veces una arista compartida por variables.
- p99/conteo son puertas POST-SOLVE sobre el mapa completo cuantizado a float32; no se convierten en restricciones suavizadas del optimizador. Reproducir el dominio/agrupación del consumidor EV82 `review-luna/verify.py:224-301, 374-424`: bank e interior secos, `incident_all`, tres tipos de bisagra concatenados, `np.percentile(...,99)` y conteo exacto `angle > 30`. Para aceptar: `n` idéntico a B; p99 <= p99(B)+1e-4°; conteo >30 <= conteo(B). La referencia es el estado EV82-B (`review-luna/report.json`, SHA de terreno `f9fb23de...061f0`, status `PASS_EV82_CONSUMER`): bank `(n=1591990,p99=4.982070186774692°,count=1)` e interior `(n=7170630,p99=3.667753611431574°,count=112)`. El gate de nuevas >30 también es post-solve exacto: en bisagras incidentes a vértices cambiados, cero con `B <= 30+1e-4` y candidato `>30+1e-4`.

## Solución propuesta [DESIGN]

Un solve SLSQP por parche, variables de altura continuas con cotas y restricciones lineales de suelo/orden/cruce. Inicio factible respecto a las restricciones lineales, próximo a B. Minimiza la suma de ángulos al cuadrado sobre la unión deduplicada de bisagras afectadas. Restricciones de desigualdad diferenciables: pendientes, máximos sectoriales por bisagra, cap de 30° donde B estaba <=30°+1e-4, descenso de energía de las 12 bisagras de cada foco. p99/count y el conteo de nuevas >30 se recalculan solo después de cuantizar float32 y se aceptan/rechazan contra los valores exactos de arriba; no se usa sustituto continuo. No se llama LP a esta optimización: el LP previo solo prueba que las restricciones lineales permiten bajar los focos.

Presupuesto: un solve por parche, máximo150 iteraciones y120s en total; una corrección permitida exclusivamente por error de implementación. No cambiar límites para obtener PASS. Cuantizar todas las alturas a float32 y recalcular TODOS los gates; cualquier fallo rechaza la propuesta, sin slack añadido ni fallback oculto. No crear otro candidato variando parámetros.

## Consumo y salida

Consumidor independiente, sin importar el optimizador: dominio/identidades/orden/aristas/extremos, agua/cruces/components, ángulos y protecciones. Negativos reales EV83 para inversión axial; fixtures de vecino fijo anterior, identidad de meseta, cruce>1m, inversión mojado/seco, nuevo>30 y agujero ODOL. Cobertura con ODOL compilados y transforms del 0WZD fuente de B hash-vinculado al OPRW/PBO, con la limitación explícita de que no son transforms de readback del motor. Cada cara ODOL se cruza por separado contra cada triángulo nativo, nunca extrapolando terreno fuera de la celda. P/F diseño menos unión compilada expuesta <=.002m2; ganancia fuera de diseño no aumenta>.002m2, cero exposición en caras previamente completamente secas o fuera del campo diseñado. Fixture relieve6x6 con SE=6 y agua3 cubierto por caraODOL grande debe dar27m2.

Perfiles completos36m 1:1 B/EV83/EV85 en ambos ejes y diagnóstico de máximos/mínimos/mesetas, sin presentar energía como aceptación artística. Si pasa, todavía no es una extensión global: el mapa completo necesita dominio e interacciones revisados. No empaquetar ni desplegar ni arrancar DayZ en esta unidad. EV82-B sigue operativo.
