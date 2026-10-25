# Arbitraje — consejo «rumbo del agua» (04-10-2026)

- **Corrida.** Manifiesto en `MANIFEST.md`; brief_sha 02e48c1b. Tipo COMPARABLE, con glm como sustituta y sin arnés.
- **Árbitro.** Claude, el orquestador, que no es lane.
- **Dictámenes.** `lanes/astra/out.md`, `lanes/gemini/out.md` y `lanes/glm/content.md`, sin editar.
- **Verificación.** Cada fila marcada ORQ lleva su cita re-leída por el árbitro en esta sesión.

## Lanes

| lane | modelo × ruta | estado | min | tokens | veredicto corto |
|---|---|---|---|---|---|
| astra | gpt-6-astra (xhigh) × `codex exec -s read-only` (codex-cli 0.160.0) | COMPLETE | 6,7 | 105.738 | Mezcla por sistemas conectados; las curvas nunca se probaron; TB antes que navmesh |
| gemini | gemini-3.1-pro-high × `agy` 1.2.16 | COMPLETE | 2,7 | 94.271 | Los aislados bajan, los conectados se quedan; piezas solo por encima de 12 m; arroyos a planos con lecho oscuro |
| glm | GLM-5.3-Flash-EXL3 × API del GX10 (**SUSTITUTA** de Grok, sin herramientas, fuentes en línea) | COMPLETE | 6,7 | 37.512 | Clases por masa; niveles antes que orillas y cauces; piezas solo con vértices mojados interiores |

- Las tres lanes entregaron completas: `EXIT` con RC=0, contrato completo y `FIN-DICTAMEN`.
- Ninguna escribió en el repo: `git status` solo muestra el arreglo del árbitro en `compare_channel_joints_v30.py`.
- Grok queda fuera: no tiene celda viva hoy (tabla C3b del manifiesto).

## Correcciones al brief que salen del consejo

| # | Corrección | Lane | Verificación |
|---|---|---|---|
| 1 | El desvío de rumbo en junta de H3 venía de un fallo de la herramienta: `compare_channel_joints_v30.py:165` comparaba la salida de A con la salida de B, no con su entrada. Ya corregido. Chernarus queda en p50 0,13° en ríos y 0,27° en arroyos, con 647 y 325 juntas: igual que la calibración de `library.json`. Nuestros R2 y R3 no cambian (8,8° y 11,4°, todo rectas). El área con doble lámina tampoco cambia. | astra | ORQ: `vanilla_channel_pieces.py:101-103`; nueva medida en `joints-r2` |
| 2 | El encadenado con curvas nunca se ha probado. El colocador solo coge rectas (`fit_channel_pieces_v30.py:211`, filtro `turn_deg == 0`), aunque la cabecera (línea 9) hable de curvas. El piloto lo documenta: «Las curvas quedan en la biblioteca sin usar». | astra | ORQ: `fit_channel_pieces_v30.py:211`; `evidence/v30-vanilla-channel-pilot-2026-10-04/README.md:127-130` |
| 3 | El censo mide contra el terreno final del candidato, no contra un terreno natural anterior. Además, el 94 % de los 7,0 km² colgados son los dos lagos mayores (4,62 + 1,96 km²). | astra | ORQ: `census.json`, `top` |
| 4 | 520 de las 631 masas (82 %) quedan por debajo de 0,3 m de agua colgada. | glm | ORQ: `census.json`, `perched_m_histogram` |
| 5 | El tope de 0,25 m rebaja el agua que fluye hacia cualquier vecino mojado más bajo, sin comprobar que haya conexión de diseño. Es la causa general de la escalera del Luga. | astra | ORQ: `build_v30_water.py:224-235` |
| 6 | La regla de orillas a +0,35 m no toca las orillas ya perfiladas. | astra | ORQ: `build_v30.py:449` (`~shaped`) |
| 7 | El canal Luga–lake_014 tiene un calado mínimo de 0,35 m, así que no acredita P9. | astra | ORQ: `polish-report.json`, `depth_m_min_max` 0,35–2,95 |
| 8 | El «26–30 %» de H2 mide el desvío de la línea de agua, no la calidad visual. | glm | ORQ: `bugs.md:19` |
| 9 | Las puertas no equivalen a aceptación: el comprobador de tramos ve un vértice mojado sin pieza y otro a −0,29 m bajo la lámina. | astra | ORQ: `reports/channel-reaches.json` |

## Hallazgos rechazados

- **«Lecho oscuro bajo el surco libre» como tercera vía** (gemini §3; glm §3.1, que lo marcó [SUPUESTO]). Ya se probó
  sin saberlo. El paquete del surco (run 16aca2e1) usaba la superficie de `v30-shore-sdf`, sin `bed_tone`, así que
  todos los lechos eran oscuros por defecto (`build_surface_v30.py:149`). Con 0,10 m de agua se veía «casi
  transparente y en primer plano parece seco» (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md:168-169`).
  **RECHAZADO-FALSO.**
- **«El v2 ya oscurece el lecho»** (gemini §0). Es al revés: el v2 aclara el fondo del agua estancada al tono del
  terreno (`README.md:30` del pulido). **RECHAZADO-FALSO.**

## Convergencias

| Tema | astra | gemini | glm | Arbitraje |
|---|---|---|---|---|
| Solape sistemático de faldones | abandonar | abandonar | abandonar | ACEPTADO, 3/3, con evidencia H3 |
| Piezas en R2/R3 para 1.0 | no: planos por defecto | no | no | ACEPTADO |
| Umbral para usar piezas | ≥ 18 m mojados y una fila de vértices interiores | sin piezas por debajo de 12 m | vértices mojados interiores (≥ 3 de ancho) | astra y glm coinciden (~18 m ≈ 3 vértices) |
| Curvas | encadenar con los marcos reales de la biblioteca, en prueba acotada | curvas de 10° y 30° | curvas y deriva lateral de ±3,5 m | ACEPTADO: probarlo, porque nunca se ha hecho (corrección 2) |
| Agua colgada | por sistema conectado; diques solo como excepciones firmadas | los aislados bajan, los conectados se quedan | por clases; el 82 % no se toca; los dos grandes aparte | ACEPTADO: no bajar en bloque, sino clasificar |
| Primer paso | ver v2 | ver v2 | ver v2 | ACEPTADO |
| Niveles antes que orillas y cauces | sí (paso 2 antes que el 4) | implícito | explícito | ACEPTADO: el ajuste de orillas se repite si los niveles cambian después |
| Fuera de 1.0 | resolución global, objetos a medida, fidelidad hidrológica absoluta, decoración, cifra de 80–100 jugadores | decoración, ferrocarril, carga | calado 0,03 m, costa y delta, charcas remotas, ferrocarril, carga, nuevas exageraciones P12 | ACEPTADO |

## Disenso (literal)

### Lagos conectados, como la cabecera del Luga

- **gemini:** «Para lagos conectados a cauces o ríos (ejemplo crítico: cabecera del Luga): Bajar el nivel del agua es
  inaceptable. […] En estos ecosistemas, se debe aceptar el levantamiento hídrico y optar por rediseñar el terreno
  perimetral: expandir los taludes del dique a mucha mayor distancia».
- **astra:** «Lago conectado a río o canal | Resolver conjuntamente nivel del lago, entrada, salida y perfil
  longitudinal; nunca bajar el lago aisladamente.»
- **glm:** «Rebajar el agua (nivel := mediana del anillo + margen pequeño) en las masas *colgadas* con dique > ~1,0 m
  o adyacentes a cauces navegables (P9)».

### Orden entre Terrain Builder y navmesh

- **astra:** «6. Cerrar Terrain Builder y el paquete de distribución. […] 7. Generar navegación y cerrar base 1.0
  sobre ese artefacto.»
- **gemini:** navmesh en el paso 3 y Terrain Builder en el 5.
- **glm:** «7. Navmesh + física + IA + lancha sobre el mundo congelado […] 8. Terrain Builder al congelar la base».

### Arroyos estrechos

- **astra:** «agua somera continua y orilla suave, con tratamiento legible del lecho […] No prometería que el
  tratamiento visual resuelva la transparencia.»
- **gemini:** surco libre con lecho oscuro (rechazado arriba: ya probado).
- **glm:** surco con lecho oscuro (rechazado), o «Ensanchar el contorno de diseño de los arroyos importantes a ≥ 3
  vértices», que es decisión de producto.

## Rumbo que propone el árbitro (para que Guillermo lo fije)

1. **Ver v2 en motor**, con veredicto por vista. Si pasa, se congela la superficie.
2. **Contrato P9.** Fijar qué cauces son navegables y con qué embarcación. El canal Luga–lake_014 es navegable
   (hoy tiene 0,35 m de calado) o solo visual.
3. **Política de niveles, firmada.**
   - El 82 % sano no se toca; los dos lagos grandes se deciden aparte.
   - Los aislados con dique alto bajan al nivel del entorno, rehaciendo lecho y orilla.
   - Los conectados se resuelven junto con el perfil de su río; el caso del Luga queda pendiente del disenso.
   - El tope de nivel solo debe actuar entre aguas conectadas por diseño.
4. **Reconstruir** niveles, ajustar después las orillas y pasar puertas y censo.
5. **Cauces: prueba acotada.**
   - Encadenado con curvas reales en R1; umbral de uso: vértices mojados interiores.
   - R2 y R3 vuelven a planos.
   - Criterio: doble lámina ≤ 1 % por tramo, 0 huecos, lectura en motor y lancha.
   - Presupuesto: 2 variantes y 1 corrección.
6. **Arroyos:** una sola sesión de decisión a altura de jugador. Ensanchar los arroyos protagonistas solo si lo pide
   Guillermo.
7. **Aceptación visual y física con mareas**, congelar la geometría, y después Terrain Builder, navmesh e IA, en el
   orden que se fije.

## Coste

- **astra:** suscripción de OpenAI, 105.738 tokens.
- **gemini:** suscripción de Google, 94.271 tokens (75.563 de entrada).
- **glm:** GX10 local, 37.512 tokens, coste 0.
- **Grok:** cinco sondas sin celda, con coste prácticamente nulo.


## Nota posterior (04-10, Guillermo)

La lane gemini usó `gemini-3.1-pro-high`, una generación vieja, cuando `agy models` ofrecía `gemini-3.8-flash-high`.
Guillermo: «usaste un modelo muy viejo de gemini, tenemos el 3.8 por cli antigravity mucho mejor». El error es del
orquestador al sellar la celda: la regla de reparto pide el id más reciente de cada familia. Queda pendiente relanzar
esa lane con `gemini-3.8-flash-high`, con el mismo `BRIEF.md` (sha 02e48c1b) y el mismo puntero, y añadirla a este
arbitraje. Hasta entonces, la voz de Gemini en este consejo es la de 3.1 Pro, y sus dos premisas falsas se le
atribuyen a ese modelo, no a la familia.

## Relanzamiento con gemini-3.8-flash-high (04-10, 18:11–18:13)

- **Celda.** `gemini-3.8-flash-high` × `agy` 1.2.16. La sonda `agy models` del mismo día la da como la versión más
  alta.
- **Entrada.**
  - El mismo `BRIEF.md`, sha 02e48c1b.
  - El puntero es el original más una frase que lleva la raíz del repo a `snapshot-5125f35`, un `git archive` del
    commit que leyeron las otras lanes. El repo vivo ya contiene sus dictámenes, este arbitraje y el plan.
  - cwd y `--add-dir`: solo la instantánea y `brief\`. Puntero sha256 a84f87aa….
- **Estado.** COMPLETE: RC=0, 136 s, 191.302 tokens (28.041 de salida), contrato completo y `FIN-DICTAMEN`. Salida
  en `lanes/gemini38/`.
- **Ceguera.** No cita nada posterior a 5125f35. Usa la medida vieja de rumbo (0,44° y 0,69°) y no menciona los
  otros dictámenes, el arbitraje ni el plan.

| Afirmación | Verificación (ORQ, en la instantánea) |
|---|---|
| Lago 269: 4,62 km², nivel 2,64 m, cuelga 0,333 m, dique 0,797 m | Correcta: `census.json:65-83` |
| Lago 170: «dique de 0,55 m» | Falsa: 0,547 m es lo que cuelga; el dique es de 1,153 m (`census.json:101-102`) |
| El colocador solo recorre rectas: `for k in straights` y `psi` | Correcta: `fit_channel_pieces_v30.py:264` y `:274` |
| Franja a 1,85 m en la cabecera del Luga | Correcta: README del pulido, línea 17 |
| Suavizar 30–60 m alrededor de los lagos con `valley_reach_m = 45.0` | Falsa: vale 150,0 y solo actúa hacia el agua que fluye, clases 3, 5 y 6 (`build_v30.py:35` y `:355`) |
| 7 huecos de R2 con planos, en el control «bedb362b» | El hecho es correcto; el run no: es el control 337562e3 (README del piloto, línea 98) |
| Rumbo en junta de Chernarus: 0,44° y 0,69° | Medida con el fallo de la herramienta (corrección 1); hoy da 0,13° y 0,27° |

### Qué añade

1. **R2 y R3 en planos vuelven a tener huecos.** Con planos, el control dejó 7 huecos a casco en R2, y el plan los
   manda a planos sin decir nada de esos huecos. ACEPTADO como riesgo:
   - R2 y R3 no son navegables, así que esos huecos no rompen P9;
   - pero vuelve el escalonado de BALTIC-015, y su aspecto entra en la sesión de arroyos (paso 6).
2. **Tercera vía para los arroyos: lecho seco, sin agua del motor.** Una vaguada de 0,30–0,60 m con grava y sonido;
   donde haga falta lámina, saltos discretos tapados con rocas en el mapeado. No es el lecho oscuro rechazado y no se
   ha probado. Queda como OPCIÓN para la sesión del paso 6. Quita el agua a los arroyos, lo que toca P2 («conservar …
   ríos … agua funcional»), así que la decide Guillermo.

### Disenso (literal)

- **Lagos conectados:** «Mantener la cota de agua requerida por el gradiente fluvial y suavizar el terreno exterior
  en un radio extendido (30–60 m).» Es la misma postura que 3.1. Guillermo ya decidió bajarlos con su río.
- **Arroyos R2 y R3:** «No deben volver a planos pond. Deben convertirse en **cauces secos / lechos de roca y
  grava**, sin planos de agua de motor.»
- **Orden:** navmesh e IA (su paso 6) antes que Terrain Builder (su paso 7). Guillermo fijó lo contrario.

### Efecto en el rumbo

- El orden no cambia.
- El paso 5 nombra los huecos de R2 y R3 en planos.
- El paso 6 suma el lecho seco como opción, pendiente de Guillermo.
- Frente a la lane de 3.1 Pro, 3.8 Flash aporta dos ideas nuevas y comprobables. Ninguna de sus premisas es falsa;
  hay tres citas erróneas de detalle.
