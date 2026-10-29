## Dictamen: SOUND-with-fixes / CONVERGE

El binding vista certificada → caminantes mantiene el alcance si se cierra en el contrato geométrico, todavía inexistente, antes de cualquier código. No requiere otra revisión del delta.

### Verificado en el delta

- El original `815ef8` no se reabre, no se reinterpreta su rechazo `ARCHIVE_CAP`, y no se relanza la proyección/consumo Q03C2A. La vista `16873c` es un artefacto nuevo, con copia literal del único registro `heights.npy`, y su certificación se limita a procedencia, NPY/CRC y límites sellados. Nada atribuye finitud, triangulación compilada, exposición ni geometría a índice/headers: la finitud la comprueban ambos caminantes al decodificar.
- El alcance sigue siendo medición, no infraestructura: adaptador mínimo sobre la entrada de terreno, helpers sellados sin editar ni relanzar, nueve áreas exactas por cara, dos caminantes independientes que recargan vista y 201 pilotos pinados por sí mismos, sin datos transmitidos entre procesos.
- Se conservan presupuestos por cara y caminante (4096 bits/100000 ops/1024 fragmentos/8192 vértices, rectas y celdas vivas incluidas, sin reinicio por celda ni omisión de área para PASS), resultado máximo `MEASURED_SOURCE_TERRAIN_SELECTED_WATER_ONLY`, y `FULL` sólo con 1520 particiones verificadas. Los nueve rechazos humanos y `C1 NOT_REVIEWED` quedan intactos; no se pide permiso de producto ya dado.

### Fixes obligatorios antes de código

1. **Pins completos, no prefijos.** El contrato geométrico fijará con SHA-256 completo y ruta canónica: contrato Q03C2A, reporte productor, `consumer.json`, recibos de completion de ambos procesos, aprobación, fuentes finales y vista. Debe declarar precedencia del consumidor `VERIFIED_SINGLE_HEIGHT_MEMBER_VIEW_ONLY` sobre el estado `UNVERIFIED` de la captura, exigir `fixture=false` y claims limitados en falso, y cruzar vista/NPY/payload/registro local/CRC/header (`16873c…/3d4280…/34c3c5…/0f7369…/ab00e7…`) como defensa redundante sobre el SHA de la vista.
2. **Rechazo del original ejecutable.** Presentar el original `815ef8` como entrada debe rechazar por pin tras stat/hash, antes de abrir ZIP o decodificar arrays. Sólo la vista canónica puede abrirse como ZIP, con exactamente un miembro.
3. **Contabilidad de sesión sin ambigüedad.** El contrato definirá si cada cota es por archivo o acumulada por sesión, con tabla calculada vista + 201 pilotos dentro de los 262434599B totales. «35 miembros» queda como cota, no como expectativa: la vista espera exactamente 1. El pico retenido de 64MiB contará buffer de descompresión, bytes NPY, array `<f4` de 16777216B y geometría seleccionada antes de copiar; el array se retiene en f4, sólo esquinas seleccionadas pasan a racional exacto, sin cuadrícula f8 ni Fraction completa. Si total o RSS (512MiB por caminante) no cabe, rechazo sin ampliación.
4. **Oráculos por referencia intacta.** Los literales del plan original se incorporan por hash/identidad sin re-derivarlos ni sustituirlos por el resumen del delta; los esperados no proceden de ningún caminante. Todo rechazo conserva código y testigo concreto.

Con estos cuatro cierres dentro del presupuesto ya adjudicado de contrato+autoría (900s), la revisión de código de 180s posterior —que incluye contrato y oráculos— basta. No hay LOOP: una corrección cerrada de 180s es el único retorno previsto.
