**Adjudicación: SOUND-with-fixes.** Sin falsos PASS encontrados; dos huecos de entregable/pruebas y un artefacto de reporte.

**Lo verificado (mecanismo y fuente)**

- Convención de coordenadas correcta. El productor usa col = x/6, fila = (top−z)/6 y triángulo A cuando u ≥ v (`road_water_contacts_ev112.py:46-48`). Coincide con `waterway_common.py:35-45` (b ≤ a → A) y con `shore_ramp_v31.py:150,167`. Diagonal NW-SE es x+z constante porque ZTOP = 12282 = 6·2047; los cortes X/Z/X+Z (líneas 38-42) particionan cada arista por cara.
- Agua por esquina igual al censo nativo: field donde plane finito, 0.75 si no (línea 86 vs `corner_water`). Mojado estricto d<0, H==W nunca mojado, intervalo coplanar sólo si d0==d1==0 (líneas 67-75). Salto de agua sin raíz registrado en todos los pares de caras (líneas 99-106).
- Caras incidentes por punto medio con tolerancia 1e-12 en unidades de celda; borde exterior exacto válido con única cara (línea 61 descarta col = n−1). Ambas caras conservadas en borde compartido y AMBIGUOUS si el agua difiere (línea 93).
- Cobertura: multiconjunto no dirigido chains vs edges exacto y sin duplicados (líneas 113-122); universo 124/36428/36467 obligatorio (153); partición [0,1] sin huecos y longitud dentro de 1e-9 por arista (95-98); suma global (175). Fallos levantan ValueError → failure.json, nunca PASS.
- Raíces contra censo guardado: sólo contrasta raíces emitidas (167-169). Una raíz estricta implica cara mixta en `expected_faces`, así `root_face_missing` no da falso FAIL. Conditioning: el residuo perpendicular ≈ δd/|∇d| con δd ≈ 6e-13·max|d_k| y |∇d| ≥ max|d_k|/8.5 m, ≈5e-12 m independientemente de pendiente; 1e-9 es robusto incluso con cara rasante.
- Nada de puentes ni crossings-ev106 como entrada; estados de cadena no son aceptación. Hashes antes/después, inputs.json, presupuesto 120s/2GiB medido en el intérprete con vigilante os._exit(3) → INCONCLUSIVE_RESOURCE.
- Oráculo independiente: recorte del triángulo por semiplano d<0 y LineString con Shapely, sin cortes ni baricéntricas del autor; conserva ambos lados; tangencias dan Point y se ignoran; coplanar no genera polígono. Tolerancia 1e-9 m en t. Random (16 trazas, 7×7, alturas −2..3, charca) y fronteras cubiertas. El test de salto sin raíz exige steps==1 y ausencia de raíces; el río estrecho exige anchura <1 cm.

**Hallazgos (ninguno es falso PASS)**

1. **Requisito del plan no implementado** (plan línea 67): "ausencia de raíz en una cara totalmente mojada se cuenta explícitamente". El reporte no cuenta caras mojadas sin raíz; sólo roots_checked. Añadir contador por parte (wet no vacío y roots vacío).
2. **Guardas sólo de producción sin test**: `root_face_missing`, `root_not_on_native_shore`, `partition_length`, `road_universe`, `edge_length` (línea 116). El significado de la tercera columna de edges como longitud euclídea 1e-9 no está demostrado en el plan (sólo "36467x3 float64"); si es otra métrica, resultado `edge_length` = INCONCLUSIVE, no falso PASS. Extraer la verificación de raíces a una función y probarla con un diccionario by_face sintético.
3. **Artefacto por t casi idénticos**: cuando una arista pasa exactamente por un vértice de rejilla, los cortes X, Z y X+Z pueden diferir en 1 ulp y crear una parte sliver cuyo punto medio incide en hasta 6 caras; el bucle de steps compara pares de caras no recorridas y puede emitir WATER_STEP espurios en charcas con field distinto por celda, marcando la arista como contacto. No causa falso FAIL ni pérdida; improbable con coordenadas OSM no ajustadas. Documentar o agrupar t con |Δt|≤1e-15 relativa (sigue sin borrar intervalos).
4. **Entregable**: no se exporta longitud mojada total por cadena ni unión geométrica (plan línea 100); partitions.npz guarda intervalos secos sin identidad de cara. Añadir longitud mojada por cadena por unión de intervalos y cara en partitions. Falta fixture con raíz exactamente en corte de celda (d==0 en frontera): el código lo trata como mojado sin raíz y lo lista por `0 in difference`; conviene test.
5. Rendimiento: ~300k partes con arrays numpy pequeños en bucle Python; estimo 30-70 s, cerca del límite. Exceso termina INCONCLUSIVE_RESOURCE, conforme al plan.

**Sin problema**: dominio inclusivo [0,12282]; mid-face selection; tolerancia 1e-12 de incidencia coherente con -1e-9 en pesos (una parte a <6e-12 m de una línea es necesariamente minúscula); hash del propio script y de los dos módulos importados pinneados en runtime.

**Siguiente paso**: aplicar fixes 1, 2 y 4 (y opcionalmente 3), re-ejecutar tests, luego la única corrida de producción.

FIN_REVISION
