# Corroboración de los umbrales del censo

El JSON inicial marca0.65/0.85m como valores heredados no revalidados por su autor. La integración ha encontrado lectura nativa del mismo paquete EV72 en `E:/DayZ-Baltic-Build/v30-base-surface-runtime-20261009/native-snapshot.log`, línea2: `SEA;0.65;0.85;0.75;0.1`.

La misión actual `BalticBaseSurfaceFullWaterV1.BalticTrial/init.c:80` emite respectivamente `SurfaceGetSeaLevelMin`, `SurfaceGetSeaLevelMax`, `SurfaceGetSeaLevel` y `SurfaceGetSeaWaveMax`. Cabecera del log: terreno b54963eb; PBO del run EV73 mundoa08b96a1/agua3946db8b. Las cifras del censo no cambian: queda corroborado el rango0.65–0.85 en el mismo estado de mapa, sin afirmar que cada zona censada sea un fallo gráfico.

`SEA_LEVEL=.75` y margen0.05 del constructor describen otra decisión (elegibilidad de piezas); no contradicen esa lectura nativa ni sustituyen su rango. El calado0.95m sólo es requisito de corredores navegables acordados: el resumen geométrico hipotético de elevar todos los fondos no convierte todos los estanques o tramos de delta en corredores navegables.
