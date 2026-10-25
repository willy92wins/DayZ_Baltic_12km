# Continuación autónoma: smoothing y render

Petición viva 08-10: «sigue trabajando autónomamente en el plan hasta acabarlo». Base real ae77c9f, mismo worktree; LIVE-STATE inyectado de v29-base anterior. Codex ejecuta e integra. Conservar fuentes y paquetes anteriores; sin subagentes Codex.

## 1. Luga

Los dos fallos nuevos constan en ../v30-luga-navigation-2026-10-07/holdout-diagnosis.json: estaciones5375/6730. No usar estos números para fabricar una máscara. Fuente de interpolación nativa: tools/terrain/v30_common.py:19.

[DESIGN] Probar una restricción general del delta vertical frente al margen original de cada vértice respecto a los planos incidentes: |delta| ≤ 0,5 × mínimo |altura_original − plano|. Aplicarla a todo el candidato anterior y repetir el descarte de caras secas empeoradas. Conserva al menos media separación vertical donde se aproximaba al agua y limita también el ahondamiento de orillas; no garantiza por sí sola cruces de normales. No cambia clases, niveles, sigma ni excepciones geográficas. Revisión independiente de la familia de fallos antes de integrar.

VERDE: mismos dos conjuntos congelados, cero cruces nuevos ausentes individualmente; p90 no peor y zigzag menor en todos los sectores; metadatos, máscara exterior, corredores, Narva, naturaleza y caras ajenas exactos; ninguna cara seca crea/empeora pendiente sobre el límite heredado. Negativos cerrados: candidato anterior rechazado, mutación de cara ajena rechazada, baseline sin smoothing no acredita mejora. Python GIS del proyecto.

Presupuesto: un candidato del mecanismo y una corrección de un defecto reproducible de implementación. Sin barrido de sigma/tolerancias ni exclusiones. Si la familia reaparece, resolver diseño/observabilidad con el revisor antes de otro parche. Continuar trabajos independientes si esta vía queda pendiente.

## 2. Integración

Tras verde local, unir con relieve seco 164ad4ff... solo si máscaras disjuntas; delta exacto contra V12, carreteras y puertas generales sin nuevos FAIL. Constructor ya probado, destino nuevo, inspección del PBO completo y hash desplegado. Arranque, alturas y vistas del candidato. Navmesh antigua no acredita geometría nueva.

## 3. Render

Aparición directa, horario fijo y poses/viewport/foco registrados; zonas de tierra identificadas. Comprobar cerca/media/lejos antes de editar materiales; aislar fallo repetible con una variable. Oscuridad global dominada por agua no demuestra textura ausente; captura estática no demuestra render bloqueado. Solo runs propios por MCP y cierre ordenado.

## 4. Cierre

Conservar navegación V12 6/6 y repetir consumidores si sus caras cambian. Commit propio, evidencias y handoff con PASS/FAIL/INCONCLUSO precisos. Finales de río, agua baja, lagos y navmesh requieren sus consumidores; el smoothing no los cierra automáticamente.
