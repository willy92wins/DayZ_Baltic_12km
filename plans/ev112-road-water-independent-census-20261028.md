# Censo independiente de contactos carretera-agua
Estado: EJECUTADO_CENSO_VALIDADO. Unidad de diagnóstico, sin autoría ni DayZ.
Codex ejecutor/integrador por petición viva; Fable revisión independiente.
Deriva de P9/P11/P14 y ROAD-CROSSING-VIS de la visita: carretera partida por río
cerca del personaje (4789.51465,5516.52197). Esa posición NO identifica por sí
sola el cruce ni autoriza a colocar un puente allí.

## Descubrimiento verificado
[EXACT] tools/terrain/verify_roads_v30.py:38-41 obtiene las líneas de referencia
desde xy de tests/regional_foundation_roads_v6/reference.npz y los índices de
evidence/regional-foundation-v1/road-grade-chains-v6.json. Hay 124 cadenas,
36428 nodos y 36467 aristas; fuente actual del gate de carretera, no prueba
de todas las carreteras OSM ni de calzada pavimentada/importada.
Esos dos datos existen en el workspace principal, NO en este worktree:
C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev.
SHA NPZ 94ecbca61bd5ba9ba61f89b765b043676a4a65703729a0b69009ae233984a1c2;
SHA cadenas b31fb7d72398981ee98132ce59eab48c4aa404043718475fbb2725b13de1b824.
El gate actual excluye proximidad al agua/Narva/extremos; su PASS no cubre cruces.
[EXACT] tools/water/shore_ramp_v31.py:161-200 define agua por esquina, mar .75m
sin charca, field donde plane es finito, triángulos NW-NE-SE y NW-SW-SE.
Se usarán terreno815ef8b7 y footprint084171b0 del censo nativo ya validado.
No se leerá crossings-ev106 ni la lista generada de puentes para descubrir
contactos: introducirlas aquí repetiría su posible omisión.

## Método y entregable
[DESIGN] Censar TODO el eje de cada cadena, incluso extremos y tramos completos
bajo agua, mediante intersección analítica con la triangulación nativa de6m.
Descomponer cada arista en parámetros t donde cruza X=6k, Z=6k y X+Z=6k;
la diagonal nativa tiene X+Z constante. Cada intervalo pertenece a una cara.
Evaluar H-W linealmente en ambos extremos con coordenadas baricéntricas de esa
cara. Si cambia de signo, resolver la raíz exacta; guardar intervalos mojados,
secos y contactos H==W, cara, cadena/arista, estaciones y coordenadas.
No muestreo cada N metros: una lámina estrecha entre muestras debe aparecer.
No construir polígonos cerrando cadenas abiertas ni decidir húmedo por paridad
de intersecciones: ambos mecanismos pueden omitir extremos sumergidos.

Aristas coincidentes con borde de celda/diagonal: evaluar las caras incidentes
a ambos lados. Si agua interpolada difiere, conservar ambas clasificaciones y
marcar AMBIGUOUS_WATER_BOUNDARY; nunca escoger silenciosamente una celda.
Fuera de rejilla, arista nula, dato no finito o cobertura incompleta no son PASS.
Conservar intervalos pequeños y tangencias; no soldar huecos con tolerancia
inventada. El umbral geométrico del residuo sigue1e-9m como el censo previo.
Separar agua nativa nominal de cobertura de modelos3D, aún NO EVALUADA.
Los contactos no significan automáticamente puente ausente: algunos tienen
puente correcto, vado u otra intención. Esta unidad no acepta/rechaza puentes.

Comprobar que el multiconjunto de aristas no dirigidas enumerado por las cadenas
coincide exactamente con edges del NPZ de referencia; también longitud total.
Registrar cada arista aunque resulte seca. Exportar tablas JSON/GeoJSON de
intervalos mojados/contactos, cobertura por cadena y contexto de Narva,
kit118 y la posición reportada, ordenado por distancia sin atribución automática.
Mantener polígonos, capas y datos originales inmutables, con hashes antes/después.

## Consumidor y controles
[DESIGN] Consumidor independiente: en fixtures pequeñas, recortar polígonos de
triángulos mojados contra líneas mediante Shapely y comparar intervalos/longitud
con el recorrido de caras. No importar el recorrido del autor como oráculo.
Controles: río transversal; río menor que paso de muestreo; carretera íntegramente
sumergida; entrada/salida en extremo; tangencia; recorrido sobre arista nativa;
agua discontinua a ambos lados de una arista; componente con isla seca; camino
seco; inversión del recorrido; división de una arista sin cambiar geometría.
Negativos: arista omitida/duplicada, coordenada no finita/fuera de rejilla,
field no finito en charca y partición con hueco deben fallar con motivo.
En producción verificar cobertura completa de124/36467 y particiones [0,1]
sin huecos, solapes ni longitud perdida. Comparar raíces producidas con segmentos
del censo nativo guardado por cara, sin usar ese censo para descubrir contactos.
Ausencia de raíz en una cara totalmente mojada es válida y se cuenta explícitamente.

## Presupuesto y criterio de cierre
Una revisión de plan y otra de código, hasta una corrección conjunta demostrada.
Una ejecución sobre mapa hasta120s/2GiB medida dentro del intérprete real,
con cierre INCONCLUSIVE_RESOURCE si excede; no duplicar ni relanzar sin cambio
de hipótesis y plan. Sólo13MB de terreno y arrays necesarios del footprint/roads;
no full WRP ni modelos en esta unidad. Pruebas antes de producción.
CENSUS_COMPLETE_NOT_BRIDGE_ACCEPTANCE sólo si invariantes y consumidores pasan;
NO_CONTACT en una cadena no equivale a carretera jugable ni cubre ancho lateral.
Fallo de datos o cobertura: REJECTED; dato/recursos faltantes: INCONCLUSIVE.

## Continuación
Con el censo íntegro, preparar el cruce independiente contra geometría real de
Roadway de todos los puentes desplegados y contra láminas3D del kit. Allí medir
alineación, anchura útil, continuidad y extremos, sin usar el inventario de
puentes como universo esperado. Proponer reparación por clase, no por punto.
No borrar restricciones por detectar conflicto. Los33 anillos congelados y
9regresiones de relieve tienen evidencia separada; la charca oriental sigue
parcial/INCONCLUSA. RAM, c1, forma visual, conducción y council permanecen abiertos.

## Adjudicación de la revisión de plan
Fable5.1 nativo,156.641s, SOUND-with-fixes; ninguna escritura ni permiso denegado.
Se incorporan los siguientes controles antes de implementar:
- La clave edges SÍ fue enumerada en la sonda inicial:36467x3 float64. Verificar
  otra vez presencia y estructura; si falta, detener INCONCLUSIVE, sin fabricar
  un grafo desde las propias cadenas ni aceptar cobertura menor. Nodos compartidos
  entre cadenas son válidos; aristas duplicadas/omitidas deben detectarse.
- WATER_STEP_AT_CELL_CUT registra cualquier salto entre valores de agua a ambos
  lados de un corte, con ambas caras y estados, incluso sin raíz H-W. No exigir
  cruce por cero para esa transición. Fixture de salto sin raíz obligatoria.
- CONTACT_INTERVAL para H-W idénticamente cero; H==W nunca es mojado.
- En borde compartido, consumidor por cara y ambas clasificaciones si difieren;
  no sumar longitudes duplicadas. Comparar la unión geométrica sólo para el total.
- Coordenadas locales comprobadas en [0,12282], sin clip silencioso. El límite
  exterior exacto es válido con su única cara incidente; sólo valores FUERA del
  intervalo se rechazan. Se corrige así la sugerencia contradictoria de rechazar
  x==ZTOP, que el propio dominio inclusivo permite. Selección por punto medio.
- Censo independiente fijado: native-shore-census-20261028/native-shore.npz,
  SHA b6612009ff531ef2f3932240ea52cf0660bce97f7904b7d667f962ce0fd95847.
- Deduplicar parámetros t idénticos, no borrar intervalos pequeños. Errores de
  interpolación/raíz <=1e-9m. Para comparación de longitud en fixtures, error
  absoluto <=1e-9m; en partición global comprobar cada arista con ese mismo
  límite y reportar suma residual, sin ocultar un fallo local por agregación.
No se rebaja tolerancia ni se habilita reparación de cruces por esta revisión.

## Revisión de código y corrección única antes de producción
Fable5.1 nativo310.516s, SOUND-with-fixes. Se incorporan conteo explícito de
partes mojadas sin raíz interior, longitud mojada por unión (sin doble conteo
de caras incidentes), identidad de cada cara en NPZ y tests de raíces ausentes
o desplazadas. La sonda del grafo real ya confirmó la tercera columna de edges
como longitud euclídea:124cadenas/36467aristas,107180.66864263683m.
Regresión propia adicional: al dividir una arista exactamente en un salto deW,
los dos tramos retenían el agua pero perdían el evento explícito. Ahora se
comparan también todas las caras incidentes por nodo del grafo, incluso entre
cadenas. No depender del modo de segmentar el eje para descubrir un salto.
Los slivers de1ulp se CONSERVAN, sin agrupar t ni borrar intervalos: marcar
NUMERICALLY_AMBIGUOUS_WATER_STEP cuando la selección de caras sea numéricamente
ambigua, sin convertir ese evento en salto confirmado ni defecto de puente.
Fixture específica reproduce dos slivers cerca de(6,6) y comprueba esa etiqueta.
La corrección conjunta consume la ronda prevista. Ejecutar20tests y después una
única corrida de producción120s/2GiB; no autoría de terreno ni despliegue.

## Resultado
20tests PASS. Única corrida exit0, sin failure/resource-stop,4.594s dentro del
intérprete125272 (launcher116600); pico residente306495488B/commit801845248B.
124cadenas/36467aristas,107180.66864263683m de eje,74357particiones completas.
770aristas con contactos en29cadenas; unión mojada nominal1929.1251683987339m.
92raíces contrastadas con censo nativo, residuo máximo2.57244e-12m;1313partes
de cara mojadas sin raíz interior.65saltos W dentro de aristas,0en nodos,
0ambigüedades numéricas o de agua en producción; fixtures conservan esos casos.
El contexto más cercano a4789.51465/5516.52197 es cadena49/arista301,11.601m;
no constituye asociación exacta de la captura ni prueba de ausencia de puente.
En kit118, el contacto nativo más cercano a la parada está a1086.304m: el
problema del extremo del kit sigue en cobertura3D NO EVALUADA, no se cierra.
Evidencia road-water-census-20261028; próximo paso: descubrir/vincular geometría
real desplegada de puentes y agua3D y revisar el plan de superposición completa.
Sin nuevo candidato de terreno, MLOD, build ni run. No repetir esta ejecución.
