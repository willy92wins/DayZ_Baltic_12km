# EV112 — corrección local verificable, 25-10-2026

**Avance parcial; EV112 continúa abierto.** Fuente S3 inmutable. 79 tests, cero fallos/errores/skips. GitHub público: https://github.com/willy92wins/DayZ_Baltic_12km (historial público saneado independiente; ver PUBLICATION.md).

## Relieve

`terrain-free-final` corrige los 43 vértices señalados que admiten intervención en el dominio seco libre. 905 alturas cambian, como máximo0,75m, mediante una superficie suave de 24m alrededor de los defectos. La solución impone cotas, prominencia, pendiente de cada triángulo y ángulo entre caras vecinas. Se verifican los valores float32 guardados con los consumidores independientes.

- Resultado global del detector congelado: **366→327 grupos de picos**, **1157→1157 depresiones**, **5→5 transiciones rectangulares**. No se ocultan los casos protegidos ni se llama PASS global a esta reducción.
- Sin nuevos picos/pozos ni empeoramiento de los existentes; ninguna nueva arista >20° ni empeoramiento de las preexistentes >20° (tolerancia de comprobación0,01°). El ángulo es un límite de no regresión, no una aceptación estética universal.
- Orillas nativas exactas; clasificación visual seca/mojada exacta; mar exacto; islotes y protecciones conservados. Se permite alisar135 esquinas secas interiores de celdas de estanque. **La regeneración completa demuestra igualdad exacta de env_plane, plane, field y visible**, sin correcciones de bury.
- Carreteras:77.559 secciones y130.534 intervalos nativos; cero fallos. Transversal máxima0,0295013m, pendiente nativa máxima0,0645519. No implica carreteras físicas ni conducción aceptadas.
- WRP fuente preparado:2.578.822 objetos;989 ajustes exclusivos de Y en vegetación, comprobados con interpolador independiente; todos los demás bytes de objetos se conservan. No cierra el problema previo de discos del bosque en los bordes.

Entradas/resultados completos bajo `E:/DayZ-Baltic-Build/shape-repair-20261025`:

| Artefacto | SHA256 |
|---|---|
| S3 terreno | `6a081028120778d3821574878d4b3845f419c411e661a97d1dc17f3440a4c8a1` |
| Final después de bury | `82e0f1ca5fb102ec4109adac8095819f9b060730e5750c9593eb6e1a86461761` |
| WRP fuente con relieve corregido | `7945e4cc5c191501f616bbce4f59ee77a89dc91bc55d0bab503631e7c84edd29` |

El delta reproducible de905 vértices está versionado en `terrain-delta.npz`; los builds grandes permanecen fuera de Git. Este WRP aún requiere compilación y prueba en motor.

## Río131.0-0

Candidato continuo independiente de314,5m sobre el cauce original. Sustituye el trazado en escalera y conserva ambos extremos.27 modelos nuevos; sin codos/escaleras en los dos ámbitos del detector; sin pliegues ni solapes de lecho, sin aristas visibles >20° en el diagnóstico muestreado.

MLOD y PBO pasan agua conectada, extremos y colisión cerrada. El binario coincide con los vértices fuente; juntas3D exactas. PBO`3c4f3fa6d7942149f47d6440062818da9aa0a80fc9abebd7172603402bb7a7e6`,4.888.069bytes. **Aún separado del WRP; sin sonda ni aceptación visual.** El comprobador se ha corregido para rechazar que el terreno base sustituya accidentalmente al soporte autorado; el informe nuevo registra el hash real revisado.

**Coste que impide extender todavía esta representación:** el kit anterior usaba169 componentes de colisión colocados; el candidato usa25.156 (148,85veces). Es un recuento estático, no una medida de FPS, pero exige reducir la geometría de colisión y medirla antes de multiplicarla por el mapa. La malla visual y la carretera de agua pueden conservarse mientras se investiga una descomposición convexa más compacta.

48.0-0 permanece rechazado: nivel1,65m frente a techo de apoyoW−0,85m y suelo mínimo1m; las cotas son incompatibles. No se bajó el fondo al mar ni se elevó el agua para forzar PASS. Confluencias, receptores no naturales y sitios vecinos requieren soporte conjunto; el generador los rechaza.

## Revisión y contraejemplos

Fable5.1, CLI nativo, solo lectura: `SOUND-with-fixes`. Reparados la falta de vínculo del terreno revisado y la conectividad diagonal entre parches. La partición de34 parches del candidato no cambia con la corrección; se regeneró y volvió a comprobar.

Además, el censo independiente encontró3 aristas peores en el candidatoB, que pasaba prominencia y pendiente. B se conserva como **rechazado**. Se añadieron restricciones de ángulo y pruebas contra el consumidor nativo, incluida una pirámide inyectada y Jacobiano contrastado por diferencias finitas. C/final cumple. La revisión de Fable sobre B no sustituye estas comprobaciones posteriores.

Los tests también rechazan terreno base en vez del candidato, referencias viales vacías/no finitas, finales de estanque/carretera/puente tratados como naturales y pérdidas de esquinas de soporte vial. `MANIFEST.json` fija los48 artefactos originales del checkpoint.

## Pendientes

Corregir/adjudicar327 picos,1157 depresiones y5 transiciones; continuar los ríos restantes y los dos sitios sin construir; optimizar la colisión continua antes de extenderla; integrar y medir el nuevo piloto; compilar/sondear el nuevo WRP; bosque de borde, navmesh, conducción y comparación A/B con Chernarus.015-45/60m sigue pendiente por decisión explícita. La aceptación visual se hace con Guillermo.

25-10,11:45UTC aproximadamente: DayZ1.30 tenía lease de Claude para LFSkateboard; esta sesión solo consultó estado, sin adquirir lease ni gestionar procesos ajenos. El helper preflight tiene un SyntaxError en su literal Windows; P:, recursos y AddonBuilder se comprobaron directamente. El build aislado terminó correctamente. No hay proceso DayZ propio que cerrar.
