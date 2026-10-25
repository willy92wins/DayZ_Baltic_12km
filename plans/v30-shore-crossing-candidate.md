# Candidato de orillas sobre el contorno de diseño, desembocaduras a la marea baja y R1 con solape

Sesión nocturna del 04-10. Guillermo aprobó a las 03:30: candidato aparte con prueba en motor y capturas
antes/después en las mismas vistas, sin tocar lo desplegado ni el canónico; búsqueda propia de lo inundado;
DayZ agrupado tras el trabajo offline; R1 con solape y gate offline, sin adoptar. Continúa BALTIC-007, -015 y -016.

## Hechos de partida

- La orilla visible de un plano pond es el cruce del terreno nativo (6 m, diagonal NO-SE) con el plano. En d5dadae8
  la tierra que toca el agua queda ~0,45 m por encima y el primer vértice mojado ~0,28 m por debajo: el cruce cae
  en una fracción fija de cada arista y dibuja la malla (escalera).
- El mar del motor es de marea, 0,50–1,00 m (`temporal-v3-result.json`, `playview-engine-v1.log`); 0,54 era una
  lectura cerca de la bajamar. Por eso la tierra seca se mantiene ≥ 1,40 m y el agua de marea ≤ 0,45 m.
- Los tramos navegables a nivel del mar (≤ 0,80 m) no tienen plano y enseñan el mar: el primer plano aguas arriba
  queda 0,30 m sobre la bajamar. Son 3 componentes (desembocadura del Narva, borde del delta del Neva y EDGE1/2).

## Cadena del candidato (`E:/DayZ-Baltic-Build/v30-shore-sdf`)

1. `tools/water/profile_river_mouths_v30.py`: rampa geodésica de nivel en esas 3 componentes, de 0,50 m en el lado
   del mar a 0,80 m en el primer plano; corte de mar del candidato 0,51 m (planos desde 0,50–0,525 m).
2. Agua: solo se regeneran las teselas de 48 m cuyas celdas cambian; el resto del agua deduplicada queda idéntico.
3. `tools/water/fit_channel_pieces_v30.py --overlap-all --no-pad --sea-cut 0.51`: R1 con solape en todo el tramo
   (gate offline: 0 celdas sin cubrir, 0 huecos previstos a alturas de juego), sin banco de calibración.
4. `tools/terrain/fit_shore_crossings_v30.py`: por cada arista nativa mojado-seco de agua pond, el terreno interpolado
   en el cruce del contorno de diseño (sd/sd_sea de `tests/terrain_v30/water_v30.npz`) debe valer el agua visible
   (plano, o lámina de la pieza vanilla en los tramos del piloto). Mínimos cuadrados acotados y dispersos, cerca de las
   alturas actuales. Las cotas mantienen todos los gates; quedan fijos los corredores de 24 m, plataformas, reservas,
   Narva (620 m), el entorno natural, el borde y la playa. La tierra bajo una pieza vanilla sube por encima de su
   lámina (adiós a las esquinas que asoman). La costa de marea no se toca.
5. Gates: `verify_terrain_v30`, carreteras, muestras secas congeladas, 23 corredores, lectura offline de cauces,
   auditoría de agua visible frente al diseño (antes y después) y el desvío de la línea de agua por clase.
6. Superficie, paquete `@DayZ_Baltic_ShoreSdfCandidate` y prueba en motor: lectura de cauces, capturas en las
   19 vistas del piloto más primeros planos de orillas, desembocaduras e inundaciones encontradas.

## Límites

- Sin navmesh nueva ni IA física: el candidato no se adopta esta noche.
- Navegables: los corredores protegidos limitan cuánto se puede mover su orilla.
- La auditoría de agua visible la escribe GLM (otra familia) como verificador independiente; se revisa antes de usarla.

## Resultado (04-10, 05:40)

Hecho de punta a punta; evidencia en `evidence/v30-shore-crossing-candidate-2026-10-04`. Terreno e144ad1a, mundo 0ab61bab, agua 6ebc62cb y mod
`@DayZ_Baltic_ShoreSdfCandidate`. Puertas offline: sin fallos fuera de R2/R3 (las de dentro ya venían del ajuste de
cauces), carreteras PASS, muestras secas 463/463, puntos someros idénticos y corredores exactos. En motor:
lectura de cauces PASS sin huecos; las orillas navegables pierden los escalones de 90°; en R2 se ven costuras
entre piezas y en R3 un zigzag de anchura uniforme (el cruce del terreno sobre la malla de 6 m). Auditoría de agua
visible (BALTIC-016): nada inundado tierra adentro; fuera del contorno solo costa de marea, Narva protegido, delta
ensanchado a propósito (BALTIC-013) y astillas de orilla, que el candidato reduce un 27 %. Decisiones abiertas:
calado mínimo cerca del contorno, surcos de ríos estrechos y anchura visible de los arroyos con piezas. No se adopta
(sin navmesh ni IA).

Tras el aviso de merge (06:10–07:00): variantes de un solo cambio y diagnóstico de cauces, en la evidencia
§Variantes exploratorias. El surco libre lleva los arroyos al contorno (p90 1,52 → 0,61 m) con las mismas puertas;
probado en motor (run 16aca2e1), quita la escalera pero deja un agua casi transparente. Decide Guillermo.
