**Veredicto: SOUND-with-fixes**

El plan es útil y está bien acotado, pero necesita cerrar tres ambigüedades antes de la investigación para que una tabla “completa” no se confunda con una escena validada.

**Hallazgos**

1. **Correcta demolición de la inferencia previa.** El testigo primario [model_geometry:244-270] guarda metadatos de `Geometry` y proxies de todos los LOD, no caras `Visual`/`Roadway`; [model_geometry:425-438] recorta poses a los rayos. Por tanto, 5509 modelos y 4 poses no son escena completa, ni base para exposición superficial, huella o accesos. El plan lo afirma sin reutilizar B2A como extracción.

2. **Contradicción latente de fase.** La tabla exige “archivo/hash/selector/API real” y “qué bytes se guardaron” para terreno, agua nativa, caras Visual, agua3D, Roadway, poses completas y proxies, pero la misma fase prohíbe abrir PBO/P3D/WRP y caras vanilla. Con índices guardados sólo se puede certificar lo guardado y localizar lo no abierto; no se puede validar el proveedor de caras ni de poses completas. Sin esa distinción, la entrega puede aparentar cobertura que no ha comprobado.

3. **Universo todavía sesgado.** El catálogo reutilizable procede de una selección con `Geometry`. No puede cerrar el universo futuro, en especial agua3D sin `Geometry`, proxies sin pose resuelta y modelos excluidos por esa selección. El plan lo prevé para el contrato posterior, pero la fase actual debe dejar el universo expresamente `UNDETERMINED`, no “inventariado”.

4. **Marco no certificado.** Conservar `raw` frente a `plus_bounding_center`, sin elegir la hipótesis que reduzca exposición, es correcto. Falta fijar que la calibración con el piloto Q04 es una unidad discriminadora previa y separada de la extracción; si Q04 depende a su vez de este contrato, hay riesgo de circularidad.

5. **Riesgo de gate por ausencia.** El resultado `DISCOVERY_FOR_COMPOSED_SCENE_CONTRACT`, con `build_ready=false/map_repaired=false`, es el límite correcto. Sin embargo, una tabla rellena con `UNKNOWN` podría leerse como “descubrimiento superado” y habilitar extracción. Deben separarse dos estados: descubrimiento documentado, aunque tenga huecos, y preparación para extracción, bloqueada si falta una firma crítica.

6. **Presupuesto optimista.** En 120s y 64MiB puede no cerrarse la búsqueda literal de recibos kit118/cont65 más seis capas de fuentes. El plan ya manda conservar huecos, pero no ordena prioridades ni declara que una tabla parcial con huecos anclados es entrega válida y no fracaso maquillable.

**Correcciones mínimas**

- Añadir a cada fila un estado cerrado: `OBSERVED_SAVED`, `LOCATED_NOT_OPENED`, `UNKNOWN` o `CONTRADICTED`, con época histórica/actual y ancla exacta. Sólo `OBSERVED_SAVED` certifica bytes.
- Añadir la regla: cualquier `UNKNOWN` en semántica de agua3D/LOD, proveedor de poses completas, marco o identidad bloquea `extraction_ready`; no existe aprobado condicional por falta de datos.
- Declarar el universo de esta fase como `UNDETERMINED_BY_DESIGN`. Los 5509 son población sesgada de partida, nunca denominador del futuro universo WRP.
- Ordenar la investigación: primero poses/marco y caras Visual/Roadway; después agua3D sin `Geometry`; por último proxies y recibos por ID literal. Al agotarse el presupuesto, parar y entregar huecos, sin ampliar lecturas.
- Precisar que los mutantes (cap lateral fuera del eje, puente omitido/girado/corto, superficie 3D sin `Geometry`, proxy sin pose) son diseño de discriminadores futuros, no pruebas ejecutadas en esta fase.

**Alcance y límites**

Esta unidad no repara lechos, no acepta ningún mapa, no fija alturas ni anchuras, no convierte AABB en área útil y no resuelve los nueve IDs de Q01. Tampoco transfiere el corredor navegable de 24m a todos los cauces ni convierte el antiguo corredor de 8m en huella de piezas de 12/9m.

Su utilidad es preparatoria y real: impide reparar un lecho sólo desde el eje, obliga a considerar exposición lateral, caps, agua3D, extremos y accesos, y prepara para carreteras el contrato de pose, pivote, huella, material y precedencia. La reparación de lechos y el pavimentado/conducción quedan para unidades posteriores con geometría completa del mismo mundo y marco calibrado.
