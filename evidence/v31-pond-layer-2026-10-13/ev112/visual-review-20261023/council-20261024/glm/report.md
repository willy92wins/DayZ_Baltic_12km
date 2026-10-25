# Council de cobertura — terreno triangular (paso 6 m, diagonal fija NO-SE)

Marco previo, tres reglas que ordenan todo lo demás:

- **R1.** Ningún número nuevo (20°, radios, densidades) se promueve a umbral sin origen: contrato ya aprobado, escena vanilla equivalente, o estudio de calibración humana pareado. Donde digo "tolerancia a calibrar" no propongo el valor.
- **R2.** En rejilla triangular hay escalonado inevitable: la firma angular de las tres familias de aristas es parte del medio, no el defecto. Toda medida angular debe **restar primero la firma de rejilla** (medida sobre terreno vanilla o sobre la propia familia en zonas planas de referencia) y solo el residuo es candidato a defecto. Confundir eje con escalonado es el falso-positivo clásico.
- **R3.** Los tramos de camino excluidos (vecindad de agua, presa, extremos) no son "aceptados": son *no medidos*. Una prueba que los trate como PASS es fabricante de falsos PASS.

---

## Prioridad 1 — Firma multiescala del suavizado (anti-pirámide y anti-aplanado)

- **Mecanismo del defecto.** Un suavizado por celda única escala rompe continuidad C1 entre celdas vecinas: aparencia de pirámides/terrazas alineadas a la diagonal; a la vez, un suavizado agresivo destruye relieves legítimos. Un solo número global (p. ej. un censo de ángulos) no distingue "escalera real" de "relieve natural empinado".
- **Variable observada.** Energía de curvatura discreta por banda de escala: para cada vértice, Laplaciano umbrela con 1, 2 y 3 anillos de vecindad; se agrega por octava la norma al cuadrado. Defecto piramidal = pico anómalo de energía en la banda de 1 anillo concentrado en la familia NO-SE, con salto de normal entre celdas adyacentes que comparten arista.
- **Algoritmo. (a)** Restar la firma de rejilla (R2): comparar el histograma de saltos de normal por familia contra el mismo histograma del vanilla o de zonas de referencia; el residuo por familia es la señal. **(b)** Ratio de energía E1/E2/E3 por región; pirámide = E1 dominante con orientación coherente con la diagonal fija; sobre-suavizado = caída de E2/E3 frente a vanilla en zonas que el contrato declara de relieve.
- **Tolerancia.** Residuo angular y ratio de energías: contra **vanilla** (escena equivalente) o **calibración humana** pareada. El 20° queda como bin diagnóstico para *localizar* dónde mirar, nunca como gate.
- **Positivo que debe pasar.** Terreno natural con crestas curvas: energía repartida entre bandas, residuo angular sin pico direccional.
- **Negativo que lo mata.** Si alguien aplana la geografía para pasar el test de saltos, la caída de E2/E3 frente a vanilla dispara el otro lado: no se puede pasar aplanando.
- **Fuente independiente.** Malla vanilla; muestreo GIS de crestas para saber dónde *debe* haber energía.
- **Coste.** O(N·constante por anillo); una pasada por regeneración, segundos para rejillas de mundo abierto por chunk.
- **Límites.** No localiza el *origen* del suavizado (máscara vs kernel); solo certifica el síntoma. Sensible al radio de vecindad elegido: fijarlo por contrato, no por ajuste al caso.
- **Clase.** Diagnóstico + FAIL mecánico (residuo direccional) + insumo para aceptación visual.

## Prioridad 2 — Grafo de cauces: continuidad, curvatura y extremos con oracle GIS

- **Mecanismo.** El suavizado y el remallado pueden partir un cauce en segmentos que la rejilla conecta "a escuadra" (quiebres en nodos de la diagonal), o dejar extremos colgados que en juego se ven como arroyos que nacen/mueren en nada.
- **Variable observada.** Sobre el grafo de talweg (acumulación de flujo sobre la rejilla, corregida por la anisotropía de la diagonal): (a) cambio de rumbo entre segmentos consecutivos *por debajo de la escala de la rejilla* — un cauce natural curvo cambia de rumbo gradualmente, un quiebre a escuadra lo hace en un nodo; (b) conectividad: todo extremo de talweg debe ser confluencia, nacimiento con cuenca aportante mínima, o salida a borde/agua; (c) continuidad de la línea de agua visible a lo largo del eje.
- **Algoritmo.** Extraer esqueleto de drenaje; para cada vértice del grafo, comparar la poligonal suavizada (spline local) contra la poligonal de la rejilla; el residuo de desviación mide "escuadria". Extremos: clasificación por regla. **No se exige rectitud**: se exige continuidad C1 del eje y extremos justificados.
- **Tolerancia.** Confluencias y puntos extremos: **contrato** (todo cauce debe terminar en algo) — eso es FAIL mecánico sin número nuevo. La curvatura del eje: contra **endpoints GIS independientes** y calibración humana.
- **Positivo.** Cauce meándrico del GIS: pasa con curvatura alta pero continua.
- **Negativo.** Cauce en zigzag alineado a la rejilla: la desviación poligonal-vs-spline y los quiebres en nodos lo señalan; borrar el cauce mata la coincidencia con el oracle GIS.
- **Fuente independiente.** Endpoints GIS y red de confluencias ajenas al productor del terreno.
- **Coste.** Una pasada de flow accumulation + análisis de grafo; bajo-medio.
- **Límites.** En zonas muy planas el flow accumulation es ruidoso: limitar a cuencas con área aportante contractual.
- **Clase.** FAIL mecánico (conectividad, extremos) + diagnóstico (curvatura).

## Prioridad 3 — Coherencia agua: geometría visible vs colisión vs volumen

- **Mecanismo.** El agua son tres capas (caras visibles, volumen de colisión, superficie lógica) que pipelines distintos pueden desincronizar: el jugador flota sobre agua seca, se hunde en agua invisible, o ve orillas con escalones que dejan el casco del jugador fuera del volumen.
- **Variable observada.** Por arista de la submalla de agua, clasificación de adyacencia (agua–agua, agua–terreno, borde libre); emparejamiento cara-visible ↔ celda-de-colisión por solape en planta; distancia vertical superficie visible vs techo del volumen de colisión; en orillas, distancia entre borde de agua y talweg del terreno.
- **Algoritmo.** Construcción del mapa de adyacencia de agua; para cada celda de colisión sin cara visible (o viceversa) → hueco. Muestreo en planta a paso sub-celda: |z_visible − z_colisión| y cobertura; en el borde, que exista cara de orilla coherente para cada arista agua–tierra.
- **Tolerancia.** Existencia de emparejamiento y de cara de orilla: **contrato estructural** (FAIL mecánico sin número nuevo). La separación vertical admisible: vanilla o calibración; no la invento.
- **Positivo.** Orilla escalonada por la rejilla pero con cara de orilla presente y volumen bajo toda cara visible: pasa.
- **Negativo.** Recortar caras de agua para "arreglar" la orilla deja celdas de colisión huérfanas: el test de emparejamiento lo detecta.
- **Fuente independiente.** El volumen de colisión y las caras visibles provienen de generadores distintos dentro del pipeline; el oracle externo es la máscara de agua regenerada por el camino GIS.
- **Coste.** Medio; proporcional al área de agua.
- **Límites.** No valida el *shader* ni el nivel de agua dinámico; solo geometría estática.
- **Clase.** FAIL mecánico + prueba en motor (ver ítem 10).

---

## Resto de la batería (compactos)

**4. Juntas y costuras del camino (extensión del contrato existente).** Mecanismo: los tramos aprobados (3 cm transversal, 6.5 %, cuerda 3 cm/6 m) se validan *dentro* de cada tramo; el defecto vive en las costuras entre tramos y en los bordes de las zonas excluidas. Variable: salto de tangente y de cota en la costura entre segmentos consecutivos, y continuidad del perfil al cruzar el límite de una exclusión. Algoritmo: re-muestrear la polilínea atravesando juntas y aplicar los mismos límites ya aprobados, sin zona exenta en la costura. Tolerancia: la ya aprobada (contrato) — no hay número nuevo. Positivo: camino curvo legítimo pasa. Negativo: partir el camino en tramos cortos para diluir defectos aumenta el número de costuras y el test las cuenta. Fuente independiente: el trazado GIS. Coste: bajo. Límite: no cubre los tramos excluidos en sí. Clase: FAIL mecánico.

**5. Mapa de cobertura de exclusión y drift.** Mecanismo: las exclusiones "no medidas" pueden crecer silenciosamente entre regeneraciones hasta vaciar la prueba de camino. Variable: fracción y distribución de metros muestreados excluidos, por regeneración, con diff contra la regeneración anterior. Algoritmo: histograma de exclusión por causa (agua/presa/extremos) + delta firmado. Tolerancia: contrato de cobertura mínima muestreada (a definir en contrato; el valor no lo invento aquí). Positivo: exclusión estable y localizada. Negativo: inflar la vecindad de agua para esconder tramos malos. Fuente independiente: máscaras de agua/presa ya validadas. Coste: trivial. Clase: diagnóstico + gate de proceso.

**6. Cruces agua–camino (puentes).** Mecanismo: donde la reserva del camino intersecta agua propia, hace falta primitiva de cruce; sin ella, o el camino se moja o el agua se corta. Variable: intersecciones agua–reserva sin elemento de cruce registrado; pendiente del perfil en el cruce contra el 6.5 % aprobado. Algoritmo: overlay de máscaras + clasificación. Tolerancia: contractual (existencia del cruce; pendiente ya aprobada). Fuente independiente: capas GIS de ambos. Coste: bajo. Clase: FAIL mecánico.

**7. Soporte de instancias vegetales.** Mecanismo: la matriz de instancia se calculó contra una versión previa del terreno; al regenerar, el punto base flota o se entierra, y el tronco queda en pendientes imposibles para la especie. Variable: distancia vertical punto-base-vs-terreno-muestreado bajo la matriz; pendiente del terreno en el anillo del radio de tronco. Algoritmo: para cada instancia, raycast analítico contra la malla (no contra la versión cacheada) y consulta de reglas de plantado por especie. Tolerancia: flotación ≤ fracción del paso (6 m) fijada por contrato; reglas de species por tabla de diseño. Positivo: árbol en ladera con base asentada pasa. Negativo: "enterrar" medio tronco para pasar flotación dispara el test de pendiente/protrusión de copa. Fuente independiente: terreno ya cerrado por los tests 1–3 y tabla de especies. Coste: lineal en instancias; medio-alto en bosques densos (paralelizable). Clase: FAIL mecánico.

**8. Distribución y oclusión de vegetación.** Mecanismo: instancias dentro de agua, de la reserva de camino, o copas solapadas más allá de lo que la regla de plantado permite, producen visual "parche" y coste de render. Variable: solape de bounding circles de copa por vecindad; instancias cuya proyección cae en máscara ajena (agua/camino/humedal de otra especie). Algoritmo: grid espacial, conteo de vecinos por radio de copa, overlay de máscaras. Tolerancia: densidades del contrato de plantado; solape extremo contra vanilla. Positivo: bosque denso pero conforme a regla pasa. Negativo: espaciar todo a fila india mata el índice de naturalidad frente a vanilla. Fuente independiente: máscaras de humedal/especie y vanilla. Coste: medio. Clase: FAIL mecánico (árbol en agua/camino) + diagnóstico (densidad).

**9. Prueba en motor: recorridos de cámara con presupuesto de escena.** Mecanismo: nada de lo anterior ve z-fighting agua–terreno, popping de instancias o caídas de FPS por *distribución* (no por conteo global, que no prueba nada). Variable: en recorridos canónicos (talweg, camino, orilla, sobrevuelo a altura media): tiempo de frame por tramo, eventos de z-fighting muestreando profundidad, y coste por área visible — comparado contra escena vanilla equivalente con el mismo presupuesto de instancias y draw distance, nunca contra conteo de objetos. Tolerancia: vanilla; percepción de popping solo como insumo a calibración humana. Positivo: escena densa pero barata por área visible pasa. Negativo: vaciar el bosque para subir FPS degrada el índice de cobertura del test 8. Fuente independiente: build vanilla. Coste: alto; fuera del bucle de regeneración, nocturno. Límite: dependiente del hardware de referencia fijado por contrato. Clase: prueba en motor + aceptación.

**10. Aceptación visual pareada y regresión de máscaras.** (a) *Visual*: capturas pareadas (mismo punto de vista, build vs vanilla o build vs versión aprobada) evaluadas por panel humano con escala de calibración previa; solo decide estética, nunca reemplaza un FAIL mecánico. (b) *Regresión de máscaras*: diff celda-a-celda de máscaras protegidas, agua y conexiones entre regeneraciones; matriz de confusión de clases. Tolerancia: contrato de "celdas protegidas no cambian sin orden de diseño"; el diff es el gate de proceso que evita que la cobertura cambie bajo los pies de los tests 1–9. Positivo: regeneración que solo toca celdas libres. Negativo: re-etiquetar agua como tierra para aprobar camino dispara la matriz. Coste: trivial (a) excluido; medio el panel. Clase: aceptación visual + gate de proceso.

---

## Riesgos transversales

- **Sobre-suavizado silencioso:** los tests de saltos angulares (1) premisan aplanar si se leen solos; por eso el ratio de energía multiescala contra vanilla es prioritario y no negociable.
- **Cobertura que deriva al regenerar:** si las máscaras se regeneran sin gate (10), los tests 4–8 miden un terreno distinto del aprobado; todo PASS queda condicionado al diff de máscaras de esa misma regeneración.
- **Falsa angularidad:** todo umbral angular debe consumarse sobre el residuo tras restar la firma de la rejilla (R2); si no, se "corrige" el escalonado inevitable y se aplana o se rompe la diagonal fija.
- **Sin oracle, sin exigencia cero:** donde solo hay calibración humana (estética general), el resultado es aceptación, no FAIL; no pedir "cero defectos" donde no existe referencia independiente.

**Resumen de prioridades:** (1) firma multiescala con residuo por familia — mata pirámides y aplanado a la vez; (2) grafo de talweg con oracle GIS — mata cauces a escuadra, discontinuos y extremos colgados sin exigir rectitud; (3) coherencia agua geometría/colisión/render — defecto directamente jugable. El resto completa camino, vegetación, motor y gobierno de máscaras.

END_COUNCIL