# EV112 — suavizado alrededor de vértices protegidos

Continuación de P12 y bug011, dentro de la corrección autorizada. Base U2/T:
terreno `ab96a8f6fb3da6ca02e566caa1cf5d61ad720d340ec611316c33bcbe2ce717ef`.
No se permite mover vértices protegidos, extremos de orilla, triángulos de
carreteras, apoyos, reserva, islas o disco015-45. El candidato va separado.

Descubrimiento de solo lectura: de327grupos de picos y1156depresiones, las
cotas de vecinos libres permiten potencialmente corregir66 y15respectivamente
sin mover sus ápices protegidos. Es una condición necesaria, no una solución.
Fuente: `guarded-relief-discovery/report.json`, con hashes de terreno/huella.

El suavizado anterior seleccionaba como testigos los mínimos/máximos del
terreno de entrada. Para un ápice fijo, puede elegir otro vecino fijo e imponer
una condición imposible aunque otro vecino libre pueda subir suavemente.
[DESIGN] Añadir al solver existente una opción explícita que elija el testigo
mínimo por su cota inferior alcanzable y el máximo por la superior. Mantener
su modo anterior como predeterminado. La desigualdad testigo sigue siendo
suficiente: min(P)−max(R) ≤ H(a)−H(b). Los verificadores usarán min/max reales,
sin depender de qué testigos eligió el autor.

Piloto inicial: grupo de un vértice en fila181,columna1316, bloqueado solo por
la orilla. Mantenerlo exacto y modificar únicamente vecinos libres a≤24m,
con transición/fijación exterior, delta≤0,75m y límites de suelo existentes.
Objetivo thin-plate con prior suavizado, pendiente≤max(35°,original), sin nuevas
aristas>20° ni empeorar las existentes. No se acepta bajar un contador mediante
una corona artificial: registrar energía/curvatura, sección y malla para revisión.

Puertas: ápice/protecciones/carretas/orilla exactos; min/max independiente bajo
0,30m en el objetivo; ningún pico/pozo/arista nuevo o agravado; clasificación
de agua idéntica; regeneración bury/huella sin cambios; P11 sin regresión.
Después bosque y composición/compilación/sonda si se integra. La navegación
U2 en curso corresponde a U2 original: no desplegar el nuevo terreno durante
su generación ni atribuirle aceptación del nuevo candidato.

Hasta tres candidatos motivados, dos sin progreso obligan a rediagnosticar.
Revisión Fable5.1 y contraejemplos del solver antes de promover. No cambian
umbrales, exclusiones ni el requisito de revisión visual conjunta.

Revisión Fable5.1: pilotoA supera geometría/agua/P11 pero eleva dos vecinos por
encima del ápice fijo; no promoverlo. CandidatoB limita la cota superior a
max(altura original del vecino, altura del ápice); en pozos, cota inferior a
min(original, fondo fijo). Así no aparecen nuevos sobrepasos y no se obliga
a bajar una ladera que ya era más alta. Registrar subidas/bajadas, energía
thin-plate pura sin prior y cantidad de vértices pegados al límite. Usar cap
interno0,2999 para margen float32, conservando umbral del consumidor0,30.


Extensión del lote tras el piloto: C se rechaza por3 sobrepasos en extremos
protegidos no objetivo; D incorpora los límites para todos los extremos
protegidos dentro del radio24m. Las máscaras se rederivan con el mismo guard
de carretera y las mismas protecciones originales. La CLI se ejecuta y
reproduce el inventario. Los fallos SLSQP quedan SOLVER_FAILED; no se confunden
con infactibilidad demostrada. La energía se comprueba por clúster contra h0;
el censo final y las puertas geométricas se comprueban globalmente.
