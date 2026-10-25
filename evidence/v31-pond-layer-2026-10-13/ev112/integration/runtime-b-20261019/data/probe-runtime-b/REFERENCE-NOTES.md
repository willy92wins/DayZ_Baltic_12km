# Referencias históricas y alturas nuevas

En `probe-runtime-b/points.json`, `probe-runtime-b/shores-points.json` y `water-temporal-runtime-b/points.json`, `d_terrain_minus_water_m` conserva el valor derivado del terreno C al seleccionar los puntos. No representa la separación nueva del terreno B. En el punto global3836, el campo histórico es−0,1439m; el `ground` nuevo es0,446000003m y el nivel0,75m, de modo que su diferencia nueva sería−0,304m redondeada.

`ground` sí se recalculó sobre B. Los IDs, coordenadas y expectativas se conservaron. Los consumidores de aceptación no leen `d_terrain_minus_water_m`; esta anotación aclara la procedencia sin modificar datos fijados por hash, puntos, umbrales ni veredictos. R2 menor2, cerrado por anotación explícita.
