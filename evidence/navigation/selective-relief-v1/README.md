# Propuesta de relieve selectivo

Decisión de producto P12 aprobada el30-09: exagerar Z localmente por jugabilidad,
incluso por encima de×3. Cotas y elipses de este plano son [DESIGN].
El usuario acepta la propuesta como punto de partida y añade P13: conservar
la reserva natural, núcleos de árboles muy densos y varios biomas. Envolvente
verde conservadora; perímetro real todavía por contrastar, no límite legal.

`zonificacion.png/pdf` superpone áreas de estudio sobre el relieve fuente×3;
no representa el aspecto del candidato nuevo ni una captura del juego.
`design.json` separa estadísticas medidas, objetivos propuestos y hashes.

Medido en las celdas excluidas de agua/humedal por los rásteres de referencia:

| Área | Máximo fuente×3 | Crestas propuestas |
|---|---:|---:|
| A, interior al oeste de Gatchina |29,4543m|80–140m|
| B, sur entre Peipus y Luga |32,5857m|100–160m|

Esto no acredita que todas esas celdas estén secas en motor. Los hitos aislados
de180–200m son opcionales; no un mínimo de todo el interior ni un nuevo límite
global. Fuentes de agua y el encuadre se conservaron por hash antes/después.

Reproducción: ejecutar `tools/navigation/plan_selective_relief.py` con el Python
GIS fijado por el proyecto. No descarga datos ni modifica ASC, WRP, PBO o navmesh.
Plan y criterios: `../../../plans/selective-relief.md`.
