# GlobalContourV1: extensión del suavizado y cobertura nativa

La pasada global mejora las orillas y conserva las masas de agua. Es una preview comprobada, no la aceptación de toda la base 1.0. Plan, autoría, consumidores y negativos se preservan junto a este informe; los binarios y fuentes grandes permanecen en `E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009`.

## Resultado geométrico

Se procesan 3.233 bloques con perímetros fijos. El candidato inicial falló conservación de una masa, máximo global y una tolerancia float32. Una reparación por composición restaura 22 bloques, sin reoptimizar ni relajar criterios. El resultado cambia 53.853 vértices respecto a NativeContourV1: p90 de giro 52,53184 → 38,94830 grados; proporción sobre 30 grados 21,7243 → 14,6426 %. Las 830 masas significativas mantienen topología y al menos 90 % de intersección; no hay nuevas caras secas inundadas ni cambios de los controles físicos/protecciones. Desplazamiento máximo del contorno correspondiente: 4,0999997 m.

La métrica independiente extrae y une los contornos de los triángulos nativos, sin reutilizar el grafo del autor. Diez de los 217 sectores muestreados empeoran su p90, máximo 3,246 grados. Quedan esquinas fijas y finales fuera del ámbito de esta pasada: no se afirma que cada rincón mejore.

## Agua compilada y lectura del motor

La nueva geometría requiere 96 microjuntas. Todas usan centros XZ exactos, planos físicos congelados y el campo visible preservado. La cobertura compilada de 404.484 celdas da cero hueco físico y residuo visible de 3,8464e-12 m². Hay 18.024 instancias de agua y nueve puentes; 13.128 modelos de agua referenciados. El coste gráfico global no está aceptado.

El censo nativo lee 4.194.304 vértices; error máximo de suelo 0,0000152588 m, sin anomalías nominales/dinámicas en controles secos. Las 19 faltas de presencia y 329 consultas escalares positivas sin ambos flags quedan inventariadas, no descartadas. La regresión de 674 puntos × 62 instantes, con calma y viento de 20 m/s, pasa integridad, controles, antiguos gaps y calado R1 seleccionado. Las 96 juntas nuevas registran presencia de estanque en las 62 muestras. La clasificación completa está en `native-diagnostic-classification.json`; los contactos intermitentes no se etiquetan como tierra seca ni como cauces navegables.

El residual calibrado junto al puente sigue físicamente seco en las 62 muestras: profundidad entre -0,889122 y -0,647191 m. Eso no resuelve su render. Las vistas R3 aérea y rasante tienen texturas cargadas y no muestran las antiguas juntas; los taludes son más continuos. Los lagos 269/170 y el final del Msta tienen vistas actuales guardadas en `surface-views.json` y `frames/`. No constituyen una inspección gráfica completa del mapa.

## Identidad y pendientes

- Terreno `223029dedd7122096bb51c704fc722629b2be549f6c946b9cb89c7d1a8b6d6eb`.
- Mundo desplegado `d72ebb45b0716e477667e829dd63082b3ab430724fa27372f117d1d102ad0efd`.
- Agua desplegada `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`.
- Mod `P:/Mods/@DayZ_Baltic_GlobalContourV1`; no promoción a TB/navmesh.

Los runs completos y gráficos cerraron ordenadamente; el último estado deja el banco libre. El marcador de materiales R2 no tuvo control positivo y queda inconcluso, sin otra variante de color. EV15 reproduce con esta preview la dependencia del residual respecto al mar y restaura el paquete normal. Siguen abiertos el mecanismo gráfico, la forma restante/finales, decisión de los dos lagos, consumidores finales de navegación y carreteras, TB/Generate Layers y navmesh/IA. El ticket de foco ya existe y no se duplica. No hay revisión externa atribuida a esta unidad.
