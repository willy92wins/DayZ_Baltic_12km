# Inventario global de caras de orilla V30

Diagnóstico de solo lectura sobre el candidato `a84dfff0`, no una modificación
del terreno ni una nueva puerta de aceptación. Script:
`tools/terrain/audit_v30_shore_triangles.py`.

- 170.073 triángulos mixtos de tierra/agua; 4.149 superan 35°; máximo 64,7481°.
- Las clases de agua se pueden solapar dentro de una misma cara: **no sumar**
  las filas de `by_water_class` para reconstruir el total global.
- Los 4.149 y el máximo coinciden con el informe independiente previo
  `evidence/v30-delta-fairways-2026-10-02/terrain-gates.json`.
- Seis controles analíticos: pendiente conocida en ambos triángulos, exclusión
  de caras totalmente secas/mojadas, cara mixta plana, identidad del triángulo
  seleccionado y rechazo de NaN. El hash del script y del NPZ están en summary.

`hotspots.png` agrupa las caras en sectores de 250 m para preparar la revisión
visual. Muchos sectores se concentran en el Luga. `steep-faces-game-xz.json`
usa metros del juego X/Z; no representa longitud/latitud RFC 7946.

Este recuento no demuestra que todas las caras sean defectos visibles, no mide
inundación dinámica y no autoriza a rellenar canales o alterar las reservas.
El gate genérico limita pendientes de caras completamente terrestres; la
estadística mixta se informa aparte. La cifra local de 113 caras de una revisión
anterior no era el total del mapa.

Siguiente uso: elegir sectores representativos y comparar contorno y perfil con
cámara controlada, protegiendo profundidad navegable, cruces, islas y reserva.
El piloto Narva `bb270ecc` sigue separado y no promovido.
