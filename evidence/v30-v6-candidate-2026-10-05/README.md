# Candidato v6: el dique de Kronstadt como terraplén y fondo sin vegetación bajo el agua — 05-10-2026

Sobre el v5 (`../v30-v5-candidate-2026-10-05`), por el orden que aprobó Guillermo el 05-10: primero el dique y, a la
vez, el desborde de FLAT1. Productos en `E:/DayZ-Baltic-Build/v30-v6`. Desplegado como `@DayZ_Baltic_V6Candidate`
(mundo `72493b1d…`, agua `c687a7be…`, la del v3b; copias comprobadas por hash en `reports/deploy-receipt.json`). Visto
en motor en el run `8f9ced33` (misión BalticTideProbeV2), cerrado en orden.

## Qué cambia frente al v5

- **`tools/terrain/shape_causeways_v30.py`** (nuevo), sobre el terreno del v5 (`62b162cb`). Da el terreno `e07ee373…`.
  - Busca los tramos de carretera con mar a los dos lados. Solo salen los dos del dique: el sur, de 403,5 m, y el
    este, de 618,5 m. Los otros ocho tramos con agua a los dos lados son puentes, con la carretera por debajo del
    agua en el terreno, y no se tocan (`scripts/find_causeways.py`).
  - Rehace cada tramo como terraplén sobre el eje de la carretera: cresta de 20 m a max(perfil, 1,70 m) y taludes 1:2
    (26,6°) hasta un fondo marino suavizado. Rampas de 80 m en los extremos, solo rellenando.
  - Solo rebaja donde hay mar a menos de 24 m a los dos lados del eje, y solo mar o la propia plataforma y reserva de
    la carretera. No rebaja ningún vértice de tierra natural.
  - Mismas puertas que `profile_coast_v30.py`.
- **`tools/terrain/build_surface_v30.py --bed-surface gravel`** (opción nueva): bajo el agua estancada mantiene el color
  de la tierra pero pone `cp_gravel`, cuyo `character` es `"Empty"` (`DZ/surfaces/config.cpp`, clase `cp_gravel`). Así
  no salen hierba ni arbustos del agua somera.
  - Sin la opción, la herramienta da las mismas teselas byte a byte (dos teselas comparadas por hash).
  - Con ella, el satélite no cambia y solo pasan a grava píxeles de máscara bajo el agua: 1,91 millones de píxeles de
    1 m² en todo el mapa.
- **El resto de la cadena** es la del v5 (`chain-v6.sh`).

## Resultado offline (`reports/`)

- **Dique** (`causeway-report.json`, `figures/causeway-before-after.png`):
  - Cresta de 1,45–1,52 m (p5–p50) a 1,70 m.
  - Giro de la línea de agua cada 12 m junto al dique: p50 de 14,0° a 5,7° y p95 de 44,7° a 10,9°.
  - Tierra de 1,40–1,60 m junto al dique: de 377 vértices a 31.
  - 1.731 vértices cambian; 270 pasan de mar a tierra y 1 de tierra a mar.
- **Puertas:**
  - `verify_terrain_v30.py`: los mismos fallos conocidos que el v5 (6 calados en arroyos, 31 celdas de piezas, Narva por
    diseño). Taludes de orilla de más de 35°: de 3.051 frente a 3.092; playa con 74 vértices más, los taludes del dique.
  - Carreteras: PASS. Cauces: idénticos. Censo de lagos colgados: igual que el v5.
- **Agua visible a 0,85 m:** 41.331 píxeles inundados por el mar, frente a 41.498 en el v5.

## En motor (`runtime/view-8f9ced33/`)

El primer cliente (run `6da865d6`) se cerró solo al llevar la cámara de golpe a unos 6 km del jugador, sin línea de
cierre ni registro de crash: es BALTIC-001. Con el jugador teletransportado junto a cada zona antes de mover la
cámara, el run `8f9ced33` hizo todo el recorrido. Cliente a 1920×1080, sin menú de pausa (se cerró con `continuebtn`).

- **Dique** (`figures/v6-dique-y-flat1.jpg`, mismas poses que el v5): los dos tramos salen como un terraplén recto,
  con los bordes paralelos y espuma a los dos lados; sin escalones a 9, 30, 40 y 80 m.
  - La grava del centro sale más oscura que en el v5. El satélite y la máscara de la carretera son los mismos (el
    satélite, algo más claro), así que lo atribuyo a la luz de esa sesión, sin comprobar.
- **Parpadeo de la cresta** (ráfagas de 10 en CONTROL, el tramo sur):
  - Tierra de 1,60–1,80 m frente a la de 2,2 m o más: se aparta como mucho 0,1 de cerca y 0,2 de lejos. En el v5,
    3,9 de cerca.
  - Cociente de la tierra a 1,60 m frente a la de 1,62–1,80 m: 0,021 de cerca (0,074 en el v5) y 0,005 de lejos.
  - Siguen variando los taludes de 1,20–1,55 m, pegados al agua.
- **FLAT1** (mismo encuadre que el v5): ya no salen arbustos del agua. Queda una lámina somera de agua limpia: es un
  tramo de cauce de clase estanque (1,71 y 1,90 m) con 0–0,6 m de agua (`figures/flat1-overlay.jpg`). La forma ancha y
  plana del cauce queda para el trabajo de ríos.
- **BALTIC-018, agua de lagos desde el aire** (`figures/v6-agua-de-lagos.jpg`):
  - Las bandas del lago 269 salen iguales en el v5 y el v6 en las mismas poses, aunque ahora el jugador estaba en la
    isla: no dependen de su posición.
  - Desde otra posición de cámara sigue habiendo zonas de bordes rectos; la proyección de la rejilla de 48 m de las
    teselas de agua cae sobre sus escalones.
  - Debajo de un punto oscuro hay exactamente cuatro piezas, una por tesela: no hay agua pintada dos veces.
  - El estanque vanilla de Chernarus (71 piezas, agua a 2,66 m y fondo a 2,54 m, 0,11 m de profundidad) no muestra
    ese patrón desde 40 m. Nuestros lagos tienen el fondo muy por debajo del mar del motor.
  - En el run del v6 el terreno cargó mal las texturas fuera del dique (recuadros oscuros de bordes rectos en tierra),
    lo que resta valor a las vistas del lago alto.

## Sin verificar

- La causa de las bandas de BALTIC-018. Siguiente prueba: un lago con el fondo subido por encima de 0,85 m.
- La luz de la grava de la cresta.
- El resto de calzadas: solo había dos tramos de carretera sobre el mar.
