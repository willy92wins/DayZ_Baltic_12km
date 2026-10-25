# EV112 — controles contra formas artificiales, 25-10

Encargo aprobado por Guillermo: reforzar y ejecutar las pruebas contra figuras geométricas en ríos y terreno. Continúa P2/P14 y ev112-visual-rework-20261023 §Ejecución1/4 y §Criterios de cierre. Codex ejecuta e integra; Fable5.1 por CLI nativo revisa en solo lectura (elección de familia/modelo conservada del council). El HANDOFF del worktree del24-10 es el vigente; el hook del checkout raíz del20-10 es histórico.

## Contrato antes de implementar

1. Ríos: consumir líneas centrales de las piezas realmente colocadas, con sus matrices y sus referencias por SHA. Medir empalmes y discontinuidades de tangente, giros concentrados, rectas largas encadenadas y escalera ortogonal independientemente del norte del mapa. No inferir receptores ni unir ramas por proximidad. Conectividad ambigua/incompleta bloquea aceptación; no ocultarla dentro de un promedio.
2. Terreno: conservar el censo de prominencia nativa y añadir formas anchas/facetadas y bordes rectangulares. Coordenadas, extensión y dominio de cada candidato; incluir protegidos y diferenciar relieve nativo oculto por agua/piloto. Ningún hallazgo concede permiso para cambiar015-45, agua, islas o apoyos.
3. Calibración cerrada: codo en empalme, escalera rotada, recta extensa, ruta cortada, pico, pirámide ancha, terraza rectangular y NaN/vacío deben ser detectados o rechazados. Plano, rampa, meandro suave, arco suave y colina redondeada no deben disparar sus detectores equivalentes. Comprobar invariancia al remuestreo, orientación y división de una misma ruta en piezas. Medidas originales y ejemplos renderizados conservados.
4. Los umbrales nuevos identifican patrones que exigen revisión; no son una ley estética universal. Se fijan y versionan con los controles sintéticos antes de medir producción. `REVIEW_REQUIRED` o cobertura incompleta impiden aprobar. Un caso natural señalado se adjudica con evidencia; no se ajusta un umbral solo para pintar verde el mapa.
5. Ejecutar sobre S3 por SHA y los modelos actuales; preservar R y su historial. Informar cobertura y vacíos. No extender el piloto ni desplegar cambios sin las puertas ya acordadas. Las pruebas de los verificadores y el resultado del mapa son estados distintos.

## Cierre mecánico del lote

Intérprete: C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe, modo -I y worktree handoff-astra-map-review-6d301c. Suite anterior53 más controles nuevos, todos con cero errores/skips; ejecución sobre entradas reales con hashes; imágenes verificables de los candidatos; revisión independiente y contraejemplos concretos resueltos.

Presupuesto: una implementación y una revisión independiente de20min, más una ronda de reparación si aparecen repros del contrato. Parada según gates-ledger §Cuándo para un bucle: producto y contraejemplos mandan, no repetir reviews hasta obtener una opinión favorable. Hallazgos fuera de la lista observable quedan en backlog explícito. Cerrar este lote no declara resuelto el aspecto de todo el mapa.

## Ejecución y alcance acreditado25-10

POLICYv3 y71tests (53anteriores+18nuevos),0fallos/errores/skips. Fable5.1 porCLI revisó en617,62s: SOUND-with-fixes. TresP1 reparados y sus regresiones ejecutadas; adjudicación y límites en el checkpoint `evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/shape-gates-20261025/README.md`.

S3 por los hashes fijados: proceso termina conexit2/REVIEW_REQUIRED en173,89s.51sitios declarados,49construidos;7.606poses de agua/piedras consumidas exactamente.43sitios con hallazgos;42con2.305empalmes89,8grados.143rectas largas y16detecciones de escalera; los scopes pieza/cadena se solapan y no deben sumarse como defectos únicos. Kit-118 y65.0-0 no disparan estos patrones, incluyendo sus delantales de12m.98.0-2 y67.0-0 siguen sin construir.

Terreno4.194.304vértices:366picos,1.157depresiones y5transiciones rectangulares. El ajuste de pirámide cuadrada/diamante no encuentra coincidencias; no equivale a ausencia de facetas ni a aceptación del terreno. Incluye fases de media celda y plano de fondo; deja explícitamente fuera pirámides truncadas, otras formas de facetas y rectángulos fusionados con otro borde.58.207candidatos y59.804parches ajustados. Los dominios son etiquetas en el punto representativo, no autorización para editar toda la extensión.

Las cadenas usan conectores medidos≤0,50m declarados individualmente y solo para analizar patrones. Los extremos diagonales slanted se separan del eje recto medido del cuerpo, conservando diagnósticos brutos. Ninguno de ambos procedimientos prueba silueta de agua o conectividad. Se mantienen las puertas visuales y de motor anteriores. No se ha modificado terreno, modelo, WRP oPBO.
