# Perfil de costa (prueba offline) — 04-10-2026, noche

Primera pieza del arreglo conjunto de BALTIC-007 (orillas serradas) y BALTIC-016 (llanos de 1,40 m que se
oscurecen), tras la validación de `../v30-tide-swell-2026-10-04`. Herramienta nueva:
`tools/terrain/profile_coast_v30.py`. Todavía no forma parte de ninguna cadena, paquete ni vista en motor.

## Qué hace

- **Contorno suave del mar y del delta.** Parte de `sd_sea` de `tests/terrain_v30/water_v30.npz`: distancia con
  signo a un contorno vectorial, con precisión por debajo de la malla. Donde no hay `sd_sea`, usa la frontera de
  clases.
  - El campo se suaviza con una gaussiana de σ 12 m.
  - Se acota para que la orilla no se mueva más de 4 m, así un islote no desaparece.
  - Después se calcula la distancia exacta a su línea cero.
- **Perfil lineal en esa distancia:** altura = 0,75 + 0,15·d, la misma rampa del 15 % que la playa de
  `build_v30.py:441-453`, pero continua a través del contorno.
  - Los vértices que cierran una arista cruzada toman el perfil. Así la línea de agua sigue el contorno con
    cualquier nivel del oleaje.
  - Se respetan las puertas del verificador: el mar con al menos 0,10 m de calado y la playa con al menos 0,80 m.
    Ningún vértice queda entre las dos.
  - Topes de movimiento: el lecho sube como mucho 2 m y la tierra baja como mucho 1,5 m, para respetar muelles y
    escolleras.
- **Las clases siguen a las alturas**, y la máscara `beach` pasa a ser toda la tierra por debajo de 1,40 m.
- **Microrrelieve en los llanos** de 1,40 m fuera de la franja de costa: hasta 0,12 m, con ruido de semilla fija y
  longitud de onda de 36 m, que se anula en el borde de cada llano.
- **Fijos:** plataformas (carreteras), reservas, envolvente natural, corredores de 24 m, agua de estanque y río,
  vértices con plano de estanque, los 480 m de identidad de Narva y el borde del mapa.

## Resultado sobre el terreno v3b (`fac76aea`)

Salida en `E:/DayZ-Baltic-Build/v30-v4-explore/coast-try2` (terreno `3f889c85…`). Copias aquí: `report.json`,
`verify-terrain.json` y `waterline-before-after.png`.

| Medida | v3b | Perfil nuevo |
|---|---|---|
| Desfase del cruce frente al contorno suave, p50 / p90 / p99 | 1,44 / 3,64 / 5,37 m | 0,00 / 1,58 / 3,83 m |
| Aristas de costa sin cruce (de 10.382) | 2.053 | 341 |
| Giro de la línea de agua (0,75 m) cada 12 m, p50 / p90 / p95 | 13,0° / 35,0° / 47,7° | 6,3° / 25,3° / 38,1° |
| Tierra exactamente a 1,40 m | 69.824 vértices | 7.543 |

- **Puertas** (`verify_terrain_v30.py`, corte 0,51 como el paquete): idénticas al v3b. Siguen los mismos 6 calados
  en arroyos, las mismas 31 celdas de piezas y Narva distinto por diseño. Ninguna nueva.
- **Lo que queda serrado lo sujetan extremos fijos.** La primera prueba, con la playa fija
  (`v30-v4-explore/coast-try1`), dio p50 0,78 y p90 3,15 m. De sus aristas malas, 4.341 tenían un extremo en la
  playa, unas 900 en plataformas o reservas y unas 200 en corredores. Con los dos extremos libres, el cruce cae
  exacto: solo 8 de 3.461 aristas pasaban de 1 m.

## Sin verificar

- Nada visto en motor; tampoco las carreteras de la costa (fijas, pero sin pasar la puerta de carreteras sobre este
  terreno).
- Los ríos, los lagos y los islotes interiores siguen con el ajuste del v3b. Esta herramienta solo toca la costa del
  mar y del delta.
- Si el microrrelieve quita el oscurecimiento de lejos: se valida con `tools/playtest/tide_views_v30.py`.

## Siguiente

1. Cadena v4, en este orden:
   - forma del v3 (`shape-b`);
   - parche de agua y piezas;
   - ajuste de orillas con el calado relajado junto al contorno;
   - `profile_coast_v30.py`;
   - superficie;
   - paquete, con `MaxWave=0.1` ya en `derive_world_v30.py`.
2. Puertas, carreteras y auditoría de agua visible.
3. Vistas con las mismas poses y ráfagas: cociente de llanos con variación ≤ 0,02 y la costa vista de cerca.
