**Dictamen (READ ONLY, una lane; Codex valida e integra)**

## 1. Hechos y censo verificados

- Censo v2: las cifras del encargo coinciden con `kit7-nav-payload-cost-20261027-v2/result.json` (Nav8 2 359 296 teselas, 3 916 960 polígonos, 1 996 338 de un polígono, 897 066 212 B en ellas, 1 338 007 300 B totales; 12,5 m 966 289 / 2 446 651 / 709 675 / 704 535 052 B; 12 m 1 048 576 / 741 138 936 B; Chernarus 94 249 / 640 312 416 B; cero teselas con 0 polígonos en los cuatro). El script valida hash por artefacto (`census_kit7_nav_payload_cost.py:47`), offsets estrictamente crecientes (`:21`), unicidad y cobertura completa de coordenadas (`:30`, `:38`) y que la contabilidad suma los bytes del archivo (`:48`). No veo cifras falsas. Dato adicional no citado: Nav12 declara 2 525 023 polígonos, más que 12,5 pese a tener 8,5 % más teselas.
- RAM: 12,5 m PASS 0,832329 / 0,844646, dispersión máx. 0,17 %, `acceptance_eligible:false`, alcance diagnóstico con cuatro FAIL preservados (`kit7-navv9diag-ram-ab-20261027/comparison.json:25,48,102-103`). Nav8 FAIL 1,265913 / 1,241333 (`kit7-nav8-ram-ab-20261027/comparison.json:25,48`). Mismos exe/config/misión entre bloques (`kit7-ram-cross-block-conditions-20261027.json:2`); el PBO de mundo difiere a propósito.
- Chernarus actual: 49 consultas, 48 comparables, NONE PASS, 17 excesos, máx. 5,595824, 0 puntos elevados (`chernarus-nav-height-reference-20261027/result.json:9-15`). Diferencia de fuente Y declarada (`:4651`). Sin exención Baltic.
- Reconstrucción Nav12: residuo nativo máx. 5,6e-7 (`kit7-nav12-height-reconstruction-20261027/result.json:3`). El vértice de esquina (9132, 2,07, 11280) está compartido por los polígonos de las cuatro teselas (`:83-86`, `:123-131`, `:184-188`), y cada tesela tiene 1 o 2 polígonos de 3 a 4 vértices sobre relieve de ~1,6 m. El límite `:306` sigue vigente: no se aísla cómo el generador partió o simplificó.
- Screen fino: 10 m da máx. 0,867578 con 1 507 984 teselas y `grid_side 1228` (`kit7-nav-fine-width-diagnostic-20261027/result.json:815-818`); estado PLANNING_ESTIMATE_ONLY (`:2`). El propio archivo advierte que no modela partición ni obstáculos (`:1795-1796`). Dado que 12 m predijo 0,785 (`:1628`) y falló 3, ese 0,868 no es evidencia ni a favor ni en contra.

## 2. ¿Permite el PASS RAM de 12,5 un candidato 10 m motivado por coste y alineación?

No con honestidad, por tres razones independientes:

1. **Coste.** Solo hay dos puntos RAM de la familia kit7 (966 289 teselas PASS 0,83; 2 359 296 FAIL 1,27). Situar 10 m (1,51 M) "dentro de la ventana" exige la interpolación lineal teselas→RAM que el plan prohíbe (`plans/ev112-kit7-nav12-cost-20261027.md:40-42`) y que el censo no autoriza (`result.json` límites, `census...py:52`).
2. **Alineación.** La única "alineación" conocida es un hecho local: el vértice forzado en (9132, 11280) cae en el cauce. Para 10 m las líneas son x=9130/9140 y z=11280: comparte la línea z=11280 con 8 m y 12 m, y sus esquinas (9130,11280) y (9140,11280) no tienen altura física medida. No existe dato independiente que diga que 10 m evita el cauce en 116 y, además, en 124 y 133 y en los demás ~300 emplazamientos de las 607 consultas.
3. **Contrato.** 10 no divide 12 288. El screen asume `floor` (1228 teselas = 12 280 m) mientras el generador real produjo 983 para 12,5 (12 287,5 m). Cómo cubre el generador el borde con 10 m es LO_NO_VERIFICADO; el inspector solo admite 8/12/12,5/25/50 (`tools/navigation/inspect_navmesh_v9_ev112.py:16`, `:88`) y comprueba límites de tesela como `x*width` (`:62-63`), sin comprobar cobertura total del mundo. Aceptar 10 m exigiría ampliar el inspector a una dimensión cuya cobertura no está definida.

Conclusión: elegir 10 m hoy sería una serie ciega de un elemento. El discriminador que falta es geométrico: una regla que, dada una anchura, diga qué consultas corren riesgo, y que haya sido comprobada contra las tres mallas reales que ya existen.

## 3. UN experimento: retrodicción offline del discriminador rejilla–cauce

**Qué.** Construir y someter a falsación, sin servidor ni generación, una regla R(w) basada en geometría conocida: para cada extremo de las 607 consultas (los waypoints nativos son los dos extremos, índices 0 y 1 en todos los registros), localizar los puntos de rejilla múltiplos de w dentro de la tesela que contiene el extremo, evaluar en esos puntos la altura física (Roadway de la pieza transformada, con el mismo diagnóstico de capas ya usado para la esquina 9132/11280) y marcar riesgo cuando la diferencia entre la altura física de la esquina y la del extremo supere 0,801 o un umbral fijado ANTES de correr. R(w) se evalúa en w = 8, 12 y 12,5, para las que existen malla real y resultado nativo completo.

**Por qué este y no otro.** Es la única medición que convierte el "alineación decide" de la revisión anterior de hipótesis en criterio comprobable, usando únicamente datos ya archivados (mallas por hash, CSV de consultas, LOD de la pieza, transformaciones de las piezas). No repite RAM ni Chernarus ni genera nada. Su valor es asimétrico y útil en ambos sentidos.

**Criterio de parada, fijado antes de ejecutar.**
- R retrodice los 7 waypoints fallidos conocidos (3 de Nav12, 4 de 12,5) y no marca ninguno de los ~1 214 extremos que Nav8 pasó con margen >0,30 m: **discriminador validado**. Entonces, y solo entonces, se aplica R a anchuras entre 8 y 12 que dividan 12 288 o cuyo comportamiento de borde esté verificado, y se escoge la de menor número de teselas con cero marcas. Una sola generación, con sonda completa 607 y después 6 pasadas ABBAAB, presupuesto 1,10, dispersión 5 %. Antes de desplegar, screen offline de altura con la interpolación de abanico ya demostrada (`reconstruction...result.json:3`), extendida a los 1 214 extremos; si marca excesos, no se despliega y el dato se conserva.
- R falla en cualquiera de los 7 o marca falsos positivos en Nav8 por encima de lo tolerado: **la anchura de tesela queda cerrada como eje ciego**. Nav8 funcional + FAIL RAM y 12,5 PASS RAM + 4 FAIL altura quedan como registro; el siguiente paso es decisión de alcance de producto, no otra generación.
- Datos de entrada incompletos (p. ej. transformaciones de alguna pieza no archivadas): INCONCLUSO, no se sustituye por estimaciones.

**Riesgo y qué no garantiza.** R ignora la partición interior del generador (vértices como 9137,9 / 11283,7 en `reconstruction...result.json:118,197`), obstáculos y cuantización. Validarla en 3 mallas no prueba que prediga una cuarta; por eso sigue mandando la sonda nativa y no se hereda PASS. Tampoco dice nada de RAM: la generación elegida puede fallar RAM, y ese resultado se conserva sin repetir.

**Presupuesto previo.** Un script offline con `-I`, lectura por hash de las tres mallas y del CSV congelado, tests positivos/negativos (esquina 9132/11280 debe marcar; extremos de Nav8 con margen amplio no deben marcar), una revisión del plan. Cero servidor. Solo tras VALIDADO se autoriza una generación (≤18 000 s, `generate_navmesh_console.py:48`) y un bloque RAM.

## 4. LO_NO_VERIFICADO

- Si la reconstrucción de las mismas cuatro teselas en Nav8 (prerrequisito 3 de mi revisión anterior) se ejecutó; no está en las fuentes de esta lane.
- Comportamiento del generador con anchuras que no dividen 12 288 (borde, última fila/columna).
- Contenido del `remaining_payload` por tesela (no decodificado, `census...py:52`); no se infiere nada de RAM de él.
- Alturas físicas de las esquinas de rejilla de 8 m y 10 m junto a 116/124/133.

No propongo editar la malla, mover consultas, tocar cellSize ni rebajar 0,801/0,011/2,1. Nav8 sigue funcional con su FAIL RAM registrado.

FIN_REVISION