# EV75 — discriminador de fondo Narva, propuesta de prueba

El usuario pide investigar con Luna para reducir ensayos de motor. La evidencia antigua Peipus aisló dependencia del fondo y la revisión actual encuentra fondo bajo el mar en el eje óptico del frame EV73. Esto no prueba todavía identidad del shader ni todos los rectángulos.

Una sola variante offline: partir del terreno EV72 b54963eb; elevar a 1 m únicamente vértices sumergidos dentro del círculo Narva de radio480 m ya empleado por el proyecto. Exigir que todas sus caras incidentes estén completamente mojadas antes y después y que todos sus planos físicos y visibles incidentes permitan al menos0.95m sobre el fondo1m. Congelar reserva vial, plataformas, tierra y soporte de caras que cruzan orilla. P/F, clases, niveles, objetos y superficie visual del paquete sin cambios. Es diagnóstico reversible separado, no nueva base ni solución global.

Discriminación: la región modificada debe contener el terreno bajo el eje óptico del frame EV73; el fondo bajo el puente debe quedar intacto como control profundo en la misma escena. Registrar cuánto queda bajo0.85m: el experimento no pretende tapar todos los fondos. No modificar ni promover EV68.

Antes de empaquetar: consumidor de las caras realmente cambiadas calcula el área mojada de los planos físicos y visibles antes/después, rechaza nuevas intersecciones con tierra, altura superior a1m donde antes era inferior, descensos, cambios de máscaras/reserva/plataformas y calado nuevo inferior0.95 en la parte modificada. Reportar pendientes/ángulos creados: diagnóstico no implica aceptación estética del lecho. Leer fuente WRP antes de construir y probar también un cambio negativo de una orilla.

Motor sólo si gates y revisión independiente pasan: mismo paquete de agua/materiales, misma cámara y clima, mapeo por GetScreenPos de puntos de tratamiento/control y tres capturas cargadas por fase. A existente sirve de evidencia de reproducción pero A/B/A exige retornoA tras B. Registrar hashes y consulta de altura nativa. Si desaparecen los parches sólo sobre el tratamiento y reaparecen al retornar A, dependencia local del lecho confirmada. Si no, rechazar esa corrección como explicación suficiente y no aumentar la cota ni repetir parámetros. Identidad mar/pond sigue hipótesis salvo evidencia adicional.

Presupuesto de esta unidad: una variante offline, un ciclo A/B/A si la preparación pasa, sin barrido de cotas/materiales/opciones. Cielo magenta/texturas ausentes invalidan la fase; no registrar PASS por capturas no cargadas. Aún no se ha lanzado el ensayo.
