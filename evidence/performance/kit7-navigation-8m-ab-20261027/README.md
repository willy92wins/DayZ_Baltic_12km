# RAM del kit7 con navegación de 8 m frente a Chernarus

Resultado: **FAIL_EMPTY_SERVER_RAM_BUDGET**. Se conservan las seis pasadas nuevas en orden
A-B-B-A-A-B, tres por mapa, sin repeticiones ni selección de resultados.
Cada misión tiene 30 s de calentamiento y 120 s de medición. Se mantienen
el presupuesto de RAM de 1,10 y la dispersión máxima del 5 %.

| Mediana por mapa | Baltic (MiB) | Chernarus (MiB) | Cociente | Resultado |
|---|---:|---:|---:|---|
| RAM residente | 4242.41 | 3351.26 | 1.26591 | FAIL_LOCAL_RAM_BUDGET |
| RAM privada | 4637.60 | 3735.98 | 1.24133 | FAIL_LOCAL_RAM_BUDGET |

Las seis mediciones están vinculadas a proceso y creación, misión, ejecutable,
configuración y paquetes por SHA-256. El lector se volvió a ejecutar sobre las
seis capturas antes de comparar. Los observadores y cierres oficiales de cada
servidor propio están archivados. El muestreo comienza antes del calentamiento;
los hashes posteriores se calculan fuera de la ventana de medición.

Esto mide RAM del proceso servidor vacío, sin CE, AI, jugadores ni cliente.
CPU se conserva como dato descriptivo. No acredita FPS, VRAM, capacidad para
80–100 jugadores ni aceptación visual o global del mapa. Los resúmenes de
actividad del equipo no prueban ausencia de carga ajena; los nombres de las
aplicaciones y los RPT completos permanecen locales.

La corrección funcional se mantiene separada: las 607 consultas nativas del
kit7 pasan con máximo 0,711963 m y límite intacto de 0,801 m. Véase
../../v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-navigation-8m-functional-20261027/README.md.
La receta, revisiones independientes y controles de preparación están en ese
checkpoint. Los archivos binarios del mapa y de vanilla no se publican en Git.

Los diagnósticos adjuntos exploran otros tamaños de tesela sin modificar el
mapa. Son estimaciones para priorizar experimentos: 12 m estima 0,715 m en los
ocho puntos originales, pero predice 74 excesos en el conjunto amplio. El mismo
método predice 10 excesos para 8 m, que pasa realmente en el motor, y 125 para
12,5 m, que falla en cuatro. No sirve como gate de aceptación. Cualquier nueva
variante necesita una generación propia, las mismas 607 consultas y otra
comparación de RAM completa antes de ser promovida.

Esta variante no se promueve como optimizada: el presupuesto de RAM no ha
superado la aceptación. Se conserva el éxito funcional y se requiere una
alternativa motivada antes de otra generación. No se cambian los límites.
