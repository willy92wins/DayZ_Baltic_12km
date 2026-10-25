Council de cobertura para terreno triangular de paso 6m con diagonal NO-SE fija.

El censo actual de ángulos entre normales por familias de aristas es diagnóstico. 20° es bin, no umbral estético. Los falsos PASS aparecen porque una métrica local pasa mientras el defecto es multiescala, topológico o de coherencia entre subsistemas.

### Prioridad alta

**1. Piramides/ridges multiescala. Diagnóstico + Aceptación visual**
Mecanismo del defecto: suavizado selectivo deja crestas planas a escala de varias celdas. Desde altura media se lee pirámide aunque el ángulo celda a celda esté dentro del bin.
Variable observada: curvatura integrada y variación de pendiente en ventanas 1x, 3x, 9x el paso.
Algoritmo implementable: sobre la malla triangular calcular pendiente media y desviación de normales en ventanas móviles de 6m, 18m, 54m. Detectar picos de curvatura media positiva sostenida y alineación de aristas de la misma familia.
Origen de tolerancia: calibración humana sobre escenas vanilla equivalentes, no valor universal.
Positivo: captura ridges visibles aunque el censo de 20° pase.
Negativo que lo mata: máscara protegida legítima que debe conservar cresta.
Fuente independiente: mapa de pendientes derivado de DEM GIS, no del productor de suavizado.
Coste: O(N) con ventanas deslizantes, bajo.
Límites: no confunde angularidad del eje con escalonado inevitable de la rejilla. Riesgo de sobre-suavizado si se usa como FAIL mecánico.

**2. Cauces angulares y discontinuos. FAIL mecánico + Diagnóstico**
Mecanismo del defecto: cauce sigue la diagonal NO-SE y presenta quiebros a escuadra y saltos de continuidad hidráulica.
Variable observada: dirección tangencial del cauce suavizada y salto de altura entre vértices consecutivos del centroide del cauce.
Algoritmo implementable: extraer polilínea del cauce por máscara de agua. Calcular dirección por ventana móvil de 3-5 muestras y cambio de dirección normalizado. Marcar discontinuidades donde la pendiente transversal excede la longitudinal de forma abrupta y donde hay ruptura de conectividad topológica.
Origen de tolerancia: contrato de hidrología y referencia vanilla de trazado natural.
Positivo: detecta escuadras visibles y cortes en extremos.
Negativo que lo mata: confluencias reales y orillas protegidas por máscara.
Fuente independiente: endpoints GIS de cauces y red de drenaje.
Coste: medio, depende de longitud de cauce.
Límites: no exige curva recta en terreno natural. No penaliza escalonado de rejilla si la dirección suavizada es coherente.

**3. Coherencia agua geometría visible / colisión / caras de agua. FAIL mecánico**
Mecanismo del defecto: geometría triangular visible, volumen de colisión y caras de agua no coinciden. El jugador ve agua en un sitio y colisiona en otro.
Variable observada: distancia signo entre malla visible y malla de colisión en zona de agua, y presencia de caras de agua fuera de la máscara.
Algoritmo implementable: muestrear puntos regulares sobre la máscara de agua, proyectar a malla visible y a volumen de colisión. Calcular gap y penetración. Verificar que caras de agua cubren exactamente la máscara.
Origen de tolerancia: contrato de gameplay de colisión y referencia vanilla de sincronía agua-terreno.
Positivo: evita falsos PASS numéricos de terreno cuando el agua está desacoplada.
Negativo que lo mata: zonas de transición intencional con rampa de entrada.
Fuente independiente: endpoints GIS de agua y capa de colisión exportada.
Coste: medio-alto por proyecciones.
Límites: no prueba estética del agua, solo coherencia mecánica.

### Otras mejoras no redundantes

**4. Orillas y confluencias agua-terreno. Aceptación visual + Prueba en motor**
Mecanismo: escalón visible en orilla por falta de transición entre terreno y cara de agua.
Variable: pendiente transversal en banda de 2-4m alrededor de máscara de agua.
Algoritmo: perfil transversal perpendicular a orilla, comparar pendiente media con pendiente aguas arriba.
Origen tolerancia: calibración humana sobre vanilla.
Positivo: detecta bordes duros visibles desde altura media.
Negativo: humedales protegidos con pendiente abrupta real.
Fuente independiente: máscara de agua GIS.
Coste bajo.

**5. Soporte y distribución de árboles. FAIL mecánico + Aceptación visual**
Mecanismo: instancias con matriz, centro de bounding box y radios de tronco/copa/base quedan flotando o hundidas, o clustering artificial.
Variable: distancia vertical entre centro de bounding box proyectado y altura del terreno en ese punto, y densidad local de instancias por especie.
Algoritmo: para cada instancia proyectar centro a terreno, comparar con altura esperada según radio de tronco/base. Calcular índice de vecindad local y comparar con distribución de referencia vanilla.
Origen tolerancia: contrato de colocación y calibración humana de naturalidad.
Positivo: evita falsos PASS de conteo global.
Negativo: humedales con especies que toleran flotación visual.
Fuente independiente: capa de especies y humedales GIS.
Coste medio.

**6. Camino reserva vs futuro físico: juntas y puentes implícitos. Diagnóstico**
Mecanismo: la reserva muestreada cada metro con 17 laterales entre -4 y +4m pasa límites de 3cm transversal, 6.5% pendiente y 3cm cuerda de 6m, pero existen discontinuidades en juntas y puentes no probados.
Variable: continuidad de pendiente y altura en cruces de segmentos de reserva y proximidad a agua/presa/extremos excluidos.
Algoritmo: detectar cambios bruscos de pendiente y altura en puntos de unión de tramos de reserva. Marcar proximidad a exclusiones como riesgo, no como PASS.
Origen tolerancia: límites aprobados de camino y contrato de infraestructura.
Positivo: evita que exclusiones de vecindad de agua, presa y extremos se interpreten como aceptados.
Negativo: tramos intencionalmente en pendiente.
Fuente independiente: trazado GIS de camino planificado.
Coste bajo-medio.
Límite: los excluidos NO son prueba de carretera física.

**7. Transición máscara protegida / suavizado y deriva de cobertura. Diagnóstico**
Mecanismo: al regenerar máscaras protegidas cambia la cobertura de suavizado y aparecen artefactos en el borde.
Variable: diferencia de altura y de normal entre versión anterior y nueva en banda de borde de máscara.
Algoritmo: comparar dos versiones de malla con misma semilla de rejilla, calcular mapa de diferencia en zona de borde de máscara.
Origen tolerancia: estabilidad contractual de áreas protegidas.
Positivo: detecta regresiones por cambio de máscara.
Negativo: actualización legítima de máscara aprobada.
Fuente independiente: historial de máscaras GIS.
Coste bajo.
Riesgo: sobre-suavizado si se fuerza continuidad en zona protegida.

**8. Rendimiento jugable por frustum, no conteo global. Prueba en motor**
Mecanismo: conteo global de objetos no prueba FPS. El defecto es densidad de instancias y costo de colisión en vista.
Variable: número de instancias visibles y triángulos de colisión por frustum típico de altura media.
Algoritmo: muestrear cámaras representativas, contar instancias y triángulos de colisión intersectados, sin optimizar motor.
Origen tolerancia: benchmark futuro con mapa vanilla equivalente.
Positivo: correlaciona con experiencia real.
Negativo: escena con pocos objetos pero costosos.
Fuente independiente: métricas de escena vanilla.
Coste medio.

**9. Filtro de frecuencia para distinguir artefacto de rejilla de defecto geométrico. Diagnóstico**
Mecanismo: confundir escalonado inevitable de la rejilla triangular con angularidad real.
Variable: contenido de frecuencia espacial de la normal.
Algoritmo: descomponer variación de normal en componentes de alta frecuencia ligada al paso 6m y baja frecuencia ligada a forma. Evaluar solo baja frecuencia para estética.
Origen tolerancia: calibración humana sobre vanilla.
Positivo: reduce falsos positivos por naturaleza de la malla.
Negativo: defecto real a escala de paso pasa desapercibido.
Fuente independiente: análisis espectral de DEM GIS.
Coste medio.

**10. Muestreo visual en motor de siluetas y perfiles. Aceptación visual**
Mecanismo: defectos visibles desde altura media no se capturan con métricas numéricas locales.
Variable: perfiles de silueta y gradiente de pendiente en vistas fijas.
Algoritmo: generar capturas de perfil desde puntos de vista de altura media y comparar gradiente visual con referencia vanilla mediante métrica de diferencia de pendiente acumulada.
Origen tolerancia: panel humano calibrado sobre vanilla.
Positivo: cierra brecha entre métrica y percepción.
Negativo: costoso y subjetivo.
Fuente independiente: escenas vanilla equivalentes.
Coste alto.

Riesgos transversales: sobre-suavizado elimina rasgos jugables y cambia cobertura al regenerar máscaras. No se debe exigir cero defectos sin oracle independiente. Las pruebas deben separar diagnóstico, FAIL mecánico, aceptación visual y pruebas en motor.

END_COUNCIL