# Cobertura física por tramos solapados — V10

Los19 casosV1 terminaron10PASS/9FAIL. La varianteAddNoiseTarget falló incluso
en el control local y se cerró ordenadamente; no es un estímulo validado para
exigir llegada exacta. El grafo del puente sí devolvió caminos directos en ocho
consultas, con controlNONE negativo y siete corrupciones rechazadas. No cambiar
terreno ni regenerar NM por estos datos de percepción.

Nueva pregunta acotada: ¿pueden los actores recorrer físicamente todos los
intervalos pendientes con objetivos cercanos y visibles? Se recupera la misión
V1/AddNoisePos, sin cambios de movimiento ni límites. Tres regresos terrestres
de120m se cubren cada uno por0–45,40–85,80–120m: nueve casos. El puente y sus
accesos, eje−135..135m, se cubren por tramos de40m, avance35m, último25m, en
ambos sentidos: dieciséis casos. Más el control local conocido: total26.
La separación de5m supera el radio4m de llegada; no quedan huecos planificados.

Congelar las coordenadas float32 y alturas antes del run. Registrar relación
con los casos originales, intervalos, hashes y alcance. Mismos criterios de
salud, continuidad, spawn, reacción, superficie, corredor4m, objetivo estable
y timeout90s. El actor no recibe posición ni velocidad durante su recorrido.
El objetivo humano se establece una vez y se asienta20s en cada caso.

Una ejecución, sin desplazar puntos ni ampliar límites al ver el resultado.
Si falla el control, detenerla; si falla otro caso, conservarlo y terminar los
restantes dentro del presupuesto. PASS significa cobertura por actores nuevos
en tramos cortos solapados; no una única persecución larga, alcance normal de
audición ni queV1/V2 hayan pasado. El mundo final permanece sin modificaciones.
Iniciar después carga y revisión visual, y reservar el ensayo fluvial largo
antes09:00UTC.
