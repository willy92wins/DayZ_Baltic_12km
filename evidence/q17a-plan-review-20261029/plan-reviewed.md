# Q17A — corpus independiente para detectar contornos artificiales

Estado: BORRADOR_PENDIENTE_DE_REVISION. Primera unidad de Q17 que habilita Q02B; puede avanzar separada de Q04/carreteras. No cambia mapa, etiquetas físicas ni umbrales de aceptación.

## Alcance y fuentes

Q01 ya conserva nueve rechazos humanos y cuatro controles de alcance, con C1 NOT_REVIEWED. Su ledger no contiene una localización exacta de todos los defectos. El Q02A guardado mide giros de 1030 cadenas, incluido cierre, pero no naturalidad, periodicidad ni arcos artificiales. No repetir ambos productores.

Fuentes [EXACT]: evidence/rejection-coverage-q01-20261029/contract.json, ledger.json y sources/ conservan los bytes de doce JSON verificados. tools/quality/verify_rejection_coverage_ev112.py es consumidor declarativo separado. Q02A documenta círculo poligonal fino sin giro>=45, que NO demuestra naturalidad. plans/quality-council-procedural-map-20261029.md:Q17 exige distinguir casos humanos, naturales/diseñados y mutantes independientes por clase; Q02B exige calibración antes de umbrales.

Hipótesis: un corpus cuyo contexto/expectativas estén fijados fuera del detector permite descubrir tanto omisiones (L, dientes, rectas/arcos regulares) como rechazos indebidos de formas diseñadas. Esta unidad valida el corpus, no un clasificador de belleza.

## Contrato y entrega [DESIGN]

Dos partes separadas y con esquema cerrado:

1. Referencias humanas: los nueve IDs de Q01 con hash/puntero al veredicto, alcance y estado de localización original. Los cuatro controles se conservan por dimensión; bosque/c0 no aceptan otras zonas, calzada49 no acepta río49, C1 no tiene veredicto. Las fotografías siguen REFERENCE_ONLY; no unir puntos por cercanía al avatar. Esta parte hereda fuentes, no duplica citas ni crea una nueva aceptación. Ausencia de geometría exacta se expresa GEOMETRY_UNBOUND, que impide usar esa fila para calibrar recall espacial.
2. Fixtures sintéticos de ingeniería guardados como arrays literales y metadatos de intención, no generados por el detector: L abierta; entrante L en perímetro cerrado; lengua rectangular; zigzag oblicuo; escalera con esquinas redondeadas; recta larga; arco circular poligonal regular; transición recta-arco; curva irregular suave de referencia sintética. El último NO es un referente natural aceptado. Un par utiliza la MISMA geometría de círculo/recta con contexto DESIGNED_STRUCTURE y UNCLASSIFIED_SHORE: el primero sólo fija que la geometría por sí sola no puede decidir intención, el segundo no recibe ACCEPTED ni REJECTED de producto.

Para cada fixture fijar explícitamente coordenadas, abierto/cerrado, unidad metros, plano XZ, rasgos esperados analíticos (conteo, cierre, longitudes de segmentos cuando exactas, área/perímetro cuando verificables, posiciones de giros no nulos), intención y límites. Un documento externo enumerará los IDs y hashes de las arrays antes de que se escriba el consumidor. El generador de corpus no inventa expectativas leyendo su propia transformación. Mantenerlo pequeño: <=20 fixtures, <=4096 vértices totales.

No asignar etiquetas NATURAL_GOOD por parecido o por pertenecer a reserva. En esta primera entrega natural_positive_count=0 y calibration_ready=false. Los nueve rechazos humanos continúan abiertos; sintéticos no aumentan falsamente el denominador de defectos reales detectados. Si una geometría real se enlaza en el futuro, exige fuente independiente y alcance acreditado.

## Consumidor y negativos [DESIGN]

Consumidor independiente del autor y de Q02A/Q02B: valida identidad externa, cardinalidades, IDs únicos, finitud, cierre explícito sin soldar, ausencia de segmentos nulos, expectativas analíticas y procedencia. No importa el generador ni shape_patterns. Usa aritmética racional en coordenadas racionales, no banda inventada para ángulos. No valida naturalidad ni declara PASS del mapa.

Metamórficos sólo donde preservan exactamente geometría: rotación90°, traslación entera, cambio del inicio de lazo, inversión de orden, subdivisión colineal racional. Identidades/roles/contexto deben conservarse y la correspondencia de testigos se documenta. No exigir invariancia bitidéntica a una rotación arbitraria que redondea. Consumidor verifica transformaciones con fórmulas distintas o arrays esperados independientes.

Negativos: omitir/duplicar caso humano; prestar ámbito de calzada a río; promover C1; ligar fotografía por posición del personaje; fake NATURAL_GOOD; quitar esquina sólo en cierre; alterar un vértice preservando número de puntos; convertir cerrado a abierto; NaN/segmento nulo; cambiar intención sin nuevo contrato; intercambiar fixtures manteniendo conteo. Co-mutación de corpus y manifiesto no debe pasar contra contrato externo anterior. Rechazar intento de calibration_ready=true sin positivos naturales aceptados.

Salida VERIFIED_CORPUS_INCOMPLETE_CALIBRATION sólo cuando integridad y expectativas se cumplen; cualquier contradicción REJECTED_CORPUS. No PASS/FAIL de geometría del mapa, no vínculo automático con 11921 testigos. Q02B podrá medir rasgos multiescala sobre estos fixtures y contornos reales, pero su umbral de naturalidad permanecerá sin calibrar hasta incorporar referentes adecuados.

## Presupuesto y parada

Review de plan90s; autoría de arrays/contrato y código240s; revisión de código180s; suite120s; un productor y un consumidor30s/256MiB cada uno. Artefactos pequeños, sin PBO/WRP/NPZ nuevo, sin DayZ ni lease. Si no puede fijarse una expectativa independiente, la fila queda fuera de las métricas de sensibilidad hasta corregir su contrato; no inventarla para completar un número.

Publicar herramientas propias, fixtures sintéticos y procedencia validada desde public-repo. No copiar geometría vanilla ni cambiar el ledger Q01 histórico. Esta unidad habilita pruebas anti-geometría de Q02B sin esperar la colocación nativa de carreteras; la reparación del mapa y la aceptación visual siguen siendo fases distintas.
