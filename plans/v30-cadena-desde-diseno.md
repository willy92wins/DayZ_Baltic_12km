# Cadena rehecha desde el diseño — 06-10-2026

Decisión de Guillermo (06-10): rehacer la cadena entera desde el diseño, con las líneas de ríos y arroyos suavizadas.
Motivo y medidas: `evidence/v30-v8-candidate-2026-10-06` (README, «Revisión general»).

## Objetivo y salida

- **Planta suave** en ríos y arroyos. Hoy las líneas centrales tienen 17,6 giros de más de 45° por km; con sigma
  18 m y los extremos fijos bajan a 1,3.
- **Sin perder lo validado:**
  - los navegables y sus corredores de 24 m, incluido el canal del Luga de 30 m × 3,05 m;
  - el delta y Narva;
  - la regla de niveles de la lista firmada;
  - las puertas.
- **Salida:** un candidato v9 que lleve:
  - el censo de defectos (orilla congelada por motivo y esquinas vivas por km);
  - vistas aéreas amplias, con 3 min de carga, comparadas con la v8;
  - las puertas sin fallos nuevos;
  - la aceptación de Guillermo.

## Principio: reproducir antes de cambiar

La cadena tiene 26 pasos desde el diseño hasta la v3b. Unos 12 no tienen el comando registrado, varias herramientas
llevan fijos la ruta y el hash de su entrada, y la lista firmada de niveles se armó a mano. Por eso:

1. primero se hace reproducible la cadena actual y se comprueba que, con el diseño de hoy, da los mismos productos
   (hash idéntico o diferencia explicada), paso a paso;
2. solo entonces se cambia el diseño.

Así, cualquier diferencia del v9 viene del suavizado y no de la cadena.

## Pasos

**0. Reproducir la cadena actual, sin cambiar el producto.**

- Un script único con los 26 pasos, `tools/terrain/chain_from_design.sh`. Los comandos se reconstruyen de los
  recibos y de los informes.
- Las herramientas con entradas fijas aceptan argumentos y mantienen sus valores por defecto:
  - los pasos 7–13 (rutas y hashes fijos);
  - la `R` de `v30_common.py` y de `water_common.py` (los datos de `tests/`);
  - el fichero de corredores.
- **Deriva:** `restore_narva_ponds_v30.py` y `connect_small_watercourses_v30.py` no coinciden con sus recibos. Se
  recupera del historial la versión que corrió, o se explica la diferencia.
- **Paso 13:** comprueba puntos congelados de un terreno concreto. Se mantiene en el replay y se revisa para el diseño
  nuevo.
- **Salida:** replay con hashes idénticos hasta la v3b (fac76aea) y después v5–v8, o cada diferencia explicada.

**1. Diseño suavizado.**

- Líneas de ríos y arroyos suavizadas a lo largo del cauce, con sigma 18 m y los extremos fijos para que no se
  muevan las confluencias.
- Semillas por cauce en lugar de un solo generador: así suavizar un río no cambia el ancho de los demás.
- Ids estables para los estanques (`osm_id`) en lugar de índices.
- El efecto de las semillas se mide aparte del suavizado: un replay con semillas por cauce y sin suavizar.

**2. Cadena con el diseño nuevo.**

- Los 26 pasos con las mismas reglas.
- **Lista firmada:** se recalcula con su regla (p25 del anillo − 0,05 m, suelo 1,35 m; hoy la cumplen 82 de 90) y
  las diferencias se le presentan a Guillermo antes de seguir.
- La cabeza del Luga, el canal Luga–lake_014 y Narva, con los mismos parámetros.

**3. Final.**

- La pasada única `profile_inland_v30.py` sustituye a lagos + ríos: contactos y reserva incluidos.
- La costa (v5) y el dique (v6).
- La superficie con `--bed-tone depth-all`.
- El paquete con OutsideTerrain y síntesis (`-OutsideSynth`).

**4. Validación.**

- Puertas, censo de defectos y auditoría del agua visible.
- Vistas aéreas amplias, con 3 min de carga, frente a la v8.
- Las pruebas de lancha (BALTIC-012/013) si el corredor del Luga cambia.

## Reparto

- **GLM en el GX10** (4 lanes como máximo): una herramienta por lane para hacerla parametrizable, con encargos
  precisos y firmas `path:line`. Yo reviso cada una y comparo por hash.
- **Yo:** la reconstrucción de los comandos, el replay, el diseño, la integración y el motor.

## Riesgos

- **Coste:** varias sesiones. La mayor parte es el paso 0.
- **Pasos hechos a mano:** la lista firmada puede no reproducirse exacta; se presentan las diferencias.
- **Motor:** vistas de todo el mapa, unos 30–40 min por candidato.
- **Cliente:** hacer una pose de calentamiento antes de ir al este (BALTIC-001); hoy se ha caído dos veces al recibir
  la cámara tras un teletransporte.

## Bordes del mapa (Guillermo, 06-10, 3 h)

- **Los bordes son de tierra, como en Chernarus.** OutsideTerrain con síntesis: en la prueba v8c, fuera del borde de
  tierra se ve tierra con textura. Donde un lago toca el borde (lago 106) salen bandas sobre el agua y tierra al otro
  lado (`evidence/v30-v8-candidate-2026-10-06/border-trial/l106-v8c-synth-bands.jpg`), así que el agua interior no
  puede tocar el borde.
- **Regla del diseño nuevo:** el agua interior (lagos, estanques, ríos, arroyos) acaba al menos a unos 60 m del borde.
  - Los tres lagos grandes que lo tocan se recortan con esa franja de tierra: 288 (Peipus, 4,62 km², borde oeste),
    106 (3,37 km², noreste) y 202 (1,96 km², sureste); pierden un 5–6 % cada uno.
  - Los diez estanques diminutos que tocan el borde (menos de 0,04 km² cada uno) se quitan.
  - Los siete cursos que salen del mapa terminan antes del borde.
- **El mar llega al borde** (norte y oeste), como las costas de Chernarus.
- Con esto la franja de dos vértices del borde de los lagos de la v7d (fondo hondo) deja de hacer falta.

## Avance del paso 0 (06-10)

- Pasos 1–3 (auditoría V29, diseño navegable, diseño de agua): reproducidos byte a byte en
  `E:/DayZ-Baltic-Build/v30-replay` (los cinco productos y los dos informes).
- Pasos 4–5 (agua V30, terreno V30): reproducidos byte a byte (water_v30 96d4a7de, terrain_v30 365c2a94, ASC 362550d1).
- Herramientas parametrizadas (GLM, lanes P1 y P2, revisadas): delta, acabado de orillas, estanques de Narva, cursos
  pequeños, deduplicado, márgenes de oleaje y cruces de orilla; más `--design` en el arreglo del Luga. Con los
  valores por defecto se comportan igual; el replay de los pasos 6–13 lo comprueba.
- Las dos herramientas con deriva (estanques de Narva, cursos pequeños) solo tienen un commit, y su hash no es el de
  los recibos ni con CRLF: la versión que corrió no se guardó. El replay dirá si cambia el producto.

## Avance de los pasos 1–4 (06-10, 5:45)

- **Paso 1, diseño suavizado:** hecho (`E:/DayZ-Baltic-Build/v30-redesign/design`; giros de más de 45° por km de 17,64
  a 1,2).
- **Paso 2, cadena:** hecha (`evidence/v30-v9-candidate-2026-10-06`).
  - La regla del borde quita 18 cuerpos: los 10 que tocan el borde y 8 que entran en la franja sin tocarlo; estos 8,
    pendientes de Guillermo.
  - El paso 13 deja fuera 7 de los 13 puntos medidos en motor, que el suavizado movió.
  - La lista de niveles, recalculada con su regla (`tools/water/derive_signed_levels_v30.py`): 88 iguales, 3
    desaparecen con el borde, connected_136 pasa de 1,43 a 1,35 m y la regla añade review_181. **Desviación del plan:**
    no se paró aquí; la cadena siguió con esa lista y las diferencias se presentan ahora, con el candidato hecho.
    Cambiarlas repite los pasos 21 en adelante (unos 20 min).
- **Paso 3, final:** hecho; candidato v9, mundo b4f68bf1 + agua a1abc83f, desplegado como `@DayZ_Baltic_V9Candidate`.
- **Paso 4, validación:** puertas iguales o mejores que la v8; el pasillo del Luga no cambia (las pruebas de lancha
  siguen valiendo); censo de defectos y vistas en motor frente a v8, v8c y v7d (run 6d421b36). Falta la aceptación de
  Guillermo.

## Avance tras la v9: v10 y v10b (06-10, 17 h)

- **Decisiones de Guillermo sobre la v9**, aplicadas en la v10 (`evidence/v30-v10-candidate-2026-10-06`):
  connected_136 a 1,35 m y review_181 a 1,44 m; lake_047 y lake_107 enteros; lagos, estanques y cuerpos de río
  suavizados en el diseño (σ 12 m, ≤ 4 m, área conservada); orilla de agua muy baja hasta su nivel + 0,05 m;
  cubierta del suelo suavizada.
- **Métrica independiente** de la línea de agua visible (`tools/water/audit_waterline_v30.py`), con el criterio
  fijado antes de construir: la v10 lo pasa frente a la v9.
- **Segunda y última ronda:** en motor quedaban en escalera un lago y un estanque del RIVER_80. Causa: el
  `sd_shape` del paso 22 (re-suavizado sin conservar el área y con el signo de la clase). La v10b lee el `sd` del
  paso 20: la línea de agua visible queda al nivel del diseño, con las mismas puertas.
- **Desviación del plan:** la cadena de la v10 se paró dos veces (lista de niveles y orillas de agua baja) y se
  reanudó tras cada arreglo; la v10b reutiliza los pasos previos de la v10 y su agua.
- Falta la aceptación de Guillermo.

## Avance tras la v10b: v11 (07-10, madrugada)

- **Aceptado por Guillermo (06-10):** la v10b como base de las orillas y su lista de niveles.
- **Pedido:** redondear el final de los ríos en el borde y más profundidad en ríos y lagos. La profundidad se
  decidió en tres rondas con medidas: la primera estimación (ríos de 1 m con 0,2–0,5 m de tierra) no se cumplía;
  Guillermo eligió la variante C (`evidence/v30-v11-candidate-2026-10-06/README.md`).
- **Candidato v11:** la cadena entera desde el paso 4 con las dos opciones nuevas; línea de agua, puertas y
  carreteras como la v10b. **Desviación:** la primera construcción dejaba el final del Гриб cuadrado por el surco
  central; se arregló y se reconstruyó (la primera queda en `v30-v11-pretrim`).
- Falta verla en motor: la pantalla estaba apagada.
