# Agua de cauces con piezas vanilla inclinadas — piloto (BALTIC-015)

Decisión de Guillermo, 03-10 noche: «Vanilla en cauces»; plan aprobado por él la misma noche. Este plan
cubre solo el piloto. El
despliegue a todo el mapa se planifica con su resultado. Ejecutor: Claude, sin concurrencia.
Relevo previo: `C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-03-dayz-baltic-integracion-orillas-y-agua-vanilla.md`.

## Hechos de partida, medidos el 03-10

- **Piezas vanilla** (`DZ/water/streams`, ODOL v54, leídas con el debinarizador local):
  - Ríos: `river_24_{6,12,24}` y las curvas `river_24_24_{l,r}{10,30}`.
  - Arroyos: `stream_14_{6,12,24}` y las curvas `stream_14_24_{l,r}{10,30,45}` y
    `stream_14_16_{l,r}{45,90}`.
  - Miden 24 y 14 m de ancho, con el origen en el centro. En las rectas, la lámina es plana
    durante 18 m a +0,07 m, y en cada extremo un faldón de 3 m baja hasta −0,07 m.
  - Usan el material `water_river.rvmat`, con flowmap. El agua la registra el LOD roadway
    (`water_ext`), no un pond.
- **Chernarus:**
  - Las rectas consecutivas van a 24 m (358 de 580 pares vecinos).
  - El flujo va hacia −Z local en 370 de 552 ríos inclinados y en 301 de 384 arroyos.
  - La pendiente mediana entre vecinas es del 2,1–2,4 %.
- **Terreno d5dadae8:**
  - Hay 5.381 escalones ≥5 cm entre celdas mojadas vecinas, sobre todo en ríos y arroyos,
    repartidos en 293 grupos.
  - El nivel de diseño va en terrazas: tramos planos con saltos entre ellos.
- **Motor:**
  - `scripts/4_World/entities/vehicles/boatscript.c:395` para el motor si
    `GetWaterDepth` en la hélice es menor que −0,2 m.
  - `GetWaterDepth` da positivo sobre las piezas vanilla: 365 de 375 ríos y 312 de 384 arroyos.
  - La flotación sobre agua roadway no se ha probado.
- **WRP:** cada registro es una matriz 3×3 más la posición (`tools/terrain/wrp0wzd.py:8`).
  Hoy `tools/terrain/derive_world_v30.py:48` escribe siempre la rotación identidad.

## Tramos del piloto

| Tramo | Caja X / Z (m) | Ancho y calado actual | Nivel | Pieza y prueba |
|---|---|---|---|---|
| R1 Luga, navegable | 10326–10590 / 3978–4206 | 43 m; 2,25–5,8 m | 4,2 → 2,1 m, saltos de hasta 1,58 m | `river_24` escalado ~1,9; lancha |
| R2 Чёрная, río | 8196–8286 / 8892–9258 | 8 m; 0,11–0,47 m | 8,4 → 1,65 m, saltos ≤0,25 m | `stream_14` escalado ~0,7 |
| R3 arroyo empinado | 7176–7446 / 5598–5862 | 3–6 m; 0,17–1,2 m | 21,7 → 4,6 m (~5 %), saltos de hasta 0,7 m | `stream_14` escalado ~0,4 |

Además, un banco de calibración en llano seco: cuatro piezas con inclinación de 0° y 2°, y
escalas de 0,5, 1 y 2.

## Reglas de lámina, lecho y piezas [DESIGN]

- **Lámina nueva:** perfil liso y monótono a lo largo del eje, que nunca supera el nivel
  actual. Se interpola por el extremo aguas abajo de cada terraza, de modo que no se inunda
  ninguna orilla.
- **Lecho:**
  - Solo se rebaja, y solo dentro de las celdas mojadas del tramo.
  - Se baja hasta la lámina menos el calado mediano actual del tramo. El mínimo es 0,10 m, el
    gate vigente en `tools/terrain/verify_terrain_v30.py:31`.
  - No se sube terreno.
  - Va en una capa propia en E:. La NPZ d5dadae8 no se toca.
- **Piezas:**
  - El eje local −Z apunta aguas abajo.
  - El cabeceo es la pendiente de la lámina en la pieza, sin alabeo.
  - La escala es uniforme: (ancho mojado + 2 m) / ancho de la pieza.
  - La altura del origen es la lámina menos 0,07 × escala.
  - Rectas y curvas se encadenan por sus marcos de entrada y salida, calibrados antes contra
    Chernarus.
- **Planos horizontales:** se retiran los del tramo. En los extremos, el faldón de la pieza
  entra bajo el plano vecino con una diferencia de nivel ≤2 cm.

## Pasos

1. **Biblioteca de piezas** [DESIGN] (`tools/water/vanilla_channel_pieces.py`).
   - Saca de la geometría los marcos de entrada y salida de cada pieza.
   - Gate: al menos el 90 % de los pares vecinos de Chernarus encajan a ≤0,5 m y ≤2°.
2. **Ajuste offline** [DESIGN] (`tools/water/fit_channel_pieces_v30.py`). Calcula perfil,
   lecho, piezas y la lista de planos que se retiran. Gates:
   - todas las celdas mojadas quedan cubiertas por la parte plana o por un faldón con calado
     positivo;
   - donde la pieza sobresale del agua, el terreno queda al menos 0,1 m por encima de la lámina;
   - la diferencia de nivel en las juntas es ≤2 cm;
   - el terreno solo cambia hacia abajo y solo dentro del tramo.
3. **Paquete aislado** [EXACT, la receta de los pasos 1–3 de `plans/v30-shore-wave-integration.md`].
   - Superficie regenerada si cambia el lecho.
   - Mundo derivado con matrices completas: `derive_world_v30.py` pasa a aceptar `matrix` por
     pose, sin cambiar el caso actual.
   - El PBO de agua no cambia: las piezas vanilla vienen de DZ_Water.
   - Se despliega en `@DayZ_Baltic_CauceVanillaPilot`, sin NM.
   - Gate: solo cambian el WRP y las teselas del lecho; los registros de agua cambian solo en
     los tres tramos.
4. **Lectura en servidor** [DESIGN], una ejecución.
   - Por pieza: `GetOrientation`, `GetDirectionUp` y `GetScale` (`scripts/1_Core/proto/enentity.c:447`)
     frente a lo previsto, con tolerancias de 0,2° y 1e-3.
   - Cada 2 m por el eje y a ±(ancho/2 − 1 m): `SurfaceY`,
     `GetWaterSurfaceHeightNoFakeWave` (`scripts/3_Game/global/game.c:1185`), `GetWaterDepth`
     (`:1183`) y `SurfaceIsPond`.
   - Gate: la lámina es continua (≤3 cm entre muestras consecutivas), el calado es positivo en
     todo el cauce y la lámina queda por debajo de la orilla en los bordes.
5. **Lancha en R1** [EXACT, la receta de `plans/v30-luga-boat-validation.md`]: Boat_01_Orange,
   ida y vuelta por el eje, con sus mismos criterios.
6. **Vista:** capturas desde cámaras fijas sobre los tres tramos, antes (paquete actual) y
   después, para la revisión de Guillermo.

## Gate del piloto

Pasos 1–5 PASS y visto bueno de Guillermo a las capturas. Con eso se planifica el despliegue:
todos los ríos y arroyos y los navegables con pendiente, con NM, V4, V3 e IA.

## Riesgos y salidas

- **La lancha no flota o no sube en R1:** los navegables siguen con planos o pasan a piezas
  propias inclinadas (opción 2); ríos y arroyos siguen con vanilla.
- **La escala no cambia el agua registrada:** se usan los anchos nativos, 24 y 14 m, y hay que
  ajustar los cauces. Es un cambio de producto, así que se pregunta a Guillermo.
- **Error en la convención de la matriz:** lo detecta la lectura del banco de calibración.
- **NM sobre agua roadway:** se estudia en el despliegue, y antes se lee la NM vanilla de
  Chernarus si es accesible.

## Coste

- Herramientas: 2–3 h.
- Paquete: 30 min.
- Una ejecución de servidor (~20 min) y una de cliente con lancha y capturas (~30 min). El
  cliente se abre en el escritorio de Guillermo: se avisa antes.

## Fuera de alcance

NM, V4, V3, IA física, Terrain Builder, los 22 cortes y el rendimiento.

## Resultado provisional — 04-10, madrugada

Evidencia: `evidence/v30-vanilla-channel-pilot-2026-10-04/README.md`.

- **Pasos 1–3 hechos.** Las desviaciones están en la evidencia:
  - R1 pasó a Narva_28.
  - Rectas sobre un eje suavizado en lugar de curvas encadenadas.
  - Planos recortados en lugar de retirados.
  - El gate de calibración previsto falla porque vanilla desplaza las piezas de lado; los marcos de las piezas
    son coherentes.
- **Paso 5 PASS:** la lancha recorre R1 en los dos sentidos.
- **Paso 4: el motor coloca las 100 piezas exactas,** pero el agua que registra no coincide con la malla en las
  piezas inclinadas o escaladas. Hay trozos sin agua y, en R3, la lámina se aleja 10 cm de mediana de la prevista.
  Diagnóstico pendiente.
- **Paso 6 sin hacer:** se cerró el cliente antes de las capturas.
- **Diagnóstico del agua (04-10, 01:00):** la lámina desplazada y los huecos eran un efecto de la sonda V1, que
  consultaba desde suelo + 50 m. La regla del motor está en `tools/water/engine_water_model.py` (1.940/1.941
  filas). A alturas de juego no hay huecos previstos. Las diferencias reales están en los faldones (±0,07·escala,
  como en vanilla) y en algunas juntas, hasta 13 cm. Queda pendiente un solo run con la lectura V2 y las capturas.
- **Paso 6 y lectura V2 (04-10, 02:15–02:45):** capturas del piloto 19/19 (run 63008090) y del control 13/19 (run
  337562e3, cortado por un reinicio del PC). La lectura V2 coincide con el modelo en ≥99,65 % de las filas y no deja
  huecos en los tramos. Falta la revisión visual y terminar el control.
