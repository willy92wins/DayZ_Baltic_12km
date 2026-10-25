# EV112 OT1 — cierre del kit v9

Petición vigente: OT1; después OT3–OT6, integración EV112 y sonda del servidor.
Alcance y umbrales: plans/ev112-plan-astra.md, OT1. Enmienda G7 aprobada por picker:
plans/ev112-ot1-confluence-control-amendment.md. Solo se considera mojado el control dentro del núcleo
realmente mojado de una rama declarada y construida, a <=1.8m de su eje continuo; los demás siguen secos.

Estado: **OT1 cerrado para integración offline**. Recibo completo en `acceptance-offline.json` y R/acceptance-l.json.
G8 pertenece a OT8 y sigue NOT_RUN; la aceptación del motor y la vista personal no están concedidas.

R = E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-ot1-20261018/.
Checkout: P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c, base f10b925.
Python: C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe -I.
Fuente congelada: R/source-snapshot-l, 37 archivos, R/checkpoint-l-source.json.
Constructor SHA256: 61c4e393d0803741da48fd417d5509bc76ab7252ed3684fb5108d3b4976cb3f9.

## Candidato completo

R/run-l: 51 sitios evaluados, 49 construidos. 98.0-2 y 67.0-0 conservan su charca porque el recorte
no deja piezas; no hay omisiones nuevas. 6593 piezas +1014 piedras =7607 objetos, eje60.36km y
tramo mojado59.62km. G1 PASS; G2/G3/G4/G5/G6/G7/G9/G10/G11 PASS. G0 en R/regression-n PASS.
G7 comprueba66166 puntos offline y selecciona3000 para motor, cero fallos. No se afirma rendimiento.

```gates
[x] SCOPE: censo exacto de cauces finos y poligonales; anchos/lisos excluidos
  EVIDENCE: R/step0-j-repeat/gate-worklist.json; R/negative-worklist-receiver/negative.json
[x] WIDTH: todas las piezas, ambas piernas slanted, signo y cobertura
  EVIDENCE: R/run-l/gate-g2.json; controles de signo/cero/slanted en R/controls-l
[x] JUNCTION: hueco seco continuo <=6m en cada receptor; puentes >=60m
  EVIDENCE: R/run-l/gate-g11.json; 1.0-0 up/down hueco0m
[x] MOUNDS: formas nativas de1/2/3 vértices y banda completa de propiedad
  EVIDENCE: R/run-l/gate-g9.json; R/controls-l/ot1
[x] STONES: >=25% del LOD completo visible; corredor libre de todos los ejes
  EVIDENCE: R/run-l/gate-g10.json; R/controls-l/ot1/stones-buried
[x] PROBE: <=3000 puntos, grupos completos, confluencias según enmienda
  EVIDENCE: R/run-l/gate-g7.json; R/controls-l/confluences.json
[x] OFFLINE-POSITIVE: G0–G7 y G9–G11 en candidato completo
  EVIDENCE: R/run-l/offline-gates-summary.json; R/regression-n/regression.json
[x] NEGATIVES: controles dirigidos detectan su defecto sobre el positivo final
  EVIDENCE: R/controls-l/summary.json PASS; 16 modos EV110 +13 modos v9 y10 grupos dirigidos
[x] DETERMINISM: pasos0 y1, procesos nuevos, salidas idénticas byte a byte
  EVIDENCE: paso0 R/step0-j-repeat/gate-worklist.json PASS; paso1 R/run-l-repeat/determinism.json PASS
[x] REVIEW-CLOSURE: hallazgos reproducibles de las dos rondas cerrados por evidencia
  EVIDENCE: R/review-r2.md; R/acceptance-l.json, puertas y negativos finales PASS
[ ] ENGINE: G8 real sobre el paquete EV112
  EVIDENCE: R/run-l/gate-g8.json NOT_RUN
```

## Cierre de hallazgos

Dos rondas consumidas; no tercera automática. Revisión cruzada Claude nativo en R/review-r2.md,
de lectura sobre run-a, sin reejecutar puertas completas.

- Lista de trabajo: semillas receptoras no absorbidas, causas de extremo y orden estables. Quitar la protección
  reproduce el fallo y la postcondición rechaza el receptor absorbido.
- Uniones: receptor real, ventana [W-6,W], límites de puente y congelados conservados. El recorte usa obstáculos
  reales y evita dilatar otra vez la máscara de ruta. G11 mide intervalos continuos sobre triángulos nativos.
- Laterales: uniones kit igualan roadway del receptor, sin elevación artificial0.05m; bancos sujetos a límites
  de todos los ejes, pendientes y montículos. Cierre de láminas después del ajuste. Confluencia mantiene1.8m.
- Holgura: rungs y cambios de labio reales añadidos al ajuste reach. run-k fallaba120.0-0 a0.09627069m;
  piloto corregido y run-l pasan G4 conservando el mínimo0.10m.
- G2: normal transversal slanted orientada por lateral real. Cobertura cero falla; sección truncada se vuelve
  a medir hasta encontrar sus bordes. Saturación irresuelta falla. Métricas locales solo diagnósticas, sin
  umbral local nuevo. El negativo de una pieza ancha entre>1000 exige rechazar SUS DOS laterales en G7.
- Montículos: pareja/triángulo y banda conjunta; piedras: LOD completo,25% y corredor de todas las ramas.
  Los negativos dirigidos exigen el fallo preciso, no un fallo ajeno.

Pilotos y candidatos anteriores son diagnósticos. run-j y run-k-repeat fueron abortados, no prueban
repetibilidad. run-g-repeat pasó pero no certifica la fuente posterior. Las seis fixtures de lector en
R/confluence-engine-fixtures son sintéticas y no prueban motor.
Handoff: C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-18-dayz-baltic-ev112-ot1-execution.md.
