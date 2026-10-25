# Prueba de BALTIC-018: el fondo del Peipus subido a 1,0 m — 05-10-2026

Prueba de la hipótesis que dejó abierta el v6: las bandas del agua de los lagos vistas desde el aire son el mar del
motor dibujándose bajo el lago, porque el fondo queda por debajo de él. Productos en `E:/DayZ-Baltic-Build/v30-v7probe`.
Es una prueba, no un candidato: solo cambia el fondo de un lago.

## Qué se construyó

- **`tools/terrain/raise_beds_v30.py`** (nuevo). Sube el fondo de los cuerpos de agua estancada elegidos por un punto
  (etiquetado del censo) a `max(h, min(--floor, nivel − --min-depth))`. Solo sube; no cambia clases, niveles ni orillas.
- **Terreno `ddd83a56`**: el del v6 (`e07ee373`) con el lago 288 del censo del v6 (el Peipus; en las capturas del v5 y
  del v6, «lago 269»), de 4,62 km² y con el agua a 2,64 m, con el fondo a 1,0 m. Suben 125.292 vértices, como máximo
  6,36 m (de −5,36 a 1,0 m). Queda un mínimo de 0,10 m de agua en vértices que ya eran someros
  (`reports/beds-report.json`).
- **Dos paquetes con el mismo terreno y el agua del v3b (`c687a7be`):**

  | variante | superficie | mundo | mod |
  |---|---|---|---|
  | A | la del v6 | `7cecad69` | `@DayZ_Baltic_V7BedProbe` |
  | B | la del v5 | `eb383bd8` | `@DayZ_Baltic_V7BedProbeB` |

  Usar una superficie ya hecha deja igual el color del fondo, así que lo único que cambia es la geometría. La B se hizo
  para descartar la máscara de grava del v6 como causa de la tierra oscura (abajo).
- **Copias por hash:** `scripts/deploy_v7probe*.py`. `reports/deploy-receipt-B.json` es el recibo de la B; el de la A
  lo sobrescribió, y sus hashes están en `reports/build-receipt-A.json`.

## En motor

Misión BalticTideProbeV2, cliente a 1920×1080, nublado 0,3, sin niebla ni lluvia, a las 12:00. El jugador se
teletransporta junto a cada pose antes de mover la cámara (BALTIC-001). Hubo tres runs, cerrados en orden:

- `c20d6f6b`: variante A;
- `5d3900d6`: el v5 sin cambios, como control con la misma luz;
- `7294adce`: variante B.

Poses, capturas y hashes en `runtime/shots-manifest.json`.

### BALTIC-018: causa confirmada

En `figures/fondo-de-lago-a-1m.jpg`:

- **Con el fondo a 1,0 m, el agua del Peipus sale uniforme**: desde 330 m, desde 40 m y desde otra posición, en las dos
  variantes. Desaparecen las zonas de agua oscura con oleaje y los parches planos de bordes rectos y en dientes.
- **Controles con la misma luz:**
  - el v5 visto hoy en el mismo encuadre mantiene las bandas;
  - el lago 202 (1,96 km², agua a 2,13 m, fondo a −5,87 m), sin tocar y en el mismo run que la variante A, también.
- **Causa:** el mar del motor (0,65–0,85 m) se dibuja bajo cualquier lago con el fondo por debajo de él. Según el punto
  de vista se ve el mar o el fondo, en polígonos de bordes rectos.
- **Alcance** (`reports/bed-floor-stats.json`, terreno v6):
  - lagos: 286.957 de 312.745 vértices tienen el fondo por debajo de 0,85 m, con una profundidad mediana de 8,0 m;
  - navegables: 29.921 de 32.421;
  - ríos, arroyos y estanques: pocos, junto al mar (1.487, 739 y 856).
- **Con un suelo de fondo de 1,0 m y 0,30 m de agua como mínimo:**
  - los lagos quedarían con 0,3–1 m de agua (97.552 vértices), 1–2 m (183.774) o 2 m o más (5.631);
  - Peipus, 1,64 m; lago 202, 1,13 m; lago 106 (3,37 km², agua a 1,43 m), 0,43 m;
  - en los navegables, 7.322 vértices se quedarían con menos de 0,30 m: choca con el calado.

### La «frontera» de dos colores: textura que tarda en cargar (BALTIC-019)

En `figures/tierra-oscura-cargando.jpg`:

- En las capturas del v6, la tierra sale oscura por teselas de 384 m. La «frontera» del lago LHIGH cae en x = 3456 m,
  el borde entre las teselas de capa 8 y 9.
- **No es la máscara de grava del v6, que fue mi primera sospecha:**
  - el satélite de esas teselas es idéntico en v5 y v6 (PNG y PAA por hash), y las máscaras solo cambian bajo el agua;
  - con la superficie del v5 (variante B), la tierra del Peipus sale oscura a los 40 s y a los 2,5 min ya va saliendo
    verde;
  - el v5 sale verde a los 10 s en las dos vistas.
- **Tampoco es el formato:** las PAA de capa tienen la misma estructura que las de Chernarus (512 px, 8 mipmaps,
  DXT1/DXT5; `scripts/paa_mips.py`). El PBO lleva las 1.024 + 1.024 texturas y los 4.775 materiales, como el del v5
  (`scripts/pbo_layers.py`).
- **Con el fondo a 1,0 m**, las teselas que aún no han cargado se ven también a través del agua: son los rectángulos
  oscuros y claros que quedan dentro del lago.
- **Hipótesis sin probar:** el cliente sin foco (unos 20 fps) y los saltos de cámara de kilómetros retrasan la carga.

## Revisión de otra familia: `shape_causeways_v30.py` y `--bed-surface`

GLM-5.3-Flash en el GX10 revisó el commit f6b3825 (`review-glm-causeway/`; 20.366 tokens de entrada, 1.100 s).
Veredicto: aceptar con arreglos. Hay tres hallazgos menores, y sus citas son exactas.

- **F1** (el alcance del talud supone un fondo a −8 m): aquí no afecta, porque cerca del dique el fondo no baja de
  −5,37 m. Se añadió una comprobación exacta que se detiene si algún vértice fuera del alcance quedara bajo el talud.
- **F2** (las cuentas `to_sea`/`to_land` antes de deshacer caras): corregido.
- **F3** (`surface.json` gana la clave `bed_surface`): es intencionada; las teselas siguen idénticas sin la opción.

Con F1 y F2, la herramienta reproduce el terreno del v6 byte a byte (`e07ee373`).

## Pendiente

- **Decisión de Guillermo:** cómo llevar el suelo de fondo a todo el mapa (profundidad de los lagos, el lago 106 y el
  calado de los navegables).
- **BALTIC-019:** capturar tras 60–120 s por pose y probar con el cliente en primer plano.
- **Orillas e islas de los lagos:** `tools/terrain/profile_lakes_v30.py`, encargado a GLM (dos lanes), con el suelo de
  fondo como opción.

## Sin verificar

- Si la carga lenta depende del foco del cliente.
- Cómo se ve desde el aire un lago con 0,3–0,5 m de agua sobre el fondo a 1,0 m.
