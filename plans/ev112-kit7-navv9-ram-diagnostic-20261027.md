# Kit7: discriminar el coste antes de otra generación

Estado: plan de diagnóstico, ejecutor/integrador Codex por encargo vivo de Guillermo.
Revisión independiente Fable 5.1 recibida; se adopta la medición y se corrigen
sus inferencias excesivas abajo. No cambia producto ni criterios de aceptación.

## Hechos comprobados y límites

[EXACT] Nav8 pasa las 607 consultas y falla RAM (1,265913 residente y 1,241333
privada, límite 1,10). Nav12 corrige las cuatro alturas originales, pero falla
otras tres: 0,856856 / 0,923148 / 0,818588 m, límite 0,801 m. Las 562
continuidades y ocho testigos pasan. Sus runs se cerraron y liberaron. No se
ejecutó RAM12. El cambio de tesela no proporciona todavía aceptación conjunta.

[EXACT] La reconstrucción de los polígonos reales reproduce los seis waypoints
fallidos de Nav12 con residuo máximo 5,65e-7 m. El censo de todos los tiles de
Nav8 y Nav12 encuentra cero en los tres contadores empíricos de detalle. No
demuestra el algoritmo del generador ni un fallo universal. El estimador de
dos diagonales falla como predictor de aceptación y no justifica otro ancho.

[EXACT] En (9132,11280), la cara visual de grava y Roadway coinciden en
1,91014218 m; Geometry da 1,90833567 m. La cara visual de agua está a
2,15066679 m y su Roadway water_ext a 1,90066679 m. La diferencia entre el
máximo visual y físico es agua frente a lecho, no un defecto de la grava.
No se cambia geometría para hacer pasar alturas de navegación.

Fuentes en E:/DayZ-Baltic-Build/shape-repair-20261025: kit7-nav12-consumer-20261027,
kit7-nav12-height-reconstruction-20261027, kit7-nav-detail-census-20261027,
kit7-grid-vertex-diagnostic-20261027 y kit7-corner-faces-20261027.

## Decisión y revisión

[DESIGN] Ejecutar un bloque diagnóstico de seis mediciones NUEVAS ABBAAB del
paquete original kit7 NavV9 de 12,5 m frente a Chernarus. Es el control de menor
densidad ya disponible; evita gastar otra generación sin medir su coste.
Sus cuatro fallos de altura se conservan y lo hacen inelegible para aceptación.

La condición del plan anterior era «si 12 m falla RAM»; no se cumplió, porque
falló geometría. Este documento replantea explícitamente el diagnóstico tras
ese fallo, dentro del encargo autónomo. No se presenta como una autorización
condicional ya satisfecha. La recomendación de Fable se acepta con límites:
un FAIL de RAM12,5 no demostraría que la densidad no influye ni que todo el
coste procede del kit; un PASS tampoco predice el coste de otra variante.
No se adopta su cota de cuantización de 0,05 m sin conocer el redondeo, ni se
confunde ausencia de detalle con fallo global. Nav8 conserva su PASS funcional.

## Ejecución verificable

[EXACT] Restaurar por copia los tres PBO propios archivados, verificando hashes
y rechazando un destino existente diferente; conservar el archivo. Mundo
a2919a80ae6da6fc90e75b0ac55d1e9dd4ba4a39f6700b9fec237c7e7683b16c,
piloto 3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6,
agua 97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43.
El NM12,5 permanece intacto. No hay generación, cambio de consultas ni de LOD.

[DESIGN] Copias independientes de los corredores RAM revisados de Nav12,
con prefijo navv9diag. No alterar el gate funcional de Nav12. Un gate separado
exige el FAIL histórico exacto por hash, sus cuatro nombres, identidad de los
paquetes, misiones nuevas, revisión y fuentes selladas. Tanto preparación
como consumo quedan marcados DIAGNOSTIC_ONLY. El agregado mantiene resultados
RAM y eligibility=false; nunca concede aceptación funcional.

Mismos consumidores y misión normalizada, 30 s de calentamiento + 120 s de
medición, ABBAAB, residente y privada <=1,10, dispersión <=5%. CPU descriptiva.
FIFO nativo on_busy=queue, wait_for_box_s=600, takeover=false, sin prelease ni
comprobación de ocupación; adoptar solo run propio después del lanzamiento.
Identidad de PID/creación/ejecutable/misión, observador, cierre oficial y lease
liberado. Hash pesado después de medir. Sin cliente ni procesos ajenos tocados.

Validación previa: seis misiones válidas y equivalentes, controles de lifecycle
y comando heredados en las copias, positivos/negativos del gate diagnóstico
(PASS falso, nombres incompletos, hash cambiado, paquetes diferentes). Revisión
Fable de la diferencia con el corredor sellado antes de lanzar.

## Parada

Presupuesto: un bloque de seis pasadas, sin seleccionar ni repetir una pasada
favorable; hasta dos rondas de corrección de implementación. Si invalida una
pasada, parar y diagnosticar; no repetir automáticamente. Si RAM12,5 falla,
cerrar esta exploración de densidades y estudiar el coste sin atribuir causa
no aislada. Si pasa, conservar solo ese hecho y replantear una única variante
funcional motivada; este plan no autoriza por sí solo otra generación.
Commit/push de controles y evidencia verdaderos, con FAIL conservados.
No afirma actores, barcos, FPS, capacidad de jugadores ni aceptación global.
