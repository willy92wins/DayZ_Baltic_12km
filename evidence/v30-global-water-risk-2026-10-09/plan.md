# Barrido global de agua sobre tierra — 09-10

Petición viva: detectar y corregir los fallos del mapa sin revisar manualmente todo a capturas. La nueva imagen junto al puente confirma que LAND180/C1R3P no cierran BALTIC-016. Se conserva el suavizado probado; no se aumenta otra vez una cota a ciegas.

Primero, inventario numérico completo sobre el terreno exacto del paquete: separación del mar físico medido, bajos respecto al umbral empírico de 1,80 m y dependencia de las protecciones (carretera, plataforma, playa y cara contigua al agua). La cota 1,80 m es un cribado fundado en LAND160/LAND180, no una altura nativa demostrada del render ni una garantía de ausencia visual.

Segundo, evaluar a varias escalas una posible pérdida de altura por simplificación del terreno. Ese modelo es hipotético hasta aislarlo con un control de detalle del cliente. No llamarlo LOD nativo ni cerrar el problema por un resultado simulado. El consumidor físico actual sigue independiente.

Calibración: el detector debe encontrar los casos confirmados de las imágenes originales y el residual nuevo, localizados por cámara/rasgos geométricos con incertidumbre explícita. Controles negativos: terreno alto y zonas de tierra verificadas estables. Rechazar un detector que solo reproduce su propia transformación o que declara PASS porque su muestra no alcanza el defecto.

Salidas: censo y coordenadas por componente/tesela, máscara de riesgo para toda la cuadrícula, clases de causa/protección y casos físicos de motor. Los puntos de orilla o mar intencional no se eliminan por pertenecer a una banda: se identifican como tales y conservan su estado de excepción pendiente si no están explicados.

Presupuesto inicial: un barrido global y un control discriminante de detalle si la evidencia lo justifica; corregir fallos de implementación del detector. Sin buscar cotas hasta obtener una captura favorable. Cualquier cambio posterior debe conservar fondo >=1 m, corredor >=0,95 m y apoyos funcionales, y pasar los consumidores afectados.

Las juntas globales también se inventarían: 6.431 de 16.442 instancias pendientes cambiarían más de 1 mm con el campo visual promediado; 333 superan 0,35 m y el máximo llega a 1,95 m. Por ello no extender ciegamente el piloto de 538 piezas a todo el mapa. Conectividad entre cuerpos distintos y límite visual/físico son puertas obligatorias.

## Corrección de la transición, D2

La proyección nativa del cliente localiza el residual confirmado en x=2718,48525; z=6812,81287. SurfaceY devuelve 1,520454 m, frente a 1,520457 m en la fuente. D1 es FAIL: congelar las caras completas contiguas al agua deja una esquina seca a 1,437 m y el punto interpolado solo llega a 1,77068 m. No empaquetar D1.

Se mantiene el objetivo empírico de 1,80 m y el techo de subida de 0,40 m. D2 permite elevar las esquinas secas de orilla que ya pertenecen al suelo interior de >=1,40 m. Se conservan exactamente los vértices mojados, playas, reserva vial, plataformas, soportes de todas las caras de corredores, los consumidores físicos históricos y el borde exterior. Las zonas por debajo de 1,40 m se inventarían como transición baja pendiente; no se borran del informe.

Puertas antes de construir: punto confirmado >=1,80 m; cero bajos libres dentro de este alcance; cero cambios de metadatos o soportes protegidos; todos los cuerpos de agua de >=1 m² del modelo físico congelado conservan una única componente significativa y >=90 % de su área; ninguna cara de tierra empeora por encima de 35 grados; consumidor de carreteras PASS. Controles negativos cerrados: punto residual restaurado, fondo elevado, plataforma movida, NaN y canal analítico seccionado. El modelo de agua horizontal no equivale al LOD visible ni certifica el shader.

Presupuesto: una corrección D2 basada en esta causa de implementación y una reparación si aparece un defecto reproducible del código. No variar el umbral ni seguir reduciendo la protección hasta obtener PASS. La comprobación de juego será puntual, sobre la localización calibrada; la cobertura territorial procederá del inventario numérico. Actualmente otra prueba LFSkateboard ocupa DayZ; continuar offline sin gestionarla.

## Resultado D2 y censo del consumidor

D2 queda retirado: el punto confirmado alcanza 1,80 m, pero 68 de las 840 componentes significativas del modelo de agua fallan la conservación; dos pierden la componente única significativa. Además quedan 169 vértices revertidos por la guarda de pendiente. El propio punto reportado toca soportes de una charca que falla. No separar un arreglo local con esa misma regresión ni empaquetar D1/D2. Presupuesto geométrico cerrado; no se crea D3.

La petición de detección sin capturas se materializa en `tools/terrain/audit_water_risk_v30.py`: evalúa todos los vértices y ambos triángulos de cada celda, identifica cada componente por coordenadas y contrasta las observaciones calibradas. Conserva en el censo las transiciones protegidas. El primer cálculo de áreas sin tolerancia contó float32(1,8) como bajo; corregido con la misma tolerancia 1e-5 de los vértices y un negativo específico. `native-census-c1r3p` es preliminar supersedido por `native-census-c1r3p-v2`.

Consumidor nativo: misión de servidor `BalticNativeCensusV1.BalticTrial`, todos los 4.194.304 vértices comparados con SurfaceY y 31.361 consultas físicas (30.668 bajos, controles altos distribuidos y siete localizaciones calibradas). Contrato: 2.048 filas únicas de 2.048 puntos, 0 diferencias >1 mm, END completo, controles negativos de referencia alterada y filas/puntos ausentes. Un error de compilación no es una prueba válida. No modifica terreno, agua ni cámara. Sigue siendo verificación física, no una certificación de la lámina visual.

V2 amplió las consultas físicas a todos los vértices, incluidos los altos: 3.195.297 secos y 999.007 húmedos. Run 66781c9a completo en 22,946 s, cerrado orderly. 73 puntos secos presentan agua nominal/dinámica; 38 etiquetas húmedas devuelven presencia falsa. Algunas de estas últimas sí devuelven profundidad positiva, por lo que son discrepancias de API/clasificación hasta comprobar el orden de consulta y la geometría; no declarar 38 gaps.

Control discriminante de render, ya previsto en el presupuesto inicial: usar `GameOptions` / `ListOptionsAccess` del cliente para cambiar solamente detalle de terreno, secuencia original–alternativo–original, con cámara exacta y registro de índices/textos nativos. API leída en P:/scripts/3_game/gameplay.c:1320-1512 y uso de la opción en 5_mission/gui/newui/options/optionsmenuvideo.c:496. `Test` aplica temporalmente; no llamar `Apply` ni guardar perfil. Restaurar el índice original al terminar. Este control no cambia geometría ni el mar y no se promociona como arreglo. Una secuencia, sin probar combinaciones de ajustes. Si no discrimina, el modelo de reducción de malla sigue siendo una hipótesis y se trabaja otra dimensión.
