# Consejo: rumbo del agua de DayZ Baltic 12km (04-10-2026)

## Tarea (una frase)

Da una segunda opinión independiente y con evidencia sobre el rumbo del sistema de agua y orillas del terreno DayZ
Baltic 12km, y propone una secuencia fija de trabajo hasta la base 1.0.

## Rol y criterio de éxito

Eres un consejero de solo lectura, de una familia de modelos distinta a la del orquestador (Claude). El dueño del
proyecto, Guillermo, quiere fijar un rumbo y dejar de dar vueltas. Tu dictamen sirve si:

1. critica primero el encuadre (Q0);
2. responde Q1–Q5 con una recomendación clara y su porqué;
3. cita cada hecho que use con `ruta:línea` o con el fichero;
4. marca como [SUPUESTO] lo que no pueda verificar;
5. dice dónde discrepa del orquestador.

Discrepar es bienvenido: el objetivo es elegir bien, no ratificar lo propuesto.

## Contexto mínimo

- **Qué es.** Un mapa DayZ de 12,288 × 12,288 km (2048² vértices a 6 m) de la región báltica (Narva, el Luga, San
  Petersburgo), generado desde datos GIS. Terreno «V30» con relieve rediseñado; todavía sin edificios ni vegetación
  colocada, por decisión de producto (`product-spec.md`, fila P10).
- **Cómo dibuja el agua el motor** (medido en este proyecto):
  - Mar: un plano horizontal infinito con marea de 0,50 a 1,00 m.
  - Agua interior: un plano horizontal por celda de 6 m, a la media de los niveles de sus esquinas mojadas,
    redondeada a 25 mm (`tools/terrain/v30_common.py:88`). La orilla visible es la línea donde el terreno, triangulado
    por la diagonal NO-SE, corta ese plano.
  - Piezas vanilla de cauce de Chernarus (`river_24_*`, `stream_14_*`): láminas inclinadas con faldones en los
    extremos. Hoy se usan en tres tramos piloto: R1 (río ancho, Narva), R2 y R3 (arroyos).
- **Puertas offline del terreno** (`tools/terrain/verify_terrain_v30.py:31`):
  - calado ≥ 0,10 m;
  - tierra a ≤ 8,5 m del agua al menos 0,05 m sobre el nivel del agua más cercana;
  - tierra ≥ 1,40 m;
  - pendientes de tierra ≤ 35°;
  - en cada celda con plano, esquinas mojadas por debajo del plano y esquinas de tierra por encima.

## Hechos verificados (con su fuente)

- **H1, orillas (BALTIC-007).** Un candidato ajusta el terreno para que cruce el agua justo en el contorno de diseño.
  El desvío p50/p90 de la línea de agua pasa de 0,517/2,441 a 0,082/1,591 m, medido sobre todas las aristas
  agua-tierra del mapa con signo coherente (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md`). En motor
  desaparecen los escalones de 90° de las orillas navegables.
- **H2, arroyos estrechos.** Los cauces de 1–2 vértices de ancho se ven en escalera. Con «surco libre» (calado
  mínimo 0,10 m) la escalera desaparece, pero en motor el agua se ve casi transparente. Con calado ≥ 0,25 m solo
  queda el 26–30 % de la mejora (`bugs.md`, fila BALTIC-007, línea 19).
- **H3, piezas vanilla (BALTIC-015).** En motor la lectura es PASS, sin huecos, pero se ven costuras en R2. Área
  de cauce con dos láminas o más, medida hoy (`evidence/v30-polish-candidate-2026-10-04/joints/joints.json`, bloque
  `groups`):
  - Chernarus: 0,33 % en ríos (660 piezas) y 0,49 % en arroyos (389 piezas);
  - nuestros tramos: 58 % en R1, 73 % en R2 y 75 % en R3.
  - Chernarus encadena canto con canto (mediana −0,044 m en la junta) y gira dentro de piezas curvas (desvío de
    rumbo en la junta, p50 0,44°).
  - Nosotros solapamos un par de faldones (`tools/water/fit_channel_pieces_v30.py:263`, con `overlap_from=None` en
    R2 y R3, líneas 56 y 58) y giramos en las juntas (p50 8,8° en R2 y 11,4° en R3).
- **H4, agua colgada (BALTIC-017).** De 631 masas de agua estancada, 111 lagos (7,0 km²) tienen el nivel más de
  0,3 m por encima de la mediana del terreno situado a 12–36 m de su borde, y 190 masas tienen diques de más de
  0,5 m (`evidence/v30-polish-candidate-2026-10-04/census/census.json`).
  - Los niveles de lago salen de las superficies V29 `contour-v2` (`tools/terrain/build_v30_water.py:46-51`).
  - El constructor sube toda la tierra a ≤ 8,5 m del agua hasta nivel + 0,35 m (`tools/terrain/build_v30.py:40` y
    `:449-450`).
  - Caso típico, la cabecera del Luga: agua a ~4,15 m sobre un terreno a ~3,0 m, con diques de ~1,4 m.
- **H5, escalera por tope de nivel.** En el agua que fluye, el constructor rebaja el nivel hasta 0,25 m por cada
  6 m hacia cualquier vecino mojado más bajo (`tools/terrain/build_v30_water.py:224`). Una charca pegada a un río
  lo arrastra en escalera: en el Luga, 141 vértices bajaron hasta 2,10 m
  (`evidence/v30-polish-candidate-2026-10-04/reports/polish-report.json`).
- **H6, agua visible (BALTIC-016).** Fuera del contorno de diseño, en bajamar: borde oeste 5,0 ha (artefacto de
  máscara), costa 3,8 ha, Narva protegido 1,2 ha, delta 1,0 ha y astillas de orilla 2,7 ha; tierra adentro, nada.
  Las manchas oscuras que vio Guillermo son probablemente fondos de charca pintados casi negros, visibles cuando la
  lámina no se dibuja. El arreglo está construido en el candidato v2, sin ver en motor (`bugs.md`, línea 28).
- **H7, candidato v2 «pulido».** Desplegado y sin ver en motor
  (`evidence/v30-polish-candidate-2026-10-04/README.md`).
- **H8, producto** (`product-spec.md`):
  - P2: conservar agua y ríos;
  - P9: ríos navegables con lancha vanilla;
  - P10: terreno y navegación antes del mapeado;
  - P12: relieve selectivo, que permite exagerar alturas de zonas concretas;
  - P14: contorno suave y bajos sin agua indeseada;
  - línea 23: «No confundir ese candidato con una decisión de cerrar todos los niveles de agua».
- **H9, estado.** La base 1.0 no está aceptada. Faltan navmesh, pruebas físicas e IA sobre el candidato que se
  acepte, y Terrain Builder cuando se congele la base (`HANDOFF.md`, bloque LIVE-STATE, campo `next`).

## Interpretaciones del orquestador (rebatibles)

- **I1.** El agua colgada nace de usar niveles V29 sobre el relieve V30 rediseñado (P12): los niveles no se
  volvieron a derivar del terreno nuevo. [SUPUESTO: no se ha comparado lago a lago con el terreno V29.]
- **I2. Rumbo que propone el orquestador.**
  - (a) Piezas vanilla solo en ríos anchos, encadenadas como Chernarus: canto con canto, curvas con piezas curvas y
    desplazamiento lateral permitido. Los arroyos estrechos (R2/R3) vuelven a planos.
  - (b) Agua colgada: derivar los niveles de lago del terreno natural (bajar el agua al nivel del entorno) en vez
    de levantar diques, empezando por las zonas visibles.
  - (c) Orden: ver v2 en motor → decidir (a) y (b) → reconstruir → navmesh e IA → congelar → Terrain Builder.
- **I3.** Para arroyos estrechos sobre la malla de 6 m no hay buena solución con planos: o escalera, o agua casi
  transparente.

## Preguntas

- **Q0 (primero, obligatoria).** ¿Qué puede estar mal en el encuadre del problema, en los hechos elegidos o en las
  opciones? Puedes aceptar un hecho y rechazar la inferencia.
- **Q1, agua colgada.** ¿Volver a derivar los niveles, rebajar el terreno, aceptar los diques o una mezcla? ¿Con qué
  criterio por masa de agua y con qué riesgos (ríos conectados, navegabilidad P9, puertas)?
- **Q2, cauces.** ¿Piezas vanilla solo en ríos anchos, encadenadas como Chernarus? ¿Cómo resolver las curvas sin
  solapes ni huecos? ¿Con qué umbral de anchura?
- **Q3, arroyos estrechos.** ¿Hay una tercera vía además de la escalera o el agua transparente (otra resolución,
  texturas, objetos…)?
- **Q4, rumbo fijo.** Secuencia numerada de 5 a 8 pasos hasta la base 1.0. Cada paso con su criterio de salida
  medible y lo que se congela al terminarlo.
- **Q5.** ¿Qué dejarías fuera de 1.0, y por qué?

## Fuentes obligatorias (solo lectura; léelas antes de opinar)

Raíz del repo: `P:\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290`. Es la misma carpeta que
`C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290`.
Rutas relativas a esa raíz:

1. `product-spec.md`
2. `evidence/v30-polish-candidate-2026-10-04/README.md`
3. `evidence/v30-shore-crossing-candidate-2026-10-04/README.md`
4. `bugs.md`: solo las filas de la tabla, líneas 19 (BALTIC-007) y 27–29 (BALTIC-015, -016 y -017)
5. `HANDOFF.md`: el bloque LIVE-STATE, líneas 3–23
6. `tools/water/fit_channel_pieces_v30.py`: líneas 1–60 y 240–300
7. `tools/terrain/build_v30_water.py`: líneas 40–60 y 205–235
8. `evidence/v30-polish-candidate-2026-10-04/census/census.json` y
   `evidence/v30-polish-candidate-2026-10-04/joints/joints.json` (solo el bloque `groups`)

Puedes abrir otros ficheros del repo para comprobar algo concreto; cita lo que uses. Mods hermanos con el mismo
problema: ninguno (censo de `P:\`, 486 entradas: las únicas carpetas de terreno son de este proyecto).

## Fronteras

- Solo lectura: no escribas, no muevas ni borres nada, no ejecutes scripts del repo, no lances DayZ ni uses la red.
- Lee los ficheros con tu herramienta de lectura, no con comandos de shell.
- No leas fuera del repo, salvo este brief.
- Entorno: Windows. Hay rutas con espacios bajo OneDrive; si tu herramienta parte las rutas por espacios, usa la
  forma `P:\`. Los ficheros están en UTF-8.
- Tiempo orientativo: unos 30 minutos. No hace falta leer cada fichero entero si bastan las líneas indicadas.

## Entregable (formato exacto)

Tu respuesta final es el dictamen, en Markdown y en español, con estas secciones en este orden:

```
## 0. Crítica del encuadre
## 1. Agua colgada
## 2. Cauces y piezas
## 3. Arroyos estrechos
## 4. Rumbo fijo
## 5. Fuera de 1.0
## 6. Discrepancias con el orquestador
## LO_NO_VERIFICADO
```

- La última línea es exactamente `FIN-DICTAMEN`.
- Cada hecho que uses lleva su `ruta:línea` o el nombre del fichero. Lo que no tenga cita va a LO_NO_VERIFICADO o se
  marca [SUPUESTO].
- Longitud orientativa: 1.200–2.500 palabras.

## Receptor

Claude, el orquestador, recibe cada dictamen por separado y sin mostrar los de los demás. Re-verifica las citas que
sostienen cada recomendación y se los presenta a Guillermo, con el disenso tal cual.
