Para abordar la problemática de falsos pasajes (false positives) y defectos ocultos en el terreno triangular del mundo abierto, es necesario desvincular la estética de las métricas numéricas rígidas y establecer oráculos independientes. El núcleo del problema radica en que el suavizado selectivo, aunque conserva máscaras, puede generar artefactos de escala (ruido vs. forma) y que el censo de ángulos de 20 grados es un bin diagnóstico, no un umbral de calidad.

A continuación, se proponen diez mejoras no redundantes, priorizando las tres que mayor valor aportan a la detección de defectos reales sin distorsionar la geografía natural.

### Mejoras Prioritarias (Top 3)

**1. Análisis de Curvatura Gaussiana Multiescala para Pirámides y Cauces**
*   **Mecanismo del defecto:** El suavizado puede eliminar picos agudos (pirámides) o redondear excesivamente cauces angulares, transformando geometría lineal/diagonal en formas orgánicas indeseadas. Las pruebas de altura media no capturan la desviación local de la superficie respecto a la forma geométrica esperada (triángulo vs. curva natural).
*   **Variable observada:** Curvatura Gaussiana ($K$) y Curvatura Media ($H$) calculadas sobre una ventana de radio variable (3m, 6m, 12m). No usar ángulos entre normales como métrica primaria, sino la desviación de la forma.
*   **Algoritmo implementable:** Para cada vértice, calcular $K$ y $H$ usando vecinos de primer orden. Aplicar un filtro de morfología matemática (ero­sión/dilación en el espacio de alturas) para detectar regiones con $K > K_{umbral}$ (picos) o $H < -H_{umbral}$ (valles profundos). Comparar esta huella digital topológica contra una referencia "ideal" derivada del GIS original (no del vanilla, que puede estar roto). Si un cauce debe ser recto según el GIS, la desviación de la línea central de la cuenca en un intervalo de 50m debe ser < 10% del ancho del cauce.
*   **Origen de tolerancia:** **Contrato de Diseño.** El GIS define la topología macro; el contrato de juego define la rugosidad micro. El umbral no es arbitrario, sino que garantiza que el jugador no pierda la referencia visual del cauce ni que las pirámides desaparezcan.
*   **Positivo:** Detecta si el suavizado ha "aplanado" una pirámide (bajada de $K$ máxima) o si ha curvado un cauce recto (desviación de la ejes).
*   **Negativo que lo mata:** Un valle natural profundo pero orgánico será detectado como defecto si el GIS original lo tenía como cauce recto, pero el diseño final exige curvatura. Esto fuerza a actualizar el oráculo GIS, no a forzar la geometría.
*   **Fuente independiente:** El archivo GIS original (vectorial) antes de la conversión a malla.
*   **Coste:** O(N log N) por escena. Bajo.
*   **Límites:** Requiere registro preciso entre la malla triangular y los vectores GIS.

**2. Integridad Topológica del Volumen de Colisión del Agua**
*   **Mecanismo del defecto:** La geometría visible (caras de agua) y el volumen de colisión pueden divergir tras la regeneración de máscaras. El suavizado del terreno puede elevar el fondo bajo el agua visible, creando "islas" de colisión flotantes o zonas donde el personaje flota en el aire porque el volumen no toca el terreno sólido. Las pruebas numéricas de altura pasan si la altura media es correcta, pero la colisión falla en bordes.
*   **Variable observada:** Distancia mínima vertical ($d_{min}$) entre la superficie de colisión del agua y la malla del terreno sólido en la proyección XY. Número de componentes conexos de la malla de agua.
*   **Algoritmo implementable:** Muestrear la rejilla de colisión del agua. Para cada celda, encontrar la altura del terreno sólido en la misma coordenada XY. Calcular $d_{min}$. Si $d_{min} < \epsilon_{contacto}$ (ej. 1cm) en más del 90% de los vértices de la frontera de colisión, la condición es PASS. Si existen islas de colisión aisladas (componentes conexos no conectados a la masa principal), es FAIL.
*   **Origen de tolerancia:** **Contrato de Física.** El volumen de colisión debe apoyar-se en el terreno para simular flotabilidad/sumersión correctamente. El $\epsilon_{contacto}$ es mínimo para evitar artefactos de redondeo, pero suficiente para asegurar contacto.
*   **Positivo:** Detecta agua "flotante" o terreno que invade el volumen de agua, imperceptible en pruebas de altura media.
*   **Negativo que lo mata:** Un diseño intencional de cascada donde el agua cae en un vacío controlado (sin colisión en el vacío) fallaría esta prueba. Se debe excluir el área de la caída (máscara de caída) de la comprobación de contacto, pero mantener la comprobación de continuidad del flujo.
*   **Fuente independiente:** La definición lógica de fuentes y escurrimientos del sistema de agua (independiente de la malla final).
*   **Coste:** O(N) para la malla de colisión. Medio.
*   **Límites:** No detecta calidad visual del shader de agua, solo integridad física/topológica.

**3. Detección de Discontinuidades en Aristas de Bosque por Intersección de Bounding Boxes**
*   **Mecanismo del defecto:** Al regenerar máscaras o aplicar suavizado, los árboles (instancias) pueden quedar "flotando" o enterrados si el terreno bajo sus raíces cambia más de lo permitido por la reserva de terreno. Además, la densidad puede agruparse de forma artificial (bloques rectangulares) debido a artefactos de la rejilla triangular, no reflejando la distribución orgánica del humedal o la especie.
*   **Variable observada:** Diferencia de altura entre el centro de la base del árbol y la malla del terreno local (delta_h). Densidad de instancias por unidad de área local (kernela). Intersección de esferas de copa (radio_copa) con el suelo o con otros árboles en la misma vertical.
*   **Algoritmo implementable:** Para cada instancia de árbol, muestrear la altura del terreno en el centro de su bounding box base. Si $|Delta_h| > T_{planteo}$ (ej. 5cm), FAIL. Para la distribución, usar un conteo de K-nearest neighbors (k=10) para cada árbol. Comparar la distancia media a los vecinos con la distribución esperada por especie (Poisson o agrupado según contrato). Si la desviación estándar de las distancias es anómalamente baja (formación en cuadrícula perfecta), es un defecto de "artefacto de rejilla".
*   **Origen de tolerancia:** **Calibración Humana / Contrato de Ecología.** $T_{planteo}$ asegura que el árbol no flote ni quede enterrado tras el suavizado. La distribución se basa en datos de campo o referencias visuales aprobadas, no en un número arbitrario.
*   **Positivo:** Detecta árboles que el suavizado ha "dejado atrás" o que han caído en huecos no previstos. Detecta la "cuadrícula" artificial de instanciación.
*   **Negativo que lo mata:** Un bosque muy denso y uniforme diseñado intencionalmente (ej. plantación agrícola) podría ser marcado como defecto de "falta de naturalidad" si el oráculo es demasiado estricto. Se debe parametrizar la varianza permitida por tipo de bosque.
*   **Fuente independiente:** La lista de semillas de instanciación y las reglas de dispersión ecológica definidas en el diseño, no el resultado final de la malla.
*   **Coste:** O(N log N) por búsqueda espacial. Alto si hay >50k árboles, pero optimizable con grids.
*   **Límites:** No detecta texturas repetitivas ni errores de LOD.

---

### Mejoras Secundarias (4-10)

**4. Validación de Pendiente en Juntas de Carreteras**
*   **Mecanismo:** Las juntas entre secciones de carretera o con el terreno pueden crear "escalones" invisibles en pruebas de altura media pero que detienen el movimiento o causan vibración en el motor.
*   **Variable:** Derivada de la altura a lo largo de la normal de la frontera de la carretera.
*   **Algoritmo:** Muestrear la altura a 0.5m de cada lado de la línea de unión. Calcular la pendiente transversal.
*   **Tolerancia:** **Contrato de Jugabilidad.** Máximo 5% de pendiente transversal para evitar desviación de vehículos.
*   **Positivo:** Detecta escalones de 3cm que son críticos para coches pero invisibles a caminando.
*   **Negativo:** Puentes o elevaciones intencionales deben estar excluidas por máscara.
*   **Fuente:** Línea de centro del camino (GIS).
*   **Coste:** Bajo.
*   **Límites:** Requiere precisión milimétrica en el alineamiento GIS-Malla.

**5. Detección de "Caños" y Desconexiones en Cauces**
*   **Mecanismo:** El suavizado puede cerrar bocas de cauce creando lagos artificiales o cortar la continuidad del flujo en confluencias.
*   **Variable:** Conectividad de la rejilla de agua (componentes conexos).
*   **Algoritmo:** Flood fill en la rejilla de células de agua. Si el número de componentes conexos aumenta respecto a la referencia GIS de flujo, es FAIL.
*   **Tolerancia:** **Contrato de Hidrología.** Cada cuenca debe mantener su singularidad o conectividad definida.
*   **Positivo:** Detecta lagos fantasma o ríos rotos.
*   **Negativo:** Evaporación intencional debe estar marcada como excepción.
*   **Fuente:** Grafo de flujo GIS.
*   **Coste:** O(N).
*   **Límites:** No valida la profundidad, solo la continuidad.

**6. Auditoría de Rugosidad de Alta Frecuencia (Bump Map Proxy)**
*   **Mecanismo:** El suavizado selectivo puede eliminar el ruido natural del terreno, creando superficies "plásticas" o "cerebros" que no envejecen bien visualmente.
*   **Variable:** Varianza de la altura en ventanas de 1m (frecuencia alta).
*   **Algoritmo:** Calcular la desviación estándar de alturas en una ventana 1m. Comparar con un rango mínimo de rugosidad por bioma.
*   **Tolerancia:** **Aceptación Visual.** El rango mínimo se calibra con renders de referencia aprobados por arte.
*   **Positivo:** Evita superficies lisas poco naturales.
*   **Negativo:** Zonas de arena compactada pueden ser legítimamente lisas.
*   **Fuente:** Referencias de campo / renders de arte.
*   **Coste:** O(N).
*   **Límites:** No detecta errores de normal mapping.

**7. Chequeo de Intersección Terreno-Objeto Estático**
*   **Mecanismo:** Rocas o ruinas pueden quedar enterradas o flotando tras el suavizado del terreno que las rodea.
*   **Variable:** Superficie de intersección entre la malla del objeto y el terreno.
*   **Algoritmo:** Cálculo de booleano o muestreo de la base del objeto. Si más del 10% de la base está bajo el terreno, FAIL.
*   **Tolerancia:** **Contrato de Diseño.** Estabilidad visual y física.
*   **Positivo:** Detecta enterramientos parciales.
*   **Negativo:** Fundaciones enterradas intencionalmente.
*   **Fuente:** Bounding boxes de objetos estáticos.
*   **Coste:** Medio (búsqueda espacial).
*   **Límites:** No aplica a árboles instanciados (cubierto por #3).

**8. Análisis de Espectralidad de la Rejilla Triangular**
*   **Mecanismo:** La rejilla triangular puede generar patrones de moiré o artefactos de aliasing visibles a distancia si la frecuencia del terreno se alinea con el paso de 6m.
*   **Variable:** Potencia espectral de la altura en el dominio de Fourier.
*   **Algoritmo:** FFT de la matriz de alturas. Buscar picos de anomalía en la frecuencia correspondiente al paso de 6m.
*   **Tolerancia:** **Diagnóstico.** Un pico excesivo en esa frecuencia indica que el terreno "vibra" con la rejilla, no es natural.
*   **Positivo:** Detecta patrones repetitivos artificiales.
*   **Negativo:** Terrenos con repetición intencional (terrazas).
*   **Fuente:** Análisis matemático (no depende de GIS).
*   **Coste:** Alto (O(N log N) FFT).
*   **Límites:** Requiere normalización cuidadosa para no falsear con bordes.

**9. Verificación de Umbrales de Slope para Movimiento Jugable**
*   **Mecanismo:** Zonas fuera de los caminos con pendiente > 30-40% pueden ser imposibles de atravesar a pie, limitando el "mundo abierto" real.
*   **Variable:** Pendiente local máxima (gradiente).
*   **Algoritmo:** Calcular el gradiente en cada vértice. Mapear zonas donde $|grad| > T_{máx}$.
*   **Tolerancia:** **Contrato de Jugabilidad.** Definida por los parámetros de movimiento del personaje (agilidad, agotamiento).
*   **Positivo:** Mapea áreas "bloqueadas" por pendiente, útil para IA y diseño de rutas.
*   **Negativo:** Acantilados intencionales.
*   **Fuente:** Parámetros de movimiento del motor (no inventados, tomados de la configuración de movimiento).
*   **Coste:** O(N).
*   **Límites:** No garantiza que el camino sea fácil, solo que el resto no sea imposible (o marca lo que es).

**10. Benchmark de Diferencia Estructural (SSIM Adaptado a Malla)**
*   **Mecanismo:** Comparar la estructura de la malla generada contra una versión "vanilla" no es válido si el diseño cambió. Pero comparar dos iteraciones de generación con el mismo seed debe ser estable.
*   **Variable:** Similitud Estructural (SSIM) entre mapas de altura consecutivas.
*   **Algoritmo:** Calcular SSIM entre la altura actual y la de la iteración anterior.
*   **Tolerancia:** **Calibración.** Si el SSIM cae bruscamente sin cambio de diseño, hay inestabilidad en el algoritmo de suavizado.
*   **Positivo:** Detecta inestabilidad del pipeline.
*   **Negativo:** Cambios intencionales de diseño.
*   **Fuente:** Historial de versiones del terreno.
*   **Coste:** O(N).
*   **Límites:** No valida calidad, solo estabilidad.

### Riesgos y Consideraciones Finales

El mayor riesgo es el **sobre-suavizado**, que elimina la personalidad del terreno. La propuesta #1 (Curvatura) mitiga esto al permitir especificar qué formas deben conservarse (pirámides, cauces rectos) y cuáles pueden redondearse (ruido micro).

La **regeneración de máscaras** es crítica. Si las máscaras de protección (agua, caminos) se regeneran de forma no determinista o con ruido, las pruebas de contacto (#2) y plantado (#3) fallarán aleatoriamente. Se debe garantizar que la generación de máscaras sea idempotente o versionada.

No se debe usar el número de 20 grados como umbral de FAIL. Es un indicador de *densidad de ángulos*. Un terreno con muchas aristas a 20 grados puede ser válido (rugosidad natural), mientras que uno con pocas puede ser liso. La clave es la **correlación con la forma esperada** (GIS), no la cantidad de ángulos.

Las pruebas en motor deben ejecutarse solo tras el paso de estas pruebas estáticas, para evitar gastar ciclos de renderizado en escenas topológicamente incorrectas. La separación entre **FAIL mecánico** (agua flotante, árbol enterrado > 5cm) y **Aceptación Visual** (rugosidad baja, pirámide muy redondeada) es esencial. El FAIL mecánico bloquea el merge; la Aceptación Visual requiere revisión de arte.

END_COUNCIL