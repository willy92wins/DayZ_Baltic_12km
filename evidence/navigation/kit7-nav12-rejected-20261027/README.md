# Nav12 rechazado: tres fallos nuevos de altura

La generación y la sonda nativa terminaron con identidad y cierre verificados.
Las607 consultas conservan coordenadas y tolerancias. Nav12 corrige las cuatro
alturas originales, pero introduce estos errores contra el límite0,801 m:

- piece116left:0,856856 m.
- piece116right:0,923148 m.
- seam116right:0,818588 m.

Las562 continuidades y ocho testigos F pasan. Resultado global de la sonda:
FAIL_KIT7_NATIVE_GRAPH. RAM12 no ejecutada por este fallo. No usar como solución.

Los polígonos del NM reproducen las seis alturas nativas con error inferior a
5,65e-7 m. Visual,Geometry y Roadway coinciden en los waypoints fallidos; la
aproximación del NM explica sus alturas. No se ha aislado la decisión interna
del generador. El estimador de dos diagonales no predice aceptación.

En el vértice diagnóstico(9132,11280), el máximo visual es agua. Su grava visual
y Roadway coinciden a1,91014218 m y Geometry a1,90833567 m. No se identificó
un defecto de grava que permita una corrección física justificada.

Nav8 sigue siendo la corrección funcional publicada:607 PASS,máximo0,711963 m,
con cuatro fallos originales cerrados. Sus seis pasadas RAM siguen FAIL.
Siguiente discriminador: bloque diagnóstico del original12,5, preservando sus
cuatro fallos. No se hereda aceptación ni se regeneran anchos a ciegas.
Actores,barcos,cliente,FPS y aceptación global permanecen pendientes.

La revisión Fable se conserva íntegra como opinión, con límites corregidos en
review/reconciled-plan.md. No se adoptan sus inferencias de causalidad exclusiva,
redondeo<=0,05 m, fallo global, condición previa cumplida ni repetición automática.
Los diagnósticos de censo y esquina son posteriores a esa revisión.
