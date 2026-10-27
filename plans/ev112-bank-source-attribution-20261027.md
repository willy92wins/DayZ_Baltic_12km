# Atribuir los fallos de altura a la geometría fuente

Estado: EJECUTADO_SOURCE_ATTRIBUTION_ONLY. Consumidor: ejecutor Codex; revisión Fable.
Continúa P7/P10/P14 tras el diagnóstico de formato publicado ff3e9d0.

## Pregunta y alcance

[EXACT] La variante12.5 tiene cuatro fallos, Nav12 otros tres; Nav8 los elimina
pero falla RAM. Los siete tienen superficies nativas y empaquetadas archivadas.
La modificación de NM carece de contrato verificado. No se reabre esa vía.

[HIPÓTESIS] Una corrección de la forma del terreno/orilla podría permitir la
malla menos costosa sin reducir tolerancias. Antes de proponerla hay que saber
si los fallos caen en el lecho, en la ladera de la orilla o en el apoyo exterior.
Esto no demuestra que la regeneración conserve los polígonos anteriores.

[EXACT] continuous_stream_pilot_v31.py:286-319 construye el perfil. qs=-18..18
incluye ±2.25. La lámina tiene ancho4.5m (líneas321-324). La cara water_ext queda
0.25m por debajo de la lámina visual (línea384). |q|≤4 es zona fija del solver
actual, pero no equivale a toda la zona húmeda: |q|≤2.25 delimita la lámina;
2.25<|q|≤4 es ladera de orilla. Distinguir q paramétrico y distancia física:
la curvatura comprime el delantal exterior, por eso q no es siempre distancia.

## Una ejecución, exclusivamente lectura

1. Fijar hashes de superficies fuente archivadas y comprobar igualdad entre
   las copias previas/posteriores de collision-only. No regenerar el autor ni
   usar su estado vivo como si fuera el que produjo el PBO. Citar recibo/hash
   histórico y contrastar con las superficies realmente leídas.
2. Reutilizar los 14 waypoints nativos archivados: ocho de las cuatro consultas
   originales y seis de Nav12. Conservar los siete FAIL y los siete PASS.
3. Interpolar el grid fuente bed con sus mismos índices de triángulo, obtener
   estación/q paramétrico y altura en cada XZ. Comparar altura con la superficie
   nativa y los resultados de ODOL ya publicados. Diferencia fuente/motor>0.002m
   deja ese punto INCONCLUSIVE; es un límite de atribución, no tolerancia de
   navegación. No cambiar0.801 ni el resto de oráculos.
4. Para cada punto, registrar W visual, water_ext=W-0.25, terreno real, altura
   de orilla y banda. Evitar llamar carretera a este Roadway fluvial. Si alguna
   fuente no se puede ligar al artefacto, no diseñar corrección sobre ella.
5. Conclusión: si FAIL en lecho/lámina, no modificar agua para pasar navegación.
   Si FAIL en orilla seca, estudiar después un alisado conjunto de orilla y
   apoyo exterior preservando lámina, calado, extremos, protecciones e islas.
   No bajar bancos al agua ni elevar/cortar agua protegida. Este estudio NO
   autoriza todavía cambios de geometría, despliegue o generación.

## Validación y presupuesto

Una revisión del plan, una ejecución local≤15min y revisión de sus hallazgos.
0runs/0generaciones/0escriturasdeactivos. Criterios:14puntosconidentidad,
7FAIL/7PASSconservados, bandas basadas en interpolación de grid fuente y residuo
contra consumidor. Fixtures: plano con q/estación conocidos, punto exterior,
triángulo degenerado; no producir altura cero ante ausencia de superficie.
Si existe solapamiento se informan candidatos y no se selecciona por cercanía
a Y nativa. Falta de cobertura o desacuerdo se conserva INCONCLUSIVE.

Salida: SOURCE_ATTRIBUTION_ONLY o INCONCLUSIVE_SOURCE_ATTRIBUTION; ninguna
es aceptación de altura/RAM. Antes de cualquier corrección, nuevo plan con
dominio, deltas, métricas de forma, preservación y build/sonda/RAM completos.
Mantener0.801/0.011/2.1,RAM1.10,dispersión5%,015-45protegido. Council tras los
pendientes, no completar fases con observaciones locales.

## Adjudicación Fable5.1

Revisión bank-source-plan-review-20261027 terminada, fuentes intactas. Aceptar:
anclar PBO3d9550bf… y autor8b340a2a… a evidencia nativa; no inferir variante por
nombre. npz original yrv-capped-v2 coinciden en hash9d8caf0f…, pero la atribución
necesita además contraste local con caras/alturas empaquetadas del consumidor.
Usar diagonal de strip_faces y registrar estación/chunk. Si una consulta cae en
los primeros/últimos6m del cauce o tapas añadidas fuera del grid, marcar CAP o
INCONCLUSIVE; no inventar filas de tapa. Separar terrenoWRP, Geometry, Roadway,
láminaW y water_extW-0.25. La comprobación existente de capas se cita y solo se
amplía si falta una de las14. La copia viva del autor coincide porSHA con la
archivada; no ejecutar autor ni limpiar asignaciones inocuas.

Ninguna conclusión cambiará orilla/agua sin plan corrector. El presupuesto de
15min se registra al comenzar la única ejecución, en budget.json de su salida.

Evidencia: evidence/navigation/bank-source-rejected-apron-20261027. No relanzar scripts consumidos. Nuevo plan dry-bank-domain está revisado, pendiente de implementación.
