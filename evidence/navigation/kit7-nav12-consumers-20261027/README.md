# Consumidor y medición preparados para Nav12

Estado: preparación revisada y pruebas offline PASS. No hay todavía resultado
nativo Nav12 ni mediciones de RAM. Fable 5.1 emitió SOUND para ambos alcances.

La sonda conserva las 607 consultas y el CSV original byte por byte. UUID nuevo
3325b685-d8cf-42d1-a476-aa2a3fe2e857; umbrales 0,801 / 0,011 / 2,1 m intactos.
Controles: 19 sintéticos del consumidor, 8 de comandos, 13 de coordinación y
2 mutantes rechazados; presupuesto persistido con 1 positivo y 12 negativos.
Los fixtures sintéticos no son capturas del motor ni aceptación del mapa.

RAM: seis misiones nuevas ABBAAB, 30 segundos de calentamiento y 120 de medida;
ratio máximo 1,10 y dispersión 5%. Se exige primero el PASS nativo607 del
paquete exacto. Seis archivos de misión validados; 12 controles de condiciones,
8 de comandos, 14 de coordinación y 3 mutantes rechazados. No se hereda ningún
resultado de Nav8 ni de E. El hashing pesado ocurre después de medir en ambos
mapas. Los snapshots privados de procesos se resumirán antes de publicar.

El control positivo añadido tras revisar confirma que una copia temporal
idéntica mantiene equivalencia: el lector normaliza saltos de línea. El
comentario deliberadamente añadido es lo que rompe la equivalencia. Fuentes
revisadas y actuales quedan registradas, sin cambiar código del consumidor.

La generación Nav12 tiene evidencia separada. El paquete no puede aceptarse
sin grid1024x1024/12m, identidad propia, cierre estricto y hashes. Locomoción,
cliente, FPS y aceptación global siguen fuera de estas pruebas.
