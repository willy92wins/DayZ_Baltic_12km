# Rumbo fijo del agua hasta la base 1.0 — 04-10-2026

Fuente: el consejo del 04-10 (astra, gemini y glm como sustituta de grok;
`reviews/2026-10-04-council-rumbo-agua/ARBITRAJE.md`) y las decisiones de Guillermo de esa tarde:

- **Lagos conectados:** se bajan junto con su río.
- **Cauces anchos:** prueba acotada de encadenado con curvas en R1.
- **Arroyos estrechos:** una sesión de comparación y se elige una opción.
- **Orden final:** Terrain Builder antes que la navmesh.

Reglas de avance:

- Cada paso tiene un criterio de salida medible y congela lo que dice.
- Un FAIL devuelve al paso responsable.
- Un resultado INCONCLUSO no congela nada.
- Cambiar algo ya congelado invalida las pruebas que dependen de ello.

Decisión vigente del 08-10: Guillermo elige conservar el fondo de 1 m y aceptar
0,95 m de calado geométrico mínimo en los corredores de 24 m, con la lancha vanilla.
Sustituye el mínimo de 1 m del 07-10; los resultados históricos de aquel umbral se
conservan. Bajos, Narva, gálibos y orden Terrain Builder → navmesh siguen sus
requisitos anteriores. Fuente: `evidence/v30-navigation-contract-2026-10-08/decision.json`.
La prueba geométrica no sustituye el consumidor ni acredita una envolvente máxima de oleaje.

## Pasos

1. **Ver el candidato v2 en motor** (`@DayZ_Baltic_PolishCandidate`, vistas de
   `evidence/v30-polish-candidate-2026-10-04/camera-poses.json`).
   - Salida: veredicto de Guillermo por vista (cabecera del Luga, rectángulos, lake_038, fosos, manchas R1/EDGE1,
     SHORE4) y BALTIC-016 confirmado o descartado con la superficie nueva.
   - Congela: la superficie (`--bed-tone land --shore-ring flowing`) si pasa.
2. **Contrato de navegación (P9).**
   - Fijar qué cauces son navegables, la embarcación de referencia (lancha vanilla; margen para barcos medianos), el
     calado y el gálibo mínimos.
   - Decidir si el canal Luga–lake_014 es navegable (hoy tiene 0,35 m de calado mínimo) o solo visual.
   - Salida: tabla firmada.
   - Congela: los requisitos de navegación.
3. **Política de niveles (BALTIC-017).**
   - Clasificar las 631 componentes del censo:
     - aisladas;
     - conectadas por diseño con su río;
     - contactos accidentales, como las charcas pegadas a un río;
     - los dos lagos grandes (4,62 y 1,96 km²).
   - Reglas:
     - no se tocan las masas por debajo de 0,3 m de agua colgada (520 de 631);
     - las aisladas con dique de más de ~1 m bajan al nivel del entorno, rehaciendo lecho y orilla;
     - las conectadas bajan junto con su río, con un perfil coherente (decisión del 04-10);
     - los dos lagos grandes se deciden aparte con Guillermo.
   - El tope de nivel del constructor solo podrá actuar entre aguas conectadas por diseño
     (`tools/terrain/build_v30_water.py:224-235`); las charcas pegadas por accidente se separan.
   - Salida: lista con el nivel nuevo de cada masa o su excepción firmada.
   - Congela: la política.
4. **Reconstruir niveles, después las orillas y pasar las puertas.**
   - Primero los niveles y luego `fit_shore_crossings_v30.py`: si los niveles cambian después, el ajuste de orillas
     se repite.
   - Salida:
     - `verify_terrain_v30` sin fallos nuevos;
     - censo sin masas colgadas de más de 0,3 m, salvo excepciones;
     - desvío de la línea de agua medido por clase y por sector, no solo global.
   - Congela: los niveles y el terreno.
5. **Cauces: prueba acotada de curvas en R1.**
   - Piezas canto con canto con los marcos reales de las curvas de la biblioteca, que nunca se han usado
     (`tools/water/fit_channel_pieces_v30.py:211` solo coge rectas), y desplazamiento lateral dentro del corredor.
   - Piezas solo donde el cauce tiene vértices mojados interiores (≈ 18 m o más). R2 y R3 vuelven a planos.
   - Salida:
     - área con doble lámina ≤ 1 % por tramo y 0 huecos en el corredor;
     - lectura del agua en motor;
     - lancha en los dos sentidos.
   - Presupuesto: 2 variantes y 1 corrección. Si no cumple, R1 también va con planos en 1.0.
   - Congela: la representación de cauces.
6. **Arroyos estrechos: una sola sesión.**
   - A altura de jugador, el candidato actual frente a una variante somera con transición de orilla. El lecho oscuro
     ya se probó y no basta.
   - Salida: se elige una opción y no se vuelve a tocar.
   - Congela: el aspecto de los arroyos.
7. **Aceptación visual y física.**
   - Bajamar, pleamar y oleaje; lancha por los cauces navegables; vehículos por las carreteras.
   - Salida: todos los casos obligatorios ejecutados, sin discontinuidades funcionales ni defectos visuales
     bloqueantes.
   - Congela: la geometría aceptada.
8. **Terrain Builder.**
   - Máscara, capas y paquete de distribución, comparados contra la geometría aceptada.
   - Salida: diferencias de alturas, agua y objetos explicadas, y paquete identificado por hash y probado en motor.
9. **Navmesh, grafo e IA sobre el paquete final.**
   - Salida: casos físicos completos en PASS, sin pendientes heredados, y aceptación de Guillermo.
   - Congela: la base 1.0.

## Fuera de 1.0

- Decoración, vegetación colocada, edificios y carreteras físicas (P10).
- Ferrocarril (P15).
- Afirmar capacidad para 80–100 jugadores (P7).
- Calado de 0,03 m.
- Malla de 3 m.
- Objetos de agua a medida.
- Re-perfilado de la costa de marea y del delta.
- Charcas remotas por debajo de 0,6 m.
- Nuevas exageraciones de relieve P12 sobre zonas ya aceptadas.

## Riesgos que hay que vigilar

- **Al bajar un lago:** la regla de separación (`build_v30_water.py:221`) puede pasar a tierra la frontera con un
  vecino y fragmentar el agua. Se revisa por cuenca, no lago a lago.
- **Al bajar un río:** el perfil hasta su tramo natural tiene que ser monótono, y las piezas y los planos se rehacen en
  ese tramo.
- **Si las curvas no quitan las costuras de R2:** se vuelve a la hipótesis de las isolíneas de profundidad antes de
  tocar más la colocación.

## Estado tras la noche del 04-10

Evidencia en `evidence/v30-v3-candidate-2026-10-04`.

1. **Paso 1, hecho.** Veredictos del v2 en motor (run d227200e): la cabecera del Luga pasa con retoques; las
   placas grises son agua colgada (BALTIC-016 se resuelve por el paso 3); en Narva, estrechar la franja somera y
   suavizar los bordes angulosos. La superficie no se congela: quedan las orillas serradas y el mar sobre tierra.
2. **Paso 2, en parte.** El canal Luga–lake_014 es navegable, con 30 m de ancho y 3,05 m de calado, el estándar de
   BALTIC-012/013. Faltan la embarcación de referencia y el gálibo del resto de los cauces.
3. **Paso 3, firmado y aplicado en el v3.**
   - Luga y los 16 lagos de la cabecera a 3,14 m, en 4,4 km planos.
   - Los dos fosos altos a 2,45 m.
   - 69 masas aisladas y 15 menores a la cota del entorno menos 5 cm.
   - 6 conectadas a la cota del entorno o de su río.
   - Los lagos 269 y 170 esperan a verse en motor.
   - Resultado: de 111 lagos colgados más de 0,3 m quedan 11.
   - El tope del constructor (`build_v30_water.py:224-235`) no se ha cambiado: el v3 aplica los niveles sobre la
     cadena con `tools/terrain/relevel_bodies_v30.py`, y el tope solo importa si se reconstruye desde el constructor.
4. **Nuevo, antes de congelar orillas (pasos 4 y 7).**
   - **Mar sobre tierra con marea** (Guillermo, captura de EDGE1). Medir en motor la altura máxima visible del mar
     con pleamar y tormenta. Después, mapear la tierra por debajo de esa altura en todo el mapa, verla en motor y
     decidir con Guillermo si esos bajos suben o pasan a ser agua de diseño. La regla «tierra ≥ 1,40 m» supone un mar
     de 1,25 m con cresta, sin medida en tormenta.
   - **Orillas serradas en costa, ríos e islotes.**
     - Causa medida en los ríos navegables: el corredor tiene 3,5 m de calado hasta el borde y está fijo en el ajuste.
     - En la costa, el ajuste no la toca.
     - Arreglo propuesto: alturas de orilla como función de la distancia a un contorno suave, con los 24 m útiles
       fijos y los bordes libres, y un ajuste de la costa a la banda de marea.

## Estado tras validar el mar (04-10, 23 h)

Evidencia en `evidence/v30-tide-swell-2026-10-04`.

- **El mar de DayZ no tiene marea.** Es un oleaje global de 12,5 s, `MaxTide/2 ± MaxWave` (hoy 0,75 ± 0,25 m), igual
  en todas las fechas y con tormenta. Se configura por mundo: un parche con `MaxTide=1.5` y `MaxWave=0.05` deja el mar
  entre 0,70 y 0,80 m.
- **Lo que Guillermo vio en EDGE1** es la tierra plana en el suelo de 1,40 m junto a la costa, que se oscurece a ratos.
  En el mapa hay 251 ha a esa cota exacta. No hay tierra por debajo de 1,25 m (20 vértices) ni agua sobre esos llanos.
- **Con el oleaje a ±0,05 m** el efecto desaparece de cerca y sigue de lejos. Así que el arreglo de fondo es de
  terreno.

Cambios en los pasos:

- El paso 4, mar sobre tierra, se une al arreglo de orillas serradas (BALTIC-007) en un solo perfil de costa y orilla.
  - Alturas en función de la distancia a un contorno suave.
  - Sin mesetas a cota fija junto al mar.
  - Bordes del corredor navegable libres, con los 24 m útiles fijos.
  - Islotes y rectángulos redondeados.
- Decisión de Guillermo, 04-10: oleaje de ±0,10 m (`MaxTide=1.5`, `MaxWave=0.1`), aplicado en `tools/terrain/derive_world_v30.py`; se verifica en el próximo paquete.
- Validación del perfil: las mismas poses y ráfagas de `tools/playtest/tide_views_v30.py`, con variación ≤ 0,02 en
  cada ráfaga.

## Perfil de costa: prueba offline (04-10, 23 h)

Evidencia en `evidence/v30-coast-profile-try-2026-10-04`. `tools/terrain/profile_coast_v30.py` da a la costa del
mar y del delta una altura lineal en la distancia a un contorno suave.

- Desfase del cruce: p50 de 1,44 a 0,00 m y p90 de 3,64 a 1,58 m.
- Giro de la línea de agua cada 12 m: p50 de 13,0° a 6,3°.
- Llanos de 1,40 m: de 69.824 a 7.543 vértices.
- Puertas idénticas al v3b.

Siguiente: la cadena v4 con este paso y el calado relajado en el ajuste de orillas, y verla en motor con las poses
de la validación del oleaje.

## Candidato v4 en motor (05-10, madrugada)

Evidencia en `evidence/v30-v4-candidate-2026-10-05`.

- **Oleaje de ±0,10 m verificado:** mar de 0,65 a 0,85 m, periodo de 12,51 s.
- **Costa sin dientes** en las vistas de cerca, con las mismas puertas que el v3b.
- **El oscurecimiento no era el llano plano:** el motor sombrea a ratos la tierra de 1,40 a 1,50 m (con ±0,25, hasta
  1,55 m). El microrrelieve la dejó dentro de esa franja.
- **Propuesta, pendiente de Guillermo:** suelo de la tierra a 1,60 m fuera de playas y taludes de costa. Cambia la regla
  «tierra ≥ 1,40 m» de este plan.

## Suelo de la tierra a 1,60 m (05-10, 4 h)

Decisión de Guillermo: la tierra sube a 1,60 m fuera de playas y taludes de costa. Sustituye la regla «tierra ≥ 1,40 m»
como objetivo de diseño. La puerta del verificador sigue en 1,40 m, porque la tierra fija (carreteras, Narva y bordes
de agua) no se mueve. El candidato v5 (`evidence/v30-v5-candidate-2026-10-05`) está construido y desplegado y falta
verlo en motor.

## v5 en motor y bordes puntiagudos (05-10, 13 h)

Evidencia en `evidence/v30-v5-candidate-2026-10-05`.

- **El suelo de 1,60 m funciona:** la tierra levantada deja de oscurecerse a ratos (10 de 13 ráfagas ≤ 0,02).
  Siguen el talud de costa de 1,35–1,55 m, una franja estrecha pegada a la playa, y el dique de Kronstadt.
- **Bordes puntiagudos que quedan:** el perfil solo edita el mar y el delta.
  - El dique de Kronstadt es plataforma fija, con escalones de 6 m y la cresta a 1,45–1,53 m.
  - Lagos, ríos, arroyos e islas conservan el ajuste v3b.
- **Nuevo (BALTIC-018):** el agua de los lagos se ve partida en bandas desde el aire; casi todos los fondos de
  lago están por debajo del mar del motor.
- **Pendiente de Guillermo:** qué va primero, el dique y las calzadas como terraplén sobre un eje suavizado, o las
  orillas e islas de los lagos con las teselas de agua regeneradas a la vez.

## Candidato v6: dique y fondo de los estanques (05-10, 15 h)

Evidencia en `evidence/v30-v6-candidate-2026-10-05`.

- **Dique de Kronstadt:** terraplén sobre el eje de la carretera (`tools/terrain/shape_causeways_v30.py`). Sale recto,
  con la cresta a 1,70 m y sin parpadeo. Era el único tramo de carretera sobre el mar.
- **Fondo de los estanques:** grava sin vegetación bajo el agua estancada (`build_surface_v30.py --bed-surface
  gravel`). El desborde de FLAT1 era un cauce de clase estanque, ancho y somero, con hierba en el fondo.
- **BALTIC-018:** las bandas del agua de los lagos vistas desde el aire siguen sin causa. Siguiente prueba: un
  lago con el fondo por encima de 0,85 m.
- **Siguiente frente:** orillas e islas de los lagos con sus teselas de agua; después los ríos.

## BALTIC-018 y candidato v7: fondo de los lagos y orillas e islas (05-10, 21 h)

Evidencia en `evidence/v30-bed-probe-2026-10-05` y `evidence/v30-v7-candidate-2026-10-05`.

- **Causa de las bandas:** el mar del motor se dibuja bajo todo lago con el fondo por debajo de 0,85 m. Con el fondo
  del Peipus a 1,0 m el agua sale uniforme; el v5 y un lago sin tocar siguen con bandas con la misma luz.
- **Decisión de Guillermo:** fondo a 1,0 m en lagos y estanques, con 0,30 m de agua al menos; los navegables
  conservan el calado hasta el contrato de navegación (paso 2).
- **Candidato v7:**
  - `tools/terrain/profile_lakes_v30.py` perfila las orillas e islas de 623 lagos y estanques sobre un contorno
    suavizado y sube los fondos;
  - ninguna clase cambia, así que las teselas de agua del v3b siguen valiendo;
  - en motor, agua uniforme e islas sin puntas.
- **La «frontera» de dos colores** era textura que tarda en cargar (BALTIC-019); se captura tras 60–90 s por pose.
- **Siguiente frente:** ríos, arroyos y navegables, con el mismo método y el calado del paso 2.

## Navegables y paso 2 (07-10, noche)

Evidencia en `evidence/baltic-018-navegables-2026-10-07` y `evidence/v30-v12-candidate-2026-10-07`.

- **Causa:** a través de los ríos navegables se veía el mar del motor, con oleaje, espuma, bordes rectos junto a la
  orilla y parches de colores a media y larga distancia. Los navegables conservaban el cauce hondo (agua a 2,10–2,55 m,
  fondo hasta −7,3 m), así que el 90,6 % de sus vértices tenía el fondo por debajo de 0,85 m.
- **Decisión de Guillermo (07-10):** «sube el fondo de los navegables a 1,0 m».
- **Cómo se aplica** (`profile_inland_v30.py --bed-floor-navigable`): cada vértice navegable, también los del corredor
  exacto de 24 m, sube a min(1,0 m, nivel − 1,0 m), así que conserva al menos 1,0 m de agua.
  - Con el agua a 2,0 m o más, el fondo queda a 1,0 m.
  - Hacia el mar, el fondo sube hasta dejar 1,0 m de agua y el mar se sigue viendo donde ese fondo queda por debajo
    de 0,85 m: los tramos con el agua bajo 1,85 m.
  - La zona de Narva no se toca.
- **Paso 2 (contrato de navegación):**
  - el calado de los navegables pasa a ser el nivel menos 1,0 m (1,0–2,17 m), y deja de ser el de 3,05 m de
    BALTIC-012/013;
  - la embarcación de referencia es la lancha vanilla, y falta probarla en motor;
  - el gálibo de los puentes no cambia.
- **Pendiente de Guillermo:** qué hacer con los tramos bajos y con Narva (14.594 vértices navegables con el mar
  debajo en la v12).
