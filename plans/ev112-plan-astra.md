# EV112: plan de continuación para Astra (relevo del 18-10-2026)

Autor: Claude (Opus 5.5), sesión del 15 al 18-10. **Este plan ya está decidido con Guillermo: no hay que replanificar.** Cada orden de
trabajo (OT) dice de dónde parte, qué hacer, cómo se acepta y quién la revisa. El orden está pensado para que EV112 salga en una sola
tanda y Guillermo la vea en el juego en una sola sesión (DZ-R5).

## Estado de ejecución — 2026-10-20

EV112: correcciones e integración verificadas; sonda de servidor completada (4114 puntos). Puentes 10/10, orillas 100/100, presa y 2450 controles obligatorios del kit PASS. G8 estricto conserva FAIL por 271 labios/juntas de hormigón pendientes según plan §5. Vista personal instalada y preparada, sin lanzar.

OT7 R2 SOUND-with-fixes, sin críticos ni mayores abiertos. La primera sonda detectó cuatro controles afectados por oleaje; se corrigieron cuatro vértices sin alterar huella, topología ni objetos. La nueva sonda y el diagnóstico temporal pasan esos controles. Se conserva el FAIL original y el FAIL estricto de las juntas. No renovación del lanzador ni cambios de umbrales. 015-45/disco60m PENDIENTE, nunca PASS. Juntas de hormigón pendientes. OT4<=0,03m solo en el dominio central. Límites forestales/regionales y de fase conservados. Sin aceptación visual, FPS ni capacidad80–100jugadores.

[Evidencia y cierre](../evidence/v31-pond-layer-2026-10-13/ev112/integration/runtime-b-20261019/README.md). Fuentes de corrección: eb77548bbfe7394db014b3000d9bd45add26a9c4; sin push.

## 0. Dónde está todo

| Qué | Dónde |
|---|---|
| Rama | `claude/handoff-astra-map-review-6d301c` (worktree `DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c`), commit del relevo del 18-10, sin push |
| Última preview vista | **EV111 V2** = EV110 + piloto de bosque: `P:/Mods/@DayZ_Baltic_EV111_ForestPilotV2`. EV110: `P:/Mods/@DayZ_Baltic_EV110_LatticeShoresV1` |
| Cadena EV110 (base de EV112) | `evidence/v31-pond-layer-2026-10-13/ev110/BUILD-EV110.md` (todos los comandos y sha) y `ev110/deploy.json` |
| Build EV111 | `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev111/r2/BUILD-EV111-r2.md` |
| Vista del 17-10 (qué dijo Guillermo y qué arregla cada cosa) | `evidence/v31-pond-layer-2026-10-13/ev110/review-ingame-2026-10-17.md` |
| Resultados de todos los flujos (diseños, implementaciones, revisiones de Codex) | `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/handoff-20261018/results/` (y copias en `evidence/.../ev110/reviews/`) |
| Dependencias que vivían en el scratchpad | `E:/.../handoff-20261018/deps/` (forest-livonia, censo de cauces finos, turn-pieces). Manifiesto con sha256: `handoff-20261018/MANIFEST.json` |
| Trabajo a medias de los agentes parados el 18-10 (SIN revisar) | `E:/.../handoff-20261018/wip/` |
| Salidas de trabajo de EV112 | `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-wip/<pista>/` |

Python: solo `C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe -I`, con scripts en fichero (nunca rutas
de Windows dentro de `python -c`). Rejilla 6 m, fila 0 al norte, diagonal NO-SE. En E: hay junctions: **nunca borrar recursivamente**.
OneDrive: escribir cada fichero del worktree de una vez y releerlo comparando el sha256.

## 1. Decisiones de Guillermo vigentes (no reabrir)

- 15-10: el kit `streambed` va **en malla** (rectas solo N-S, E-O y NO-SE, centradas en una fila de vértices), como Chernarus.
- 15-10: la pasada de orillas **puede mover el margen de reserva** (reserve sin platform); la calzada (`platform`) y Narva no se tocan.
- 15-10, 015-16: **apilar** una copia del puente de madera debajo y repintar la ladera bajo el puente como suelo natural (hecho en EV110).
- 16-10: **bosque**, primero un piloto en 2 sectores y después todo el mapa; referencia **Livonia**; árboles y arbustos; borde que
  **desborda como Livonia**; turbera de **pino disperso y abierta**.
- 17-10: bosque piloto «muy bien, casi perfecto» (EV111 V2): **aprobado para extenderlo a todo el mapa**.
- 17-10: cauces finos poligonales → **kit en malla** (no charca reencauzada).
- 17-10: escalón río/mar de Narva → **presa vanilla**. 18-10: **aprobada «tal cual»**: 21 vértices de Narva para los estribos
  (hasta 4,5 m), 33 celdas aguas abajo pasan a lecho seco a 1,0 m, 3 vértices de mar secos, punto de aparición en la ladera y
  cruce transitable por la presa. Es la **única excepción** a Narva congelada.
- 18-10: calzadas: el islote (c0, c1) con terraplén de ancho constante y **también revisar los otros 6 sitios** del censo (c2–c7),
  cada uno con su regla.
- 17-10, 015-16: «aquí lo dejamos así de momento». **No** reabrir el «tablero enrasado» de las rampas de madera sin Guillermo.

## 2. Estado de las herramientas en este commit

| Herramienta | Versión en el commit | Estado |
|---|---|---|
| `tools/water/streambed_kit_v31.py` | **v9** (sha 9d83006e…) | Implementado; Codex ronda 1 «sound_with_fixes» con 6 fallos mayores ABIERTOS (OT1). El arreglo a medias está en `wip/kit-v9-fix-round/` (973fec4e…, sin revisar). |
| `tools/water/kit_worklist_v31.py`, `extract_stones_geometry_v31.py`, `streambed_stones_geometry_v31.json` | v9 | Igual que el kit. |
| `tools/terrain/despike_v31.py`, `census_pyramids_v31.py`, `evidence/.../despike/` | final (988625aa…) | **Hecho**: 2 rondas de Codex, la última «sound_with_fixes» con solo menores. |
| `tools/water/dam_v31.py`, `dam_gates_v31.py`, `dam_negatives_v31.py`, `probe_points_dam_v31.py`, `eval_dam_probe_v31.py`, `verify_pond_exact_v31.py`, `run_with_odol56.py`, `evidence/.../dam/frozen-exception-narva.json` y `sites-dam.json` | **ronda 3 entregada** (dam_v31 516d89f9…; conjunto de 9 ficheros en `handoff-20261018/wip/ev112-dam-r3-top/deliver-manifest-9.json`) | Implementa los arreglos de la ronda 2 de Codex: el contrato de la excepción congelada, G3, G4, la LOD roadway y la sonda. Al agente lo pararon mientras volvía a pasar las puertas (`regate_r3.py`), así que **faltan la ejecución final de puertas y negativos y la revisión de Codex** (OT3). La ronda 2, revisada por Codex, está en `handoff-20261018/wip/dam-round2-reviewed/` (dam_v31 5df65281…). |
| `tools/water/causeway_v31.py` + gate en `evidence/.../ev112/causeway/` | ronda 2 (bb8a32b2…) | c0/c1 hechos (puertas en PASS); Codex ronda 2: 2 mayores sobre la puerta ABIERTOS. c2–c7 por hacer (OT4). WIP parado: `wip/ev112-causeways2-r3-top/`. |
| `tools/terrain/bridges_v31.py` | **v6** (0ea49c4b…) | Implementado con fallos abiertos (OT5). Respaldo v5 (el de EV110): `evidence/.../bridges/ev112/bridges_v31_v5.py` (f0c9fedf…). `merge_bridge_records_v31.py` es nuevo (incluye el puente piloto 015-15). |
| `tools/vegetation/forest_v31.py` | **EV111 r2** (d81e8ede…, revisado) | El despliegue al mapa se paró a medias: `wip/forest-rollout/` (c476bc4b…, sin revisar) (OT6). Necesita `deps/forest-livonia`. |
| `tools/water/shore_ramp_v31.py`, `tools/terrain/patch_surface_v31.py`, `package_surface_patch_v31.py`, `build_surface_v30.py` (`--road-off-lowered`) | EV110 | En uso desde EV110. |
| `tools/water/run_with_odol56.py` | nuevo | Parche en memoria del lector ODOL para el formato v56 de binarize del 15-10 (buzón fb-20261017-234641-96e0). Úsalo para todo lo que lea ODOL de builds nuevos. |

## 3. Órdenes de trabajo

Reglas comunes a todas las OT:
- Puertas mecánicas: script que imprime PASS/FAIL, con controles negativos que deben dar FAIL.
- Revisión de **otra familia** (Claude ↔ Codex) con un **tope de 2 rondas** fijado antes de la primera. Pasado el tope, decide el
  producto (la sonda y Guillermo en el juego), no más rondas.
- Ninguna puerta se relaja sin decirlo.
- Sin commit hasta que la OT pase.

### OT1. Kit v9 (piedras y cauces finos)

**Cierre offline 18-10:** `evidence/v31-pond-layer-2026-10-13/ev112/ot1/GATES.md` y `acceptance-offline.json`.
G0–G7/G9–G11, negativos y determinismo de pasos0/1 PASS sobre run-l; 6593 piezas +1014 piedras.
49/51 sitios construidos, mismos dos conservados como charca. G8 se ejecuta en OT8 sobre el paquete final.

**Parte de:** el kit v9 del worktree, `E:/.../ev112-wip/kit/` (run, gates G0–G11, `reach-report.csv`, `sites-ev112.json`,
`worklist-ev112.json`, `exclusions-ev112.json`) y la revisión de Codex en `handoff-20261018/results/wf-ev112-partial-results.json`
(flujo `wf_f0e14df0-f87`).

**Ya bien:** las piedras. Base enterrada a −0,08 m y q p50 2,98 m, dentro de Chernarus p25–p75 de 1,06–3,23 m.

**Problemas** (resultado de v9 más los 6 mayores de Codex):
1. El alcance se pasó de lo decidido. Son 8.419 piezas, con 5.120 `slanted` y 1,42 Mm³ de tierra movida. Además, 22 tallos (18,5 km)
   con ancho p50 > 6 m pasan a 3,5 m.
2. Las uniones con charca, puente y otro kit acaban en seco antes del agua conservada: p50 21 m, p90 50 m, máximo 514 m.
3. G2 excluye las piezas inclinadas y da PASS con cero medidas.
4. G3 no comprueba la continuidad en las uniones.
5. El kit crea 12 montículos de dos vértices que G9 no ve y que despike protege.
6. Hay una franja sin dueño entre el suavizado del kit (24 m) y la protección de despike.
7. G10 no exige visibilidad mínima de las piedras.
8. El paso 0 no es determinista: desempata con el orden de un `set`.

**Hacer:**
- a) Lista de trabajo = tramos del censo **finos** (ancho p50 ≤ 6 m) y **poligonales** (métrica del censo, umbral en
  `kit_worklist_v31.py`). Los tallos más anchos quedan como charca. Informe de lo excluido.
- b) Cada tramo de kit llega al agua conservada sin hueco seco > 6 m (cascada o sill en el extremo, o recortar menos). Puerta nueva
  sobre las uniones, en triángulos nativos.
- c) G2 mide todas las piezas (también `slanted`) y falla con cero medidas.
- d) Montículos: el kit no deja ninguna prominencia > 0,5 m (métrica de `census_pyramids_v31.py`) en su banda. Las 18 pirámides
  de las filas de patas de los puentes de madera son de la OT5.
- e) G10 exige ≥ 25 % visible con el LOD visual completo.
- f) Determinismo: ordenar antes de desempatar y probar dos ejecuciones byte a byte.
- g) Sonda: muestreo por tramo de ≤ 3.000 puntos en total, no 84.679.

**Aceptación:** G0–G11 en PASS más las puertas nuevas, los negativos y Codex sin críticos ni mayores (tope de 2 rondas).
**Número de piezas a informar a Guillermo** antes de EV112 (rendimiento, regla 7: no se afirma nada por aritmética).

### OT2. Despike (montículos piramidales): HECHO, solo integrar

**Corrección aprobada verificada 18-10:** los 12 islotes conservan suelo seco (mínimo 0,80 m). G1–G8 y 13 negativos PASS; el negativo de hundir un islote falla únicamente G5. Máscara de mar idéntica, por lo que su topología de aristas nativas no cambia. Recibo `evidence/v31-pond-layer-2026-10-13/despike/acceptance-dry-islets-20261018.json`. Repetir sobre el terreno final de EV112.

En la cadena va después de orillas y calzadas y antes del último bury. Los comandos exactos están en
`handoff-20261018/results/wf-ev112-partial-results.json` (pista `despike`, `chain_commands`) y en
`E:/.../ev112-wip/despike/final-r3/commands.txt`. La puerta debe imprimir `OVERALL: PASS`.

Lo que no es de esta OT:
- las 18 pirámides de las filas de patas de madera (OT5);
- 34 residuos retenidos por el suelo de orilla;
- 12 islotes que pasan a fondo de mar: Guillermo decidió por picker el 18-10 **conservarlos secos y ajustar despike**. Comprobar topología de agua en OT7; no hundirlos ni dejar incoherente la máscara `water`.

**Guarda de integración verificada 18-10:** despike puede desplazar una orilla ya suavizada aunque sus G1–G8 pasen. La prueba del 18-10 usa `--shore-footprint` del terreno de entrada y `--shore-mask v31_causeway --shore-mask v31_shore_ramp`. La guarda conserva los extremos de las aristas de agua corregidas; las puertas originales siguen sin cambios. Prueba diagnóstica: los seis contornos idénticos, reducción >90 % para prominencias >0,5 y >1 m, 12 islotes secos; sin guarda C3/C7 regresan. Recibo `evidence/v31-pond-layer-2026-10-13/despike/shore-guard-20261018.json`. Repetir con el candidato final de C3; esto no acepta EV112.

La revisión de integración R1 detectó dos vértices de laguna que movían la orilla pese a conservar la huella. La misma guarda incluye ahora `--shore-mask v31_lagoon`: conserva sus alturas y aristas de agua exactamente; quedan tres picos secos corregidos, sin triángulos mojados incidentes. G1–G8, las 157 orillas y las métricas c0–c7 pasan con el terreno C. Evidencia `ev112-build-20261018/terrain-c-review-closure.json`. R2 permite continuar sin hallazgos mayores; la aceptación del build sigue pendiente. La medición central OT4 no se extrapola a los 1.491 vértices exteriores que tocan agua: 538 inciden en tramos G2, y `ot4-outer-waterline-c.json` informa las métricas de todos, con p90 entre 0,02869 y 0,11791 m fuera del dominio central.

El bosque se coloca **después** del despike.

### OT3. Presa de Narva (aprobada «tal cual» el 18-10)

**Cierre offline 18-10:** ronda 3 verificada, puertas/negativos/lector ODOL y revisión Codex sin críticos ni mayores. Evidencia en `evidence/v31-pond-layer-2026-10-13/ev112/ot3/REVIEW.md`. La holgura independiente es 0,01960633 m; repetir sobre la cadena final en OT7 y sonda en OT8.

**Parte de:** la **ronda 3 ya entregada** al worktree (ver la tabla de la sección 2). Se escribió para cerrar los hallazgos de la ronda 2
de Codex (`handoff-20261018/results/wf-ev112-B-results.json`, pista `dam`):
1. La excepción congelada aprobada es un contrato explícito en `evidence/.../dam/frozen-exception-narva.json`, generado con
   `make_contract.py`.
2. G4 falla ante cualquier otro cambio congelado, cualquier cambio de máscaras y cualquier bajada.
3. G3 falla si aparece agua nueva fuera de la envolvente original.
4. `verify_pond_exact_v31` exige exactamente una LOD visual y una roadway.
5. Los puntos de sonda están corregidos.

**Hacer:**
- a) Correr las puertas y negativos de la ronda 3: `wip/ev112-dam-r3-top/regate_r3.py` y `dam_negatives_v31.py`. Además, añadir un
  negativo por cada hueco cerrado si no está.
- b) Volver a medir la holgura de G2 (0,02 m) sobre el terreno real de la cadena EV112.
- c) Una revisión de Codex con tope de 2 rondas. La ronda 1 de Codex falló una vez por las comillas del heredoc: pasarle el prompt
  en un fichero.

**Aceptación:**
- puertas y negativos;
- `bury` sin bordes nuevos;
- `verify_pond_exact` (con `run_with_odol56.py`);
- Codex sin críticos ni mayores.

### OT4. Calzadas: c0–c7 verificadas offline; disco 015-45 pendiente

**Decisión adicional de Guillermo, picker 18-10:** conservar los 60 m protegidos alrededor del cruce navegable pendiente 015-45, centro (10397.4, 9421.9). El tramo de c4 que se solapa queda pendiente, sin declararlo PASS; completar el resto de EV112. No se autoriza alterar la navegación ni la plataforma de ese cruce.

**Decisión vigente posterior, picker 18-10:** «Seguir corrigiendo; no entregar EV112 hasta que cumplan» para c2, c3, c5, c6 y c7. No está autorizado aplazar esos cinco sitios, reducir su umbral de ondulación ni presentar los candidatos fallidos como entrega. El disco protegido de 015-45 sigue pendiente, sin PASS.

**Excepción concreta de topología aprobada por picker 18-10:** rellenar a 1,05 m únicamente los 11 vértices de la depresión aislada de c2 identificada en `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-ot4-20261018/proposal-c2-pocket-NOT-AUTHORIZED/proposal.json`. El nombre de la carpeta conserva el estado de la propuesta original; esta decisión posterior autoriza su integración. Se permite exclusivamente la desaparición de ese componente (82→81), sin uniones ni divisiones de canales; permanecen el umbral 0,03 m y todas las demás protecciones. La aceptación exige verificar el cambio concreto y el terreno final.

**Cierre offline 19-10:** c2, c3, c4 fuera de 015-45, c5, c6 y c7 pasan la puerta física independiente con p90 máximo 0,02987227 m. Capa reproducible de 3.792 vértices (`tools/terrain/apply_causeway_sites_v31.py`, `evidence/.../ev112/causeway/c2-c7-height-layer.*`), replay idéntico bit a bit, seis negativos de puerta y siete rechazos de capa. Topología: mar 82→81 por los 11 vértices aprobados; tierra seca 27→27; charcas y complementos intactos; cero cambios protegidos, defectos nuevos o cambios de bury. Los seis renders de 0,25 m/px se han inspeccionado. Despike final conserva los p90. Evidencia: `additional-sites-acceptance-20261019.json`. La transición sur de C3 se ha corregido para conservar también las 157 orillas de la fase anterior: G2 pasa tras despike. El G7 histórico de orillas conserva FAIL en cuatro vértices de C7 sustituidos por la rampa posterior de OT4; su aplicabilidad se documenta en el recibo y queda sujeta a la revisión independiente del build. La aceptación del build y OT8 siguen pendientes.

**Parte de:** `tools/water/causeway_v31.py` (ronda 2) y la puerta con su INVENTORY en
`evidence/.../ev112/causeway/gate_causeway.py`.

**Hacer:**
- a) Arreglar los 2 mayores de Codex. G8 convierte una aprobación explícitamente falsa en PASS, y el INVENTORY tiene que congelar
  también las coordenadas de c2–c7.
- b) Para cada sitio c2–c7 (Guillermo pidió revisarlos), hacer un render a 0,25 m/px y un diagnóstico, elegir la regla y aplicarla
  con la puerta por sitio (wiggle p90 ≤ 0,03 m, sin cambios en platform ni Narva, sin bordes nuevos, topología del mar intacta).
  Las reglas posibles son el terraplén de ancho constante, la rampa de orillas, un cono como en EV102, o dejarlo como está si se
  demuestra que ya cumple.

   | Sitio | Centro | Qué hay |
   |---|---|---|
   | c2, c4 | (10235, 9398), (10417, 9426) | ~35 m junto a un canal de mar |
   | c3 | | cruce de arroyo de 6 m |
   | c5 | | 37 m, mar a un lado y charca al otro |
   | c6 | | 32 m en una junta de río |
   | c7 | | río de charca junto a la carretera |

   Las coordenadas de cada id están en el INVENTORY. Los centros del censo son (8568,10414), (8227,10468), (3588,6867) y
   (9678,2661).

### OT5. Puentes

**Verificado offline 18-10:** v6 pasa G1/G3/G4/G6/G7/G8/G10/G12/G14 sobre OT1 run-l, con fixtures v4 nuevas; escapes G10/G14 y entradas numéricas corregidos y probados. Véase `evidence/v31-pond-layer-2026-10-13/bridges/ev112/REVIEW-20261018.md`. Integración y comparación de sonda OT8 pendientes.

**Parte de:** `bridges_v31.py` v6 y sus puertas (`evidence/.../bridges/ev112/gates_v6.py`, `run_gates_v6.py`). Revisión en
`wf-ev112-B-results.json` (pista `bridges`).

**Logrado en v6:**
- agua continua bajo los 10 puentes (la abertura de 015-18 pasa de 1,5 a 3,1 m);
- extremos metálicos nivelados (lo que Guillermo pidió en 015-13);
- G1, G3, G4, G6, G7, G8, G10, G12 y G14 en PASS.

**Abierto:**
- G11, la orilla a < 60 m del puente: p90 de 0,18–0,51 m frente al objetivo de 0,08. Guillermo: «la parte del río a ambos lados
  del puente cerca le falta smoothing».
- G2, G9 y G13: rampas y alas de madera (0,83–2,27 m de aire), imposibles en la malla de 6 m sin cambiar la pose. Requiere a
  Guillermo y no se reabre por ahora.
- G5: 4 vértices de calzada de 015-40 bajan al lecho para unir el agua.
- Escapes de G10 y G14 que señaló Codex.

**Decisión para EV112:**
- Usar **v6** si pasa su batería sobre el terreno del kit v9 (la OT1 cerrada) en G1, G3, G4, G6, G7, G8, G10, G12 y G14, y si la
  sonda no empeora frente a EV110.
- Si no, usar **v5** (`bridges_v31_v5.py`) más solo el nivelado de los extremos metálicos.

**Después de EV112 (OT5b):** el suavizado junto a los puentes con otro enfoque.
- El kit en malla puede pasar bajo el puente en los arroyos, ya que la OT1 extiende el kit.
- Una regla de orilla que pueda tocar la zona de corte fuera de las huellas.
- Dar a las filas de patas de madera las mismas alas suaves que a las rampas, que es el origen de las 18 pirámides de la OT2.

### OT6. Bosque en todo el mapa

**Parte de:** `tools/vegetation/forest_v31.py` (EV111 r2, revisado), `handoff-20261018/deps/forest-livonia` (pasar la ruta, que
antes era el scratchpad) y las puertas en `E:/.../ev111-wip/forest/scripts-v3/`. WIP parado: `wip/forest-rollout/`.

**Hacer:**
- a) **Suelo oscuro sin árboles**, lo que vio Guillermo: bordes de los cuadrados del piloto y claros sintéticos sobre textura de
  bosque. Al extender al mapa desaparecen los bordes. En los claros, no ponerlos sobre textura de bosque o repintarlos como prado
  con `patch_surface_v31.py`. Puerta de concordancia textura/árboles con bandas medidas en Livonia; los casos del piloto de EV111
  deben dar FAIL.
- b) Todo el mapa con las mismas reglas, sin costuras entre teselas de cálculo. Exclusiones: carreteras con su ancho pintado, agua
  y mar, puentes, kit y sus piedras, Narva, presa y calzadas.
- c) Robustez: G7 (turbera) fallaba en 4 de 10 semillas de reserva en la turbera pequeña de B, y G2 en las semillas 22 y 31.
  Arreglar el generador, no las bandas, y validar con semillas nuevas no vistas.
- d) Recuento por familia y por km² frente a Livonia, sin afirmar rendimiento. Señalar el km² más denso para medir FPS en el juego.

Se coloca al final de la cadena, sobre el terreno definitivo y `fp-ev112`.

### OT7. Integración de EV112

Orden de la cadena, sobre la base de `BUILD-EV110.md` (comando a comando):

1. Kit v9 (OT1) con el paso 1 sobre las entradas de EV107, luego `bury` y la última `fpN`.
2. Puentes (OT5) sobre el terreno del kit, luego `merge_bridge_records_v31.py` (piloto 015-15 + kit + puentes), luego `bury`.
3. Presa (OT3), luego `bury`.
4. Orillas, luego calzadas c0–c7 (OT4), luego despike (OT2), luego el último `bury` y su fpN como `fp-ev112`.
5. `pond_author_v31`, luego `pack_water_v30.ps1`, luego `stage_pond_pilot_v31 --full`, luego `verify_pond_exact_v31` (con
   `run_with_odol56.py`).
6. Bosque (OT6) sobre el terreno final.
7. `stage_bridges_v31` con los registros piloto + kit + puentes + presa + bosque, luego el compilado (copia de
   `compile_world_ev110.ps1`; AddonBuilder necesita el subst de P:).
8. Parche de superficie sobre el terreno final, atado al sha del terreno y del WRP. Debe cubrir carreteras rebajadas, celdas de
   calzada, el lecho seco de Narva y los claros repintados. Comprobar que el despike no borra pintura de carretera que debe quedar.
9. Empaquetar `@DayZ_Baltic_EV112_...` sobre el PBO base de EV95, con la lista exacta de entradas cambiadas, y escribir
   `deploy.json`.
10. Revisión del build por otra familia (como `wf-ev110-build-results.json`).

### OT8. Sonda del servidor y vista con Guillermo

**Sonda:**
- Misión `BalticBridgeProbeV2.BalticTrial`, solo servidor. Respaldar y sustituir el `points.csv` de
  `C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticBridgeProbeV2.BalticTrial/`.
- Lanzar:
  `dayz_test_run(project="DayZ_MCP", mode="server", mission=<esa ruta>, extra_mods=["P:\\Mods\\@DayZ_Baltic_EV112_..."], no_base_mods=true, no_file_patching=true, on_busy="queue", wait_for_box_s=600)`.
- Luego `session_acquire_wait`, `wait_for(file_matches, role=server, profile_file="baltic_bridge_probe_v2.log", pattern="END;<N>")`,
  `dayz_test_close` y `session_release`.
- Separar el registro con el `split_log.py` estricto de `evidence/.../ev110/probe/`.
- Evaluar con la G8 del kit, `eval_bridges_shores.py` (el nivel se lee del campo de superficie de charca del motor, porque
  `ground + depth` lleva oleaje) y `eval_dam_probe_v31.py`.

**Vista con Guillermo:** misión `BalticBasic.BalticTrial` en modo `all`, con lease y teletransportes. Puntos:

Decisión por picker del 18-10: completar la sonda del servidor aunque Guillermo no esté y dejar la vista personal preparada. No bloquear las pruebas del servidor esperando su regreso; no declarar su aceptación visual sin que haya visto el resultado.
- aparición en Narva, con la presa;
- kit-118 (8253, 9038) y un tramo nuevo de kit hacia el NE;
- calzada sur del islote (6798, 10422) y uno de c2–c7;
- 015-13 (9369, 8717), extremo oeste, y el cauce junto al puente;
- el río junto al 015-16 (10360, 7441);
- bosque en un km² denso (medir FPS) y la turbera (8271, 5422).

## 4. Entorno (lo que rompió esta semana)

- **Lanzador de DayZ MCP**: si Steam actualiza DayZ o DayZ Tools, `dayz_test_run` da `invalid_native_launcher_bundle`.
  1. Diagnóstico (solo lectura): `tools/.venv-mcp/Scripts/python.exe -m dayz_mcp.doctor --daemon-policy normal --json` en
     `DayZ_MCP_dev/tools`.
  2. Renovación autorizada por picker del 18-10 **solo si se reproduce ese error y pasan las verificaciones**: `build_native_launcher.py --offline --verify-reproducible`, comprobar que sale con 0, y
     después `launcher_registry_update replace-dayz-test-v1 --expected-sha256 <sha del registro actual>`.
  3. **No** usar `rollback-last` + `install`: con una entrada ya instalada falla (buzón fb-20261016-155416-c9aa).
- **ODOL v56 / OPRW v32** desde el binarize del 15-10: `run_with_odol56.py`. Arreglo de fondo pedido al Pack (fb-20261017-234641-96e0).
- **Otras sesiones** usan DayZ MCP (helicóptero H2R): mirar `session_status` antes de lanzar y no pisar un lease ajeno.
- `steam_app_view_stale`: lanzar siempre con `dayz_test_run`, nunca DayZ a mano desde una shell de la app.
- Cliente sin foco: menú de pausa y cielo morado hasta que Guillermo hace clic y pulsa «Continuar».

## 5. Abierto que solo decide Guillermo (no bloquea EV112)

- Rampas de madera, «tablero enrasado»: después de EV112.
- 015-25: sin apilar; el tablero inferior quedaría a 1 m del agua.
- El número de piezas del kit y de árboles: FPS en el juego.
- Agua del motor en las juntas de hormigón del kit, cortada 3–4 m en cada junta, como la geometría vanilla. Sin comprobar en Chernarus.
- 23,4 km de cauces: si tras la OT1 sigue habiendo cauces anchos poligonales fuera del kit, proponer otra regla.
