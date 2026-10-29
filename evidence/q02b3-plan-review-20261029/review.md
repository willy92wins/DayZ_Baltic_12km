**Identidad real.** Q02B3 es un plan de escalado numérico: aplicar la localización de estaciones por prefijos de extremos enteros (sellada en Q02B2) a todo el universo centro×escala del NPZ b661, con un consumidor nuevo basado en árbol de sumas para evitar el caminante lineal. No es un plan de naturalidad, de ángulos ni de reparación. Lo único ya medido es el piloto Q02B2 (54 consultas, tamaños de cache/query observados). Todo lo demás (538390 pares, 600s/900s, 2GiB, 32767 nodos) es propuesta o cota analítica.

**Veredicto.** Dirección correcta, pero NO listo para contrato. Falta un paso de derivación escrita del árbol antes de redactar contrato o fixtures. Con las modificaciones mínimas de abajo puede pasar a contrato.

**Lo que está bien fundamentado**
- El árbol de sumas de `lo` y de `hi` por separado es algebraicamente idéntico a la resta de prefijos del mismo extremo y al caminante: sólo reordena sumas enteras exactas por asociatividad. La costura cerrada del productor (líneas 143-144 y 148-149) ya se expresa como dos rangos disjuntos [center,m) y [0,r). El árbol elimina la resta por completo, así que "no resta cruzada" se cumple por construcción si cada consulta se descompone en nodos disjuntos.
- La unicidad del segmento es demostrable: con prefijos monótonos no decrecientes, a lo sumo un índice satisface S_hi < h < N_lo, y la rama de igualdad exacta no colisiona con la estricta. Eso debe constar en la derivación, no presumirse.
- Cota de nodos: 2·16384−1 = 32767 para 14000 aristas. Correcta.
- Independencia bien planteada: el consumidor recertifica cada raíz contra NPZ con desigualdades enteras y no importa prefijos del productor.

**Problemas concretos**

1. **Derivación del árbol ausente.** El plan la exige pero no la contiene. Deben fijarse por escrito: layout (relleno a potencia de dos con hojas cero explícitas, excluidas del índice de aristas y del conteo m), algoritmo de descomposición rango→nodos con prueba de disjunción y cobertura, regla de partición en la costura, y estrategia de búsqueda. Sin esto, los fixtures "nodo corrupto/hoja intercambiada" no tienen referencia contra qué fallar.

2. **Búsqueda: dos opciones, elegir una.** (a) Bisección sobre prefijos como `_locate:177-181`, cada paso consultando el árbol: O(log²) nodos, acotado y claramente dentro de 100000. (b) Descenso directo por el árbol sobre sumas `lo`: O(log) pero en cadenas cerradas requiere operar con h−T1, que es intervalo, y reintroduce aritmética que el plan quiere evitar. Recomiendo (a): mismas semánticas que el caminante, verificación de S_hi<h<N_lo en vecinos ±2 idéntica, sin resta sobre h.

3. **Partial sin marcador de cadena.** Flush+fsync por cadena no basta: si el proceso muere a mitad de cadena, el shard contiene queries de esa cadena sin cierre. Añadir un registro terminal por cadena (conteo de pares, hash acumulado). Queries de una cadena sin registro terminal no cuentan para VERIFIED_PARTIAL; se reportan como inconclusas. "Subset contiguo" debe definirse como cadenas 0..k con terminal presente.

4. **Shard de 16MiB vs cache de 16MiB.** Un cache al tope no cabe junto a nada. Separar caches de queries: un archivo cache por cadena con su propio cap, shards sólo para queries.

5. **Riesgo del cap de 2GiB.** Extrapolación lineal de los bytes observados en Q02B2 (no es medición ni tiempo):

| Elemento | Base observada | Extrapolación |
|---|---|---|
| Caches | 3674405 B / 4 | ≈ 946 MB para 1030 |
| Queries | 93635 B / 54 | ≈ 934 MB para 538390 |

El total roza 2GiB antes de manifest. El contrato debe declarar que cobertura completa dentro de 2GiB es incierta, o subir el cap de disco explícitamente. No es motivo para tocar caps numéricos.

6. **Equivalencia con el caminante.** Comparar registros completos (state, support, stations, features) de las 54 consultas Q02B2 guardadas, excluyendo `ops`. Esto el plan lo dice bien; añadir que la equivalencia es sobre ESOS 54 casos y fixtures, no una prueba general de igualdad de resultados.

7. **Identidad cerrada/core.** Al quitar la repetición final debe comprobarse igualdad exacta último==primero antes de descartar; si no son iguales, registro de anomalía y cadena excluida con causa, no cache con arista degenerada implícita.

8. **Contabilidad de construcción.** Verificar cada raíz (cuadrados a 4096 bits) más 32767 sumas de nodos entra en 4M por cadena de forma plausible, pero es cuenta nueva: fijar en contrato qué operación cobra qué, y el chequeo de bits antes de cada suma como en `_dir_total:143`.

**Modificaciones mínimas antes del contrato**
- Redactar la derivación del árbol (layout, descomposición, costura, búsqueda por bisección, unicidad del segmento) como documento revisable propio.
- Registro terminal por cadena y definición formal de "contiguo".
- Separar archivos cache de shards query.
- Declarar explícitamente que 2GiB y 600s/900s son presupuestos sin medición; la salida esperada por defecto es PARTIAL o RESOURCE, y FULL es resultado, no objetivo prometido.
- Comprobación exacta último==primero en la derivación core.

**Lo que no cambia.** Correcto mantener h0 fuera del universo, natural 0/calibration false, GEOMETRY_UNBOUND, PENDING_CERTIFIED_ANGLE y no promover nada humano por censo. La unidad entrega sólo cobertura numérica; ninguna de sus etiquetas es aceptación natural.