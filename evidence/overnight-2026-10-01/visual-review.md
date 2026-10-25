# Revisión visual regional V10 — 01-10-2026

Resultado: **aceptación visual parcial**. Los siete grupos completaron sus
12 poses y la restauración de cámara sin reproducir el crash de la transición
distante Narva→SPB. Esto no demuestra que su causa esté corregida.

El mundo permaneció en `d1008dd6…`; no se cambió terreno, agua, material ni
navmesh durante estas pruebas. Cada grupo conserva referencia, identidad del
run, RPT, scripts, telemetría, comprobación y cierre ordenado en
`foundation-visual_g_<grupo>_v1/`. El verificador de telemetría pasó 14 controles
negativos contra el registro real de Narva; no acepta imágenes por sí solo.

| Grupo | Píxeles observados y límites |
|---|---|
| SPB | Las dos primeras capturas fueron negras. Un clic de foco hizo aparecer la escena; `phase2.jpg` muestra golfo, delta y Ladoga. Vista aérea con near-plane de diagnóstico a 10 m. No aceptar las dos tomas negras. |
| Narva | `phase0.jpg`, `phase1.jpg`, `phase2.jpg` muestran acceso, río y puente desde tierra, 180 m y 650 m. No se observa el antiguo mosaico de grandes cuadros azules. Persisten orillas escalonadas y coloración WorldCover provisional. Media distancia usa near-plane original; aérea usa 10 m. La copia de telemetría de la toma terrestre se guardó tarde y no prueba por sí sola su instante exacto. |
| Neva | Registro completo y cliente vivo. La primera observación estuvo dominada por terreno/clutter; el segundo enfoque llegó después de la restauración y mostró cielo. Sin fotograma archivado válido de la lámina de agua: INCONCLUSO visual. El viaje físico completo del Neva sí pasó por separado. |
| Reserva | Se observó contexto terrestre, pero `phase0.jpg` se tomó junto al cambio a la pose terrestre y `phase1.jpg` después de restaurar la cámara. No aceptar ambos nombres como prueba de las poses previstas. Aérea pendiente. |
| Norte | Válidos los fotogramas `09-57-20.023Z` y `09-57-29.223Z`: lomas y corredores visibles, sin grandes discontinuidades de textura en esas vistas. Los dos primeros fotogramas capturaron otra ventana y quedan excluidos. |
| Sur | El proceso permaneció vivo cuando Computer Use dejó de encontrar un destino de captura. Se recuperó una imagen con terreno y menú de pausa; no es aceptación de una vista limpia. No hubo crash. |
| Conjunto | Seis fotogramas reales del juego, pero el terreno queda oculto por bruma a 4.3 km de altura. La telemetría fija posición, dirección y vista solicitada; no acredita distancia efectiva de dibujo ni aspecto del mapa entero. |

Los colores de superficie todavía son provisionales. No hay poblaciones,
bosques densos ni red completa de piezas de carretera colocadas. No se presenta
el clutter automático como vegetación ya mapeada.

## Captura y rendimiento

Los contadores nativos se registraron, pero hubo cambios de foco, un menú de
pausa y capturas de una ventana superpuesta. No comparar sus medianas como
benchmark regional. La exclusión prevista de 23–28 s por pose no cubre todas
las interacciones reales; conservar los datos descriptivos con esta limitación.

No basta que Computer Use devuelva el identificador de DayZ: hay que inspeccionar
los píxeles y vincularlos al intervalo de la pose. Las capturas nuevas del norte
y conjunto guardan registros de cámara antes y después. Las ventanas ajenas
no cuentan como evidencia visual del mapa y no se incluirán en el archivo
complementario de entrega.

Siguiente ensayo visual: empezar con foco y vista normal estables, esperar un
marcador de pose asentada, capturar dentro de su intervalo y comprobar la escena
antes de pasar a la siguiente. Repetir únicamente las tomas pendientes; conservar
los intentos anteriores. No cambiar el heightmap para corregir foco, bruma o
sincronización de una cámara de diagnóstico.

Repetición del Neva a10:24–10:26UTC: misma referencia y mismo mundo. La cámara
completó su pose y restauración, pero Computer Use mostró carga, perdió el
destino de captura y después devolvió píxeles de otra aplicación pese a la
identidad DayZ. No se guardaron esos píxeles como evidencia; control liberado.
El run se cerró ordenadamente y se conserva en `foundation-visual_g_neva_v1/repeat-01/`.
La repetición de reserva quedó preparada sin ejecutar. No cambia la aceptación
visual parcial ni se infiere un crash a partir de un fallo de captura.
