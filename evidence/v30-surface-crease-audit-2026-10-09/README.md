# EV24 — inventario de quiebros de la superficie completa

Se miden las 12.566.533 aristas internas de los 8.380.418 triángulos nativos de EV16. Los normales se contrastan con productos vectoriales independientes, un plano inclinado y un pliegue conocido de 45 grados. No se interpretan los umbrales de inventario como aceptación artística.

La tierra natural tiene 8.341 quiebros mayores de 30 grados; 7.698 están en la banda de 54 m de orilla. El máximo de 69,99986 grados en x11319,z3747 proviene de dos caras opuestas que cumplen individualmente el límite de pendiente de 35 grados. Por ello un verificador de pendiente aislada no impide estos pliegues.

`audit.json` usa exactamente los cuatro vértices de las dos caras incidentes. La primera salida, conservada como `audit-conservative-domain-superseded.json`, exigía los seis vértices de las dos celdas vecinas: era conservadora al clasificar dominios, pero excluía algunas aristas válidas. El control `exact_four_incident_vertices` reproduce y corrige esa diferencia. Geometría sin cambios en esta unidad.
