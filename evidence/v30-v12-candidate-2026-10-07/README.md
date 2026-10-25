# Candidato v12: fondo de los navegables a 1,0 m — 07-10-2026

La v12 es la v11 con el fondo de los ríos navegables subido al suelo de 1,0 m que ya tiene el resto del agua interior.
Lo decidió Guillermo el 07-10: «sube el fondo de los navegables a 1,0 m».

El motivo: a través de los navegables se veía el mar del motor, con oleaje, espuma y bordes rectos, y de lejos salían
parches de colores (BALTIC-018, `../baltic-018-navegables-2026-10-07`).

Productos en `E:/DayZ-Baltic-Build/v30-v12`. Desplegado como `@DayZ_Baltic_V12Candidate` (mundo f0813174 + agua 07c5295f; copias comprobadas por hash, `E:/DayZ-Baltic-Build/v30-v12/deploy-receipt.json`), misión `BalticTideProbeV2.BalticTrial`. **Sin ver en motor y sin aceptar.**

## Qué cambia frente a la v11

| commit | herramienta | qué hace |
|---|---|---|
| ae233e1 | `profile_inland_v30.py --bed-floor-navigable --bed-floor-navigable-min-depth 1.0` | sube cada vértice navegable a min(1,0 m, nivel − 1,0 m, tope de las puertas), también los del corredor exacto de 24 m, así que siempre quedan al menos 1,0 m de agua; sin la opción, la pasada sale igual que en la v11 (autoprueba) |
| — | `scripts/chain_v12.sh` | repite desde la pasada de orillas con los parámetros de la v11; lo anterior (hasta el dique del v6) y el agua son de la v11 (`-Pieces`, PBO 07c5295f) |

**Primera construcción, descartada** (`E:/DayZ-Baltic-Build/v30-v12-stepbed`, sin paquete). Solo subía los vértices con
el agua a 2,0 m o más. Donde el nivel cruza 2,0 m, el fondo saltaba de 1,0 m a −2…−7 m, y eso habría dibujado una línea
de mar de orilla a orilla. Se paró en la superficie, se renombró la carpeta y no se borró nada.

## Resultados (sin motor)

**Frente a la v11** (`check-v12-vs-v11.json`): PASS.

- Solo cambian vértices navegables, 21.777, y solo hacia arriba (hasta 7,01 m).
- Las clases y los niveles son idénticos.

**Agua que queda sobre el fondo:**

- Con el agua a 2,0 m o más (13.250 vértices): el fondo queda a 1,0 m, con 1,00–2,17 m de agua (mediana 1,72 m).
- Tramos bajos hacia el mar (8.235 vértices): 1,00 m exacto de agua.

**Navegables con el fondo por debajo de 0,85 m: de 28.505 a 14.594 vértices** (el 46 % de los 31.953 navegables por
encima del corte de 0,80 m). El nivel mediano de los que quedan es 1,35 m. Son:

- los tramos bajos hacia el mar: con el agua por debajo de 1,85 m, conservar 1 m de agua deja el fondo bajo el mar;
- la zona de Narva (unos 4.000 vértices), que la pasada no toca.

**Censo por tramo** (`reports/navigable-below-sea.txt`). Cuenta todos los navegables, también los que están a la cota
del mar, así que el total pasa de 33.148 (90,6 %) a 19.237 (52,6 %).

| tramo navegable | fondo bajo el mar en la v11 | en la v12 |
|---|---|---|
| el del punto de aparición, el de la captura de Guillermo (14 ha) | 3.126 (80 %) | 30 (1 %); fondo mediano a 1,00 m |
| el grande (77 ha) | 19.547 (91 %) | 8.732 (41 %), en los tramos bajos; fondo mediano a 1,00 m |
| Narva (22 ha) | sin cambio | sin cambio |
| el tramo a la cota del mar (18 ha, agua a 1,00 m) | 97 % | sin cambio en la práctica (fondo de −2,7 a 0,0 m) |

Lagos, ríos, arroyos y estanques no cambian.

**Puertas** (`verify-v12.json`, `roads-v12.json`): las mismas que en la v11.

- Calado: 1 fallo. Piezas: 21. Fondos, suelo de tierra, taludes y orillas: 0.
- Narva, distinto por diseño. Carreteras: PASS.

**Paquete:** mundo f0813174 + agua 07c5295f (la de la v11). Terreno 8b3a8c55.

## Calado para la navegación (paso 2 del plan, contrato P9)

- El calado de los navegables pasa a ser el nivel del agua menos 1,0 m: 1,0–2,17 m. Ya no es el de 3,05 m de
  BALTIC-012/013.
- La embarcación de referencia es la lancha vanilla. **No se ha probado** que navegue con ese calado.

## Qué no se ha comprobado

- Nada en motor: si en los navegables altos ya no se ve el mar, y cómo se ve el paso a los tramos bajos.
- La lancha vanilla.
- Qué hacer con los tramos bajos y con Narva, que siguen con el mar debajo (decisión de Guillermo).

## Siguiente

La sección «Rumbo para seguir» de `HANDOFF.md`.
