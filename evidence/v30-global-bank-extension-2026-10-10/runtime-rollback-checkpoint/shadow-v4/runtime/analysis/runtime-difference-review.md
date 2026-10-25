# V4 A/B/A: revisión de actividad y contraste de sombras

**Veredicto: INCONCLUSO para atribuir el cambio a sombras; no hay evidencia de una captura pixel-idéntica/congelada.** Los cuatro JPEG tienen hashes distintos y las capturas temporales informan 3/3 o 5/5 frames distintos. Aun así, el recibo marca `render_frozen_signal` en todas las fases y `max_adjacent_delta` está entre 0.000444 y 0.000505. `frame_stale=false` solo indica que la ruta no repitió el mismo frame; no acredita avance normal de la simulación/render.

## Procedencia y método

- Run/recibo: `runtime-receipt.json`, SHA-256 `0b961d635bbaaf477d3bd37f48f0dded103fad108902524799f979b56213df78`; log `probe.log`, SHA-256 `14da30e21b62116f8c23171bee5e7748d841c2e52c5e389cab4d89b1935f674e`.
- Orden: A(Shadows=0), A2(0), B(1), A′(0). El control `Terrain shadows` id 163 quedó en 0. El log registra readback 0→1 y restauración 1→0. Resolución entregada: 1920×1080.
- Cámara final leída: posición `[2417,65,6745]`, matriz/dirección coherentes con el encuadre del experimento. El campo FOV leído es 0 y no sirve como readback de FOV real; tampoco se guardó readback de cámara por cada captura. No afirmo identidad perfecta de pose entre fases.
- Comparé los JPEG originales sin reescribirlos. `compare_captures.py` calcula diferencias RGB (máximo absoluto de canales por píxel), luminancia firmada y correlación entre los cambios A2→B y B→A′. ROIs fijadas en coordenadas cliente antes de comparar; son rectángulos manuales, no máscaras semánticas.
- Script: SHA-256 `da79578caa50954bf9e79f692a860db84c703d8f913d4094f49a1b2e9ee853ea`. Salida: `pixel-difference-analysis.json`, SHA-256 `9d0fe3bb5241c398ac234d43dc57c4363e50bd984c1588e28eb462b7dbd42e81`.

Capturas y hashes:

| Fase | Archivo | SHA-256 | Frames distintos | `max_adjacent_delta` |
|---|---|---|---:|---:|
| A | `capture_20261010_214102_468.jpg` | `bac269e5a9ee6c51c496b6b80d507292b5f47d5f97a29df6b1ac60538847809e` | 3/3 | 0.0004440 |
| A2 | `capture_20261010_214130_034.jpg` | `441c1e3e326b5286d6ea9a6498ef746b9e924e9652de45a58b7030501abc4bfb` | 5/5 | 0.0005055 |
| B | `capture_20261010_214159_815.jpg` | `2f729cecd08d8c7e2c41a7ad570a7dc5ef730d56ab9783cde8e2e7770e7891ea` | 5/5 | 0.0005037 |
| A′ | `capture_20261010_214217_191.jpg` | `0e2d255de900d559377fb88702e03cdc787592a4e4ba70dac918775e6d75d611` | 5/5 | 0.0004852 |

## Diferencias observadas

La ROIs relevantes son `midwater_rect_patch` (x=900–1015, y=450–515), `near_channel_water_control` (120–500, 790–1010), `bridge_and_piers` (500–1515, 515–645), `under_bridge_shadow_candidate` (500–1515, 600–735) y dos controles de terreno seco. Los píxeles de agua cambian claramente entre capturas, pero el control temporal también cambia casi igual:

| ROI; media de diferencia RGB máxima | A→A2, 0→0 | A2→B, 0→1 | B→A′, 1→0 | A2→A′, 0→0 |
|---|---:|---:|---:|---:|
| Parche de agua rectangular | 1.506 | 1.616 | 1.756 | 1.506 |
| Agua cercana | 1.738 | 1.926 | 2.046 | 1.767 |
| Puente y pilas | 0.795 | 1.437 | 1.498 | 1.039 |
| Terreno seco izquierdo | 0.0009 | 0.0337 | 0.0376 | 0.0699 |
| Terreno seco derecho | 0.0777 | 0.1127 | 0.1284 | 0.1490 |

Las variaciones de puente son mayores en las transiciones de ajuste que en A→A2; además, los mapas de luminancia A2→B y B→A′ son parcialmente anticorrelacionados en puente (`r=-0.781`) y agua (`r=-0.62` a `-0.66`). Eso es compatible con un efecto reversible, pero no lo aísla: el control de retorno A2→A′ también acumula diferencias sustanciales en puente (media 1.039) y agua (1.506–1.767), y el agua tiene variación temporal propia. JPEG, posibles pequeñas diferencias de pose/exposición/fog y ausencia de un control positivo visual impiden atribuir la señal a id 160.

La referencia EV74 (`v30-water-rectangles-detail-20261009/summary.json`, SHA-256 `6c008f04a08f7b15931c77d99cb0c6bed137ffef7b53c5344e0242c3913a4e0e`) conserva el mismo encuadre solicitado y documenta que el rectángulo siguió visible al cambiar detalle del agua; su propio límite dice que no descarta todos los mecanismos de culling. Es evidencia de persistencia visual entre aquella prueba y esta, no una comparación pixel a pixel ni una prueba sobre sombras.

## Qué permite concluir y siguiente discriminador

1. **No está congelada la ruta de captura** en el sentido de repetir una imagen idéntica: las superficies/hashes y todos los JPEG difieren. La señal temporal es pequeña según la métrica del probe, así que no se demuestra que el render/animación avance normalmente.
2. **El estado de Shadows cambió y volvió**, según readback; `Terrain shadows` permaneció apagado. No hay control positivo de sombra visualmente confirmado. La señal localizada del puente es sugestiva pero queda al nivel de correlación.
3. **No hay efecto de sombras demostrado** sobre los rectángulos de agua ni una explicación de su mecanismo. El contraste de agua se solapa con la variación de las fases 0→0; no atribuirlo al shader, culling, iluminación o al agua dinámica.

Si hace falta un discriminador adicional, el mínimo útil sería una sola secuencia A/A/B/A′ con cámara, tiempo/clima fijos y una ROI seca de borde de sombra cuyo cambio al activar id 160 se confirme visualmente como control positivo, manteniendo id 163=0. Comparar su respuesta reversible frente a un control seco fuera de sombra y conservar el control A→A para ruido temporal. Si no se puede verificar ese control positivo en el propio frame, la secuencia seguiría siendo inconclusa.
