# EV66 — restricciones de pliegue en la transición

EV65 converge y pasa fondo, profundidad, huella, conectividad, pendientes, política local y aumento máximo <2 grados. Falla en 309 aristas cuyo pliegue ya grande aumenta hasta 0,5623 grados. La energía cuadrática del desplazamiento no impone el límite de cada normal; no corresponde cambiar niveles ni ampliar radios.

Una corrección de formulación: proyectar EV65 sobre sus límites explícitos de ángulo y pendiente. Dominio de reparación determinista: vértices de las 309 aristas y dos celdas de contorno, intersectados con los 3886 libres de EV65. 1019 variables en seis grupos, cerrados con dos celdas para que ninguna bisagra comparta variables entre grupos. Una resolución SLSQP por grupo, <=100 iteraciones cada una y <=300 s en conjunto. Gradiente analítico de coseno entre normales de planos triangulares, cotejado con producto vectorial EV25 y derivadas centrales. Si falla, conservar fallo; no cambiar gates, cotas ni protecciones.

Minimizar distancia cuadrática a EV65 con las mismas cotas 0..0,425 m y suelo seco mínimo derivado. Normal de cada arista <=min(original+2,max(original,10)); pendiente <=max(original,35). Validación de conjunto mediante consumidor independiente EV65. Política de charcas647/651 pendiente, no promoción automática; EV61 sigue vigente.
