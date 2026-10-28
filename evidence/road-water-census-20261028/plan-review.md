**Veredicto: SOUND-with-fixes.** El método geométrico es correcto y consistente con las APIs reales; faltan cuatro precisiones sin las cuales la producción puede dar falsos FAIL o cobertura engañosa.

**Lo que verifiqué como correcto**

- Registro de triángulos. `tri_h` en `tools/water/shore_ramp_v31.py:150` usa `fc >= fr` para la cara NW-NE-SE y `sample` en `tools/navigation/waterway_common.py:43` usa `b <= a`. Son la misma regla. Con ZTOP = 6·2047 la diagonal cumple X+Z = 6k exactamente, como afirma el plan.
- Modelo lineal H-W. `extract_segments` interpola d = H-W por arista con el agua de esquina de la celda propia. Evaluar H-W baricéntrico por cara y resolver una raíz única por intervalo es el mismo modelo. Comparar raíces con segmentos guardados es legítimo.
- Mojado estricto. Productor y consumidor nativo usan `H < W`. Si el censo de carreteras usa la misma desigualdad, H==W cae en contacto y nunca en mojado.
- Presupuesto. 36467 aristas cortas cruzan pocas celdas cada una; 120s/2GiB sobra con holgura.
- Independencia. No lee crossings-ev106 ni la lista de puentes; el consumidor Shapely no importa el recorrido. Correcto.

**Fixes necesarios, con mecanismo**

1. **Clave `edges` del NPZ no verificada.** Ningún script del repositorio lee otra clave que `xy` de reference.npz. Si la clave no existe, la invariante "multiconjunto igual a edges" no puede ejecutarse y el plan no dice qué pasa. Fix: listar `npz.files` al inicio; si no hay `edges`, la comprobación queda INCONCLUSIVE_NO_EDGE_KEY y la cobertura se declara solo contra las 124 cadenas, sin afirmar igualdad con un grafo no disponible. No inventar edges a partir de las propias cadenas y compararlas consigo mismas.

2. **Cambio de estado en corte de celda sin raíz.** El agua es por esquina de celda, no por vértice. Una carretera puede pasar de mojada a seca exactamente en X=6k o Z=6k porque W salta de charca a mar (0,75 m) sin que H-W cruce cero en ninguna cara. El plan solo nombra discontinuidades para aristas coincidentes con borde. Si la comparación "raíces frente a segmentos" exige una raíz en cada transición, producirá falso FAIL; si las ignora, el contacto desaparece del inventario. Fix: clase explícita WATER_STEP_AT_CELL_CUT con t, celda a cada lado y ambos valores de W. El consumidor Shapely la reproduce al recortar por cara, así que la fixture "agua discontinua a ambos lados" debe exigir exactamente esa clase, no una raíz.

3. **Consumidor Shapely y aristas sobre borde.** Recortar la línea contra polígonos mojados de dos caras adyacentes cuenta dos veces la longitud de un tramo que yace sobre el borde compartido, o cero veces si Shapely lo trata como frontera. La fixture "recorrido sobre arista nativa" fallará por mecanismo del consumidor, no del productor. Fix: el consumidor compara por cara, no por unión, y para intervalos AMBIGUOUS_WATER_BOUNDARY verifica que el recorrido reporta ambas clasificaciones en lugar de igualdad de longitud.

4. **Fuera de rejilla y selección de cara.** `tri_h` recorta índices con `np.clip` en silencio; `sample` lanza error pero exige +200000 en X. Si el autor reutiliza `tri_h` sin comprobación previa, un vértice con x = 12282 o z > ZTOP se clasifica como si fuera interior. Fix: comprobación explícita de 0 ≤ x,z ≤ ZTOP antes de cualquier evaluación, coordenadas locales sin desfase, y cara del intervalo elegida por el punto medio del intervalo, nunca por un extremo que cae sobre la diagonal. Deduplicar valores de t solo por igualdad exacta.

**Riesgos menores que conviene fijar por escrito**

- Cara coplanar con H-W ≡ 0 a lo largo del intervalo tiene raíces infinitas. Clasificar como CONTACT_INTERVAL en lugar de intentar resolver.
- El censo nativo guardado está en E:\DayZ-Baltic-Build\shape-repair-20261025\native-shore-census-20261028\native-shore.npz con SHA b6612009…; el plan no pina ni ruta ni hash. Añadirlos a inputs antes y después.
- 36428 nodos con 36467 aristas en 124 cadenas implica unos 163 nodos de unión repetidos. La igualdad del multiconjunto detecta aristas duplicadas entre cadenas, pero el plan debe decir que un nodo compartido no es error.
- El 1e-9 m de residuo es adecuado para raíces baricéntricas. Para la igualdad de longitudes del consumidor Shapely conviene declarar la tolerancia por separado, porque Shapely acumula error distinto al de la fracción t.

**Falsos PASS buscados y no encontrados**

No hay mecanismo que marque NO_CONTACT por ausencia de datos: fuera de rejilla, dato no finito y cobertura incompleta están declarados como no PASS. El criterio CENSUS_COMPLETE_NOT_BRIDGE_ACCEPTANCE no afirma ancho real, pavimento ni importación, y los contactos no se traducen en "falta puente". Correcto.

**Corrección mínima verificable**

Añadir al plan las cuatro clases y reglas anteriores, más la pin del censo nativo. Fixtures nuevas: salto de W en corte de celda sin raíz, línea sobre borde comparada por cara, vértice en x = ZTOP rechazado, cara coplanar. Todas deben fallar antes de la corrección y pasar después.

FIN_REVISION
