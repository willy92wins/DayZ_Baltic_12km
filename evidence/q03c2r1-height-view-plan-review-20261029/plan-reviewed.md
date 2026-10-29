# Q03C2R1 — continuación geométrica con vista de alturas verificada

Estado: BORRADOR_PENDIENTE_DE_REVISION_DEL_DELTA. Codex planner/integrator;
executor local explícito para contrato y geometría después de esta revisión.
No nuevo council ni repetición de la revisión original Q03C2.

## Cambio de entrada, no de criterio [EXACT]

El plan quality-council-q03c2-source-terrain-water-partition-20261029.md,
SHA79160993e66653336c0eee77ef6cce27498ace51056c1414873f7f5ff543ee30,
ya revisado, define nueve áreas conjuntas por cara y dos algoritmos distintos.
Su única inspección del NPZ completo815ef8 fue consumida y rechazada ARCHIVE_CAP
en0.437s, antes de cabeceras/arrays. Ese rechazo no se reinterpreta ni se relanza.

Q03C2A creó una vista NUEVA con el único heights.npy por copia literal de su
registro local y bytes comprimidos, sin recomprimir. Productor0.735s y consumidor
separado0.938s verificaron procedencia original/vista, NPY/CRC y límites sellados.
La suma declarada original142609920B supera128MiB; es metadata observada de28
miembros, no validación de sus27 payloads auxiliares. Se conserva el original.

Vista privada:
E:/DayZ-Baltic-Build/shape-repair-20261025/q03c2a-height-view-20261029/heights-view.npz
SHA16873c39505aff39533584d329256f6bf7625e27d2ab73da6dbd567c8c929911,
12276275B. Miembro heights.npy <f4, shape[2048,2048], Corder,
expandido16777344B, payload16777216B. SHA del NPY completo
3d428032dcaad84a951f30d9cc46763062e5818b38ef0ee34b78f7f02505a78e;
SHA del payload34c3c5b695de151313b660d0bcce97cf95df6353f78f6d1254ded73dbc614912.
No finitud, triangulación compilada, exposición o mapa evaluados todavía.

## Binding del nuevo contrato [DESIGN]

Fijar externamente antes de código: contratoQ03C2A33de008a, reporte completo
83fbcde52cb7d342532317e068d7819bc254be527d17bc663a802413ff1239d9,
consumer.json2c297d7a8279df7ecb1b907e7f9438891180a3c1f9f0d33bc52872d5ce062a7d,
completion de ambos procesos, aprobación, fuentes finales y vista16873c.
El consumidor de Q03C2A debe tener fixture=false y claims limitados en falso.
La relación original815ef8 queda certificada por recibos guardados; Q03C2R1
NO reabre el original ni rehace la proyección o consumo Q03C2A.

Ambos caminantes geométricos recargan por sí mismos la vista y los201pilotos
pinados. Verifican exactamente su único miembro, descriptor <f4 y2048x2048,
payload/hash propios y finitud al decodificar. Contrato externo, no esquema
inferido del array candidato ni datos transmitidos entre procesos. Una sesión
acumulada por caminante:16MiB stored/128MiB archivo/262434599B total/35miembros
intactos. Reservar heights16MiB y geometría seleccionada dentro del presupuesto
retenido64MiB antes de copias. Si total/RSS no cabe, rechazo; no ampliación.
Las reservas lógicas no prometen RSS. No nuevos lectores genéricos.

El resto del plan original se conserva:1520bed,4760water,201pilotos3d955 ya
mundiales; terreno fuente grid6, ejeXZ/Y y diagonalNW-SE explícitamente asumida.
No agua nominal nueva, terreno WRP decodificado, oclusores ni geometría actual
de motor. No doble transformación. Nueve slots y marginales POR CARA exactas
contra Q03C1 metrics3dea334a. El adaptador únicamente cambia la entrada terreno
por la vista ligada; helpers sellados no se editan ni sus CLIs se relanzan.

Oráculos independientes ANTES de código: asimetría X/Z y filas, cuatro alturas
no coplanares que distingan diagonales, contactos planos/bordes, celdas vecinas,
F/G de aguas opuestas y solapadas, borde final delgrid, winding/permutación y
subdivisión. No derivar esperados de ningún caminante. Negativo de recibo fixture,
vista/NPY/payload alterados, finitud y descriptor, además de los negativos del
plan original. Todo rechazo conserva código y testigo concreto.

## Presupuesto y criterio [DESIGN]

Esta revisión sólo del delta: Muse nativo120s, entrega<=900palabras; una
recuperación120s si no hay dictamen. No revalidar código antiguo ni ejecutar NPZ.
Tras adjudicación: mismo presupuesto de contrato+autoría local900s del plan
original (todavía NO iniciado), review180s incluyendo contrato, suite120s256MiB,
una corrección180 por repro cerrado y recuperación180 por noentrega. Una
producción120s y consumidor120s512MiB, salida32MiB, sin reintentos internos.
4096bits/100000ops/1024fragmentos/8192vértices por cara y caminante, rectas y
celdas vivas incluidas; no reiniciar por celda ni omitir área para PASS.

FULL sólo1520 particiones verificadas; parcial explícito si no cabe. Resultado
MEASURED_SOURCE_TERRAIN_SELECTED_WATER_ONLY, nunca exposición o reparación.
Después Q05 debe medir huella vial completa y ambos accesos; el punto de control
actual no justifica colocar puentes por proximidad ni convertir ancho bbox en
ancho útil. Nueve rechazos humanos abiertos, C1NOT_REVIEWED; P9/P10/P11 y Narva
intactos. Este siguiente hito es medición geométrica, no otra ronda de lectores.
