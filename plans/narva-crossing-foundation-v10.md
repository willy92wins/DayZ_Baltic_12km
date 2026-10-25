# Cruce de Narva sobre la hidrografía regional

01-10-2026, sesión nocturna. Corrección dentro de P9/P10/P11; no cambia el
encuadre, el eje del puente, la escala de los assets ni la hidrografía aceptada.
V9 permanece inmutable como referencia. Estado vivo: HANDOFF.md. La propuesta inicial de siete tramos fue sustituida por nueve tras demostrar inviabilidad (ver discriminador).

## Problema verificado y modificación

El consumidor V4 pasó 81.212 muestras sobre el paquete diagnóstico V9. El agua
de Narva está alrededor de 2.075–2.2m, mientras el antiguo cálculo de gálibo
usaba 1m. El Geometry del puente metálico25 invade 1.661799m bajo el tablero:
tablero9m deja aproximadamente 5.14m bajo vigas con agua2.2, menos del objetivo6m.
Además, la apertura regional del cauce dejó ambos extremos de los tres tramos
actuales sobre agua: a estación -37.5m el lecho está entre -2.25 y -1.45m;
a +37.5m, entre -4.27 y -3.13m. No rellenar esos canales para salvar el cruce.

[DESIGN] Siete tramos vanilla25m, longitud175m, tablero11m. Conservar centro,
orientación y escala1 de los tres actuales; añadir dos por extremo. Extremos
±87.5m ya fuera del soporte de agua/canal/islas en las muestras de calzada8m.
La envolvente de ingeniería del agua para el gálibo es 3m: reserva por encima
del agua local medida, no una medición del máximo dinámico. Predicción de paso
central18m: 11 - 1.661799 - 3 = 6.338201m. Contrastar en motor y conservar ese
carácter de reserva hasta medir ondas/nivel en el recorrido.

[DESIGN] Preparar accesos secos de 8m útiles y empalmes a11m; conectar el este
progresivamente con su eje de carretera existente. Ajustar el terreno en una
capa local, preservando cada vértice de agua, fairway e islas y todas las
superficies de agua. Los taludes deben respetar el límite regional35.01grados.
No usar el generador histórico de Narva: lee una base anterior y aguas0.5–1m.

## Puertas antes de sustituir el candidato

1. Fuente V9 por SHA, delta local acotado, identidad exacta fuera de la zona,
   agua/canal/islas exactos; 79.420 muestras de canal mantienen profundidad3m.
2. Accesos: muestreo independiente de triángulos nativos cada0.25m, calzada8m,
   pendiente<=6.5%, desnivel transversal<=3cm y desviación de cuerda6m<=3cm.
   Empalme de tablero<=1cm. Registrar también cambio de pendiente y curvatura.
   Estos umbrales preparan el terreno; no prueban conducción cómoda.
3. Repetir consumidor geométrico regional sin mover sus muestras ni bajar sus
   umbrales. Las zonas fuera del cruce deben permanecer exactas frente a V9.
4. Modelo instalado por hash, comprobar gálibo18m/6m y unión de los siete
   tramos. Altura prevista no equivale a colisión medida ni barco con tripulante.
5. Proyecto nativo guardado/reabierto y exportaciones completas independientes;
   alturas, siete poses canónicas, 10.152 aguas y materiales. Gate específico
   de esta versión, sin hacer pasar el gate V9 cambiando sus constantes.
6. Paquete nuevo, navegación nueva desde ese WRP exacto; consumidor regional,
   cruce terrestre y lancha ida/vuelta sin SetPosition durante el recorrido.

Si el ajuste local es incompatible con algún canal/isla, conservar el FAIL y
resolver con longitud/perfil del cruce, sin estrechar ni desecar el río.
Presupuesto inicial: un candidato medido; antes de cada corrección identificar
el discriminador y el conjunto de restricciones que falló. No hay límite
arbitrario de rondas ni aceptación por el tiempo gastado.

Fuentes leídas: tools/navigation/audit_assets.py:28–68,
waterway_common.py:35–49, fit_road_native_triangles.py:20–28,
verify_combined_foundation.py:17–68; evidencia vanilla-assets.json y consumidor
V4 en evidence/overnight-2026-10-01/diagnostic-consumer-v4/.

## Discriminador del primer ajuste

El candidato7 no llegó a generar ASC: el sistema es inviable incluso quitando
todas las restricciones de carretera y conservando solamente pendientes
nativas, vértices protegidos y apoyos a11m. Evidencia
tests/narva_foundation_7span_discriminator_v1/solve.json. Por tanto cambiar el
perfil de conducción no resuelve ese conflicto. [DESIGN] Ensayar nueve tramos
(225m, extremos±112.5m) para separar el terraplén del canal. Se mantienen cota,
eje, ancho, máscaras y puertas; los tres tramos originales conservan XY. La
longitud sigue siendo de un cruce de ingeniería, no mapeado definitivo.
