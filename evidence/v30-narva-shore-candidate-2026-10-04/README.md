# Candidato de Narva: referencia V29 y fosos con agua — 04-10-2026

Decisiones de Guillermo del 04-10 por la mañana: en Narva manda V29 y los fosos de la fortaleza llevan agua. Plan:
`plans/v30-narva-shore-candidate.md`. Datos completos en `summary.json`; productos en `E:/DayZ-Baltic-Build/v30-narva-shore`.

- **Fosos.** Los lagos de diseño 093, 096 y 099 salían secos porque sus vértices llevaban el nivel del río (2,45 o
  2,65 m) y el plano quedaba bajo el fondo. Ahora son lago a 2,75, 4,62 y 4,61 m: 194 vértices. No hizo falta
  excavar ni separar nada, porque las paredes ya los aíslan del río. Los huecos de la zona bajan de 2.936 a 28 m².
- **Orillas.** El ajuste usa un contorno sacado del propio río V29, suavizado con σ = 9 m, dentro de 600 m del
  puente. El núcleo fijo son plataformas, reservas y corredores; a 60 m del puente no queda nada más que fijar.
  - Desvío p50/p90: 1,63/3,78 → 0,11/1,06 m. Ahora cruzan el agua 1.514 de 1.541 aristas; antes, 778.
  - En la tierra que rodea los fosos el ajuste sube hasta 1,59 m, para contener el agua a 4,62 m.
- **Puertas.** Iguales que el candidato: carreteras PASS con los mismos máximos, sin fallos de lecho, suelo ni
  taludes. La identidad V29 alrededor del puente falla por diseño (máximo 2,66 m).
- **Paquete.** `@DayZ_Baltic_NarvaCandidate`, sin probar en el motor todavía.
- **Descartado.** Abrir Narva contra water_v3 solo quitaba el 6 % de las bandas, porque son un desfase de 6–10 m
  por una orilla entre el río V29 y water_v3.
