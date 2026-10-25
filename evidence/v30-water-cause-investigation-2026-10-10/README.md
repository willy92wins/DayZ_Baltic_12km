# EV75/76 — investigación localizada de los rectángulos de agua

Las dos revisiones Luna pedidas por Guillermo localizan el defecto y eliminan comparaciones inválidas; no reparan todavía el render. La base sigue EV72/73, mundo a08b96a1, agua3946db8b, terreno b54963eb. No se promueve EV68 ni ningún terreno rechazado.

## Hechos contrastados

- Dos transiciones visibles de la captura EV73 `233431_541` coinciden con bordes de objetos globalvis: par16812770/71,145px de solape con0.44–0.46px de offset; par16812805/15,45.28px de46 con1.75–1.79px. Son trazas visuales aproximadas, no límites de cajas ROI.
- Los cuatro ODOL comparten material CalmWater, normalmap y flags de alpha/visibilidad. Geometría y radios difieren. Lectura `scan_fallback`, sin errores de LOD: no convertir metadatos interpretados en prueba del mecanismo de render.
- EV76 lee proyección nativa en EV72 sin alterar mapa: focal654.545476px,8puntos retenidos con error máximo0.000073px. ROI gris345/345rayos atraviesan P/F por delante del terreno; terreno bajoF −4.445…−1.699m. El control ondulado378/378 también está bajo el mar. Por tanto, el lecho profundo es un factor compartido, no una clasificación del gris.
- La ROI gris toca reserva vial en20.3% de caras muestreadas. El eje óptico no era una localización válida del parche: está fuera de la ROI gris seleccionada.
- EV73 nativo confirma SeaMin0.65/SeaMax0.85. El censo global localiza120componentes interiores candidatos y548195.87m² de coincidencia a nivel máximo. Es índice geométrico, no120fallos gráficos; los gates secos EV72 no autorizan ni prohíben por sí solos reparar agua.
- El control histórico Peipus05-10 mejoró al elevar fondo manteniendo agua/material; no prueba universal ni mecanismo del Narva actual.

## Rechazos y límites

EV75 directo14c6b0b2 falló calado/pendientes; correcciónc0e0c206 conserva huella y mínimo0.952835m en4872caras afectadas, pero falla corte estricto de pendiente y objetivo del eje. Ambos permanecen fuera del juego; no se relajó el consumidor ni se redefinió retrospectivamente PASS.52caras tocaban reserva aunque sus vértices cambiados no. Ver rejected-narva/README.md.

El primer análisis DDA de EV76 con cero hits era incorrecto y queda invalidado. `projection/roi-world.json` final usa paso4 y `visible-field.npy` real; roundtrip nativo y celda óptica pasan. La captura EV76 es magenta y no sirve para aceptación visual: la calibración se transfiere a EV73 por pose/FOV/viewport iguales, con ese límite explícito.

Se rechaza el swap de modelos propuesto inicialmente por Luna: huellas distintas cambiarían P/F y exposición. La siguiente unidad EV77 observa una sola pose en wireframe para distinguir categorías visibles Water/Ocean/OceanShore; no vuelve a barrer opciones ni cambia el mapa. Ausencia de arista no prueba ausencia de capa, y presencia no atribuye composición del pixel normal.

## Evidencia y estado

`preservation.json` registra55archivos copiados con hash/bytes: scripts, informes, capturas y dos notas Luna. Terrenos NPZ rechazados permanecen en E:/DayZ-Baltic-Build, identificados por hash; no se empaquetaron. EV76 run3b4a4a81 cerrado orderly y lease liberado. EV77 está en preparación/ejecución en E:/DayZ-Baltic-Build/v30-water-wire-classification-20261010; consultar LIVE-STATE antes de usar DayZ. La base completa sigue abierta.
