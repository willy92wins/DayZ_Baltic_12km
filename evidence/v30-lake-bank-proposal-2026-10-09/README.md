# EV19 — propuesta de terraplenes descartada

Una propuesta offline, sin cambiar niveles ni agua y sin desplegar. Conserva todos los vértices que soportan agua compilada, ingeniería y controles. Suaviza únicamente la tierra de las orillas exteriores de los dos lagos grandes.

Los controles físicos pasan, pero falla el criterio de forma en ambos lagos: la curvatura empeora un 2,21 % en el suroeste y un 3,18 % en el sureste. No alcanza la reducción mínima del 10 %. Las crestas que bajan no compensan ese empeoramiento. Los 3.299 vértices de la propuesta no se integran en EV16.

`proposal.json` contiene medidas y hashes; `terrain-delta.npz` conserva los cambios rechazados. No se abre una búsqueda de radios o intensidades gaussianas. La decisión de niveles del plan sigue pendiente del usuario; esto no la anticipa.
