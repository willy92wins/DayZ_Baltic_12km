# BALTIC-018, agua navegable: el mar del motor bajo los ríos navegables — 07-10-2026

Aviso de Guillermo (07-10, tarde), con una captura junto al punto de aparición de la v11: «sigo viendo problema de que
en ciertas partes del agua a distancias medias o altas no se renderiza bien el agua o muestra parches de colores».

## Qué es

En la v11, los ríos navegables (clase 3) conservan el cauce hondo:

- el agua está a 2,10–2,55 m;
- el fondo baja hasta −7,3 m (mediana de −1,3 a −3,4 m según el tramo).

El mar del motor (0,65–0,85 m) se dibuja en todo punto donde el terreno queda por debajo, también bajo el río. Por eso, a
través de la superficie del río se ve el mar, con su oleaje y su espuma. Solo las franjas de la orilla, con el fondo a
2,2–2,4 m (por encima del mar), se ven como agua somera.

El paso entre las dos apariencias sigue el borde del cauce en la malla de 6 m: sale en líneas rectas, con una línea
de espuma a lo largo de la pared del cauce. De lejos, las dos apariencias se alternan como parches.

Reproducido en motor (run 54aa1eef) en `figures/vista-y-seccion.png`:

- **Arriba:** a 12 m sobre el punto de aparición, mirando al SSE, el mismo río de la captura.
- **Abajo:** su sección a z = 5250, con el agua a 2,58 m, el fondo a −0,9…−3,8 m y la franja del mar.

Es la parte de BALTIC-018 que quedó abierta. El fondo de lagos, estanques, ríos y arroyos se subió a 1,0 m en la v9; los
navegables se dejaron como estaban hasta el contrato de navegación (paso P9 de `plans/v30-rumbo-agua-1.0.md`, sin
firmar).

## Cuánto (`reports/navegables-bajo-el-mar.txt`)

| clase | vértices de agua | con el fondo por debajo de 0,85 m |
|---|---|---|
| lagos (2) | 295.349 | 0,2 % |
| ríos (5) | 10.602 | 5,8 % |
| arroyos (6) | 13.807 | 0,3 % |
| estanques (7) | 5.269 | 14,7 % |
| **navegables (3)** | **36.596** | **90,6 %** |

Las clases 1 y 4, con el agua a 0,75 m, son el propio mar.

Los navegables forman cuatro tramos grandes:

- **77 ha**, con el agua a 2,10 m; cruza el mapa (x 2256–10602).
- **22 ha**, a 2,45 m, en torno a (2314, 6711).
- **18 ha**, a 1,00 m: ya está al nivel del mar, en torno a (9776, 9698).
- **14 ha**, a 2,55 m: el de la captura (x 996–2010, z 4632–6492).

## Opciones

La decisión es de Guillermo y cierra el contrato de navegación (P9).

1. **Recomendada: subir el fondo de los navegables a 1,0 m, como el del resto del agua.** Con el agua a 2,10–2,55 m,
   el calado queda en 1,1–1,55 m. Hay que comprobar en motor que la lancha vanilla, la embarcación de referencia del
   P9, navega con ese calado. El tramo de 18 ha, que ya está a 1,00 m, se quedaría como agua unida al mar.
2. **Mantener los 3,05 m de calado y subir el agua y el terreno de los navegables 1,5–2 m.** Para que el fondo quede a
   1,0 m o más, el agua tiene que estar a 4,05 m o más. Son 131 ha de cauce, con sus valles, y un escalón en la
   desembocadura al mar: un cambio grande.
3. **Dejarlo así:** los navegables seguirían pareciendo mar, con oleaje y líneas de espuma.

## Qué no se ha comprobado

- Qué calado necesita la lancha vanilla.
- Los parches de los demás tramos navegables: en motor solo se miró el del punto de aparición.
- Si «a distancias medias o altas» incluye también las teselas sin textura de BALTIC-019. En la captura, a la derecha,
  hay un rectángulo oscuro de borde recto sobre la tierra que encaja con ellas.

## Ficheros

- `figures/vista-y-seccion.png`: vista en motor y sección del río.
- `reports/navegables-bajo-el-mar.txt`: recuento por clase y tramos navegables.
- `reports/seccion-aparicion.txt`: clase, nivel y fondo cada 6 m en cuatro secciones al sur del punto de aparición.
- `scripts/navigable_below_sea.py`, `scripts/spawn_classes.py`, `scripts/baltic018_navigable_figure.py`: de solo
  lectura, sobre `E:/DayZ-Baltic-Build/v30-v11/inland/terrain_inland.npz`. La orientación de la malla se comprueba
  contra las alturas que da el motor (error de 0,33 m en cuatro puntos).
