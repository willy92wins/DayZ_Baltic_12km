# V18: ampliar la transición lateral, no la cota

El certificado estructural deV16/V17 cancela los96.096 vértices editables y
deja ocho vértices fijos incompatibles con carretera lisa + taludes<=35°.
Las189 filas se reconstruyeron y compararon exactamente con la matriz congelada.
Los ocho puntos están a19.8..28.3m del eje y475..651m del agua; ninguno pertenece
al fairway. Pueden resolver ese certificado con un cambio mínimo local de0.599m.
No demuestra suficiencia para todos los demás puntos de la red.

Fuentes: `tests/regional_road_network_v16/conflict-row-trace/{trace,fixed-boundary}.json`
y `cap-certificate-scan/{report,structural-conflict-region}.json`.
El escaneo se detuvo automáticamente: aumentar el límite vertical no elimina
esta contradicción. No se generó ASC ni se cambió terreno.

[DESIGN] Misma red/dominio/triángulos/pisos, mismos criterios y límite vertical3m.
Ampliar la transición desde los triángulos de carretera de12 a24m. La envolvente
independiente máxima pasa de24.5 a36.5m desde el eje; se comprueba, no se deriva
del soporte declarado. Esto incluye los ocho puntos certificados. Mantener
agua+30m, fairways y Narva480m exactos, pisos de islas y todas las verificaciones
de hidrografía/reserva. Ninguna relajación de pendientes, anchura o cuerda.

Presupuesto: una construcción y un solve L1<=600s/un hilo, guardiaRAM y650s
de proceso. Primal factible no óptimo solo como candidato para consumidores
independientes. Si falla, conservarlo y localizar otro conflicto antes de otra
variante. No encadenar ampliaciones sin evidencia. No importación/NM antes de
geometría de toda la red, hidrografía y negativos pertinentes.
