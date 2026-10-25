**Veredicto: SOUND-with-fixes.** El inspector detecta correctamente truncación, desplazamientos no crecientes, huecos y colas (vía longitud de prefijo), duplicados de coordenada y referencia, NaN/inf y desacuerdo de límites. No encontré ninguna falsa aceptación dentro del alcance prefijos/coverage. Los hallazgos son endurecimientos baratos y huecos de cobertura en tests.

**Confirmado contra el referente**

- Cabecera 48 bytes, tabla en 48, base 377044 coincide con `offset` del tile 0 en installed-nav-tiles.json. Prefijo 16 bytes y `VAND` en +16 en las 94249 teselas.
- Layout de `dtMeshHeader` (15 enteros + 10 flotantes) coincide con los seis samples. Los seis cumplen offMeshBase + offMeshConCount == polyCount y bvNodeCount == 2·offMeshBase.
- Tracé los seis cortes del test de truncación: ninguno llega a lanzar `struct.error`, así que `assertRaises(ValueError)` sin patrón en tests/test_navmesh_v9_prefixes_ev112.py:57 es aceptable.
- El fixture vanilla de dos teselas existe solo en E:/…/navmesh-v9-two-reference-tiles.nm. tests/fixtures/ contiene solo material híbrido ajeno. La afirmación del plan de no publicar bytes vanilla se sostiene.

**Fixes recomendados (inspector)**

- tools/navigation/inspect_navmesh_v9_ev112.py:26 no comprueba ni reporta el u32 en offset 44 (1048576, maxPolys). El docstring línea 4 dice que solo acepta el layout observado, y ese campo queda libre. Fijarlo a 1048576 o al menos emitirlo en el resultado.
- tools/navigation/inspect_navmesh_v9_ev112.py:44 solo exige referencia no nula y única. Los 94249 u32 altos del referente son 65536 + (índice >> 12) y los seis samples cumplen ref == 1<<48 | índice<<20. Comprobar ese patrón cuesta una línea y cierra una aceptación no observada.
- tools/navigation/inspect_navmesh_v9_ev112.py:62 suma polyCount y vertCount y los publica como `polygons` y `vertices` sin contraste con la longitud de carga. Añadir a `limits` que son sumas de cabecera no verificadas. Lo mismo aplica a reference-inspection.json.
- Opcional, mismo alcance de cabecera: layer == 0, offMeshBase + offMeshConCount == polyCount, bvNodeCount == 2·offMeshBase. Observados en todos los samples y gratis de comprobar.
- tools/navigation/inspect_navmesh_v9_ev112.py:81 mezcla dos fallos distintos en un mensaje. Menor.

**Fixes recomendados (tests)**

- tests/test_navmesh_v9_prefixes_ev112.py:30 no tiene negativos para: referencia duplicada (offset 176 a 0), referencia cero (offset 60 a 0), magic corrupto (offset 0), origen o dimensiones de tesela (offsets 20 a 39), parámetros walkable o bvQuantFactor no positivos, y grid que no coincide con el esperado con count coherente.
- tests/test_navmesh_v9_prefixes_ev112.py:49 el primer bucle carece de `subTest`, un fallo oculta los siguientes.
- tests/test_navmesh_v9_prefixes_ev112.py:26 solo comprueba `tiles` y `polygons`. Añadir `vertices`, `y_bounds` esperado [-10, 20] y `grid`.

**Plan**

- plans/ev112-navmesh-v9-20261025.md:53 dice que las pruebas detectan "duplicados". Hoy solo se prueban coordenadas duplicadas, no referencias. Ajustar redacción o añadir el test.
- plans/ev112-navmesh-v9-20261025.md:51 es exacto respecto al código actual. Conviene añadir que polígonos y vértices reportados son sumas de cabecera.

**No verificado en solo lectura**

- No puedo recalcular SHA256 sin ejecutar, así que no confirmo que `inspector_sha256` en reference-inspection.json corresponda a los bytes actuales del inspector. Recomputarlo tras aplicar los fixes y regenerar reference-inspection.json antes de cerrar.

Nada de esto afecta la conclusión declarada: el inspector solo valida el subconjunto observado y Baltic deberá pasar su propia inspección y la sonda de 37 rutas.
