# Orillas de Narva sobre el contorno de diseño (BALTIC-016, BALTIC-007)

Borrador del 04-10 por la mañana. Guillermo aprobó tocar la zona protegida de Narva («sí dale»). Falta su elección del
núcleo del puente que se conserva (§Decisión pendiente).

## Hechos de partida

- **Protección actual.** A menos de 480 m del centro del puente (2417, 6890) las alturas son idénticas a V29, con una
  transición hasta 600 m (`tools/terrain/build_v30.py`, paso 6). La herramienta de orillas fija además 620 m y la
  máscara `narva` (20.109 vértices).
- **Agua visible fuera del diseño.** La auditoría encuentra 1,22 ha en la zona, en 110 manchas.
  - Bandas en las orillas del río: las de cerca del puente (40–250 m), sobre todo por planos; las de aguas abajo,
    hacia R1 y EDGE, por mar.
  - 2.924 m² de lagos de diseño secos junto a (2100, 6650). Allí el terreno V29 tiene río navegable o tierra, con
    niveles de 2,45 a 4,62 m.
- **Sin campo de distancia.** El campo de distancia al contorno (`sd` de `tests/terrain_v30/water_v30.npz`) está
  vacío en la zona: 7.654 vértices mojados sin valor. La herramienta de orillas no puede ajustar nada allí sin él.
- **Qué hay en la zona.** 416 vértices de plataforma, 134 de reserva, corredores de 24 m, 7.774 de navegable,
  354 de lago y 75 de laguna.

## Cadena propuesta (candidato aparte, sin tocar lo desplegado)

1. **Distancia al contorno en la zona.** Se calcula desde los mismos polígonos que usa la auditoría (water_v3
   navegable y río, y lagos de contour-v2), solo dentro de 620 m, y se une al campo existente.
2. **Ajuste de orillas en la zona.** Mismas cotas y puertas que el candidato. La protección de Narva se sustituye
   por el núcleo del puente: plataformas, reservas, corredores y el radio elegido alrededor del puente.
3. **Puertas.**
   - Las del candidato.
   - La identidad V29 a 480 m se sustituye por identidad V29 del núcleo.
   - Carreteras, como siempre.
   - Auditoría de agua visible en la zona, antes y después.
4. **Lagos secos.** Se informan uno a uno (nivel de diseño frente a clase y nivel del terreno). No se tocan sin una
   decisión aparte: excavarlos cambia el agua y quizá la navegación.
5. **Paquete y motor.** Sobre el candidato elegido. Vistas FLOOD0, FLOOD1, R1, EDGE1 y el puente, en las mismas
   poses, frente al candidato.

## Decisión pendiente

Núcleo del puente que queda idéntico a V29:
- (a) solo plataformas y reservas;
- (b) radio de 60 m alrededor del puente;
- (c) los 480 m actuales, ajustando solo fuera, que deja casi todas las bandas como están.

## Resultado (04-10, mañana)

Guillermo decidió que en Narva manda V29 y que los fosos llevan agua. Al abrir Narva contra water_v3 solo se
quitaba el 6 % de las bandas: son un desfase de 6–10 m por una orilla entre el río V29 y water_v3. Candidato
construido: fosos como lagos a su nivel y orillas ajustadas al contorno V29 suavizado (desvío de la zona
1,63/3,78 → 0,11/1,06 m). Mismas puertas que el candidato, salvo la identidad V29 (2,66 m, por diseño).
Mod `@DayZ_Baltic_NarvaCandidate`, sin ver en el motor. Evidencia en
`evidence/v30-narva-shore-candidate-2026-10-04`.

## Límites

Sin navmesh ni IA. La costa de marea y el mar no se reperfilan. Los lagos secos solo se informan.
