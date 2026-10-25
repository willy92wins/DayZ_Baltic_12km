# EV57 - reparacion numerica acotada de EV56

EV56 no se promociona. Su consumidor independiente pasa toda la geometria pero el solucionador agota 100 iteraciones. No aumentar iteraciones ni cambiar objetivos/semilla/dominio. Diagnostico sin nueva optimizacion: las dos restricciones de area son independientes (singulares 237.59 y5.52), no hay conflicto de pendientes, area, suelo ni RMS en el iterado. El gradiente forward por defecto diverge del central estable hasta0.001266 por coordenadas globales. Solo trasladar el origen reduce ese error a0.000125; central local entre pasos1e-5 y1e-6 difiere2.28e-6. Esto identifica ruido en la derivada, no prueba por si solo la causa completa del limite de iteraciones.

Reparar la implementacion: posiciones relativas al sector y jacobianos centrales explicitos (paso1e-5, anclado por el control de estabilidad), gradiente exacto de la desviacion cuadratica. La evaluacion de areas/energia y los gates no cambian; no se modifica semilla, pesos, limite100/120s ni margenes. Una ejecucion. Si no converge o falla consumidor: conservar FAIL, sin barrido. El consumidor sigue reconstruyendo poligonos GEOS y giros por diferencias de orientacion independientes.

Fuente sigue EV55 conP/F EV54. No hay cambios de nivel. Validar despues float32, compilado y nativo antes de incorporarlo al candidato de trabajo.
