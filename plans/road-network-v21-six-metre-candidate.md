# V21: margen local6m, sin cambiar restricciones de carretera

V20 cota5m terminó sin ASC: certificado94filas exige>=5,004889m en
un vértice dominante(4512,6924). El minimax independiente agotó600s y dejó
una cota inferior5,131519m de un subproblema óptimo; no obtuvo mínimo global.
Son datos distintos compatibles, no una solución completa.

[DESIGN] Fijar6m como tope del siguiente candidato L1, sembrado con las393.722
filas del certificadoV20. Mantener matrizV18 completa, transición24m,
envolvente36,5m, pisos de islas, agua/fairways/Narva inmutables y todas las
tolerancias de suavidad originales. No agrandar encuadre ni elevar regiones.
Guardar cada conjunto activo para permitir reanudar diagnóstico sin repetir
cálculos.600s/650s,un hilo y guardiaRAM. Sin incremento automático del límite.

Antes de aceptar: todas las filas originales, mapa de cambios/cuantiles,
consumidor denso independiente con6m explícitos, hidrografía/reserva y negativos.
No importar si falla. Si vuelve a ser inviable, revisar el conflicto localizado
y la franja de transición antes de ampliar más la altura.
