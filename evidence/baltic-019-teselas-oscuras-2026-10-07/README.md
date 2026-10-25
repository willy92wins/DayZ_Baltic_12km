# BALTIC-019: tierra oscura por teselas en las vistas de motor — 07-10-2026

Petición de Guillermo: «hay que mirar bien lo de las teselas oscuras».

## Conclusión

**No es un defecto del mapa.** Con el mismo cliente y el mismo protocolo, Chernarus vanilla sale igual o peor: en
Berezino, a 80 m y a ras de suelo, la tierra sigue negra y los edificios, árboles y matorrales sin textura a los 7 min
del teletransporte (`figures/panels.jpg`). Es la carga de texturas del cliente de pruebas después de un
teletransporte: en la v11 tardó entre 25 s y más de 6 min según la pose (`figures/timeseries.png`). Lo que ya estaba
cargado sale con textura: la zona de aparición, que carga tras la pantalla de carga, y lo visto en poses anteriores.

## Qué se midió

**Serie de la v11** (run 9b486b9a, 10:58–11:27; `reports/dark-tiles-v11.jsonl`). Nueve poses y 36 capturas: la
primera a los 2–10 s del teletransporte y después cada 25–60 s. La medida es `tools/playtest/dark_tiles_v30.py`: la
cuota de bloques de 16 px planos y oscuros en la mitad inferior. Las vistas con tierra sin textura dan 0,37–0,63 y
las texturizadas 0,00–0,15; el agua también cuenta como plana. Una vista se da por texturizada por debajo de 0,2,
aunque una franja de teselas puede seguir oscura: es lo que pasa en END_GRIB_40.

| pose | al llegar | bajo 0,2 |
|---|---|---|
| NAVFREE_85 (primera tras arrancar; inicio aproximado) | 0,46 | entre 31 y 99 s |
| LAKE10_150 | 0,60 | entre 78 y 172 s |
| PONDS_120 | 0,58 | entre 2 y 24 s |
| L202_330 | 0,60 | no, a los 51 s (no se esperó más) |
| BORDER_E330 | 0,52 | no, a los 51 s (no se esperó más) |
| RIVER_80 | 0,48 | entre 119 y 362 s |
| END_GRIB_40 (a 150 m del RIVER_80, ya cargado) | 0,15 | desde el principio, con una franja oscura junto al borde este |
| END_VOLKHOV_60 | 0,47 | no, en 171 s y en otros 178 s de una segunda visita |
| RIVER_8 (en el RIVER_80, ya cargado) | 0,14 | desde el principio |

**Control en Chernarus vanilla** (run 4272a090, 11:27–11:38; `reports/dark-tiles-chernarus.jsonl`), lanzado con
`DayZ_MCP`, sin mods base ni file patching. El jugador apareció en (8280, 3134) y se le llevó a Berezino, a 7 km.
A 80 m, la cuota pasó de 0,43 a 0,37–0,38 y ahí se quedó durante 7 min. A ras de suelo, nada tenía textura a los
3,5 min.

**Estado del cliente** (`reports/visibility-*.csv`, una muestra cada 5 s):

- DayZDiag sin foco, a 19 FPS según el contador de diagnóstico de las capturas y con un 1–11 % de un núcleo.
- Con la tierra oscura, el proceso no leyó nada del disco en 5 s (v11, 11:13:50).

**Memoria:**

- RAM: 16–21 GB disponibles, y 52 GB comprometidos durante la v11.
- VRAM: unos 4 GB usados de 24 GB.
- La 3090 sin lease ni modelos cargados (`gpu_lease.py estado`, 11:05).

**Ventana:**

- Durante la serie v11 estuvo tapada por completo por Chrome (0 de 25 puntos visibles).
- En Chernarus estuvo a la vista en 22–25 de 25 puntos entre las 11:29 y las 11:31:46, y la tierra siguió sin textura.

**Datos del terreno** (`reports/layer-data.txt`): la misma estructura que Chernarus.

- 1024 teselas de satélite DXT1 y 1024 máscaras DXT5, de 512 px y con 8 mipmaps.
- Los mipmaps del satélite se descomprimen enteros y con el mismo color medio en cada nivel, sin ninguno negro.
- Los rvmat de tesela usan las mismas texturas de superficie vanilla, y sus rutas resuelven dentro del PBO (prefijo
  `dayz_baltic_12km_dev\tb\narva_trial`).
- El RPT y el `error.log` del cliente no tienen errores de texturas ni de materiales del mapa.

## Hipótesis descartadas

- **Memoria del sistema** (la del 06-10, con 5,9 GB disponibles): hoy había 20 GB y tardó igual.
- **Ventana tapada:** en Chernarus, con la ventana a la vista, no cargó.
- **Formato, tamaño o mipmaps de nuestras texturas:** son como los de Chernarus, y Chernarus sale peor.
- **OneDrive o file patching:** el cliente va sin `-filePatching`, el PBO se lee por la unión a C: y el disco estaba
  parado.
- **Menú de pausa al arrancar:** LAKE10_150, RIVER_80 y END_VOLKHOV_60, sin menú, también tardaron.

## Qué no se ha comprobado

- **El cliente con foco** (la ventana delante y activa): se pidió la prueba y no se hizo. Es la causa candidata que
  queda: sin foco, el cliente baja a 19 FPS y casi no usa CPU.
- **El cliente retail o la sesión de un jugador:** no hay medida. Nada indica que un jugador lo vea, pero tampoco está
  probado que no.
- **Por qué la carga casi no avanza** (0 B leídos con la tierra oscura): es interno del motor.

## Consecuencia para las vistas de motor

Una vista vale si `dark_tiles_v30.py` da menos de 0,2 y, mirada a ojo, no queda una franja oscura. Si no, hay que
esperar o repetir. Con la misma medida, varias vistas anteriores tenían la tierra sin textura:

- **v10:** BORDER_E330 0,46; L202_330 0,62; L288_330 0,37; L288_60 0,29; LAKE10_150 0,32; NAV_330 0,29; PONDS_120 0,40
  tres veces y 0,08 a los 30 min.
- **v10b:** LAKE10_150 0,61 y NAVFREE_85 0,49, en las dos capturas de cada pose.

La línea de agua se sigue leyendo, porque los planos de agua no dependen de esa textura. El color de la tierra y el
contraste de la orilla, no.

## Siguiente

1. **Prueba con foco**, unos 2 minutos con la ventana de DayZ delante. Si así la textura carga en segundos, las vistas
   se toman con la ventana delante; si no, con la espera medida.
2. **Puerta en la toma de vistas:** capturar cuando la cuota baje de 0,2, con un tope de unos 6 min por pose, y marcar
   el resto como no válidas.

## Prueba con foco (07-10, tarde, run 54aa1eef)

Petición de Guillermo: «haz la prueba con foco». Cliente v11. Esta vez la ventana se abrió en el monitor principal.
Había menos memoria que por la mañana: 6,4 GB de RAM disponibles (con WSL, Chrome, OneDrive y MTGA abiertos) y
6,9 GB de VRAM usados. La comparación se hizo dentro de la misma sesión.

| hora | qué pasó | resultado |
|---|---|---|
| 13:31:43 | teletransporte a END_VOLKHOV_60, sin foco | índice 0,50 a los 5, 27 y 80 s |
| 13:33:41 | foco dado por script (`scripts/focus_window.ps1`); Windows lo devolvió a otra ventana a los ~5 s | 0,00 a las 13:33:47, 6 s después del foco y 124 s después del teletransporte |
| 13:34:10–13:35 | LAKE10_150 y L202_330, ya sin foco | 0,66 y 0,59, sin cambio a los 15 s |
| 13:35:15 | segundo intento por script: Windows lo rechazó (`SetForegroundWindow` = False) | — |
| 13:35:51 | clic de Guillermo; foco unos 4 s | L202_330 sigue en 0,59 (vista casi toda de mar: la medida no distingue) |
| 13:47:17 | clic de Guillermo; foco 10,4 s (`scripts/wait_focus_hold.ps1`) sobre NE_120, sin textura a los 4 s | con textura a los 121 s; no hubo captura durante el foco |
| 13:49:35–13:55 | sonda a 1 fotograma/s (`scripts/focus_probe.ps1`) sobre SW_120; sin foco en todo el plazo | carga parcial sola a los ~2 min (0,84 → 0,67; fotogramas con la barra de título) |

**Conclusión: sin decidir.** El foco sigue siendo la causa candidata. Los dos casos con foco son compatibles con ella,
pero sin foco la carga ya tarda entre 25 s y más de 6 min, así que no la separan. Lo que falta:

- tener la ventana delante al menos 20 s, con la sonda grabando (`focus_probe.ps1`);
- comparar el fotograma anterior al foco con los siguientes.

Desde fuera no se puede mantener el foco: Windows se lo devuelve a la ventana que usa la persona. El monitor de esta
sesión está en `reports/visibility-focus.csv` y el registro de la sonda, en `reports/probe-SW_120-log.csv`.

## Ficheros

- `figures/panels.jpg`: el mismo síntoma en la v11 y en Chernarus.
- `figures/timeseries.png`: la cuota frente a los minutos desde el teletransporte.
- `reports/dark-tiles-v11.jsonl`, `reports/dark-tiles-chernarus.jsonl`: una fila por captura.
- `reports/visibility-v11.csv`, `reports/visibility-chernarus.csv`: visibilidad de la ventana, foco y CPU del cliente.
- `reports/layer-data.txt`: censo de capas, mipmaps y referencias de los rvmat de los dos mapas.
- `scripts/baltic019_figures.py`: genera los informes y las figuras a partir de las capturas en
  `E:/DayZ-Baltic-Build/v30-v11/views-timeseries*`.
- `scripts/dayz_visibility_monitor.ps1`, `scripts/pbo_layers_census.py`, `scripts/paa_mips.py`,
  `scripts/pbo_extract.py`, `scripts/engine_pairs.py`: herramientas de solo lectura usadas aquí.
- `scripts/focus_window.ps1`, `scripts/wait_focus_hold.ps1`, `scripts/focus_probe.ps1`: prueba con foco (dar el foco, esperar a que la ventana lo mantenga y grabar a 1 fotograma/s).
