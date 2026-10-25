# Calidad de F y colisión C — 25-10-2026

La colisión C supera **4.749 controles nativos y la rejilla adicional de 300 rayos**, sin fallos. Mantiene 25 piezas optimizadas y restaura exactamente las dos piezas U2 donde B falló; las otras 35 piezas anteriores también son byte idénticas. Agua, terreno, poses y LOD visuales conservados. No es una aceptación visual/global de EV112.

| Ámbito | Resultado medido | Límite |
|---|---|---|
| Río 131, colisión C | 1.449 componentes frente a 2.245 de U2; 45.470 caras frente a 53.854; 25.633 vértices frente a 31.417. Overlay compilado y 4.749 + 300 puntos PASS. | No equivale a FPS, CCT, navegación ni extensión a otros ríos. |
| Bosque F | 3.727 árboles, 269.968 consultas; cero fallos de raíz, soporte o agua en las muestras. Error máximo de raíz 0,00005752 m. | Todas las raíces listadas medidas; apoyo/margen muestreados, sin aceptar el disco continuo ni el bosque global. |
| Carreteras F | 187 puntos sobre las 11 secciones antes fallidas, máximo transversal 0.02950 m frente a límite 0,03 m. | No valida conducción, colocación de todos los objetos de carretera ni el censo entero. |
| Navegación E | Las 37 rutas anteriores y 8 nuevas: 45 PASS. | E es referencia; no demuestra navegación F. |
| Navegación F | Generación FAIL al 63 %, sin archivo NM válido. | El servidor terminó ordenadamente unos 60 minutos después de arrancar; causa no aislada. No se atribuye a la caducidad posterior del lease. |
| Pruebas de herramientas | 225 PASS; controles negativos de geometría/contacto y revisiones Fable5.1. | Los tests no sustituyen las sondas del motor. |

## Evidencia y rechazos conservados

- `collision/runtime-c-full/result.json` y `collision/runtime-c-grid/result.json`: resultados C; `runtime.log.gz`, manifiestos y capturas de identidad vinculan PID, creación, misión, ejecutable real y PBO. El run completo recuperó su propio lease sin relanzar; `lease-recovery.json` lo registra.
- `collision/runtime-full` y `collision/runtime-grid`: B rechazado (1/4.749 y 13/300 fallos). A queda rechazado por cambio de pose. Ningún umbral ni punto se desplazó para aceptar C.
- `collision/c/compiled-contact-review.json`: unión completa empaquetada en poses F; controles negativos de hueco y exceso de altura. Este gate offline no detectó el fallo nativo de B, por lo que se exige además motor.
- `reviews/midpoint-c-review/resolution.json`: los 4.749 puntos son idénticos a B; cambia exclusivamente la metainformación de rutas y hash del paquete. Registra procedencia de la copia de poses y errata textual del recibo inmutable.
- `forest/result.json`: sonda nueva completa. Se corrigió el lector de booleanos nativos `true/false`; `forest/boolean-fix` conserva el negativo anterior y la corrección.
- `roads/runtime/result.json`: misma XZ/orden de secciones; expectativas de altura recalculadas sobre F. Se probó el mundo F con piloto B, no se etiqueta como una nueva prueba de carretera sobre C.
- `nav/e45` y `nav/f-failed`: referencia de 45 rutas y generación F fallida. Los ocho recorridos locales se congelaron antes del motor; el gate compara los caminos devueltos, no solo sus extremos.
- `rivers-next/79-bounds-report.json`: diagnóstico, sin candidato, con 244 incompatibilidades entre suelo mínimo 1 m y techo de soporte ~0,8 m. No se alteran las protecciones para continuar.
- `tests`, `reviews`, `source` y `executed-source`: pruebas, revisiones y bytes exactos ejecutados comprimidos. `MANIFEST.json` fija cada archivo; no se incluyen PBO, assets vanilla ni credenciales.

## Identidad y alcance

Mundo F `4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38`; piloto C `c7dc430d809bcec2f29ff1fe86f266f0f9680b8ad676a8722b0b45d4494de02f`; agua `97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43`. Mod aislado `@DayZ_Baltic_EV112_MidpointC`. Sondas físicas en modo data-server, sin cliente. Todos los runs propios de esta unidad se cerraron y liberaron; recibos por run.

La reducción máxima de casco 102/200 → 72/140 se compara con U2 efectivo; compact-a ya tenía 72/140. La reducción de componentes no acredita una mejora de rendimiento en juego.

Quedan 268 picos, 1.144 depresiones y cuatro transiciones del censo, otros cauces angulares y finales, la excepción protegida de 60 m en 015-45, navegación correspondiente a F/C, conducción, actores y revisión visual. La comparación de RAM con Chernarus publicada antes pertenece a E + Nav9: no se traslada a F/C.
