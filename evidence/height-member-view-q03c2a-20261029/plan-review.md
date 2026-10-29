## Veredicto: **SOUND-with-fixes / CONVERGE**

Revisión estática del plan, sin certificar fuentes reales ni ejecutar nada. Contrato y oráculos todavía inexistentes. El rechazo Q03C2 y el cap de 128 MiB quedan intactos.

### Por qué no es una relajación disfrazada

La distinción es legítima si se mantiene literal: el lector nuevo de metadata **observa** la suma declarada de expandidos sin descomprimir auxiliares, sin reservar por ella y sin convertirla en permiso. Solo `heights.npy`, con topes propios previos a toda descompresión (expandido ≤33.570.828 B = 2048×2048 f8 + header 16.384 + prefijo 12; comprimido ≤16 MiB), se materializa. La vista de un miembro es una **identidad nueva y distinta** que vuelve al `Session` sellado sin modificarlo; su suma de un solo miembro pasa el cap porque el objeto cambió, no porque el cap cediera. El resultado `VERIFIED_SINGLE_HEIGHT_MEMBER_VIEW_ONLY` con `whole_source_archive_validated=false` lo declara correctamente. Tampoco se infiere la suma exacta desde `saved_bytes=142613546` (STORED con overhead ZIP), como el plan exige.

La procedencia está bien encaminada: snapshot pinado por SHA-256 `815ef8…`, copia literal del registro local y de los bytes comprimidos, consumidor en proceso distinto que no importa la proyección del productor, comparación byte a byte del NPY y CRC/longitudes propios.

### Vacíos mínimos a cerrar antes de autoría

1. **Esquema NPY no autodeterminado.** Fijar el esquema «descubierto dentro de la ejecución antes de `Session.open`» es circular: el miembro no puede dictar su propio esperado. Debe pinarse antes de leer, desde fuente independiente, el `descr` exacto o el conjunto cerrado {f4, f8} pre-declarado, con shape 2048×2048 y orden C. Lo descubierto solo se compara; si no hay ancla externa del dtype, parar.
2. **Espejo completo de `_central` para *todos* los miembros en el lector de metadata.** Rechazar `0xffffffff` en cualquier campo central de tamaño/offset, extra o comentario central no nulos, disco, y EOCD que no cierre exacto en EOF. Sin esto, la «suma observada» podría sumar centinelas ZIP64 como si fueran tamaños. Recorrer además los registros locales de las 28 filas en orden, contiguos de 0 al offset central, no solo el del miembro elegido; la suma se reporta como `declared_expanded_sum_observed`, nunca como validada.
3. **Descriptor de datos y copia central.** Exigir flags dentro del subconjunto sellado y rechazar el bit de data descriptor, o la copia del registro local quedaría truncada frente a la congruencia local/central. En la vista, copia central idéntica salvo offset=0, extra/comentario en cero, y EOCD reconstruido con conteo 1 y offset/tamaño recalculados.
4. **Identidad sin TOCTOU.** Un único snapshot en memoria: se hashea y se parsea el mismo objeto bytes. El recibo liga SHA/tamaño de la vista; el consumidor la re-hashea antes de usarla. Si `Session` solo acepta ruta, hashear antes y después y contrastar el SHA del payload NPY con el calculado independientemente; cualquier inestabilidad es rechazo.
5. **Contabilidad explícita.** Comparación del NPY en streaming por chunks de 64 KiB sin retener el expandido completo; declarar por proceso snapshot ≤16 MiB, vista ≤16 MiB y array ≤32 MiB bajo el cap de 256 MiB, reconociendo que es presupuesto del ejecutor, no garantía sobre asignaciones internas de zlib/NumPy.
6. **Recibo completo.** Debe incluir: suma declarada observada rotulada como tal, filas completas, offsets local/central de heights, SHA de bytes comprimidos, CRC, tamaño expandido, SHA del NPY, header observado y SHA/tamaño de la vista.
7. **Dos negativos más en fixtures:** vista con NPY idéntico pero recomprimido (debe fallar por procedencia, no por contenido) y auxiliar con centinela central ZIP64 (debe fallar, no contarse como 4 GiB declarados).

### Condición de convergencia

Con los fixes 1–3 y 7 incorporados al contrato antes de escribir código, el plan converge en una sola lane sin reejecutar Q03C2 ni la extracción antigua. Si el dtype de heights no puede pinarse independientemente (fix 1), el estado pasa a NEEDS-WORK y no debe autorizarse la ejecución.
