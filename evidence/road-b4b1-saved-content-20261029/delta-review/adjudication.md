# RoadB4B1 delta y cierre de integración

Fable 5.1 nativo 124.422 s, SOUND-with-fixes. Cinco correcciones aceptadas:
1. Productor y consumidor rechazan tipos históricos inválidos antes del reporte.
2. Los nombres fuente inválidos ahora rechazan todo el snapshot con source_id/índice/motivo; se elige fallo cerrado explícito, no descarte silencioso ni heurística de cercanía.
3. Se recorren los seis oráculos de agrupación y los tres históricos. El oráculo vacío UNRESOLVED sólo clasifica agrupación; la historia R2 inválida tiene prioridad MALFORMED, conservando literal y contrato.
4. Se elimina el test que sólo verificaba fixture inválido; queda el que invierte índices y resuelve el pointer contra la fuente.
5. Los bindings se prueban por omisión y por SHA válido distinto.

Integrador Codex añadió serialización incremental con cap previo a retención y negativo antes de crear salida. No se cambió contrato, fuente histórica ni tolerancia. Suite final 24 tests PASS, 1.922 s; no skips. Revisión de integración con contexto compartido, no lane ciega ni consenso nuevo. Reconstrucciones separadas, algoritmo similar y librería IO compartida; no afirmar diversidad conceptual.

Estado REVISADO_PARA_DERIVACION_GUARDADA_UNICA. R2 263a2bfc/oráculos596c8158. Todavía sin resultado real. Una derivación 30 s/256 MiB y un consumidor guardado 30 s/256 MiB; no WRP/PBO/P3D/DayZ ni bucle de reintentos. Si falla, conservar causa/streams y no promover.
