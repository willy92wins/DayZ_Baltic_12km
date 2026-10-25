# EV51 — conservar el soporte terminal nativo

EV47 modifica un unico vertice mojado a seco: fila600,col2037 (x12222,z8682), altura3.16858387m a4.11435318m, agua3.425m. La ultima orilla se contrae antes de ese nodo y su punta pasa a72.391grados. La inspeccion de los segmentos reales identifica el mecanismo, no una arista diminuta.

Un candidato: conservar la altura original de ese ultimo vertice mojado, manteniendo las demas reglas de EV47. Resolver nuevamente la igualdad de area nativa por la misma biseccion monotona; no ajustar radios, pendientes ni umbrales por el resultado. Esto mantiene el apoyo terminal que estaba presente en el cauce fuente. El perfil de talud EV47 rechazado es solo el modelo de autoria, no una base aceptada.

Gates sin relajar: fuenteEV25 inmutable, ingenieria exacta, delta<=1.5m, fondo>=1m, nucleo de profundidad, pendientes<=max(fuente,35grados), area exacta0.001m2, desplazamiento<=4.1m, esquina maxima<=49.345grados, energia angular1m al menos10%mejor, RMS de pliegues no mayor. Un candidato; consumidor independiente despues de autoria. No empaquetar si falla.
