# Graduación de tierra firme sin cambiar hidrografía

Deriva de P2/P9/P11/P12/P13 y del falloV15, que permanece registrado. Guillermo
autorizó adaptar Z por jugabilidad preservando XY, agua, islas y reserva; no
fijó como requisito que cada vértice de tierra firme de una isla fuera inmutable.
El planV15 había congelado regiones de soporte conservadoras completas.

Descubrimiento: entre las secciones defectuosas del dominio original,87tocan
protecciones:45el buffer42m,46islas y4bancos (categorías solapadas). Ninguna
toca fairway. Diagnóstico en road-protection-domain.json. Los conflictosLP
son199anchura/rasante y25cuerda; no se elimina ninguna de esas restricciones.

[DESIGN] V16 mantiene todas las tolerancias y el dominio original de evaluación.
Cambiar solo la protección técnica del ajuste, para graduar tierra firme:
- congelar todo vértice a<=30m del agua/oceáno, el fairway y el radioNarva480m;
- conservar la cota mínima conservadora de cada isla, comprobada además por
  el consumidor independiente de polígonos de tierra;
- suelo seco>=1.4m (o cota anterior si menor), sin cambios de fuentes ni niveles
  de agua; permitir rasante local fuera del buffer30m en bancos/islas;
- soporte local de carretera y transición12m, cambio máximo±2.05m, todos los
  triángulos afectables<=35° y ninguna edición fuera del soporte declarado.

El buffer30m deja más de21m intactos incluso descontando la diagonal de una
celda6m. Es protección geométrica adicional, no una nueva tolerancia de costa.
Además, comprobar directamente identidad de los triángulos del agua/costa,
profundidad de fairways, clasificación de tierra e islas y reserva; si falla
cualquiera, rechazar aunque la carretera pase. Se cambia una máscara técnica
excesiva, no los requisitos de conservar geografía ni los límites de suavidad.

Presupuesto: una preparación y un solve L1<=600s/un hilo con guardia de memoria
V15. Si no resuelve, preservar matrices y resultado; sin otro ajuste dentro de
este candidato. Después, consumidor denso independiente de la red completa
(0.37m/0.25m), geometría hidrográfica y negativos pertinentes. No importar hasta
superarlos. V10 desplegado y pilotoV14 se conservan.
