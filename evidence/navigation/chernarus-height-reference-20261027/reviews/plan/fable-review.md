**Dictamen: SOUND-with-fixes.** El experimento discrimina una cuestión útil antes de otra generación, la selección es ciega al resultado, y el observable es el mismo que el verificador Baltic. Hay seis puntos de contrato que hay que fijar antes del run; ninguno relaja tolerancias ni cambia el verificador.

**Qué discrimina.** El verificador compara NavY con SurfaceRoadY por waypoint y falla sobre 0,801 (`tools/navigation/verify_continuity_nav_v30.py:32,41`). Si la malla Chernarus desplegada produce la misma desviación sobre streambed vanilla, la búsqueda de anchos deja de ser la hipótesis principal y el mecanismo pasa a ser el generador del motor sobre la LOD Roadway. Si no la produce, el defecto sigue acotado a Baltic. Ambos resultados cambian la siguiente decisión. El plan ya dice correctamente que ningún resultado vanilla autoriza borrar FAIL ni rebajar 0,801.

**Comparabilidad geométrica verificada.** Las rutas Baltic son laterales ±6 desde el eje del lecho (`discover_kit7_nav_routes.py:19`), y los tramos de pieza cubren 25%-75% de la estación (`:42`). El kit documenta +Z del modelo a lo largo del tramo (`streambed_kit_v31.py:105,658`), así que ModelToWorld(q,0,±6) con q=±6 es el equivalente nativo razonable. La tolerancia 2,1 de extremos coincide con `verify_kit7_nav_ev112.py:73`. No se detecta falso contraste en la selección: ordenar por (z,x,shape) y floor(i*(N-1)/7) es determinista y no toca alturas. El CSV contiene 554 filas long_straight, coherente con 218/188/148; recontar por familia en el congelado.

**Bugs de contrato a corregir (mínimos):**

1. **Variante de SurfaceRoadY no fijada.** `game.c:1177` tiene parámetro `rsd` con defecto LEGACY. Baltic usa el defecto (`init.c:88`). La encuesta vanilla usó SurfaceRoadY3D UNDER (`BalticVanillaTricksV1/init.c:205`). El plan debe decir explícitamente: SurfaceRoadY(x,z) sin tercer argumento, tanto en extremos como por waypoint. Mezclar variantes cambia el observable.

2. **Anclaje: radio y definición de duplicado ausentes.** El plan exige "exactamente uno" pero no fija el radio de GetObjectsAtPosition ni qué cuenta como duplicado. Piezas consecutivas del mismo modelo están a pocos metros, así que un radio amplio produciría INCONCLUSO falso. Fijar: duplicado es dos objetos con el modelo esperado a <=0,05 de la posición registrada; otros objetos del mismo modelo fuera de ese radio no cuentan. Además, la encuesta deduplicó con clave redondeada a 0,1 m (`init.c:175`), así que el CSV no acredita unicidad; sólo el chequeo en tiempo de ejecución lo hace.

3. **Extensión z=±6 sin comprobar contra la longitud de la pieza.** Si los extremos caen fuera de los plate-ends del long_straight, el extremo mide terreno, no Roadway, y la ruta deja de ser de orilla. Antes de congelar, derivar la z de plate-end del long_straight de cada familia desde datos ya existentes del kit (centre/roadway_flat_y como en `kit_dims`, `streambed_kit_v31.py:657-663`) y asertar que 6 m queda dentro. Si no cabe, informar y volver a revisión; no cambiar z sin revisión.

4. **Poder discriminante no registrado.** Una ruta vanilla sólo puede fallar si en algún waypoint |SurfaceRoadY−SurfaceY| supera 0,801. Si todas las piezas elegidas están a ras de terreno, 48 PASS serían un falso contraste. Registrar por waypoint esa separación y, por ruta, si existe algún waypoint con separación >0,801. Si ninguna ruta comparable es discriminante, el contraste es INCONCLUSO. Esto es estratificación en el informe, no selección.

5. **Resultado esperado del control NONE sin definir.** Con `init.c:65-72` y `aiworld.c:120`, el filtro NONE da sa=false, sb=false, found=false, count=0, y a/b quedan intactos. El consumidor debe exigir exactamente eso.

6. **Orden por waypoint.** Mantener la secuencia de `init.c:78-94`: FindPath, luego por waypoint warm radio 40 en (x,0,z), SurfaceY, SurfaceRoadY. El pre-calentamiento adicional sólo antes de fijar Y de extremos. Comprobar en cabecera que GetWorldName devuelve ChernarusPlus, como en los bloques RAM.

**Diferencia a declarar en límites, no corregir.** Los extremos Baltic tomaron Y de max(roof, terreno)+0,2 offline (`discover_kit7_nav_routes.py:34-37`); aquí la Y viene de SurfaceRoadY del motor +0,2. El observable por waypoint es idéntico; la fuente de Y de extremos no. Registrar también la escala del objeto, ya que ModelToWorld la incluye y los vanilla no están a escala 1 (CSV ay_y 0,98965, 0,99342).

**Sampling y tolerancias.** Radio 2 de SampleNavmeshPosition y comparabilidad 2,1 son correctos y coinciden con Baltic. El 0,05 de anclaje es adecuado para un CSV con tres decimales. Nada en el plan rebaja 0,801 ni toca verify_kit7_nav_ev112.py.

**Siguientes pasos dentro del alcance:**

1. Codex corrige el plan con los seis puntos y fija selección, CSV y hashes.
2. Pre-chequeo offline de extensión z (punto 3) y recuento por familia; resultado al paquete de congelado.
3. Plantilla init.c nueva con 49 filas, END;49, comprobación de mundo, anclaje y NONE según puntos 2, 5 y 6.
4. Consumidor separado con comparabilidad, integridad, separación road−terreno y distribución de errores, con los negativos listados en el plan más "ninguna ruta discriminante".
5. Revisión del diferencial operativo antes del lanzamiento, luego un run FIFO con cierre observado y liberación.

Esta prueba no es aceptación; Nav8 PASS 607, RAM FAIL y Nav12 FAIL se conservan intactos.
