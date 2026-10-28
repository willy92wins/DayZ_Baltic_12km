**Veredicto: SOUND-with-fixes.** El Plan A es coherente con la petición (inventario sólo lectura, sin build, DayZ ni colocación) y conserva la separación preparación/base. Hay fallos de trazabilidad, cobertura y controles que deben corregirse antes de código. B y C quedan como descubrimiento posterior; no se revisa aquí la reparación del río B3E.

**Problemas concretos**

1. **Lector fuera de cápsula sin identidad fijada.** El plan cita `C:/temp/moto_lanes/review_g3/tools/odol_reader.py` pero no registra su hash ni lo trae al árbol de evidencia. Consecuencia: el catálogo no es reproducible (P8) y un cambio silencioso del lector invalidaría todas las medidas. Corrección: copiar el lector a `tools/` o a la carpeta de evidencia, registrar su hash junto al del PBO, y hacer que el inventario aborte si el hash del lector difiere del fijado.

2. **Denominador de cobertura mal definido.** "Lista exhaustiva de entradas parts/*.p3d" convierte un filtro en denominador. Consecuencia: una entrada mal prefijada, con extensión en mayúsculas o fuera de `parts/` desaparecería sin contarse como omitida, y la "cobertura exacta" sería falsa. Corrección: el denominador es la totalidad de entradas del PBO (p3d, rvmat, paa, config, otros). Clasificar cada una; `parts/*.p3d` y modelos de puente son categorías, y las demás se listan como fuera de alcance, no se omiten.

3. **Modelos de puente: ubicación no verificada.** El plan asume que los puentes separados están en `structures_roads.pbo`. Consecuencia: si viven en otro PBO, el catálogo cerraría CATALOG_COMPLETE con los puentes ausentes y C heredaría un inventario incompleto. Corrección: el inventario declara qué PBO se recorrió y, si no aparecen modelos de puente, cierra con nota explícita "puentes no encontrados en este PBO" y propone un PBO adicional como plan separado, sin barrer la carpeta Addons.

4. **Métodos de empaquetado del PBO.** `read_pbo` de attach_navmesh.py se usó para navmesh; no está acreditado que gestione entradas comprimidas o mimetypes distintos. Consecuencia: un parse parcial podría presentarse como lectura completa. Corrección: leer la definición antes de implementar; validar que la suma de tamaños de entradas más cabecera y checksum coincide con los 318217469 bytes y que el checksum final del PBO verifica. Si alguna entrada tiene método de empaquetado no soportado, INCONCLUSIVE_PARSE para esa entrada y cierre INCONCLUSIVE_CATALOG.

5. **Control analítico irrealizable sin herramienta nueva.** "Muestras de geometría analítica con bbox conocido y LOD ausente" exige escribir ODOL sintético, es decir, un escritor nuevo, contrario al principio del propio plan. Consecuencia: o se crea herramienta no autorizada o el control se finge. Corrección: usar controles disponibles: las 17 piezas FTT como subconjunto que debe aparecer con nombres exactos; el asf1_25 con bbox 12×25 como regresión numérica; y recomputar bbox y centro desde los vértices crudos con una ruta independiente del método del lector (NumPy min/max sobre el array devuelto). Los tests de LOD ausente se hacen con entradas reales que carezcan de ese LOD, no fabricadas.

6. **Riesgo de falso ancho vía Roadway.** El plan prohíbe equiparar bbox con ancho útil, pero no dice qué pasa con la extensión de la Roadway. Consecuencia: la extensión lateral de la Roadway puede filtrarse a B como "ancho útil" sin regla de producto. Corrección: el catálogo publica `roadway_bbox` y `visual_bbox` como campos separados y un campo `usable_width = UNDETERMINED`. B sólo puede rellenarlo con regla de producto o medida de calzada documentada, y el producto no autoriza un ancho global nuevo.

7. **Exportación de derivados vanilla.** "Sólo medidas/metadatos y hashes" es correcto, pero puntos/selecciones completos son derivados de la geometría. Corrección: exportar conteos, nombres de selecciones, propiedades, materiales, bbox, centro y hashes por LOD; nunca arrays de vértices ni caras.

8. **Trazabilidad P9 en C.** C habla de "espacio libre bajo tablero" sin referenciar el contrato de navegación de `evidence/v30-navigation-contract-2026-10-08/decision.json` (fondo 1 m, calado 0,95 m, gálibo con agua máxima). Corrección: C debe citar ese contrato y medir gálibo con agua máxima, no sólo espacio libre nominal.

9. **Afirmaciones sin recibo en la tabla.** "Visual201 midió 24 m²" y "11 secciones con evidencia nativa local" no apuntan a carpeta de evidencia. Corrección: añadir rutas exactas o marcarlas como pendientes de recibo.

**Lo que está bien**

- Separación clara: A no genera poses; B y C requieren plan y revisión propios.
- Cierres correctos: CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE o INCONCLUSIVE_CATALOG; nunca PASS de carretera.
- Hash del PBO comprobado vivo, sin identidad por fecha/tamaño.
- P: declarado como no oráculo del instalado.
- Límites de verify_roads_v30.py conservados y los ámbitos excluidos declarados NO EVALUADOS.
- R-CROSS-49 prohíbe puente en coordenadas del personaje; cruce 49/301 sin puente observado.
- Presupuesto A plausible: 318 MB en 120 s y 2 GiB es realista si el lector no materializa todos los LOD de todos los modelos a la vez. Añadir liberación por entrada.

**Orden para Codex**

Adjudicar los puntos 1 a 5 contra las definiciones reales de `read_pbo`, `read_backend` y `odol_reader.py` antes de escribir código. Actualizar el plan con denominador total del PBO, hash del lector, campo `usable_width = UNDETERMINED`, declaración del PBO recorrido y controles reales en lugar de ODOL sintético. Los puntos 6 a 9 son ediciones de texto del plan. Después, suite 120 s y lectura 120 s/2 GiB. No relanzar CLI de B2A/FTT/B3E ni modificar P:/vanilla.

FIN_REVISION