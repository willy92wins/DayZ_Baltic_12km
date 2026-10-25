# Lancha física en los dos brazos del Neva

**PASS de cuatro recorridos**, run `16fe4ad8-17d1-4982-aab2-4cf5abd94368`.
Pequeño Neva con conector y tronco (384,0275 m), y Gran Neva con tronco
(283,2348 m), cada ruta en ambos sentidos. Lancha vanilla vacía, propulsión y
dirección reales; ninguna escritura de pose tras el spawn.

- 2269 muestras, marcador final ALL_CASES_COMPLETE y todos los criterios
  por caso cumplidos en `verification.json`.
- Salud 600 al inicio, mínimo y final de cada caso; sin daño observado.
- Intervalo máximo 0.729 s, desplazamiento por muestra
  máximo 0.992829 m; error máximo de altura del suelo
  0.000041121 m contra el ASC congelado.
- Mundo `916948ec`, navmesh `eece8e5e`, agua `e9b52b8c`, sonda `c5414ffe`.
  Identidad completa en `identity.json` y referencia previa `../boat-reference.json`.
- Cierre ordenado acreditado, proceso retirado y lease liberado (`closure.json`).
  Dos caducidades y readopciones del mismo run propio quedan registradas; no
  se afirma posesión continua. Logs copiados y fijados por hash en
  `E:/DayZ-Baltic-Build/navmesh-v30-delta/boat-16fe4ad8` (`logs-archive.json`).

Alcance: estos recorridos y esta lancha vacía. No acredita tripulación, barcos
medianos, todos los ríos, locomoción de IA ni una envolvente temporal completa
de oleaje. El Luga requiere su propio consumidor físico.
