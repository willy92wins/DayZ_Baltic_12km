# EV93 preflight final review — 2026-10-10

**Dictamen:** READY_PILOT. No implica factibilidad global, factibilidad acoplada ni aceptación de geometría.

## Anclajes revisados

- Preflight congelado: `preflight/ev93_preflight_windows.py`, SHA256 `a5a8537fa8b9caf092d6ba7b3d55f1f168f15e3541c242cdcc288065cb40c1cc`.
- Fixtures congeladas: `preflight/test_ev93_preflight_windows.py`, SHA256 `7f4fad61b64df64cb1091d8b0ace13cf0f125f4cd14fdea80ec2548961bbefde`.
- Índice: la ejecución requiere el informe independiente PASS fijado por hash y run/manifest exactos; el reporte debe concordar en conteo de caras, LOD, objetos, modelos y muestras. El piloto y el batch vuelven a verificar el informe, manifest y fuentes.
- EV91: `prepared.json` queda fijado en `PINS` y su hash se lleva al recibo/header; el guard y autoría ya estaban fijados.

## Cambio final y semántica

El delta final respecto a la revisión anterior añade `free_count` al resumen D8 y clasifica una ventana como `PREFLIGHT_INFEASIBLE` cuando `free_count == 0` (`ev93_preflight_windows.py:167-177, 339-342`). Esto es correcto: aunque el test de caja separable encuentre intervalos/prominencia admisibles, si el guard fija todos los nodos B no queda ningún grado de libertad para el piloto. No convierte la caja en prueba acoplada; el plan conserva explícitamente ese límite y los estados `READY` solo habilitan revisión del integrador.

La auditoría de caja también retiene los nodos con intervalo vacío, los nodos cuyo B float32 queda fuera de la caja inward y el caso sin variables. Los detalles por ventana quedan en sidecars enlazados por hash; errores no cuentan como ventanas completadas. Estos resultados son de preflight, no de solver.

## Verificación

Con `C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe`, `--fixtures` pasó 11/11, incluido `no_free_variables_infeasible`; `py_compile` pasó. No ejecuté piloto, batch, solver ni autoría. El cambio no permite concluir factibilidad global: solo clasifica sin libertad restante un dominio local.
